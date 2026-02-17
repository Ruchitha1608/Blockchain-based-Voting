# Git & GitHub Complete Command Reference

## 📚 Table of Contents
1. [Understanding Git vs GitHub](#understanding-git-vs-github)
2. [Essential Setup](#essential-setup)
3. [Daily Workflow Commands](#daily-workflow-commands)
4. [Branching & Merging](#branching--merging)
5. [Remote Repository Operations](#remote-repository-operations)
6. [Undoing Changes](#undoing-changes)
7. [Viewing History & Status](#viewing-history--status)
8. [GitHub-Specific Operations](#github-specific-operations)
9. [Common Scenarios](#common-scenarios)
10. [Troubleshooting](#troubleshooting)

---

## Understanding Git vs GitHub

**Git** = Version control system (runs on your computer)
**GitHub** = Cloud hosting service for Git repositories

```
Your Computer (Git)  ←→  GitHub (Remote)
     Local Repo      ←→  Remote Repo
```

---

## Essential Setup

### 1. Configure Git Identity

**When:** First time using Git on a new machine

```bash
# Set your name (shows in commits)
git config --global user.name "Your Name"

# Set your email (links to GitHub account)
git config --global user.email "your.email@example.com"

# View current config
git config --list

# View specific setting
git config user.name
git config user.email
```

**Why:** Every commit includes author information. This identifies you.

### 2. Set Default Editor

**When:** You want to customize commit message editor

```bash
# Use VS Code
git config --global core.editor "code --wait"

# Use nano (simple)
git config --global core.editor "nano"

# Use vim
git config --global core.editor "vim"
```

### 3. Set Default Branch Name

**When:** Creating new repositories (modern standard is "main")

```bash
git config --global init.defaultBranch main
```

---

## Daily Workflow Commands

### 1. Check Status

**When:** Before any operation, to see what's changed

```bash
git status
```

**Output tells you:**
- Current branch
- Changes staged for commit (green)
- Changes not staged (red)
- Untracked files (red)

### 2. Stage Changes

**When:** You want to prepare files for commit

```bash
# Stage specific file
git add filename.txt

# Stage specific directory
git add src/

# Stage all changes in current directory
git add .

# Stage all changes everywhere
git add -A

# Stage only modified/deleted (not new files)
git add -u

# Interactive staging (choose what to stage)
git add -p
```

**When to use what:**
- `git add filename.txt` → Stage specific file you know you changed
- `git add .` → Stage everything in current folder (most common)
- `git add -A` → Stage everything in entire project
- `git add -p` → Carefully review each change before staging

### 3. Unstage Changes

**When:** You staged something by mistake

```bash
# Unstage specific file (keeps changes)
git restore --staged filename.txt

# Unstage everything (keeps changes)
git restore --staged .

# Old way (still works)
git reset HEAD filename.txt
```

### 4. Commit Changes

**When:** You've staged changes and want to save them

```bash
# Commit with inline message
git commit -m "Add login feature"

# Commit with detailed message (opens editor)
git commit

# Stage all tracked files and commit
git commit -am "Fix bug in checkout"

# Amend last commit (change message or add files)
git commit --amend

# Amend without changing message
git commit --amend --no-edit
```

**Good commit message format:**
```
Short summary (50 chars or less)

Detailed explanation if needed. Explain WHY, not what.
- Bullet points are fine
- Reference issue numbers: Fixes #123

Co-Authored-By: Name <email@example.com>
```

**When to use what:**
- `git commit -m "..."` → Quick commit (most common)
- `git commit` → Need detailed multi-line message
- `git commit -am "..."` → Quick commit of all changes (skip `git add`)
- `git commit --amend` → Fix last commit (ONLY if not pushed!)

### 5. Discard Changes

**When:** You want to throw away local changes

```bash
# Discard changes in specific file
git restore filename.txt

# Discard all changes in current directory
git restore .

# Old way (still works)
git checkout -- filename.txt
```

**⚠️ WARNING:** This permanently deletes your changes!

---

## Branching & Merging

### Understanding Branches

```
main     ──●──●──●──●──●
            \       /
feature      ●──●──●
```

**Why use branches:**
- Work on features without breaking main code
- Multiple people work simultaneously
- Test before merging to main

### Branch Commands

```bash
# List all local branches
git branch

# List all branches (including remote)
git branch -a

# Create new branch
git branch feature-name

# Create and switch to new branch
git checkout -b feature-name

# Switch to existing branch
git checkout branch-name

# Rename current branch
git branch -m new-name

# Delete branch (safe - warns if unmerged)
git branch -d branch-name

# Force delete branch (⚠️ loses unmerged changes)
git branch -D branch-name

# Delete remote branch
git push origin --delete branch-name
```

**When to use what:**
- `git checkout -b feature-name` → Start new feature (most common)
- `git checkout main` → Go back to main branch
- `git branch -d feature-name` → Cleanup after merge

### Merging Branches

```bash
# Merge feature-branch into current branch
git merge feature-branch

# Merge with commit message
git merge feature-branch -m "Merge feature X"

# Abort merge if conflicts
git merge --abort
```

**Typical workflow:**
```bash
# You're on feature branch
git checkout main          # Switch to main
git merge feature-branch   # Merge feature into main
git branch -d feature-branch  # Delete feature branch
```

---

## Remote Repository Operations

### 1. Clone Repository

**When:** First time getting project from GitHub

```bash
# Clone with HTTPS
git clone https://github.com/username/repo.git

# Clone with SSH (recommended)
git clone git@github.com:username/repo.git

# Clone into specific folder
git clone https://github.com/username/repo.git my-folder

# Clone specific branch
git clone -b branch-name https://github.com/username/repo.git
```

### 2. View Remotes

**When:** Check where your repo connects to

```bash
# List remotes
git remote -v

# Add new remote
git remote add origin https://github.com/username/repo.git

# Change remote URL (HTTPS to SSH)
git remote set-url origin git@github.com:username/repo.git

# Remove remote
git remote remove origin

# Rename remote
git remote rename old-name new-name
```

### 3. Fetch vs Pull

**Fetch** = Download changes but don't merge
**Pull** = Download changes AND merge

```bash
# Download changes from remote (don't merge)
git fetch origin

# Download and merge changes
git pull origin main

# Pull current branch
git pull

# Pull with rebase (cleaner history)
git pull --rebase
```

**When to use what:**
- `git fetch` → Check what changed before merging
- `git pull` → Update local branch (most common)
- `git pull --rebase` → Cleaner history for feature branches

### 4. Push Changes

**When:** You want to upload local commits to GitHub

```bash
# Push to remote branch
git push origin branch-name

# Push current branch
git push

# Push and set upstream (first time)
git push -u origin branch-name

# Force push (⚠️ DANGEROUS - overwrites remote)
git push --force

# Safer force push (fails if remote changed)
git push --force-with-lease
```

**When to use what:**
- `git push` → Upload commits (most common)
- `git push -u origin main` → First push of new branch
- `git push --force-with-lease` → After amending commits (safer than --force)
- **NEVER** `git push --force` to shared branches like main!

---

## Undoing Changes

### 1. Undo Last Commit (Keep Changes)

**When:** Committed too early, want to modify

```bash
# Undo commit, keep changes staged
git reset --soft HEAD~1

# Undo commit, keep changes unstaged
git reset HEAD~1

# Undo commit, discard changes (⚠️ DANGEROUS)
git reset --hard HEAD~1
```

### 2. Undo Multiple Commits

```bash
# Undo last 3 commits (keep changes)
git reset HEAD~3

# Undo to specific commit
git reset abc1234
```

### 3. Revert Commit (Safe)

**When:** Undo a commit that's already pushed

```bash
# Create new commit that undoes changes
git revert abc1234

# Revert last commit
git revert HEAD
```

**Difference:**
- `git reset` → Rewrite history (use before pushing)
- `git revert` → Create new commit (safe for pushed commits)

### 4. Change Commit Author

**When:** Wrong name/email in commit

```bash
# Change last commit author
git commit --amend --author="Name <email@example.com>"

# Change and keep message
git commit --amend --author="Name <email@example.com>" --no-edit
```

---

## Viewing History & Status

### 1. View Commits

```bash
# View commit history
git log

# One line per commit
git log --oneline

# Show last 5 commits
git log -5

# Show commits with file changes
git log --stat

# Show commits with full diff
git log -p

# Show graph of branches
git log --graph --oneline --all

# Show commits by author
git log --author="Name"

# Show commits in date range
git log --since="2 weeks ago"
git log --after="2024-01-01" --before="2024-12-31"
```

### 2. View Changes

```bash
# Show unstaged changes
git diff

# Show staged changes
git diff --staged

# Show changes in specific file
git diff filename.txt

# Compare branches
git diff main..feature-branch

# Compare commits
git diff abc1234..def5678
```

### 3. View File History

```bash
# Show commits that modified file
git log filename.txt

# Show who changed each line
git blame filename.txt

# Show file content at specific commit
git show abc1234:path/to/file.txt
```

---

## GitHub-Specific Operations

### 1. Fork & Pull Request Workflow

```bash
# 1. Fork on GitHub (click Fork button)

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/repo.git

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL-OWNER/repo.git

# 4. Create feature branch
git checkout -b my-feature

# 5. Make changes and commit
git add .
git commit -m "Add feature"

# 6. Push to your fork
git push origin my-feature

# 7. Create Pull Request on GitHub

# 8. Keep fork updated
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### 2. Using GitHub CLI (gh)

**Install:** `brew install gh` (Mac) or download from https://cli.github.com

```bash
# Login to GitHub
gh auth login

# Create repository
gh repo create my-project --public

# Clone repository
gh repo clone username/repo

# View pull requests
gh pr list

# Create pull request
gh pr create --title "Add feature" --body "Description"

# View PR
gh pr view 123

# Checkout PR locally
gh pr checkout 123

# Merge PR
gh pr merge 123

# View issues
gh issue list

# Create issue
gh issue create --title "Bug" --body "Description"

# View workflow runs
gh run list

# View repository in browser
gh repo view --web
```

---

## Common Scenarios

### Scenario 1: Starting New Project

```bash
# Create project folder
mkdir my-project
cd my-project

# Initialize Git
git init

# Create first file
echo "# My Project" > README.md

# Make first commit
git add .
git commit -m "Initial commit"

# Create GitHub repo (using gh)
gh repo create my-project --public

# Push to GitHub
git push -u origin main
```

### Scenario 2: Contributing to Existing Project

```bash
# Clone repository
git clone https://github.com/username/repo.git
cd repo

# Create feature branch
git checkout -b fix-bug

# Make changes
# ... edit files ...

# Stage and commit
git add .
git commit -m "Fix bug in login"

# Push branch
git push -u origin fix-bug

# Create PR on GitHub
gh pr create
```

### Scenario 3: Syncing Fork with Upstream

```bash
# Add upstream (one time)
git remote add upstream https://github.com/original/repo.git

# Fetch upstream changes
git fetch upstream

# Switch to main
git checkout main

# Merge upstream changes
git merge upstream/main

# Push to your fork
git push origin main
```

### Scenario 4: Fixing Merge Conflicts

```bash
# Attempt merge
git merge feature-branch

# If conflicts:
# 1. Open conflicted files
# 2. Look for conflict markers:
#    <<<<<<< HEAD
#    Your changes
#    =======
#    Their changes
#    >>>>>>> feature-branch

# 3. Edit file to resolve
# 4. Stage resolved files
git add filename.txt

# 5. Complete merge
git commit
```

### Scenario 5: Accidentally Committed to Wrong Branch

```bash
# You're on main, should be on feature
git log -1  # Note commit hash

# Undo commit on main (keep changes)
git reset HEAD~1

# Create/switch to correct branch
git checkout -b feature-branch

# Commit there
git add .
git commit -m "Feature X"
```

### Scenario 6: Delete Sensitive Data from Commit

```bash
# ⚠️ If you committed passwords/secrets:

# Remove from last commit
git reset HEAD~1
# Edit file to remove secrets
git add .
git commit -m "Add feature (fixed)"

# If already pushed (⚠️ rewrites history):
git push --force-with-lease

# Better: Use git-filter-repo or BFG Repo-Cleaner
# for old commits
```

---

## Troubleshooting

### Problem 1: "Permission denied" when pushing

**Cause:** SSH key not set up or wrong remote URL

**Fix:**
```bash
# Check remote URL
git remote -v

# If using HTTPS but should use SSH:
git remote set-url origin git@github.com:username/repo.git

# Set up SSH key:
ssh-keygen -t ed25519 -C "your.email@example.com"
# Add ~/.ssh/id_ed25519.pub to GitHub → Settings → SSH Keys
```

### Problem 2: "Your branch is behind"

**Cause:** Remote has commits you don't have locally

**Fix:**
```bash
# Pull changes
git pull origin main

# If you have local commits:
git pull --rebase origin main
```

### Problem 3: "Merge conflict"

**Fix:**
```bash
# See conflicted files
git status

# Open each file, resolve conflicts
# (remove <<<, ===, >>> markers)

# Stage resolved files
git add .

# Complete merge
git commit
```

### Problem 4: "Detached HEAD state"

**Cause:** Checked out a commit instead of a branch

**Fix:**
```bash
# Create branch from current position
git checkout -b new-branch-name

# Or go back to main
git checkout main
```

### Problem 5: Accidentally deleted local branch

**Fix:**
```bash
# Find commit hash
git reflog

# Recreate branch
git checkout -b branch-name abc1234
```

### Problem 6: Want to undo push

**Fix:**
```bash
# ⚠️ Only if you're the only user of the branch!

# Reset local
git reset --hard HEAD~1

# Force push
git push --force-with-lease
```

---

## Git Workflow Cheat Sheet

### Daily Work Cycle

```bash
# Morning: Update local
git checkout main
git pull

# Start new feature
git checkout -b feature-name

# Work on feature
# ... edit files ...
git add .
git commit -m "Message"

# Push to GitHub
git push -u origin feature-name

# Create PR on GitHub
# After PR approved and merged:

# Cleanup
git checkout main
git pull
git branch -d feature-name
```

### Emergency Fixes

```bash
# Undo last commit (not pushed)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD

# Undo last commit (already pushed)
git revert HEAD
git push
```

---

## Best Practices

### ✅ DO

1. **Commit often** - Small, focused commits
2. **Write good messages** - Explain WHY, not what
3. **Pull before push** - Avoid conflicts
4. **Use branches** - Keep main stable
5. **Review before commit** - `git diff` and `git status`
6. **Test before commit** - Make sure code works

### ❌ DON'T

1. **Don't commit secrets** - .env files, API keys, passwords
2. **Don't commit large files** - Use .gitignore for binaries
3. **Don't force push to main** - Breaks team's work
4. **Don't rewrite public history** - Causes conflicts
5. **Don't commit without testing** - Breaks builds
6. **Don't use generic messages** - "fix", "update", "changes"

---

## .gitignore Examples

Create `.gitignore` file to ignore files:

```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Node.js
node_modules/
package-lock.json
npm-debug.log

# Environment
.env
.env.local
*.secret

# IDEs
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
*.log
```

---

## Quick Reference Card

```bash
# Setup
git config --global user.name "Name"
git config --global user.email "email"

# Daily workflow
git status                    # Check status
git add .                     # Stage all changes
git commit -m "Message"       # Commit changes
git push                      # Upload to GitHub
git pull                      # Download from GitHub

# Branching
git checkout -b feature       # Create and switch to branch
git checkout main             # Switch to main
git merge feature             # Merge branch
git branch -d feature         # Delete branch

# Undo
git restore file.txt          # Discard changes
git reset --soft HEAD~1       # Undo commit (keep changes)
git commit --amend            # Modify last commit

# View
git log --oneline            # View commits
git diff                     # View changes
git remote -v                # View remotes

# Remote
git clone URL                # Clone repository
git remote add origin URL    # Add remote
git push -u origin main      # Push and set upstream
```

---

## When to Use What - Decision Tree

**Need to upload code to GitHub?**
- New project → `git init`, `git add .`, `git commit`, `gh repo create`, `git push`
- Existing project → `git clone`, edit, `git add`, `git commit`, `git push`

**Made a mistake?**
- Not committed yet → `git restore file.txt`
- Committed but not pushed → `git reset HEAD~1`
- Already pushed → `git revert HEAD`

**Working with others?**
- Start feature → `git checkout -b feature`
- Update code → `git pull`
- Share work → `git push`, create PR
- Sync fork → `git fetch upstream`, `git merge upstream/main`

**Having problems?**
- Conflicts → `git status`, resolve, `git add`, `git commit`
- Behind remote → `git pull`
- Wrong branch → `git checkout correct-branch`

---

**Last Updated:** February 17, 2026
**Version:** 1.0

For official documentation: https://git-scm.com/doc
For GitHub help: https://docs.github.com
