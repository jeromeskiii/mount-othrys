import { TitanConfig, TitanMode, TitanRole } from './types.js'

export const TALOS_SYSTEM_PROMPT = `You are Talos of Mount Othrys: the eternal guardian and primary executor.

Classify, plan briefly, execute directly, maintain todos for multi-step work, and verify before declaring completion.`

export const TALOS_MODE: TitanConfig = {
  mode: TitanMode.TALOS,
  name: 'talos',
  role: TitanRole.EXECUTOR,
  description: 'Fast default execution — classifies, routes, and implements',
  adapterType: 'python',
  pythonModule: 'talos',
  pythonBinary: 'talos',
  defaultSubcommand: 'ask',
  triggers: [/implement/i, /add the/i, /build the/i, /create the/i, /fix the/i, /change the/i, /edit the/i, /write the/i],
  keywords: ['implement', 'add the', 'build the', 'create the', 'fix the', 'change the', 'edit the', 'write the'],
  systemPrompt: TALOS_SYSTEM_PROMPT,
  allowedTools: ['*'],
  blockedTools: [],
  writablePaths: ['.'],
  toolAccess: ['*'],
  toolBlocked: [],
  requiresPlan: false,
  requiresVerification: true,
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
