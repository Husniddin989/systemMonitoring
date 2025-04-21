#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tizim resurslarini monitoring qilish moduli
RAM, CPU, Disk, Swap, Load va Network resurslarini tekshiradi
"""

import psutil
import socket
import platform
import subprocess
import time
import os

class SystemMonitor:
    def __init__(self, config, logger):
        """
        Tizim monitoringini ishga tushirish
        
        Args:
            config (dict): Konfiguratsiya sozlamalari
            logger (logging.Logger): Log yozish uchun logger obyekti
        """
        self.config = config
        self.logger = logger

    def get_system_info(self):
        """
        Tizim haqida umumiy ma'lumotlarni olish
        
        Returns:
            dict: Tizim ma'lumotlari (hostname, ip, os, kernel, cpu, uptime, ram, disk)
        """
        hostname = socket.gethostname()
        server_ip = '127.0.0.1'
        
        # IP manzilni aniqlash
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            server_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        kernel = platform.release()
        os_info = f"{platform.system()} {platform.release()}"
        
        try:
            os_info = subprocess.check_output("cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"'", shell=True).decode().strip()
        except:
            pass
        
        # Ishlash vaqtini hisoblash
        uptime_seconds = 0
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
        except:
            uptime_seconds = time.time() - psutil.boot_time()
        
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        if uptime_days > 0:
            uptime = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
        elif uptime_hours > 0:
            uptime = f"{uptime_hours}h {uptime_minutes}m"
        else:
            uptime = f"{uptime_minutes}m"
        
        # CPU ma'lumotlari
        cpu_info = "Unknown CPU"
        cpu_cores = psutil.cpu_count(logical=True)
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        cpu_info = line.split(':', 1)[1].strip()
                        break
        except:
            pass
        
        # Xotira ma'lumotlari
        total_memory = psutil.virtual_memory().total
        total_memory_gb = total_memory / (1024 ** 3)
        
        # Disk ma'lumotlari
        total_disk = 0
        try:
            disk_usage = psutil.disk_usage(self.config['disk_path'])
            total_disk = disk_usage.total
        except:
            pass
        
        total_disk_gb = total_disk / (1024 ** 3)
        
        return {
            'hostname': hostname,
            'ip': server_ip,
            'os': os_info,
            'kernel': kernel,
            'cpu': f"{cpu_info} ({cpu_cores} cores)",
            'uptime': uptime,
            'total_ram': f"{total_memory_gb:.1f}Gi",
            'total_disk': f"{total_disk_gb:.1f}G"
        }

    def check_ram_usage(self):
        """
        RAM foydalanish foizini tekshirish
        
        Returns:
            float: RAM foydalanish foizi
        """
        mem = psutil.virtual_memory()
        return mem.percent

    def check_cpu_usage(self):
        """
        CPU foydalanish foizini tekshirish
        
        Returns:
            float: CPU foydalanish foizi
        """
        if not self.config['monitor_cpu']:
            return 0
        return psutil.cpu_percent(interval=1)

    def check_disk_usage(self):
        """
        Disk foydalanish foizini tekshirish
        
        Returns:
            float: Disk foydalanish foizi
        """
        if not self.config['monitor_disk']:
            return 0
        try:
            disk_usage = psutil.disk_usage(self.config['disk_path'])
            return disk_usage.percent
        except Exception as e:
            self.logger.error(f"Disk foydalanishini tekshirishda xatolik: {e}")
            return 0

    def check_swap_usage(self):
        """
        Swap xotira foydalanish foizini tekshirish
        
        Returns:
            float: Swap foydalanish foizi
        """
        if not self.config['monitor_swap']:
            return 0
        try:
            swap = psutil.swap_memory()
            if swap.total == 0:
                return 0
            return swap.percent
        except Exception as e:
            self.logger.error(f"Swap foydalanishini tekshirishda xatolik: {e}")
            return 0

    def check_load_average(self):
        """
        Tizim yuklanishini tekshirish (core boshiga)
        
        Returns:
            float: Yuklanish foizi
        """
        if not self.config['monitor_load']:
            return 0
        try:
            load_avg = psutil.getloadavg()[0]
            cpu_cores = psutil.cpu_count(logical=True)
            load_per_core = load_avg / cpu_cores
            return load_per_core * 100
        except Exception as e:
            self.logger.error(f"Yuklanishni tekshirishda xatolik: {e}")
            return 0

    def check_network_usage(self):
        """
        Tarmoq foydalanishini tekshirish (Mbps)
        
        Returns:
            list: [rx_rate, tx_rate]
        """
        if not self.config['monitor_network']:
            return [0, 0]
        interface = self.config['network_interface']
        try:
            net_io_counters = psutil.net_io_counters(pernic=True)
            if interface not in net_io_counters:
                self.logger.error(f"Tarmoq interfeysi topilmadi: {interface}")
                return [0, 0]
            
            rx_bytes_1 = net_io_counters[interface].bytes_recv
            tx_bytes_1 = net_io_counters[interface].bytes_sent
            
            time.sleep(1)
            
            net_io_counters = psutil.net_io_counters(pernic=True)
            rx_bytes_2 = net_io_counters[interface].bytes_recv
            tx_bytes_2 = net_io_counters[interface].bytes_sent
            
            rx_rate = ((rx_bytes_2 - rx_bytes_1) * 8) / 1024 / 1024
            tx_rate = ((tx_bytes_2 - tx_bytes_1) * 8) / 1024 / 1024
            
            return [rx_rate, tx_rate]
        except Exception as e:
            self.logger.error(f"Tarmoq foydalanishini tekshirishda xatolik: {e}")
            return [0, 0]

    def get_top_processes(self):
        """
        Eng ko‘p resurs ishlatuvchi jarayonlarni olish
        
        Args:
            resource_type (str): Resurs turi ('RAM', 'CPU', 'Disk')
            
        Returns:
            str: Formatlangan jarayonlar ro‘yxati
        """
        count = self.config['top_processes_count']
        try:
            if resource_type == 'RAM':
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    try:
                        processes.append((proc.info['pid'], proc.info['name'], proc.info['memory_percent']))
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                processes.sort(key=lambda x: x[2], reverse=True)
                result = [f"  - {name.ljust(15)} ({mem_percent:.1f}%)" for _, name, mem_percent in processes[:count]]
                return "\n".join(result)
                
            elif resource_type == 'CPU':
                processes = []
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        # CPU foizini 1 soniya oralig‘ida hisoblash
                        cpu_percent = proc.cpu_percent(interval=1)
                        if cpu_percent > 0:  # Faqat faol jarayonlarni qo‘shish
                            processes.append((proc.info['pid'], proc.info['name'], cpu_percent))
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                processes.sort(key=lambda x: x[2], reverse=True)
                result = [f"  - {name.ljust(15)} ({cpu_percent:.1f}%)" for _, name, cpu_percent in processes[:count]]
                return "\n".join(result)
                
            elif resource_type == 'Disk':
                try:
                    output = subprocess.check_output(f"du -h {self.config['disk_path']}/* 2>/dev/null | sort -rh | head -n {count}", shell=True).decode()
                    lines = output.strip().split('\n')
                    result = []
                    for line in lines:
                        if line:
                            parts = line.split('\t')
                            if len(parts) == 2:
                                size, path = parts
                                path = os.path.basename(path)
                                result.append(f"  - /{path.ljust(15)} {size}")
                    return "\n".join(result)
                except:
                    return "Disk foydalanish ma'lumotlarini olish imkonsiz"
                
            else:
                return f"Noma'lum resurs turi: {resource_type}"
                
        except Exception as e:
            self.logger.error(f"Top jarayonlarni olishda xatolik: {e}")
            return f"{resource_type} jarayon ma'lumotlarini olish imkonsiz"

    def get_disk_breakdown(self):
        """
        Disk bo‘linmalari bo‘yicha foydalanish ma'lumotlarini olish
        
        Returns:
            dict: Yo‘l va hajm juftliklari (masalan, {'/usr': '2.1G', '/lib': '1.3G'})
        """
        breakdown = {}
        paths = ['/usr', '/lib', '/snap']  # Tekshiriladigan direktoriyalar
        try:
            for path in paths:
                if os.path.exists(path):
                    usage = psutil.disk_usage(path)
                    size_gb = usage.used / (1024 ** 3)  # Baytlarni GiB ga aylantirish
                    breakdown[path] = f"{size_gb:.1f}G"
            self.logger.debug(f"Disk bo‘linmalari: {breakdown}")
        except Exception as e:
            self.logger.error(f"Disk bo‘linmalarini olishda xatolik: {e}")
        return breakdown