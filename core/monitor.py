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

    def check_cpu_usage(self):
        """
        CPU foydalanish foizini tekshirish
        
        Returns:
            float: CPU foydalanish foizi
        """
        if not self.config.get('monitor_cpu', False):
            return 0
        try:
            # Bir nechta o‘lchovlar orqali aniqlikni oshirish
            cpu_percent = psutil.cpu_percent(interval=1)
            self.logger.debug(f"CPU Usage: {cpu_percent}%")
            return cpu_percent
        except Exception as e:
            self.logger.error(f"CPU foydalanishini tekshirishda xatolik: {e}")
            return 0

    def get_top_processes(self, resource_type):
        """
        Eng ko‘p resurs ishlatuvchi jarayonlarni olish
        
        Args:
            resource_type (str): Resurs turi ('RAM', 'CPU', 'Disk')
            
        Returns:
            str: Formatlangan jarayonlar ro‘yxati
        """
        count = self.config.get('top_processes_count', 10)
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
                # Jarayonlarni oldindan yig‘ish
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        # CPU foizini 1 soniya oralig‘ida hisoblash
                        proc.cpu_percent(interval=None)  # Birinchi chaqiruv
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                time.sleep(1)  # Sinxron o‘lchov uchun kutish
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        cpu_percent = proc.cpu_percent(interval=None)
                        if cpu_percent >= 0:  # Barcha jarayonlarni qo‘shish
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

    # Qo‘shimcha metodlar (oldingi versiyadan qolganlar saqlanadi)
    def check_ram_usage(self):
        """
        RAM foydalanish foizini tekshirish
        
        Returns:
            float: RAM foydalanish foizi
        """
        mem = psutil.virtual_memory()
        return mem.percent

    def check_disk_usage(self):
        """
        Disk foydalanish foizini tekshirish
        
        Returns:
            float: Disk foydalanish foizi
        """
        if not self.config.get('monitor_disk', False):
            return 0
        try:
            disk_usage = psutil.disk_usage(self.config['disk_path'])
            return disk_usage.percent
        except Exception as e:
            self.logger.error(f"Disk foydalanishini tekshirishda xatolik: {e}")
            return 0

    def get_disk_breakdown(self):
        """
        Disk bo‘linmalari bo‘yicha foydalanish ma'lumotlarini olish
        
        Returns:
            dict: Yo‘l va hajm juftliklari
        """
        breakdown = {}
        paths = ['/usr', '/lib', '/snap']
        try:
            for path in paths:
                if os.path.exists(path):
                    usage = psutil.disk_usage(path)
                    size_gb = usage.used / (1024 ** 3)
                    breakdown[path] = f"{size_gb:.1f}G"
            self.logger.debug(f"Disk bo‘linmalari: {breakdown}")
        except Exception as e:
            self.logger.error(f"Disk bo‘linmalarini olishda xatolik: {e}")
        return breakdown

    # Boshqa metodlar (get_system_info, check_swap_usage, check_load_average, check_network_usage) o‘zgarishsiz qoladi