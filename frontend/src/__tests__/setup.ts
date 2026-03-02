// src/__tests__/setup.ts
import "@testing-library/jest-dom/vitest";

/**
 * Mock sessionStorage per test environment.
 * jsdom fornisce sessionStorage ma conviene resettarlo tra i test.
 */
beforeEach(() => {
  sessionStorage.clear();
});
