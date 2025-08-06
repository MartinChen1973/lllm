# 🧠 Cursor: From Beginner to Mid-Level Pro

---

## ✅ What Is Cursor?

**Cursor** is a modified version of VS Code, enhanced with powerful AI assistance. Think of it as VS Code with a helpful AI co-pilot that understands your code, explains it, generates snippets, debugs errors, and even refactors.

---

## 🟢 Step 1: Install Cursor

1. Go to [https://www.cursor.sh](https://www.cursor.sh)
2. Download the version for your OS (Windows/Mac/Linux).
3. Install it just like you'd install VS Code.
4. Sign in with GitHub （recommended） or Google.

---

## 🛠️ Step 2: Start a Project

1. Click **“Open Folder”** to start or load your project.
2. Create a new file, like `main.py` or `index.ts`.
3. You'll see a **"Cursor" button** on the side bar — this is your AI assistant panel.

---

## 🤖 Step 3: Talk to the AI

You can chat with the AI in four ways:

### 💬 1. Chat Panel (bottom-left)

- Ask things like:
  - “What does this function do?”
  - “How do I write a binary search in Python?”
  - “Can you help me refactor this code?”

### 🧠 2. Inline Actions

- **Right-click** any code → Choose `Explain`, `Refactor`, or `Find bugs`.
- Or **highlight code**, press `Cmd/Ctrl + K`, then type your prompt.

### ⚡ 3. Cmd + K (Quick Prompt)

- Press `Cmd/Ctrl + K` to bring up a floating prompt anywhere.

### 🧭 4. Right Panel (AI History and Chat Context)

There’s a powerful fourth way to use AI in Cursor — the **right panel**, which serves as a history-aware AI chat with deeper context.

#### 🔍 How to Open the Right Panel

- **Method 1:**

  - Click the "Cursor" icon in the upper right corner of the window, or use the shortcut `Cmd/Ctrl + Shift + P` → `Cursor: Open Chat`
  - This will display a vertically docked chat window on the right side, which stores your recent interactions and complete context awareness.

- **Method 2:**
  - In the left directory, select a file, "Add to chat" (with current/new two options) to add and open it.

#### 💡 What Makes This Different?

- It keeps **session history**, so you can go back and continue a previous question.
- You can **inject file, terminal, or editor context** to improve answer quality.

#### ➕ How to Add Context to the Right Panel Chat

- **Files**: Click the `+` icon → select any file open in the editor to inject its content.
- **Code blocks**: Select code in the editor → right-click → `Send to Chat`.
- **Terminal output**: Copy logs from your terminal → paste directly into the chat box.

#### 🧠 Example Usage

- Ask: _"Why is this script failing with exit code 1?"_, after adding relevant terminal output.
- Ask: _"Can you explain how this function interacts with the database?"_, after adding your ORM model file.

#### ✨ Tip

The more relevant context you attach, the **smarter** and more **accurate** the AI becomes.

This makes the right-side panel your go-to interface for **project-wide, history-rich, context-enhanced conversations**.

---

## 💡 Step 4: Ask Smart Prompts

Try things like:

- "Explain this code to a beginner."
- "Convert this Python code to JavaScript."
- "Add comments to this function."
- "Add type hints to this function."
- "Write unit tests for this class."
- "Find performance bottlenecks in this loop."

---

## 🧰 Step 5: Middle-Class Tips (Level Up!)

### 🧪 1. Use the "Edit With AI" Feature

- Select a block of code
- Right-click → `Edit with AI`
- Describe what you want changed (e.g., “make it async”, “use regex instead of loop”)

### 🧠 2. Use `// @cursor` comments to guide the AI

```python
# @cursor: write a Flask app with two endpoints
```

### 🏗️ 3. Leverage Cursor's Context Awareness

It reads your entire file and neighboring files to give smarter answers. You don’t need to copy/paste everything into the prompt.

### 📦 4. Use the AI Terminal (experimental)

Try:

- `Cmd/Ctrl + Shift + P` → "Cursor: Run AI Terminal"
- Ask it to run shell commands, e.g., "Set up a Python virtual environment"

### 🧱 5. Autocomplete with AI

As you type, Cursor suggests completions like Copilot — but more aware of your codebase.

---

## ⚙️ Step 6: Customize Settings

- File → Preferences → Settings
  - Enable/disable specific AI tools
  - Set model type (e.g., GPT-4 vs. GPT-3.5)
  - Customize shortcuts

---

## 🧑‍🏫 Example Prompts for Practice

| Situation                   | Prompt                                                        |
| --------------------------- | ------------------------------------------------------------- |
| You want to understand code | "Explain what this class does, and how it could be improved." |
| You need to write new code  | "Write a function that checks for balanced parentheses."      |
| You hit a bug               | "Why is this function returning `None` when it shouldn’t?"    |
| You want to optimize        | "Can you make this loop more efficient using NumPy?"          |

---

## 📛 What Not to Use Cursor AI For (Let the Editor Do It!)

While Cursor's AI is powerful, there are tasks that the **editor itself** (VS Code-based) handles more reliably and efficiently. These tasks don't require AI help, and using it can actually slow you down.

### ❌ Tasks Better Done Manually in the Editor:

- ✏️ **Renaming a Method or Variable**Use `F2` or right-click → Rename Symbol.
- 📂 **Renaming a File**Right-click the file in the sidebar → Rename.
- ↔️ **Moving a File to a Different Folder**Drag and drop it directly.
- 📝 **Moving a Method to a New File**Cut + paste; then use the editor's auto-import feature.
- 📚 **Creating or Deleting Files**Faster using sidebar or `Cmd/Ctrl + N`, `Delete`.
- ♻️ **Refactoring Multiple Imports or Reorganizing Code Structure**Use multi-cursor or structural search/replace.
- 📈 **Checking Git Status, Commits, and Branches**Use built-in Git view (left sidebar) or terminal.
- 🔄 **Formatting Code**Use `Shift + Alt + F` or Prettier/Black integration.
- ⚠️ **Fixing Linter Warnings/Errors**
  Use `Quick Fix` (lightbulb icon) rather than AI guesses.

> **Why avoid AI here?** These are **deterministic, structured tasks** where the editor's tools already excel with accuracy and speed.

---

## 📚 Resources for Further Learning

- Cursor’s official docs: [https://docs.cursor.sh](https://docs.cursor.sh)
- Follow their Discord or Twitter for updates
- Use in GitHub projects to try AI-assisted PRs

---

## 🏁 Final Tips

- Treat Cursor AI like a **junior developer**: guide it clearly.
- Use short, precise instructions.
- Don’t blindly accept results — review and test.
- Let the AI **assist** you, not replace your judgment.
