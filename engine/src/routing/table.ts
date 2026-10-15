/**
 * Routing table loader (MF-2).
 *
 * The canonical table lives in the `othrys` Python package
 * (`othrys/src/othrys/routing.table.json`) because that package is the one
 * shared artifact both languages already ship and install; `othrys.routing`
 * exposes the identical precedence rules to Python consumers. Keeping the table
 * inside a shipped package means the wheel carries it automatically, so an
 * installed Titan and the engine cannot drift.
 *
 * The table is read at runtime (not imported) because it sits outside this
 * package's `rootDir`, which TypeScript cannot import without breaking the
 * `tsc` emit. `zod` validates it on load so a malformed edit fails loudly
 * instead of silently changing routing behaviour.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { z } from 'zod'

const RoutingPatternSchema = z.object({
  pattern: z.string().min(1),
  flags: z.string().default(''),
})

const RoutingEntrySchema = z.object({
  id: z.string().min(1),
  titan: z.string().min(1),
  weight: z.number().int(),
  description: z.string().default(''),
  patterns: z.array(RoutingPatternSchema).min(1),
})

const RoutingExampleSchema = z.object({
  message: z.string().min(1),
  titan: z.string().min(1),
})

const RoutingTableSchema = z.object({
  version: z.number().int(),
  entries: z.array(RoutingEntrySchema).min(1),
  examples: z.array(RoutingExampleSchema).default([]),
})

export interface RoutingPattern {
  readonly source: string
  readonly flags: string
  readonly regex: RegExp
}

export interface RoutingEntry {
  readonly id: string
  readonly titan: string
  readonly weight: number
  readonly description: string
  readonly patterns: readonly RoutingPattern[]
}

export interface RoutingExample {
  readonly message: string
  readonly titan: string
}

export interface RoutingMatch {
  readonly titan: string
  readonly entryId: string
  readonly weight: number
  readonly pattern: string
  readonly reason: string
}

/** Resolved from both `src/routing/` and `dist/routing/`, i.e. three levels up. */
const TABLE_PATH = resolve(
  import.meta.dirname ?? process.cwd(),
  '../../../othrys/src/othrys/routing.table.json',
)

let cache: { entries: RoutingEntry[]; examples: RoutingExample[] } | undefined

export function loadRoutingTable(): { entries: RoutingEntry[]; examples: RoutingExample[] } {
  if (cache) return cache

  let raw: string
  try {
    raw = readFileSync(TABLE_PATH, 'utf8')
  } catch (cause) {
    throw new Error(
      `Cannot read the canonical routing table at ${TABLE_PATH}. ` +
        `Mount Othrys expects othrys/src/othrys/routing.table.json to sit alongside this package.`,
      { cause },
    )
  }

  const parsed = RoutingTableSchema.parse(JSON.parse(raw))

  const entries = parsed.entries.map(
    (entry): RoutingEntry => ({
      id: entry.id,
      titan: entry.titan,
      weight: entry.weight,
      description: entry.description,
      patterns: entry.patterns.map(
        (pattern): RoutingPattern => ({
          source: pattern.pattern,
          flags: pattern.flags,
          regex: new RegExp(pattern.pattern, pattern.flags),
        }),
      ),
    }),
  )

  cache = { entries, examples: parsed.examples }
  return cache
}

/** Titan keys the table knows about, in precedence order, without duplicates. */
export function routingTitans(): string[] {
  const seen = new Set<string>()
  for (const entry of loadRoutingTable().entries) seen.add(entry.titan)
  return [...seen]
}

/** The golden (message, titan) corpus, shared with the Python test suite. */
export function routingExamples(): RoutingExample[] {
  return loadRoutingTable().examples
}

/**
 * Highest matching weight wins; ties resolve to the earliest entry. Mirrors
 * `othrys.routing.match_rule` exactly — keep the two in step.
 */
export function matchRoutingRule(message: string): RoutingMatch | undefined {
  let bestEntry: RoutingEntry | undefined
  let bestPattern: RoutingPattern | undefined

  for (const entry of loadRoutingTable().entries) {
    if (bestEntry && entry.weight <= bestEntry.weight) continue
    for (const pattern of entry.patterns) {
      if (pattern.regex.test(message)) {
        bestEntry = entry
        bestPattern = pattern
        break
      }
    }
  }

  if (!bestEntry || !bestPattern) return undefined

  return {
    titan: bestEntry.titan,
    entryId: bestEntry.id,
    weight: bestEntry.weight,
    pattern: bestPattern.source,
    reason: `Canonical rule '${bestEntry.id}' matched /${bestPattern.source}/ → ${bestEntry.titan}`,
  }
}