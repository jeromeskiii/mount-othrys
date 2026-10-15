import { chmodSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterAll, describe, expect, it } from 'vitest'
import {
  CONTEXT_ENV_VAR,
  DIRECTIVE_SEPARATOR,
  buildEngineContext,
  buildTitanInvocation,
  resolveSystemPrompt,
  spawnPythonTitan,
} from '../src/adapters'
import { ThemisAdapter } from '../src/adapters/themis-adapter'
import { HeraclesAdapter } from '../src/adapters/heracles-adapter'
import { TITAN_REGISTRY } from '../src/modes/registry'
import type { TitanConfig } from '../src/modes/types'
import type { TitanInput } from '../src/adapters/types'
import type { LLMProvider, LLMRequest } from '../src/providers/LLMProvider'

const talos = TITAN_REGISTRY.talos

const routed: TitanInput = {
  prompt: 'inspect the repo',
  workdir: '/tmp/example',
  context: {
    systemPrompt: 'You are Talos of Mount Othrys.',
    mode: 'talos',
    phase: 'execute',
  },
}

/** Captures what an adapter actually asked the model for, without a network call. */
function recordingProvider(): { provider: LLMProvider; requests: LLMRequest[] } {
  const requests: LLMRequest[] = []
  const provider: LLMProvider = {
    name: 'recording',
    async complete(request) {
      requests.push(request)
      return { content: 'ok', model: 'recording', metadata: {} }
    },
  }
  return { provider, requests }
}

function systemMessageOf(requests: LLMRequest[]): string {
  return requests[0]?.messages.find(message => message.role === 'system')?.content ?? ''
}

const sandbox = mkdtempSync(join(tmpdir(), 'othrys-context-'))
afterAll(() => rmSync(sandbox, { recursive: true, force: true }))

describe('engine context propagation (MF-1)', () => {
  it('builds an envelope from the routed mode and workflow context', () => {
    expect(buildEngineContext(talos, routed)).toEqual({
      mode: 'talos',
      phase: 'execute',
      systemPrompt: 'You are Talos of Mount Othrys.',
    })
  })

  it('omits absent fields instead of emitting empty ones', () => {
    expect(buildEngineContext(talos, { prompt: 'hi' })).toEqual({ mode: 'talos' })
  })

  it('passes the envelope through the environment rather than argv', () => {
    const invocation = buildTitanInvocation(talos, routed, '/repo', {}, {})
    const decoded = JSON.parse(invocation.env[CONTEXT_ENV_VAR] as string)

    expect(decoded.systemPrompt).toBe('You are Talos of Mount Othrys.')
    expect(invocation.args).not.toContain('You are Talos of Mount Othrys.')
  })

  it('keeps global flags ahead of the Titan subcommand', () => {
    const invocation = buildTitanInvocation(talos, routed, '/repo', {}, {})
    expect(invocation.args.slice(0, 3)).toEqual(['-m', 'talos', '--json'])
  })

  it('runs the worker in the mission workdir', () => {
    expect(buildTitanInvocation(talos, routed, '/repo', {}, {}).cwd).toBe('/tmp/example')
    expect(buildTitanInvocation(talos, { prompt: 'hi' }, '/repo', {}, {}).cwd).toBe('/repo')
  })

  it('prepends the engine directive without discarding the worker prompt', () => {
    const composed = resolveSystemPrompt('WORKER PROMPT', routed.context)

    expect(composed).toBe(`You are Talos of Mount Othrys.${DIRECTIVE_SEPARATOR}WORKER PROMPT`)
    expect(composed).toContain('WORKER PROMPT')
  })

  it('leaves the worker prompt untouched when the engine sends no directive', () => {
    expect(resolveSystemPrompt('WORKER PROMPT', undefined)).toBe('WORKER PROMPT')
    expect(resolveSystemPrompt('WORKER PROMPT', { mode: 'talos' })).toBe('WORKER PROMPT')
  })

  it('native adapters merge the routed directive instead of replacing their own prompt', async () => {
    const { provider, requests } = recordingProvider()
    const adapter = new ThemisAdapter({ apiKey: 'unused', provider })

    const result = await adapter.execute({
      prompt: 'review this design',
      context: { systemPrompt: 'You are Themis of Mount Othrys: strategic technical advisor.' },
    })

    expect(result.passed).toBe(true)
    const system = systemMessageOf(requests)
    expect(system).toContain('You are Themis of Mount Othrys: strategic technical advisor.')
    expect(system).toContain('Strategic Technical Advisor')
    expect(system).toContain(DIRECTIVE_SEPARATOR)
  })

  it('native adapters keep their own prompt when no directive is routed', async () => {
    const { provider, requests } = recordingProvider()
    const adapter = new HeraclesAdapter({ apiKey: 'unused', provider })

    await adapter.execute({ prompt: 'finish this now' })

    const system = systemMessageOf(requests)
    expect(system).toContain('<ultrawork-mode>')
    expect(system).not.toContain(DIRECTIVE_SEPARATOR)
  })

  it('delivers the envelope to a real child process', async () => {
    const script = join(sandbox, 'echo-context.sh')
    writeFileSync(script, `#!/bin/sh\nprintf "%s" "$OTHRYS_CONTEXT"\n`, 'utf8')
    chmodSync(script, 0o755)

    const titan: TitanConfig = { ...talos, pythonBinary: script }
    const result = await spawnPythonTitan(
      titan,
      { ...routed, workdir: sandbox },
      '/repo',
      {},
      {},
    )

    expect(result.passed).toBe(true)
    expect(JSON.parse(result.output)).toEqual({
      mode: 'talos',
      phase: 'execute',
      systemPrompt: 'You are Talos of Mount Othrys.',
    })
  })
})