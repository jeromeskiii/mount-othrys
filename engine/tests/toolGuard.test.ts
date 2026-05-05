import { describe, expect, it } from 'vitest'
import { guardCommand, guardFilePath, guardScope } from '../src/workflow/tool-guard'

describe('tool guard', () => {
  it('allows normal commands', () => {
    expect(guardCommand('npm test').allowed).toBe(true)
  })

  it('blocks dangerous commands', () => {
    const result = guardCommand('rm -rf /')
    expect(result.allowed).toBe(false)
    expect(result.blockedReason).toMatch(/Blocked command/)
  })

  it('blocks rm with double spaces', () => {
    const result = guardCommand('rm  -rf  /')
    expect(result.allowed).toBe(false)
  })

  it('allows rm on subdirectories', () => {
    expect(guardCommand('rm -rf /tmp/safe_dir').allowed).toBe(true)
    expect(guardCommand('rm -rf ./node_modules').allowed).toBe(true)
  })

  it('blocks git push --force but allows --force-with-lease', () => {
    expect(guardCommand('git push --force').allowed).toBe(false)
    expect(guardCommand('git push --force-with-lease').allowed).toBe(true)
  })

  it('allows paths inside workdir', () => {
    const result = guardFilePath('/tmp/project/file.txt', '/tmp/project')
    expect(result.allowed).toBe(true)
  })

  it('blocks paths outside workdir', () => {
    const result = guardFilePath('/tmp/other/file.txt', '/tmp/project')
    expect(result.allowed).toBe(false)
  })

  it('blocks path traversal via ..', () => {
    const result = guardFilePath('../../../etc/passwd', '/tmp/project')
    expect(result.allowed).toBe(false)
  })

  it('blocks write scope for Themis', () => {
    const result = guardScope('themis', 'write')
    expect(result.allowed).toBe(false)
  })

  it('allows full access for Talos', () => {
    const result = guardScope('talos', 'write')
    expect(result.allowed).toBe(true)
  })
})
