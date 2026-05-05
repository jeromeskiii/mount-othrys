import { TitanAdapter } from '../adapters/types.js'
import { Router } from '../router.js'
import { WorkflowRunner, WorkflowRunnerOptions } from '../workflow/runner.js'
import { EventBus } from './EventBus.js'
import type { WorkflowResult } from '../modes/types.js'

export interface ModeEngineOptions extends WorkflowRunnerOptions {
  adapters: Map<string, TitanAdapter>
  router?: Router
  eventBus?: EventBus
}

export class ModeEngine {
  readonly router: Router
  readonly eventBus: EventBus
  private runner: WorkflowRunner
  private options: ModeEngineOptions

  constructor(options: ModeEngineOptions) {
    this.options = options
    this.router = options.router ?? new Router()
    this.eventBus = options.eventBus ?? new EventBus()
    this.runner = new WorkflowRunner(options.adapters, {
      ...options,
      router: this.router,
      eventBus: this.eventBus,
    })
  }

  async run(message: string, options: Partial<WorkflowRunnerOptions> = {}): Promise<WorkflowResult> {
    try {
      return await this.runner.run(message, {
        ...this.options,
        ...options,
        router: this.router,
        eventBus: this.eventBus,
      })
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      this.eventBus.emit('error', { error: err })
      throw err
    }
  }
}
