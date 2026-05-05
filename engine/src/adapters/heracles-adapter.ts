import { TitanMode } from '../modes/types.js'
import { TitanAdapter, TitanInput, TitanOutput } from './types.js'

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

export class HeraclesAdapter implements TitanAdapter {
  name = 'Heracles'
  mode = TitanMode.HERACLES

  async execute(input: TitanInput): Promise<TitanOutput> {
    const prompt = typeof input.prompt === 'string' ? input.prompt : String(input.prompt)
    return {
      output: `${HERACLES_EXECUTOR_MESSAGE}\n\n## Objective\n\n${prompt}`,
      metadata: {
        mode: TitanMode.HERACLES,
      },
      passed: true,
      checks: [],
    }
  }
}
