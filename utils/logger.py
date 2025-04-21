#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Log sozlamalarini boshqarish moduli
"""

import logging
import os

class Logger:
    def __init__(self, log_file, log_level):
        """
        Logger obyectini ishga tushirish
        
        Args:
            log_file (str): Log faylining yo‘li
            log_level (str): Log darajasi (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file = log_file
        self.log_level = log_level
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """
        Log sozlamalarini tashkil qilish
        
        Returns:
            logging.Logger: Tayyor logger obyekti
        """
        log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        
        # Log fayli uchun direktoriyani yaratish
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Log sozlamalarini o‘rnatish
        log_level = log_levels.get(self.log_level, logging.INFO)
        logger = logging.getLogger('memory_monitor')
        logger.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        
        # Fayl handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Konsol handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        return logger

    def get_logger(self):
        """
        Logger obyectini qaytarish
        
        Returns:
            logging.Logger: Logger obyekti
        """
        return self.logger