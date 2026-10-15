#!/usr/bin/env node
/**
 * Copy the canonical routing table into the engine's build output (G-3).
 *
 * The table's source of truth lives in the `othrys` Python package because that
 * is the artifact both languages install, and the wheel carries it automatically.
 * The engine reads it at runtime, but TypeScript cannot import it — it sits
 * outside this package's `rootDir`, which would break `tsc`'s emit. The engine
 * therefore reads it from disk, and needs a copy beside its own compiled output
 * so it does not depend on the monorepo layout being present on disk.
 *
 * Runs as part of `npm run build`, after `tsc`. Pass `--out <dir>` to target a
 * different directory (used by the regression test).
 */
import { copyFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const engineRoot = resolve(here, '..')
const SOURCE = resolve(engineRoot, '..', 'othrys', 'src', 'othrys', 'routing.table.json')

function resolveOutDir(argv) {
  const flag = argv.indexOf('--out')
  if (flag === -1) return join(engineRoot, 'dist', 'routing')
  const value = argv[flag + 1]
  if (!value) {
    console.error('[sync-routing-table] --out requires a directory')
    process.exit(2)
  }
  return resolve(value)
}

if (!existsSync(SOURCE)) {
  console.error(`[sync-routing-table] canonical table not found at ${SOURCE}`)
  process.exit(1)
}

const outDir = resolveOutDir(process.argv.slice(2))
const target = join(outDir, 'routing.table.json')

mkdirSync(outDir, { recursive: true })
copyFileSync(SOURCE, target)
console.log(`[sync-routing-table] copied ${SOURCE} -> ${target}`)