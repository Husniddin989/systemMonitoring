#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Konfiguratsiya faylini test qilish uchun skript
"""

import os
import sys
import logging

# Modullarni import qilish
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config_loader import ConfigLoader

# Logger sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('config_test')

def test_config_loader():
    """
    ConfigLoader klassini test qilish
    """
    logger.info("ConfigLoader klassini test qilish...")
    
    # Konfiguratsiya faylini yuklash
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.conf")
    logger.info(f"Konfiguratsiya fayli: {config_file}")
    
    # ConfigLoader obyektini yaratish
    config_loader = ConfigLoader(config_file, logger)
    config = config_loader.get_config()
    
    # Konfiguratsiya parametrlarini tekshirish
    logger.info("Konfiguratsiya parametrlarini tekshirish...")
    
    # Asosiy parametrlar
    logger.info(f"Bot token: {config['bot_token'][:5]}...{config['bot_token'][-5:]}")
    logger.info(f"Chat ID: {config['chat_id']}")
    logger.info(f"Log fayli: {config['log_file']}")
    logger.info(f"Log darajasi: {config['log_level']}")
    logger.info(f"Tekshirish oralig'i: {config['check_interval']} soniya")
    
    # Monitoring parametrlari
    logger.info(f"CPU monitoring: {config['monitor_cpu']}")
    logger.info(f"CPU threshold: {config['cpu_threshold']}%")
    logger.info(f"RAM threshold: {config['ram_threshold']}%")
    logger.info(f"Disk monitoring: {config['monitor_disk']}")
    logger.info(f"Disk threshold: {config['disk_threshold']}%")
    logger.info(f"Disk yo'li: {config['disk_path']}")
    logger.info(f"Swap monitoring: {config['monitor_swap']}")
    logger.info(f"Swap threshold: {config['swap_threshold']}%")
    logger.info(f"Load monitoring: {config['monitor_load']}")
    logger.info(f"Load threshold: {config['load_threshold']}%")
    logger.info(f"Network monitoring: {config['monitor_network']}")
    logger.info(f"Network interfeysi: {config['network_interface']}")
    logger.info(f"Network threshold: {config['network_threshold']}%")
    
    # Top jarayonlar
    logger.info(f"Top jarayonlarni ko'rsatish: {config['include_top_processes']}")
    logger.info(f"Top jarayonlar soni: {config['top_processes_count']}")
    logger.info(f"Top jarayonlar umumiy CPU foizini ko'rsatish: {config['show_total_cpu_usage_in_list']}")
    logger.info(f"Umumiy CPU foizi sifatida top jarayonlar yig'indisini ko'rsatish: {config['show_top_processes_cpu_sum']}")
    
    # Ma'lumotlar bazasi
    logger.info(f"Ma'lumotlar bazasi yoqilgan: {config['db_enabled']}")
    logger.info(f"Ma'lumotlar bazasi turi: {config['db_type']}")
    
    # Prometheus
    logger.info(f"Prometheus yoqilgan: {config['prometheus_enabled']}")
    logger.info(f"Prometheus port: {config['prometheus_port']}")
    
    # Alert format
    logger.info(f"Alert format yoqilgan: {config['alert_format_enabled']}")
    logger.info(f"Ramka chizish: {config['alert_format_use_box_drawing']}")
    logger.info(f"Kenglik: {config['alert_format_width']}")
    logger.info(f"Sarlavha tekislash: {config['alert_format_title_align']}")
    
    logger.info("ConfigLoader testi muvaffaqiyatli yakunlandi!")
    return True

if __name__ == "__main__":
    test_config_loader()
