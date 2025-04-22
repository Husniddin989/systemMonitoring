#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram orqali alert yuborish va Prometheus metrikalarini yangilash moduli
"""

import requests
import time
import datetime
from prometheus_client import start_http_server, Gauge, Counter

class AlertManager:
    def __init__(self, config, logger, formatter, monitor):
        """
        Alert boshqaruvchisini ishga tushirish
        
        Args:
            config (dict): Konfiguratsiya sozlamalari
            logger (logging.Logger): Log yozish uchun logger obyekti
            formatter (AlertFormatter): Xabar formatlovchi obyekti
            monitor (SystemMonitor): Tizim monitoring obyekti
        """
        self.config = config
        self.logger = logger
        self.formatter = formatter
        self.monitor = monitor
        self.last_alert_times = {
            'ram': 0,
            'cpu': 0,
            'disk': 0,
            'swap': 0,
            'load': 0,
            'network': 0,
            'network_rx': 0,
            'network_tx': 0
        }
        
        # Threshold qiymatlaridan oshganligini kuzatish uchun
        self.threshold_crossed = {
            'ram': False,
            'cpu': False,
            'disk': False,
            'swap': False,
            'load': False,
            'network': False,
            'network_rx': False,
            'network_tx': False
        }
        
        # Oxirgi yuborilgan alert vaqti (barcha alertlar uchun)
        self.last_any_alert_time = 0
        
        # Prometheus sozlamalari
        if self.config.get('prometheus_enabled', False):
            self._init_prometheus()
        
        # Telegram ulanishini sinovdan o'tkazish
        self.test_telegram_connection()

    def _init_prometheus(self):
        """
        Prometheus metrikalarini ishga tushirish
        """
        try:
            # Metrikalarni yaratish
            self.prom_ram_usage = Gauge('system_monitor_ram_usage_percent', 'RAM usage in percent')
            self.prom_cpu_usage = Gauge('system_monitor_cpu_usage_percent', 'CPU usage in percent')
            self.prom_disk_usage = Gauge('system_monitor_disk_usage_percent', 'Disk usage in percent')
            self.prom_swap_usage = Gauge('system_monitor_swap_usage_percent', 'Swap usage in percent')
            self.prom_load_average = Gauge('system_monitor_load_average', 'System load average')
            self.prom_network_rx = Gauge('system_monitor_network_rx_mbps', 'Network receive rate in Mbps')
            self.prom_network_tx = Gauge('system_monitor_network_tx_mbps', 'Network transmit rate in Mbps')
            
            # Alert hisoblagichlari
            self.prom_ram_alerts = Counter('system_monitor_ram_alerts_total', 'Total number of RAM alerts')
            self.prom_cpu_alerts = Counter('system_monitor_cpu_alerts_total', 'Total number of CPU alerts')
            self.prom_disk_alerts = Counter('system_monitor_disk_alerts_total', 'Total number of disk alerts')
            self.prom_swap_alerts = Counter('system_monitor_swap_alerts_total', 'Total number of swap alerts')
            self.prom_load_alerts = Counter('system_monitor_load_alerts_total', 'Total number of load alerts')
            self.prom_network_alerts = Counter('system_monitor_network_alerts_total', 'Total number of network alerts')
            
            # Serverni ishga tushirish
            prometheus_port = self.config.get('prometheus_port', 9090)
            start_http_server(prometheus_port)
            self.logger.info(f"Prometheus exporter ishga tushirildi, port: {prometheus_port}")
            
        except ImportError:
            self.logger.error("Prometheus-client o'rnatilmagan. 'pip install prometheus-client' buyrug'i bilan o'rnating.")
            self.config['prometheus_enabled'] = False
        except Exception as e:
            self.logger.error(f"Prometheus exporterni ishga tushirishda xatolik: {e}")
            self.config['prometheus_enabled'] = False

    def update_prometheus_metrics(self, metrics):
        """
        Prometheus metrikalarini yangilash
        
        Args:
            metrics (dict): Tizim metrikalari
            
        Returns:
            bool: Muvaffaqiyatli yangilangan bo'lsa True
        """
        if not self.config.get('prometheus_enabled', False):
            return False
        
        try:
            self.prom_ram_usage.set(metrics.get('ram', 0))
            self.prom_cpu_usage.set(metrics.get('cpu', 0))
            self.prom_disk_usage.set(metrics.get('disk', 0))
            self.prom_swap_usage.set(metrics.get('swap', 0))
            self.prom_load_average.set(metrics.get('load', 0))
            
            if 'network' in metrics and isinstance(metrics['network'], list) and len(metrics['network']) == 2:
                self.prom_network_rx.set(metrics['network'][0])
                self.prom_network_tx.set(metrics['network'][1])
            
            self.logger.debug("Prometheus metrikalari muvaffaqiyatli yangilandi")
            return True
            
        except Exception as e:
            self.logger.error(f"Prometheus metrikalarini yangilashda xatolik: {e}")
            return False

    def check_threshold_crossing(self, alert_type, current_value, threshold):
        """
        Threshold qiymatidan oshganligini tekshirish
        
        Args:
            alert_type (str): Alert turi
            current_value (float): Joriy qiymat
            threshold (float): Threshold qiymati
            
        Returns:
            bool: Alert yuborish kerak bo'lsa True
        """
        alert_key = alert_type.lower()
        alert_mode = self.config.get('alert_mode', 'threshold_cross')
        
        # Agar alert_mode 'continuous' bo'lsa, har doim alert yuborish
        if alert_mode == 'continuous':
            return current_value >= threshold
        
        # Agar alert_mode 'threshold_cross' bo'lsa, faqat threshold qiymatidan oshganda alert yuborish
        if current_value >= threshold:
            if not self.threshold_crossed.get(alert_key, False):
                self.threshold_crossed[alert_key] = True
                return True
        else:
            # Threshold qiymatidan pastga tushganda, keyingi safar yana alert yuborish uchun
            self.threshold_crossed[alert_key] = False
        
        return False

    def check_alert_interval(self, alert_type):
        """
        Alert yuborish intervalini tekshirish
        
        Args:
            alert_type (str): Alert turi
            
        Returns:
            bool: Alert yuborish mumkin bo'lsa True
        """
        current_time = int(time.time())
        alert_key = alert_type.lower()
        
        # Har qanday alert uchun minimal interval (barcha alertlar uchun)
        min_alert_interval = self.config.get('min_alert_interval', 300)  # 5 daqiqa
        time_since_last_any_alert = current_time - self.last_any_alert_time
        
        if time_since_last_any_alert < min_alert_interval:
            self.logger.debug(f"Alert cheklandi (so'nggi alertdan {time_since_last_any_alert} soniya o'tdi, minimal interval: {min_alert_interval})")
            return False
        
        # Har bir alert turi uchun alohida interval
        alert_interval = self.config.get('alert_interval', 1800)  # 30 daqiqa
        time_since_last_alert = current_time - self.last_alert_times.get(alert_key, 0)
        
        if time_since_last_alert < alert_interval:
            self.logger.debug(f"{alert_type} alert cheklandi (so'nggi xabardan {time_since_last_alert} soniya o'tdi, interval: {alert_interval})")
            return False
        
        return True

    def send_telegram_alert(self, alert_type, usage_value, database, system_info, current_value=None, threshold=None):
        """
        Telegram orqali alert yuborish
        
        Args:
            alert_type (str): Alert turi
            usage_value (str): Alert qiymati
            database (Database): Ma'lumotlar bazasi obyekti
            system_info (dict): Tizim ma'lumotlari
            current_value (float, optional): Joriy qiymat
            threshold (float, optional): Threshold qiymati
            
        Returns:
            bool: Muvaffaqiyatli yuborilgan bo'lsa True
        """
        # Threshold qiymatidan oshganligini tekshirish
        if current_value is not None and threshold is not None:
            if not self.check_threshold_crossing(alert_type, current_value, threshold):
                self.logger.debug(f"{alert_type} alert yuborilmadi (threshold qiymatidan oshmagan)")
                return False
        
        # Alert intervalini tekshirish
        if not self.check_alert_interval(alert_type):
            return False
        
        message = self.formatter.format_alert_message(alert_type, usage_value)
        if not message:
            self.logger.debug(f"{alert_type or 'SYSTEM STATUS'} xabari formatlanmadi")
            return False
    
        self.logger.debug(f"Telegramga yuboriladigan xabar: {message}")
        
        self.logger.info('-' * 40)
        self.logger.info(message)
        
        max_retries = 3
        retry = 0
        success = False
        
        while retry < max_retries and not success:
            try:
                self.logger.debug(f"Telegramga xabar yuborilmoqda: {alert_type}")
                url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
                payload = {
                    'chat_id': self.config['chat_id'],
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200 and response.json().get('ok'):
                    self.logger.info(f"{alert_type} alert xabari Telegramga muvaffaqiyatli yuborildi")
                    success = True
                    
                    # Alert vaqtlarini yangilash
                    current_time = int(time.time())
                    self.last_alert_times[alert_type.lower()] = current_time
                    self.last_any_alert_time = current_time
                    
                    if self.config.get('prometheus_enabled', False):
                        alert_key = alert_type.lower()
                        if alert_key.startswith('network_'):
                            alert_key = 'network'
                        if hasattr(self, f"prom_{alert_key}_alerts"):
                            getattr(self, f"prom_{alert_key}_alerts").inc()
                    
                    if self.config.get('db_enabled', False) and database:
                        database.store_alert(alert_type, usage_value, message, True, system_info)
                    
                else:
                    retry += 1
                    error_description = response.json().get('description', 'Unknown error')
                    self.logger.warning(f"Telegramga xabar yuborishda xatolik (urinish {retry}/{max_retries}): {error_description}")
                    time.sleep(2)
                    
            except Exception as e:
                retry += 1
                self.logger.warning(f"Telegramga xabar yuborishda xatolik (urinish {retry}/{max_retries}): {e}")
                time.sleep(2)
        
        if not success:
            self.logger.error(f"Telegramga xabar yuborib bo'lmadi ({max_retries} urinishdan so'ng)")
            self.logger.error(f"BOT_TOKEN: {self.config['bot_token'][:5]}...{self.config['bot_token'][-5:]}")
            self.logger.error(f"CHAT_ID: {self.config['chat_id']}")
            
            if self.config.get('db_enabled', False) and database:
                database.store_alert(alert_type, usage_value, message, False, system_info)
            
            return False
        
        return True

    def test_telegram_connection(self):
        """
        Telegram ulanishini sinovdan o'tkazish
        
        Returns:
            bool: Muvaffaqiyatli ulangan bo'lsa True
        """
        self.logger.info('Telegram bog\'lanishini tekshirish...')
        system_info = self.monitor.get_system_info()
        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.config.get('alert_format_enabled', False):
            width = self.config.get('alert_format_width', 44)
            use_box_drawing = self.config.get('alert_format_use_box_drawing', True)
            
            if use_box_drawing:
                line_prefix = self.config.get('alert_format_line_prefix', '│ ')
                line_suffix = self.config.get('alert_format_line_suffix', ' │')
            else:
                line_prefix = ""
                line_suffix = ""
                
            content_width = width - len(line_prefix) - len(line_suffix) if width > 0 else 0
            
            message = []
            if use_box_drawing:
                message.append(self.config.get('alert_format_top_border', '┌' + '─' * (width - 2) + '┐'))
            
            message.append(f"{line_prefix}🔄 SYSTEM MONITOR TEST MESSAGE{' ' * (content_width - len('🔄 SYSTEM MONITOR TEST MESSAGE'))}{line_suffix}")
            
            if use_box_drawing:
                message.append(self.config.get('alert_format_title_border', '├' + '─' * (width - 2) + '┤'))
            
            message.append(f"{line_prefix}🖥️ Hostname:     {system_info['hostname']}{' ' * (content_width - len('🖥️ Hostname:     ') - len(system_info['hostname']))}{line_suffix}")
            message.append(f"{line_prefix}🌐 IP Address:   {system_info['ip']}{' ' * (content_width - len('🌐 IP Address:   ') - len(system_info['ip']))}{line_suffix}")
            message.append(f"{line_prefix}⏱️ Time:         {date_str}{' ' * (content_width - len('⏱️ Time:         ') - len(date_str))}{line_suffix}")
            
            if use_box_drawing:
                message.append(self.config.get('alert_format_bottom_border', '└' + '─' * (width - 2) + '┘'))
            
            message = "\n".join(message)
        else:
            message = "🔄 SYSTEM MONITOR TEST MESSAGE\n\n"
            message += f"🖥️ Hostname: {system_info['hostname']}\n"
            message += f"🌐 IP Address: {system_info['ip']}\n"
            message += f"⏱️ Time: {date_str}"
        
        try:
            url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
            payload = {
                'chat_id': self.config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200 and response.json().get('ok'):
                self.logger.info('Telegram bog\'lanishi muvaffaqiyatli tekshirildi')
                return True
            else:
                error_description = response.json().get('description', 'Unknown error')
                self.logger.error(f"Telegram bog'lanishini tekshirishda xatolik: {error_description}")
                self.logger.error(f"BOT_TOKEN: {self.config['bot_token'][:5]}...{self.config['bot_token'][-5:]}")
                self.logger.error(f"CHAT_ID: {self.config['chat_id']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram bog'lanishini tekshirishda xatolik: {e}")
            return False
