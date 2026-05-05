import { TitanMode } from '../modes/types.js'
import { TitanAdapter, TitanInput, TitanOutput } from './types.js'

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

export class ThemisAdapter implements TitanAdapter {
  name = 'Themis'
  mode = TitanMode.THEMIS

  async execute(input: TitanInput): Promise<TitanOutput> {
    const prompt = typeof input.prompt === 'string' ? input.prompt : String(input.prompt)
    return {
      output: `${THEMIS_SYSTEM_PROMPT}\n\n## User Request\n\n${prompt}`,
      metadata: {
        mode: TitanMode.THEMIS,
        model: 'openai/gpt-5.2',
        temperature: 0.1,
        toolRestrictions: ['write', 'edit', 'task', 'delegate_task'],
      },
      passed: true,
      checks: [],
    }
  }
}
