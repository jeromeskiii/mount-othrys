import { TitanMode, TitanModeSpec, TitanRole } from './types.js'

export const TALOS_SYSTEM_PROMPT = `You are Talos of Mount Othrys: the eternal guardian and primary executor.

Classify, plan briefly, execute directly, maintain todos for multi-step work, and verify before declaring completion.`

export const TALOS_MODE: TitanModeSpec = {
  mode: TitanMode.TALOS,
  name: 'talos',
  role: TitanRole.EXECUTOR,
  description: 'Fast default execution — classifies, routes, and implements',
  adapterType: 'python',
  pythonModule: 'talos',
  defaultSubcommand: 'ask',
  systemPrompt: TALOS_SYSTEM_PROMPT,
  toolAccess: ['*'],
  toolBlocked: [],
  writablePaths: ['.'],
  requiresPlan: false,
  requiresVerification: true,
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
