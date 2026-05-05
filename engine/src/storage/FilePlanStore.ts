import { mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import type { PlanStore, StoredPlan } from './PlanStore.js'

export class FilePlanStore implements PlanStore {
  private dir: string

  constructor(rootDir: string) {
    this.dir = join(rootDir, '.sisyphus', 'plans')
  }

  async save(plan: StoredPlan): Promise<void> {
    await mkdir(this.dir, { recursive: true })
    await writeFile(this.pathFor(plan.id), JSON.stringify(plan, null, 2), 'utf8')
  }

  async load(id: string): Promise<StoredPlan | null> {
    try {
      const raw = await readFile(this.pathFor(id), 'utf8')
      return JSON.parse(raw) as StoredPlan
    } catch {
      return null
    }
  }

  async list(): Promise<StoredPlan[]> {
    try {
      const entries = await readdir(this.dir)
      const plans = await Promise.all(
        entries
          .filter(entry => entry.endsWith('.json'))
          .map(entry => this.load(entry.replace(/\.json$/, ''))),
      )
      return plans.filter((plan): plan is StoredPlan => plan !== null)
    } catch {
      return []
    }
  }

  async delete(id: string): Promise<void> {
    await rm(this.pathFor(id), { force: true })
  }

  private pathFor(id: string): string {
    const safeId = id.replace(/[^a-zA-Z0-9._-]/g, '_')
    return join(this.dir, `${safeId}.json`)
  }
}
