# Facebook setup — Buckeye Trail Guide

Automate posts to a **Facebook Page** (not a personal profile). Meta only allows API posting as a Page.

Pinterest is paused for now.

## 1) Create a Facebook Page (required)

1. On desktop, open [facebook.com/pages/create](https://www.facebook.com/pages/create)
2. Create a Page:
   - Name: **Buckeye Trail Guide**
   - Category: e.g. **Shopping & retail** / **Writer** / **Local business**
3. Add profile photo: use `brand/profiles/gumroad-avatar.png`
4. Confirm you can open **Professional dashboard** / Meta Business Suite for that Page

## 2) Easiest token path (Graph API Explorer)

This avoids a brittle OAuth dance for a single-owner Page.

1. Open [developers.facebook.com](https://developers.facebook.com/) → log in  
2. **My Apps** → **Create App**
   - Use case: **Other** / business  
   - App name: `Buckeye Trail Guide`
3. Open [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
4. Select your app in the top-right app dropdown
5. **Generate Access Token** → grant (at least):
   - `pages_show_list`
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_read_user_content` (if shown)
6. Change the query to `GET /me/accounts` → **Submit**
7. In the response, find your Page (`Buckeye Trail Guide`) and copy:
   - `id` → Page ID  
   - `access_token` → Page access token  

### Make the Page token long-lived

1. Still in Explorer, take your **User** token (not Page yet) and open  
   [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)
2. Paste user token → **Extend Access Token** (long-lived user token, ~60 days)
3. In Explorer, use that long-lived **user** token and run `GET /me/accounts` again
4. Copy the Page `access_token` from the response — that Page token is effectively permanent for posting

## 3) Put values in `.env` (don’t paste tokens in chat)

Edit `buckeye-trail-guide/publisher/.env`:

```bash
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token
```

Optional:

```bash
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
```

## 4) Verify + post

```bash
cd buckeye-trail-guide/publisher
npm run facebook-auth
npm run facebook-posts -- --dry-run
npm run facebook-posts
```

`facebook-posts` publishes one Page post per product (message + Gumroad link).

## Instagram later

Link Instagram **Business/Creator** to this same Facebook Page in Meta Business Suite.  
Then we can add IG publishing with extra permissions (`instagram_content_publish`).

## App Review note

For **your own Page only**, Development mode + your admin role is usually enough.  
If Meta blocks posting, the Page token may be missing `pages_manage_posts`, or the app needs Advanced Access / App Review for that permission.

## Security

- Never commit `.env`
- Prefer putting tokens in `.env` yourself instead of pasting in chat
- If a token was shared in chat, revoke it in Meta and generate a new one
