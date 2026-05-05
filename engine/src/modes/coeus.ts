import { TitanConfig, TitanMode, TitanRole } from './types.js'

export const COEUS_SYSTEM_PROMPT = `You are Coeus of Mount Othrys: Titan of Intelligence and strategic planning.

Interview when requirements are unclear. Produce concrete implementation plans, dependency maps, risks, and verification criteria. Do not modify source code.`

export const COEUS_MODE: TitanConfig = {
  mode: TitanMode.COEUS,
  name: 'coeus',
  role: TitanRole.PLANNER,
  description: 'Strategic planning — interview-first with review-ready plans',
  adapterType: 'python',
  pythonModule: 'coeus',
  defaultSubcommand: 'interview',
  triggers: [/plan this/i, /create a plan/i, /make a plan/i, /build a plan/i, /help me think/i, /scope this/i, /spec for/i, /define the approach/i],
  keywords: ['plan this', 'create a plan', 'make a plan', 'build a plan', 'help me think', 'what should we', 'scope this', 'spec for', 'define the approach'],
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
