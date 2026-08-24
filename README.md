# Facts or Whacks

A browser studio for **9:16 phone videos** in this card format:

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
The African National Congress won that first open vote after decades banned
A 1996 constitution locked in equal rights after apartheid collapsed
Mandela and F. W. de Klerk shared the 1993 Nobel Peace Prize for the talks
Black South Africans had been denied a national vote until those 1994 elections
```

9:16 (1080×1920) frames: the photograph fills the phone canvas and the title, year, **12 sentence facts**, and credit overlay it. A dark veil, per-line plates, and stroked type keep the copy readable on any photo. Episode numbers and hashtags stay off the image. Watermark defaults to `@FactsOrWhacks`. Save a PNG if you want to finish the video in another editor.

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
4. Edit the sentence bullets. Hashtags are for your caption, not the frame.
5. Hit **Play** to preview (subtle original pad, not licensed music).
6. **Save PNG** for a 1080×1920 still you can edit locally. **Download video** renders a WebM.

The bundled catalog is 395 original episode scripts (CSV + Wikimedia still URLs, not pre-made video files). Search an episode, load it, and download the WebM. **Download all 395 stills** fetches the prebuilt 9:16 WebP zip when it is on disk (`public/catalog/*.zip`, gitignored because it is ~82 MB). If that file is missing or the browser blocks it, use the smaller 50-episode packs, or **ZIP stills** for a range. **ZIP videos** encodes in real time (~20 seconds per episode).

To bake Buffer-ready 30s MP4s (1080×1920 H.264 + original royalty-free pad, not a licensed track):

```bash
npm run catalog:pad
npm run catalog:videos
```

That writes `dist/catalog-videos/*.mp4` and 50-episode zips under `public/catalog/facts-or-whacks-videos-*.zip`.

Themes: Cosmic, Ocean, Ember. Reveal modes: all-at-once or line-by-line cascade.

## Tests

```bash
npm test
npm run build
```
