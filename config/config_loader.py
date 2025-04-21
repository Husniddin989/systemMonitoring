#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Konfiguratsiya faylini o‘qish va standart qiymatlarni qo‘llash moduli
"""

import configparser
import os
import sys
import psutil
import logging

class ConfigLoader:
    def __init__(self, config_file, logger):
        """
        Konfiguratsiya yuklovchini ishga tushirish
        
        Args:
            config_file (str): Konfiguratsiya faylining yo‘li
            logger (logging.Logger): Log yozish uchun logger obyekti
        """
        self.config_file = config_file
        self.logger = logger
        self.config = self._load_config()

    def _load_config(self):
        """
        Konfiguratsiya faylini o‘qish va standart qiymatlarni qo‘llash
        
        Returns:
            dict: Konfiguratsiya sozlamalari
        """
        # Standart konfiguratsiya qiymatlari
        default_config = {
            'bot_token': "7120243579:AAEoaMz5DK8pv1uvwmbD--Mmt8nqbhL_mec",
            'chat_id': "664131109",
            'log_file': '/var/log/memory_monitor.log',
            'threshold': 80,
            'check_interval': 60,
            'log_level': 'INFO',
            'alert_message_title': "🖥️ SYSTEM STATUS ALERT",
            'include_top_processes': True,
            'top_processes_count': 10,
            'monitor_cpu': True,
            'cpu_threshold': 90,
            'monitor_disk': True,
            'disk_threshold': 90,
            'disk_path': "/",
            'monitor_swap': True,
            'swap_threshold': 80,
            'monitor_load': True,
            'load_threshold': 5,
            'monitor_network': True,
            'network_interface': "",
            'network_threshold': 90,
            # Ma'lumotlar bazasi sozlamalari
            'db_enabled': False,
            'db_type': "sqlite",
            'db_path': "/var/lib/memory-monitor/metrics.db",
            'db_host': "localhost",
            'db_port': 3306,
            'db_name': "system_monitor",
            'db_user': "",
            'db_password': "",
            # Prometheus sozlamalari
            'prometheus_enabled': False,
            'prometheus_port': 9090,
            # Alert format sozlamalari
            'alert_format_enabled': True,
            'alert_format_use_box_drawing': False,
            'alert_format_title_align': "left",
            'alert_format_width': 0,
            # Emojilar
            'alert_format_date_emoji': "📅",
            'alert_format_ram_emoji': "💥",
            'alert_format_cpu_emoji': "💥",
            'alert_format_disk_emoji': "💥",
            'alert_format_top_processes_emoji': "🔍",
            'alert_format_disk_breakdown_emoji': "🔍",
            'alert_format_hostname_emoji': "🖥️",
            'alert_format_ip_emoji': "🌐",
            'alert_format_uptime_emoji': "",
            'alert_format_os_emoji': "",
            'alert_format_kernel_emoji': "",
            # Tizim qismlarini ko‘rsatish
            'alert_format_include_system_info': True,
            'alert_format_include_resources': True,
            'alert_format_include_top_processes': True,
            'alert_format_include_disk_breakdown': True,
        }

        try:
            if not os.path.exists(self.config_file):
                self.logger.error(f"XATO: Konfiguratsiya fayli topilmadi: {self.config_file}")
                self.logger.error("Standart konfiguratsiya qiymatlari ishlatiladi.")
                return default_config

            config = configparser.ConfigParser()
            config.read(self.config_file)
            
            # INI bo‘limlarini konfiguratsiya lug‘atiga moslashtirish
            result = default_config.copy()
            
            # Umumiy sozlamalar
            if 'General' in config:
                for key in ['bot_token', 'chat_id', 'log_file', 'log_level', 'alert_message_title']:
                    if key in config['General']:
                        result[key] = config['General'][key]
                for key in ['threshold', 'check_interval', 'top_processes_count']:
                    if key in config['General']:
                        result[key] = int(config['General'][key])
                if 'include_top_processes' in config['General']:
                    result['include_top_processes'] = config['General'].getboolean('include_top_processes')
            
            # CPU monitoring
            if 'CPU' in config:
                if 'monitor_cpu' in config['CPU']:
                    result['monitor_cpu'] = config['CPU'].getboolean('monitor_cpu')
                if 'cpu_threshold' in config['CPU']:
                    result['cpu_threshold'] = int(config['CPU']['cpu_threshold'])
            
            # Disk monitoring
            if 'Disk' in config:
                for key in ['monitor_disk', 'disk_path']:
                    if key in config['Disk']:
                        result[key] = config['Disk'][key] if key == 'disk_path' else config['Disk'].getboolean(key)
                if 'disk_threshold' in config['Disk']:
                    result['disk_threshold'] = int(config['Disk']['disk_threshold'])
            
            # Swap monitoring
            if 'Swap' in config:
                if 'monitor_swap' in config['Swap']:
                    result['monitor_swap'] = config['Swap'].getboolean('monitor_swap')
                if 'swap_threshold' in config['Swap']:
                    result['swap_threshold'] = int(config['Swap']['swap_threshold'])
            
            # Load monitoring
            if 'Load' in config:
                if 'monitor_load' in config['Load']:
                    result['monitor_load'] = config['Load'].getboolean('monitor_load')
                if 'load_threshold' in config['Load']:
                    result['load_threshold'] = int(config['Load']['load_threshold'])
            
            # Network monitoring
            if 'Network' in config:
                for key in ['monitor_network', 'network_interface']:
                    if key in config['Network']:
                        result[key] = config['Network'][key] if key == 'network_interface' else config['Network'].getboolean(key)
                if 'network_threshold' in config['Network']:
                    result['network_threshold'] = int(config['Network']['network_threshold'])
            
            # Ma'lumotlar bazasi sozlamalari
            if 'Database' in config:
                for key in ['db_enabled', 'db_type', 'db_path', 'db_host', 'db_name', 'db_user', 'db_password']:
                    if key in config['Database']:
                        result[key] = config['Database'][key] if key != 'db_enabled' else config['Database'].getboolean(key)
                if 'db_port' in config['Database']:
                    result['db_port'] = int(config['Database']['db_port'])
            
            # Prometheus sozlamalari
            if 'Prometheus' in config:
                if 'prometheus_enabled' in config['Prometheus']:
                    result['prometheus_enabled'] = config['Prometheus'].getboolean('prometheus_enabled')
                if 'prometheus_port' in config['Prometheus']:
                    result['prometheus_port'] = int(config['Prometheus']['prometheus_port'])
            
            # Alert format sozlamalari
            if 'AlertFormat' in config:
                for key in ['alert_format_enabled', 'alert_format_use_box_drawing', 
                           'alert_format_include_system_info', 'alert_format_include_resources',
                           'alert_format_include_top_processes', 'alert_format_include_disk_breakdown']:
                    if key in config['AlertFormat']:
                        result[key] = config['AlertFormat'].getboolean(key)
                for key in ['alert_format_title_align', 'alert_format_date_emoji', 'alert_format_ram_emoji',
                           'alert_format_cpu_emoji', 'alert_format_disk_emoji', 'alert_format_top_processes_emoji',
                           'alert_format_disk_breakdown_emoji', 'alert_format_hostname_emoji', 'alert_format_ip_emoji',
                           'alert_format_uptime_emoji', 'alert_format_os_emoji', 'alert_format_kernel_emoji']:
                    if key in config['AlertFormat']:
                        result[key] = config['AlertFormat'][key]
                if 'alert_format_width' in config['AlertFormat']:
                    result['alert_format_width'] = int(config['AlertFormat']['alert_format_width'])
            
            # Kerakli sozlamalarni tekshirish
            if not result['bot_token'] or not result['chat_id']:
                self.logger.error("XATO: BOT_TOKEN va CHAT_ID konfiguratsiya faylida ko'rsatilishi kerak.")
                sys.exit(1)
            
            # Tarmoq interfeysini avtomatik aniqlash
            if not result['network_interface']:
                interfaces = psutil.net_if_addrs()
                for iface in interfaces:
                    if iface != 'lo':
                        result['network_interface'] = iface
                        break
            
            self.logger.info(f"Konfiguratsiya fayli muvaffaqiyatli o‘qildi: {self.config_file}")
            return result
            
        except Exception as e:
            self.logger.error(f"Konfiguratsiya faylini o‘qishda xatolik: {e}")
            self.logger.error("Standart konfiguratsiya qiymatlari ishlatiladi.")
            return default_config

    def get_config(self):
        """
        Yuklangan konfiguratsiyani qaytarish
        
        Returns:
            dict: Konfiguratsiya sozlamalari
        """
        return self.config