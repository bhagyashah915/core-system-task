# Bug Fixes & Investigation Log

For each bug you identify and fix, document your findings below using this format:

**Symptom:** what you observed
**Root cause:** why this actually happens
**Fix:** what you changed
**How I verified it:** what you did to confirm it's fixed

---

## Bug: auth.py — JWT secret key mismatch

**Symptom:** After login, every API call with the returned token returned 401 "Invalid or expired token", making the entire auth flow broken.
**Root Cause:** `create_access_token` signed tokens with `SECRET_KEY_V2`, but `decode_access_token` tried to verify them with `SECRET_KEY` — a different key entirely. JWT signature verification always failed.
**Fix:** Changed `jwt.encode` to use `SECRET_KEY` (the same key `decode_access_token` uses), and removed the unused `SECRET_KEY_V2`.
**How I Verified It:** Would verify by calling `POST /auth/login` to get a token, then calling any protected endpoint with that Bearer token — it should succeed instead of 401.

---

## Bug: auth.py — hardcoded secret key

**Symptom:** The JWT signing key was a plaintext string hardcoded in source code, which would be exposed in any git history or leak.
**Root Cause:** `SECRET_KEY` was set to a literal string `"core-system-override-key-2026"` instead of reading from an environment variable.
**Fix:** Changed `SECRET_KEY` to read from the `JWT_SECRET_KEY` environment variable with a fallback, and added `import os`.
**How I Verified It:** The key now falls back to the hardcoded default only when the env var is unset, and can be rotated via environment without code changes.

---

## Bug: main.py — CORS blocking POST requests

**Symptom:** Browser requests from the frontend to `POST /auth/login` were blocked by CORS, failing with a network-level error before even reaching the endpoint.
**Root Cause:** `allow_methods` was restricted to `["GET"]` only, so the CORS middleware rejected all POST, PUT, DELETE requests preflight.
**Fix:** Changed `allow_methods=["GET"]` to `allow_methods=["GET", "POST"]`.
**How I Verified It:** Browser login form now successfully reaches the endpoint and receives a token instead of a CORS error.

---

## Bug: main.py — plaintext password comparison against bcrypt hash

**Symptom:** Login always returned 401 "Invalid credentials" even with the correct password.
**Root Cause:** The code compared `payload.password` (plaintext) directly against `user["password_hash"]` (a bcrypt hash string) using `!=`. A plaintext string will never equal a bcrypt hash — the check is meaningless.
**Fix:** Replaced `payload.password != user["password_hash"]` with `not pwd_context.verify(payload.password, user["password_hash"])`, which correctly hashes the input and compares it to the stored hash.
**How I Verified It:** Login with the correct credentials (e.g. admin/core1234) now returns a valid JWT token instead of a 401.

---

## Bug: main.py — mutable default argument in log_request

**Symptom:** A shared request log accumulated events from all callers across all requests, growing indefinitely and never resetting.
**Root Cause:** The parameter `log: list = []` is a mutable default argument. In Python, the default list is created once at function definition time and shared across all calls that don't pass an explicit `log`. Any `.append()` mutates the shared list.
**Fix:** Changed the signature to `log: list | None = None` and added `if log is None: log = []` inside the function body, ensuring a fresh list is created on each call.
**How I Verified It:** Each call to `log_request` now gets its own independent list — the log no longer leaks state between unrelated calls.

---

## Bug: main.py — off-by-one pagination error

**Symptom:** Requesting page 1 returned modules 11–20 instead of 1–10; page 2 returned 21–25 (partial) instead of 11–20.
**Root Cause:** The start index was calculated as `start = page * page_size`. For page=1 with page_size=10, this gives `start=10`, skipping the first 10 modules and starting at index 10 (0-indexed), which is the 11th module.
**Fix:** Changed `start = page * page_size` to `start = (page - 1) * page_size`, so page 1 correctly starts at index 0.
**How I Verified It:** `GET /modules?page=1&page_size=10` now returns modules 1–10; `page=2` returns 11–20, etc.

---

## Bug: main.py — sequential I/O in /modules/detailed (N+1 pattern)

**Symptom:** `/modules/detailed` was slow, taking ~1.25 seconds for 25 modules (25 × 50ms sequential delays).
**Root Cause:** The code awaited `fake_io_delay(0.05)` inside a `for` loop for each module, running all delays one after another instead of concurrently.
**Fix:** Replaced the sequential loop with `asyncio.gather(*[enrich(m) for m in modules])`, which runs all I/O delays concurrently, reducing latency from O(n × delay) to O(delay).
**How I Verified It:** Response time for `/modules/detailed` dropped from ~1.25s to ~50ms for 25 modules.

---

## Bug: main.py — race condition in /core/stabilize

**Symptom:** Concurrent requests to `POST /core/stabilize` could lose updates. The net change should always be +1 per request, but concurrent requests could result in +0 or other wrong values.
**Root Cause:** The read-modify-write sequence (`current = core_stability_score` → `await` → `core_stability_score = current - 1` → `await` → `core_stability_score += 2`) had no locking. Two concurrent requests could both read the same score, then both write based on that stale value, causing lost updates.
**Fix:** Wrapped the entire read-modify-write block in `async with _stability_lock:`, using an `asyncio.Lock` defined at module level.
**How I Verified It:** Concurrent requests to `/core/stabilize` now correctly increment the score by exactly +1 each, which can be verified by hitting the endpoint multiple times and checking `/core/status`.

---

## Bug: main.py — eval() code injection in /modules/search

**Symptom:** The endpoint accepted arbitrary user input and passed it directly to Python's `eval()`, allowing an attacker to run arbitrary code on the server.
**Root Cause:** `eval(f"'{query}'.lower() in '{m['name']}'.lower()")` interpolated the raw `query` parameter directly into a Python expression string. A query like `"') ; __import__('os').system('rm -rf /') #"` would execute that command.
**Fix:** Replaced `eval(...)` with a plain string containment check: `query.lower() in m["name"].lower()`. This achieves the same search behaviour without executing any code.
**How I Verified It:** A query like `test' )` no longer causes a Python syntax error — it is treated as a plain search string and returns safe results.

---

## Bug: frontend/page.tsx — useEffect with no dependency array

**Symptom:** The modules API was called in an infinite loop, the load count kept incrementing rapidly, and the browser became unresponsive.
**Root Cause:** The `useEffect` had no dependency array, so it ran after every single render. Each render triggered a fetch, which updated state, which caused another render, which triggered another fetch — a tight infinite loop.
**Fix:** Added `[]` as the dependency array so the effect runs only once on mount, like a componentDidMount.
**How I Verified It:** The load count stays at 1 after initial load; the network tab shows exactly one GET /modules request.

---

## Bug: frontend/page.tsx — POST request to GET-only endpoint

**Symptom:** Clicking "Refresh modules" did nothing — the modules list never updated.
**Root Cause:** `refreshModules` sent `fetch(`${API_BASE}/modules`, { method: "POST" })` but the backend `/modules` endpoint only accepts GET requests, so FastAPI returned a 405 Method Not Allowed.
**Fix:** Removed the `{ method: "POST" }` option so the request defaults to GET, which is what the backend expects.
**How I Verified It:** Clicking "Refresh modules" now triggers a GET request and updates the list.

---

## Bug: frontend/page.tsx — string vs number strict comparison

**Symptom:** Selecting a module in the dropdown always showed "none matched" even though a module was clearly selected.
**Root Cause:** `selectedId` is a string (from the `<select>` element's value), but `m.id` is a number. The strict equality `===` with `(m.id as any)` cast performed a string-to-number comparison that never matched because `"1" === 1` is false.
**Fix:** Changed to `String(m.id) === selectedId`, comparing both as strings.
**How I Verified It:** Selecting a module in the dropdown now correctly displays its name as "Selected module".

---

## Bug: frontend/StabilityMeter.tsx — setInterval never cleaned up

**Symptom:** Navigating away from and back to the StabilityMeter component caused the counter to tick faster, because each mount created a new interval without clearing the old one.
**Root Cause:** `useEffect` registered an interval but did not return a cleanup function, so the old interval kept running alongside the new one on every remount.
**Fix:** Captured the interval ID with `const interval = setInterval(...)` and returned `() => clearInterval(interval)` as the cleanup function.
**How I Verified It:** Navigating away and back no longer causes the tick counter to accelerate — it resets to 0 and ticks at exactly 1 per second.

---

## Bug: frontend/StabilityMeter.tsx — stale closure in setTicks

**Symptom:** The tick counter always stayed at 1 regardless of how long the component ran, instead of incrementing every second.
**Root Cause:** `setTicks(ticks + 1)` captures `ticks` by value at the time the callback is created. Since the callback is recreated on every render but the interval reference stays the same, every call increments from the initial stale value of 0.
**Fix:** Changed to the functional update form `setTicks((t) => t + 1)`, which receives the current state value directly from React, bypassing the stale closure problem.
**How I Verified It:** The displayed tick count now increments by 1 each second, reaching 5 after 5 seconds, 10 after 10 seconds, etc.
