# Etsy setup — PAUSED

**Status: out of the active pipeline.** Etsy listing/transaction fees are too expensive for Buckeye Trail Guide right now. Sell on **Gumroad** only.

The auth + publisher code (`etsy-auth.js`, `platforms/etsy.js`) is kept in the repo for a later reopen. `npm run publish -- --platforms etsy` will refuse with a pause message until we re-enable it in `platforms/index.js`.

When fees make sense again:

1. Un-pause in `publisher/src/platforms/index.js`
2. Follow the original steps below
3. Re-add checklist items in `launch/CHECKLIST.md`

---

## Original setup (reference only)

### 1) Create an Etsy shop (if you don’t have one)

1. Go to [etsy.com/sell](https://www.etsy.com/sell)  
2. Finish shop setup on a personal device / personal email  

### 2) Create a developer app

1. Open **[etsy.com/developers/your-apps](https://www.etsy.com/developers/your-apps)**  
2. Create an app; copy keystring + shared secret into `publisher/.env`  

### 3) OAuth

```bash
cd buckeye-trail-guide/publisher
npm run etsy-auth
```

### 4) Publish (only after un-pausing)

```bash
npm run publish -- --platforms etsy
```

## Security

- Never paste Etsy secrets/tokens into chat  
- Never commit `.env`
