import { spawn } from 'node:child_process'
import { TitanConfig, TitanMode } from '../modes/types.js'
import { TitanInput, TitanOutput } from './types.js'
import { CONTEXT_ENV_VAR, serializeEngineContext } from './engineContext.js'

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

/** A fully resolved command line for one Titan worker invocation. */
export interface TitanInvocation {
  pythonBin: string
  args: string[]
  env: NodeJS.ProcessEnv
  cwd: string
}

/**
 * Resolve everything needed to run a Titan worker.
 *
 * Kept separate from the spawn so the argument and environment contract can be
 * asserted without launching a process (MF-1 regression coverage).
 *
 * Global flags precede the subcommand: every Titan CLI defines `--json` on its
 * main argparse parser, and subparsers reject options they do not know. The cwd
 * is already `input.workdir` (the Python CLIs default `--root`/`--workdir` to
 * cwd), so no `--workdir` flag is needed — coeus does not even define one.
 * Routing context travels in `OTHRYS_CONTEXT` instead of argv, because no Titan
 * CLI accepts `--system-prompt` and long prompts do not belong in the process
 * table.
 */
export function buildTitanInvocation(
  titan: TitanConfig,
  input: TitanInput,
  rootDir: string,
  venvs: Record<string, string>,
  apiKeys: Record<string, string>,
): TitanInvocation {
  const pythonBin = resolveVenvPath(titan, rootDir, venvs)
  const args: string[] = ['-m', titan.pythonModule ?? titan.mode, '--json']

  args.push(titan.defaultSubcommand)

  // Subcommand-specific argument adjustments for non-interactive engine execution:
  if (titan.mode === TitanMode.COEUS && titan.defaultSubcommand === 'interview') {
    args.push('--force', '--no-ask')
  }

  if (input.prompt) {
    args.push(input.prompt)
  }

  // Forward API keys and environment cleanly
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    ...apiKeys,
  }
  // Ensure ANTHROPIC_API_KEY is available if set in engine or process
  if (apiKeys['anthropic'] || apiKeys['ANTHROPIC_API_KEY']) {
    env.ANTHROPIC_API_KEY = apiKeys['anthropic'] ?? apiKeys['ANTHROPIC_API_KEY']
  }

  const titanDir = titan.name.toLowerCase()
  const titanSrc = `${rootDir}/${titanDir}/src`
  const othrysSrc = `${rootDir}/othrys/src`
  const existingPp = process.env.PYTHONPATH ? `:${process.env.PYTHONPATH}` : ''
  env.PYTHONPATH = `${titanSrc}:${othrysSrc}${existingPp}`

  // MF-1: hand the routed mode identity to the worker. `othrys.llm.BaseLLM`
  // reads this and prepends the engine directive to the Titan's own prompt.
  env[CONTEXT_ENV_VAR] = serializeEngineContext(titan, input)

  return { pythonBin, args, env, cwd: input.workdir ?? rootDir }
}

export async function spawnPythonTitan(
  titan: TitanConfig,
  input: TitanInput,
  rootDir: string,
  venvs: Record<string, string>,
  apiKeys: Record<string, string>,
): Promise<TitanOutput> {
  const { pythonBin, args, env, cwd } = buildTitanInvocation(titan, input, rootDir, venvs, apiKeys)

  return new Promise((resolveResult) => {
    let stdout = ''
    let stderr = ''
    let killed = false

    const proc = spawn(pythonBin, args, {
      cwd,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    })

    const timeoutHandle = setTimeout(() => {
      killed = true
      proc.kill('SIGKILL')
    }, SPAWN_TIMEOUT_MS)

    proc.stdout?.on('data', (chunk) => {
      stdout += chunk.toString()
    })

    proc.stderr?.on('data', (chunk) => {
      stderr += chunk.toString()
    })

    proc.on('error', (err) => {
      clearTimeout(timeoutHandle)
      resolveResult({
        output: err.message,
        metadata: { mode: titan.mode, error: err.name },
        passed: false,
        checks: [{ name: 'spawn', passed: false, detail: err.message }],
      })
    })

    proc.on('close', (exitCode, signal) => {
      clearTimeout(timeoutHandle)
      if (killed || signal === 'SIGKILL') {
        resolveResult({
          output: `Titan timed out after ${SPAWN_TIMEOUT_MS / 1000}s`,
          metadata: { mode: titan.mode, exitCode: -1, timedOut: true },
          passed: false,
          checks: [{ name: 'spawn', passed: false, detail: 'Process timed out' }],
        })
        return
      }

      if (exitCode !== 0 && exitCode !== null) {
        if (exitCode === 127) {
          resolveResult({
            output: `Titan binary not found: ${pythonBin}`,
            metadata: { mode: titan.mode, exitCode: 127, binary: pythonBin },
            passed: false,
            checks: [{ name: 'spawn', passed: false, detail: `Binary not found: ${pythonBin}` }],
          })
          return
        }

        resolveResult({
          output: (stdout || stderr || `Titan exited with code ${exitCode}`).trim(),
          metadata: { mode: titan.mode, exitCode, stderr: stderr.trim() },
          passed: false,
          checks: [{ name: 'spawn', passed: false, detail: stderr.trim() || `Exit code ${exitCode}` }],
        })
        return
      }

      const output = stdout.trim()
      if (!output) {
        resolveResult({
          output: stderr.trim() || 'No output from Titan',
          metadata: { mode: titan.mode, exitCode: 0, stderr: stderr.trim() },
          passed: true,
          checks: [],
        })
        return
      }

      try {
        const parsed = JSON.parse(output)
        if (parsed && typeof parsed === 'object' && 'output' in parsed) {
          resolveResult({
            output: parsed.output ?? String(output),
            metadata: parsed.metadata ?? { mode: titan.mode },
            passed: parsed.passed ?? true,
            checks: parsed.checks ?? [],
          })
          return
        }
      } catch {
        // Not JSON — return raw output
      }

      resolveResult({
        output,
        metadata: { mode: titan.mode, exitCode: 0 },
        passed: true,
        checks: [],
      })
    })
  })
}