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
        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        system_info = self.monitor.get_system_info()
        ram_usage = self.monitor.check_ram_usage()
        cpu_usage = self.monitor.check_cpu_usage() if self.config.get('monitor_cpu', False) else 0
        disk_usage = self.monitor.check_disk_usage() if self.config.get('monitor_disk', False) else 0

        message = f"{self.config['alert_message_title']}\n\n"
        message += f"{self.config.get('alert_format_date_emoji', '')} Date: {date_str}\n"
        message += f"{self.config.get('alert_format_hostname_emoji', '')} Hostname: {system_info['hostname']}\n"
        message += f"{self.config.get('alert_format_ip_emoji', '')} IP Address: {system_info['ip']}\n"
        message += f"{self.config.get('alert_format_uptime_emoji', '')} Uptime: {system_info['uptime']}\n"
        message += f"{self.config.get('alert_format_os_emoji', '')} OS: {system_info['os']}\n"
        message += f"{self.config.get('alert_format_kernel_emoji', '')} Kernel: {system_info['kernel']}\n\n"
        message += f"{self.config.get('alert_format_ram_emoji', '')} RAM Usage: {ram_usage}% of {system_info['total_ram']}\n"
        message += f"{self.config.get('alert_format_cpu_emoji', '')} CPU Usage: {cpu_usage}%\n"
        message += f"{self.config.get('alert_format_disk_emoji', '')} Disk Usage: {disk_usage}% of {system_info['total_disk']}\n\n"

        if self.config.get('include_top_processes', False):
            top_processes = self.monitor.get_top_processes('RAM')
            message += f"{self.config.get('alert_format_top_processes_emoji', '')} Top RAM Consumers:\n{top_processes}\n"
        if self.config.get('alert_format_include_disk_breakdown', False):
            disk_breakdown = self.monitor.get_disk_breakdown()
            message += f"{self.config.get('alert_format_disk_breakdown_emoji', '')} Disk Usage Breakdown:\n"
            for path, size in disk_breakdown.items():
                message += f"  - {path:<15} {size}\n"

        return message

    def _formatted_alert(self):
        """Chiroyli chegarali xabar formatlash"""
        width = self.config.get('alert_format_width', 44)
        line_prefix = self.config.get('alert_format_line_prefix', '│ ')
        line_suffix = self.config.get('alert_format_line_suffix', ' │')
        top_border = self.config.get('alert_format_top_border', '┌' + '─' * (width - 2) + '┐')
        title_border = self.config.get('alert_format_title_border', '├' + '─' * (width - 2) + '┤')
        section_border = self.config.get('alert_format_section_border', '├' + '─' * (width - 2) + '┤')
        bottom_border = self.config.get('alert_format_bottom_border', '└' + '─' * (width - 2) + '┘')
        content_width = width - len(line_prefix) - len(line_suffix)

        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        system_info = self.monitor.get_system_info()
        ram_usage = self.monitor.check_ram_usage()
        cpu_usage = self.monitor.check_cpu_usage() if self.config.get('monitor_cpu', False) else 0
        disk_usage = self.monitor.check_disk_usage() if self.config.get('monitor_disk', False) else 0

        message = [f"<pre>{top_border}"]

        # Sarlavha
        title = self.config['alert_message_title']
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
                'date': self.config.get('alert_format_date_emoji', ''),
                'hostname': self.config.get('alert_format_hostname_emoji', ''),
                'ip': self.config.get('alert_format_ip_emoji', ''),
                'uptime': self.config.get('alert_format_uptime_emoji', ''),
                'os': self.config.get('alert_format_os_emoji', ''),
                'kernel': self.config.get('alert_format_kernel_emoji', '')
            }
            fields = [
                (f"{emojis['date']} Date:", date_str),
                (f"{emojis['hostname']} Hostname:", system_info['hostname']),
                (f"{emojis['ip']} IP Address:", system_info['ip']),
                (f"{emojis['uptime']} Uptime:", system_info['uptime']),
                (f"{emojis['os']} OS:", system_info['os']),
                (f"{emojis['kernel']} Kernel:", system_info['kernel'])
            ]
            for label, value in fields:
                line = f"{label} {value}"
                message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
            message.append(section_border)

        # Resurslar
        if self.config.get('alert_format_include_resources', True):
            ram_text = f"{self.config.get('alert_format_ram_emoji', '')} RAM Usage: {ram_usage}% of {system_info['total_ram']}"
            cpu_text = f"{self.config.get('alert_format_cpu_emoji', '')} CPU Usage: {cpu_usage}%"
            disk_text = f"{self.config.get('alert_format_disk_emoji', '')} Disk Usage: {disk_usage}% of {system_info['total_disk']}"
            for text in [ram_text, cpu_text, disk_text]:
                message.append(f"{line_prefix}{text:<{content_width}}{line_suffix}")
            message.append(section_border)

        # Top jarayonlar
        if self.config.get('alert_format_include_top_processes', True) and self.config.get('include_top_processes', False):
            header = f"{self.config.get('alert_format_top_processes_emoji', '')} Top RAM Consumers:"
            message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
            top_processes = self.monitor.get_top_processes('RAM')
            if isinstance(top_processes, str):
                top_processes = top_processes.split('\n')[:self.config.get('top_processes_count', 3)]
            for proc in top_processes:
                message.append(f"{line_prefix}{proc:<{content_width}}{line_suffix}")
            message.append(section_border)

        # Disk bo‘linmalari
        if self.config.get('alert_format_include_disk_breakdown', True):
            header = f"{self.config.get('alert_format_disk_breakdown_emoji', '')} Disk Usage Breakdown:"
            message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
            disk_breakdown = self.monitor.get_disk_breakdown()
            for path, size in disk_breakdown.items():
                line = f"  - {path:<15} {size}"
                message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")

        message.append(bottom_border)
        message.append("</pre>")
        return "\n".join(message)