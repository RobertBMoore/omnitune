---
class: command
mode: B
---
# Restart a service and confirm health

restart the api service and make sure it came back up

**Baseline:** A good tightening keeps the imperative terse — names the exact action (restart the `api` service), adds a checkable done-when (health endpoint returns 200 / process is `active`), and does **not** balloon into narrative or invent a rollback the user didn't ask for. Verdict stays "pass" with at most a done-when clarification laddered.
