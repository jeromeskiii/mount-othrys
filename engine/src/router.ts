import { TitanConfig, RouteResult } from './modes/types.js'
import { TITAN_REGISTRY, LEGACY_ALIASES } from './modes/registry.js'

export interface RouterOptions {
  registry?: Record<string, TitanConfig>
  defaultMode?: string
}

export class Router {
  private registry: Record<string, TitanConfig>
  private defaultMode: string

  constructor(options: RouterOptions = {}) {
    this.registry = options.registry ?? TITAN_REGISTRY
    this.defaultMode = options.defaultMode ?? 'talos'
  }

  route(message: string): RouteResult {
    // MF-2: precedence comes from the canonical table's routingPriority instead
    // of declaration order, so a generic trigger can no longer shadow a more
    // specific one. Array#sort is stable, so equal priorities keep registry
    // order and the result stays deterministic.
    const candidates = Object.entries(this.registry).sort(
      ([, a], [, b]) => (b.routingPriority ?? 0) - (a.routingPriority ?? 0),
    )

    for (const [key, config] of candidates) {
      for (const trigger of config.triggers) {
        if (trigger.test(message)) {
          trigger.lastIndex = 0
          return {
            mode: config.mode,
            reason: `Trigger match: ${trigger.toString()} → ${key}`,
            config,
          }
        }
      }
    }

    const defaultConfig = this.registry[this.defaultMode]
    if (!defaultConfig) {
      throw new Error(`Default Titan not registered: ${this.defaultMode}`)
    }

    return {
      mode: defaultConfig.mode,
      reason: `Default to ${defaultConfig.name} (primary executor)`,
      config: defaultConfig,
    }
  }

  routeExplicit(titanName: string): RouteResult {
    const key = titanName.toLowerCase().trim()
    const resolved = LEGACY_ALIASES[key] ?? key
    const config = this.registry[resolved]
    if (!config) {
      throw new Error(`Unknown Titan: ${titanName}. Available: ${Object.keys(this.registry).join(', ')}`)
    }

    return {
      mode: config.mode,
      reason: `Explicit override → ${resolved}`,
      config,
    }
  }
}

const defaultRouter = new Router()

export function route(message: string): RouteResult {
  return defaultRouter.route(message)
}

export function routeExplicit(titanName: string): RouteResult {
  return defaultRouter.routeExplicit(titanName)
}
