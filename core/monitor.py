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

    # def check_cpu_usage(self):
    #     """
    #     CPU foydalanish foizini tekshirish - bloklashsiz usul
        
    #     Returns:
    #         float: CPU foydalanish foizi
    #     """
    #     if not self.config.get('monitor_cpu', False):
    #         return 0
    #     try:
    #         # Agar top CPU jarayonlar umumiy foizini ko'rsatish kerak bo'lsa
    #         if self.config.get('show_top_processes_cpu_sum', True):
    #             return self._top_cpu_processes_total
                
    #         # Aks holda, tizim umumiy CPU foizini ko'rsatish
    #         # Bloklashsiz usul - interval=None bilan chaqiriladi
    #         current_time = time.time()
            
    #         # Birinchi marta chaqirilganda, boshlang'ich qiymatni o'rnatish
    #         if self._last_cpu_measure_time is None:
    #             # Birinchi o'lchov - faqat boshlang'ich qiymatni o'rnatish
    #             self._last_cpu_measure_time = current_time
    #             # interval=None bilan chaqirilganda, faqat o'lchov boshlaydi, qiymat qaytarmaydi
    #             psutil.cpu_percent(interval=None)
    #             return 0
            
    #         # Ikkinchi va keyingi o'lchovlar
    #         # Oldingi o'lchovdan beri o'tgan vaqtni tekshirish
    #         time_diff = current_time - self._last_cpu_measure_time
            
    #         # Agar kamida 0.5 soniya o'tgan bo'lsa, yangi o'lchov olish
    #         if time_diff >= 0.5:
    #             # interval=None bilan chaqirilganda, oldingi chaqiruvdan beri o'tgan vaqt uchun CPU foizini qaytaradi
    #             cpu_percent = psutil.cpu_percent(interval=None)
    #             self._last_cpu_measure_time = current_time
    #             self._last_cpu_percent = cpu_percent
    #             self.logger.debug(f"CPU Usage: {cpu_percent}% (yangilandi)")
    #             return cpu_percent
    #         else:
    #             # Agar kamida 0.5 soniya o'tmagan bo'lsa, oxirgi o'lchov natijasini qaytarish
    #             self.logger.debug(f"CPU Usage: {self._last_cpu_percent}% (keshdan)")
    #             return self._last_cpu_percent
                
    #     except Exception as e:
    #         self.logger.error(f"CPU foydalanishini tekshirishda xatolik: {e}")
    #         return 0
   
    def check_cpu_usage(self):
        """
        CPU foydalanish foizini tekshirish - Linux komandasi asosida (bloklashsiz)
        
        Returns:
            float: CPU foydalanish foizi
        """
        if not self.config.get('monitor_cpu', False):
            return 0
        try:
            current_time = time.time()

            if self._last_cpu_measure_time is None:
                self._last_cpu_measure_time = current_time
                return 0

            time_diff = current_time - self._last_cpu_measure_time

            if time_diff >= 0.5:
                # Linuxning top komandasi yordamida CPU yuklanishini olish
                result = subprocess.run(['top', '-bn1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                output = result.stdout

                # 'Cpu(s):' satridan %id (idle) ni ajratib olish
                cpu_line = next((line for line in output.splitlines() if "Cpu(s):" in line), None)
                if cpu_line:
                    # Regex orqali idle qiymatini olish
                    match = re.search(r'(\d+\.\d+)\s*id', cpu_line)
                    if match:
                        idle = float(match.group(1))
                        cpu_usage = int(round(100.0 - idle))
                        cpu_count = os.cpu_count()
                        self._last_cpu_measure_time = current_time
                        self._last_cpu_percent = cpu_usage
                        self.logger.debug(f"🔥 CPU Usage: {cpu_usage:.2f}% of {cpu_count} cores")
                        # self.logger.debug(f"CPU Usage (from top): {cpu_usage:.2f}%")
                        
                        return cpu_usage

                # Agar top natijasini o'qib bo'lmasa
                self.logger.warning("top chiqishini tahlil qilib bo'lmadi")
                return self._last_cpu_percent or 0
            else:
                return self._last_cpu_percent or 0

        except Exception as e:
            self.logger.error(f"CPU foydalanishini olishda xatolik (top orqali): {e}")
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
        Tarmoq foydalanishini tekshirish (Mbps)
        
        Returns:
            list: [rx_rate, tx_rate]
        """
        if not self.config.get('monitor_network', False):
            return [0, 0]
        interface = self.config.get('network_interface', 'eth0')
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

    # def get_top_processes(self, resource_type):
    #     """
    #     Eng ko'p resurs ishlatuvchi jarayonlarni olish
        
    #     Args:
    #         resource_type (str): Resurs turi ('RAM', 'CPU', 'Disk')
            
    #     Returns:
    #         str: Formatlangan jarayonlar ro'yxati
    #     """
    #     count = self.config.get('top_processes_count', 10)
    #     try:
    #         if resource_type == 'RAM':
    #             processes = []
    #             for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
    #                 try:
    #                     processes.append((proc.info['pid'], proc.info['name'], proc.info['memory_percent']))
    #                 except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #                     pass
                
    #             processes.sort(key=lambda x: x[2], reverse=True)
    #             result = [f"  - {name.ljust(15)} ({mem_percent:.1f}%)" for _, name, mem_percent in processes[:count]]
    #             return "\n".join(result)
                
    #         elif resource_type == 'CPU':
    #             # Yangilangan CPU jarayonlarini olish usuli
    #             current_time = time.time()
    #             processes = []
                
    #             # Barcha jarayonlarni o'qib olish
    #             for proc in psutil.process_iter(['pid', 'name']):
    #                 try:
    #                     pid = proc.info['pid']
    #                     name = proc.info['name']
                        
    #                     # Jarayon CPU vaqtini olish
    #                     proc_cpu_times = proc.cpu_times()
    #                     proc_create_time = proc.create_time()
                        
    #                     # Jarayon uchun CPU vaqti va tizim vaqtini saqlash
    #                     total_cpu_time = proc_cpu_times.user + proc_cpu_times.system
                        
    #                     # Agar jarayon avval ko'rilgan bo'lsa, CPU foizini hisoblash
    #                     if pid in self._process_cpu_times:
    #                         old_time, old_timestamp = self._process_cpu_times[pid]
                            
    #                         # Vaqt farqini hisoblash
    #                         time_delta = current_time - old_timestamp
                            
    #                         if time_delta > 0:
    #                             # CPU vaqti farqini hisoblash
    #                             cpu_delta = total_cpu_time - old_time
                                
    #                             # CPU foizini hisoblash (100% = 1 CPU core)
    #                             cpu_usage = (cpu_delta / time_delta) * 100
                                
    #                             # Natijani qo'shish
    #                             processes.append((pid, name, cpu_usage))
                        
    #                     # Joriy vaqtni yangilash
    #                     self._process_cpu_times[pid] = (total_cpu_time, current_time)
                        
    #                 except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #                     # Jarayon yo'qolgan yoki ruxsat yo'q
    #                     if pid in self._process_cpu_times:
    #                         del self._process_cpu_times[pid]
    #                     continue
                
    #             # Eski jarayonlarni tozalash (mavjud bo'lmagan jarayonlar)
    #             pids_to_remove = []
    #             for pid in self._process_cpu_times:
    #                 if not psutil.pid_exists(pid):
    #                     pids_to_remove.append(pid)
                
    #             for pid in pids_to_remove:
    #                 del self._process_cpu_times[pid]
                
    #             # Natijalarni tartiblash
    #             processes.sort(key=lambda x: x[2], reverse=True)
                
    #             # Agar hech qanday jarayon bo'lmasa yoki hisoblangan CPU foizlari bo'lmasa
    #             if not processes:
    #                 # Oddiy usul bilan olish
    #                 self.logger.debug("CPU jarayonlari hisoblash uchun ma'lumot yetarli emas, oddiy usul ishlatilmoqda")
                    
    #                 # ps buyrug'i orqali olish
    #                 try:
    #                     output = subprocess.check_output("ps -eo pid,comm,%cpu --sort=-%cpu | head -n " + str(count+1), shell=True).decode()
    #                     lines = output.strip().split('\n')[1:]  # Sarlavhani o'tkazib yuborish
                        
    #                     # Umumiy CPU foizini hisoblash
    #                     total_cpu = 0
    #                     result = []
    #                     for line in lines:
    #                         parts = line.strip().split()
    #                         if len(parts) >= 3:
    #                             pid = parts[0]
    #                             name = parts[1]
    #                             cpu_percent = float(parts[2])
    #                             total_cpu += cpu_percent
    #                             result.append(f"  - {name.ljust(15)} ({cpu_percent:.1f}%)")
                        
    #                     # Umumiy CPU foizini saqlash
    #                     self._top_cpu_processes_total = total_cpu
    #                     self.logger.debug(f"Top {count} jarayonlar umumiy CPU foizi: {total_cpu:.1f}%")
                        
    #                     # Agar qo'shimcha ma'lumot ko'rsatish kerak bo'lsa
    #                     if self.config.get('show_total_cpu_usage_in_list', True):
    #                         result.append(f"\nUmumiy CPU usage (TOP {count}): {total_cpu:.1f}%")
                        
    #                     return "\n".join(result)
    #                 except Exception as e:
    #                     self.logger.error(f"ps buyrug'i orqali CPU jarayonlarini olishda xatolik: {e}")
    #                     return "CPU jarayon ma'lumotlarini olish imkonsiz"
                
    #             # Umumiy CPU foizini hisoblash
    #             total_cpu = sum(cpu_percent for _, _, cpu_percent in processes[:count])
    #             self._top_cpu_processes_total = total_cpu
    #             self.logger.debug(f"Top {count} jarayonlar umumiy CPU foizi: {total_cpu:.1f}%")
                
    #             # Formatlangan natijani qaytarish
    #             result = [f"  - {name.ljust(15)} ({cpu_percent:.1f}%)" for _, name, cpu_percent in processes[:count]]
                
    #             # Agar qo'shimcha ma'lumot ko'rsatish kerak bo'lsa
    #             if self.config.get('show_total_cpu_usage_in_list', True):
    #                 result.append(f"\nUmumiy CPU usage (TOP {count}): {total_cpu:.1f}%")
                
    #             return "\n".join(result)
                
    #         elif resource_type == 'Disk':
    #             try:
    #                 output = subprocess.check_output(f"du -h {self.config['disk_path']}/* 2>/dev/null | sort -rh | head -n {count}", shell=True).decode()
    #                 lines = output.strip().split('\n')
    #                 result = []
    #                 for line in lines:
    #                     if line:
    #                         parts = line.split('\t')
    #                         if len(parts) == 2:
    #                             size, path = parts
    #                             path = os.path.basename(path)
    #                             result.append(f"  - /{path.ljust(15)} {size}")
    #                 return "\n".join(result)
    #             except:
    #                 return "Disk foydalanish ma'lumotlarini olish imkonsiz"
                
    #         else:
    #             return f"Noma'lum resurs turi: {resource_type}"
                
    #     except Exception as e:
    #         self.logger.error(f"Top jarayonlarni olishda xatolik: {e}")
    #         return f"{resource_type} jarayon ma'lumotlarini olish imkonsiz"

    def get_top_processes(self, metric="CPU"):
        try:
            if metric.upper() == "RAM":
                process_list_command = (
                    "ps -eo comm,%mem --sort=-%mem | "
                    "awk 'NR==1 {next} NR<=11 {printf \"│   - %-20s (%s%%)\\n\", $1, $2}'"
                )
                total_command = (
                    "ps -eo %mem --sort=-%mem | awk 'NR==1 {next} NR<=11 {sum+=$1} END {printf \"Umumiy RAM: %.1f%%\\n\", sum}'"
                )
            else:
                process_list_command = (
                    "ps -eo comm,%cpu --sort=-%cpu | "
                    "awk 'NR==1 {next} NR<=11 {printf \"│   - %-20s (%s%%)\\n\", $1, $2}'"
                )
                total_command = (
                    "ps -eo %cpu --sort=-%cpu | awk 'NR==1 {next} NR<=11 {sum+=$1} END {printf \"Umumiy CPU: %.1f%%\\n\", sum}'"
                )

            process_output = subprocess.check_output(process_list_command, shell=True, text=True)
            total_output = subprocess.check_output(total_command, shell=True, text=True)
            return process_output + total_output

        except subprocess.CalledProcessError as e:
            return f"Xatolik yuz berdi: {e}"


    def get_disk_breakdown(self):
        """
        Disk bo'linmalari bo'yicha foydalanish ma'lumotlarini olish
        
        Returns:
            dict: Yo'l va hajm juftliklari
        """
        breakdown = {}
        paths = ['/usr', '/lib', '/snap']
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
