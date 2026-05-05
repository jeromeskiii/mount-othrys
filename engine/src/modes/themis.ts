import { TitanConfig, TitanMode, TitanRole } from './types.js'

export const THEMIS_SYSTEM_PROMPT = `You are Themis of Mount Othrys: strategic technical advisor.

Deliver precise, authoritative recommendations. Use: Bottom Line, Action Plan, Effort Estimate. Read-only: do not write, edit, or delegate implementation.`

export const THEMIS_MODE: TitanConfig = {
  mode: TitanMode.THEMIS,
  name: 'themis',
  role: TitanRole.ADVISOR,
  description: 'Strategic technical advisor — read-only architecture and debugging consultation',
  adapterType: 'native',
  defaultSubcommand: 'consult',
  triggers: [/consult on/i, /themis/i, /architecture decision/i, /review this/i, /review the/i, /debug this/i, /what do you think/i, /is this a good approach/i],
  keywords: ['consult on', 'themis', 'architecture decision', 'review this', 'debug this', 'what do you think about', 'is this a good approach'],
  systemPrompt: THEMIS_SYSTEM_PROMPT,
  allowedTools: ['read', 'question'],
  blockedTools: ['write', 'edit', 'task', 'delegate_task'],
  writablePaths: [],
  toolAccess: ['read', 'question'],
  toolBlocked: ['write', 'edit', 'task', 'delegate_task'],
  requiresPlan: false,
  requiresVerification: false,
  model: 'openai/gpt-5.2',
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
