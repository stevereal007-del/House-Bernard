# /legal — House Bernard Legal Infrastructure

This directory contains the legal documents governing House
Bernard LLC and the $HOUSEBERNARD token economy.

---

## Contents

| Document | Purpose | Status |
|----------|---------|--------|
| OPERATING_AGREEMENT.md | LLC Operating Agreement | DRAFT — review before execution |
| TOKEN_TERMS_OF_SERVICE.md | $HOUSEBERNARD holder terms | DRAFT — review before publication |
| TRADEMARK_GUIDE.md | USPTO filing guide with pre-drafted descriptions | DRAFT — verify ID Manual before filing |

---

## Claude Cowork Integration

These documents are designed to work with the Claude Cowork
Legal Plugin. Once you have Cowork installed with the legal
plugin:

### Review Workflow

```
/review-contract OPERATING_AGREEMENT.md
```

Claude reviews the operating agreement clause-by-clause against
standard LLC best practices, flags risks, and suggests edits.

```
/review-contract TOKEN_TERMS_OF_SERVICE.md
```

Claude reviews the token terms for completeness, regulatory
compliance gaps, and enforceability issues.

### Research Workflow

```
/brief "Evaluate Howey test exposure for the $HOUSEBERNARD
token based on SOVEREIGN_ECONOMICS.md and
TOKEN_TERMS_OF_SERVICE.md. Identify any gaps in the utility
token defense."
```

```
/brief "Research current SEC guidance on utility tokens with
governance rights. Compare House Bernard's token structure
against recent enforcement actions."
```

```
/brief "Review the TRADEMARK_GUIDE.md filing strategy.
Verify that all goods/services descriptions align with
current USPTO Trademark ID Manual entries."
```

### Compliance Workflow

```
/vendor-check "Verify LLC formation requirements for
[Crown's home state]. Check filing fees, registered
agent requirements, and annual report obligations."
```

---

## Filing Sequence

1. **LLC Formation** — File articles of organization, obtain
   EIN, execute OPERATING_AGREEMENT.md
2. **ENS Domain** — Register housebernard.eth immediately
3. **Trademark Class 42** — File HOUSE BERNARD under Class 42
   (Use in Commerce) using GitHub as specimen
4. **Trademark Class 9** — File HOUSE BERNARD under Class 9
   (Intent to Use) for downloadable software
5. **Token Terms** — Publish TOKEN_TERMS_OF_SERVICE.md in
   repository before any external token distribution
6. **Token Trademarks** — File $HOUSEBERNARD marks before
   token launch announcement

---

## Important Notices

- All documents in this directory are DRAFTS until reviewed
  and executed
- These documents were created with AI assistance
- They do not constitute legal advice
- House Bernard recommends reviewing all documents through
  the Claude Cowork Legal Plugin before execution or filing
- State-specific provisions may need customization
- Tax provisions should be validated by a CPA or through
  AI-assisted tax review

---

*Maintained by: HeliosBlade (Crown)*
*Created: February 2026*
