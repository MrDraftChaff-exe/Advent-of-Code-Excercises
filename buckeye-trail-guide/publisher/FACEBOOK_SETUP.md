# Facebook setup — Buckeye Trail Guide

Automate posts to a **Facebook Page** (not a personal profile). Meta only allows API posting as a Page.

---

## Recommended: OAuth paste-code (works when Graph Explorer looks different)

App ID + App Secret are already in `publisher/.env`.

### 1) Create a Facebook Page (if you don’t have one)

https://www.facebook.com/pages/create → name **Buckeye Trail Guide**

### 2) Turn on Facebook Login in your app

1. Open your app at [developers.facebook.com/apps](https://developers.facebook.com/apps/)
2. **Add product** → **Facebook Login** (or **Facebook Login for Business**)
3. Facebook Login → **Settings**
4. Under **Valid OAuth Redirect URIs**, add exactly:

```text
https://localhost:3458/oauth/callback
```

5. Save

### 3) Authorize + paste the redirect URL back

In this environment:

```bash
cd buckeye-trail-guide/publisher
npm run facebook-auth
```

That prints an authorize URL. Open it in your browser (same Facebook account that owns the Page), approve permissions.

The browser will try to load `localhost` and may show an error — **that’s OK**.  
Copy the **full address bar** (it contains `?code=...`) and paste it in chat, or run:

```bash
npm run facebook-auth -- --code 'PASTE_FULL_URL_OR_CODE'
```

We’ll exchange it, find your Page, and write `FACEBOOK_PAGE_ID` + `FACEBOOK_PAGE_ACCESS_TOKEN` into `.env`.

### 4) Verify + post

```bash
npm run facebook-auth
npm run facebook-posts -- --dry-run
npm run facebook-posts
```

---

## Alternate: Graph API Explorer (new UI)

Meta moved the token control. There often is **no big “Access Token” text box** anymore.

1. Open https://developers.facebook.com/tools/explorer/
2. Upper right: **Meta App** → **Buckeye Trail Guide**
3. Upper right: **User or Page** dropdown → **Get User Access Token**
4. In the permission popup, check:
   - `pages_show_list`
   - `pages_manage_posts`
   - `pages_read_engagement`
5. Query box: `me/accounts` → **Submit**
6. Copy the Page’s `id` and `access_token` from the JSON

Paste in chat:

```text
Facebook Page ID: …
Facebook Page access token: …
```

---

## Optional env

```bash
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_PAGE_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_REDIRECT_URI=https://localhost:3458/oauth/callback
```

## Instagram later

Link Instagram Business/Creator to this Page in Meta Business Suite.

## Security

- Never commit `.env`
- If secrets were pasted in chat, rotate App Secret later in App settings → Basic
