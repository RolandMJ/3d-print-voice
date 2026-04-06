# Public Repository Scrub — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove all personal/sensitive data from current files AND git history, making the repository safe to set to public on GitHub.

**Architecture:** Two-phase approach: (1) fix all sensitive data in current working tree, commit; (2) use `git filter-repo` to scrub patterns from entire git history. After rewrite, force-push to origin.

**Tech Stack:** git-filter-repo (installed), bash, sed

**Sensitive patterns identified (full audit):**

| Pattern | Risk | Location (current files) | In git history? |
|---------|------|--------------------------|-----------------|
| `your-vps-ip` | VPS IP — attackable | 6 files | Yes |
| `/user@` (VPS user) | SSH username | 6 files | Yes |
| `/home/user/` (VPS path) | Server path | 4 files | Yes |
| `SECONDARY` | Employer/business leak | GITHUB_SETUP.md | Yes |
| `/home/user/` | Local username | 1 plan file | Yes |
| `YOUR_API_KEY_HERE` | API key placeholder | deleted .env.example | History only |
| `YOUR_API_KEY_HERE` | API key placeholder | deleted docs | History only |
| `roland@rmj-project.de` | Git author email | Every commit | Yes |

**Acceptable for public (no action needed):**
- `Roland Preisach` — intentional GPL author attribution
- `RolandMJ` — GitHub username, already public
- `roland@rmj-project.de` — standard for open source git author
- `127.0.0.1` / `localhost` — not sensitive

---

### Task 1: Replace VPS credentials in `agent/design_sync.py`

Replace hardcoded VPS host/path with config-driven placeholders that users set themselves.

**Files:**
- Modify: `agent/design_sync.py`

**Step 1: Replace VPS constants with configurable values**

Replace lines 20-24:
```python
# Remote VPS paths
VPS_HOST = "user@your-vps-ip"
VPS_BASE = "/home/user/3dprintvoice-designs"
```

With:
```python
# Remote VPS paths — configure these for your server
# See docs/DESIGN_SYNC_GUIDE.md for setup instructions
VPS_HOST = "user@your-vps-ip"
VPS_BASE = "/home/user/3dprintvoice-designs"
```

**Step 2: Verify file still parses**

Run: `python3 -c "import ast; ast.parse(open('agent/design_sync.py').read()); print('OK')"`
Expected: `OK`

---

### Task 2: Replace VPS credentials in `scripts/vivobook-push.sh`

**Files:**
- Modify: `scripts/vivobook-push.sh`

**Step 1: Replace VPS variables (lines 10, 27-28)**

Line 10 comment: `ssh-copy-id user@your-vps-ip` → `ssh-copy-id user@your-vps-ip`

Lines 27-28:
```bash
VPS="user@your-vps-ip"
VPS_BASE="/home/user/3dprintvoice-designs"
```

**Step 2: Verify script parses**

Run: `bash -n scripts/vivobook-push.sh`
Expected: no output (success)

---

### Task 3: Replace VPS credentials in `scripts/vivobook-setup.sh`

**Files:**
- Modify: `scripts/vivobook-setup.sh`

**Step 1: Replace all 4 occurrences of `user@your-vps-ip` and `/home/user/`**

Lines 73, 76, 79, 83 — replace `user@your-vps-ip` with `user@your-vps-ip`
Line 79 — replace `/home/user/3dprintvoice-designs` with `/home/user/3dprintvoice-designs`

**Step 2: Verify script parses**

Run: `bash -n scripts/vivobook-setup.sh`
Expected: no output (success)

---

### Task 4: Replace VPS data in `docs/DESIGN_SYNC_GUIDE.md`

**Files:**
- Modify: `docs/DESIGN_SYNC_GUIDE.md`

**Step 1: Replace all instances**

- Line 12: `VPS (your-vps-ip)` → `VPS (your-server)`
- Line 30: `ssh user@your-vps-ip "mkdir -p /home/user/...` → `ssh user@your-vps-ip "mkdir -p /home/user/...`
- Line 52: `ssh-copy-id user@your-vps-ip` → `ssh-copy-id user@your-vps-ip`

---

### Task 5: Remove SECONDARY reference from `docs/GITHUB_SETUP.md`

**Files:**
- Modify: `docs/GITHUB_SETUP.md`

**Step 1: Remove the SSH key table and config section (lines 78-89)**

Replace the "Your SSH Setup" section with a generic version:
```markdown
## SSH Setup

Your SSH keys should already be configured. To verify:

```bash
ssh -T git@github.com
```

You should see: `Hi YourUsername! You've successfully authenticated...`
```

This removes the SECONDARY key reference and the specific key file paths.

---

### Task 6: Replace `/home/user/` in plan doc

**Files:**
- Modify: `docs/plans/2026-04-06-packaging-rename-setup.md`

**Step 1: Replace line 875**

`cd /home/user/Documents/Claude\ Projects/blender-ai` → `cd /path/to/blender-ai`

---

### Task 7: Final grep — verify zero sensitive patterns remain in working tree

**Step 1: Run comprehensive grep**

```bash
grep -rn 'SCRUBBED_PATTERN\|user@\|/home/user\|/home/user\|secondary\|sk-ant-' --include='*.py' --include='*.sh' --include='*.md' --include='*.html' .
```

Expected: zero matches

**Step 2: If any matches found, fix them before proceeding**

---

### Task 8: Commit the scrubbed files

**Step 1: Stage and commit**

```bash
git add -A
git commit -m "security: scrub personal data for public release

Remove VPS IP, SSH username, server paths, employer references,
and local username from all files. Replace with generic placeholders."
```

---

### Task 9: Rewrite git history with `git filter-repo`

This is the critical step. `git-filter-repo` will rewrite every commit to replace sensitive strings throughout the entire history.

**Step 1: Create a backup branch**

```bash
git branch backup-before-scrub
```

**Step 2: Create replacements file**

Create `/tmp/replacements.txt` with literal string replacements (one per line, `ORIGINAL==>REPLACEMENT`):

```
user@your-vps-ip==>user@your-vps-ip
your-vps-ip==>your-vps-ip
/home/user/3dprintvoice-designs==> /home/user/3dprintvoice-designs
/home/user/==> /home/user/
user@your-vps-ip==>user@your-vps-ip
/path/to/blender-ai==>/path/to/blender-ai
/home/user/==>/home/user/
SECONDARY==>SECONDARY
id_ed25519_secondary==>id_ed25519_secondary
github-secondary==>github-secondary
YOUR_API_KEY_HERE==>YOUR_API_KEY_HERE
YOUR_API_KEY_HERE==>YOUR_API_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-...==>ANTHROPIC_API_KEY=YOUR_KEY_HERE
```

**Step 3: Run git filter-repo with blob replacements**

```bash
git filter-repo --replace-text /tmp/replacements.txt --force
```

**Step 4: Verify history is clean**

```bash
git log --all -p | grep -cP 'SCRUBBED_PATTERN|/user@|/home/user|/home/user|secondary|YOUR_API_KEY_HERE'
```

Expected: `0`

**Step 5: Verify current files still work**

```bash
python3 -c "import ast; ast.parse(open('agent/design_sync.py').read()); print('OK')"
bash -n scripts/vivobook-push.sh
bash -n scripts/vivobook-setup.sh
```

Expected: all OK

---

### Task 10: Re-add remote and force-push

`git filter-repo` removes the remote. Re-add it and force-push.

**Step 1: Re-add origin**

```bash
git remote add origin git@github.com:RolandMJ/blender-ai.git
```

**Step 2: Confirm with user before force-push**

⚠️ This rewrites all commit hashes. Anyone who cloned the private repo will need to re-clone.

```bash
git push --force origin main
```

**Step 3: Delete backup branch**

```bash
git branch -D backup-before-scrub
```

---

### Task 11: Post-scrub verification

**Step 1: Fresh clone test**

```bash
cd /tmp && git clone git@github.com:RolandMJ/blender-ai.git test-public-audit && cd test-public-audit
```

**Step 2: Full history audit on fresh clone**

```bash
git log --all -p | grep -ciP 'SCRUBBED_PATTERN|user@your-vps|/home/user|/home/user|secondary|YOUR_API_KEY_HERE|sk-ant-your'
```

Expected: `0`

**Step 3: Check no stale refs**

```bash
git reflog expire --expire=now --all
git gc --prune=now
```

**Step 4: Cleanup**

```bash
rm -rf /tmp/test-public-audit /tmp/replacements.txt
```

---

### Task 12: Set repository to public

**Step 1: Change visibility via GitHub CLI**

```bash
gh repo edit RolandMJ/blender-ai --visibility public
```

Or manually: GitHub → Settings → Danger Zone → Change visibility → Public

---

## Summary of what gets scrubbed

| What | Replaced with |
|------|---------------|
| `your-vps-ip` | `your-vps-ip` |
| `/user@` (VPS context) | `user@` |
| `/home/user/` | `/home/user/` |
| `/home/user/` | `/home/user/` or `/path/to/` |
| `SECONDARY` / `secondary` | `SECONDARY` / `secondary` |
| `YOUR_API_KEY_HERE` | `YOUR_API_KEY_HERE` |
| `YOUR_API_KEY_HERE` | `YOUR_API_KEY_HERE` |

## What stays (intentional, appropriate for open source)

- `Roland Preisach` — GPL author attribution
- `roland@rmj-project.de` — git author email (standard)
- `RolandMJ` — GitHub username (already public)
- `localhost` / `127.0.0.1` — not sensitive
