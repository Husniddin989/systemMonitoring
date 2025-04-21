#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tizim monitoring dasturining asosiy moduli
"""

import argparse
import time
from config.config_loader import ConfigLoader
from utils.logger import Logger
from utils.database import Database
from core.monitor import SystemMonitor
from core.formatter import AlertFormatter
from core.alerts import AlertManager

class MemoryMonitor:
    def __init__(self, config_file):
        """
        Monitoring dasturini ishga tushirish
        
        Args:
            config_file (str): Konfiguratsiya faylining yo‘li
        """
        # Logger ni ishga tushirish
        self.logger = Logger('/var/log/memory_monitor.log', 'INFO').get_logger()
        
        # Konfiguratsiyani yuklash
        self.config_loader = ConfigLoader(config_file, self.logger)
        self.config = self.config_loader.get_config()
        
        # Modullarni ishga tushirish
        self.monitor = SystemMonitor(self.config, self.logger)
        self.formatter = AlertFormatter(self.config, self.logger, self.monitor)
        self.alert_manager = AlertManager(self.config, self.logger, self.formatter, self.monitor)
        self.database = Database(self.config, self.logger)
        
        self.logger.info(f"Memory monitoring xizmati boshlandi")
        self.logger.info(f"Konfiguratsiya fayli: {config_file}")
        self.logger.debug(f"Monitoring sozlamalari: RAM {self.config['threshold']}%, interval {self.config['check_interval']} sek")

    def update_status_file(self, metrics):
        """
        Holat faylini yangilash
        
        Args:
            metrics (dict): Tizim metrikalari
        """
        status_file = '/tmp/memory-monitor-status.tmp'
        date_str = time.strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            status_content = f"So'nggi tekshirish: {date_str}\n"
            
            for key, value in metrics.items():
                if key == 'ram':
                    status_content += f"RAM: {value}%\n"
                elif key == 'cpu' and self.config['monitor_cpu']:
                    status_content += f"CPU: {value}%\n"
                elif key == 'disk' and self.config['monitor_disk']:
                    status_content += f"Disk ({self.config['disk_path']}): {value}%\n"
                elif key == 'swap' and self.config['monitor_swap'] and value > 0:
                    status_content += f"Swap: {value}%\n"
                elif key == 'load' and self.config['monitor_load']:
                    load_per_core = value / 100
                    load_1min = load_per_core * psutil.cpu_count(logical=True)
                    status_content += f"Load: {load_1min:.2f} (core boshiga: {load_per_core:.2f})\n"
                elif key == 'network' and self.config['monitor_network']:
                    rx_rate, tx_rate = value
                    status_content += f"Network ({self.config['network_interface']}): RX: {rx_rate:.2f} Mbps, TX: {tx_rate:.2f} Mbps\n"
            
            with open(status_file, 'w') as f:
                f.write(status_content)
                
        except Exception as e:
            self.logger.error(f"Holat faylini yangilashda xatolik: {e}")

    def run(self):
        """
        Monitoring jarayonini boshlash
        """
        self.logger.info(f"Monitoring boshlandi. Interval: {self.config['check_interval']} soniya")
        
        while True:
            try:
                # Metrikalarni yig‘ish
                metrics = {
                    'ram': self.monitor.check_ram_usage(),
                    'cpu': self.monitor.check_cpu_usage(),
                    'disk': self.monitor.check_disk_usage(),
                    'swap': self.monitor.check_swap_usage(),
                    'load': self.monitor.check_load_average(),
                    'network': self.monitor.check_network_usage()
                }
                
                system_info = self.monitor.get_system_info()
                
                # Ma'lumotlar bazasida saqlash
                if self.config['db_enabled']:
                    self.database.store_metrics(metrics, system_info)
                
                # Prometheus metrikalarini yangilash
                if self.config['prometheus_enabled']:
                    self.alert_manager.update_prometheus_metrics(metrics)
                
                # Holat faylini yangilash
                self.update_status_file(metrics)
                
                # Chegaralarni tekshirish va alert yuborish
                if metrics['ram'] >= self.config['threshold']:
                    self.logger.warning(f"Yuqori RAM ishlatilishi: {metrics['ram']}%")
                    self.alert_manager.send_telegram_alert('RAM', f"{metrics['ram']}%", self.database, system_info)
                
                if self.config['monitor_cpu'] and metrics['cpu'] >= self.config['cpu_threshold']:
                    self.logger.warning(f"Yuqori CPU ishlatilishi: {metrics['cpu']}%")
                    self.alert_manager.send_telegram_alert('CPU', f"{metrics['cpu']}%", self.database, system_info)
                
                if self.config['monitor_disk'] and metrics['disk'] >= self.config['disk_threshold']:
                    self.logger.warning(f"Yuqori disk ishlatilishi ({self.config['disk_path']}): {metrics['disk']}%")
                    self.alert_manager.send_telegram_alert('Disk', f"{metrics['disk']}%", self.database, system_info)
                
                if self.config['monitor_swap'] and metrics['swap'] >= self.config['swap_threshold'] and metrics['swap'] > 0:
                    self.logger.warning(f"Yuqori swap ishlatilishi: {metrics['swap']}%")
                    self.alert_manager.send_telegram_alert('Swap', f"{metrics['swap']}%", self.database, system_info)
                
                if self.config['monitor_load'] and metrics['load'] >= self.config['load_threshold']:
                    load_per_core = metrics['load'] / 100
                    load_1min = load_per_core * psutil.cpu_count(logical=True)
                    self.logger.warning(f"Yuqori load average: {load_1min:.2f} (core boshiga: {load_per_core:.2f})")
                    self.alert_manager.send_telegram_alert('Load', f"{load_1min:.2f} (core boshiga: {load_per_core:.2f})", self.database, system_info)
                
                if self.config['monitor_network']:
                    rx_rate, tx_rate = metrics['network']
                    if rx_rate >= self.config['network_threshold'] or tx_rate >= self.config['network_threshold']:
                        self.logger.warning(f"Yuqori tarmoq trafigi ({self.config['network_interface']}): RX: {rx_rate:.2f} Mbps, TX: {tx_rate:.2f} Mbps")
                        self.alert_manager.send_telegram_alert('Network', f"RX: {rx_rate:.2f} Mbps, TX: {tx_rate:.2f} Mbps", self.database, system_info)
                
            except Exception as e:
                self.logger.error(f"Monitoring jarayonida xatolik: {e}")
            
            time.sleep(self.config['check_interval'])

def main():
    """
    Dasturni ishga tushirish
    """
    parser = argparse.ArgumentParser(description='Tizim xotirasi, CPU va disk monitoringi')
    parser.add_argument('--config', default='/etc/memory-monitor/config.conf', help='Konfiguratsiya fayli yo‘li')
    parser.add_argument('--version', action='store_true', help='Versiya malumotini korsatish')
    
    args = parser.parse_args()
    
    if args.version:
        print("Tizim Monitor 1.2.0")
        sys.exit(0)
    
    monitor = MemoryMonitor(args.config)
    monitor.run()

if __name__ == "__main__":
    main()