#!/bin/bash

set -e

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

if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    if [ -z "$REPO_URL" ]; then
        echo "REPO_URL not set. Please set it or manually copy files."
        echo "Example: REPO_URL=https://github.com/yourusername/Latin-Vocab-Trainer.git ./setup.sh"
        exit 1
    fi
    git clone "$REPO_URL" .
else
    echo "Repository already exists, pulling latest..."
    git pull
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
cp deploy/latin-vocab.service /etc/systemd/system/
sed -i "s|/var/www/latin-vocab-trainer|$INSTALL_DIR|g" /etc/systemd/system/latin-vocab.service
sed -i "s|5000|$PORT|g" /etc/systemd/system/latin-vocab.service

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "Setting up nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/latin-vocab
sed -i "s|latin-vocab.trainer|$DOMAIN|g" /etc/nginx/sites-available/latin-vocab
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