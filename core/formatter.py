#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alert xabarlarini formatlash moduli - har bir metrika uchun alohida xabar formati
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

    def format_metric_alert(self, metric_type, usage_value, alert_format='HTML', alert_title=None, system_info=None):
        """
        Metrika turiga qarab xabarni formatlash
        
        Args:
            metric_type (str): Metrika turi (RAM, CPU, Disk, va h.k.)
            usage_value (str): Metrika qiymati
            alert_format (str): Xabar formati (HTML yoki TEXT)
            alert_title (str, optional): Xabar sarlavhasi
            system_info (dict, optional): Tizim ma'lumotlari
            
        Returns:
            str: Formatlangan xabar
        """
        metric_key = metric_type.lower()
        
        # Tizim ma'lumotlarini olish
        if system_info is None:
            system_info = self.monitor.get_system_info()
            
        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Metrika qiymatini olish
        metric_value = None
        if metric_key == 'ram':
            metric_value = self.monitor.check_ram_usage()
            metric_emoji = self.config.get('alert_format_ram_emoji', '🧠')
            metric_total = system_info.get('total_ram', 'N/A')
        elif metric_key == 'cpu':
            metric_value = self.monitor.check_cpu_usage()
            metric_emoji = self.config.get('alert_format_cpu_emoji', '🔥')
            metric_total = system_info.get('total_cpu', 'N/A')
        elif metric_key == 'disk':
            metric_value = self.monitor.check_disk_usage()
            metric_emoji = self.config.get('alert_format_disk_emoji', '💾')
            metric_total = system_info.get('total_disk', 'N/A')
        elif metric_key == 'swap':
            metric_value = self.monitor.check_swap_usage()
            metric_emoji = self.config.get('alert_format_swap_emoji', '💾')
            metric_total = "N/A"
        elif metric_key == 'load':
            metric_value = self.monitor.check_load_average()
            metric_emoji = self.config.get('alert_format_load_emoji', '⚖️')
            metric_total = "N/A"
        elif metric_key == 'network rx':
            network_usage = self.monitor.check_network_usage()
            metric_value = network_usage[0]
            metric_emoji = self.config.get('alert_format_network_emoji', '🌐')
            metric_total = "N/A"
        elif metric_key == 'network tx':
            network_usage = self.monitor.check_network_usage()
            metric_value = network_usage[1]
            metric_emoji = self.config.get('alert_format_network_emoji', '🌐')
            metric_total = "N/A"
        else:
            metric_emoji = "🚨"
            metric_total = "N/A"
        
        # Sarlavhani o'rnatish
        if not alert_title:
            alert_title = f'{metric_emoji} {metric_type} ALERT: {usage_value}'
        
        # Xabar formatini tanlash
        if alert_format.upper() == 'HTML':
            return self._format_html_metric_alert(metric_type, usage_value, metric_value, metric_emoji, metric_total, system_info, date_str, alert_title)
        else:
            return self._format_text_metric_alert(metric_type, usage_value, metric_value, metric_emoji, metric_total, system_info, date_str, alert_title)

    def _format_html_metric_alert(self, metric_type, usage_value, metric_value, metric_emoji, metric_total, system_info, date_str, alert_title):
        """
        HTML formatida metrika xabarini formatlash
        
        Args:
            metric_type (str): Metrika turi
            usage_value (str): Metrika qiymati
            metric_value (float): Metrika qiymati (son)
            metric_emoji (str): Metrika emojisi
            metric_total (str): Metrika umumiy qiymati
            system_info (dict): Tizim ma'lumotlari
            date_str (str): Sana va vaqt
            alert_title (str): Xabar sarlavhasi
            
        Returns:
            str: HTML formatida xabar
        """
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
        
        message = [f"<pre>{top_border}"]
        
        # Sarlavha
        title_align = self.config.get('alert_format_title_align', 'center')
        if title_align == 'center':
            title_line = alert_title.center(content_width)
        elif title_align == 'right':
            title_line = alert_title.rjust(content_width)
        else:
            title_line = alert_title.ljust(content_width)
        message.append(f"{line_prefix}{title_line}{line_suffix}")
        message.append(title_border)
        
        # Tizim ma'lumotlari
        emojis = {
            'date': self.config.get('alert_format_date_emoji', '🗓️'),
            'hostname': self.config.get('alert_format_hostname_emoji', '🖥️'),
            'ip': self.config.get('alert_format_ip_emoji', '🌐'),
            'uptime': self.config.get('alert_format_uptime_emoji', '⏳')
        }
        
        fields = [
            (f"{emojis['date']} Date:", date_str),
            (f"{emojis['hostname']} Hostname:", system_info.get('hostname', 'N/A')),
            (f"{emojis['ip']} IP Address:", system_info.get('ip', 'N/A')),
            (f"{emojis['uptime']} Uptime:", system_info.get('uptime', 'N/A'))
        ]
        
        for label, value in fields:
            line = f"{label} {value}"
            message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
        
        message.append(section_border)
        
        # Metrika ma'lumotlari
        metric_text = f"{metric_emoji} {metric_type}: {usage_value}"
        if metric_total != "N/A":
            metric_text += f" of {metric_total}"
        
        message.append(f"{line_prefix}{metric_text:<{content_width}}{line_suffix}")
        
        # Metrika turiga qarab qo'shimcha ma'lumotlar
        metric_key = metric_type.lower()
        
        if metric_key == 'cpu' and self.config.get('include_top_processes', False):
            message.append(section_border)
            top_processes = self.monitor.get_top_processes('CPU')
            top_processes_lines = top_processes.split('\n')
            
            header = f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top CPU Consumers:"
            message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
            
            for line in top_processes_lines:
                if line.strip():
                    message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
        
        elif metric_key == 'ram' and self.config.get('include_top_processes', False):
            message.append(section_border)
            top_processes = self.monitor.get_top_processes('RAM')
            top_processes_lines = top_processes.split('\n')
            
            header = f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top RAM Consumers:"
            message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
            
            for line in top_processes_lines:
                if line.strip():
                    message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
        
        elif metric_key == 'disk' and self.config.get('alert_format_include_disk_breakdown', False):
            message.append(section_border)
            disk_breakdown = self.monitor.get_disk_breakdown() if hasattr(self.monitor, 'get_disk_breakdown') else None
            
            header = f"{self.config.get('alert_format_disk_breakdown_emoji', '📁')} Disk Usage Breakdown:"
            message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
            
            if disk_breakdown:
                for path, size in disk_breakdown.items():
                    line = f"  - {path:<15} {size}"
                    message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
            else:
                message.append(f"{line_prefix}  - Ma'lumot topilmadi{' ' * (content_width - 22)}{line_suffix}")
        
        message.append(bottom_border)
        message.append("</pre>")
        
        return "\n".join(message)

    def _format_text_metric_alert(self, metric_type, usage_value, metric_value, metric_emoji, metric_total, system_info, date_str, alert_title):
        """
        Oddiy matn formatida metrika xabarini formatlash
        
        Args:
            metric_type (str): Metrika turi
            usage_value (str): Metrika qiymati
            metric_value (float): Metrika qiymati (son)
            metric_emoji (str): Metrika emojisi
            metric_total (str): Metrika umumiy qiymati
            system_info (dict): Tizim ma'lumotlari
            date_str (str): Sana va vaqt
            alert_title (str): Xabar sarlavhasi
            
        Returns:
            str: Oddiy matn formatida xabar
        """
        message = f"{alert_title}\n\n"
        
        # Tizim ma'lumotlari
        emojis = {
            'date': self.config.get('alert_format_date_emoji', '🗓️'),
            'hostname': self.config.get('alert_format_hostname_emoji', '🖥️'),
            'ip': self.config.get('alert_format_ip_emoji', '🌐'),
            'uptime': self.config.get('alert_format_uptime_emoji', '⏳')
        }
        
        message += f"{emojis['date']} Date: {date_str}\n"
        message += f"{emojis['hostname']} Hostname: {system_info.get('hostname', 'N/A')}\n"
        message += f"{emojis['ip']} IP Address: {system_info.get('ip', 'N/A')}\n"
        message += f"{emojis['uptime']} Uptime: {system_info.get('uptime', 'N/A')}\n\n"
        
        # Metrika ma'lumotlari
        message += f"{metric_emoji} {metric_type}: {usage_value}"
        if metric_total != "N/A":
            message += f" of {metric_total}"
        message += "\n\n"
        
        # Metrika turiga qarab qo'shimcha ma'lumotlar
        metric_key = metric_type.lower()
        
        if metric_key == 'cpu' and self.config.get('include_top_processes', False):
            top_processes = self.monitor.get_top_processes('CPU')
            message += f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top CPU Consumers:\n{top_processes}\n"
        
        elif metric_key == 'ram' and self.config.get('include_top_processes', False):
            top_processes = self.monitor.get_top_processes('RAM')
            message += f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top RAM Consumers:\n{top_processes}\n"
        
        elif metric_key == 'disk' and self.config.get('alert_format_include_disk_breakdown', False):
            disk_breakdown = self.monitor.get_disk_breakdown() if hasattr(self.monitor, 'get_disk_breakdown') else None
            
            message += f"{self.config.get('alert_format_disk_breakdown_emoji', '📁')} Disk Usage Breakdown:\n"
            
            if disk_breakdown:
                for path, size in disk_breakdown.items():
                    message += f"  - {path:<15} {size}\n"
            else:
                message += "  - Ma'lumot topilmadi\n"
        
        return message

    def format_alert_message(self, alert_type=None, usage_value=None):
        """
        Alert xabarini konfiguratsiyaga muvofiq formatlash (eski usul, backward compatibility uchun)
        
        Args:
            alert_type (str, optional): Alert turi (masalan, 'RAM', 'CPU')
            usage_value (str, optional): Alert qiymati (masalan, '85%')
            
        Returns:
            str: Formatlangan xabar
        """
        if alert_type is None:
            self.logger.warning("alert_type=None bilan chaqirildi, SYSTEM STATUS ALERT o'chirildi")
            return None
        if not self.config.get('alert_format_enabled', False):
            self.logger.info("Oddiy matn formati ishlatilmoqda")
            return self._simple_format(alert_type, usage_value)

        self.logger.info("Chiroyli formatlash ishlatilmoqda")
        return self._formatted_alert(alert_type, usage_value)

    def _simple_format(self, alert_type=None, usage_value=None):
        """
        Oddiy matnli xabar formatlash (eski usul, backward compatibility uchun)
        
        Args:
            alert_type (str, optional): Alert turi
            usage_value (str, optional): Alert qiymati
            
        Returns:
            str: Formatlangan xabar
        """
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

            # Alert sarlavhasini yaratish
            if alert_type and usage_value:
                title = f"🚨 {alert_type} ALERT: {usage_value} threshold oshildi!"
            else:
                title = self.config.get('alert_message_title', '🖥️ SYSTEM STATUS ALERT')

            message = f"{title}\n\n"
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
            
            if self.config.get('monitor_swap', False) and self.config.get('include_swap_details', True):
                message += f"{self.config.get('alert_format_swap_emoji', '💾')} Swap Usage: {swap_usage}%\n"
            
            if self.config.get('monitor_load', False) and self.config.get('include_load_details', True):
                message += f"{self.config.get('alert_format_load_emoji', '⚖️')} Load Average: {load_average:.1f}%\n"
            
            if self.config.get('monitor_network', False) and self.config.get('include_network_details', True):
                message += f"{self.config.get('alert_format_network_emoji', '🌐')} Network Usage: RX {network_usage[0]:.1f} Mbps, TX {network_usage[1]:.1f} Mbps\n"
            
            message += "\n"

            if self.config.get('include_top_processes', False):
                # Umumiy qiymatlarni ko'rsatish uchun show_total=True
                self.config['show_total_cpu_usage_in_list'] = True
                
                top_processes = self.monitor.get_top_processes('RAM')
                message += f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top RAM Consumers:\n{top_processes}\n"
                
                top_cpu_processes = self.monitor.get_top_processes('CPU')
                message += f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top CPU Consumers:\n{top_cpu_processes}\n"
            
            if self.config.get('alert_format_include_disk_breakdown', False) and self.config.get('monitor_disk', False) and self.config.get('include_disk_details', True):
                disk_breakdown = self.monitor.get_disk_breakdown() if hasattr(self.monitor, 'get_disk_breakdown') else None
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

    def _formatted_alert(self, alert_type=None, usage_value=None):
        """
        Chiroyli chegarali xabar formatlash (eski usul, backward compatibility uchun)
        
        Args:
            alert_type (str, optional): Alert turi
            usage_value (str, optional): Alert qiymati
            
        Returns:
            str: Formatlangan xabar
        """
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
            if alert_type and usage_value:
                title = f"🚨 {alert_type} ALERT: {usage_value}"
            else:
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
                if self.config.get('monitor_swap', False) and self.config.get('include_swap_details', True) and self.config.get('alert_format_include_swap_details', True):
                    swap_text = f"{self.config.get('alert_format_swap_emoji', '💾')} Swap Usage: {swap_usage}%"
                    message.append(f"{line_prefix}{swap_text:<{content_width}}{line_suffix}")
                
                # Load Average
                if self.config.get('monitor_load', False) and self.config.get('include_load_details', True) and self.config.get('alert_format_include_load_details', True):
                    load_text = f"{self.config.get('alert_format_load_emoji', '⚖️')} Load Average: {load_average:.1f}%"
                    message.append(f"{line_prefix}{load_text:<{content_width}}{line_suffix}")
                
                # Network
                if self.config.get('monitor_network', False) and self.config.get('include_network_details', True) and self.config.get('alert_format_include_network_details', True):
                    network_text = f"{self.config.get('alert_format_network_emoji', '🌐')} Network: RX {network_usage[0]:.1f} Mbps, TX {network_usage[1]:.1f} Mbps"
                    message.append(f"{line_prefix}{network_text:<{content_width}}{line_suffix}")
                
                message.append(section_border)

            # Top jarayonlar (RAM)
            if self.config.get('alert_format_include_top_processes', True) and self.config.get('include_top_processes', False):
                # Umumiy qiymatlarni ko'rsatish uchun show_total=True
                self.config['show_total_cpu_usage_in_list'] = True
                
                header = f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top RAM Consumers:"
                message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
                
                top_processes = self.monitor.get_top_processes('RAM')
                top_processes_lines = top_processes.split('\n')
                
                # Jarayonlar va umumiy qiymatni alohida ajratish
                process_lines = []
                total_line = ""
                
                for proc in top_processes_lines:
                    if proc.strip():
                        if proc.startswith('Umumiy RAM:'):
                            total_line = proc
                        elif proc.startswith('│'):
                            process_lines.append(proc)
                        else:
                            process_lines.append(f"{line_prefix}{proc:<{content_width}}{line_suffix}")
                
                # Jarayonlarni qo'shish
                for line in process_lines:
                    message.append(line)
                
                # Umumiy qiymatni qo'shish
                if total_line:
                    message.append(f"{line_prefix}{total_line:<{content_width}}{line_suffix}")
                
                message.append(section_border)

                # Top jarayonlar (CPU)
                header = f"{self.config.get('alert_format_top_processes_emoji', '🧾')} Top CPU Consumers:"
                message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
                
                top_cpu_processes = self.monitor.get_top_processes('CPU')
                top_cpu_processes_lines = top_cpu_processes.split('\n')
                
                # Jarayonlar va umumiy qiymatni alohida ajratish
                process_lines = []
                total_line = ""
                
                for proc in top_cpu_processes_lines:
                    if proc.strip():
                        if proc.startswith('Umumiy CPU usage'):
                            total_line = proc
                        elif proc.startswith('│'):
                            process_lines.append(proc)
                        else:
                            process_lines.append(f"{line_prefix}{proc:<{content_width}}{line_suffix}")
                
                # Jarayonlarni qo'shish
                for line in process_lines:
                    message.append(line)
                
                # Umumiy qiymatni qo'shish
                if total_line:
                    message.append(f"{line_prefix}{total_line:<{content_width}}{line_suffix}")
                
                message.append(section_border)

            # Disk breakdown
            if self.config.get('alert_format_include_disk_breakdown', True) and self.config.get('monitor_disk', False) and self.config.get('include_disk_details', True):
                disk_breakdown = self.monitor.get_disk_breakdown() if hasattr(self.monitor, 'get_disk_breakdown') else None
                
                header = f"{self.config.get('alert_format_disk_breakdown_emoji', '📁')} Disk Usage Breakdown:"
                message.append(f"{line_prefix}{header:<{content_width}}{line_suffix}")
                
                if disk_breakdown:
                    for path, size in disk_breakdown.items():
                        line = f"  - {path:<15} {size}"
                        message.append(f"{line_prefix}{line:<{content_width}}{line_suffix}")
                else:
                    message.append(f"{line_prefix}  - Ma'lumot topilmadi{' ' * (content_width - 22)}{line_suffix}")
            
            message.append(bottom_border)
            message.append("</pre>")
            
            return "\n".join(message)
            
        except Exception as e:
            self.logger.error(f"Chiroyli formatlashda xatolik: {str(e)}")
            return "Chiroyli formatlashda xatolik yuz berdi"
