# Feather Hill Maine Coons — local copy

Public snapshot of [featherhillmainecoons.com](https://featherhillmainecoons.com/) for local browsing and self-management.

The live site is **WordPress on GoDaddy** (Beaver Builder + Gravity Forms). This repo holds a **static HTML export** of the public pages so you can open and edit them on your machine without GoDaddy’s editor.

## Pages included

- Home (`/`)
- About Us
- Our Queens and Toms
- Available Kittens
- Past Kittens
- Contact

## Run locally

```bash
./scripts/serve.sh
```

Then open [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

Optional custom port:

```bash
PORT=3000 ./scripts/serve.sh
```

Or without the script:

```bash
cd site && python3 -m http.server 8080
```

## Refresh the export from the live site

```bash
./scripts/reexport.sh
```

Requires `wget` and `python3`.

## What works locally

- Full page layout, images, CSS, and navigation
- Browsing all public pages offline

## What does not work locally (needs WordPress)

- Contact form submissions (Gravity Forms)
- WordPress admin / page editing in the GoDaddy UI
- Dynamic catalog updates until you re-export or move to your own WordPress host

## Taking full ownership later

For a **editable** WordPress install you control (not just a static snapshot):

1. In GoDaddy → your hosting → **cPanel / File Manager** or **FTP**, download `wp-content/` (themes, plugins, uploads).
2. Export the database (phpMyAdmin → Export), or use a plugin such as **All-in-One WP Migration** / **Duplicator**.
3. Import into local WordPress (Local WP, Docker, or `wp-env`) or another host.
4. Point the domain’s DNS away from GoDaddy when you are ready to cut over.

The static `site/` folder here is enough to preview and hand-edit HTML/CSS; use a full WP migration when you want the same admin experience off GoDaddy.
