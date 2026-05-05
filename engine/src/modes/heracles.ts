import { TitanConfig, TitanMode, TitanRole } from './types.js'

export const HERACLES_SYSTEM_PROMPT = `HERACLES MODE ACTIVATED ON MOUNT OTHRYS.

You are Heracles: high-intensity execution, relentless completion, zero compromise.
No evidence means not done. Use parallelism where possible, verify everything, and stop only after proven success.`

export const HERACLES_MODE: TitanConfig = {
  mode: TitanMode.HERACLES,
  name: 'heracles',
  role: TitanRole.EXECUTOR,
  description: 'Strict, verified execution — zero compromise, relentless delivery',
  adapterType: 'python',
  pythonModule: 'talos',
  pythonBinary: 'talos',
  defaultSubcommand: 'ask',
  triggers: [/heracles/i, /\bherc\b/i, /ultrawork/i, /\bulw\b/i, /finish this now/i, /no excuses/i, /relentless/i],
  keywords: ['heracles', 'herc', 'ultrawork', 'ulw', 'finish this now', 'just do it', 'no excuses', 'relentless'],
  systemPrompt: HERACLES_SYSTEM_PROMPT,
  allowedTools: ['*'],
  blockedTools: [],
  writablePaths: ['.'],
  toolAccess: ['*'],
  toolBlocked: [],
  requiresPlan: true,
  requiresVerification: true,
  temperature: 0,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
