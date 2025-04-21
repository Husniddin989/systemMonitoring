#!/bin/bash

# System Monitor o'rnatish skripti
# Muallif: Manus AI
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

# Utils katalogini yaratish
cat > $install_dir/utils/__init__.py << EOF
# Utils package
EOF

# Logger modulini yaratish
cat > $install_dir/utils/logger.py << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logging modulini sozlash
"""

import logging

class Logger:
    def __init__(self, log_file, log_level):
        """
        Logger yaratish
        
        Args:
            log_file (str): Log fayli yo'li
            log_level (str): Log darajasi
        """
        self.log_file = log_file
        self.log_level = log_level
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """
        Logger sozlash
        
        Returns:
            logging.Logger: Logger obyekti
        """
        # Log darajasini aniqlash
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        level = level_map.get(self.log_level.upper(), logging.INFO)
        
        # Logger yaratish
        logger = logging.getLogger('system_monitor')
        logger.setLevel(level)
        
        # Formatni o'rnatish
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        
        # Fayl handleri
        try:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Log faylini yaratishda xatolik: {e}")
            print(f"Standart log fayli ishlatiladi: /tmp/system_monitor.log")
            file_handler = logging.FileHandler('/tmp/system_monitor.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def get_logger(self):
        """
        Logger obyektini qaytarish
        
        Returns:
            logging.Logger: Logger obyekti
        """
        return self.logger
EOF

# Database modulini yaratish
cat > $install_dir/utils/database.py << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ma'lumotlar bazasi bilan ishlash moduli
"""

import os
import time
import json
import sqlite3

class Database:
    def __init__(self, config, logger):
        """
        Ma'lumotlar bazasi obyektini yaratish
        
        Args:
            config (dict): Konfiguratsiya sozlamalari
            logger (logging.Logger): Log yozish uchun logger obyekti
        """
        self.config = config
        self.logger = logger
        self.db_type = config.get('db_type', 'sqlite').lower()
        self.connection = None
        self._connect()
    
    def _connect(self):
        """
        Ma'lumotlar bazasiga ulanish
        """
        try:
            if self.db_type == 'sqlite':
                db_path = self.config.get('db_path', '/var/lib/system-monitor/metrics.db')
                # Katalogni yaratish
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                self.connection = sqlite3.connect(db_path)
                self._create_tables_sqlite()
                self.logger.info(f"SQLite ma'lumotlar bazasiga ulandi: {db_path}")
            elif self.db_type == 'mysql':
                import mysql.connector
                self.connection = mysql.connector.connect(
                    host=self.config.get('db_host', 'localhost'),
                    port=self.config.get('db_port', 3306),
                    database=self.config.get('db_name', 'system_monitor'),
                    user=self.config.get('db_user', ''),
                    password=self.config.get('db_password', '')
                )
                self._create_tables_mysql()
                self.logger.info(f"MySQL ma'lumotlar bazasiga ulandi: {self.config.get('db_host')}:{self.config.get('db_port')}")
            elif self.db_type == 'postgresql':
                import psycopg2
                self.connection = psycopg2.connect(
                    host=self.config.get('db_host', 'localhost'),
                    port=self.config.get('db_port', 5432),
                    database=self.config.get('db_name', 'system_monitor'),
                    user=self.config.get('db_user', ''),
                    password=self.config.get('db_password', '')
                )
                self._create_tables_postgresql()
                self.logger.info(f"PostgreSQL ma'lumotlar bazasiga ulandi: {self.config.get('db_host')}:{self.config.get('db_port')}")
            else:
                self.logger.error(f"Noma'lum ma'lumotlar bazasi turi: {self.db_type}")
                self.connection = None
        except Exception as e:
            self.logger.error(f"Ma'lumotlar bazasiga ulanishda xatolik: {e}")
            self.connection = None
    
    def _create_tables_sqlite(self):
        """
        SQLite jadvallarini yaratish
        """
        cursor = self.connection.cursor()
        
        # Metrics jadvali
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            ram_usage REAL,
            cpu_usage REAL,
            disk_usage REAL,
            swap_usage REAL,
            load_average REAL,
            network_rx REAL,
            network_tx REAL,
            system_info TEXT
        )
        ''')
        
        # Alerts jadvali
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            usage_value TEXT NOT NULL,
            message TEXT,
            success INTEGER,
            system_info TEXT
        )
        ''')
        
        self.connection.commit()
    
    def _create_tables_mysql(self):
        """
        MySQL jadvallarini yaratish
        """
        cursor = self.connection.cursor()
        
        # Metrics jadvali
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp INT NOT NULL,
            ram_usage FLOAT,
            cpu_usage FLOAT,
            disk_usage FLOAT,
            swap_usage FLOAT,
            load_average FLOAT,
            network_rx FLOAT,
            network_tx FLOAT,
            system_info TEXT
        )
        ''')
        
        # Alerts jadvali
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp INT NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            usage_value VARCHAR(50) NOT NULL,
            message TEXT,
            success TINYINT,
            system_info TEXT
        )
        ''')
        
        self.connection.commit()
    
    def _create_tables_postgresql(self):
        """
        PostgreSQL jadvallarini yaratish
        """
        cursor = self.connection.cursor()
        
        # Metrics jadvali
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id SERIAL PRIMARY KEY,
            timestamp INTEGER NOT NULL,
            ram_usage REAL,
            cpu_usage REAL,
            disk_usage REAL,
            swap_usage REAL,
            load_average REAL,
            network_rx REAL,
            network_tx REAL,
            system_info TEXT
        )
        ''')
        
        # Alerts jadvali
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            timestamp INTEGER NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            usage_value VARCHAR(50) NOT NULL,
            message TEXT,
            success BOOLEAN,
            system_info TEXT
        )
        ''')
        
        self.connection.commit()
    
    def store_metrics(self, metrics, system_info):
        """
        Metrikalarni ma'lumotlar bazasiga saqlash
        
        Args:
            metrics (dict): Tizim metrikalari
            system_info (dict): Tizim ma'lumotlari
            
        Returns:
            bool: Muvaffaqiyatli saqlangan bo'lsa True
        """
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            timestamp = int(time.time())
            system_info_json = json.dumps(system_info)
            
            if self.db_type == 'sqlite' or self.db_type == 'mysql':
                cursor.execute('''
                INSERT INTO metrics (
                    timestamp, ram_usage, cpu_usage, disk_usage, swap_usage, 
                    load_average, network_rx, network_tx, system_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, 
                    metrics.get('ram', 0), 
                    metrics.get('cpu', 0), 
                    metrics.get('disk', 0), 
                    metrics.get('swap', 0), 
                    metrics.get('load', 0), 
                    metrics.get('network', [0, 0])[0], 
                    metrics.get('network', [0, 0])[1], 
                    system_info_json
                ))
            elif self.db_type == 'postgresql':
                cursor.execute('''
                INSERT INTO metrics (
                    timestamp, ram_usage, cpu_usage, disk_usage, swap_usage, 
                    load_average, network_rx, network_tx, system_info
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp, 
                    metrics.get('ram', 0), 
                    metrics.get('cpu', 0), 
                    metrics.get('disk', 0), 
                    metrics.get('swap', 0), 
                    metrics.get('load', 0), 
                    metrics.get('network', [0, 0])[0], 
                    metrics.get('network', [0, 0])[1], 
                    system_info_json
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Metrikalarni saqlashda xatolik: {e}")
            return False
    
    def store_alert(self, alert_type, usage_value, message, success, system_info):
        """
        Alertni ma'lumotlar bazasiga saqlash
        
        Args:
            alert_type (str): Alert turi
            usage_value (str): Alert qiymati
            message (str): Alert xabari
            success (bool): Muvaffaqiyatli yuborilgan bo'lsa True
            system_info (dict): Tizim ma'lumotlari
            
        Returns:
            bool: Muvaffaqiyatli saqlangan bo'lsa True
        """
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            timestamp = int(time.time())
            system_info_json = json.dumps(system_info)
            success_int = 1 if success else 0
            
            if self.db_type == 'sqlite' or self.db_type == 'mysql':
                cursor.execute('''
                INSERT INTO alerts (
                    timestamp, alert_type, usage_value, message, success, system_info
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, 
                    alert_type, 
                    usage_value, 
                    message, 
                    success_int, 
                    system_info_json
                ))
            elif self.db_type == 'postgresql':
                cursor.execute('''
                INSERT INTO alerts (
                    timestamp, alert_type, usage_value, message, success, system_info
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp, 
                    alert_type, 
                    usage_value, 
                    message, 
                    success, 
                    system_info_json
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Alertni saqlashda xatolik: {e}")
            return False
    
    def close(self):
        """
        Ma'lumotlar bazasi ulanishini yopish
        """
        if self.connection:
            self.connection.close()
            self.logger.info("Ma'lumotlar bazasi ulanishi yopildi")
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
