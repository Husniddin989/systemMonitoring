#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ma'lumotlar bazasi bilan ishlash moduli
Metrics va alertlarni saqlash uchun
"""

import logging
import sqlite3
import datetime
import json
import os

class Database:
    def __init__(self, config, logger):
        """
        Ma'lumotlar bazasi ulanishini ishga tushirish
        
        Args:
            config (dict): Konfiguratsiya sozlamalari
            logger (logging.Logger): Log yozish uchun logger obyekti
        """
        self.config = config
        self.logger = logger
        self.db_conn = None
        self.db_cursor = None
        
        if self.config['db_enabled']:
            self._init_database()

    def _init_database(self):
        """
        Ma'lumotlar bazasi ulanishini tashkil qilish va jadvallarni yaratish
        SQLite, MySQL va PostgreSQL ni qo‘llab-quvvatlaydi
        """
        try:
            db_type = self.config['db_type']
            self.logger.info(f"Ma'lumotlar bazasi integratsiyasi yoqilgan: {db_type}")
            
            if db_type == 'sqlite':
                # Direktoriyani yaratish
                db_dir = os.path.dirname(self.config['db_path'])
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                
                # SQLite ma'lumotlar bazasiga ulanish
                self.db_conn = sqlite3.connect(self.config['db_path'])
                self.db_cursor = self.db_conn.cursor()
                
                # Jadvallarni yaratish
                self.db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        hostname TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        ram_usage REAL,
                        cpu_usage REAL,
                        disk_usage REAL,
                        swap_usage REAL,
                        load_average REAL,
                        network_rx REAL,
                        network_tx REAL,
                        extra_data TEXT
                    )
                ''')
                
                self.db_cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        hostname TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        value TEXT NOT NULL,
                        message TEXT,
                        sent_successfully BOOLEAN
                    )
                ''')
                
                self.db_conn.commit()
                self.logger.info("SQLite ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")
                
            elif db_type == 'mysql':
                try:
                    import mysql.connector
                    self.db_conn = mysql.connector.connect(
                        host=self.config['db_host'],
                        port=self.config['db_port'],
                        user=self.config['db_user'],
                        password=self.config['db_password'],
                        database=self.config['db_name']
                    )
                    self.db_cursor = self.db_conn.cursor()
                    
                    # Jadvallarni yaratish
                    self.db_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS metrics (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            timestamp DATETIME NOT NULL,
                            hostname VARCHAR(255) NOT NULL,
                            ip_address VARCHAR(45) NOT NULL,
                            ram_usage FLOAT,
                            cpu_usage FLOAT,
                            disk_usage FLOAT,
                            swap_usage FLOAT,
                            load_average FLOAT,
                            network_rx FLOAT,
                            network_tx FLOAT,
                            extra_data TEXT
                        )
                    ''')
                    
                    self.db_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS alerts (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            timestamp DATETIME NOT NULL,
                            hostname VARCHAR(255) NOT NULL,
                            alert_type VARCHAR(50) NOT NULL,
                            value VARCHAR(100) NOT NULL,
                            message TEXT,
                            sent_successfully BOOLEAN
                        )
                    ''')
                    
                    self.db_conn.commit()
                    self.logger.info("MySQL ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")
                    
                except ImportError:
                    self.logger.error("MySQL-connector-python o'rnatilmagan. 'pip install mysql-connector-python' buyrug'i bilan o'rnating.")
                    self.config['db_enabled'] = False
                
            elif db_type == 'postgresql':
                try:
                    import psycopg2
                    self.db_conn = psycopg2.connect(
                        host=self.config['evole']['db_host'],
                        port=self.config['db_port'],
                        user=self.config['db_user'],
                        password=self.config['db_password'],
                        database=self.config['db_name']
                    )
                    self.db_cursor = self.db_conn.cursor()
                    
                    # Jadvallarni yaratish
                    self.db_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS metrics (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP NOT NULL,
                            hostname VARCHAR(255) NOT NULL,
                            ip_address VARCHAR(45) NOT NULL,
                            ram_usage FLOAT,
                            cpu_usage FLOAT,
                            disk_usage FLOAT,
                            swap_usage FLOAT,
                            load_average FLOAT,
                            network_rx FLOAT,
                            network_tx FLOAT,
                            extra_data TEXT
                        )
                    ''')
                    
                    self.db_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS alerts (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP NOT NULL,
                            hostname VARCHAR(255) NOT NULL,
                            alert_type VARCHAR(50) NOT NULL,
                            value VARCHAR(100) NOT NULL,
                            message TEXT,
                            sent_successfully BOOLEAN
                        )
                    ''')
                    
                    self.db_conn.commit()
                    self.logger.info("PostgreSQL ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi")
                    
                except ImportError:
                    self.logger.error("Psycopg2 o'rnatilmagan. 'pip install psycopg2-binary' buyrug'i bilan o'rnating.")
                    self.config['db_enabled'] = False
                
            else:
                self.logger.error(f"Noma'lum ma'lumotlar bazasi turi: {db_type}")
                self.config['db_enabled'] = False
                
        except Exception as e:
            self.logger.error(f"Ma'lumotlar bazasini ishga tushirishda xatolik: {e}")
            self.config['db_enabled'] = False

    def store_metrics(self, metrics, system_info):
        """
        Tizim metrikalarini ma'lumotlar bazasida saqlash
        
        Args:
            metrics (dict): Tizim metrikalari lug‘ati
            system_info (dict): Tizim haqida ma'lumotlar lug‘ati
            
        Returns:
            bool: Metrikalar muvaffaqiyatli saqlangan bo‘lsa True, aks holda False
        """
        if not self.config['db_enabled']:
            return False
        
        try:
            # Tarmoq metrikalarini ajratish
            network_rx, network_tx = 0.0, 0.0
            if 'network' in metrics and isinstance(metrics['network'], list) and len(metrics['network']) == 2:
                network_rx, network_tx = metrics['network']
            
            # Qo‘shimcha ma'lumotlarni tayyorlash
            extra_data = {}
            for key, value in metrics.items():
                if key not in ['ram', 'cpu', 'disk', 'swap', 'load', 'network']:
                    extra_data[key] = value
            
            extra_data_json = json.dumps(extra_data) if extra_data else None
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if self.config['db_type'] == 'sqlite':
                self.db_cursor.execute('''
                    INSERT INTO metrics (
                        timestamp, hostname, ip_address, ram_usage, cpu_usage, disk_usage, 
                        swap_usage, load_average, network_rx, network_tx, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    system_info['hostname'],
                    system_info['ip'],
                    metrics.get('ram', 0.0),
                    metrics.get('cpu', 0.0),
                    metrics.get('disk', 0.0),
                    metrics.get('swap', 0.0),
                    metrics.get('load', 0.0),
                    network_rx,
                    network_tx,
                    extra_data_json
                ))
                
                self.db_conn.commit()
                
            elif self.config['db_type'] == 'mysql':
                self.db_cursor.execute('''
                    INSERT INTO metrics (
                        timestamp, hostname, ip_address, ram_usage, cpu_usage, disk_usage, 
                        swap_usage, load_average, network_rx, network_tx, extra_data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp,
                    system_info['hostname'],
                    system_info['ip'],
                    metrics.get('ram', 0.0),
                    metrics.get('cpu', 0.0),
                    metrics.get('disk', 0.0),
                    metrics.get('swap', 0.0),
                    metrics.get('load', 0.0),
                    network_rx,
                    network_tx,
                    extra_data_json
                ))
                
                self.db_conn.commit()
                
            elif self.config['db_type'] == 'postgresql':
                self.db_cursor.execute('''
                    INSERT INTO metrics (
                        timestamp, hostname, ip_address, ram_usage, cpu_usage, disk_usage, 
                        swap_usage, load_average, network_rx, network_tx, extra_data
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp,
                    system_info['hostname'],
                    system_info['ip'],
                    metrics.get('ram', 0.0),
                    metrics.get('cpu', 0.0),
                    metrics.get('disk', 0.0),
                    metrics.get('swap', 0.0),
                    metrics.get('load', 0.0),
                    network_rx,
                    network_tx,
                    extra_data_json
                ))
                
                self.db_conn.commit()
            
            self.logger.debug("Metrikalar ma'lumotlar bazasida muvaffaqiyatli saqlandi")
            return True
            
        except Exception as e:
            self.logger.error(f"Metrikalarni saqlashda xatolik: {e}")
            return False

    def store_alert(self, alert_type, value, message, sent_successfully, system_info):
        """
        Alert ma'lumotlarini ma'lumotlar bazasida saqlash
        
        Args:
            alert_type (str): Alert turi (masalan, 'RAM', 'CPU')
            value (str): Alert qiymati (masalan, '85%')
            message (str): Alert xabari mazmuni
            sent_successfully (bool): Alert muvaffaqiyatli yuborilganligi
            system_info (dict): Tizim haqida ma'lumotlar lug‘ati
            
        Returns:
            bool: Alert muvaffaqiyatli saqlangan bo‘lsa True, aks holda False
        """
        if not self.config['db_enabled']:
            return False
        
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if self.config['db_type'] == 'sqlite':
                self.db_cursor.execute('''
                    INSERT INTO alerts (
                        timestamp, hostname, alert_type, value, message, sent_successfully
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    system_info['hostname'],
                    alert_type,
                    str(value),
                    message,
                    1 if sent_successfully else 0
                ))
                
                self.db_conn.commit()
                
            elif self.config['db_type'] == 'mysql':
                self.db_cursor.execute('''
                    INSERT INTO alerts (
                        timestamp, hostname, alert_type, value, message, sent_successfully
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp,
                    system_info['hostname'],
                    alert_type,
                    str(value),
                    message,
                    sent_successfully
                ))
                
                self.db_conn.commit()
                
            elif self.config['db_type'] == 'postgresql':
                self.db_cursor.execute('''
                    INSERT INTO alerts (
                        timestamp, hostname, alert_type, value, message, sent_successfully
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    timestamp,
                    system_info['hostname'],
                    alert_type,
                    str(value),
                    message,
                    sent_successfully
                ))
                
                self.db_conn.commit()
            
            self.logger.debug(f"Alert muvaffaqiyatli saqlandi: {alert_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Alertni saqlashda xatolik: {e}")
            return False

    def close(self):
        """
        Ma'lumotlar bazasi ulanishini yopish
        """
        if self.db_conn:
            self.db_conn.close()
            self.logger.info("Ma'lumotlar bazasi ulanishi yopildi")