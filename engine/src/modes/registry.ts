import { TitanConfig, TitanModeSpec } from './types.js'
import { HERACLES_MODE } from './heracles.js'
import { TALOS_MODE } from './talos.js'
import { COEUS_MODE } from './coeus.js'
import { THEMIS_MODE } from './themis.js'
import { ATLAS_MODE } from './atlas.js'
import { IAPETUS_MODE } from './iapetus.js'
import { KRONOS_MODE } from './kronos.js'
import { loadRoutingTable, routingTitans } from '../routing/table.js'

/**
 * Static per-Titan definitions. Routing data (triggers, keywords, precedence)
 * lives in the canonical routing table and is injected below, so there is one
 * source of truth for how a request reaches a Titan (MF-2).
 */
const MODE_SPECS: Record<string, TitanModeSpec> = {
  heracles: HERACLES_MODE,
  talos: TALOS_MODE,
  coeus: COEUS_MODE,
  themis: THEMIS_MODE,
  atlas: ATLAS_MODE,
  iapetus: IAPETUS_MODE,
  kronos: KRONOS_MODE,
}

function buildRegistry(): Record<string, TitanConfig> {
  const { entries } = loadRoutingTable()
  const registry: Record<string, TitanConfig> = {}

  for (const [key, spec] of Object.entries(MODE_SPECS)) {
    const entry = entries.find(candidate => candidate.titan === key)
    if (!entry) {
      throw new Error(
        `Canonical routing table has no entry for Titan '${key}'. ` +
          `Declared Titans: ${Object.keys(MODE_SPECS).join(', ')}; table Titans: ${routingTitans().join(', ')}`,
      )
    }
    registry[key] = {
      ...spec,
      triggers: entry.patterns.map(pattern => pattern.regex),
      keywords: entry.patterns.map(pattern => pattern.source),
      routingPriority: entry.weight,
    }
  }

  return registry
}

/**
 * Built once at import time from the canonical table. An unreadable or
 * malformed table fails loudly here rather than silently changing routing, so
 * the engine cannot start with a partially configured router.
 */
export const TITAN_REGISTRY: Record<string, TitanConfig> = buildRegistry()

export const LEGACY_ALIASES: Record<string, string> = {
  sisyphus: 'talos',
  prometheus: 'coeus',
  oracle: 'themis',
  hephaestus: 'iapetus',
  ultrawork: 'heracles',
  coordinator: 'kronos',
}

export function getTitan(name: string, registry: Record<string, TitanConfig> = TITAN_REGISTRY): TitanConfig {
  const key = name.toLowerCase().trim()
  const resolved = LEGACY_ALIASES[key] ?? key
  const config = registry[resolved]
  if (!config) {
    throw new Error(`Unknown Titan: ${name}. Available: ${Object.keys(registry).join(', ')}`)
  }
  return config
}

export function listTitans(registry: Record<string, TitanConfig> = TITAN_REGISTRY): TitanConfig[] {
  return Object.values(registry)
}
