import { z } from 'zod'
import {
  RouteResultSchema,
  TitanConfigSchema,
  VerificationResultSchema,
  WorkflowResultSchema,
} from './schemas.js'
import type {
  RouteResult,
  TitanConfig,
  VerificationResult,
  WorkflowResult,
} from '../modes/types.js'

export function validateTitanConfig(value: unknown): TitanConfig {
  return TitanConfigSchema.parse(value)
}

export function validateRouteResult(value: unknown): RouteResult {
  return RouteResultSchema.parse(value)
}

export function validateVerificationResult(value: unknown): VerificationResult {
  return VerificationResultSchema.parse(value)
}

export function validateWorkflowResult(value: unknown): WorkflowResult {
  return WorkflowResultSchema.parse(value)
}

export function formatValidationError(error: unknown): string {
  if (error instanceof z.ZodError) {
    return error.issues.map(issue => `${issue.path.join('.')}: ${issue.message}`).join('; ')
  }
  return error instanceof Error ? error.message : String(error)
}
