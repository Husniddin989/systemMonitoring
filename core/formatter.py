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

    def format_alert_message(self, alert_type, usage_value):
        """
        Alert xabarini konfiguratsiyaga muvofiq formatlash
        
        Args:
            alert_type (str): Alert turi
            usage_value (str): Alert qiymati
            
        Returns:
            str: Formatlangan xabar
        """
        if not self.config['alert_format_enabled']:
            # Oddiy matn formati
            date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            system_info = self.monitor.get_system_info()
            
            message = f"{self.config['alert_message_title']}\n\n"
            message += f"Date: {date_str}\n"
            message += f"Hostname: {system_info['hostname']}\n"
            message += f"IP Address: {system_info['ip']}\n"
            message += f"Uptime: {system_info['uptime']}\n"
            message += f"OS: {system_info['os']}\n"
            message += f"Kernel: {system_info['kernel']}\n\n"
            
            ram_usage = self.monitor.check_ram_usage()
            cpu_usage = self.monitor.check_cpu_usage() if self.config['monitor_cpu'] else 0
            disk_usage = self.monitor.check_disk_usage() if self.config['monitor_disk'] else 0
            
            message += f"RAM Usage: {ram_usage}% of {system_info['total_ram']}\n"
            message += f"CPU Usage: {cpu_usage}%\n"
            message += f"Disk Usage: {disk_usage}% of {system_info['total_disk']}\n\n"
            
            if self.config['include_top_processes']:
                message += f"Top RAM Consumers:\n{self.monitor.get_top_processes('RAM')}\n\n"
                message += f"Disk Usage Breakdown:\n{self.monitor.get_top_processes('Disk')}"
            
            return message
        
        # Maxsus format
        width = self.config['alert_format_width']
        line_prefix = "│ " if self.config['alert_format_use_box_drawing'] else ""
        line_suffix = " │" if self.config['alert_format_use_box_drawing'] else ""
        content_width = width - len(line_prefix) - len(line_suffix) if width > 0 else 0
        
        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        system_info = self.monitor.get_system_info()
        ram_usage = self.monitor.check_ram_usage()
        cpu_usage = self.monitor.check_cpu_usage() if self.config['monitor_cpu'] else 0
        disk_usage = self.monitor.check_disk_usage() if self.config['monitor_disk'] else 0
        
        # Sarlavhani formatlash
        title = self.config['alert_message_title']
        title_align = self.config['alert_format_title_align']
        if content_width > 0:
            if title_align == 'center':
                title_line = line_prefix + title.center(content_width) + line_suffix
            elif title_align == 'right':
                title_line = line_prefix + title.rjust(content_width) + line_suffix
            else:
                title_line = line_prefix + title.ljust(content_width) + line_suffix
        else:
            title_line = line_prefix + title + line_suffix
        
        message = []
        message.append("┌────────────────────────────────────────────┐" if self.config['alert_format_use_box_drawing'] else "")
        message.append(title_line)
        message.append("├────────────────────────────────────────────┤" if self.config['alert_format_use_box_drawing'] else "")
        
        # Tizim ma'lumotlari
        if self.config['alert_format_include_system_info']:
            emojis = {
                'date': self.config['alert_format_date_emoji'],
                'hostname': self.config['alert_format_hostname_emoji'],
                'ip': self.config['alert_format_ip_emoji'],
                'uptime': self.config['alert_format_uptime_emoji'],
                'os': self.config['alert_format_os_emoji'],
                'kernel': self.config['alert_format_kernel_emoji']
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
                if content_width > 0:
                    message.append(f"{line_prefix}{label} {value}{' ' * (content_width - len(label) - len(value) - 1)}{line_suffix}")
                else:
                    message.append(f"{line_prefix}{label} {value}{line_suffix}")
            message.append("├────────────────────────────────────────────┤" if self.config['alert_format_use_box_drawing'] else "")
        
        # Resurslar
        if self.config['alert_format_include_resources']:
            ram_text = f"{self.config['alert_format_ram_emoji']} RAM Usage: {ram_usage}% of {system_info['total_ram']}"
            cpu_text = f"{self.config['alert_format_cpu_emoji']} CPU Usage: {cpu_usage}%"
            disk_text = f"{self.config['alert_format_disk_emoji']} Disk Usage: {disk_usage}% of {system_info['total_disk']}"
            for text in [ram_text, cpu_text, disk_text]:
                if content_width > 0:
                    message.append(f"{line_prefix}{text}{' ' * (content_width - len(text))}{line_suffix}")
                else:
                    message.append(f"{line_prefix}{text}{line_suffix}")
            message.append("├────────────────────────────────────────────┤" if self.config['alert_format_use_box_drawing'] else "")
        
        # Top jarayonlar
        if self.config['alert_format_include_top_processes'] and self.config['include_top_processes']:
            header = f"{self.config['alert_format_top_processes_emoji']} Top RAM Consumers:"
            if content_width > 0:
                message.append(f"{line_prefix}{header}{' ' * (content_width - len(header))}{line_suffix}")
            else:
                message.append(f"{line_prefix}{header}{line_suffix}")
            
            top_processes = self.monitor.get_top_processes('RAM').split('\n')[:3]
            for proc in top_processes:
                if content_width > 0:
                    message.append(f"{line_prefix}{proc}{' ' * (content_width - len(proc))}{line_suffix}")
                else:
                    message.append(f"{line_prefix}{proc}{line_suffix}")
            message.append("├────────────────────────────────────────────┤" if self.config['alert_format_use_box_drawing'] else "")
        
        # Disk bo‘linmalari
        if self.config['alert_format_include_disk_breakdown'] and self.config['include_top_processes']:
            header = f"{self.config['alert_format_disk_breakdown_emoji']} Disk Usage Breakdown:"
            if content_width > 0:
                message.append(f"{line_prefix}{header}{' ' * (content_width - len(header))}{line_suffix}")
            else:
                message.append(f"{line_prefix}{header}{line_suffix}")
            
            disk_breakdown = self.monitor.get_top_processes('Disk').split('\n')[:3]
            for entry in disk_breakdown:
                if content_width > 0:
                    message.append(f"{line_prefix}{entry}{' ' * (content_width - len(entry))}{line_suffix}")
                else:
                    message.append(f"{line_prefix}{entry}{line_suffix}")
        
        message.append("└────────────────────────────────────────────┘" if self.config['alert_format_use_box_drawing'] else "")
        return "\n".join(message)