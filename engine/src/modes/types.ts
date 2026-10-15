export enum TitanMode {
  HERACLES = 'heracles',
  TALOS = 'talos',
  COEUS = 'coeus',
  THEMIS = 'themis',
  ATLAS = 'atlas',
  IAPETUS = 'iapetus',
  KRONOS = 'kronos',
}

export enum TitanRole {
  EXECUTOR = 'executor',
  PLANNER = 'planner',
  ADVISOR = 'advisor',
  ORCHESTRATOR = 'orchestrator',
}

export enum WorkflowPhase {
  ROUTE = 'route',
  PLAN = 'plan',
  ADVISE = 'advise',
  EXECUTE = 'execute',
  ORCHESTRATE = 'orchestrate',
  VERIFY = 'verify',
}

export interface TitanConfig {
  mode: TitanMode
  name: string
  role: TitanRole
  description: string
  adapterType: 'python' | 'native' | 'llm'
  pythonModule?: string
  pythonBinary?: string
  defaultSubcommand: string

  /**
   * Regex triggers used by Router, sourced from the canonical routing table
   * (MF-2). Precedence is by `routingPriority`, not declaration order.
   */
  triggers: RegExp[]

  /**
   * Human-readable trigger keywords for CLI display and simple consumers.
   * Derived from the canonical routing table alongside `triggers`.
   */
  keywords: string[]

  /**
   * Relative routing precedence, sourced from the canonical routing table
   * (MF-2). The highest matching weight wins; ties fall back to registry order.
   * Absent for caller-supplied registries, where 0 is assumed.
   */
  routingPriority?: number

  /**
   * Full system prompt injected into native/LLM execution.
   */
  systemPrompt: string

  /**
   * Tool permission policy.
   */
  toolAccess: string[]
  toolBlocked: string[]
  writablePaths: string[]

  requiresPlan: boolean
  requiresVerification: boolean

  model?: string
  temperature: number
  thinkingBudget: number
  maxTokens: number
}

/**
 * A Titan's static definition without its routing data.
 *
 * `triggers`, `keywords`, and `routingPriority` are injected by the registry from
 * the canonical routing table (MF-2), so they exist in exactly one place and the
 * mode files cannot drift from what the router actually does.
 */
export type TitanModeSpec = Omit<TitanConfig, 'triggers' | 'keywords' | 'routingPriority'>

export interface RouteResult {
  mode: TitanMode
  reason: string
  config: TitanConfig
}

export interface VerificationCheck {
  name: string
  passed: boolean
  detail: string
}

export interface VerificationResult {
  passed: boolean
  checks: VerificationCheck[]
}

export interface WorkflowResult {
  mode: TitanMode
  phase: WorkflowPhase
  output: string
  metadata: Record<string, unknown>
  verification: VerificationResult
}
