export interface LLMMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface LLMRequest {
  model?: string
  messages: LLMMessage[]
  temperature?: number
  maxTokens?: number
  metadata?: Record<string, unknown>
}

export interface LLMResponse {
  content: string
  model: string
  usage?: {
    inputTokens?: number
    outputTokens?: number
    totalTokens?: number
  }
  metadata: Record<string, unknown>
}

export interface LLMProvider {
  name: string
  complete(request: LLMRequest): Promise<LLMResponse>
}
