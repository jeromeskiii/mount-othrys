export interface HeraclesHook {
  name: string
  enabled: boolean
  detectKeyword: (input: string) => boolean
  getMessage: (isPlanner: boolean) => string
  createHeraclesReminder: (isPlanner: boolean) => string
  hook: {
    "tool.execute.before": (
      input: { tool: string; prompt?: string },
      output: { args: Record<string, unknown>; message?: string }
    ) => Promise<void>
    "chat.message": (
      input: { text: string },
      output: { parts: Array<{ type: string; text?: string }> }
    ) => Promise<void>
  }
}
