# Facebook setup — Buckeye Trail Guide

Automate posts to a **Facebook Page** (not a personal profile). Meta only allows API posting as a Page.

Pinterest is paused for now.

---

## Do this now (click path)

### A) Create the Page (if you don’t have it)

1. Open [facebook.com/pages/create](https://www.facebook.com/pages/create)
2. Name: **Buckeye Trail Guide**
3. Category: **Shopping & retail**, **Writer**, or **Local business**
4. Profile photo: `brand/profiles/gumroad-avatar.png` (or `social-avatar.png`)
5. Cover photo: `brand/buckeye-trail-guide-facebook-cover.jpg` (851×315 JPG)

### B) Create a Meta app + Page token

1. Open [developers.facebook.com](https://developers.facebook.com/) → log in with the same Facebook account that owns the Page  
2. **My Apps** → **Create App**
   - Type / use case: **Other** (or Business)
   - App name: `Buckeye Trail Guide`
3. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
4. Top-right: select your **Buckeye Trail Guide** app
5. **Generate Access Token** → allow at least:
   - `pages_show_list`
   - `pages_manage_posts`
   - `pages_read_engagement`
6. In the query box: `me/accounts` → **Submit**
7. In the JSON, find the Page named **Buckeye Trail Guide** and copy:
   - `id`
   - `access_token` ← this is the **Page** token (not the user token in the top field)

### C) Make the Page token long-lived (recommended)

1. Open [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
2. Paste the **user** token from Graph Explorer (the one in the token field, before you switched to Page) → **Debug** → **Extend Access Token**
3. Back in Graph Explorer, paste that long-lived **user** token → run `me/accounts` again
4. Copy the Page `access_token` from the response (Page tokens from a long-lived user token don’t expire for posting)

### D) Hand credentials to the agent / CLI

**Option 1 — paste in chat to the agent** (agent writes `.env` for you):

```text
Facebook Page ID: <id>
Facebook Page access token: <access_token>
```

**Option 2 — run locally / in this environment:**

```bash
cd buckeye-trail-guide/publisher
npm run facebook-auth -- --page-id 'PAGE_ID' --token 'PAGE_ACCESS_TOKEN'
```

Or paste the whole `/me/accounts` response:

```bash
npm run facebook-auth -- --accounts-json '{"data":[{"id":"...","name":"Buckeye Trail Guide","access_token":"..."}]}'
```

### E) Verify + post

```bash
cd buckeye-trail-guide/publisher
npm run facebook-auth
npm run facebook-posts -- --dry-run
npm run facebook-posts
```

`facebook-posts` publishes one Page feed post per product (message + Gumroad link).

---

## Optional: App ID / Secret (token debugging)

In `publisher/.env`:

```bash
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
```

When set, `facebook-auth` can print scopes / expiry via `debug_token`.

---

## Instagram later

Link Instagram **Business/Creator** to this same Facebook Page in Meta Business Suite.  
Then we can add IG publishing with `instagram_content_publish`.

## App Review note

For **your own Page only**, Development mode + your admin role is usually enough.  
If Meta blocks posting, the Page token may be missing `pages_manage_posts`, or the app needs Advanced Access / App Review.

## Security

- Never commit `.env`
- Prefer putting tokens in `.env` yourself instead of pasting in chat when possible
- If a token was shared in chat, revoke it in Meta and generate a new one
