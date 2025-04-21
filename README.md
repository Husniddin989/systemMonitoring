# System Monitoring

Tizim resurslarini monitoring qilish va Telegram orqali xabarlar yuborish uchun dastur.

## Imkoniyatlar

- RAM, CPU, disk, swap, load va tarmoq resurslarini monitoring qilish
- Telegram orqali xabarlar yuborish
- Chiroyli formatlangan xabarlar
- Prometheus metrikalarini eksport qilish
- Ma'lumotlar bazasiga metrikalarni saqlash (SQLite, MySQL, PostgreSQL)
- Konfiguratsiya fayli orqali sozlash
- Systemd service sifatida ishlash

## O'rnatish

### Talablar

- Python 3.6 yoki undan yuqori
- pip
- Systemd (Linux)

### O'rnatish jarayoni

1. Repozitoriyani yuklab oling:

```bash
git clone https://github.com/username/system-monitoring.git
cd system-monitoring
```

2. O'rnatish skriptini ishga tushiring:

```bash
sudo ./install.sh
```

O'rnatish jarayonida quyidagi qo'shimcha paketlarni o'rnatishni tanlashingiz mumkin:
- SQLite (standart Python bilan birga keladi)
- MySQL (mysql-connector-python)
- PostgreSQL (psycopg2-binary)
- Prometheus (prometheus-client)

3. Konfiguratsiya faylini sozlang:

```bash
sudo nano /etc/system-monitor/config.conf
```

4. Telegram ulanishini tekshiring:

```bash
sudo system-monitor-test-telegram
```

5. Xizmatni yoqing va ishga tushiring:

```bash
sudo systemctl enable system-monitor.service
sudo systemctl start system-monitor.service
```

## Konfiguratsiya

Konfiguratsiya fayli `/etc/system-monitor/config.conf` da joylashgan. Konfiguratsiya fayli INI formatida bo'lib, quyidagi bo'limlardan iborat:

### General

```ini
[General]
# Telegram bot token va chat ID
bot_token = YOUR_BOT_TOKEN
chat_id = YOUR_CHAT_ID

# Log fayli va log darajasi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
log_file = /var/log/system_monitor.log
log_level = INFO

# Tekshirish oralig'i (soniyalarda)
check_interval = 60

# Xabar sarlavhasi
alert_message_title = 🖥️ SYSTEM STATUS ALERT

# Top jarayonlarni ko'rsatish
include_top_processes = true
top_processes_count = 10

# Top jarayonlar umumiy CPU foizini ko'rsatish
show_total_cpu_usage_in_list = true

# Umumiy CPU foizi sifatida top jarayonlar yig'indisini ko'rsatish
show_top_processes_cpu_sum = true
```

### CPU, RAM, Disk, Swap, Load, Network

```ini
[CPU]
# CPU monitoringini yoqish
monitor_cpu = true

# CPU threshold (foizda)
cpu_threshold = 90

[RAM]
# RAM threshold (foizda)
ram_threshold = 80

[Disk]
# Disk monitoringini yoqish
monitor_disk = true

# Disk threshold (foizda)
disk_threshold = 90

# Disk yo'li
disk_path = /

[Swap]
# Swap monitoringini yoqish
monitor_swap = true

# Swap threshold (foizda)
swap_threshold = 80

[Load]
# Tizim yuklanishi monitoringini yoqish
monitor_load = true

# Load threshold (foizda)
load_threshold = 80

[Network]
# Tarmoq monitoringini yoqish
monitor_network = true

# Tarmoq interfeysi (bo'sh qoldirilsa avtomatik aniqlanadi)
network_interface = 

# Tarmoq threshold (Mbps)
network_threshold = 90
```

### Database

```ini
[Database]
# Ma'lumotlar bazasini yoqish
db_enabled = false

# Ma'lumotlar bazasi turi (sqlite, mysql, postgresql)
db_type = sqlite

# SQLite uchun fayl yo'li
db_path = /var/lib/system-monitor/metrics.db

# MySQL/PostgreSQL uchun
db_host = localhost
db_port = 3306
db_name = system_monitor
db_user = username
db_password = password
```

### Prometheus

```ini
[Prometheus]
# Prometheus metrikalarini yoqish
prometheus_enabled = false

# Prometheus port
prometheus_port = 9090
```

### AlertFormat

```ini
[AlertFormat]
# Chiroyli formatlashni yoqish
alert_format_enabled = true

# Ramka chizishni yoqish
alert_format_use_box_drawing = true

# Ramka belgilari
alert_format_top_border = ┌────────────────────────────────────────────┐
alert_format_title_border = ├────────────────────────────────────────────┤
alert_format_section_border = ├────────────────────────────────────────────┤
alert_format_bottom_border = └────────────────────────────────────────────┘
alert_format_line_prefix = │ 
alert_format_line_suffix =  │

# Kenglik va tekislash
alert_format_width = 44
alert_format_title_align = center

# Turli bo'limlar uchun emojilar
alert_format_date_emoji = 🗓️
alert_format_ram_emoji = 🧠
alert_format_cpu_emoji = 🔥
alert_format_disk_emoji = 💾
alert_format_top_processes_emoji = 🧾
alert_format_disk_breakdown_emoji = 📁
alert_format_hostname_emoji = 🖥️
alert_format_ip_emoji = 🌐
alert_format_uptime_emoji = ⏳
alert_format_os_emoji = 🐧
alert_format_kernel_emoji = ⚙️

# Ko'rsatiladigan bo'limlar
alert_format_include_system_info = true
alert_format_include_resources = true
alert_format_include_top_processes = true
alert_format_include_disk_breakdown = true
```

## Telegram Bot yaratish

1. Telegram-da [@BotFather](https://t.me/BotFather) ga murojaat qiling
2. `/newbot` buyrug'ini yuboring va ko'rsatmalarga amal qiling
3. Bot yaratilgandan so'ng, bot token oling (masalan, `123456789:ABCdefGhIJKlmnOPQRstUVwxYZ`)
4. Botni guruhga qo'shing yoki bot bilan shaxsiy chat boshlang
5. Chat ID olish uchun quyidagi URL ga o'ting (bot token o'rniga o'zingizning bot tokeningizni qo'ying):
   ```
   https://api.telegram.org/bot123456789:ABCdefGhIJKlmnOPQRstUVwxYZ/getUpdates
   ```
6. Xabar yuboring va URL ni yangilang, keyin JSON javobidan chat ID ni oling
7. Olingan bot token va chat ID ni konfiguratsiya fayliga qo'ying

## Xizmatni boshqarish

Xizmatni ishga tushirish:
```bash
sudo systemctl start system-monitor.service
```

Xizmatni to'xtatish:
```bash
sudo systemctl stop system-monitor.service
```

Xizmat holatini tekshirish:
```bash
sudo systemctl status system-monitor.service
```

Xizmatni qayta ishga tushirish:
```bash
sudo systemctl restart system-monitor.service
```

Loglarni ko'rish:
```bash
sudo tail -f /var/log/system_monitor.log
```

## Prometheus bilan integratsiya

Prometheus metrikalarini yoqish uchun konfiguratsiya faylida `prometheus_enabled = true` ni o'rnating va `prometheus_port` ni sozlang.

Prometheus konfiguratsiyasiga quyidagi scrape konfiguratsiyasini qo'shing:

```yaml
scrape_configs:
  - job_name: 'system_monitor'
    static_configs:
      - targets: ['localhost:9090']
```

## Ma'lumotlar bazasi bilan integratsiya

Ma'lumotlar bazasini yoqish uchun konfiguratsiya faylida `db_enabled = true` ni o'rnating va kerakli ma'lumotlar bazasi parametrlarini sozlang.

### SQLite

SQLite standart Python bilan birga keladi, qo'shimcha o'rnatish talab qilinmaydi.

```ini
[Database]
db_enabled = true
db_type = sqlite
db_path = /var/lib/system-monitor/metrics.db
```

### MySQL

MySQL uchun `mysql-connector-python` paketi kerak bo'ladi:

```bash
pip3 install mysql-connector-python
```

```ini
[Database]
db_enabled = true
db_type = mysql
db_host = localhost
db_port = 3306
db_name = system_monitor
db_user = username
db_password = password
```

### PostgreSQL

PostgreSQL uchun `psycopg2-binary` paketi kerak bo'ladi:

```bash
pip3 install psycopg2-binary
```

```ini
[Database]
db_enabled = true
db_type = postgresql
db_host = localhost
db_port = 5432
db_name = system_monitor
db_user = username
db_password = password
```

## Muammolarni hal qilish

### Telegram xabarlar kelmayapti

1. Bot token va chat ID to'g'ri ekanligini tekshiring
2. Telegram sinov skriptini ishga tushiring:
   ```bash
   sudo system-monitor-test-telegram
   ```
3. Loglarni tekshiring:
   ```bash
   sudo tail -f /var/log/system_monitor.log
   ```

### Xizmat ishga tushmayapti

1. Xizmat holatini tekshiring:
   ```bash
   sudo systemctl status system-monitor.service
   ```
2. Loglarni tekshiring:
   ```bash
   sudo journalctl -u system-monitor.service
   sudo tail -f /var/log/system_monitor.log
   ```
3. Python paketlari o'rnatilganligini tekshiring:
   ```bash
   pip3 list | grep psutil
   pip3 list | grep requests
   ```

## Litsenziya

Bu dastur MIT litsenziyasi ostida tarqatiladi. Batafsil ma'lumot uchun LICENSE faylini ko'ring.
