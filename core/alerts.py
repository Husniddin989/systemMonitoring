#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alert xabarlarini yuborish moduli - tez-tez xabar yuborish uchun o'zgartirilgan
"""

import time
import json
import logging
import requests
from datetime import datetime

class AlertManager:
    def __init__(self, config, logger, formatter, monitor=None):
        """
        Alert managerini ishga tushirish
        
        Args:
            config (dict): Konfiguratsiya sozlamalari
            logger (logging.Logger): Log yozish uchun logger obyekti
            formatter (AlertFormatter): Alert xabarlarini formatlash uchun formatter obyekti
            monitor (SystemMonitor, optional): Tizim monitoring obyekti
        """
        self.config = config
        self.logger = logger
        self.formatter = formatter
        self.monitor = monitor
        
        # Telegram bot token va chat ID
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
        
        # Alert yuborish rejimi
        self.alert_mode = config.get('alert_mode', 'threshold_cross')
        
        # Alert intervallarini o'rnatish
        self.min_alert_interval = config.get('min_alert_interval', 300)
        self.alert_interval = config.get('alert_interval', 1800)
        
        # So'nggi alert vaqtlarini saqlash uchun lug'at
        self.last_alert_times = {}
        
        # Prometheus metrikalarini saqlash uchun lug'at
        self.prometheus_metrics = {}
        
        # Telegram bog'lanishini tekshirish
        self._check_telegram_connection()
    
    def _check_telegram_connection(self):
        """
        Telegram bog'lanishini tekshirish
        """
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram bot token yoki chat ID ko'rsatilmagan")
            return False
        
        self.logger.info("Telegram bog'lanishini tekshirish...")
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.logger.info("Telegram bog'lanishi muvaffaqiyatli tekshirildi")
                return True
            else:
                self.logger.error(f"Telegram bog'lanishini tekshirishda xatolik: {response.reason}")
                self.logger.error(f"BOT_TOKEN: {self.bot_token[:3]}...")
                self.logger.error(f"CHAT_ID: {self.chat_id}")
                return False
        except Exception as e:
            self.logger.error(f"Telegram bog'lanishini tekshirishda xatolik: {str(e)}")
            self.logger.error(f"BOT_TOKEN: {self.bot_token[:3]}...")
            self.logger.error(f"CHAT_ID: {self.chat_id}")
            return False
    
    def _standardize_alert_key(self, alert_type):
        """
        Alert turini standartlashtirish
        
        Args:
            alert_type (str): Alert turi
            
        Returns:
            str: Standartlashtirilgan alert turi
        """
        if not alert_type:
            return "unknown"
        
        # Kichik harflarga o'girish
        alert_key = alert_type.lower()
        
        # Network RX va TX uchun maxsus ishlov
        if alert_key == "network rx":
            return "network_rx"
        elif alert_key == "network tx":
            return "network_tx"
        
        # Bo'shliqlarni _ bilan almashtirish
        alert_key = alert_key.replace(" ", "_")
        
        return alert_key
    
    def check_alert_interval(self, alert_type):
        """
        Alert yuborish intervali tekshirish
        
        Args:
            alert_type (str): Alert turi
            
        Returns:
            bool: Alert yuborish mumkinligi
        """
        # Alert turini standartlashtirish
        alert_key = self._standardize_alert_key(alert_type)
        
        # Joriy vaqt
        current_time = time.time()
        
        # So'nggi alert vaqtini olish
        last_alert_time = self.last_alert_times.get(alert_key, 0)
        
        # Alert yuborish rejimini tekshirish
        if self.alert_mode == 'continuous':
            # Minimal interval
            min_interval = self.min_alert_interval
            
            # Metrika turiga qarab interval
            if hasattr(self.config, 'get') and callable(self.config.get):
                metric_interval_key = f"{alert_key}_alert_interval"
                if self.config.get(metric_interval_key):
                    min_interval = self.config.get(metric_interval_key)
            
            # Vaqt farqi
            time_diff = current_time - last_alert_time
            
            # Minimal intervaldan kam bo'lsa, alert yuborilmaydi
            if time_diff < min_interval:
                self.logger.debug(f"Alert cheklandi (so'nggi alertdan {int(time_diff)} soniya o'tdi, minimal interval: {min_interval})")
                return False
            
            # Alert vaqtini yangilash
            self.last_alert_times[alert_key] = current_time
            return True
        
        elif self.alert_mode == 'threshold_cross':
            # Agar so'nggi alert vaqti 0 bo'lsa, alert yuboriladi
            if last_alert_time == 0:
                self.last_alert_times[alert_key] = current_time
                return True
            
            # Alert intervali
            alert_interval = self.alert_interval
            
            # Metrika turiga qarab interval
            if hasattr(self.config, 'get') and callable(self.config.get):
                metric_interval_key = f"{alert_key}_alert_interval"
                if self.config.get(metric_interval_key):
                    alert_interval = self.config.get(metric_interval_key)
            
            # Vaqt farqi
            time_diff = current_time - last_alert_time
            
            # Alert intervalidan kam bo'lsa, alert yuborilmaydi
            if time_diff < alert_interval:
                self.logger.debug(f"Alert cheklandi (so'nggi alertdan {int(time_diff)} soniya o'tdi, interval: {alert_interval})")
                return False
            
            # Alert vaqtini yangilash
            self.last_alert_times[alert_key] = current_time
            return True
        
        # Noma'lum rejim
        self.logger.warning(f"Noma'lum alert rejimi: {self.alert_mode}")
        return True
    
    def _check_threshold_crossing(self, alert_type, current_value, threshold):
        """
        Chegara qiymatidan oshganligini tekshirish
        
        Args:
            alert_type (str): Alert turi
            current_value (float): Joriy qiymat
            threshold (float): Chegara qiymati
            
        Returns:
            bool: Chegara qiymatidan oshganligi
        """
        # Alert turini standartlashtirish
        alert_key = self._standardize_alert_key(alert_type)
        
        # Joriy vaqt
        current_time = time.time()
        
        # So'nggi alert vaqtini olish
        last_alert_time = self.last_alert_times.get(alert_key, 0)
        
        # Alert yuborish rejimini tekshirish
        if self.alert_mode == 'continuous':
            # Chegara qiymatidan oshgan bo'lsa, alert yuboriladi
            return current_value >= threshold
        
        elif self.alert_mode == 'threshold_cross':
            # Agar so'nggi alert vaqti 0 bo'lsa, chegara qiymatidan oshgan bo'lsa alert yuboriladi
            if last_alert_time == 0:
                return current_value >= threshold
            
            # Alert intervali
            alert_interval = self.alert_interval
            
            # Metrika turiga qarab interval
            if hasattr(self.config, 'get') and callable(self.config.get):
                metric_interval_key = f"{alert_key}_alert_interval"
                if self.config.get(metric_interval_key):
                    alert_interval = self.config.get(metric_interval_key)
            
            # Vaqt farqi
            time_diff = current_time - last_alert_time
            
            # Alert intervalidan kam bo'lsa, alert yuborilmaydi
            if time_diff < alert_interval:
                return False
            
            # Chegara qiymatidan oshgan bo'lsa, alert yuboriladi
            return current_value >= threshold
        
        # Noma'lum rejim
        self.logger.warning(f"Noma'lum alert rejimi: {self.alert_mode}")
        return current_value >= threshold
    
    def _send_telegram_message(self, message, parse_mode='HTML'):
        """
        Telegram xabarini yuborish
        
        Args:
            message (str): Xabar matni
            parse_mode (str, optional): Xabar formati (HTML yoki Markdown)
            
        Returns:
            bool: Xabar yuborilganligi
        """
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram bot token yoki chat ID ko'rsatilmagan")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(url, data=data, timeout=10)
                
                if response.status_code == 200:
                    return True
                else:
                    self.logger.warning(f"Telegramga xabar yuborishda xatolik (urinish {attempt}/{max_retries}): {response.reason}")
                    
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= 2
            except Exception as e:
                self.logger.warning(f"Telegramga xabar yuborishda xatolik (urinish {attempt}/{max_retries}): {str(e)}")
                
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    retry_delay *= 2
        
        self.logger.error(f"Telegramga xabar yuborib bo'lmadi ({max_retries} urinishdan so'ng)")
        self.logger.error(f"BOT_TOKEN: {self.bot_token[:3]}...")
        self.logger.error(f"CHAT_ID: {self.chat_id}")
        
        return False
    
    def format_and_send_metric_alert(self, metric_type, usage_value, database=None, system_info=None, current_value=None, threshold=None):
        """
        Metrika uchun alohida xabar formatlab yuborish
        
        Args:
            metric_type (str): Metrika turi (RAM, CPU, Disk, va h.k.)
            usage_value (str): Metrika qiymati
            database (Database, optional): Ma'lumotlar bazasi obyekti
            system_info (dict, optional): Tizim ma'lumotlari
            current_value (float, optional): Joriy qiymat
            threshold (float, optional): Chegara qiymati
            
        Returns:
            bool: Xabar yuborilganligi
        """
        # Metrika turiga qarab alohida xabar yuborishni tekshirish
        metric_key = self._standardize_alert_key(metric_type)
        separate_alert_key = f"{metric_key}_separate_alert"
        
        if not self.config.get(separate_alert_key, True):
            self.logger.debug(f"{metric_type} uchun alohida xabar yuborish o'chirilgan")
            return False
        
        # Chegara qiymatidan oshganligini tekshirish
        if current_value is not None and threshold is not None:
            if not self._check_threshold_crossing(metric_type, current_value, threshold):
                self.logger.debug(f"{metric_type} alert yuborilmadi (threshold qiymatidan oshmagan)")
                return False
        
        # Alert yuborish intervalini tekshirish
        if not self.check_alert_interval(metric_type):
            return False
        
        # Metrika turiga qarab xabar formatini tanlash
        alert_format_key = f"{metric_key}_alert_format"
        alert_format = self.config.get(alert_format_key, 'HTML')
        
        # Metrika turiga qarab xabar sarlavhasini tanlash
        alert_title_key = f"{metric_key}_alert_title"
        alert_title = self.config.get(alert_title_key, f"🚨 {metric_type} ALERT")
        
        # Xabarni formatlash
        message = self.formatter.format_metric_alert(metric_type, usage_value, alert_format, alert_title, system_info)
        
        if not message:
            self.logger.error(f"{metric_type} xabarini formatlashda xatolik")
            return False
        
        # Xabarni logga yozish
        self.logger.debug(f"Telegramga yuboriladigan xabar: {message}")
        self.logger.info(f"----------------------------------------")
        self.logger.info(message)
        
        # Xabarni yuborish
        self.logger.debug(f"Telegramga xabar yuborilmoqda: {metric_type}")
        
        if self._send_telegram_message(message, 'HTML' if alert_format.upper() == 'HTML' else 'Markdown'):
            self.logger.info(f"{metric_type} alert xabari Telegramga muvaffaqiyatli yuborildi")
            
            # Ma'lumotlar bazasiga saqlash
            if database and hasattr(database, 'store_alert'):
                try:
                    database.store_alert(metric_type, usage_value, message)
                except Exception as e:
                    self.logger.error(f"Ma'lumotlar bazasiga saqlashda xatolik: {str(e)}")
            
            return True
        else:
            self.logger.error(f"{metric_type} alert xabarini yuborishda xatolik")
            return False
    
    def send_telegram_alert(self, alert_type=None, usage_value=None, database=None, system_info=None, current_value=None, threshold=None):
        """
        Telegram xabarini yuborish (eski usul, backward compatibility uchun)
        
        Args:
            alert_type (str, optional): Alert turi (masalan, 'RAM', 'CPU')
            usage_value (str, optional): Alert qiymati (masalan, '85%')
            database (Database, optional): Ma'lumotlar bazasi obyekti
            system_info (dict, optional): Tizim ma'lumotlari
            current_value (float, optional): Joriy qiymat
            threshold (float, optional): Chegara qiymati
            
        Returns:
            bool: Xabar yuborilganligi
        """
        # Umumiy xabar yuborishni tekshirish
        if not self.config.get('send_general_alert', True):
            self.logger.debug("Umumiy xabar yuborish o'chirilgan")
            return False
        
        # Chegara qiymatidan oshganligini tekshirish
        if alert_type and current_value is not None and threshold is not None:
            if not self._check_threshold_crossing(alert_type, current_value, threshold):
                self.logger.debug(f"{alert_type} alert yuborilmadi (threshold qiymatidan oshmagan)")
                return False
        
        # Alert yuborish intervalini tekshirish
        if alert_type and not self.check_alert_interval(alert_type):
            return False
        
        # Xabarni formatlash
        message = self.formatter.format_alert_message(alert_type, usage_value)
        
        if not message:
            self.logger.error("Xabarni formatlashda xatolik")
            return False
        
        # Xabarni logga yozish
        self.logger.debug(f"Telegramga yuboriladigan xabar: {message}")
        self.logger.info(f"----------------------------------------")
        self.logger.info(message)
        
        # Xabarni yuborish
        self.logger.debug(f"Telegramga xabar yuborilmoqda: {alert_type if alert_type else 'SYSTEM STATUS'}")
        
        if self._send_telegram_message(message, 'HTML'):
            self.logger.info(f"{alert_type if alert_type else 'SYSTEM STATUS'} alert xabari Telegramga muvaffaqiyatli yuborildi")
            
            # Alert turini standartlashtirish
            if alert_type:
                alert_key = self._standardize_alert_key(alert_type)
                
                # Alert vaqtini yangilash
                self.last_alert_times[alert_key] = time.time()
            
            # Ma'lumotlar bazasiga saqlash
            if database and hasattr(database, 'store_alert'):
                try:
                    database.store_alert(alert_type, usage_value, message)
                except Exception as e:
                    self.logger.error(f"Ma'lumotlar bazasiga saqlashda xatolik: {str(e)}")
            
            return True
        else:
            self.logger.error(f"{alert_type if alert_type else 'SYSTEM STATUS'} alert xabarini yuborishda xatolik")
            return False
    
    def update_prometheus_metrics(self, metrics):
        """
        Prometheus metrikalarini yangilash
        
        Args:
            metrics (dict): Metrikalar lug'ati
        """
        if not self.config.get('prometheus_enabled', False):
            return
        
        # Metrikalarni saqlash
        for metric_type, value in metrics.items():
            # Metrika turini standartlashtirish
            metric_key = self._standardize_alert_key(metric_type)
            
            # Metrikani saqlash
            self.prometheus_metrics[metric_key] = value
        
        # Network metrikalarini alohida saqlash
        if 'network' in metrics and isinstance(metrics['network'], list) and len(metrics['network']) >= 2:
            self.prometheus_metrics['network_rx'] = metrics['network'][0]
            self.prometheus_metrics['network_tx'] = metrics['network'][1]
