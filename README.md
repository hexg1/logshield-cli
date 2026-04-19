# LogShield CLI

**Sanitize logs, code, and text before sending them to LLMs.**

LogShield automatically detects and redacts sensitive data — API keys, emails, phone numbers, credit cards, passwords, and more — so you can safely use AI tools without leaking secrets.

---

## What it detects

- API keys (AWS, OpenAI, GitHub, Stripe, Slack, and more)
- Emails, phone numbers, credit card numbers (Luhn-validated)
- Passwords and secrets in environment variables
- JWT tokens, Bearer tokens, private keys
- Named entities: people and organizations (English + Italian)
- Public IP addresses

Private IPs (192.168.x.x, 10.x.x.x) and known test/demo emails are ignored.

---

## Installation

```bash
pip install logshield
```

Requires Python 3.10+.

---

## Setup

Get your API key from [RapidAPI](https://rapidapi.com/hexg1/api/logshield) and run:

```bash
logshield
```

On first launch, use `/setkey` to save your API key.

---

## Usage

### Interactive TUI

```bash
logshield
```

Paste any text, press Enter — get back the sanitized version with a list of what was detected.

### Pipe mode

```bash
cat app.log | logshield pipe
```

Reads from stdin, writes sanitized output to stdout. Exits non-zero if quota is exceeded.

### Check quota

```bash
logshield quota
```

---

## Example

![LogShield in action](example.jpg)

**Input:**
```
User mario.rossi@company.it connected from 8.8.8.8
AWS key: AKIAIOSFODNN7EXAMPLE
password=hunter2
```

**Output:**
```
User [REDACTED:email] connected from [REDACTED:ip]
AWS key: [REDACTED:aws_key]
[REDACTED:env_secret]
```

---

## Privacy

Your text is sent to the LogShield API over HTTPS and processed in memory. **No input text is stored or logged.** Only anonymous usage counters (call count, character count) are recorded for quota tracking.

> **Disclaimer:** LogShield is a privacy-assistance tool. While it uses advanced algorithms (Luhn validation, NER, regex patterns), it does not guarantee 100% detection of all sensitive data. The user remains solely responsible for any data sent to third parties. No liability is accepted for undetected sensitive information.

---

## Pricing

Available on [RapidAPI](https://rapidapi.com/hexg1/api/logshield) — free tier included.

---

## License

MIT
