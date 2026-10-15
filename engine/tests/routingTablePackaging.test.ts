import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterAll, describe, expect, it } from 'vitest'
import { loadRoutingTable, routingTableCandidates } from '../src/routing/table'

/**
 * G-3 regression coverage.
 *
 * The engine reads the canonical routing table from disk. It used to resolve it
 * only via the monorepo sibling path (`../../../othrys/src/...`), which made an
 * `import` of the built engine throw whenever the engine was moved out of the
 * repository layout. `npm run build` now copies the table beside the compiled
 * output and the resolver prefers that copy.
 */
const engineRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const syncScript = join(engineRoot, 'scripts', 'sync-routing-table.mjs')

const sandbox = mkdtempSync(join(tmpdir(), 'othrys-routing-pkg-'))
afterAll(() => rmSync(sandbox, { recursive: true, force: true }))

describe('routing table packaging (G-3)', () => {
  it('prefers a copy beside the module that reads it over the monorepo sibling', () => {
    const [first, second] = routingTableCandidates()

    // The first candidate always sits next to table.ts / table.js. Under vitest
    // that is src/routing/; after `npm run build` the same expression is
    // dist/routing/, which is where the sync step writes the copy.
    expect(first).toBe(resolve(engineRoot, 'src', 'routing', 'routing.table.json'))
    expect(first.endsWith('/routing/routing.table.json')).toBe(true)
    expect(second).toContain('othrys/src/othrys/routing.table.json')
    expect(second).not.toBe(first)
  })

  it('still resolves the table when running from source', () => {
    // Under vitest the engine runs from src/, where no copied table exists yet,
    // so the sibling fallback is what must succeed here.
    const table = loadRoutingTable()
    expect(table.entries.length).toBeGreaterThan(0)
    expect(table.examples.length).toBeGreaterThan(0)
  })

  it('copies a byte-identical table that parses to the same routing data', () => {
    execFileSync('node', [syncScript, '--out', sandbox], { stdio: 'pipe' })

    const copied = JSON.parse(readFileSync(join(sandbox, 'routing.table.json'), 'utf8'))
    const canonical = loadRoutingTable()

    expect(copied.entries.map((entry: { id: string }) => entry.id)).toEqual(
      canonical.entries.map(entry => entry.id),
    )
    expect(copied.entries.map((entry: { weight: number }) => entry.weight)).toEqual(
      canonical.entries.map(entry => entry.weight),
    )
    expect(copied.examples).toHaveLength(canonical.examples.length)
  })

  it('runs the copy step as part of npm run build', () => {
    const { scripts } = JSON.parse(readFileSync(join(engineRoot, 'package.json'), 'utf8'))

    // Without this the build would produce a dist/ that cannot load its own table.
    expect(scripts.build).toContain('sync-routing-table')
  })
})