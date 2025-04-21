#!/bin/bash

# Memory Monitor Python o'rnatish skripti
# Muallif: Manus AI
# Versiya: 1.2.0

echo "====================================================="
echo "MEMORY MONITOR PYTHON - O'rnatish skripti"
echo "Versiya: 1.2.0"
echo "====================================================="
echo ""

# Root tekshirish
if [ "$(id -u)" != "0" ]; then
   echo "Bu skriptni ishga tushirish uchun root huquqiga ega bo'lishingiz kerak." 1>&2
   echo "Maslahat: 'sudo ./install.sh' buyrug'i bilan ishlatib ko'ring" 1>&2
   exit 1
fi

# Python borligini tekshirish
if ! command -v python3 &> /dev/null; then
    echo "Python3 topilmadi. O'rnatilmoqda..."
    apt-get update
    apt-get install -y python3 python3-pip
fi

# Kerakli paketlarni o'rnatish
echo "Kerakli paketlarni o'rnatish..."
apt-get update
apt-get install -y curl

# Python paketlarini o'rnatish
echo "Python paketlarini o'rnatish..."
pip3 install psutil requests

# Qo'shimcha paketlarni so'rash
read -p "SQLite integratsiyasi o'rnatilsinmi? (y/n) [n]: " install_sqlite
if [ "$install_sqlite" = "y" ]; then
    echo "SQLite standart Python bilan birga keladi, qo'shimcha o'rnatish talab qilinmaydi."
fi

read -p "MySQL integratsiyasi o'rnatilsinmi? (y/n) [n]: " install_mysql
if [ "$install_mysql" = "y" ]; then
    pip3 install mysql-connector-python
fi

read -p "PostgreSQL integratsiyasi o'rnatilsinmi? (y/n) [n]: " install_postgresql
if [ "$install_postgresql" = "y" ]; then
    pip3 install psycopg2-binary
fi

read -p "Prometheus integratsiyasi o'rnatilsinmi? (y/n) [n]: " install_prometheus
if [ "$install_prometheus" = "y" ]; then
    pip3 install prometheus-client
fi

# Kataloglarni yaratish
echo "Kataloglarni yaratish..."
mkdir -p /opt/memory-monitor/config
mkdir -p /opt/memory-monitor/core
mkdir -p /opt/memory-monitor/utils
mkdir -p /etc/memory-monitor
mkdir -p /var/lib/memory-monitor
mkdir -p /var/log

# Fayllarni nusxalash
echo "Fayllarni nusxalash..."
cp main.py /opt/memory-monitor/
cp config/config_loader.py /opt/memory-monitor/config/
cp core/monitor.py /opt/memory-monitor/core/
cp core/alerts.py /opt/memory-monitor/core/
cp core/formatter.py /opt/memory-monitor/core/
cp utils/logger.py /opt/memory-monitor/utils/
cp utils/database.py /opt/memory-monitor/utils/

# Konfiguratsiya faylini yaratish
if [ ! -f "/etc/memory-monitor/config.conf" ]; then
    echo "Konfiguratsiya faylini yaratish..."
    cp config.conf /etc/memory-monitor/
else
    echo "Konfiguratsiya fayli mavjud, yangilanmaydi."
    echo "Yangi konfiguratsiya fayli config.conf.new sifatida saqlandi."
    cp config.conf /etc/memory-monitor/config.conf.new
fi

# Systemd service faylini yaratish
echo "Systemd service faylini yaratish..."
cat > /etc/systemd/system/memory-monitor.service << EOF
[Unit]
Description=System Memory, CPU and Disk Monitoring Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/memory-monitor/main.py --config /etc/memory-monitor/config.conf
Restart=always
RestartSec=10
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Huquqlarni o'rnatish
echo "Huquqlarni o'rnatish..."
chmod +x /opt/memory-monitor/main.py
chmod 644 /opt/memory-monitor/config/config_loader.py
chmod 644 /opt/memory-monitor/core/monitor.py
chmod 644 /opt/memory-monitor/core/alerts.py
chmod 644 /opt/memory-monitor/core/formatter.py
chmod 644 /opt/memory-monitor/utils/logger.py
chmod 644 /opt/memory-monitor/utils/database.py
chmod 644 /etc/memory-monitor/config.conf
chmod 644 /etc/systemd/system/memory-monitor.service

# Systemd ni yangilash
echo "Systemd ni yangilash..."
systemctl daemon-reload

# Telegram sinov skriptini yaratish
echo "Telegram sinov skriptini yaratish..."
cat > /opt/memory-monitor/test_telegram.py << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from config.config_loader import ConfigLoader
from utils.logger import Logger

def test_telegram():
    logger = Logger('/var/log/memory_monitor.log', 'INFO').get_logger()
    config_loader = ConfigLoader('/etc/memory-monitor/config.conf', logger)
    config = config_loader.get_config()
    
    message = "🔄 MEMORY MONITOR TEST MESSAGE\n\n"
    message += "🖥️ Test xabari muvaffaqiyatli yuborildi!"
    
    try:
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        payload = {
            'chat_id': config['chat_id'],
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200 and response.json().get('ok'):
            logger.info('Telegram sinov xabari muvaffaqiyatli yuborildi')
        else:
            error_description = response.json().get('description', 'Unknown error')
            logger.error(f"Telegram sinov xabarini yuborishda xatolik: {error_description}")
            
    except Exception as e:
        logger.error(f"Telegram sinov xabarini yuborishda xatolik: {e}")

if __name__ == "__main__":
    test_telegram()
EOF

chmod +x /opt/memory-monitor/test_telegram.py

echo ""
echo "O'rnatish muvaffaqiyatli yakunlandi!"
echo ""
echo "Telegram xabar yuborishni tekshirish uchun:"
echo "  sudo /opt/memory-monitor/test_telegram.py"
echo ""
echo "Xizmatni yoqish uchun:"
echo "  sudo systemctl enable memory-monitor.service"
echo ""
echo "Xizmatni ishga tushirish uchun:"
echo "  sudo systemctl start memory-monitor.service"
echo ""
echo "Xizmat holatini tekshirish uchun:"
echo "  sudo systemctl status memory-monitor.service"
echo ""
echo "Konfiguratsiya fayli:"
echo "  /etc/memory-monitor/config.conf"
echo ""
echo "Log fayli:"
echo "  /var/log/memory_monitor.log"
echo ""
echo "====================================================="