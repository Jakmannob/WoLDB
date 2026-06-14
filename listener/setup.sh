#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== WoLDB Listener Setup ==="

# Check for uv
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "Installing Python dependencies..."
uv sync

# Generate TLS certificates
mkdir -p certs
if [ ! -f certs/cert.pem ]; then
    echo "Generating TLS certificate..."
    openssl req -x509 -newkey rsa:4096 \
        -keyout certs/key.pem -out certs/cert.pem \
        -days 36500 -nodes \
        -subj '/CN=woldb-listener'
    chmod 600 certs/key.pem
    echo "Certificate generated."
    echo "  -> Copy certs/cert.pem to the bot server's bot/certs/ directory."
else
    echo "TLS certificate already exists, skipping."
fi

# Generate .env with shared secret
if [ ! -f .env ]; then
    SECRET=$(uv run python -c "import secrets; print(secrets.token_urlsafe(32))")
    cat > .env <<EOF
LISTENER_HOST=0.0.0.0
LISTENER_PORT=9443
SHARED_SECRET=$SECRET
EOF
    echo "Generated .env with a new shared secret."
    echo "  -> Copy the SHARED_SECRET value to the bot's .env file."
else
    echo ".env already exists, skipping."
fi

# Create top-level machines.json from example
MACHINES_FILE="$SCRIPT_DIR/../machines.json"
if [ ! -f "$MACHINES_FILE" ]; then
    cp "$SCRIPT_DIR/../machines.json.example" "$MACHINES_FILE"
    echo "Created machines.json from example. Edit MAC addresses as needed."
else
    echo "machines.json already exists, skipping."
fi

# Generate systemd service file
UV_PATH="$(which uv)"
SERVICE_FILE="woldb-listener.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=WoLDB Wake-on-LAN Listener
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$UV_PATH run python listener.py
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
echo "  sudo systemctl enable --now woldb-listener"
echo ""
echo "Setup complete!"
