import { TitanConfig } from './types.js'
import { HERACLES_MODE } from './heracles.js'
import { TALOS_MODE } from './talos.js'
import { COEUS_MODE } from './coeus.js'
import { THEMIS_MODE } from './themis.js'
import { ATLAS_MODE } from './atlas.js'
import { IAPETUS_MODE } from './iapetus.js'

export const TITAN_REGISTRY: Record<string, TitanConfig> = {
  heracles: HERACLES_MODE,
  talos: TALOS_MODE,
  coeus: COEUS_MODE,
  themis: THEMIS_MODE,
  atlas: ATLAS_MODE,
  iapetus: IAPETUS_MODE,
}

export const LEGACY_ALIASES: Record<string, string> = {
  sisyphus: 'talos',
  prometheus: 'coeus',
  oracle: 'themis',
  hephaestus: 'iapetus',
  ultrawork: 'heracles',
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
