#!/bin/bash

# System Monitor o'rnatish skripti
# Muallif: Husniddin
# Versiya: 1.0.0

echo "====================================================="
echo "SYSTEM MONITOR - O'rnatish skripti"
echo "Versiya: 1.0.0"
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
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Python paketlarini o'rnatishda xatolik yuz berdi."
    exit 1
fi
echo "Python paketlari muvaffaqiyatli o'rnatildi."


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

# O'rnatish katalogini so'rash
read -p "O'rnatish katalogini kiriting [/opt/system-monitor]: " install_dir
install_dir=${install_dir:-/opt/system-monitor}

# Kataloglarni yaratish
echo "Kataloglarni yaratish..."
mkdir -p $install_dir/config
mkdir -p $install_dir/core
mkdir -p $install_dir/utils
mkdir -p /etc/system-monitor
mkdir -p /var/lib/system-monitor
mkdir -p /var/log

# Fayllarni nusxalash
echo "Fayllarni nusxalash..."
cp main.py $install_dir/
cp config/config_loader.py $install_dir/config/
cp core/monitor.py $install_dir/core/
cp core/alerts.py $install_dir/core/
cp core/formatter.py $install_dir/core/
cp utils/logger.py $install_dir/utils/
cp utils/database.py $install_dir/utils/



# Utils katalogini yaratish
cat > $install_dir/utils/__init__.py << EOF
# Utils package
EOF


# Konfiguratsiya faylini yaratish
if [ ! -f "/etc/system-monitor/config.conf" ]; then
    echo "Konfiguratsiya faylini yaratish..."
    cp config.conf /etc/system-monitor/
else
    echo "Konfiguratsiya fayli mavjud, yangilanmaydi."
    echo "Yangi konfiguratsiya fayli config.conf.new sifatida saqlandi."
    cp config.conf /etc/system-monitor/config.conf.new
fi

# Systemd service faylini yaratish
echo "Systemd service faylini yaratish..."
cat > /etc/systemd/system/system-monitor.service << EOF
[Unit]
Description=System Monitoring Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $install_dir/main.py --config /etc/system-monitor/config.conf
Restart=always
RestartSec=10
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Huquqlarni o'rnatish
echo "Huquqlarni o'rnatish..."
chmod +x $install_dir/main.py
chmod 644 $install_dir/config/config_loader.py
chmod 644 $install_dir/core/monitor.py
chmod 644 $install_dir/core/alerts.py
chmod 644 $install_dir/core/formatter.py
chmod 644 $install_dir/utils/logger.py
chmod 644 $install_dir/utils/database.py
chmod 644 /etc/system-monitor/config.conf
chmod 644 /etc/systemd/system/system-monitor.service

# Systemd ni yangilash
echo "Systemd ni yangilash..."
systemctl daemon-reload

# Telegram sinov skriptini yaratish
echo "Telegram sinov skriptini yaratish..."
cat > $install_dir/test_telegram.py << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging

# Modullarni import qilish
sys.path.append('$install_dir')
from config.config_loader import ConfigLoader
from core.monitor import SystemMonitor
from core.alerts import AlertManager
from core.formatter import AlertFormatter

def test_telegram():
    # Boshlang'ich logger
    logger = logging.getLogger('test_telegram')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Konfiguratsiyani yuklash
    config_loader = ConfigLoader('/etc/system-monitor/config.conf', logger)
    config = config_loader.get_config()
    
    # Monitoring obyektlarini yaratish
    monitor = SystemMonitor(config, logger)
    formatter = AlertFormatter(config, logger, monitor)
    alert_manager = AlertManager(config, logger, formatter, monitor)
    
    # Telegram ulanishini tekshirish
    success = alert_manager.test_telegram_connection()
    
    if success:
        logger.info("Telegram sinov xabari muvaffaqiyatli yuborildi!")
    else:
        logger.error("Telegram sinov xabarini yuborishda xatolik yuz berdi.")
        logger.error("Konfiguratsiya faylini tekshiring: /etc/system-monitor/config.conf")

if __name__ == "__main__":
    test_telegram()
EOF

chmod +x $install_dir/test_telegram.py

# Simlink yaratish
echo "Simlink yaratish..."
ln -sf $install_dir/main.py /usr/local/bin/system-monitor
ln -sf $install_dir/test_telegram.py /usr/local/bin/system-monitor-test-telegram

echo ""
echo "O'rnatish muvaffaqiyatli yakunlandi!"
echo ""
echo "Telegram xabar yuborishni tekshirish uchun:"
echo "  sudo system-monitor-test-telegram"
echo ""
echo "Xizmatni yoqish uchun:"
echo "  sudo systemctl enable system-monitor.service"
echo ""
echo "Xizmatni ishga tushirish uchun:"
echo "  sudo systemctl start system-monitor.service"
echo ""
echo "Xizmat holatini tekshirish uchun:"
echo "  sudo systemctl status system-monitor.service"
echo ""
echo "Konfiguratsiya fayli:"
echo "  /etc/system-monitor/config.conf"
echo ""
echo "Log fayli:"
echo "  /var/log/system_monitor.log"
echo ""
echo "====================================================="
