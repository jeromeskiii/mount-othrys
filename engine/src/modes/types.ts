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
   * Regex triggers used by Router. Order matters: first matching Titan wins.
   */
  triggers: RegExp[]

  /**
   * Backward-compatible keyword list for CLI display and simple consumers.
   */
  keywords: string[]

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
