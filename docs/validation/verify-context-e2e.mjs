/**
 * Pass-2 independent verification, method 2:
 * drive the envelope through the REAL runner chain (ModeEngine -> WorkflowRunner ->
 * PythonTitanAdapter -> spawnPythonTitan -> child process), rather than calling
 * buildTitanInvocation in isolation as the unit tests do.
 */
import { chmodSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { ModeEngine, PythonTitanAdapter, TITAN_REGISTRY, CONTEXT_ENV_VAR } from '/Users/ohmskiii/mount-othrys/engine/dist/index.js'

const sandbox = mkdtempSync(join(tmpdir(), 'othrys-e2e-'))
const script = join(sandbox, 'echo-context.sh')
// Emit a well-formed TitanOutput whose `output` is the raw envelope the child received.
writeFileSync(
  script,
  `#!/bin/sh\nexec python3 -c 'import json,os;print(json.dumps({"output":os.environ["OTHRYS_CONTEXT"],"passed":True,"checks":[]}))'\n`,
  'utf8',
)
chmodSync(script, 0o755)

// Talos is a python-adapter Titan, so this exercises the real bridge.
const titan = { ...TITAN_REGISTRY.talos, pythonBinary: script }
const adapters = new Map([['talos', new PythonTitanAdapter(titan, '/Users/ohmskiii/mount-othrys', {}, {})]])

// Empty workdir => verifier derives no commands => verification passes.
const engine = new ModeEngine({ adapters, rootDir: '/Users/ohmskiii/mount-othrys' })
const result = await engine.run('Implement this complex work', {
  workdir: sandbox,
  titanOverride: 'talos',
})

const envelope = JSON.parse(result.output)
console.log('mode routed        :', result.mode)
console.log('phase              :', result.phase)
console.log('verification passed:', result.verification.passed)
console.log('envelope in child  :', JSON.stringify(envelope))
console.log('systemPrompt carried:', envelope.systemPrompt === TITAN_REGISTRY.talos.systemPrompt)
console.log('mode carried       :', envelope.mode === 'talos')
console.log('phase carried      :', envelope.phase === 'execute')

rmSync(sandbox, { recursive: true, force: true })

const ok = envelope.systemPrompt === TITAN_REGISTRY.talos.systemPrompt &&
  envelope.mode === 'talos' && envelope.phase === 'execute' && result.verification.passed
console.log(ok ? 'RESULT: PASS' : 'RESULT: FAIL')
process.exit(ok ? 0 : 1)