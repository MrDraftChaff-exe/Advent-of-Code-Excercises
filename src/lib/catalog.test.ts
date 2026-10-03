import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import {
  cleanBullet,
  episodeToReel,
  extractYear,
  parseCatalogCsv,
  parseCatalogJson,
  splitBullets,
  TARGET_FACT_COUNT,
} from "./catalog";

const SAMPLE = `topic_number,title,hook,video_prompt,on_screen_bullets,image_url,hashtags,caption
30,End of Apartheid,27 years in prison. Then he became PRESIDENT.,prompt,"Apartheid was South Africa's legal system of racial segregation (1948-1994). | Nelson Mandela spent 27 years in prison — a key part of the story of End of Apartheid. | First democratic elections held April 27, 1994.",https://example.com/mandela.jpg,#NelsonMandela #Apartheid,caption
`;

describe("catalog", () => {
  it("strips generated filler tails from bullets", () => {
    expect(
      cleanBullet(
        "Boston Tea Party — 342 chests dumped — a key part of the story of American Revolution.",
      ),
    ).toBe("Boston Tea Party — 342 chests dumped");
  });

  it("keeps hashtags off on-screen bullets", () => {
    expect(
      cleanBullet(
        "They rewrote the rules. #HistoryTok #Enlightenment Reason changed the world.",
      ),
    ).toBe("They rewrote the rules. Reason changed the world.");
  });

  it("drops prompt-meta leftover lines", () => {
    expect(
      cleanBullet("Tone: dramatic, fast-paced, documentary style. 9:16 vertical."),
    ).toBe("");
    expect(cleanBullet("Hook: Buried ALIVE in 24 hours.")).toBe("");
  });

  it("splits pipe bullets and pulls a year", () => {
    const bullets = splitBullets(
      "Bastille — July 14 1789. | King Louis XVI guillotined.",
    );
    expect(bullets).toHaveLength(2);
    expect(extractYear("French Revolution", ...bullets)).toBe("1789");
  });

  it("parses the catalog CSV into a reel", () => {
    const [ep] = parseCatalogCsv(SAMPLE);
    expect(ep.n).toBe(30);
    expect(ep.title).toBe("End of Apartheid");
    expect(ep.bullets[1]).toBe("Nelson Mandela spent 27 years in prison");
    const reel = episodeToReel(ep);
    expect(reel.episode).toBe("30");
    expect(reel.year).toBe("1994");
    expect(reel.handle).toBe("@FactsOrWhacks");
    expect(reel.imageCaption).toBe(
      "27 years in prison. Then he became PRESIDENT.",
    );
    expect(reel.hashtags).toContain("#Apartheid");
  });

  it("parses compact JSON catalog rows", () => {
    const [ep] = parseCatalogJson([
      {
        n: 1,
        title: "The Enlightenment",
        hook: "Reason changed the world forever.",
        bullets: ["Voltaire challenged kings."],
        image: "https://example.com/a.jpg",
        tags: "#HistoryTok",
      },
    ]);
    expect(ep.title).toBe("The Enlightenment");
    expect(episodeToReel(ep).theme).toBe("cosmic");
  });

  it("uses Commons credit from JSON when present", () => {
    const [ep] = parseCatalogJson([
      {
        n: 2,
        title: "American Revolution",
        hook: "13 colonies said no.",
        bullets: ["Declaration signed 1776."],
        image: "/images/catalog/002-american-revolution.jpg",
        tags: "#USHistory",
        credit: "John Trumbull · Public domain",
        source: "https://commons.wikimedia.org/wiki/File:Declaration_of_Independence_(1819),_by_John_Trumbull.jpg",
      },
    ]);
    expect(ep.credit).toContain("Trumbull");
    expect(episodeToReel(ep).imageCredit).toContain("Trumbull");
    expect(episodeToReel(ep).imageUrl.startsWith("/images/catalog/")).toBe(true);
  });
});

describe("bundled catalog copy", () => {
  const raw = JSON.parse(
    readFileSync("public/catalog/episodes.json", "utf8"),
  ) as unknown;
  const catalog = parseCatalogJson(raw);

  it("gives every episode twelve on-screen facts", () => {
    expect(catalog).toHaveLength(395);
    for (const ep of catalog) {
      expect(ep.bullets, `episode ${ep.n}`).toHaveLength(TARGET_FACT_COUNT);
    }
  });

  it("keeps leftover prompt and hashtag copy off the facts", () => {
    for (const ep of catalog) {
      for (const bullet of ep.bullets) {
        expect(bullet, `${ep.n}: ${bullet}`).not.toMatch(/#/);
        expect(bullet, `${ep.n}: ${bullet}`).not.toMatch(/9:16/);
        expect(bullet, `${ep.n}: ${bullet}`).not.toMatch(
          /^(Hook|Tone|Cover|Create):/i,
        );
        expect(bullet, `${ep.n}: ${bullet}`).not.toMatch(/documentary style/i);
        expect(bullet, `${ep.n}: ${bullet}`).not.toMatch(
          /from classrooms to documentaries/i,
        );
        expect(bullet, `${ep.n}: ${bullet}`).not.toMatch(/ the\.$/);
      }
    }
  });

  it("keeps the signed-off apartheid facts", () => {
    const ep = catalog.find((row) => row.n === 30);
    expect(ep?.bullets[0]).toMatch(/Apartheid was South Africa/);
    expect(ep?.bullets[11]).toMatch(/1994 elections/);
  });
});
