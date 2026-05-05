import type { LLMProvider, LLMRequest, LLMResponse } from './LLMProvider.js'

interface OpenAIProviderOptions {
  apiKey: string
  baseUrl?: string
  defaultModel?: string
}

interface OpenAIResponse {
  model: string
  choices?: Array<{ message?: { content?: string } }>
  usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  }
}

export class OpenAIProvider implements LLMProvider {
  name = 'openai'
  private apiKey: string
  private baseUrl: string
  private defaultModel: string

  constructor(options: OpenAIProviderOptions) {
    this.apiKey = options.apiKey
    this.baseUrl = options.baseUrl ?? 'https://api.openai.com/v1'
    this.defaultModel = options.defaultModel ?? 'gpt-4o-mini'
  }

  async complete(request: LLMRequest): Promise<LLMResponse> {
    const model = request.model ?? this.defaultModel
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        authorization: `Bearer ${this.apiKey}`,
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: request.messages,
        temperature: request.temperature,
        max_tokens: request.maxTokens,
      }),
    })

    if (!response.ok) {
      throw new Error(`OpenAI request failed: ${response.status} ${await response.text()}`)
    }

    const data = (await response.json()) as OpenAIResponse
    const content = data.choices?.[0]?.message?.content ?? ''

    return {
      content,
      model: data.model ?? model,
      usage: {
        inputTokens: data.usage?.prompt_tokens,
        outputTokens: data.usage?.completion_tokens,
        totalTokens: data.usage?.total_tokens,
      },
      metadata: request.metadata ?? {},
    }
  }
}
