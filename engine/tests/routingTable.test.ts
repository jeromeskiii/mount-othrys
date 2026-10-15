import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { Router } from '../src/router'
import { LEGACY_ALIASES, TITAN_REGISTRY } from '../src/modes/registry'
import { TitanMode, TitanRole } from '../src/modes/types'
import type { TitanConfig } from '../src/modes/types'
import { loadRoutingTable, routingExamples, routingTitans } from '../src/routing/table'

/**
 * A minimal registry used to pin the precedence rules themselves, independently
 * of whatever the real table happens to contain.
 */
function stubRegistry(order: Array<[string, number]>): Record<string, TitanConfig> {
  const entries = order.map(([name, routingPriority]) => [
    name,
    {
      mode: TitanMode.TALOS,
      name,
      role: TitanRole.EXECUTOR,
      description: 'stub',
      adapterType: 'python',
      defaultSubcommand: 'ask',
      triggers: [/same/],
      keywords: [],
      systemPrompt: 'stub',
      toolAccess: [],
      toolBlocked: [],
      writablePaths: [],
      requiresPlan: false,
      requiresVerification: false,
      temperature: 0,
      thinkingBudget: 1,
      maxTokens: 1,
      routingPriority,
    },
  ])
  return Object.fromEntries(entries) as unknown as Record<string, TitanConfig>
}

describe('canonical routing table (MF-2)', () => {
  it('is the only source of triggers and precedence for the registry', () => {
    const { entries } = loadRoutingTable()

    for (const [key, config] of Object.entries(TITAN_REGISTRY)) {
      const entry = entries.find(candidate => candidate.titan === key)
      expect(entry, `no routing entry for ${key}`).toBeDefined()
      expect(config.triggers.map(trigger => trigger.source)).toEqual(
        entry!.patterns.map(pattern => pattern.source),
      )
      expect(config.routingPriority).toBe(entry!.weight)
    }
  })

  it('declares a table entry for exactly the registered Titans', () => {
    expect([...routingTitans()].sort()).toEqual(Object.keys(TITAN_REGISTRY).sort())
  })

  it('routes every golden example from the shared corpus', () => {
    const examples = routingExamples()
    expect(examples.length).toBeGreaterThanOrEqual(20)

    const mismatches = examples
      .map(example => ({
        ...example,
        actual: new Router().route(example.message).config.name.toLowerCase(),
      }))
      .filter(result => result.actual !== result.titan)

    expect(mismatches).toEqual([])
  })

  it('matches the routing table documented in README.md', () => {
    const readme = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), '../../README.md'), 'utf8')
    const rows = [...readme.matchAll(/^\|\s*"([^"]+)"\s*\|\s*([A-Za-z]+)[^|]*\|/gm)]

    // Guard against the regex silently matching nothing if the docs change shape.
    expect(rows.length).toBeGreaterThanOrEqual(8)

    for (const [, message, documented] of rows) {
      const expected = LEGACY_ALIASES[documented.toLowerCase()] ?? documented.toLowerCase()
      expect(new Router().route(message).config.name.toLowerCase(), `README row "${message}"`).toBe(
        expected,
      )
    }
  })

  it('does not let a generic trigger shadow a more specific one', () => {
    // Regression: Talos's generic /implement/ sat earlier in the registry than
    // Iapetus, so this always resolved to Talos even though the README promised
    // Iapetus.
    const result = new Router().route('Implement this complex work')

    expect(result.config.name).toBe('iapetus')
    expect(result.config.routingPriority!).toBeGreaterThan(
      TITAN_REGISTRY.talos.routingPriority!,
    )
  })

  it('resolves the same way regardless of registry key order', () => {
    const forward = new Router().route('Implement this complex work').mode
    const reversed = new Router({
      registry: Object.fromEntries(Object.entries(TITAN_REGISTRY).reverse()),
    }).route('Implement this complex work').mode

    expect(reversed).toBe(forward)
  })

  it('prefers the higher weight over registry order', () => {
    const router = new Router({ registry: stubRegistry([['alpha', 10], ['beta', 90]]) })
    expect(router.route('same').config.name).toBe('beta')
  })

  it('breaks equal weights by table order', () => {
    const first = new Router({ registry: stubRegistry([['alpha', 50], ['beta', 50]]) })
    const second = new Router({ registry: stubRegistry([['beta', 50], ['alpha', 50]]) })

    expect(first.route('same').config.name).toBe('alpha')
    expect(second.route('same').config.name).toBe('beta')
  })

  it('still falls through to the default Titan when nothing matches', () => {
    const result = new Router().route('zzzz no intent here')
    expect(result.config.name).toBe('talos')
    expect(result.reason).toMatch(/Default to/)
  })
})