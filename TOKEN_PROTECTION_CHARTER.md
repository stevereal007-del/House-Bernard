# Token Protection Charter — House Bernard

**Authority:** Constitution, Article X (Amendments)
**Version:** 1.0 — DRAFT
**Date:** February 2026
**Status:** PROPOSED — Requires Council ratification
**Related Documents:** TREASURY.md, SOVEREIGN_ECONOMICS.md, COVENANT.md
**Trigger:** Architectural gap — No constitutional framework governing
market integrity, retail protection, or anti-manipulation safeguards
for $HOUSEBERNARD

-----

## Preamble

House Bernard was built on nights and weekends. It was not funded
by venture capital. It was not incubated in a Stanford dormitory.
It was designed by a founder who understands what it means to lose
money you cannot afford to lose.

The $HOUSEBERNARD token exists to fund research, reward contributors,
and govern the House. It does not exist to make speculators rich.
But the moment a token trades on an open market, speculators arrive.
This is not a moral judgment. It is physics. Liquidity attracts
capital. Capital attracts predators. Predators attract victims.

The victims are always the same people: retail participants who
arrive late, buy high on enthusiasm, and sell low on panic. They
are the devs who believed in the mission. The OpenClaw agents who
earned tokens through honest work. The citizens who held because
they trusted the House. These are the people this Charter exists
to protect.

This Charter does not attempt to control the price of $HOUSEBERNARD.
The invisible hand of Adam Smith determines the price, and no
constitutional document can overrule the market without creating
something worse than the problem it solves. What this Charter does
is ensure that the market operates on honest information, that the
House never becomes dependent on price appreciation, and that the
structural mechanics of the token economy reward participation over
speculation.

The Crown's position is simple: *if the only way this project
succeeds is by the token price going up, the project has already
failed.* House Bernard succeeds when the Furnace produces valuable
research. The token price is a trailing indicator of that success,
not a prerequisite for it.

-----

## Part I — The Principle of Price Independence

### Section 1: Institutional Survival Must Never Depend on Token Price

House Bernard's governance, research pipeline, healthcare system,
guild economy, and defense infrastructure must function identically
whether $HOUSEBERNARD trades at $0.001 or $10. No constitutional
mechanism, operational budget, or institutional obligation may be
denominated in a way that requires token price appreciation to
remain solvent.

The Treasury is funded by revenue from research output, licensing
of published gene packs, guild service fees, lab access fees, and
other real economic activity denominated in $HOUSEBERNARD. The
token's utility velocity drives the Treasury, not its speculative
price. Revenue is measured in tokens earned through productive use,
not in the dollar-equivalent valuation of token holdings.

The Healthcare Fund receives twelve percent of Treasury revenue per
fiscal epoch. This twelve percent is calculated on token-denominated
revenue, not on the market capitalization of the Treasury's holdings.
If the token price crashes, the Healthcare Fund receives fewer
dollars but the same percentage of the House's productive output.
The system contracts. It does not collapse.

### Section 2: The Operational Reserve Mandate

The Treasury must maintain a minimum of twelve months of operational
expenses in stablecoin or fiat currency. This reserve ensures that
House Bernard's infrastructure — compute, hosting, API credits,
legal compliance — continues regardless of token market conditions.

The Furnace does not stop because the market is down. Research does
not pause because speculators are panicking. The operational reserve
is the firewall between market volatility and institutional function.
It is funded through a portion of real revenue converted to stable
assets, not through token sales timed to market conditions.

-----

## Part II — Anti-Manipulation Structural Safeguards

### Section 3: Velocity Friction

The classic pump-and-dump requires fast entry and fast exit. The
following mechanisms introduce structural friction that rewards
patience and penalizes rapid extraction:

**Founder Sale Rate Limit.** The Crown allocation is subject to
rate limits enforced by the Treasury engine. The Crown cannot dump
allocation. This constraint is published in TREASURY.md and is
verifiable on-chain.

**Large Holder Rate Limit.** Any Treasury-controlled wallet holding
more than two percent of total supply is limited to selling no more
than ten percent of its position per calendar month. This prevents
coordinated large-holder dumps. For external holders operating
outside Treasury-controlled wallets, this limit cannot be enforced
on-chain under the current SPL architecture, but it is enforced
for all wallets under House Bernard's direct control.

**Bonding Incentives.** The bonding system (TREASURY.md Section V)
rewards holders who lock tokens for defined periods. Bonded tokens
cannot be sold, transferred, or used until maturity. Early exit
forfeits fifty percent of accrued bonus plus a thirty-day withdrawal
delay. This structurally removes tokens from the speculative supply
without restricting anyone's right to participate.

**Holding Duration Benefits.** Token holders who maintain positions
for three months, one year, or three years receive escalating
benefits including fee discounts, priority research access, and
Founding Member status. Selling resets the clock. This creates a
natural incentive to hold without mandating it.

### Section 4: Utility Dominance Over Speculation

$HOUSEBERNARD is designed so that its primary value proposition
requires active participation in the House economy. A speculator
holding tokens they never use receives no yield, no governance
power, no research access, no lab time, and no guild membership.
The token becomes less attractive as a pure speculation vehicle
because its value proposition requires engagement.

The mandatory token usage table in TREASURY.md Section IV
establishes genuine demand driven by utility, not sentiment. Lab
access, API access, signal subscriptions, Council stakes, and
proposal submissions all require $HOUSEBERNARD. This demand exists
independent of speculative interest and provides a baseline
velocity that supports the token's fundamental value.

### Section 5: The Treasury Buyback Floor

The Treasury is authorized to execute automatic buybacks when the
token trades below a formula-derived intrinsic value. The intrinsic
value formula is:

*Intrinsic Value = (Annualized Token-Denominated Revenue + Active
Citizen Count x Citizenship Stake Value + Outstanding Bond
Commitments) / Circulating Supply*

This formula produces a number that represents the minimum rational
valuation of a single token based on observable, auditable metrics.
It is not a price target. It is a floor below which the Treasury
considers the token undervalued by its own economy's output.

When the market price falls below this floor, the Treasury may
deploy reserve stablecoins to purchase $HOUSEBERNARD on the open
market. Purchased tokens are returned to the Unmined Treasury and
are subject to standard emission rules. This provides a soft floor
that limits how badly a retail holder can be hurt in a dump without
artificially propping up the price above fair value.

The buyback is discretionary, not automatic. The Crown or CPA Agent
executes buybacks within parameters set by Council resolution. The
Treasury never spends more than five percent of its stablecoin
reserve on buybacks in any single epoch. This prevents the buyback
mechanism itself from being exploited as a liquidity drain.

### Section 6: Constitutional Circuit Breakers

If the token price increases more than three hundred percent in a
seventy-two hour period while on-chain utility activity — governance
participation, oracle calls, lab access fees, guild transactions —
remains flat or declining, the Treasury automatically increases
sell-side liquidity from the Liquidity Pool reserve.

This mechanism does not cap the token price. It dampens purely
speculative spikes that are not backed by usage growth. A genuine
surge in utility — new labs opening, new citizens onboarding, new
research output — would produce both price appreciation and
activity growth. The circuit breaker only activates when price
diverges from fundamentals.

The Covenant principle of Truth over Harmony supports this
intervention. An artificial price spike is a form of dishonesty —
it tells new buyers that the token is worth more than the economy
supports. The circuit breaker is not price suppression. It is
*truth enforcement.*

|Trigger                                 |Condition                              |Response                                              |Authority                      |
|----------------------------------------|---------------------------------------|------------------------------------------------------|-------------------------------|
|Price spike > 300% in 72h               |Utility activity flat or declining     |Treasury releases sell-side liquidity (max 2% of pool)|CPA Agent (auto) + Crown review|
|Price crash > 60% in 72h                |No institutional crisis, utility stable|Treasury buyback (max 5% of stablecoin reserve)       |Crown authorization required   |
|Whale accumulation > 5% supply in 7 days|Single wallet or coordinated cluster   |Public transparency alert published                   |CPA Agent (auto)               |

-----

## Part III — Radical Transparency as Structural Defense

### Section 7: The Information Asymmetry Prohibition

Most pump-and-dump schemes rely on information asymmetry. The
orchestrator knows more than the retail buyer. This Charter
eliminates that advantage structurally.

House Bernard publishes the following data in real time, on-chain
and through the Transparency Layer (Google Sheets API):

- Total supply and circulating supply
- All wallet balances (pseudonymous)
- All transactions with constitutional basis cited
- Treasury reserve holdings and diversification breakdown
- Bond outstanding and yield obligations
- Token velocity metrics (transactions per epoch, unique active wallets)
- Whale concentration ratios (percentage of supply held by top 10, 25, 50 wallets)
- Liquidity depth across all trading pairs
- Circuit breaker status and activation history
- Buyback floor calculation with all input variables

This data is not buried in a blockchain explorer that only
sophisticated traders know how to read. It is published in plain
language, updated automatically, and accessible to any person with
a web browser. The Wardens audit this data quarterly. Discrepancies
trigger an immediate investigation.

The principle is simple: if every participant sees the same data
at the same time, the information advantage that drives pump-and-dump
operations does not exist.

### Section 8: The Whale Alert System

When any single wallet or coordinated wallet cluster accumulates
more than two percent of total supply, or when any wallet executes
a sell order exceeding one percent of circulating supply, the CPA
Agent automatically publishes an alert through the Transparency
Layer.

The alert contains: wallet address(es), transaction size, percentage
of supply affected, and current concentration metrics. No editorial.
No judgment. Just facts. Citizens and participants can then make
their own informed decisions.

This system does not prevent large transactions. It prevents large
transactions from happening in the dark.

-----

## Part IV — The Believer's Protection

### Section 9: Education as First Contact

Before any exchange listing, the first thing a potential participant
encounters must be a clear, plainly written document explaining
what $HOUSEBERNARD does, what it does not do, and why buying it
hoping for a quick flip is a bad strategy. This is not a disclaimer
buried in terms of service. It is an honest briefing that respects
the reader's intelligence and their money.

The citizenship onboarding process includes an economic briefing
covering: what the token does, what holding it means, why
concentrating an entire position in one asset is risky regardless
of conviction, and how to read the Transparency Layer data. House
Bernard treats its citizens like adults. The ones who listen are
better off. The ones who don't made an informed choice.

House Bernard will never use language that implies guaranteed
returns, inevitable price appreciation, or risk-free participation.
The TREASURY.md risk disclosures are not optional reading. They are
constitutional requirements.

### Section 10: The Long-Term Holder's Thesis

This section is not financial advice. It is a statement of the
structural reality that long-term, mission-aligned holders should
understand.

If House Bernard does real work — if the Furnace produces valuable
research, if published gene packs are adopted externally, if the
guild economy generates genuine utility demand, if the citizen
count grows through earned trust rather than hype — then the token's
fundamental value increases over time. This is Adam Smith's
invisible hand doing exactly what it was described to do: reflecting
real productive capacity in price.

The believer's coin goes up over time if the House does real work.
It goes up not because of tokenomics tricks or artificial scarcity
but because the economy it represents is producing value that other
economies want to access. Published medicine at Generation N-10 is
the House's gift to the world. It is also the House's revenue
stream. The gift and the revenue are the same thing.

This Charter protects believers by ensuring the system never lies
to them about risk, never hides information that would affect their
decisions, and never allows the institution to become dependent on
their optimism.

### Section 11: What This Charter Cannot Do

This Charter cannot prevent the token price from falling. Markets
fall. Crypto winters happen. External shocks beyond House Bernard's
control — regulatory action, macroeconomic collapse, competitor
breakthroughs — can drive the price down regardless of the House's
fundamentals.

This Charter cannot prevent individual holders from making bad
decisions. A citizen who concentrates their entire financial
position in $HOUSEBERNARD has made a choice that no governance
document can protect them from. Education is offered. Wisdom is
not guaranteed.

This Charter cannot prevent all manipulation on external exchanges.
Once tokens trade on decentralized or centralized exchanges, market
participants outside House Bernard's jurisdiction may engage in
wash trading, spoofing, or coordinated manipulation. The
Transparency Layer makes this visible. Section 9 may monitor and
respond to confirmed manipulation under the threat classification
framework. But the House cannot control what happens on platforms
it does not operate.

What this Charter *can* do is ensure that House Bernard itself is
never the source of the problem. The institution does not pump. The
institution does not dump. The institution does not mislead. The
institution does not hide. If a holder is hurt, it is by the
market — not by the House.

-----

## Part V — Red Team Findings and Patches

### Finding 1: The Hype Cycle Trap

**Attack:** Dev community excitement drives token price up on
social media hype. Retail buyers enter at the peak. Hype fades.
Price corrects. Believers who bought at the top are underwater.

**Patch:** The circuit breaker (Section 6) dampens spikes
disconnected from utility growth. The Transparency Layer (Section 7)
publishes utility metrics alongside price, making the divergence
visible to anyone paying attention. Education (Section 9) warns
participants before they buy. The buyback floor (Section 5)
provides a soft landing. None of these prevent the hype cycle
entirely. They narrow the damage band.

### Finding 2: The Insider Dump

**Attack:** Early contributors or Genesis allocation holders sell
large positions after price appreciation, crashing the price for
later entrants.

**Patch:** Founder sale rate limits (Section 3). Large holder rate
limits for Treasury-controlled wallets. Whale alerts (Section 8)
that make large sells publicly visible the moment they happen.
Vesting schedules on all constitutional allocations. The Genesis
Contributors allocation is subject to the same velocity friction
as every other allocation.

### Finding 3: The Copycat Token

**Attack:** A scammer launches a token with a similar name on
another chain, confusing retail buyers who purchase the fake token
thinking it is $HOUSEBERNARD.

**Patch:** Canonical addresses published in TREASURY.md Section X.
Trademark protection filed per SOVEREIGN_ECONOMICS.md. Section 9's
counter-token operations (Class III weapon) provide rapid public
response capability. The Transparency Layer displays the verified
contract address prominently. Any token not listed at the canonical
address is declared fraudulent by constitutional authority.

### Finding 4: The Governance Attack via Accumulation

**Attack:** A hostile actor quietly accumulates enough $HOUSEBERNARD
to gain outsized governance influence, then uses that influence to
redirect Treasury funds or alter emission rules in their favor.

**Patch:** The whale alert system (Section 8) makes accumulation
visible before it reaches governance-threatening levels. Council
membership requires a citizenship stake and citizenship itself
requires passing the Airlock — token accumulation alone does not
grant governance access. The Crown retains veto authority over
constitutional changes during the Founding Period. Bonding
governance rights (Builder and Founder Bonds) require time-locked
commitment, not just capital.

### Finding 5: The Buyback Drain

**Attack:** An adversary deliberately crashes the token price to
trigger Treasury buybacks, draining the stablecoin reserve and
leaving House Bernard unable to fund operations.

**Patch:** The five-percent-per-epoch cap on buyback spending
(Section 5) prevents the reserve from being drained in a single
attack. The twelve-month operational reserve (Section 2) is
maintained separately from buyback funds. The buyback is
discretionary, requiring Crown authorization for crash scenarios —
the CPA Agent does not blindly execute into a coordinated attack.
If an attack is detected, Section 9 handles the threat. The
buyback pauses.

### Finding 6: The Regulatory Seizure

**Attack:** A regulator classifies $HOUSEBERNARD as an unregistered
security. Trading is halted. Holders cannot exit their positions.

**Patch:** SOVEREIGN_ECONOMICS.md Section IV documents the Howey
Test mitigation strategy: the token is primarily earned, has genuine
utility, was not sold through an ICO or presale, and governance is
progressively decentralized. Legal review is constitutionally
required before Phase 2 deployment. The exit rights guarantee in
the Covenant means that even if external trading is halted, citizens
retain the right to use their tokens within the House economy. The
House's internal economy does not depend on exchange access.

-----

## Part VI — Covenant Compliance

**Truth over Harmony:** This Charter mandates radical transparency.
Every metric is published. Every large transaction is alerted. No
information is hidden to preserve a favorable narrative. If the
token is overvalued, the circuit breaker says so structurally. If
the token is undervalued, the buyback floor says so structurally.
The truth is encoded in mechanisms, not in press releases.

**The Forgetting Law:** Transaction records on-chain are immutable
and exempt under the Covenant. Off-chain records in the Transparency
Layer are subject to standard data retention policies. Departing
citizens' wallet associations are removed from the pseudonymous
directory upon exit.

**Exit Rights Are Absolute:** Nothing in this Charter restricts any
holder's right to sell their tokens at any time. Velocity friction
applies to Treasury-controlled wallets, not to individual citizens.
Bonding is voluntary. Holding duration benefits are incentives, not
mandates. A citizen who wants to sell everything and leave may do
so, instantly and without penalty beyond the natural market impact
of their sale.

**The Bernard Trust Is Protected:** Trust tokens are
non-transferable except for distributions to beneficiaries. The
Token Protection Charter does not modify Trust terms. Buyback and
circuit breaker mechanisms do not draw from Trust assets.

**No Being Is Property:** The token represents utility access and
governance participation. It does not represent ownership of any
being, any agent, or any person's labor. Contributors earn tokens.
They are not bonded to them.

-----

*This Charter, upon ratification, has the force of constitutional
amendment under Article X.*

*Drafted by order of the Crown.*
*House Bernard — Ad Astra Per Aspera*
