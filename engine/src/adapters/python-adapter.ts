import { TitanConfig, TitanMode } from '../modes/types.js'
import { TitanAdapter, TitanInput, TitanOutput } from './types.js'
import { spawnPythonTitan } from './python-bridge.js'

export class PythonTitanAdapter implements TitanAdapter {
  name: string
  mode: TitanMode
  private titan: TitanConfig
  private rootDir: string
  private venvs: Record<string, string>
  private apiKeys: Record<string, string>

  constructor(titan: TitanConfig, rootDir: string, venvs: Record<string, string>, apiKeys: Record<string, string>) {
    this.name = titan.name
    this.mode = titan.mode
    this.titan = titan
    this.rootDir = rootDir
    this.venvs = venvs
    this.apiKeys = apiKeys
  }

  async execute(input: TitanInput): Promise<TitanOutput> {
    return spawnPythonTitan(this.titan, input, this.rootDir, this.venvs, this.apiKeys)
  }
}