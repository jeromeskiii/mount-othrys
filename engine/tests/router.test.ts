import { describe, expect, it } from 'vitest'
import { Router } from '../src/router'
import { TitanMode } from '../src/modes/types'

describe('Router', () => {
  it('routes planning requests to Coeus', () => {
    const result = new Router().route('create a plan for this migration')
    expect(result.mode).toBe(TitanMode.COEUS)
  })

  it('routes advisory requests to Themis', () => {
    const result = new Router().route('consult on this architecture decision')
    expect(result.mode).toBe(TitanMode.THEMIS)
  })

  it('routes ultrawork requests to Heracles', () => {
    const result = new Router().route('ultrawork finish this now')
    expect(result.mode).toBe(TitanMode.HERACLES)
  })

  it('defaults to Talos', () => {
    const result = new Router().route('hello there')
    expect(result.mode).toBe(TitanMode.TALOS)
  })

  it('supports explicit legacy aliases', () => {
    const result = new Router().routeExplicit('prometheus')
    expect(result.mode).toBe(TitanMode.COEUS)
  })

  it('throws for unknown explicit mode', () => {
    expect(() => new Router().routeExplicit('unknown')).toThrow(/Unknown Titan/)
  })
})
