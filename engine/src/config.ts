import { resolve } from 'node:path'

export interface EngineConfig {
  rootDir: string
  defaultModel: string
  apiKeys: Record<string, string>
  pythonVenvs: Record<string, string>
  thinkingBudget: number
  maxTokens: number
  timeout: number
}

const DEFAULT_CONFIG: EngineConfig = {
  rootDir: resolve(import.meta.dirname, '../../'),
  defaultModel: 'claude-sonnet-4-5',
  apiKeys: {},
  pythonVenvs: {},
  thinkingBudget: 32_000,
  maxTokens: 64_000,
  timeout: 600,
}

export function loadConfig(overrides?: Partial<EngineConfig>): EngineConfig {
  return {
    ...DEFAULT_CONFIG,
    ...overrides,
    apiKeys: {
      ...DEFAULT_CONFIG.apiKeys,
      ...(overrides?.apiKeys ?? {}),
    },
    pythonVenvs: {
      ...DEFAULT_CONFIG.pythonVenvs,
      ...(overrides?.pythonVenvs ?? {}),
    },
  }
}

export function resolveVenvs(rootDir: string): Record<string, string> {
  return {
    coeus: `${rootDir}/Coeus/.venv/bin/python`,
    atlas: `${rootDir}/atlas/.venv/bin/python`,
    iapetus: `${rootDir}/Iapetus/.venv/bin/python`,
    talos: `${rootDir}/Talos/.venv/bin/python`,
  }
}