# Latin Vocab Trainer

A Flask web application for learning Latin vocabulary with spaced repetition.

## Quick Deploy to Linux Server

### Prerequisites
- Ubuntu/Debian Linux server
- Git installed
- sudo access

### Option 1: Automated Setup (Recommended)

1. Clone or upload this repository to your server
2. Set environment variables and run:
```bash
cd /path/to/Latin-Vocab-Trainer
chmod +x deploy/setup.sh
sudo DOMAIN=yourdomain.com PORT=5000 REPO_URL=https://github.com/YOUR_USERNAME/Latin-Vocab-Trainer.git ./deploy/setup.sh
```

### Option 2: Manual Setup

1. Install dependencies:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv nginx git
```

2. Create application directory:
```bash
sudo mkdir -p /var/www/latin-vocab-trainer
cd /var/www/latin-vocab-trainer
sudo cp -r /path/to/Latin-Vocab-Trainer/* .
```

3. Set up Python environment:
```bash
sudo python3 -m venv venv
sudo source venv/bin/activate
pip install -r flask_app/requirements.txt
```

4. Create environment file:
```bash
sudo cp deploy/.env.example .env
sudo nano .env  # Edit SECRET_KEY
```

5. Set up systemd service:
```bash
sudo cp deploy/latin-vocab.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable latin-vocab
sudo systemctl start latin-vocab
```

6. Configure nginx:
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/latin-vocab
sudo nano /etc/nginx/sites-available/latin-vocab  # Set your domain
sudo ln -sf /etc/nginx/sites-available/latin-vocab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Publishing to GitHub

```bash
chmod +x deploy/publish.sh
export GITHUB_USERNAME=yourusername
export GITHUB_TOKEN=your_personal_access_token
./deploy/publish.sh
```

Create a token at: https://github.com/settings/tokens (scopes: repo)

## Development

```bash
cd flask_app
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

## Updating Production Safely

If you deploy updates with `rsync --delete`, preserve runtime files that are not in git.

```bash
sudo rsync -av --delete \
  --exclude ".git" \
  --exclude "venv" \
  --exclude "flask_app/app.db" \
  --exclude ".env" \
  ~/production/Latin-Vocab-Trainer/ /var/www/latin-vocab-trainer/
```

Then restart:

```bash
sudo chown -R www-data:www-data /var/www/latin-vocab-trainer
sudo systemctl restart latin-vocab
```

## Adding Lessons

Add JSON files to the root directory and update `index.json`:

```json
[
  {"path": "L21.json", "title": "Lesson 21"}
]
```

Lesson format (L21.json):
```json
[
  {"latein": "Poenus", "deutsch": "der Punier"},
  {"latein": " Hispania", "deutsch": "Spanien"}
]
```