# How to Set Up Auto-Formatting

We added a tool that automatically formats our code locally so we don't have to wait for the GitLab pipeline to fail over minor styling issues.

## One-Time Setup
Open your terminal in the root of our project folder and run these three steps/commands:

#### 1. Get new updates from main (`.pre-commit-config.yaml`)

```bash
git pull (to get the new configuration file)
```

#### 2. Install `pre-commit` package

```bash
pip install pre-commit (to install the tool)
```

#### 3. Install Ruff trough pre-commit package

```bash
pre-commit install (to activate the tool in Git)
```

- **`NOTE:`**  What to Expect on Your First Commit
The very first time you type git commit, you will see a message saying:
    ```
    Initializing environment for https://github.com..."
    ```
    This means that pre-commit is downloading the formatter to your computer. This takes a few seconds and `will only happen once`.

## Your Daily Workflow
Just commit your code normally. When you type git commit, the tool will intercept it:

- **If your code is clean:** The commit succeeds instantly.

- **If your code has styling issues:** The commit will fail, but the tool will instantly fix the files for you!

    - **The Fix:** If it auto-fixes your files, simply type git add . and then git commit again with your message. It will pass the second time. If it does not aut-fix, you need to do it manually. Just read the output.

## Manual Checking & Correcting with Ruff Commands
If you want to run the formatter yourself without doing a git commit, you can use these commands described below. Both commands will check for errors and automatically fix the code for you:

- **"pre-commit run <file or folder>":** Scans and corrects only the specific files you are currently working on (the ones you just ran git add on).

```bash
pre-commit run <file or folder>
```
- **"pre-commit run --all-files":** Scans and corrects every single file in the entire repository. This is great if you want to do a full project cleanup.

```bash
pre-commit run --all-files
```