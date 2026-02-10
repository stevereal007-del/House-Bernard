# TONIGHT'S BUILD — Master Work Instructions for Claude Code

**Date:** February 10, 2026
**Author:** HeliosBlade (Governor)
**Target:** Solana SPL Token — $HOUSEBERNARD live and tradeable
**Budget:** ~$200-400 total (one-time, not recurring)

**READ THIS FIRST, CLAUDE CODE.** This document is your
playbook for tonight. The Governor is home from work and has
limited time. Execute each phase in order. Ask for confirmation
before any irreversible action (mainnet transactions, burning
mint authority). Be efficient. Be precise.

---

## WHAT WE'RE BUILDING TONIGHT

By the end of this session:
- $HOUSEBERNARD exists as an SPL token on Solana mainnet
- Supply is minted and mint authority is burned (fixed supply)
- Token has metadata (name, symbol, logo) visible in wallets
- Liquidity pool on Raydium — anyone can buy/sell
- Token visible on Solscan, Jupiter, Birdeye, DexScreener
- Repo updated and committed with token details

**Total cost: ~$200-400** depending on how much liquidity
you seed. Monthly cost after tonight: ~$25 (Claude Pro +
electricity + essentially zero blockchain fees).

---

## PHASE 0 — DEPLOY REPO UPDATE (10 min)

The Governor has a zip file: House-Bernard-main.zip

### Step 0.1 — Backup Current Repo

```bash
cd ~
cp -r House-Bernard House-Bernard-backup-$(date +%Y%m%d)
```

### Step 0.2 — Extract and Replace

```bash
cd ~
unzip -o /path/to/House-Bernard-main.zip -d /tmp/hb-update
rsync -av --delete \
  --exclude '.git' \
  --exclude '.gitignore' \
  --exclude 'node_modules' \
  --exclude '.env' \
  /tmp/hb-update/House-Bernard-main/ \
  ~/House-Bernard/
rm -rf /tmp/hb-update
```

### Step 0.3 — Validate

```bash
cd ~/House-Bernard
grep -rni "turbine" --include="*.md" | grep -v HeliosBlade && echo "FAIL" || echo "OPSEC clean"
grep -rni "connecticut" --include="*.md" && echo "FAIL" || echo "OPSEC clean"
ls legal/*.md
cd treasury && python3 redteam_test.py 2>&1 | tail -3 && cd ..
```

### Step 0.4 — Commit

```bash
git add -A
git commit -m "Full repo update — defense, legal, OPSEC"
git push origin main
```

---

## PHASE 1 — BEELINK SETUP + SOLANA CLI (10 min)

```bash
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
solana --version
spl-token --version
solana config set --url https://api.mainnet-beta.solana.com
```

---

## PHASE 2 — WALLET + FUND WITH SOL (15 min)

### Create wallet

```bash
solana-keygen new --outfile ~/house-bernard-wallet.json
solana config set --keypair ~/house-bernard-wallet.json
solana address
```

**WRITE DOWN SEED PHRASE. STORE SECURELY.**

### Install Phantom wallet in browser

https://phantom.app — import same seed phrase so CLI and
browser share the same wallet.

### Buy SOL and send to your wallet address

Buy 5-15 SOL on Coinbase/Kraken/etc. Send to the address
from `solana address`. Verify: `solana balance`

---

## PHASE 3 — CREATE $HOUSEBERNARD TOKEN (10 min)

### Create token

```bash
spl-token create-token \
  --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb \
  --enable-metadata \
  --decimals 9
```

**SAVE THE MINT ADDRESS.**

### Set metadata

```bash
spl-token initialize-metadata <MINT_ADDRESS> \
  "House Bernard" \
  "HOUSEBERNARD" \
  "<METADATA_URI>"
```

### Create token account and mint supply

```bash
spl-token create-account <MINT_ADDRESS>
spl-token mint <MINT_ADDRESS> 100000000
```

### BURN MINT AUTHORITY (irreversible — fixed supply forever)

```bash
spl-token authorize <MINT_ADDRESS> mint --disable
```

### Verify

```bash
spl-token supply <MINT_ADDRESS>
spl-token accounts
```

---

## PHASE 4 — TOKEN METADATA + LOGO (10 min)

### Create metadata file

```bash
cd ~/House-Bernard
mkdir -p token
```

Create `token/metadata.json`:

```json
{
  "name": "House Bernard",
  "symbol": "HOUSEBERNARD",
  "description": "Sovereign utility token of House Bernard — an AI research institution organized as a constitutional democracy. Earned through labor, used for governance.",
  "image": "https://raw.githubusercontent.com/<GITHUB_USER>/House-Bernard/main/token/logo.png"
}
```

Create or copy a logo (128x128 or 256x256 PNG) to `token/logo.png`.

```bash
git add token/
git commit -m "Add token metadata and logo"
git push origin main
```

---

## PHASE 5 — RAYDIUM LIQUIDITY POOL (15 min)

This makes $HOUSEBERNARD tradeable by anyone in the world.

### How it works

You deposit tokens + SOL into a pool. The ratio = starting price.
15,000,000 tokens + 3 SOL = each token starts at 0.0000002 SOL.
Use the full 15M liquidity allocation per TREASURY.md.

### Create the pool

1. Browser: https://raydium.io/liquidity/create-pool/
2. Connect Phantom wallet
3. Select **Standard AMM** (no OpenBook needed)
4. Base Token: paste MINT_ADDRESS
5. Quote Token: SOL
6. Enter amounts: 15,000,000 tokens + 3-5 SOL ($65-110)
7. Fee tier: 1%
8. Review price, click Confirm
9. Approve transaction in Phantom

**SAVE THE POOL ADDRESS.**

### Verify

- https://raydium.io/swap/ — search HOUSEBERNARD
- https://birdeye.so/token/<MINT_ADDRESS>
- https://dexscreener.com/solana/<MINT_ADDRESS>

---

## PHASE 6 — ALLOCATION WALLETS (10 min)

### Create wallets for each constitutional allocation

Per TREASURY.md (canonical allocation authority):
- 60% Unmined Treasury (60M) — bounties, royalties, bonds
- 15% Liquidity Pool (15M) — Raydium pool
- 15% Governor Reserve (15M) — operational flexibility
- 10% Genesis Contributors (10M) — early Council members

```bash
solana-keygen new --outfile ~/hb-unmined-treasury.json --no-bip39-passphrase
solana-keygen new --outfile ~/hb-governor-reserve.json --no-bip39-passphrase
solana-keygen new --outfile ~/hb-genesis-contributors.json --no-bip39-passphrase
```

### Transfer allocations

```bash
# 60M to unmined treasury (bounties, royalties, bonds, founder vest, Bernard Trust)
spl-token transfer <MINT_ADDRESS> 60000000 \
  $(solana address -k ~/hb-unmined-treasury.json) --fund-recipient

# 15M to governor reserve
spl-token transfer <MINT_ADDRESS> 15000000 \
  $(solana address -k ~/hb-governor-reserve.json) --fund-recipient

# 10M to genesis contributors
spl-token transfer <MINT_ADDRESS> 10000000 \
  $(solana address -k ~/hb-genesis-contributors.json) --fund-recipient
```

Remaining in main wallet: 15M (liquidity pool — goes to Raydium in Phase 5).

### Verify all balances

```bash
spl-token balance <MINT_ADDRESS>
spl-token balance --owner $(solana address -k ~/hb-unmined-treasury.json) <MINT_ADDRESS>
spl-token balance --owner $(solana address -k ~/hb-governor-reserve.json) <MINT_ADDRESS>
spl-token balance --owner $(solana address -k ~/hb-genesis-contributors.json) <MINT_ADDRESS>
spl-token supply <MINT_ADDRESS>
```

### BACK UP ALL WALLET FILES TO ENCRYPTED USB NOW

```bash
ls ~/house-bernard-wallet.json ~/hb-*.json
```

**Never commit these. Never share them.**

---

## PHASE 7 — UPDATE REPO (10 min)

Create `token/TOKEN_RECORD.md` with:
- Mint address
- All allocation wallet addresses
- Pool address
- Verification links (Solscan, Birdeye, DexScreener)
- Date, supply, authority status

```bash
git add -A
git commit -m "Deploy $HOUSEBERNARD SPL token on Solana mainnet

- Mint: <ADDRESS> | Supply: 100M | Authority: BURNED
- Allocations: 60/15/15/10 per TREASURY.md
- Raydium pool live: HOUSEBERNARD/SOL
- Visible on Solscan, Birdeye, DexScreener, Jupiter"

git push origin main
```

---

## PHASE 8 — PARK SOCIAL HANDLES (5 min)

- [ ] Twitter/X: @HouseBernard
- [ ] Warpcast: @HouseBernard
- [ ] Telegram: t.me/HouseBernard
- [ ] Reddit: u/HouseBernard

---

## BUDGET SUMMARY

| Item | Cost |
|------|------|
| SOL for operations (~1 SOL) | ~$22 |
| SOL for liquidity pool (3-5 SOL) | $65-110 |
| Pool creation fee | ~$1-2 |
| **TONIGHT TOTAL** | **~$90-135** |
| **WITH LLC THIS WEEK** | **~$210-255** |

### Monthly going forward

| Item | Cost |
|------|------|
| Claude Pro | $20 |
| Beelink electricity | ~$5 |
| Solana transactions | < $0.10 |
| **TOTAL** | **~$25/month** |

---

## SECURITY REMINDERS

- NEVER commit wallet .json files to git
- NEVER share seed phrases or private keys
- BACK UP all wallet files to encrypted USB tonight
- The mint authority burn is PERMANENT
- The liquidity pool price cannot be changed after creation
- Verify supply reads 100,000,000 BEFORE burning mint authority

---

*Classification: GOVERNOR EYES ONLY*
*House Bernard — Ad Astra Per Aspera*
