import { TitanMode } from '../modes/types.js'
import { TitanAdapter, TitanInput, TitanOutput } from './types.js'
import { OpenAIProvider } from '../providers/OpenAIProvider.js'
import type { LLMProvider } from '../providers/LLMProvider.js'
import { resolveSystemPrompt } from './engineContext.js'

const THEMIS_SYSTEM_PROMPT = `You are Themis — Strategic Technical Advisor.

You are a strategic technical advisor with deep reasoning capabilities,
operating as a specialized consultant within an AI-assisted development
environment. Each consultation is standalone. Deliver actionable insight,
not exhaustive analysis.

## Response Structure
- **Bottom line**: 2-3 sentences capturing your recommendation
- **Action plan**: Numbered steps or checklist
- **Effort estimate**: Quick/Short/Medium/Large

## Guiding Principles
- Bias toward simplicity
- Leverage what exists
- One clear path
- Dense and useful beats long and thorough`

export interface ThemisAdapterOptions {
  apiKey: string
  model?: string
  /**
   * Injection seam for tests. Defaults to an OpenAI-backed provider; supplying
   * one keeps the adapter's request shape assertable without network access.
   */
  provider?: LLMProvider
}

export class ThemisAdapter implements TitanAdapter {
  name = 'Themis'
  mode = TitanMode.THEMIS
  private provider: LLMProvider

  constructor(options: ThemisAdapterOptions) {
    this.provider =
      options.provider ??
      new OpenAIProvider({
        apiKey: options.apiKey,
        defaultModel: options.model ?? 'gpt-4o',
      })
  }

  async execute(input: TitanInput): Promise<TitanOutput> {
    try {
      const prompt = typeof input.prompt === 'string' ? input.prompt : String(input.prompt)
      const response = await this.provider.complete({
        messages: [
          { role: 'system', content: resolveSystemPrompt(THEMIS_SYSTEM_PROMPT, input.context) },
          { role: 'user', content: prompt },
        ],
        temperature: 0.1,
        maxTokens: 64_000,
      })

      return {
        output: response.content,
        metadata: {
          mode: TitanMode.THEMIS,
          model: response.model,
          usage: response.usage,
        },
        passed: true,
        checks: [],
      }
    } catch (err: unknown) {
      const error = err as Error
      return {
        output: error.message || String(err),
        metadata: { mode: TitanMode.THEMIS, error: error.name },
        passed: false,
        checks: [{ name: 'llm', passed: false, detail: error.message || String(err) }],
      }
    }
  }
}
