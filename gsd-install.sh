#!/bin/bash

# ─────────────────────────────────────────────
#  GSD for Antigravity — Global Installer
#  Usage: bash gsd-install.sh [target-project-path]
#  If no path is given, installs into current directory
# ─────────────────────────────────────────────

GSD_GLOBAL_DIR="$HOME/Documents/gsd-global/gsd-template"
GSD_REPO="https://github.com/toonight/get-shit-done-for-antigravity.git"

# ── Step 1: Download GSD globally (only once) ──
if [ ! -d "$GSD_GLOBAL_DIR" ]; then
  echo "📦 GSD not found globally. Downloading..."
  mkdir -p "$HOME/Documents/gsd-global"
  git clone "$GSD_REPO" "$GSD_GLOBAL_DIR"
  echo "✅ GSD downloaded to $GSD_GLOBAL_DIR"
else
  echo "✅ GSD already downloaded globally. Skipping clone."
fi

# ── Step 2: Determine target project folder ──
if [ -n "$1" ]; then
  TARGET="$1"
else
  TARGET="$(pwd)"
fi

echo ""
echo "📁 Installing GSD into: $TARGET"
mkdir -p "$TARGET"

# ── Step 3: Copy GSD files into the project ──
cp -r "$GSD_GLOBAL_DIR/.agent"               "$TARGET/"
cp -r "$GSD_GLOBAL_DIR/.gemini"              "$TARGET/"
cp -r "$GSD_GLOBAL_DIR/.gsd"                 "$TARGET/"
cp -r "$GSD_GLOBAL_DIR/adapters"             "$TARGET/"
cp -r "$GSD_GLOBAL_DIR/docs"                 "$TARGET/"
cp -r "$GSD_GLOBAL_DIR/scripts"              "$TARGET/"
cp    "$GSD_GLOBAL_DIR/PROJECT_RULES.md"     "$TARGET/"
cp    "$GSD_GLOBAL_DIR/GSD-STYLE.md"         "$TARGET/"
cp    "$GSD_GLOBAL_DIR/model_capabilities.yaml" "$TARGET/"

echo ""
echo "🎉 GSD installed successfully into: $TARGET"
echo "👉 Open Antigravity in that folder and run /new-project to get started."
