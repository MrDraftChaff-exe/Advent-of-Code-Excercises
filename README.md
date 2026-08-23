# Facts or Whacks

A browser studio for **16:9 history videos** in this card format:

```
The End of Apartheid (1994)
Image: Nelson Mandela voting, 1994

Apartheid was South Africa’s legal system of racial segregation (1948–1994)
Nelson Mandela spent 27 years in prison for anti-apartheid activism
International boycotts and sanctions pressured the white minority government
Mandela was released in 1990 and negotiated a peaceful transition
First democratic elections held April 27, 1994 — Mandela became president
At age 75, he chose reconciliation over revenge
The Truth and Reconciliation Commission addressed past atrocities
South Africa’s transition is studied as a model of peaceful revolution
Hashtags: #NelsonMandela #Apartheid #SouthAfrica #HistoryTok
```

16:9 (1920×1080) frames: the photograph fills the canvas and the title, year, sentence facts, hashtags, and credit overlay it. Episode numbers stay off the video. Watermark defaults to `@FactsOrWhacks`. Save a PNG if you want to finish the video in another editor.

The default template is that apartheid episode. The voting photograph is [Paul Weinberg, 1994, CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Mandela_voting_in_1994.jpg); the credit is printed on the frame so exports keep the attribution.

## Run

```bash
npm install
npm run dev
```

Then open the local URL Vite prints (default `http://localhost:5173`).

## Use

1. Pick a template or start from a blank reel.
2. Set the title and year. The episode number is for the catalog and filenames only — it is not drawn on the video.
3. Add a photo (bundled path, URL, or upload), caption, and credit.
4. Edit the sentence bullets and hashtags.
5. Hit **Play** to preview (subtle original pad, not licensed music).
6. **Save PNG** for a 1920×1080 still you can edit locally. **Download video** renders a WebM.

The bundled catalog is 395 original episode scripts (CSV + Wikimedia still URLs, not pre-made video files). Search an episode, load it, and download the WebM. **ZIP videos** encodes a number range in real time (~20 seconds per episode). **ZIP stills** is much faster.

Themes: Cosmic, Ocean, Ember. Reveal modes: all-at-once or line-by-line cascade.

## Tests

```bash
npm test
npm run build
```
