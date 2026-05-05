import { TitanConfig, TitanMode, TitanRole } from './types.js'

export const ATLAS_SYSTEM_PROMPT = `You are Atlas of Mount Othrys: master orchestrator.

Hold the entire workflow until completion. Coordinate agents, maintain fortress state in .sisyphus/, and enforce verification across diagnostics, builds, and tests.`

export const ATLAS_MODE: TitanConfig = {
  mode: TitanMode.ATLAS,
  name: 'atlas',
  role: TitanRole.ORCHESTRATOR,
  description: 'Master orchestrator — coordinates plans, delegation, and verification',
  adapterType: 'python',
  pythonModule: 'atlas',
  defaultSubcommand: 'design',
  triggers: [/atlas/i, /system design/i, /design the system/i, /architecture review/i, /design review/i, /plan the architecture/i, /complete this todo/i],
  keywords: ['atlas', 'system design', 'design the system', 'architecture review', 'design review', 'plan the architecture'],
  systemPrompt: ATLAS_SYSTEM_PROMPT,
  toolAccess: ['read', 'lsp_diagnostics', 'delegate_task'],
  toolBlocked: ['write', 'edit'],
  writablePaths: ['.sisyphus/'],
  requiresPlan: true,
  requiresVerification: true,
  temperature: 0.1,
  thinkingBudget: 32_000,
  maxTokens: 16_000,
}
