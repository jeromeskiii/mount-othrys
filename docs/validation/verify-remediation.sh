#!/usr/bin/env bash
# Independent verification of MF-1 and MF-2 (reads only; no repo writes).
set -uo pipefail
REPO=/Users/ohmskiii/mount-othrys
cd "$REPO"
PY=./talos/.venv/bin/python

echo "=== MF-2: engine router (built dist) vs Python matcher, same corpus ==="
"$PY" - <<'PY' > /tmp/othrys-eval/mf2-corpus.txt
from othrys.routing import load_examples
for message, expected in load_examples():
    print(f"{expected}\t{message}")
PY
fails=0
while IFS=$'\t' read -r expected message; do
  ts=$(cd engine && node dist/cli.js route "$message" --json 2>/dev/null | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{process.stdout.write(JSON.parse(s).titan)})")
  py=$("$PY" -c "
from othrys.routing import canonical_titan
print(canonical_titan('''$message''')[0])" 2>/dev/null)
  if [ "$ts" = "$expected" ] && [ "$py" = "$expected" ]; then
    printf '  OK    %-8s %-8s %s\n' "$ts" "$py" "$message"
  else
    fails=$((fails+1))
    printf '  FAIL  ts=%-8s py=%-8s want=%-8s %s\n' "$ts" "$py" "$expected" "$message"
  fi
done < /tmp/othrys-eval/mf2-corpus.txt
echo "MF-2 corpus mismatches: $fails"

echo
echo "=== MF-2: shadowing regression (was talos before the fix) ==="
(cd engine && node dist/cli.js route "Implement this complex work" --json) | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{const j=JSON.parse(s);console.log('  titan:',j.titan,'| reason:',j.reason)})"

echo
echo "=== MF-1: engine builds the envelope (built dist) ==="
node --input-type=module -e "
import { TITAN_REGISTRY, buildTitanInvocation, CONTEXT_ENV_VAR } from '$REPO/engine/dist/index.js'
const inv = buildTitanInvocation(
  TITAN_REGISTRY.iapetus,
  { prompt: 'what can break', workdir: '/tmp', context: { systemPrompt: 'You are Iapetus of Mount Othrys: deep execution and craft.', mode: 'iapetus', phase: 'execute' } },
  '$REPO', {}, {},
)
console.log('  args  :', JSON.stringify(inv.args))
console.log('  argv carries prompt?', inv.args.some(a => a.includes('Iapetus of Mount Othrys')))
console.log('  ' + CONTEXT_ENV_VAR + ':', inv.env[CONTEXT_ENV_VAR])
"

echo
echo "=== MF-1: worker honours the envelope (no network call) ==="
OTHRYS_CONTEXT='{"mode":"talos","phase":"execute","systemPrompt":"ENGINE DIRECTIVE"}' \
ANTHROPIC_API_KEY=test-key-not-used \
"$PY" - <<'PY'
from othrys import load_context
from talos.llm import TalosLLM

ctx = load_context()
print('  parsed mode/phase :', ctx.mode, '/', ctx.phase)
llm = TalosLLM()
print('  model             :', llm.config.model)
text = llm._system_block('WORKER PROMPT')[0]['text']
print('  system prompt     :', repr(text[:80]) + '...')
assert text.startswith('ENGINE DIRECTIVE'), 'engine directive was not applied'
assert 'WORKER PROMPT' in text, 'worker prompt was destroyed'
print('  -> engine directive prepended, worker prompt preserved')
PY

echo
echo "=== MF-1: no envelope => worker behaviour unchanged ==="
ANTHROPIC_API_KEY=test-key-not-used "$PY" - <<'PY'
from talos.llm import TalosLLM
text = TalosLLM()._system_block('WORKER PROMPT')[0]['text']
print('  system prompt     :', repr(text))
assert text == 'WORKER PROMPT', 'standalone CLI behaviour changed'
print('  -> unchanged')
PY