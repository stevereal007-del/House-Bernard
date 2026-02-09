# House Bernard Defense Protocol

## Purpose

This document establishes the canonical identity of House Bernard and provides a playbook for responding to brand attacks, token scams, and impersonation attempts.

---

## Canonical Sources of Truth

**If it's not listed here, it's not official.**

| Asset | Official Location | Status |
|-------|-------------------|--------|
| **GitHub** | github.com/HouseBernard/House-Bernard | ✅ Active |
| **Token Contract** | TBD | ⏳ Pending |
| **Treasury Wallet** | TBD | ⏳ Pending |
| **Governor Wallet** | TBD | ⏳ Pending |

### Reserved Handles (Claim These)

Before public visibility, secure these:

- [ ] X/Twitter: @HouseBernard or @House_Bernard
- [ ] GitHub: ✅ HouseBernard/House-Bernard
- [ ] ENS: housebernard.eth
- [ ] Solana Domain: housebernard.sol
- [ ] Base Domain: housebernard.base

---

## Known Attack Vectors

Based on documented incidents (OpenClaw hijack, ClawHub malware), expect these attacks if House Bernard gains visibility:

### 1. Token Squatting

**What happens:** Scammers launch fake tokens like `$BERNARD`, `$HOUSEBERNARD2`, `$HBERNARD` before or after your official launch.

**Defense:**
- Launch first, document the contract address immediately
- Pin contract address in GitHub README, TREASURY.md, and all social bios
- Never acknowledge fake tokens by name (don't give them SEO)

### 2. Username Sniping

**What happens:** If you rename or abandon a social handle, scammers claim it within seconds and impersonate you.

**Defense:**
- Never rename accounts; create new ones if needed and keep old ones dormant
- Secure handles on platforms you don't use yet (park them)

### 3. Malicious "Skills" or Plugins

**What happens:** Third parties create fake House Bernard integrations, browser extensions, or marketplace "skills" that steal credentials.

**Defense:**
- Maintain a list of official integrations (currently: none)
- Explicitly state "we have no browser extensions" until you do
- Any official plugins will be announced in this repo first

### 4. Phishing Sites

**What happens:** Fake websites (housebernard.io, house-bernard.com, etc.) mimic your interface to steal wallet credentials.

**Defense:**
- Register obvious domain variations (or document which ones you don't own)
- Official communications only via GitHub or documented channels
- Never ask users for seed phrases or private keys

### 5. Social Engineering

**What happens:** Scammers pose as "House Bernard team members" in Discord, Telegram, or DMs offering "support" or "airdrops."

**Defense:**
- House Bernard communicates via Discord DM to the AchillesRun agent (Phase 0)
- The Governor will never DM you first
- There are no airdrops unless announced in this repository

---

## Threat Landscape Validation

In February 2026, VirusTotal detected hundreds of malicious skills in the OpenClaw ClawHub marketplace, including trojan infostealers (Atomic Stealer / AMOS) and backdoors disguised as helpful automation. Cisco's independent audit confirmed that OpenClaw agents with elevated privileges create a new class of supply-chain attack surface.

House Bernard's Executioner pipeline, AST-based security scanner, and Docker+seccomp isolation were designed to prevent exactly this class of attack. The security_scanner.py bans subprocess, exec, eval, pickle, and network imports at the AST level — the exact vectors used in the ClawHub attacks. Lab B's intent integrity tests (I1-I6) specifically test for behavioral manipulation through prompt injection and disguised payloads.

When House Bernard skills are published to ClawHub, they pass through three layers of defense: VirusTotal Code Insight scan, House Bernard's own security_scanner.py, and the Executioner's Docker sandbox with seccomp lockdown. Defense in depth, not defense by hope.

References: blog.virustotal.com/2026/02/from-automation-to-infection-how.html, blogs.cisco.com/ai/personal-ai-agents-like-openclaw-are-a-security-nightmare

---

## If You See a Fake Token

### For Community Members

1. **Do not buy it** — Any token not matching our official contract address is fraudulent
2. **Do not engage** — Don't argue with scammers; it gives them visibility
3. **Report it** — Flag on the relevant platform (DEX, social media)
4. **Verify here** — Check this document for the canonical contract address

### For the Governor

1. **Do not acknowledge the fake token by name publicly**
2. **Post a single clarification** pointing to this document
3. **Do not threaten legal action** (invites more attention)
4. **Document the incident** in the Ledger for the record

---

## What House Bernard Will Never Do

- DM you first asking for funds or wallet access
- Ask for your seed phrase or private keys
- Launch a token without updating this repository first
- Run a "presale" or "private sale" via DMs
- Promise guaranteed returns or "alpha"

**If someone claiming to be House Bernard does any of these things, they are a scammer.**

---

## Incident Response Template

When a scam is detected, post this (modify as needed):

```
⚠️ SCAM ALERT

A fraudulent token/account is impersonating House Bernard.

THE ONLY OFFICIAL CONTRACT ADDRESS IS:
[Insert from TREASURY.md]

THE ONLY OFFICIAL GITHUB IS:
github.com/HouseBernard/House-Bernard

We have no Discord, Telegram, or other social channels at this time.
Do not send funds to any address not listed in our GitHub repository.
```

---

## The Hard Truth

**We cannot protect you from yourself.**

If you buy a fake token without verifying the contract address, we cannot help you recover those funds. Crypto transactions are irreversible. The defense protocol works only if you verify before you transact.

The canonical source is always this repository. Bookmark it. Check it. Trust nothing else.

---

## Verification Checklist

Before interacting with anything claiming to be House Bernard:

- [ ] Is the contract address listed in TREASURY.md?
- [ ] Is the GitHub repo at HouseBernard/House-Bernard?
- [ ] Was the announcement made in this repository?
- [ ] Did you navigate there directly (not via a link in DMs)?

If any answer is "no" — do not proceed.

---

*Last Updated: February 2025*  
*Document Version: 0.1*
