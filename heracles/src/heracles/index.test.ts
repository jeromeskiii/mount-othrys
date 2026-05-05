import { describe, it, expect } from "vitest"
import { createHeraclesHook, KEYWORD_PATTERNS } from "./index.js"

describe("Heracles Hook", () => {
  describe("keyword detection", () => {
    const hook = createHeraclesHook()

    it("detects 'heracles' keyword", () => {
      expect(hook.detectKeyword("heracles do something")).toBe(true)
      expect(hook.detectKeyword("HERACLES mode")).toBe(true)
      expect(hook.detectKeyword("run heracles task")).toBe(true)
    })

    it("detects 'ultrawork' keyword", () => {
      expect(hook.detectKeyword("ultrawork implement this")).toBe(true)
      expect(hook.detectKeyword("ULTRAWORK mode")).toBe(true)
      expect(hook.detectKeyword("ultrawork finish the task")).toBe(true)
    })

    it("detects 'ulw' keyword", () => {
      expect(hook.detectKeyword("ulw do something")).toBe(true)
      expect(hook.detectKeyword("ULW mode")).toBe(true)
    })

    it("does not detect when keyword not present", () => {
      expect(hook.detectKeyword("implement this feature")).toBe(false)
      expect(hook.detectKeyword("do the work")).toBe(false)
    })
  })

  describe("message generation", () => {
    const hook = createHeraclesHook()

    it("returns planner message for planner context", () => {
      const message = hook.getMessage(true)
      expect(message).toContain("PLANNER")
      expect(message).toContain(".sisyphus/")
    })

    it("returns executor message for non-planner context", () => {
      const message = hook.getMessage(false)
      expect(message).toContain("HERACLES MODE ENABLED")
      expect(message).toContain("ABSOLUTE CERTAINTY REQUIRED")
    })
  })

  describe("hook creation", () => {
    it("creates hook with default options", () => {
      const hook = createHeraclesHook()
      expect(hook.name).toBe("heracles")
      expect(hook.enabled).toBe(true)
    })

    it("creates disabled hook when option set", () => {
      const hook = createHeraclesHook({ enabled: false })
      expect(hook.enabled).toBe(false)
    })

    it("uses custom messages when provided", () => {
      const customPlanner = "CUSTOM PLANNER"
      const customExecutor = "CUSTOM EXECUTOR"
      const hook = createHeraclesHook({
        customPlannersMessage: customPlanner,
        customExecutorMessage: customExecutor,
      })
      expect(hook.getMessage(true)).toBe(customPlanner)
      expect(hook.getMessage(false)).toBe(customExecutor)
    })
  })

  describe("reminder creation", () => {
    const hook = createHeraclesHook()

    it("creates reminder with system-reminder wrapper", () => {
      const reminder = hook.createHeraclesReminder(false)
      expect(reminder).toContain("<system-reminder>")
      expect(reminder).toContain("</system-reminder>")
      expect(reminder).toContain("HERACLES MODE ENABLED")
    })
  })
})
