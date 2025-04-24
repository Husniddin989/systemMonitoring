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
import re

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
        # CPU o'lchovi uchun o'zgaruvchilar
        self._last_cpu_measure_time = None
        self._last_cpu_percent = 0
        # Jarayonlar CPU foizini kuzatish uchun lug'at
        self._process_cpu_times = {}
        
        # Top CPU jarayonlar umumiy foizi
        self._top_cpu_processes_total = 0
        
        # Network o'lchovi uchun o'zgaruvchilar
        self._last_network_measure_time = None
        self._last_network_bytes_recv = 0
        self._last_network_bytes_sent = 0
        self._last_network_rates = [0, 0]  # [rx_rate, tx_rate]

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
            'total_disk': f"{total_disk_gb:.1f}G",
            'total_cpu': f"{cpu_cores} cores"
        }

    # def check_ram_usage(self):
    #     """
    #     RAM foydalanish foizini tekshirish
        
    #     Returns:
    #         float: RAM foydalanish foizi
    #     """
    #     mem = psutil.virtual_memory()
    #     return mem.percent
    def check_ram_usage(self):
        try:
            mem = psutil.virtual_memory()
            self.logger.debug(f"RAM Usage: {mem.percent}% (Total: {mem.total / (1024 ** 3):.1f}Gi, Used: {mem.used / (1024 ** 3):.1f}Gi)")
            return mem.percent
        except Exception as e:
            self.logger.error(f"RAM foydalanishini tekshirishda xatolik: {e}")
            return 0
    # def check_cpu_usage(self):
    #     """
    #     CPU foydalanish foizini tekshirish - Linux komandasi asosida (bloklashsiz)
        
    #     Returns:
    #         float: CPU foydalanish foizi
    #     """
    #     if not self.config.get('monitor_cpu', False):
    #         return 0
    #     try:
    #         # Agar top CPU jarayonlar umumiy foizini ko'rsatish kerak bo'lsa
    #         if self.config.get('show_top_processes_cpu_sum', True):
    #             return self._top_cpu_processes_total
                
    #         current_time = time.time()

    #         if self._last_cpu_measure_time is None:
    #             self._last_cpu_measure_time = current_time
    #             return 0

    #         time_diff = current_time - self._last_cpu_measure_time

    #         if time_diff >= 0.5:
    #             # Linuxning top komandasi yordamida CPU yuklanishini olish
    #             result = subprocess.run(['top', '-bn1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #             output = result.stdout

    #             # 'Cpu(s):' satridan %id (idle) ni ajratib olish
    #             cpu_line = next((line for line in output.splitlines() if "Cpu(s):" in line), None)
    #             if cpu_line:
    #                 # Regex orqali idle qiymatini olish
    #                 match = re.search(r'(\d+\.\d+)\s*id', cpu_line)
    #                 if match:
    #                     idle = float(match.group(1))
    #                     cpu_usage = int(round(100.0 - idle))
    #                     cpu_count = os.cpu_count()  # CPU yadrolari soni
    #                     self._last_cpu_measure_time = current_time
    #                     self._last_cpu_percent = cpu_usage
    #                     self.logger.debug(f"🔥 CPU Usage: {cpu_usage:.2f}% of {cpu_count} cores")
                        
    #                     return cpu_usage

    #             # Agar top natijasini o'qib bo'lmasa
    #             self.logger.warning("top chiqishini tahlil qilib bo'lmadi")
    #             return self._last_cpu_percent or 0
    #         else:
    #             return self._last_cpu_percent or 0

    #     except Exception as e:
    #         self.logger.error(f"CPU foydalanishini olishda xatolik (top orqali): {e}")
    #         return 0
    def check_cpu_usage(self):
        if not self.config.get('monitor_cpu', False):
            return 0
        try:
            cpu_usage = psutil.cpu_percent(interval=0.5)
            self.logger.debug(f"🔥 CPU Usage: {cpu_usage:.2f}% of {os.cpu_count()} cores")
            return cpu_usage
        except Exception as e:
            self.logger.error(f"CPU foydalanishini olishda xatolik: {e}")
            return 0
        
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
    
    def check_swap_usage(self):
        """
        Swap xotira foydalanish foizini tekshirish
        
        Returns:
            float: Swap foydalanish foizi
        """
        if not self.config.get('monitor_swap', False):
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
        if not self.config.get('monitor_load', False):
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
        Tarmoq foydalanishini tekshirish (Mbps) - bloklashsiz usulda
        
        Returns:
            list: [rx_rate, tx_rate]
        """
        if not self.config.get('monitor_network', False):
            return [0, 0]
            
        interface = self.config.get('network_interface', 'eth0')
        try:
            current_time = time.time()
            
            # Mavjud tarmoq interfeyslari ro'yxatini olish
            net_io_counters = psutil.net_io_counters(pernic=True)
            
            # Agar interfeys topilmasa, avtomatik aniqlash
            if interface not in net_io_counters:
                # Mavjud interfeyslarda birinchi faol bo'lganini tanlash
                for iface, counters in net_io_counters.items():
                    if iface != 'lo' and counters.bytes_recv > 0:
                        interface = iface
                        self.logger.info(f"Tarmoq interfeysi avtomatik aniqlandi: {interface}")
                        self.config['network_interface'] = interface
                        break
                        
                # Agar hali ham interfeys topilmasa
                if interface not in net_io_counters:
                    self.logger.error(f"Tarmoq interfeysi topilmadi: {interface}")
                    return [0, 0]
            
            # Joriy o'lchovlarni olish
            current_bytes_recv = net_io_counters[interface].bytes_recv
            current_bytes_sent = net_io_counters[interface].bytes_sent
            
            # Agar bu birinchi o'lchov bo'lsa
            if self._last_network_measure_time is None:
                self._last_network_measure_time = current_time
                self._last_network_bytes_recv = current_bytes_recv
                self._last_network_bytes_sent = current_bytes_sent
                return [0, 0]
            
            # Vaqt farqini hisoblash
            time_diff = current_time - self._last_network_measure_time
            
            # Agar yetarlicha vaqt o'tgan bo'lsa, yangi o'lchovni olish
            if time_diff >= 1.0:  # Kamida 1 soniya o'tgan bo'lishi kerak
                # Bayt farqini hisoblash
                bytes_recv_diff = current_bytes_recv - self._last_network_bytes_recv
                bytes_sent_diff = current_bytes_sent - self._last_network_bytes_sent
                
                # Mbps ga aylantirish
                rx_rate = (bytes_recv_diff * 8) / time_diff / 1024 / 1024
                tx_rate = (bytes_sent_diff * 8) / time_diff / 1024 / 1024
                
                # Yangi qiymatlarni saqlash
                self._last_network_measure_time = current_time
                self._last_network_bytes_recv = current_bytes_recv
                self._last_network_bytes_sent = current_bytes_sent
                self._last_network_rates = [rx_rate, tx_rate]
                
                self.logger.debug(f"🌐 Network: RX {rx_rate:.1f} Mbps, TX {tx_rate:.1f} Mbps (yangilandi)")
                return [rx_rate, tx_rate]
            else:
                # Agar yetarlicha vaqt o'tmagan bo'lsa, oxirgi o'lchovni qaytarish
                self.logger.debug(f"🌐 Network: RX {self._last_network_rates[0]:.1f} Mbps, TX {self._last_network_rates[1]:.1f} Mbps (keshdan)")
                return self._last_network_rates
                
        except Exception as e:
            self.logger.error(f"Tarmoq foydalanishini tekshirishda xatolik: {e}")
            return [0, 0]

    # def get_top_processes(self, metric="CPU"):
    #     """
    #     Eng ko'p resurs ishlatuvchi jarayonlarni olish
        
    #     Args:
    #         metric (str): Resurs turi ('RAM', 'CPU')
            
    #     Returns:
    #         str: Formatlangan jarayonlar ro'yxati
    #     """
    #     try:
    #         top_count = self.config.get('top_processes_count', 10)
    #         show_total = self.config.get('show_total_cpu_usage_in_list', True)
            
    #         if metric.upper() == "RAM":
    #             process_list_command = (
    #                 f"ps -eo comm,%mem --sort=-%mem | "
    #                 f"awk 'NR==1 {{next}} NR<={top_count+1} {{printf \"│   - %-20s (%s%%)\\n\", $1, $2}}'"
    #             )
    #             total_command = (
    #                 f"ps -eo %mem --sort=-%mem | awk 'NR==1 {{next}} NR<={top_count+1} {{sum+=$1}} END {{printf \"\\nUmumiy RAM: %.1f%%\\n\", sum}}'"
    #             )
    #         else:  # CPU
    #             process_list_command = (
    #                 f"ps -eo comm,%cpu --sort=-%cpu | "
    #                 f"awk 'NR==1 {{next}} NR<={top_count+1} {{printf \"│   - %-20s (%s%%)\\n\", $1, $2}}'"
    #             )
    #             total_command = (
    #                 f"ps -eo %cpu --sort=-%cpu | awk 'NR==1 {{next}} NR<={top_count+1} {{sum+=$1}} END {{printf \"\\nUmumiy CPU usage (TOP {top_count}): %.1f%%\\n\", sum}}'"
    #             )

    #         process_output = subprocess.check_output(process_list_command, shell=True, text=True)
            
    #         # Umumiy qiymatni hisoblash va saqlash
    #         total_output = subprocess.check_output(total_command, shell=True, text=True)
            
    #         # CPU uchun umumiy qiymatni saqlash
    #         if metric.upper() == "CPU":
    #             try:
    #                 # Umumiy CPU foizini ajratib olish
    #                 match = re.search(r'(\d+\.\d+)%', total_output)
    #                 if match:
    #                     self._top_cpu_processes_total = float(match.group(1))
    #                     self.logger.debug(f"Top {top_count} jarayonlar umumiy CPU foizi: {self._top_cpu_processes_total:.1f}%")
    #             except Exception as e:
    #                 self.logger.error(f"Umumiy CPU foizini ajratib olishda xatolik: {e}")
            
    #         # Agar umumiy qiymatni ko'rsatish kerak bo'lsa
    #         if show_total:
    #             return process_output + total_output
    #         else:
    #             return process_output

    #     except subprocess.CalledProcessError as e:
    #         self.logger.error(f"Top jarayonlarni olishda xatolik: {e}")
    #         return f"Xatolik yuz berdi: {e}"
    #     except Exception as e:
    #         self.logger.error(f"Top jarayonlarni olishda umumiy xatolik: {e}")
    #         return f"Umumiy xatolik: {e}"
    def get_top_processes(self, metric="CPU"):
        try:
            top_count = self.config.get('top_processes_count', 10)
            show_total = self.config.get('show_total_cpu_usage_in_list', True)
            
            if metric.upper() == "RAM":
                process_list_command = (
                    f"ps -eo comm,%mem --sort=-%mem | "
                    f"head -n {top_count + 1} | "
                    f"awk 'NR>1 {{printf \"│   - %-20s (%.1f%%)\\n\", $1, $2}}'"
                )
                total_command = (
                    f"ps -eo %mem --sort=-%mem | head -n {top_count + 1} | "
                    f"awk 'NR>1 {{sum+=$1}} END {{printf \"\\nUmumiy RAM: %.1f%%\\n\", sum}}'"
                )
            else:  # CPU
                process_list_command = (
                    f"ps -eo comm,%cpu --sort=-%cpu | "
                    f"head -n {top_count + 1} | "
                    f"awk 'NR>1 {{printf \"│   - %-20s (%.1f%%)\\n\", $1, $2}}'"
                )
                total_command = (
                    f"ps -eo %cpu --sort=-%cpu | head -n {top_count + 1} | "
                    f"awk 'NR>1 {{sum+=$1}} END {{printf \"\\nUmumiy CPU usage (TOP {top_count}): %.1f%%\\n\", sum}}'"
                )

            process_output = subprocess.check_output(process_list_command, shell=True, text=True)
            total_output = subprocess.check_output(total_command, shell=True, text=True)
            
            if metric.upper() == "CPU":
                match = re.search(r'(\d+\.\d+)%', total_output)
                if match:
                    self._top_cpu_processes_total = float(match.group(1))
                    self.logger.debug(f"Top {top_count} jarayonlar umumiy CPU foizi: {self._top_cpu_processes_total:.1f}%")
            
            return process_output + total_output if show_total else process_output
        except Exception as e:
            self.logger.error(f"Top jarayonlarni olishda xatolik: {e}")
            return f"Xatolik yuz berdi: {e}"
    def get_disk_breakdown(self):
        """
        Disk bo'linmalari bo'yicha foydalanish ma'lumotlarini olish
        
        Returns:
            dict: Yo'l va hajm juftliklari
        """
        if not self.config.get('monitor_disk', False):
            self.logger.debug("Disk monitoring o'chirilgan, bo'sh breakdown qaytarilmoqda")
            return {}
        
        breakdown = {}
        paths = ['/', '/var', '/root', '/home', '/tmp', '/mnt', '/media']
        try:
            for path in paths:
                if os.path.exists(path):
                    usage = psutil.disk_usage(path)
                    size_gb = usage.used / (1024 ** 3)
                    breakdown[path] = f"{size_gb:.1f}G"
            self.logger.debug(f"Disk bo'linmalari: {breakdown}")
        except Exception as e:
            self.logger.error(f"Disk bo'linmalarini olishda xatolik: {e}")
        return breakdown
