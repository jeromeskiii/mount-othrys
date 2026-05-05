import { z } from 'zod'
import { TitanMode, TitanRole, WorkflowPhase } from '../modes/types.js'

export const TitanModeSchema = z.nativeEnum(TitanMode)
export const TitanRoleSchema = z.nativeEnum(TitanRole)
export const WorkflowPhaseSchema = z.nativeEnum(WorkflowPhase)

export const TitanConfigSchema = z.object({
  mode: TitanModeSchema,
  name: z.string().min(1),
  role: TitanRoleSchema,
  description: z.string().min(1),
  adapterType: z.enum(['python', 'native', 'llm']),
  pythonModule: z.string().optional(),
  pythonBinary: z.string().optional(),
  defaultSubcommand: z.string().min(1),
  triggers: z.array(z.instanceof(RegExp)),
  keywords: z.array(z.string()),
  systemPrompt: z.string().min(1),
  allowedTools: z.array(z.string()),
  blockedTools: z.array(z.string()),
  writablePaths: z.array(z.string()),
  toolAccess: z.array(z.string()),
  toolBlocked: z.array(z.string()),
  requiresPlan: z.boolean(),
  requiresVerification: z.boolean(),
  model: z.string().optional(),
  temperature: z.number().min(0).max(2),
  thinkingBudget: z.number().int().positive(),
  maxTokens: z.number().int().positive(),
})

export const RouteResultSchema = z.object({
  mode: TitanModeSchema,
  reason: z.string(),
  config: TitanConfigSchema,
})

export const VerificationCheckSchema = z.object({
  name: z.string(),
  passed: z.boolean(),
  detail: z.string(),
})

export const VerificationResultSchema = z.object({
  passed: z.boolean(),
  checks: z.array(VerificationCheckSchema),
})

export const WorkflowResultSchema = z.object({
  mode: TitanModeSchema,
  phase: WorkflowPhaseSchema,
  output: z.string(),
  metadata: z.record(z.string(), z.unknown()),
  verification: VerificationResultSchema,
})
