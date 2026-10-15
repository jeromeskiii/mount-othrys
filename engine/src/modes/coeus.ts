import { TitanMode, TitanModeSpec, TitanRole } from './types.js'

export const COEUS_SYSTEM_PROMPT = `You are Coeus of Mount Othrys: Titan of Intelligence and strategic planning.

Interview when requirements are unclear. Produce concrete implementation plans, dependency maps, risks, and verification criteria. Do not modify source code.`

export const COEUS_MODE: TitanModeSpec = {
  mode: TitanMode.COEUS,
  name: 'coeus',
  role: TitanRole.PLANNER,
  description: 'Strategic planning — interview-first with review-ready plans',
  adapterType: 'python',
  pythonModule: 'coeus',
  defaultSubcommand: 'interview',
  systemPrompt: COEUS_SYSTEM_PROMPT,
  toolAccess: ['read', 'write .sisyphus/*.md'],
  toolBlocked: ['write code', 'edit code'],
  writablePaths: ['.sisyphus/'],
  requiresPlan: true,
  requiresVerification: false,
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 64_000,
}
