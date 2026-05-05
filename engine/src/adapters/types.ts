import { TitanConfig, TitanMode, VerificationResult } from '../modes/types.js'

export interface TitanInput {
  prompt: string
  context?: Record<string, unknown>
  workdir?: string
  session?: string
}

export interface TitanOutput {
  output: string
  metadata: Record<string, unknown>
  passed: boolean
  checks: VerificationResult['checks']
}

export interface TitanAdapter {
  name: string
  mode: TitanMode
  execute(input: TitanInput): Promise<TitanOutput>
}

export interface AdapterConfig {
  titan: TitanConfig
  rootDir: string
  pythonVenvs: Record<string, string>
  apiKeys: Record<string, string>
}