export interface ThemisMetadata {
  category: "advisor"
  cost: "EXPENSIVE" | "MODERATE" | "CHEAP"
  promptAlias: string
  triggers: Array<{
    domain: string
    trigger: string
  }>
  useWhen: string[]
  avoidWhen: string[]
}

export interface ThemisAgent {
  name: string
  description: string
  model: string
  temperature: number
  thinking: { type: "enabled"; budgetTokens: number }
  textVerbosity?: "low" | "medium" | "high"
  prompt: string
  toolRestrictions: string[]
  metadata: ThemisMetadata
}
