import { beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  vi.unstubAllGlobals();
});

describe("player profile storage", () => {
  it("round trips a complete profile", async () => {
    const data = new Map<string, string>();
    vi.stubGlobal("window", {
      localStorage: {
        getItem: (key: string) => data.get(key) ?? null,
        setItem: (key: string, value: string) => data.set(key, value),
      },
    });
    const { readPlayerProfile, savePlayerProfile } = await import("./profile");
    const profile = {
      name: "Alex",
      avatar: { shape: "spark", expression: "wink", color: "purple" },
    } as const;
    savePlayerProfile(profile);
    expect(readPlayerProfile()).toEqual(profile);
    expect(data.has("mtmai.player.v1")).toBe(true);
  });
  it("rejects malformed persisted data", async () => {
    vi.stubGlobal("window", {
      localStorage: {
        getItem: () => '{"name":" ","avatar":{"shape":"unknown"}}',
      },
    });
    const { readPlayerProfile } = await import("./profile");
    expect(readPlayerProfile()).toBeNull();
  });
  it("retains a profile in memory when storage throws", async () => {
    vi.stubGlobal("window", {
      localStorage: {
        getItem: () => {
          throw Error("blocked");
        },
        setItem: () => {
          throw Error("blocked");
        },
      },
    });
    const { readPlayerProfile, savePlayerProfile } = await import("./profile");
    const profile = {
      name: "Sam",
      avatar: { shape: "droplet", expression: "wow", color: "red" },
    } as const;
    savePlayerProfile(profile);
    expect(readPlayerProfile()).toEqual(profile);
  });
});
