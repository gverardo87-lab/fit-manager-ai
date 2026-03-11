import { describe, expect, it } from "vitest";

import { getConnectivityOnboardingPrompt } from "@/components/dashboard/connectivity-onboarding";

describe("getConnectivityOnboardingPrompt", () => {
  it("propone trusted devices quando il profilo e locale", () => {
    const prompt = getConnectivityOnboardingPrompt("local_only");

    expect(prompt).toEqual(
      expect.objectContaining({
        id: "configure-trusted-devices",
      }),
    );
  });

  it("propone portale pubblico quando il profilo e trusted_devices", () => {
    const prompt = getConnectivityOnboardingPrompt("trusted_devices");

    expect(prompt).toEqual(
      expect.objectContaining({
        id: "configure-public-portal",
      }),
    );
  });

  it("non propone nulla quando il profilo e gia public_portal", () => {
    expect(getConnectivityOnboardingPrompt("public_portal")).toBeNull();
  });
});
