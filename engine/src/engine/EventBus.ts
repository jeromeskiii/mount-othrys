import { EventEmitter } from 'node:events'
import type { RouteResult, VerificationResult, WorkflowPhase, WorkflowResult } from '../modes/types.js'

export interface EngineEvents {
  'route:start': { message: string }
  'route:complete': { result: RouteResult }
  'phase:start': { phase: WorkflowPhase; mode: string }
  'phase:complete': { phase: WorkflowPhase; mode: string; output?: string }
  'tool:start': { tool: string; input: unknown }
  'tool:complete': { tool: string; success: boolean; output: string }
  'verification:start': { mode: string }
  'verification:complete': { mode: string; result: VerificationResult }
  'workflow:complete': { result: WorkflowResult }
  'error': { error: Error; phase?: WorkflowPhase }
}

export class EventBus {
  private emitter = new EventEmitter()

  on<K extends keyof EngineEvents>(event: K, listener: (payload: EngineEvents[K]) => void): this {
    this.emitter.on(event, listener as (payload: unknown) => void)
    return this
  }

  once<K extends keyof EngineEvents>(event: K, listener: (payload: EngineEvents[K]) => void): this {
    this.emitter.once(event, listener as (payload: unknown) => void)
    return this
  }

  off<K extends keyof EngineEvents>(event: K, listener: (payload: EngineEvents[K]) => void): this {
    this.emitter.off(event, listener as (payload: unknown) => void)
    return this
  }

  emit<K extends keyof EngineEvents>(event: K, payload: EngineEvents[K]): boolean {
    return this.emitter.emit(event, payload)
  }
}
