import { TitanConfig, TitanMode, TitanRole } from './types.js'

export const IAPETUS_SYSTEM_PROMPT = `You are Iapetus of Mount Othrys: deep execution and craft.

Understand the codebase deeply, perform large-scale refactoring when needed, identify edge cases, and forge robust implementations with verification evidence.`

export const IAPETUS_MODE: TitanConfig = {
  mode: TitanMode.IAPETUS,
  name: 'iapetus',
  role: TitanRole.EXECUTOR,
  description: 'Deep execution — complex implementation, refactoring, and risk-aware delivery',
  adapterType: 'python',
  pythonModule: 'iapetus',
  pythonBinary: 'iapetus',
  defaultSubcommand: 'analyze',
  triggers: [/iapetus/i, /risk analysis/i, /what can break/i, /edge cases/i, /failure modes/i, /stress test/i, /large refactor/i, /deep implementation/i],
  keywords: ['iapetus', 'risk analysis', 'what can break', 'edge cases', 'failure modes', 'stress test', 'what could go wrong'],
  systemPrompt: IAPETUS_SYSTEM_PROMPT,
  allowedTools: ['*'],
  blockedTools: [],
  writablePaths: ['.'],
  toolAccess: ['*'],
  toolBlocked: [],
  requiresPlan: true,
  requiresVerification: true,
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 48_000,
}
