import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { guardCommand } from '../workflow/tool-guard.js'
import type { Tool, ToolContext, ToolResult } from './Tool.js'

const execFileAsync = promisify(execFile)

export interface ShellInput {
  command: string
  timeout?: number
}

export class ShellTool implements Tool<ShellInput> {
  name = 'shell'
  description = 'Execute a shell command inside the current workspace'

  async execute(input: ShellInput, context: ToolContext): Promise<ToolResult> {
    const guard = guardCommand(input.command)
    if (!guard.allowed) {
      return {
        success: false,
        output: guard.blockedReason ?? 'Command blocked',
        metadata: { checks: guard.checks },
      }
    }

    try {
      const { stdout, stderr } = await execFileAsync('bash', ['-c', input.command], {
        cwd: context.workdir,
        timeout: input.timeout ?? 120_000,
        maxBuffer: 5 * 1024 * 1024,
      })

      return {
        success: true,
        output: stdout || stderr,
        metadata: { stderr },
      }
    } catch (error) {
      const err = error as { stdout?: string; stderr?: string; code?: number }
      return {
        success: false,
        output: err.stderr || err.stdout || `Command failed with code ${err.code ?? 1}`,
        metadata: { code: err.code },
      }
    }
  }
}
