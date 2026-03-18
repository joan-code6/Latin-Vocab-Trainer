#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Latin Vocab Trainer Setup ==="
echo ""

INSTALL_DIR="/var/www/latin-vocab-trainer"
SERVICE_NAME="latin-vocab"
DOMAIN="${DOMAIN:-localhost}"
PORT="${PORT:-5000}"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

echo "Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx git

echo ""
echo "Creating application directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

if [ -n "$REPO_URL" ]; then
    echo "Cloning repository..."
    git clone "$REPO_URL" .
elif [ -f "$PROJECT_DIR/flask_app/app.py" ]; then
    echo "Copying local files from $PROJECT_DIR..."
    cp -r "$PROJECT_DIR/"* .
else
    echo "Error: No repository URL provided and no local files found."
    exit 1
fi

echo ""
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r flask_app/requirements.txt

echo ""
echo "Creating environment file..."
if [ ! -f ".env" ]; then
    cp deploy/.env.example .env
    echo "Please edit .env file to set SECRET_KEY and other settings"
fi

echo ""
echo "Setting up systemd service..."
sed -e "s|/var/www/latin-vocab-trainer|$INSTALL_DIR|g" \
    -e "s|127.0.0.1:5000|127.0.0.1:$PORT|g" \
    "$SCRIPT_DIR/latin-vocab.service" > /etc/systemd/system/latin-vocab.service

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "Setting up nginx..."
DOMAIN_HOSTNAME=$(echo "$DOMAIN" | sed 's|https://||' | sed 's|http://||' | cut -d':' -f1 | cut -d'/' -f1)
sed "s|latin-vocab.trainer|$DOMAIN_HOSTNAME|g" "$SCRIPT_DIR/nginx.conf" > /etc/nginx/sites-available/latin-vocab
sed -i "s|127.0.0.1:5000|127.0.0.1:$PORT|g" /etc/nginx/sites-available/latin-vocab

ln -sf /etc/nginx/sites-available/latin-vocab /etc/nginx/sites-enabled/
nginx -t

echo ""
echo "Starting services..."
systemctl start "$SERVICE_NAME"
systemctl restart nginx

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Service status: systemctl status $SERVICE_NAME"
echo "Nginx status: systemctl status nginx"
echo ""
echo "To view logs: journalctl -u $SERVICE_NAME -f"
echo ""
echo "IMPORTANT: Edit .env file to set a secure SECRET_KEY!"