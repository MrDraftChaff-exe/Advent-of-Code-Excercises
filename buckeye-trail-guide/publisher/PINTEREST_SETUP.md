# Pinterest setup — Buckeye Trail Guide

Connect your Pinterest **Business** account so we can create pins for each guide (set-and-forget marketing).

## 0) What you already did

- [x] Pinterest account created

## 1) Use a Business account

If you created a personal account, convert it:  
[Create / convert to Business](https://help.pinterest.com/business/article/get-access-to-pinterest-business-features)

Verify the email on the account.

## 2) Register a developer app (required)

1. Open **[developers.pinterest.com/apps](https://developers.pinterest.com/apps/)** while logged into that Business account  
2. Accept Developer Terms if prompted  
3. **Connect app** / register a new app:
   - Name: `Buckeye Trail Guide`
   - Description: Personal pin publisher for Buckeye Trail Guide digital downloads
4. Submit for **Trial access** (Pinterest reviews on business days — you may wait for approval email)
5. After approval, open the app → copy:
   - **App ID** (client id)
   - **App secret**
6. Under **Redirect URIs**, add exactly:

```text
https://localhost:3457/oauth/callback
```

(Must match character-for-character. `https`, port `3457`, no trailing slash.)

## 3) Put keys in `.env` (do not paste secrets in chat)

Edit `buckeye-trail-guide/publisher/.env`:

```bash
PINTEREST_APP_ID=your_app_id
PINTEREST_APP_SECRET=your_app_secret
PINTEREST_REDIRECT_URI=https://localhost:3457/oauth/callback
```

Leave access/refresh tokens empty — the auth script fills them.

## 4) Connect OAuth (one-time)

```bash
cd buckeye-trail-guide/publisher
npm run pinterest-auth
```

- Open the printed URL in your browser  
- Approve access  
- Accept the localhost certificate warning if shown  
- Tokens + default board id are written to `.env`

## 5) Create a board (if you don’t have one)

In Pinterest, create a board e.g. **Buckeye Trail Guide** / **Columbus Guides**.  
The auth script will list boards and store `PINTEREST_BOARD_ID`. You can also set it manually in `.env`.

## 6) Post pins

```bash
cd buckeye-trail-guide/publisher
npm run pinterest-pins -- --dry-run
npm run pinterest-pins
```

Pins use product covers + Gumroad links from the catalog.

## Access tiers (important)

| Tier | What you get |
| --- | --- |
| **Trial** | Explore API; some write endpoints may be limited until upgraded |
| **Standard** | Full pin create for production automation |

If Trial blocks `pins:write`, request **Standard** access in the developer portal (they often want a short demo of the OAuth flow).

## Security

- Never commit `.env`  
- Never paste App secret / tokens into chat  
- Rotate secret if it leaks
