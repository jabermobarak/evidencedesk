import argparse
import json

from .config import Settings
from .schemas import Question
from .service import EvidenceService
from .store import Store


def main():
    parser = argparse.ArgumentParser(description="EvidenceDesk document QA")
    parser.add_argument("command", choices=["serve", "demo", "ask", "evaluate"])
    parser.add_argument("question", nargs="?")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--output", default="reports/benchmark.json")
    parser.add_argument("--use-llm", action="store_true")
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("evidencedesk.api:create_app", factory=True, host=args.host, port=args.port)
        return
    if args.command == "evaluate":
        from .evaluation import evaluate
        print(json.dumps(evaluate(args.output), indent=2))
        return
    settings = Settings.from_env()
    service = EvidenceService(Store(settings.database), settings)
    if args.command == "demo":
        print(json.dumps(service.load_demo(), indent=2))
    else:
        if not args.question:
            parser.error("ask requires a question")
        print(service.ask(Question(question=args.question, use_llm=args.use_llm)).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
