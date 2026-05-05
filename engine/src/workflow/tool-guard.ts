import { resolve as resolvePath, isAbsolute } from 'node:path'
import { VerificationCheck } from '../modes/types.js'
import { TITAN_REGISTRY } from '../modes/registry.js'

const BLOCKED_COMMANDS = [
  /^rm\s+.*?-rf?\s+\/\s*$/i,
  /mkfs/i,
  /dd\s+if=/i,
  /:\{\(\):\s*\|:&\};:/i,
  /git\s+push\s+--force(?!-)/i,
  /git\s+reset\s+--hard/i,
  /DROP\s+(TABLE|DATABASE)/i,
]

const BLOCKED_PATH_PATTERNS = [
  '/etc/',
  '/usr/',
  '/var/',
  '/sys/',
  '/proc/',
  '/dev/',
  'C:\\Windows\\',
  'C:\\Program Files\\',
]

export interface GuardCheck {
  name: string
  passed: boolean
  detail: string
}

export interface GuardResult {
  allowed: boolean
  checks: GuardCheck[]
  blockedReason?: string
}

export function guardCommand(command: string): GuardResult {
  const checks: GuardCheck[] = []
  let blocked = false
  let blockedReason: string | undefined

  for (const pattern of BLOCKED_COMMANDS) {
    if (pattern.test(command)) {
      blocked = true
      blockedReason = `Blocked command pattern: ${pattern}`
      checks.push({ name: 'command-safety', passed: false, detail: blockedReason })
      break
    }
  }

  if (!blocked) {
    checks.push({ name: 'command-safety', passed: true, detail: 'Command passed safety check' })
  }

  return { allowed: !blocked, checks, blockedReason }
}

export function guardFilePath(filePath: string, workdir: string): GuardResult {
  const checks: GuardCheck[] = []
  const resolved = resolvePath(isAbsolute(filePath) ? filePath : `${workdir}/${filePath}`)

  for (const pattern of BLOCKED_PATH_PATTERNS) {
    if (resolved.startsWith(pattern) || resolved.includes(pattern)) {
      checks.push({ name: 'path-safety', passed: false, detail: `Path outside workdir: ${resolved} matches blocked pattern: ${pattern}` })
      return { allowed: false, checks, blockedReason: `Write blocked: path outside workdir (${pattern})` }
    }
  }

  const resolvedWorkdir = resolvePath(workdir)
  if (!resolved.startsWith(resolvedWorkdir + '/') && resolved !== resolvedWorkdir) {
    checks.push({ name: 'path-safety', passed: false, detail: `Path outside workdir: ${resolved} (workdir: ${resolvedWorkdir})` })
    return { allowed: false, checks, blockedReason: `Write blocked: path outside workdir` }
  }

  checks.push({ name: 'path-safety', passed: true, detail: 'Path within workdir' })
  return { allowed: true, checks }
}

export function guardScope(mode: string, action: string): GuardResult {
  const checks: GuardCheck[] = []
  const config = TITAN_REGISTRY[mode]

  if (!config) {
    checks.push({ name: 'scope-safety', passed: false, detail: `Unknown mode: ${mode}` })
    return { allowed: false, checks, blockedReason: `Unknown mode: ${mode}` }
  }

  const blockedTools = [...config.toolBlocked]
  const allowedTools = [...config.toolAccess]

  if (blockedTools.includes('*')) {
    checks.push({ name: 'scope-safety', passed: false, detail: `Mode ${mode} has all tools blocked` })
    return { allowed: false, checks, blockedReason: `Mode ${mode} is read-only` }
  }

  if (blockedTools.includes(action)) {
    checks.push({ name: 'scope-safety', passed: false, detail: `Mode ${mode} blocks action: ${action}` })
    return { allowed: false, checks, blockedReason: `Mode ${mode} cannot ${action}` }
  }

  if (allowedTools.includes('*')) {
    checks.push({ name: 'scope-safety', passed: true, detail: `Mode ${mode} has full tool access` })
    return { allowed: true, checks }
  }

  if (!allowedTools.includes(action)) {
    checks.push({ name: 'scope-safety', passed: false, detail: `Mode ${mode} does not have access to: ${action}` })
    return { allowed: false, checks, blockedReason: `Mode ${mode} lacks access to ${action}` }
  }

  checks.push({ name: 'scope-safety', passed: true, detail: `Action ${action} allowed for mode ${mode}` })
  return { allowed: true, checks }
}
