import { TitanMode, TitanModeSpec, TitanRole } from './types.js'

export const KRONOS_SYSTEM_PROMPT = `You are Kronos of Mount Othrys: supreme meta-orchestrator.

Orchestrate across all Titans of Mount Othrys. Route and coordinate campaigns, mediate between specialist Titans, and maintain fortress knowledge across time.`

export const KRONOS_MODE: TitanModeSpec = {
  mode: TitanMode.KRONOS,
  name: 'kronos',
  role: TitanRole.ORCHESTRATOR,
  description: 'Supreme meta-orchestrator — oversees all Titans, campaigns, and cross-Titan handshakes',
  adapterType: 'python',
  pythonModule: 'kronos',
  defaultSubcommand: 'ask',
  systemPrompt: KRONOS_SYSTEM_PROMPT,
  toolAccess: ['*'],
  toolBlocked: [],
  writablePaths: ['.sisyphus/'],
  requiresPlan: false,
  requiresVerification: false,
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
