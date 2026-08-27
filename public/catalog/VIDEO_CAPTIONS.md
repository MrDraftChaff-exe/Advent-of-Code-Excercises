# Video captions

`facts-or-whacks-videos-captions.csv` is one row per video. Open it in Sheets or Excel, click `copy_caption`, copy. That cell is the description, `@FactsOrWhacks`, and hashtags on a single line.

How to match a file:

1. Find the MP4 name in `video_filename` (example: `030-end-of-apartheid.mp4`).
2. Catalog files live in `video_zip_pack` as `path_inside_zip`.
3. Click `copy_caption` once and paste under the Reel. `description` is the same text without handle/hashtags. `hashtags` is the tag list only.

Episode `001` is pack `001-050`. Episode `351` is pack `351-395`. Rows `396` (Dolly Parton), `397` (Tim Curry), and `398` (Peter Cullen) are extras, not in the 395 packs. Buffer’s CSV bulk upload cannot attach these videos; paste `copy_caption` in the composer.

## Dolly Parton extra post

Load the **Dolly Parton** template in the studio, or copy row `396`. Caption file: [`dolly-parton-post.txt`](dolly-parton-post.txt). Video filename: `396-dolly-parton.mp4`.

## Tim Curry extra post

Load the **Tim Curry** template, or copy row `397`. Caption file: [`tim-curry-post.txt`](tim-curry-post.txt). Video filename: `397-tim-curry.mp4`.

## Peter Cullen extra post

Load the **Peter Cullen** template, or copy row `398`. Caption file: [`peter-cullen-post.txt`](peter-cullen-post.txt). Video filename: `398-peter-cullen.mp4`.
