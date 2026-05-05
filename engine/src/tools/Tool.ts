export interface ToolContext {
  workdir: string
  mode?: string
  metadata?: Record<string, unknown>
}

export interface ToolResult {
  success: boolean
  output: string
  metadata: Record<string, unknown>
}

export interface Tool<Input = unknown> {
  name: string
  description: string
  execute(input: Input, context: ToolContext): Promise<ToolResult>
}
