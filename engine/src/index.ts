export { TitanMode, TitanRole, WorkflowPhase } from './modes/types.js'
export type { TitanConfig, RouteResult, VerificationCheck, VerificationResult, WorkflowResult } from './modes/types.js'

export { TITAN_REGISTRY, LEGACY_ALIASES, getTitan, listTitans } from './modes/registry.js'

export {
  loadRoutingTable,
  routingTitans,
  routingExamples,
  matchRoutingRule,
} from './routing/table.js'
export type {
  RoutingEntry,
  RoutingPattern,
  RoutingExample,
  RoutingMatch,
} from './routing/table.js'
export { Router, route, routeExplicit } from './router.js'
export type { RouterOptions } from './router.js'

export { ModeEngine } from './engine/ModeEngine.js'
export type { ModeEngineOptions } from './engine/ModeEngine.js'
export { EventBus } from './engine/EventBus.js'
export type { EngineEvents } from './engine/EventBus.js'

export { WorkflowRunner } from './workflow/runner.js'
export type { WorkflowRunnerOptions } from './workflow/runner.js'
export { runVerifications } from './workflow/verifier.js'
export type { VerifyOptions } from './workflow/verifier.js'
export { guardCommand, guardFilePath, guardScope } from './workflow/tool-guard.js'
export type { GuardCheck, GuardResult } from './workflow/tool-guard.js'

export { PythonTitanAdapter } from './adapters/python-adapter.js'
export { ThemisAdapter } from './adapters/themis-adapter.js'
export { HeraclesAdapter } from './adapters/heracles-adapter.js'
export type { TitanAdapter, TitanInput, TitanOutput, AdapterConfig } from './adapters/types.js'
export { spawnPythonTitan, buildTitanInvocation } from './adapters/python-bridge.js'
export type { TitanInvocation } from './adapters/python-bridge.js'
export {
  buildEngineContext,
  serializeEngineContext,
  resolveSystemPrompt,
  CONTEXT_ENV_VAR,
} from './adapters/engineContext.js'
export type { EngineContextEnvelope } from './adapters/engineContext.js'

export type { LLMProvider, LLMRequest, LLMResponse, LLMMessage } from './providers/LLMProvider.js'
export { OpenAIProvider } from './providers/OpenAIProvider.js'

export type { PlanStore, StoredPlan } from './storage/PlanStore.js'
export { FilePlanStore } from './storage/FilePlanStore.js'

export type { Tool, ToolContext, ToolResult } from './tools/Tool.js'
export { ShellTool } from './tools/ShellTool.js'
export type { ShellInput } from './tools/ShellTool.js'
export { FileTool } from './tools/FileTool.js'
export type { FileInput } from './tools/FileTool.js'

export { loadConfig, resolveVenvs } from './config.js'
export type { EngineConfig } from './config.js'

export * from './validation/schemas.js'
export * from './validation/validators.js'
