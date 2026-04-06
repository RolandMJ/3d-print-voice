# Pushing 3DPrintVoice to GitHub — Step by Step

You already have SSH keys configured. This guide walks you through creating
a GitHub repository and pushing your code to it.

---

## Step 1: Create a New Repository on GitHub

1. Open your browser: https://github.com/new
2. Fill in:
   - **Repository name:** `3d-print-voice`
   - **Description:** `AI-powered natural language interface for Blender`
   - **Visibility:** Select **Private** (you own the IP — keep it private until
     you decide to share)
   - **Do NOT** check "Add a README" or ".gitignore" — we already have those
3. Click **Create repository**
4. GitHub shows you a page with setup instructions — you need the SSH URL.
   It looks like: `git@github.com:YourUsername/3d-print-voice.git`

**Why private?** This is your intellectual property. A private repo means only
you can see it. You can make it public later if you want. Keeping it private
preserves your options and protects your work.

---

## Step 2: Connect Your Local Repo to GitHub

You already have a git repository with a commit. Now you need to tell git
where the remote (GitHub) copy lives.

Open a terminal and run:

```bash
cd ~/Documents/Claude\ Projects/3d-print-voice
git remote add origin git@github.com:YourUsername/3d-print-voice.git
```

Replace `YourUsername` with your actual GitHub username.

**What this does:** `origin` is the conventional name for "the main remote
copy." This command says: "when I push, send my code to this GitHub repo."

---

## Step 3: Push Your Code

```bash
git push -u origin main
```

**What this does:**
- `push` — sends your local commits to GitHub
- `-u origin main` — sets up tracking so future pushes just need `git push`
- After this, your code is safely backed up on GitHub

You should see output like:
```
Enumerating objects: 22, done.
...
To github.com:YourUsername/3d-print-voice.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

---

## Step 4: Verify

1. Go to `https://github.com/YourUsername/3d-print-voice` in your browser
2. You should see all your files listed
3. Click on a few files to verify the content is there

---

## Your SSH Setup (Already Configured)

Your SSH keys are already set up correctly:

| Key | File | Purpose |
|-----|------|---------|
| Personal | `~/.ssh/id_ed25519` | Used for `github.com` (RolandMJ account) |
| SECONDARY | `~/.ssh/id_ed25519_secondary` | Used for `github-secondary` host |

Your `~/.ssh/config` routes the correct key automatically:
- `git@github.com:...` uses your personal key
- `git@github-secondary:...` uses the SECONDARY key

**You don't need to do anything additional for SSH.** It's already working.

To verify your SSH connection to GitHub:
```bash
ssh -T git@github.com
```
You should see: `Hi YourUsername! You've successfully authenticated...`

---

## Future Workflow

After making changes and committing them:

```bash
# See what changed
git status

# Stage specific files
git add addon/ai_bridge.py agent/main.py

# Commit with a message
git commit -m "description of what you changed"

# Push to GitHub
git push
```

Each push updates the GitHub copy and adds another entry to your development
history — which serves as timestamped proof of your work for IP purposes.
