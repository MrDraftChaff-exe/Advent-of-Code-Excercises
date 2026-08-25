# Video captions

`facts-or-whacks-videos-captions.csv` is one row per episode, mapped to the 30s MP4s.

How to match a file:

1. Find the MP4 name in `video_filename` (example: `030-end-of-apartheid.mp4`).
2. That file lives in `video_zip_pack` as `path_inside_zip`.
3. Copy `paste_caption` into Buffer. `description` is the same text without handle/hashtags. `hashtags` is the tag list only.

Episode `001` is pack `001-050`. Episode `351` is pack `351-395`. Buffer’s CSV bulk upload cannot attach these videos; paste captions in the composer.
