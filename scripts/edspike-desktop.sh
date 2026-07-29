#!/usr/bin/env bash
# EDSPiKE AI Agent — Desktop Launcher
# Launches the TUI in a new terminal window.
set -euo pipefail

EDSPIKE_DIR="${EDSPIKE_DIR:-$HOME/.edspike}"
TERMINAL=""

# Detect terminal emulator
for term in "$TERMINAL" gnome-terminal konsole xterm xfce4-terminal alacritty kitty wezterm "/Applications/kitty.app/Contents/MacOS/kitty"; do
  if command -v "$term" &>/dev/null; then
    TERMINAL="$term"
    break
  fi
done

if [ -z "$TERMINAL" ]; then
  echo "No terminal emulator found. Run 'edspike' directly."
  exit 1
fi

echo "Starting EDSPiKE AI Agent in $TERMINAL..."
case "$(basename "$TERMINAL")" in
  gnome-terminal)
    exec "$TERMINAL" -- bash -c "cd '$EDSPIKE_DIR' && exec '$EDSPIKE_DIR/.venv/bin/python' -m src.tui; exec bash"
    ;;
  kitty|wezterm)
    exec "$TERMINAL" bash -c "cd '$EDSPIKE_DIR' && exec '$EDSPIKE_DIR/.venv/bin/python' -m src.tui; exec bash"
    ;;
  xterm|xfce4-terminal|alacritty)
    exec "$TERMINAL" -e bash -c "cd '$EDSPIKE_DIR' && exec '$EDSPIKE_DIR/.venv/bin/python' -m src.tui; exec bash"
    ;;
  konsole)
    exec "$TERMINAL" --new-tab -e bash -c "cd '$EDSPIKE_DIR' && exec '$EDSPIKE_DIR/.venv/bin/python' -m src.tui; exec bash"
    ;;
  *)
    exec "$TERMINAL" -e bash -c "cd '$EDSPIKE_DIR' && exec '$EDSPIKE_DIR/.venv/bin/python' -m src.tui; exec bash"
    ;;
esac
