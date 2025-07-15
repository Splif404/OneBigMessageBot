1. reload service environment and restart
sudo systemctl daemon-reload
sudo systemctl restart obmbot

2. watch logs
journalctl -u obmbot -f





sudo nano /etc/systemd/system/obmbot.service

[Unit]
Description=Blighted Scroll Telegram Bot
After=network-online.target

[Service]
Type=simple
User=bodyisnumb
WorkingDirectory=/home/bodyisnumb/obmbot
EnvironmentFile=/home/bodyisnumb/obmbot/.env
ExecStart=/home/bodyisnumb/obmbot/venv/bin/python bot.py
Restart=on-failure            
RestartSec=5s                 

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
