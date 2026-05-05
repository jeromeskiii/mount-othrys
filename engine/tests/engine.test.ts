import { describe, expect, it } from 'vitest'
import { ModeEngine } from '../src/engine/ModeEngine'
import { EventBus } from '../src/engine/EventBus'
import { TitanMode, WorkflowPhase } from '../src/modes/types'
import type { TitanAdapter, TitanInput, TitanOutput } from '../src/adapters/types'

class FakeAdapter implements TitanAdapter {
  name = 'Fake Talos'
  mode = TitanMode.TALOS

  async execute(input: TitanInput): Promise<TitanOutput> {
    return {
      output: `executed: ${input.prompt}`,
      metadata: { fake: true },
      passed: true,
      checks: [],
    }
  }
}

describe('ModeEngine', () => {
  it('routes and executes through WorkflowRunner', async () => {
    const adapters = new Map<string, TitanAdapter>([
      [TitanMode.TALOS, new FakeAdapter()],
    ])

    const engine = new ModeEngine({
      adapters,
      rootDir: process.cwd(),
    })

    const result = await engine.run('hello')
    expect(result.mode).toBe(TitanMode.TALOS)
    expect(result.phase).toBe(WorkflowPhase.EXECUTE)
    expect(result.output).toContain('executed: hello')
  })

  it('emits route and workflow events', async () => {
    const events: string[] = []
    const eventBus = new EventBus()
    eventBus.on('route:start', () => events.push('route:start'))
    eventBus.on('route:complete', () => events.push('route:complete'))
    eventBus.on('workflow:complete', () => events.push('workflow:complete'))

    const adapters = new Map<string, TitanAdapter>([
      [TitanMode.TALOS, new FakeAdapter()],
    ])

    const engine = new ModeEngine({
      adapters,
      eventBus,
      rootDir: process.cwd(),
      workdir: undefined,
    })

    await engine.run('hello')

    expect(events).toEqual(['route:start', 'route:complete', 'workflow:complete'])
  })

  it('uses explicit titan override', async () => {
    const adapters = new Map<string, TitanAdapter>([
      [TitanMode.TALOS, new FakeAdapter()],
    ])

    const engine = new ModeEngine({
      adapters,
      rootDir: process.cwd(),
    })

    const result = await engine.run('anything', { titanOverride: 'talos' })
    expect(result.mode).toBe(TitanMode.TALOS)
  })
})
