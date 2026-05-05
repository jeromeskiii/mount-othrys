import { TitanConfig } from '../modes/types.js'
import { TitanInput, TitanOutput } from './types.js'
import { ProcessSandbox } from '@core/exec-core/src/proc-sandbox.js'
import { DEFAULT_SANDBOX_CONFIG, SandboxConfig } from '@core/exec-core/src/types.js'

const SPAWN_TIMEOUT_MS = 600_000

export interface PythonBridgeOptions {
  pythonBinary: string
  module: string
  subcommand: string
  args?: string[]
  workdir?: string
  jsonOutput?: boolean
  env?: Record<string, string>
}

function resolveVenvPath(titan: TitanConfig, rootDir: string, venvs: Record<string, string>): string {
  if (titan.pythonBinary) {
    return titan.pythonBinary
  }
  const venvPath = venvs[titan.mode]
  if (venvPath) {
    return venvPath
  }
  const titanDir = titan.name.toLowerCase()
  return `${rootDir}/${titanDir}/.venv/bin/python`
}

export async function spawnPythonTitan(
  titan: TitanConfig,
  input: TitanInput,
  rootDir: string,
  venvs: Record<string, string>,
  apiKeys: Record<string, string>,
): Promise<TitanOutput> {
  const pythonBin = resolveVenvPath(titan, rootDir, venvs)
  const args: string[] = ['-m', titan.pythonModule ?? titan.mode, titan.defaultSubcommand]

  if (input.prompt) {
    args.push(input.prompt)
  }

  args.push('--json')

  if (input.workdir) {
    args.push('--workdir', input.workdir)
  }

  const env: Record<string, string> = {
    ...process.env as Record<string, string>,
    ...apiKeys,
  }

  if (input.context) {
    const contextArgs = Object.entries(input.context)
      .filter(([, v]) => v !== undefined && v !== null)
      .map(([k, v]) => `--${k}=${String(v)}`)
    args.push(...contextArgs)
  }

  const sandboxConfig: SandboxConfig = {
    ...DEFAULT_SANDBOX_CONFIG,
    rootDir: input.workdir ?? rootDir,
    allowedPaths: {
      read: ['**/*'],
      write: (titan as any).writablePaths ?? ['.sisyphus/'],
    },
    commands: {
      mode: 'whitelist',
      whitelist: [pythonBin, 'python3', 'python', 'git', 'npm', 'pnpm'],
      allowShell: false,
    },
    limits: {
      ...DEFAULT_SANDBOX_CONFIG.limits,
      timeout: SPAWN_TIMEOUT_MS,
    },
    env: {
      inherit: true,
      extra: apiKeys,
    },
    audit: {
      logAllOperations: true,
      captureStderr: true,
      captureStdout: true,
    }
  }

  const sandbox = new ProcessSandbox(sandboxConfig)

  try {
    const { stdout, stderr, exitCode, killed } = await sandbox.executeCommand(pythonBin, args)

    if (killed) {
      return {
        output: `Titan timed out after ${SPAWN_TIMEOUT_MS / 1000}s`,
        metadata: { mode: titan.mode, exitCode: -1, timedOut: true },
        passed: false,
        checks: [{ name: 'spawn', passed: false, detail: 'Process timed out' }],
      }
    }

    if (exitCode !== 0) {
      if (exitCode === 127) {
        return {
          output: `Titan binary not found: ${pythonBin}`,
          metadata: { mode: titan.mode, exitCode: 127, binary: pythonBin },
          passed: false,
          checks: [{ name: 'spawn', passed: false, detail: `Binary not found: ${pythonBin}` }],
        }
      }

      return {
        output: (stdout || stderr || `Titan exited with code ${exitCode}`),
        metadata: { mode: titan.mode, exitCode, stderr },
        passed: false,
        checks: [{ name: 'spawn', passed: false, detail: stderr || `Exit code ${exitCode}` }],
      }
    }

    const output = stdout.trim()
    if (!output) {
      return {
        output: stderr.trim() || 'No output from Titan',
        metadata: { mode: titan.mode, exitCode: 0, stderr: stderr.trim() },
        passed: true,
        checks: [],
      }
    }

    try {
      const parsed = JSON.parse(output)
      if (parsed && typeof parsed === 'object' && 'output' in parsed) {
        return {
          output: parsed.output ?? String(output),
          metadata: parsed.metadata ?? { mode: titan.mode },
          passed: parsed.passed ?? true,
          checks: parsed.checks ?? [],
        }
      }
    } catch {
      // Not JSON — return raw output
    }

    return {
      output,
      metadata: { mode: titan.mode, exitCode: 0 },
      passed: true,
      checks: [],
    }
  } catch (err: unknown) {
    const error = err as Error
    return {
      output: error.message || String(err),
      metadata: { mode: titan.mode, error: error.name },
      passed: false,
      checks: [{ name: 'sandbox', passed: false, detail: error.message || String(err) }],
    }
  }
}