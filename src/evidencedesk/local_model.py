"""Optional local Transformers adapter exposing the subset used by EvidenceDesk.

Run with `python -m evidencedesk.local_model`. Downloads real pretrained weights.
This is a localhost development adapter, not a general inference platform.
"""

import argparse
import json
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str = Field(max_length=16000)


class Completion(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=8)
    max_tokens: int = Field(default=500, ge=1, le=800)
    response_format: dict | None = None


def first_json_object(text):
    """Normalize a complete first JSON object; source validation happens in the caller."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[len("```json"):].lstrip()
    value, _ = json.JSONDecoder().raw_decode(text)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def create_model_app(model_name="Qwen/Qwen2.5-1.5B-Instruct"):
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        StoppingCriteria,
        StoppingCriteriaList,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=False)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=False)
    model.to(device).eval()
    app = FastAPI(title="EvidenceDesk local model adapter")
    lock = threading.Lock()

    @app.get("/health")
    def health():
        return {"status": "ok", "model": model_name, "device": device}

    @app.post("/v1/chat/completions")
    def complete(request: Completion):
        messages = [m.model_dump() for m in request.messages]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        if inputs["input_ids"].shape[1] > 6000:
            raise HTTPException(status_code=400, detail="Prompt exceeds this demo adapter's context limit")
        json_mode = request.response_format and request.response_format.get("type") == "json_object"
        prompt_length = inputs["input_ids"].shape[1]

        class StopAtCompleteJSON(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                decoded = tokenizer.decode(input_ids[0, prompt_length:], skip_special_tokens=True)
                try:
                    first_json_object(decoded)
                    return True
                except (ValueError, json.JSONDecodeError):
                    return False

        stopping = StoppingCriteriaList([StopAtCompleteJSON()]) if json_mode else None
        with lock, torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=request.max_tokens,
                                    do_sample=False, pad_token_id=tokenizer.eos_token_id,
                                    stopping_criteria=stopping)
        text = tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        if json_mode:
            try:
                text = json.dumps(first_json_object(text))
            except (ValueError, json.JSONDecodeError) as exc:
                raise HTTPException(status_code=502, detail="Model did not return a complete JSON object") from exc
        return {"model": model_name, "choices": [{"message": {"role": "assistant", "content": text}}]}

    return app


def main():
    import uvicorn
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--port", type=int, default=11434)
    args = parser.parse_args()
    uvicorn.run(create_model_app(args.model), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
