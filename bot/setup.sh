#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== WoLDB Bot Setup ==="

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "Installing Python dependencies..."
uv sync

# Ensure certs directory exists
mkdir -p certs
if [ ! -f certs/cert.pem ]; then
    echo ""
    echo "IMPORTANT: Copy the TLS certificate from the listener server:"
    echo "  scp user@listener-host:/path/to/WoLDB/listener/certs/cert.pem certs/"
fi

# Create .env template
if [ ! -f .env ]; then
    cat > .env <<EOF
DISCORD_TOKEN=your_discord_bot_token
LISTENER_HOST=your_listener_ip_or_hostname
LISTENER_PORT=9443
SHARED_SECRET=paste_shared_secret_from_listener_setup
EOF
    echo "Created .env template. Fill in the values."
else
    echo ".env already exists, skipping."
fi

# Create top-level machines.json from example
MACHINES_FILE="$SCRIPT_DIR/../machines.json"
if [ ! -f "$MACHINES_FILE" ]; then
    cp "$SCRIPT_DIR/../machines.json.example" "$MACHINES_FILE"
    echo "Created machines.json from example. Edit as needed."
else
    echo "machines.json already exists, skipping."
fi

# Generate systemd service file
UV_PATH="$(which uv)"
SERVICE_FILE="woldb.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=WoLDB Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$UV_PATH run python woldb.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
echo "Generated $SERVICE_FILE"

echo ""
echo "To install the systemd service:"
echo "  sudo cp $SERVICE_FILE /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now woldb"
echo ""
echo "Setup complete!"
