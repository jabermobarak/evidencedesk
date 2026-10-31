/* Untrusted text is rendered through textContent, never HTML. */
const $ = (id) => document.getElementById(id);
let busy = false;
async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if ($('token').value) headers.set('Authorization', `Bearer ${$('token').value}`);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(path, {...options, headers});
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Please check the request and try again.');
  return data;
}
function textNode(tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}
async function refresh() {
  const [docs, config] = await Promise.all([api('/api/documents'), api('/api/config')]);
  $('connection').textContent = 'Workspace ready';
  $('doc-count').textContent = docs.length;
  $('backend').textContent = config.llm_model ? `LLM available: ${config.llm_model}` : 'Offline retrieval demo · no API key required';
  $('documents').replaceChildren();
  for (const doc of docs) {
    const row = textNode('div', '', 'document');
    row.append(textNode('span', '▤', 'doc-icon'));
    const info = textNode('div', '', 'doc-info');
    info.append(textNode('div', doc.title, 'doc-title'), textNode('div', `${doc.pages} page${doc.pages === 1 ? '' : 's'} · ${doc.chars.toLocaleString()} characters`, 'doc-meta'));
    const remove = textNode('button', '×', 'delete');
    remove.setAttribute('aria-label', `Delete ${doc.title}`);
    remove.onclick = () => perform(async () => {
      if (confirm(`Remove ${doc.title} from this workspace?`)) {
        await api(`/api/documents/${encodeURIComponent(doc.id)}`, {method:'DELETE'});
        await refresh();
      }
    });
    row.append(info, remove);
    $('documents').append(row);
  }
  if (!docs.length) $('documents').append(textNode('p', 'Your documents will appear here.', 'muted'));
}
async function perform(action) {
  if (busy) return;
  busy = true;
  $('ask').disabled = true;
  $('load-demo').disabled = true;
  $('notice').textContent = 'Working…';
  try { await action(); $('notice').textContent = ''; }
  catch (error) { $('notice').textContent = error.message; }
  finally { busy = false; $('ask').disabled = false; $('load-demo').disabled = false; }
}
$('token').addEventListener('change', () => perform(refresh));
$('load-demo').onclick = () => perform(async () => { await api('/api/demo', {method:'POST'}); await refresh(); });
$('upload').onchange = (event) => perform(async () => {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 2000000) throw new Error('Please choose a file smaller than 2 MB.');
  const body = new FormData(); body.append('file', file);
  await api('/api/documents', {method:'POST', body});
  event.target.value = ''; await refresh();
});
$('ask-form').onsubmit = (event) => {
  event.preventDefault();
  perform(async () => {
    const data = await api('/api/ask', {method:'POST', body:JSON.stringify({question:$('question').value, mode:$('mode').value, use_llm:$('use-llm').checked})});
    $('empty').hidden = true; $('result').hidden = false;
    $('answer').textContent = data.answer;
    $('status').textContent = data.status; $('status').className = `badge ${data.status}`;
    $('citation-count').textContent = `${data.citations.length} verified quote${data.citations.length === 1 ? '' : 's'}`;
    $('citations').replaceChildren();
    data.citations.forEach((citation, index) => {
      const card = textNode('article', '', 'citation');
      card.append(textNode('div', `[${index + 1}] ${citation.title} · page ${citation.page}`, 'citation-label'), textNode('blockquote', citation.quote));
      $('citations').append(card);
    });
    $('trace').textContent = `${data.latency_ms} ms · ${data.retrieval_backend} · ${data.generation_backend} · trace ${data.request_id.slice(0, 12)}`;
    $('warnings').replaceChildren(...data.warnings.map(warning => textNode('li', warning)));
  });
};
document.querySelectorAll('[data-question]').forEach(button => button.onclick = () => {
  $('question').value = button.dataset.question; $('question').focus();
});
perform(refresh);
