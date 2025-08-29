# Auto Commit Hook for Claude

This hook automatically commits changes made by Claude during file editing operations.

## Installation

### 1. Install uv

First, install `uv` - a fast Python package installer and resolver:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### 2. Copy the Hook File

Copy `auto_commit.py` to your Claude hooks directory:

```bash
mkdir -p ~/.claude/hooks/
cp auto_commit.py ~/.claude/hooks/
```

### 3. Update Claude Settings

Add the following configuration to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run /path/to/your/home/.claude/hooks/auto_commit.py"
          }
        ]
      }
    ]
  }
}
```

**Important**: Replace `/path/to/your/home` with your actual home directory path (e.g., `/home/username` on Linux, `/Users/username` on macOS). The `~` shorthand cannot be used in the JSON configuration - you must use the full absolute path.

To find your home directory path, run:
```bash
echo $HOME
```

If you already have hooks configured, merge this configuration with your existing settings.

## How It Works

The hook automatically triggers after Claude uses any file editing tools (Write, Edit, or MultiEdit), creating a git commit with a descriptive message about the changes made.

## Requirements

- Python 3.8+
- Git (configured in repositories where you want auto-commits)
- uv package manager

## Troubleshooting

- Ensure the script has execute permissions: `chmod +x ~/.claude/hooks/auto_commit.py`
- Verify that `uv` is installed and in your PATH
- Check that your git repository is properly initialized before using Claude to edit files