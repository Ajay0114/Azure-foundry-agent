// Extracts the PC_HomeDelivery (Product Return) dialog from the Kore export into readable markdown.
// Usage: node extract.js   ->  writes flow.md and nodes/*.md next to this file.
const fs = require('fs');
const path = require('path');

const data = JSON.parse(fs.readFileSync('D:/test2/appDefinition.json', 'utf8'));
const comp = Object.fromEntries(data.dialogComponents.map(c => [c._id, c]));
const dialog = data.dialogs[0];
const byNode = Object.fromEntries(dialog.nodes.map(n => [n.nodeId, n]));
const out = __dirname;
fs.mkdirSync(path.join(out, 'nodes'), { recursive: true });

const NOISE = new Set(['_id', 'refId', 'piiDataEnabled', 'applyDefaultTemplate', 'spellcorrectThreshold',
  'vNameSpace', 'useTaskLevelNs', 'isSensitive', 'isTransient', 'skipDGPTStrictly', 'parentId',
  'entityFields', 'localeData', 'serviceNodeType', 'preConditions', 'dialogId']);
const SECRET = /authorization|api[-_]?key|secret|token|password|bearer|ocp-apim/i;

function decode(v) {
  if (typeof v === 'string' && /%[0-9A-Fa-f]{2}/.test(v)) {
    try { return decodeURIComponent(v); } catch { return v; }
  }
  return v;
}
function clean(v, key = '') {
  if (SECRET.test(key) && typeof v === 'string') return '<REDACTED>';
  if (Array.isArray(v)) return v.map(x => clean(x, key));
  if (v && typeof v === 'object') {
    const o = {};
    for (const [k, x] of Object.entries(v)) {
      if (NOISE.has(k)) continue;
      const c = clean(x, k);
      if (c === '' || c === null || (Array.isArray(c) && !c.length) ||
          (c && typeof c === 'object' && !Array.isArray(c) && !Object.keys(c).length)) continue;
      o[k] = c;
    }
    return o;
  }
  return decode(v);
}
// header objects like {key:'Authorization', value:'...'}: redact by sibling key name
function redactHeaders(o) {
  if (Array.isArray(o)) return o.map(redactHeaders);
  if (o && typeof o === 'object') {
    if (typeof o.key === 'string' && SECRET.test(o.key) && 'value' in o) o.value = '<REDACTED>';
    for (const k of Object.keys(o)) o[k] = redactHeaders(o[k]);
  }
  return o;
}

function label(nodeId) {
  const n = byNode[nodeId];
  if (!n) return nodeId;
  const c = comp[n.componentId] || {};
  return `${c.name || n.componentId} [${c.type}]`;
}
function cond(t) {
  if (t.default) return 'DEFAULT';
  if (t.if && t.if.dialogAct) return `USER SAYS ${t.if.dialogAct.toUpperCase()}`;
  if (t.if && t.if.intent) return `INTENT ${t.if.intent}`;
  if (t.if) {
    const tests = (t.if.tests || []).map(x => `${x.context} ${x.op} ${JSON.stringify(x.value)}`);
    return `IF ${tests.join(` ${t.if.conjoin || 'and'} `)}`;
  }
  if (t.condition) return `COND ${JSON.stringify(t.condition)}`;
  return JSON.stringify(Object.keys(t).filter(k => k !== 'metadata'));
}

// ---- flow.md: BFS from the intent node, in execution order
const order = [];
const seen = new Set();
const queue = ['intent0'];
while (queue.length) {
  const id = queue.shift();
  if (seen.has(id) || !byNode[id]) continue;
  seen.add(id); order.push(id);
  for (const t of byNode[id].transitions || []) {
    const to = t.then || t.default;
    if (to) queue.push(to);
  }
}
const orphans = dialog.nodes.map(n => n.nodeId).filter(id => !seen.has(id));

let flow = `# PC_HomeDelivery (Product Return) – flow graph\n\n${dialog.nodes.length} nodes; ${order.length} reachable from intent0 (breadth-first order below); ${orphans.length} not reachable (interrupt/intent entry points).\n\n`;
for (const id of order) {
  const n = byNode[id];
  flow += `## ${label(id)}\n- nodeId: \`${id}\`\n`;
  for (const t of n.transitions || []) {
    const to = t.then || t.default;
    flow += `- ${cond(t)} -> ${to ? label(to) : '(end)'}\n`;
  }
  flow += '\n';
}
flow += `## Not reachable from intent0\n` + orphans.map(id => `- ${label(id)} (\`${id}\`)`).join('\n') + '\n';
fs.writeFileSync(path.join(out, 'flow.md'), flow);

// ---- nodes/<name>.md: decoded component content (deduped by component)
const done = new Set();
let index = '# Node index\n\n| type | name | file |\n|---|---|---|\n';
for (const id of order.concat(orphans)) {
  const c = comp[byNode[id].componentId];
  if (!c || done.has(c._id)) continue;
  done.add(c._id);
  const cleaned = redactHeaders(clean(c));
  const file = `${c.type}__${c.name.replace(/[^\w.-]/g, '_')}.md`;
  let md = `# ${c.name}  (${c.type})\n\n`;
  // pull big text fields out as code blocks for readability
  const blocks = [];
  (function walk(o, p) {
    if (o && typeof o === 'object') {
      for (const [k, v] of Object.entries(o)) {
        if (typeof v === 'string' && (v.length > 160 || v.includes('\n'))) {
          blocks.push([p ? `${p}.${k}` : k, v]); delete o[k];
        } else walk(v, p ? `${p}.${k}` : k);
      }
    }
  })(cleaned, '');
  md += '## Config\n```json\n' + JSON.stringify(cleaned, null, 2) + '\n```\n';
  for (const [k, v] of blocks) md += `\n## ${k}\n\`\`\`\n${v}\n\`\`\`\n`;
  fs.writeFileSync(path.join(out, 'nodes', file), md);
  index += `| ${c.type} | ${c.name} | nodes/${file} |\n`;
}
fs.writeFileSync(path.join(out, 'index.md'), index);
console.log('nodes written:', done.size, ' reachable:', order.length, ' orphans:', orphans.length);
