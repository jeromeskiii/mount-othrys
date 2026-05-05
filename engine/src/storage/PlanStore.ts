export interface StoredPlan {
  id: string
  mode: string
  prompt: string
  plan: string
  status: 'draft' | 'active' | 'completed' | 'failed'
  createdAt: string
  updatedAt: string
  metadata: Record<string, unknown>
}

export interface PlanStore {
  save(plan: StoredPlan): Promise<void>
  load(id: string): Promise<StoredPlan | null>
  list(): Promise<StoredPlan[]>
  delete(id: string): Promise<void>
}
