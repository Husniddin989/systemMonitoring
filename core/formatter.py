#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alert xabarlarini formatlash moduli
"""

import datetime

class AlertFormatter:
    def __init__(self, config, logger, monitor):
        """
        Alert formatlovchini ishga tushirish
        
        Args:
            config (dict): Konfiguratsiya sozlamalari
            logger (logging.Logger): Log yozish uchun logger obyekti
            monitor (SystemMonitor): Tizim monitoring obyekti
        """
        self.config = config
        self.logger = logger
        self.monitor = monitor

    def format_alert_message(self, alert_type=None, usage_value=None):
        """
        Alert xabarini konfiguratsiyaga muvofiq formatlash
        
        Args:
            alert_type (str, optional): Alert turi (masalan, 'RAM', 'CPU')
            usage_value (str, optional): Alert qiymati (masalan, '85%')
            
        Returns:
            str: Formatlangan xabar
        """
        if not self.config.get('alert_format_enabled', False):
            self.logger.info("Oddiy matn formati ishlatilmoqda")
            return self._simple_format()

        self.logger.info("Chiroyli formatlash ishlatilmoqda")
        return self._formatted_alert()

    def _simple_format(self):
        """Oddiy matnli xabar formatlash"""
        try:
            date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            system_info = self.monitor.get_system_info()
            
            # Barcha metrikalarni olish
            ram_usage = self.monitor.check_ram_usage()
            cpu_usage = self.monitor.check_cpu_usage() if self.config.get('monitor_cpu', False) else 0
            disk_usage = self.monitor.check_disk_usage() if self.config.get('monitor_disk', False) else 0
            swap_usage = self.monitor.check_swap_usage() if self.config.get('monitor_swap', False) else 0
            load_average = self.monitor.check_load_average() if self.config.get('monitor_load', False) else 0
            network_usage = self.monitor.check_network_usage() if self.config.get('monitor_network', False) else [0, 0]

            message = f"{self.config.get('alert_message_title', '🖥️ SYSTEM STATUS ALERT')}\n\n"
            message += f"{self.config.get('alert_format_date_emoji', '🗓️')} Date: {date_str}\n"
            message += f"{self.config.get('alert_format_hostname_emoji', '🖥️')} Hostname: {system_info.get('hostname', 'N/A')}\n"
            message += f"{self.config.get('alert_format_ip_emoji', '🌐')} IP Address: {system_info.get('ip', 'N/A')}\n"
            message += f"{self.config.get('alert_format_uptime_emoji', '⏳')} Uptime: {system_info.get('uptime', 'N/A')}\n"
            message += f"{self.config.get('alert_format_os_emoji', '🐧')} OS: {system_info.get('os', 'N/A')}\n"
            message += f"{self.config.get('alert_format_kernel_emoji', '⚙️')} Kernel: {system_info.get('kernel', 'N/A')}\n\n"
            
            # Resurslar bo'limi
            message += f"{self.config.get('alert_format_ram_emoji', '🧠')} RAM Usage: {ram_usage}% of {system_info.get('total_ram', 'N/A')}\n"
            message += f"{self.config.get('alert_format_cpu_emoji', '🔥')} CPU Usage: {cpu_usage}% of {system_info.get('total_cpu', 'N/A')}\n"
            
            if self.config.get('monitor_disk', False):
                message += f"{self.config.get('alert_format_disk_emoji', '💾')} Disk Usage: {disk_usage}% of {system_info.get('total_disk', 'N/A')}\n"
            
            if self.config.get('monitor_swap', False):
                message += f"💾 Swap Usage: {swap_usage}%\n"
            
            if self.config.get('monitor_load', False):
                message += f"⚖️ Load Average: {load_average:.1f}%\n"
            
            if self.config.get('monitor_network', False):
                message += f"🌐 Network Usage: RX {network_usage[0]:.1f} Mbps, TX {network_usage[1]:.1f} Mbps\n"
            
            message += "\n"

            if self.config.get('include_top_processes', False):
                top_processes = self.monitor.get_top_processes('RAM')
                message += f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top RAM Consumers:\n{top_processes}\n"
                top_cpu_processes = self.monitor.get_top_processes('CPU')
                message += f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top CPU Consumers:\n{top_cpu_processes}\n"
            
            if self.config.get('alert_format_include_disk_breakdown', False) and self.config.get('monitor_disk', False):
                disk_breakdown = self.monitor.get_disk_breakdown()
                message += f"{self.config.get('alert_format_disk_breakdown_emoji', '📁')} Disk Usage Breakdown:\n"
                if disk_breakdown:
                    for path, size in disk_breakdown.items():
                        message += f"  - {path:<15} {size}\n"
                else:
                    message += "  - Ma'lumot topilmadi\n"

            return message
        except Exception as e:
            self.logger.error(f"Oddiy formatlashda xatolik: {str(e)}")
            return "Oddiy formatlashda xatolik yuz berdi"

    def _formatted_alert(self):
        """Chiroyli chegarali xabar formatlash"""
        try:
            use_box_drawing = self.config.get('alert_format_use_box_drawing', True)
            width = self.config.get('alert_format_width', 44)
            
            if use_box_drawing:
                line_prefix = self.config.get('alert_format_line_prefix', '│ ')
                line_suffix = self.config.get('alert_format_line_suffix', ' │')
                top_border = self.config.get('alert_format_top_border', '┌' + '─' * (width - 2) + '┐')
                title_border = self.config.get('alert_format_title_border', '├' + '─' * (width - 2) + '┤')
                section_border = self.config.get('alert_format_section_border', '├' + '─' * (width - 2) + '┤')
                bottom_border = self.config.get('alert_format_bottom_border', '└' + '─' * (width - 2) + '┘')
            else:
                line_prefix = ""
                line_suffix = ""
                top_border = ""
                title_border = "─" * width
                section_border = "─" * width
                bottom_border = ""
            
            content_width = width - len(line_prefix) - len(line_suffix)

            date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            system_info = self.monitor.get_system_info()
            
            # Barcha metrikalarni olish
            ram_usage = self.monitor.check_ram_usage()
            cpu_usage = self.monitor.check_cpu_usage() if self.config.get('monitor_cpu', False) else 0
            disk_usage = self.monitor.check_disk_usage() if self.config.get('monitor_disk', False) else 0
            swap_usage = self.monitor.check_swap_usage() if self.config.get('monitor_swap', False) else 0
            load_average = self.monitor.check_load_average() if self.config.get('monitor_load', False) else 0
            network_usage = self.monitor.check_network_usage() if self.config.get('monitor_network', False) else [0, 0]

            message = [f"<pre>{top_border}"]

            # Sarlavha
            title = self.config.get('alert_message_title', '🖥️ SYSTEM STATUS ALERT')
            title_align = self.config.get('alert_format_title_align', 'center')
            if title_align == 'center':
                title_line = title.center(content_width)
            elif title_align == 'right':
                title_line = title.rjust(content_width)
            else:
                title_line = title.ljust(content_width)
            message.append(f"{line_prefix}{title_line}{line_suffix}")
            message.append(title_border)

            # Tizim ma'lumotlari
            if self.config.get('alert_format_include_system_info', True):
                emojis = {
                    'date': self.config.get('alert_format_date_emoji', '🗓️'),
                    'hostname': self.config.get('alert_format_hostname_emoji', '🖥️'),
                    'ip': self.config.get('alert_format_ip_emoji', '🌐'),
                    'uptime': self.config.get('alert_format_uptime_emoji', '⏳'),
                    'os': self.config.get('alert_format_os_emoji', '🐧'),
                    'kernel': self.config.get('alert_format_kernel_emoji', '⚙️')
                }
                fields = [
                    (f"{emojis['date']} Date:", date_str),
                    (f"{emojis['hostname']} Hostname:", system_info.get('hostname', 'N/A')),
                    (f"{emojis['ip']} IP Address:", system_info.get('ip', 'N/A')),
                    (f"{emojis['uptime']} Uptime:", system_info.get('uptime', 'N/A')),
                    (f"{emojis['os']} OS:", system_info.get('os', 'N/A')),
                    (f"{emojis['kernel']} Kernel:", system_info.get('kernel', 'N/A'))
                ]
                for label, value in fields:
                    line = f"{label} {value}"
                    message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
                message.append(section_border)

            # Resurslar
            if self.config.get('alert_format_include_resources', True):
                # RAM va CPU
                ram_text = f"{self.config.get('alert_format_ram_emoji', '🧠')} RAM Usage: {ram_usage}% of {system_info.get('total_ram', 'N/A')}"
                cpu_text = f"{self.config.get('alert_format_cpu_emoji', '🔥')} CPU Usage: {cpu_usage}% of {system_info.get('total_cpu', 'N/A')}"
                
                message.append(f"{line_prefix}{ram_text:<{content_width}}{line_suffix}")
                message.append(f"{line_prefix}{cpu_text:<{content_width}}{line_suffix}")
                
                # Disk
                if self.config.get('monitor_disk', False):
                    disk_text = f"{self.config.get('alert_format_disk_emoji', '💾')} Disk Usage: {disk_usage}% of {system_info.get('total_disk', 'N/A')}"
                    message.append(f"{line_prefix}{disk_text:<{content_width}}{line_suffix}")
                
                # Swap
                if self.config.get('monitor_swap', False):
                    swap_text = f"💾 Swap Usage: {swap_usage}%"
                    message.append(f"{line_prefix}{swap_text:<{content_width}}{line_suffix}")
                
                # Load Average
                if self.config.get('monitor_load', False):
                    load_text = f"⚖️ Load Average: {load_average:.1f}%"
                    message.append(f"{line_prefix}{load_text:<{content_width}}{line_suffix}")
                
                # Network
                if self.config.get('monitor_network', False):
                    network_text = f"🌐 Network: RX {network_usage[0]:.1f} Mbps, TX {network_usage[1]:.1f} Mbps"
                    message.append(f"{line_prefix}{network_text:<{content_width}}{line_suffix}")
                
                message.append(section_border)

            # Top jarayonlar (RAM)
            if self.config.get('alert_format_include_top_processes', True) and self.config.get('include_top_processes', False):
                header = f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top RAM Consumers:"
                message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
                top_processes = self.monitor.get_top_processes('RAM')
                top_processes_lines = top_processes.split('\n')
                for proc in top_processes_lines:
                    if proc.strip():
                        if proc.startswith('│'):
                            # Agar jarayon qatori allaqachon formatli bo'lsa
                            message.append(proc)
                        else:
                            message.append(f"{line_prefix}{proc:<{content_width}}{line_suffix}")
                message.append(section_border)

                # Top jarayonlar (CPU)
                header = f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top CPU Consumers:"
                message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
                top_cpu_processes = self.monitor.get_top_processes('CPU')
                top_cpu_processes_lines = top_cpu_processes.split('\n')
                for proc in top_cpu_processes_lines:
                    if proc.strip():
                        if proc.startswith('│'):
                            # Agar jarayon qatori allaqachon formatli bo'lsa
                            message.append(proc)
                        else:
                            message.append(f"{line_prefix}{proc:<{content_width}}{line_suffix}")
                message.append(section_border)

            # Disk bo'linmalari
            if self.config.get('alert_format_include_disk_breakdown', True) and self.config.get('monitor_disk', False):
                header = f"{self.config.get('alert_format_disk_breakdown_emoji', '📁')} Disk Usage Breakdown:"
                message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
                disk_breakdown = self.monitor.get_disk_breakdown()
                if disk_breakdown:
                    for path, size in disk_breakdown.items():
                        line = f"  - {path:<15} {size}"
                        message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
                else:
                    no_data_text = "  - Ma'lumot topilmadi"
                    padding = ' ' * (content_width - len(no_data_text))
                    message.append(f"{line_prefix}{no_data_text}{padding}{line_suffix}")
                
            message.append(bottom_border)
            message.append("</pre>")
            return "\n".join(message)
        except Exception as e:
            self.logger.error(f"Chiroyli formatlashda xatolik: {str(e)}")
            return "Chiroyli formatlashda xatolik yuz berdi"

