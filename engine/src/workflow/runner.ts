import { TitanRole, WorkflowPhase, WorkflowResult } from '../modes/types.js'
import { TitanAdapter, TitanInput } from '../adapters/types.js'
import { Router } from '../router.js'
import { EventBus } from '../engine/EventBus.js'
import { runVerifications } from './verifier.js'

export interface WorkflowRunnerOptions {
  workdir?: string
  session?: string
  titanOverride?: string
  apiKeys?: Record<string, string>
  venvs?: Record<string, string>
  rootDir: string
  router?: Router
  eventBus?: EventBus
}

export class WorkflowRunner {
  private adapters: Map<string, TitanAdapter>
  private rootDir: string
  private router: Router
  private eventBus?: EventBus

  constructor(adapters: Map<string, TitanAdapter>, options: WorkflowRunnerOptions) {
    this.adapters = adapters
    this.rootDir = options.rootDir
    this.router = options.router ?? new Router()
    this.eventBus = options.eventBus
  }

  async run(message: string, options: WorkflowRunnerOptions): Promise<WorkflowResult> {
    this.eventBus?.emit('route:start', { message })

    const routeResult = options.titanOverride
      ? this.router.routeExplicit(options.titanOverride)
      : this.router.route(message)

    this.eventBus?.emit('route:complete', { result: routeResult })

    const phase = this.phaseFor(routeResult.config.role)
    this.eventBus?.emit('phase:start', { phase, mode: routeResult.mode })

    const adapter = this.adapters.get(routeResult.mode) ?? this.adapters.get(String(routeResult.mode))
    if (!adapter) {
      return {
        mode: routeResult.mode,
        phase: WorkflowPhase.ROUTE,
        output: `No adapter found for mode: ${routeResult.mode}`,
        metadata: { reason: routeResult.reason, error: 'missing_adapter' },
        verification: {
          passed: false,
          checks: [{ name: 'adapter', passed: false, detail: `No adapter for ${routeResult.mode}` }],
        },
      }
    }

    const input: TitanInput = {
      prompt: message,
      workdir: options.workdir,
      session: options.session,
      context: {
        systemPrompt: routeResult.config.systemPrompt,
        mode: routeResult.mode,
        phase,
      },
    }

    const result = await adapter.execute(input)
    this.eventBus?.emit('phase:complete', { phase, mode: routeResult.mode, output: result.output })

    let verification = { passed: result.passed, checks: result.checks }
    if (routeResult.config.requiresVerification && options.workdir) {
      this.eventBus?.emit('verification:start', { mode: routeResult.mode })
      const envChecks = await runVerifications({ workdir: options.workdir })
      // Merge instead of replace: environment checks must not mask a failed
      // Titan run (e.g. spawn/exit failures) — all checks must pass.
      verification = {
        passed: verification.passed && envChecks.passed,
        checks: [...verification.checks, ...envChecks.checks],
      }
      this.eventBus?.emit('verification:complete', { mode: routeResult.mode, result: verification })
    }

    const workflowResult: WorkflowResult = {
      mode: routeResult.mode,
      phase,
      output: result.output,
      metadata: { ...result.metadata, reason: routeResult.reason },
      verification,
    }

    this.eventBus?.emit('workflow:complete', { result: workflowResult })
    return workflowResult
  }

  private phaseFor(role: TitanRole): WorkflowPhase {
    if (role === TitanRole.PLANNER) return WorkflowPhase.PLAN
    if (role === TitanRole.ADVISOR) return WorkflowPhase.ADVISE
    if (role === TitanRole.ORCHESTRATOR) return WorkflowPhase.ORCHESTRATE
    return WorkflowPhase.EXECUTE
  }
}
