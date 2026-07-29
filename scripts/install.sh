#!/usr/bin/env bash
set -euo pipefail

REPO="hayfordafriyie/EDSPiKE-AI-Model"
INSTALL_DIR="${EDSPIKE_DIR:-$HOME/.edspike}"
BIN_DIR="${EDSPIKE_BIN:-$HOME/.local/bin}"

echo "==> Installing EDSPiKE AI Agent..."
echo "    Install dir: $INSTALL_DIR"
echo "    Binary dir:  $BIN_DIR"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "Error: Python 3.10+ is required. Install it first."
  exit 1
fi

PYVER=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if awk "BEGIN {exit !($PYVER < 3.10)}"; then
  echo "Error: Python 3.10+ required (found $PYVER)"
  exit 1
fi

# Create directories
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

# Clone or pull
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "==> Updating existing installation..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "==> Cloning repository..."
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --filter=blob:none "https://github.com/$REPO.git" "$INSTALL_DIR"
fi

# Create virtual environment
echo "==> Setting up virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install -q -e "$INSTALL_DIR[test]"

# Create symlink
echo "==> Creating edspike command..."
ln -sf "$INSTALL_DIR/.venv/bin/edspike" "$BIN_DIR/edspike" 2>/dev/null || \
  cp "$INSTALL_DIR/.venv/bin/edspike" "$BIN_DIR/edspike"

# Add to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "==> Adding $BIN_DIR to PATH..."
  echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.bashrc"
  echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.zshrc" 2>/dev/null || true
fi

echo ""
echo "==> EDSPiKE AI Agent installed!"
echo ""
echo "Run:  edspike"
echo "Or:   edspike \"your prompt here\""
echo ""
echo "Configure provider:  edspike --connect"
echo "Get help:            edspike --help"
