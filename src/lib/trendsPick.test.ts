import { describe, expect, it } from "vitest";
import { spawnSync } from "node:child_process";

describe("Google Trends daily pick", () => {
  it("skips junk, holds 9/11 on Sep 10, and keeps history-shaped queries", () => {
    const run = spawnSync(
      "python3",
      [
        "scripts/fetch_trends.py",
        "--fixture",
        "scripts/fixtures/trends-us-sample.xml",
        "--date",
        "2026-09-10",
        "--json",
      ],
      { encoding: "utf8" },
    );
    expect(run.status, run.stderr).toBe(0);
    const payload = JSON.parse(run.stdout) as {
      items: Array<{ title: string; status: string; reason: string }>;
    };
    const byTitle = Object.fromEntries(
      payload.items.map((item) => [item.title, item]),
    );
    expect(byTitle.games.status).toBe("skip");
    expect(byTitle.duolingo.status).toBe("skip");
    expect(byTitle["jaclyn smith on farrah fawcett"].status).toBe("skip");
    expect(byTitle["september 11 2001"].status).toBe("hold");
    expect(byTitle["september 11 2001"].reason).toMatch(/09-11/);
    expect(byTitle["thurgood marshall"].status).toBe("candidate");
  });

  it("promotes 9/11 to a candidate on the anniversary", () => {
    const run = spawnSync(
      "python3",
      [
        "scripts/fetch_trends.py",
        "--fixture",
        "scripts/fixtures/trends-us-sample.xml",
        "--date",
        "2026-09-11",
        "--json",
      ],
      { encoding: "utf8" },
    );
    expect(run.status, run.stderr).toBe(0);
    const payload = JSON.parse(run.stdout) as {
      items: Array<{ title: string; status: string }>;
    };
    const item = payload.items.find((row) => row.title === "september 11 2001");
    expect(item?.status).toBe("candidate");
  });
});
