import { describe, it, expect } from "vitest"
import { createThemisAgent, THEMIS_SYSTEM_PROMPT, createThemisReminder } from "./index.js"

describe("Themis Agent", () => {
  describe("agent creation", () => {
    it("creates agent with default options", () => {
      const agent = createThemisAgent()
      expect(agent.name).toBe("themis")
      expect(agent.model).toBe("openai/gpt-5.2")
      expect(agent.temperature).toBe(0.1)
      expect(agent.thinking.budgetTokens).toBe(32000)
    })

    it("creates agent with custom options", () => {
      const agent = createThemisAgent({
        model: "anthropic/claude-opus-4-5",
        temperature: 0.2,
        thinkingBudget: 64000,
      })
      expect(agent.model).toBe("anthropic/claude-opus-4-5")
      expect(agent.temperature).toBe(0.2)
      expect(agent.thinking.budgetTokens).toBe(64000)
    })

    it("uses custom prompt when provided", () => {
      const customPrompt = "Custom Themis prompt"
      const agent = createThemisAgent({ customPrompt })
      expect(agent.prompt).toBe(customPrompt)
    })

    it("has correct tool restrictions", () => {
      const agent = createThemisAgent()
      expect(agent.toolRestrictions).toContain("write")
      expect(agent.toolRestrictions).toContain("edit")
      expect(agent.toolRestrictions).toContain("task")
      expect(agent.toolRestrictions).toContain("delegate_task")
    })
  })

  describe("metadata", () => {
    it("has advisor category", () => {
      const agent = createThemisAgent()
      expect(agent.metadata.category).toBe("advisor")
    })

    it("has expensive cost", () => {
      const agent = createThemisAgent()
      expect(agent.metadata.cost).toBe("EXPENSIVE")
    })

    it("has correct triggers", () => {
      const agent = createThemisAgent()
      expect(agent.metadata.triggers).toHaveLength(3)
      expect(agent.metadata.triggers[0].domain).toBe("Architecture decisions")
      expect(agent.metadata.triggers[1].domain).toBe("Self-review")
      expect(agent.metadata.triggers[2].domain).toBe("Hard debugging")
    })

    it("has useWhen and avoidWhen lists", () => {
      const agent = createThemisAgent()
      expect(agent.metadata.useWhen).toBeDefined()
      expect(agent.metadata.useWhen.length).toBeGreaterThan(0)
      expect(agent.metadata.avoidWhen).toBeDefined()
      expect(agent.metadata.avoidWhen.length).toBeGreaterThan(0)
    })
  })

  describe("system prompt", () => {
    it("contains key themis identity", () => {
      expect(THEMIS_SYSTEM_PROMPT).toContain("Themis")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Strategic Technical Advisor")
    })

    it("contains decision framework", () => {
      expect(THEMIS_SYSTEM_PROMPT).toContain("Bias toward simplicity")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Leverage what exists")
    })

    it("contains response structure guidance", () => {
      expect(THEMIS_SYSTEM_PROMPT).toContain("Bottom line")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Action plan")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Effort estimate")
    })

    it("contains effort estimates", () => {
      expect(THEMIS_SYSTEM_PROMPT).toContain("Quick")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Short")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Medium")
      expect(THEMIS_SYSTEM_PROMPT).toContain("Large")
    })
  })

  describe("reminder creation", () => {
    it("creates system reminder wrapper", () => {
      const reminder = createThemisReminder()
      expect(reminder).toContain("<system-reminder>")
      expect(reminder).toContain("</system-reminder>")
    })

    it("contains consultation mode guidance", () => {
      const reminder = createThemisReminder()
      expect(reminder).toContain("CONSULTATION MODE")
      expect(reminder).toContain("read-only")
    })

    it("contains action guidance", () => {
      const reminder = createThemisReminder()
      expect(reminder).toContain("DO NOT")
      expect(reminder).toContain("DO")
    })
  })
})
