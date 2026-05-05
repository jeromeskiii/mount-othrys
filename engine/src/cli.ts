#!/usr/bin/env node

import { Command } from 'commander'
import { TITAN_REGISTRY, getTitan, listTitans } from './modes/registry.js'
import { TitanMode } from './modes/types.js'
import { route, routeExplicit } from './router.js'
import { WorkflowRunner } from './workflow/runner.js'
import { PythonTitanAdapter } from './adapters/python-adapter.js'
import { ThemisAdapter } from './adapters/themis-adapter.js'
import { HeraclesAdapter } from './adapters/heracles-adapter.js'
import { TitanAdapter } from './adapters/types.js'
import { loadConfig, resolveVenvs } from './config.js'

const program = new Command()

program
  .name('mount-othrys')
  .description('Mount Othrys — Unified Titan Intelligence')
  .version('0.1.0')

program
  .command('route')
  .description('Classify and route a request to the appropriate Titan')
  .argument('<message>', 'natural-language request')
  .option('--json', 'output as JSON')
  .option('--execute', 'also execute the routed command')
  .option('--workdir <dir>', 'working directory', '.')
  .action(async (message: string, opts: { json?: boolean; execute?: boolean; workdir?: string }) => {
    const result = route(message)
    if (opts.json) {
      console.log(JSON.stringify({
        message: message.slice(0, 200),
        titan: result.config.name.toLowerCase(),
        mode: result.mode,
        domain: result.config.role,
        reason: result.reason,
      }, null, 2))
    } else {
      console.log(`  → ${result.config.name} (${result.config.role})`)
      console.log(`    Reason: ${result.reason}`)
    }

    if (opts.execute) {
      const config = loadConfig({ rootDir: opts.workdir ?? '.' })
      const venvs = resolveVenvs(config.rootDir)
      const adapters = buildAdapters(config, venvs)
      const runner = new WorkflowRunner(adapters, { rootDir: config.rootDir, workdir: opts.workdir ?? '.' })
      const workflowResult = await runner.run(message, { rootDir: config.rootDir, workdir: opts.workdir })
      if (opts.json) {
        console.log(JSON.stringify(workflowResult, null, 2))
      } else {
        console.log(`\n${workflowResult.output}`)
      }
      process.exit(workflowResult.verification.passed ? 0 : 1)
    }
  })

program
  .command('titan')
  .description('Show Titan info or list all Titans')
  .argument('[name]', 'Titan name')
  .option('--list', 'list all Titans')
  .option('--json', 'output as JSON')
  .action((name: string | undefined, opts: { list?: boolean; json?: boolean }) => {
    if (opts.list || !name) {
      const titans = listTitans()
      if (opts.json) {
        console.log(JSON.stringify(titans.map(t => ({
          name: t.name.toLowerCase(),
          domain: t.role,
          model: t.model ?? 'default',
          description: t.description,
          adapter: t.adapterType,
        })), null, 2))
      } else {
        console.log('Available Titans:\n')
        for (const t of titans) {
          console.log(`  ${t.name.padEnd(10)} (${t.role})`)
          console.log(`             ${t.description}`)
          console.log(`             adapter: ${t.adapterType}, model: ${t.model ?? 'default'}`)
          console.log()
        }
      }
      return
    }

    const titan = getTitan(name)
    if (opts.json) {
      console.log(JSON.stringify({
        name: titan.name.toLowerCase(),
        domain: titan.role,
        model: titan.model ?? 'default',
        description: titan.description,
        toolAccess: titan.toolAccess,
        toolBlocked: titan.toolBlocked,
        adapter: titan.adapterType,
        keywords: titan.keywords,
      }, null, 2))
    } else {
      console.log(`Titan: ${titan.name}`)
      console.log(`Domain: ${titan.role}`)
      console.log(`Description: ${titan.description}`)
      console.log(`Adapter: ${titan.adapterType}`)
      console.log(`Tool access: ${titan.toolAccess.join(', ')}`)
      console.log(`Tool blocked: ${titan.toolBlocked.join(', ') || '(none)'}`)
      console.log(`Keywords: ${titan.keywords.join(', ')}`)
    }
  })

program
  .command('ask')
  .description('Route and execute a natural-language request')
  .argument('<message>', 'natural-language request')
  .option('--titan <mode>', 'override: force specific Titan mode')
  .option('--workdir <dir>', 'working directory', '.')
  .option('--json', 'output as JSON')
  .action(async (message: string, opts: { titan?: string; workdir?: string; json?: boolean }) => {
    const config = loadConfig({ rootDir: opts.workdir ?? '.' })
    const venvs = resolveVenvs(config.rootDir)
    const adapters = buildAdapters(config, venvs)
    const runner = new WorkflowRunner(adapters, { rootDir: config.rootDir, workdir: opts.workdir ?? '.' })

    const result = await runner.run(message, {
      rootDir: config.rootDir,
      workdir: opts.workdir,
      titanOverride: opts.titan,
    })

    if (opts.json) {
      console.log(JSON.stringify(result, null, 2))
    } else {
      console.log(`  Classification: ${result.mode} (${result.metadata.reason ?? 'routed'})`)
      console.log(`\n${result.output}`)
      if (!result.verification.passed) {
        console.log('\nVerification failures:')
        for (const check of result.verification.checks.filter(c => !c.passed)) {
          console.log(`  ✗ ${check.name}: ${check.detail}`)
        }
      }
    }

    process.exit(result.verification.passed ? 0 : 1)
  })

program
  .command('config')
  .description('View or edit engine configuration')
  .option('--json', 'output as JSON')
  .option('--set-model <model>', 'set default model')
  .option('--set-api-key <key>', 'set API key')
  .action((opts: { json?: boolean; setModel?: string; setApiKey?: string }) => {
    const config = loadConfig()
    if (opts.setModel) config.defaultModel = opts.setModel
    if (opts.setApiKey) config.apiKeys['default'] = opts.setApiKey

    if (opts.json) {
      console.log(JSON.stringify({
        defaultModel: config.defaultModel,
        apiKeys: Object.keys(config.apiKeys).length ? '***configured***' : '(none)',
        thinkingBudget: config.thinkingBudget,
        maxTokens: config.maxTokens,
        timeout: config.timeout,
        rootDir: config.rootDir,
      }, null, 2))
    } else {
      console.log(`  Model:           ${config.defaultModel}`)
      console.log(`  API Keys:        ${Object.keys(config.apiKeys).length ? '***configured***' : '(none)'}`)
      console.log(`  Thinking Budget:  ${config.thinkingBudget}`)
      console.log(`  Max Tokens:       ${config.maxTokens}`)
      console.log(`  Timeout:          ${config.timeout}`)
      console.log(`  Root Dir:         ${config.rootDir}`)
    }
  })

function buildAdapters(config: ReturnType<typeof loadConfig>, venvs: Record<string, string>): Map<string, TitanAdapter> {
  const adapters = new Map<string, TitanAdapter>()
  const defaultApiKey = config.apiKeys['default'] ?? process.env.OPENAI_API_KEY ?? ''

  for (const [, titan] of Object.entries(TITAN_REGISTRY)) {
    if (titan.adapterType === 'native' && titan.mode === TitanMode.THEMIS) {
      adapters.set(titan.mode, new ThemisAdapter({ apiKey: defaultApiKey, model: titan.model }))
    } else if (titan.adapterType === 'native' && titan.mode === TitanMode.HERACLES) {
      adapters.set(titan.mode, new HeraclesAdapter({ apiKey: defaultApiKey }))
    } else if (titan.adapterType === 'python') {
      adapters.set(titan.mode, new PythonTitanAdapter(titan, config.rootDir, venvs, config.apiKeys))
    }
  }

  return adapters
}

program.parse()
