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

## Pricing

| Plan  | Calls/month | Price  |
|-------|-------------|--------|
| FREE  | 250         | $0     |
| HOBBY | 6,000       | $12.99 |
| PRO   | 50,000      | $49.99 |

Available on [RapidAPI](https://rapidapi.com/hexg1/api/logshield).

---

## License

MIT
