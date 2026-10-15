import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { access, readFile } from 'node:fs/promises'
import { VerificationCheck, VerificationResult } from '../modes/types.js'

const execFileAsync = promisify(execFile)

const DEFAULT_TIMEOUT_MS = 120_000

export interface VerifyOptions {
  workdir: string
  commands?: Array<{ name: string; command: string; timeout?: number }>
  fileChecks?: Array<{ name: string; path: string; shouldExist: boolean }>
}

export async function runVerifications(options: VerifyOptions): Promise<VerificationResult> {
  const checks: VerificationCheck[] = []

  const commands = await defaultCommands(options.workdir)
  for (const cmd of commands) {
    try {
      const { stdout, stderr } = await execFileAsync('bash', ['-c', cmd.command], {
        cwd: options.workdir,
        timeout: cmd.timeout ?? DEFAULT_TIMEOUT_MS,
        maxBuffer: 5 * 1024 * 1024,
      })
      checks.push({ name: cmd.name, passed: true, detail: (stdout || '').trim().slice(0, 500) })
    } catch (err: unknown) {
      const error = err as { stdout?: string; stderr?: string; code?: number }
      const detail = (error.stderr || error.stdout || `exit code ${error.code ?? 1}`).trim().slice(0, 500)
      checks.push({ name: cmd.name, passed: false, detail })
    }
  }

  const fileChecks = options.fileChecks ?? []
  for (const fc of fileChecks) {
    try {
      await access(fc.path)
      checks.push({ name: fc.name, passed: fc.shouldExist, detail: fc.shouldExist ? 'File exists' : 'File exists (expected absent)' })
    } catch {
      checks.push({ name: fc.name, passed: !fc.shouldExist, detail: fc.shouldExist ? 'File missing' : 'File absent (as expected)' })
    }
  }

  return {
    passed: checks.every(c => c.passed),
    checks,
  }
}

async function defaultCommands(workdir: string): Promise<Array<{ name: string; command: string; timeout?: number }>> {
  const cmds: Array<{ name: string; command: string; timeout?: number }> = []

  const pkgPath = `${workdir}/package.json`
  if (await fileExists(pkgPath)) {
    try {
      const pkgContent = JSON.parse(await readFile(pkgPath, 'utf8'))
      const scripts = (pkgContent && typeof pkgContent === 'object' && pkgContent.scripts) || {}
      if (scripts.build) {
        cmds.push({ name: 'build', command: 'npm run build 2>&1' })
      }
      if (scripts.test) {
        cmds.push({ name: 'test', command: 'npm test 2>&1' })
      }
      if (scripts.lint) {
        cmds.push({ name: 'lint', command: 'npm run lint 2>&1' })
      }
    } catch {
      // ignore JSON parse errors
    }
  }

  const hasPyproject = await fileExists(`${workdir}/pyproject.toml`)
  if (hasPyproject) {
    cmds.push({
      name: 'python-compile',
      command: '(python3 -m py_compile $(find . -name "*.py" -not -path "./.venv/*" -not -path "./node_modules/*" | head -20) 2>&1) || (python -m py_compile $(find . -name "*.py" -not -path "./.venv/*" -not -path "./node_modules/*" | head -20) 2>&1)',
    })
  }

  return cmds
}

async function fileExists(path: string): Promise<boolean> {
  try {
    await access(path)
    return true
  } catch {
    return false
  }
}