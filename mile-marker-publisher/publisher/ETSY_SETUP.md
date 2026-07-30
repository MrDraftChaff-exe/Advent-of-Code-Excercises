# Etsy setup — Mile Marker Publisher

Push the same kits to Etsy with the publisher CLI.

## 1) Create an Etsy shop (if you don’t have one)

1. Go to [etsy.com/sell](https://www.etsy.com/sell)  
2. Finish shop setup (name can be **MileMarkerPublisher** or similar)  
3. Confirm you can open the Shop Manager

## 2) Create a developer app

1. Open **[etsy.com/developers/your-apps](https://www.etsy.com/developers/your-apps)**  
2. **Create a new app**  
   - Name: `Mile Marker Publisher`  
   - Description: Personal tool to publish my digital Columbus field kits  
3. After it’s created, open the app and copy:
   - **Keystring**
   - **Shared secret**
4. Set **Callback URL / Redirect URI** to exactly:

```text
https://localhost:3456/oauth/callback
```

(Must be `https`, no trailing slash.)

## 3) Put keys in `.env` (do not paste secrets in chat)

Edit `mile-marker-publisher/publisher/.env`:

```bash
ETSY_API_KEY=your_keystring:your_shared_secret
# or:
# ETSY_API_KEY=your_keystring
# ETSY_SHARED_SECRET=your_shared_secret
```

Leave `ETSY_ACCESS_TOKEN` / `ETSY_SHOP_ID` empty — the auth script fills them.

## 4) Connect OAuth (one-time)

From this environment:

```bash
cd mile-marker-publisher/publisher
node src/etsy-auth.js
```

- Open the printed URL in your browser  
- Approve access (listings + shops)  
- Accept the localhost certificate warning  
- Tokens + shop id are written to `.env` automatically  

## 5) Publish kits to Etsy

```bash
cd mile-marker-publisher/publisher
npm run publish -- --platforms etsy
# or both:
npm run publish -- --platforms gumroad,etsy
```

`ETSY_AUTO_PUBLISH=true` (set by auth script) activates listings after files upload.  
If Etsy asks for payment/billing setup first, finish that in Shop Manager, then re-run publish.

## Scopes used

`listings_r listings_w listings_d shops_r shops_w`

## Security

- Never commit `.env`  
- Never paste Etsy secrets/tokens into chat  
- Access tokens expire ~1 hour; the publisher refreshes via `ETSY_REFRESH_TOKEN`
