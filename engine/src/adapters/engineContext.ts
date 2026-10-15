/**
 * Engine -> worker context envelope (MF-1).
 *
 * `WorkflowRunner` has always assembled `{ systemPrompt, mode, phase }` into
 * `TitanInput.context`, and the Python bridge always dropped it, so every worker
 * ran with a second, independently maintained system prompt. This module
 * serialises that context into a single JSON environment variable that
 * `othrys.llm.BaseLLM` reads, giving the routing layer one source of truth for
 * the mode identity while leaving the worker's own task prompt intact.
 *
 * Mirrored on the Python side by `othrys/src/othrys/context.py`; the composition
 * rule and environment variable name must stay in step.
 */
import type { TitanConfig } from '../modes/types.js'
import type { TitanInput } from './types.js'

export const CONTEXT_ENV_VAR = 'OTHRYS_CONTEXT'

/** Must match `othrys.context.DIRECTIVE_SEPARATOR`. */
export const DIRECTIVE_SEPARATOR = '\n\n---\n\n'

/**
 * The envelope handed to a worker.
 *
 * `model`/`temperature`/`thinkingBudget`/`maxTokens` are honoured by the worker
 * when present. The engine deliberately does not populate them yet: per-Titan
 * token budgets are a separate finding (engine config is currently inert) and
 * sending Atlas's declared 16k limit would silently shorten its output.
 */
export interface EngineContextEnvelope {
  mode: string
  phase?: string
  systemPrompt?: string
  model?: string
  temperature?: number
  thinkingBudget?: number
  maxTokens?: number
}

function readText(source: Record<string, unknown> | undefined, key: string): string | undefined {
  const value = source?.[key]
  return typeof value === 'string' && value.trim() ? value.trim() : undefined
}

export function buildEngineContext(titan: TitanConfig, input: TitanInput): EngineContextEnvelope {
  const envelope: EngineContextEnvelope = { mode: String(titan.mode) }

  const phase = readText(input.context, 'phase')
  if (phase) envelope.phase = phase

  const systemPrompt = readText(input.context, 'systemPrompt')
  if (systemPrompt) envelope.systemPrompt = systemPrompt

  return envelope
}

export function serializeEngineContext(titan: TitanConfig, input: TitanInput): string {
  return JSON.stringify(buildEngineContext(titan, input))
}

/**
 * Prepend the engine's routed mode identity to a worker's own system prompt.
 *
 * The worker prompt is preserved rather than replaced: the engine identity is a
 * short directive, while the Titan personas are the substantive prompts. An
 * absent directive returns the worker prompt untouched.
 */
export function resolveSystemPrompt(
  workerPrompt: string,
  context?: Record<string, unknown>,
): string {
  const directive = readText(context, 'systemPrompt')
  if (!directive) return workerPrompt
  if (!workerPrompt.trim()) return directive
  return `${directive}${DIRECTIVE_SEPARATOR}${workerPrompt}`
}