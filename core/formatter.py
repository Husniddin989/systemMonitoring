#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tizim holati uchun Telegram xabarlarini formatlash moduli
"""

import textwrap
from datetime import datetime

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

    def format_alert(self):
        """
        Tizim holati uchun formatlangan alert xabarini yaratish
        
        Returns:
            str: Formatlangan xabar matni
        """
        if not self.config.get('alert_format_enabled', True):
            self.logger.info("Oddiy formatlash ishlatilmoqda")
            return self._simple_format()

        self.logger.info("Chiroyli formatlash ishlatilmoqda")
        return self._formatted_alert()

    def _simple_format(self):
        """Oddiy matnli xabar formatlash"""
        system_info = self.monitor.get_system_info()
        resources = self.monitor.get_resources()
        top_processes = self.monitor.get_top_processes()
        disk_breakdown = self.monitor.get_disk_breakdown()

        message = f"{self.config['alert_message_title']}\n\n"
        message += f"{self.config['alert_format_date_emoji']} Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f" Hostname: {system_info['hostname']}\n"
        message += f" IP Address: {system_info['ip']}\n"
        message += f" Uptime: {system_info['uptime']}\n"
        message += f" OS: {system_info['os']}\n"
        message += f" Kernel: {system_info['kernel']}\n\n"
        message += f"{self.config['alert_format_ram_emoji']} RAM Usage: {resources['memory_percent']:.1f}% of {system_info['total_ram']}\n"
        message += f"{self.config['alert_format_cpu_emoji']} CPU Usage: {resources['cpu_percent']:.1f}%\n"
        message += f"{self.config['alert_format_disk_emoji']} Disk Usage: {resources['disk_percent']:.1f}% of {system_info['total_disk']}\n\n"
        if self.config['alert_format_include_top_processes']:
            message += f"{self.config['alert_format_top_processes_emoji']} Top RAM Consumers:\n"
            for proc in top_processes:
                message += f"  - {proc['name']} ({proc['memory_percent']:.1f}%)\n"
        if self.config['alert_format_include_disk_breakdown']:
            message += f"\n{self.config['alert_format_disk_breakdown_emoji']} Disk Usage Breakdown:\n"
            for path, size in disk_breakdown.items():
                message += f"  - {path:<15} {size}\n"

        return message

    def _formatted_alert(self):
        """Chiroyli chegarali xabar formatlash"""
        system_info = self.monitor.get_system_info()
        resources = self.monitor.get_resources()
        top_processes = self.monitor.get_top_processes()
        disk_breakdown = self.monitor.get_disk_breakdown()

        width = self.config.get('alert_format_width', 44)
        line_prefix = self.config.get('alert_format_line_prefix', '│ ')
        line_suffix = self.config.get('alert_format_line_suffix', ' │')
        top_border = self.config.get('alert_format_top_border', '┌' + '─' * (width - 2) + '┐')
        title_border = self.config.get('alert_format_title_border', '├' + '─' * (width - 2) + '┤')
        section_border = self.config.get('alert_format_section_border', '├' + '─' * (width - 2) + '┤')
        bottom_border = self.config.get('alert_format_bottom_border', '└' + '─' * (width - 2) + '┘')

        message = f"<pre>{top_border}\n"

        # Sarlavha
        title = self.config['alert_message_title']
        if self.config.get('alert_format_title_align', 'center') == 'center':
            title = title.center(width - 4)
        message += f"{line_prefix}{title}{line_suffix}\n{title_border}\n"

        # Tizim ma'lumotlari
        if self.config.get('alert_format_include_system_info', True):
            message += f"{line_prefix}{self.config['alert_format_date_emoji']} Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{line_suffix}\n"
            message += f"{line_prefix}{self.config.get('alert_format_hostname_emoji', '')} Hostname: {system_info['hostname']}{line_suffix}\n"
            message += f"{line_prefix}{self.config.get('alert_format_ip_emoji', '')} IP Address: {system_info['ip']}{line_suffix}\n"
            message += f"{line_prefix}{self.config.get('alert_format_uptime_emoji', '')} Uptime: {system_info['uptime']}{line_suffix}\n"
            message += f"{line_prefix}{self.config.get('alert_format_os_emoji', '')} OS: {system_info['os']}{line_suffix}\n"
            message += f"{line_prefix}{self.config.get('alert_format_kernel_emoji', '')} Kernel: {system_info['kernel']}{line_suffix}\n"
            message += f"{section_border}\n"

        # Resurslar
        if self.config.get('alert_format_include_resources', True):
            message += f"{line_prefix}{self.config['alert_format_ram_emoji']} RAM Usage: {resources['memory_percent']:.1f}% of {system_info['total_ram']}{line_suffix}\n"
            message += f"{line_prefix}{self.config['alert_format_cpu_emoji']} CPU Usage: {resources['cpu_percent']:.1f}%{line_suffix}\n"
            message += f"{line_prefix}{self.config['alert_format_disk_emoji']} Disk Usage: {resources['disk_percent']:.1f}% of {system_info['total_disk']}{line_suffix}\n"
            message += f"{section_border}\n"

        # Top jarayonlar
        if self.config.get('alert_format_include_top_processes', True):
            message += f"{line_prefix}{self.config['alert_format_top_processes_emoji']} Top RAM Consumers:{line_suffix}\n"
            for proc in top_processes:
                proc_line = f"  - {proc['name']} ({proc['memory_percent']:.1f}%)"
                message += f"{line_prefix}{proc_line:<{width-4}}{line_suffix}\n"
            message += f"{section_border}\n"

        # Disk bo‘linmalari
        if self.config.get('alert_format_include_disk_breakdown', True):
            message += f"{line_prefix}{self.config['alert_format_disk_breakdown_emoji']} Disk Usage Breakdown:{line_suffix}\n"
            for path, size in disk_breakdown.items():
                disk_line = f"  - {path:<15} {size}"
                message += f"{line_prefix}{disk_line:<{width-4}}{line_suffix}\n"

        message += f"{bottom_border}</pre>"
        return message