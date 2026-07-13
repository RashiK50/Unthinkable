import { describe, expect, it } from "vitest";

import { formatBytes, formatDuration, formatMs } from "./format";

describe("formatMs", () => {
  it("renders mm:ss", () => {
    expect(formatMs(0)).toBe("00:00");
    expect(formatMs(61_000)).toBe("01:01");
    expect(formatMs(3_599_000)).toBe("59:59");
  });
});

describe("formatDuration", () => {
  it("handles null", () => expect(formatDuration(null)).toBe("—"));
  it("renders minutes under an hour", () => expect(formatDuration(48 * 60)).toBe("48 min"));
  it("renders hours + minutes", () => expect(formatDuration(72 * 60)).toBe("1 h 12 min"));
});

describe("formatBytes", () => {
  it("handles null", () => expect(formatBytes(null)).toBe("—"));
  it("renders KB below 1 MB", () => expect(formatBytes(512 * 1024)).toBe("512 KB"));
  it("renders MB with one decimal", () => expect(formatBytes(46_137_344)).toBe("44.0 MB"));
});
