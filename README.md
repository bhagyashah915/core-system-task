# 🖥️ CodeVerse — Core System Restoration Protocol

**MISSION BRIEFING**

The Core System has failed. 15 critical faults are scattered across the
backend (`FastAPI`) and frontend (`Next.js`) of the Core Terminal.
Your job, Debugger: find them, fix them, and prove you understood *why*
each one broke the system — not just what line to change.

## Setup

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # then fill in a real value
python run.py          # serves on http://localhost:8000
```
Try `GET /health` first to confirm the server is up.

**Frontend**
```bash
cd frontend
npm install
npm run dev             # serves on http://localhost:3000
```

## Rules of engagement

1. There are **15 bugs total**, difficulty tagged loosely as EASY / MEDIUM / HARD
   in spirit (you won't find tags in the code — that would defeat the point).
2. For **every** bug you fix, add a short note to `FIXES.md` (template below)
   explaining: what was broken, why it broke, and how your fix resolves it.
   Fixes without an explanation get partial credit at best — we're testing
   understanding, not luck.
3. Don't just make the error message disappear. A few bugs can be "fixed"
   in a way that hides the symptom without solving the actual problem
   (e.g. wrapping something in try/except and swallowing the error). That's
   worse than not fixing it — we're checking for this specifically.
4. You may use any tools you'd normally use on the job (docs, Stack
   Overflow, an AI assistant). Copy-pasting an AI's fix without being able
   to explain it in your own words during review will not go well for you.
5. Time box: **48-72 hours** for take-home, **90 minutes** for the live round.

## Submission

Push your fixes to a fork/branch and share the link, along with your
completed `FIXES.md`. Include the output of any manual testing you did
(screenshots, curl output, console logs — whatever shows the bug is
actually gone).

---

### `FIXES.md` template (copy this in and fill it per bug)

```markdown
## Bug: <short name/location>
**Symptom:** what you observed (error message, wrong behavior, etc.)
**Root cause:** why this actually happens
**Fix:** what you changed
**How I verified it:** what you did to confirm it's actually fixed
```

Good luck, Debugger. Reboot the Core.
