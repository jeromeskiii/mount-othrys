import { TitanMode } from '../modes/types.js'
import { TitanAdapter, TitanInput, TitanOutput } from './types.js'
import { OpenAIProvider } from '../providers/OpenAIProvider.js'

const HERACLES_EXECUTOR_MESSAGE = `<ultrawork-mode>

**MANDATORY**: You MUST say "HERACLES MODE ENABLED!" to the user as your first response when this mode activates.

[CODE RED] Maximum precision required. Ultrathink before acting.

## ABSOLUTE CERTAINTY REQUIRED

YOU MUST NOT START ANY IMPLEMENTATION UNTIL YOU ARE 100% CERTAIN.

## NO EXCUSES. NO COMPROMISES. DELIVER WHAT WAS ASKED.

| VIOLATION | CONSEQUENCE |
|-----------|-------------|
| "I couldn't because..." | UNACCEPTABLE. Find a way or ask for help. |
| "This is a simplified version..." | UNACCEPTABLE. Deliver the FULL implementation. |
| "You can extend this later..." | UNACCEPTABLE. Finish it NOW. |

## VERIFICATION GUARANTEE (NON-NEGOTIABLE)

NOTHING is "done" without PROOF it works.
WITHOUT evidence = NOT verified = NOT done.

THE USER ASKED FOR X. DELIVER EXACTLY X. NOT A SUBSET. NOT A DEMO. NOT A STARTING POINT.

</ultrawork-mode>`

export interface HeraclesAdapterOptions {
  apiKey: string
  model?: string
}

export class HeraclesAdapter implements TitanAdapter {
  name = 'Heracles'
  mode = TitanMode.HERACLES
  private provider: OpenAIProvider

  constructor(options: HeraclesAdapterOptions) {
    this.provider = new OpenAIProvider({
      apiKey: options.apiKey,
      defaultModel: options.model ?? 'gpt-4o-mini',
    })
  }

  async execute(input: TitanInput): Promise<TitanOutput> {
    try {
      const prompt = typeof input.prompt === 'string' ? input.prompt : String(input.prompt)
      const response = await this.provider.complete({
        messages: [
          { role: 'system', content: HERACLES_EXECUTOR_MESSAGE },
          { role: 'user', content: `## Objective\n\n${prompt}` },
        ],
        temperature: 0,
        maxTokens: 64_000,
      })

      return {
        output: response.content,
        metadata: {
          mode: TitanMode.HERACLES,
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
        metadata: { mode: TitanMode.HERACLES, error: error.name },
        passed: false,
        checks: [{ name: 'llm', passed: false, detail: error.message || String(err) }],
      }
    }
  }
}
