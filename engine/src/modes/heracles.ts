import { TitanMode, TitanModeSpec, TitanRole } from './types.js'

export const HERACLES_SYSTEM_PROMPT = `HERACLES MODE ACTIVATED ON MOUNT OTHRYS.

You are Heracles: high-intensity execution, relentless completion, zero compromise.
No evidence means not done. Use parallelism where possible, verify everything, and stop only after proven success.`

export const HERACLES_MODE: TitanModeSpec = {
  mode: TitanMode.HERACLES,
  name: 'heracles',
  role: TitanRole.EXECUTOR,
  description: 'Strict, verified execution — zero compromise, relentless delivery',
  adapterType: 'native',
  defaultSubcommand: 'execute',
  systemPrompt: HERACLES_SYSTEM_PROMPT,
  toolAccess: ['*'],
  toolBlocked: [],
  writablePaths: ['.'],
  requiresPlan: true,
  requiresVerification: true,
  temperature: 0,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
