#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tizim monitoringi asosiy dasturi
"""

import os
import sys
import time
import argparse
import logging
import fcntl
from datetime import datetime

# Modullarni import qilish
from config.config_loader import ConfigLoader
from core.monitor import SystemMonitor
from core.alerts import AlertManager
from core.formatter import AlertFormatter

def setup_logger(log_file, log_level):
    """
    Logger sozlash
    
    Args:
        log_file (str): Log fayli yo'li
        log_level (str): Log darajasi
        
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
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # Logger yaratish
    logger = logging.getLogger('system_monitor')
    logger.setLevel(level)
    
    # Formatni o'rnatish
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    
    # Fayl handleri
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Log faylini yaratishda xatolik: {e}")
        print(f"Standart log fayli ishlatiladi: /tmp/system_monitor.log")
        file_handler = logging.FileHandler('/tmp/system_monitor.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Konsol handleri
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def main():
    """
    Asosiy dastur
    """
    # Lock faylini yaratish
    lock_file = '/tmp/system_monitor.lock'
    lock_fd = open(lock_file, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.error("Boshqa System Monitor jarayoni ishlamoqda. Dastur to'xtatiladi.")
        sys.exit(1)

    # Argumentlarni tahlil qilish
    parser = argparse.ArgumentParser(description='Tizim monitoringi')
    parser.add_argument('--config', type=str, default='./config.conf', help='Konfiguratsiya fayli yo\'li')
    args = parser.parse_args()
    
    # Boshlang'ich logger
    temp_logger = logging.getLogger('temp')
    temp_logger.setLevel(logging.INFO)
    temp_handler = logging.StreamHandler()
    temp_logger.addHandler(temp_handler)
    
    # Konfiguratsiyani yuklash
    config_loader = ConfigLoader(args.config, temp_logger)
    config = config_loader.get_config()
    
    # Asosiy loggerni sozlash
    logger = setup_logger(config['log_file'], config['log_level'])
    logger.info(f"System Monitor ishga tushirilmoqda...")
    logger.info(f"Konfiguratsiya fayli: {args.config}")
    
    # Monitoring obyektlarini yaratish
    monitor = SystemMonitor(config, logger)
    formatter = AlertFormatter(config, logger, monitor)
    alert_manager = AlertManager(config, logger, formatter, monitor)
    
    # Database obyektini yaratish (agar kerak bo'lsa)
    database = None
    if config.get('db_enabled', False):
        try:
            from utils.database import Database
            database = Database(config, logger)
            logger.info("Ma'lumotlar bazasi ulanishi o'rnatildi")
        except ImportError:
            logger.error("Database moduli topilmadi")
            config['db_enabled'] = False
        except Exception as e:
            logger.error(f"Ma'lumotlar bazasiga ulanishda xatolik: {e}")
            config['db_enabled'] = False
    
    # Asosiy monitoring sikli
    logger.info("Monitoring sikli boshlandi")
    
    try:
        while True:
            start_time = time.time()
            
            # Tizim ma'lumotlarini olish
            system_info = monitor.get_system_info()
            
            # Resurslarni tekshirish
            ram_usage = monitor.check_ram_usage()
            cpu_usage = monitor.check_cpu_usage() if config.get('monitor_cpu', False) else 0
            disk_usage = monitor.check_disk_usage() if config.get('monitor_disk', False) else 0
            swap_usage = monitor.check_swap_usage() if config.get('monitor_swap', False) else 0
            load_average = monitor.check_load_average() if config.get('monitor_load', False) else 0
            network_usage = monitor.check_network_usage() if config.get('monitor_network', False) else [0, 0]
            
            # Metrikalarni saqlash
            metrics = {
                'ram': ram_usage,
                'cpu': cpu_usage,
                'disk': disk_usage,
                'swap': swap_usage,
                'load': load_average,
                'network': network_usage
            }
            
            # Prometheus metrikalarini yangilash
            if config.get('prometheus_enabled', False):
                alert_manager.update_prometheus_metrics(metrics)
            
            # Ma'lumotlar bazasiga saqlash
            if config.get('db_enabled', False) and database:
                database.store_metrics(metrics, system_info)
            
            # Alertlarni tekshirish
            ram_threshold = config.get('ram_threshold', 80)
            if ram_usage >= ram_threshold:
                alert_manager.send_telegram_alert('RAM', f"{ram_usage}%", database, system_info, ram_usage, ram_threshold)
            
            cpu_threshold = config.get('cpu_threshold', 90)
            if config.get('monitor_cpu', False) and cpu_usage >= cpu_threshold:
                alert_manager.send_telegram_alert('CPU', f"{cpu_usage}%", database, system_info, cpu_usage, cpu_threshold)
            
            disk_threshold = config.get('disk_threshold', 90)
            if config.get('monitor_disk', False) and disk_usage >= disk_threshold:
                alert_manager.send_telegram_alert('Disk', f"{disk_usage}%", database, system_info, disk_usage, disk_threshold)
            
            swap_threshold = config.get('swap_threshold', 80)
            if config.get('monitor_swap', False) and swap_usage >= swap_threshold:
                alert_manager.send_telegram_alert('Swap', f"{swap_usage}%", database, system_info, swap_usage, swap_threshold)
            
            load_threshold = config.get('load_threshold', 80)
            if config.get('monitor_load', False) and load_average >= load_threshold:
                alert_manager.send_telegram_alert('Load', f"{load_average:.1f}%", database, system_info, load_average, load_threshold)
            
            network_threshold = config.get('network_threshold', 90)
            if config.get('monitor_network', False):
                network_rx = network_usage[0]
                network_tx = network_usage[1]
                if network_rx >= network_threshold:
                    alert_manager.send_telegram_alert('Network RX', f"{network_rx:.1f} Mbps", database, system_info, network_rx, network_threshold)
                if network_tx >= network_threshold:
                    alert_manager.send_telegram_alert('Network TX', f"{network_tx:.1f} Mbps", database, system_info, network_tx, network_threshold)
            
            # Keyingi tekshirishgacha kutish
            execution_time = time.time() - start_time
            sleep_time = max(1, config.get('check_interval', 60) - execution_time)
            
            logger.debug(f"Tekshirish tugadi. Keyingi tekshirishgacha {sleep_time:.1f} soniya")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Dastur to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
