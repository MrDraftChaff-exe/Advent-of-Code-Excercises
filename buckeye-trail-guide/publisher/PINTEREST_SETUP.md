# Pinterest setup — Buckeye Trail Guide

Connect Pinterest so we can auto-create pins for each guide.

## Why it often “doesn’t work”

1. **A normal Pinterest account is not enough** — you need a **developer app** at [developers.pinterest.com/apps](https://developers.pinterest.com/apps/).
2. **Trial access must be approved** (business days). Until then, App secret / API calls stay locked.
3. **Cloud agents can’t use localhost redirects in your browser.** After you approve OAuth, copy the URL from the address bar and paste it back with `--code`.

## Steps

### 1) Business account
Use / convert to [Pinterest Business](https://help.pinterest.com/business/article/get-access-to-pinterest-business-features). Verify email.

### 2) Register developer app
1. Open [developers.pinterest.com/apps](https://developers.pinterest.com/apps/)
2. **Connect app** → name `Buckeye Trail Guide`
3. Submit **Trial access** and wait for the approval email
4. After approval, copy **App ID** + **App secret**
5. Add Redirect URI (press Enter/Add, then Save) exactly:

```text
https://localhost:3457/oauth/callback
```

### 3) Put keys in `.env` (don’t paste secrets in chat)

In `buckeye-trail-guide/publisher/.env`:

```bash
PINTEREST_APP_ID=your_app_id
PINTEREST_APP_SECRET=your_app_secret
PINTEREST_REDIRECT_URI=https://localhost:3457/oauth/callback
```

### 4) Connect (two commands)

```bash
cd buckeye-trail-guide/publisher
npm run pinterest-auth
```

Open the printed URL → Approve → browser may error on localhost (**expected**).

Copy the full address bar (`https://localhost:3457/oauth/callback?code=...&state=...`) and run:

```bash
npm run pinterest-auth -- --code 'PASTE_FULL_URL_HERE'
```

### 5) Pin products

Deploy or host cover images publicly, set:

```bash
PINTEREST_IMAGE_BASE=https://your-deployed-site.com
```

Then:

```bash
npm run pinterest-pins -- --dry-run
npm run pinterest-pins
```

## If Trial is still pending

You’ll see locked secret fields or API errors like consumer type not supported. Options:

- Wait for approval / ask in [Pinterest developer community](https://community.pinterest.biz/)
- Or use **Buffer free** connected to Pinterest (no developer app) — I can queue post copy for you to import

## Security

Never commit `.env`. Never paste App secret / tokens into chat if you can avoid it.
