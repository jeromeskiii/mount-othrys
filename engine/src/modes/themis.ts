import { TitanMode, TitanModeSpec, TitanRole } from './types.js'

export const THEMIS_SYSTEM_PROMPT = `You are Themis of Mount Othrys: strategic technical advisor.

Deliver precise, authoritative recommendations. Use: Bottom Line, Action Plan, Effort Estimate. Read-only: do not write, edit, or delegate implementation.`

export const THEMIS_MODE: TitanModeSpec = {
  mode: TitanMode.THEMIS,
  name: 'themis',
  role: TitanRole.ADVISOR,
  description: 'Strategic technical advisor — read-only architecture and debugging consultation',
  adapterType: 'native',
  defaultSubcommand: 'consult',
  systemPrompt: THEMIS_SYSTEM_PROMPT,
  toolAccess: ['read', 'question'],
  toolBlocked: ['write', 'edit', 'task', 'delegate_task'],
  writablePaths: [],
  requiresPlan: false,
  requiresVerification: false,
  model: 'gpt-4o',
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
