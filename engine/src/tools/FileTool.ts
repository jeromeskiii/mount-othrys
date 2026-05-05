import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { guardFilePath } from '../workflow/tool-guard.js'
import type { Tool, ToolContext, ToolResult } from './Tool.js'

export type FileInput =
  | { operation: 'read'; path: string }
  | { operation: 'write'; path: string; content: string }

export class FileTool implements Tool<FileInput> {
  name = 'file'
  description = 'Read or write files inside the current workspace'

  async execute(input: FileInput, context: ToolContext): Promise<ToolResult> {
    const absolute = resolve(context.workdir, input.path)
    const guard = guardFilePath(absolute, context.workdir)

    if (!guard.allowed) {
      return {
        success: false,
        output: guard.blockedReason ?? 'Path blocked',
        metadata: { checks: guard.checks },
      }
    }

    if (input.operation === 'read') {
      const content = await readFile(absolute, 'utf8')
      return { success: true, output: content, metadata: { path: absolute } }
    }

    await mkdir(dirname(absolute), { recursive: true })
    await writeFile(absolute, input.content, 'utf8')
    return { success: true, output: `Wrote ${absolute}`, metadata: { path: absolute } }
  }
}
