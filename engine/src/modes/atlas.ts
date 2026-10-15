import { TitanMode, TitanModeSpec, TitanRole } from './types.js'

export const ATLAS_SYSTEM_PROMPT = `You are Atlas of Mount Othrys: master orchestrator.

Hold the entire workflow until completion. Coordinate agents, maintain fortress state in .sisyphus/, and enforce verification across diagnostics, builds, and tests.`

export const ATLAS_MODE: TitanModeSpec = {
  mode: TitanMode.ATLAS,
  name: 'atlas',
  role: TitanRole.ORCHESTRATOR,
  description: 'Master orchestrator — coordinates plans, delegation, and verification',
  adapterType: 'python',
  pythonModule: 'atlas',
  defaultSubcommand: 'design',
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
