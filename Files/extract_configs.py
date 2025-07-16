import json
import re
import os
from datetime import datetime
import pytz

# مسیر فایل‌ها
COUNTRIES_PROTOCOLS_FILE = os.path.join('Files', 'countries_protocols.json')
PROVIDERS_DIR = 'providers'
CONFIGS_DIR = 'configs'
TEMPLATE_FILE = os.path.join('Files', 'template.yaml')
GITHUB_REPO = os.environ.get('GITHUB_REPOSITORY')

# خواندن فایل JSON
with open(COUNTRIES_PROTOCOLS_FILE, 'r', encoding='utf-8') as f:
    countries_protocols = json.load(f)

# خواندن فایل قالب
with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
    template_content = f.read()

# ایجاد پوشه configs
os.makedirs(CONFIGS_DIR, exist_ok=True)

def extract_configs():
    """استخراج کانفیگ‌ها بر اساس کشورها و تولید فایل‌های YAML"""
    country_files = {country: [] for country in countries_protocols if country not in ['Vmess', 'Vless', 'Trojan', 'ShadowSocks', 'ShadowSocksR', 'Tuic', 'Hysteria2', 'WireGuard']}

    # خواندن فایل‌های ارائه‌دهنده
    for provider_file in os.listdir(PROVIDERS_DIR):
        provider_path = os.path.join(PROVIDERS_DIR, provider_file)
        with open(provider_path, 'r', encoding='utf-8') as f:
            content = f.read().splitlines()

        for line in content:
            # فیلتر کردن کانفیگ‌های نامعتبر
            if '%25' in line or len(line) > 500:
                continue

            # بررسی کشورها
            for country, identifiers in countries_protocols.items():
                if country not in ['Vmess', 'Vless', 'Trojan', 'ShadowSocks', 'ShadowSocksR', 'Tuic', 'Hysteria2', 'WireGuard']:
                    for identifier in identifiers:
                        if identifier.lower() in line.lower():
                            country_files[country].append(line)
                            break

    # ذخیره فایل‌های کشور به‌صورت YAML
    for country, configs in country_files.items():
        if configs:
            # تولید محتوای YAML
            provider_filename = f"{country}.txt"
            provider_path = os.path.join(PROVIDERS_DIR, provider_filename)
            raw_provider_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{provider_path}"
            
            # ذخیره کانفیگ‌ها به‌صورت متنی در providers
            with open(provider_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(configs))

            # جایگزینی placeholderها در قالب
            yaml_content = template_content
            yaml_content = yaml_content.replace("%%URL_PLACEHOLDER%%", raw_provider_url)
            yaml_content = yaml_content.replace("%%PATH_PLACEHOLDER%%", f"./{provider_path}")

            # ذخیره فایل YAML
            yaml_filename = f"{country}.yaml"
            yaml_path = os.path.join(CONFIGS_DIR, yaml_filename)
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

def update_readme_with_countries():
    """به‌روزرسانی README با لینک‌های کانفیگ آماده و جدول کشورها"""
    if not GITHUB_REPO:
        print("Warning: GITHUB_REPOSITORY not set. README links may not work.")
        return

    # محاسبه زمان به وقت ایران
    iran_tz = pytz.timezone('Asia/Tehran')
    current_time = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M:%S")

    # محتوای README
    readme_content = f"""
# 🚀 ClashFactory: کانفیگ‌های Clash Meta

**ClashFactory** ابزاری خودکار برای تولید و به‌روزرسانی کانفیگ‌های Clash Meta است. این پروژه با دریافت URLهای اشتراک از منابع معتبر، فایل‌های YAML آماده‌ای تولید می‌کند که به‌راحتی در کلاینت Clash Meta قابل استفاده هستند. کانفیگ‌ها بر اساس کشورها تفکیک شده‌اند تا انتخاب سرور موردنظر شما ساده‌تر شود.

**آخرین به‌روزرسانی**: {current_time} به وقت ایران

---

## ✨ ویژگی‌های پروژه
- 🛠 **تولید خودکار**: تبدیل URLهای اشتراک به فایل‌های YAML سازگار با Clash Meta.
- 🌍 **تفکیک بر اساس کشورها**: ارائه کانفیگ‌های جداگانه برای هر کشور.
- 🔄 **به‌روزرسانی روزانه**: اجرای خودکار با GitHub Actions برای اطمینان از تازگی کانفیگ‌ها.
- 📋 **دسترسی آسان**: لینک‌های خام (Raw) برای کپی مستقیم در کلاینت Clash Meta.

---

## 🔗 لینک‌های کانفیگ آماده (Raw)
لینک‌های زیر را در کلاینت Clash Meta کپی کنید تا به سرورهای موردنظر متصل شوید:

"""
    for filename in sorted(os.listdir('output')):
        if filename.endswith('.yaml'):
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/output/{filename}"
            title = os.path.splitext(filename)[0]
            readme_content += f"- **{title}**: `{raw_url}`\n"

    readme_content += """
---

## 🌍 کانفیگ‌های کشورها
جدول زیر شامل فایل‌های YAML برای هر کشور است. تعداد کانفیگ‌های موجود در هر فایل نمایش داده شده است.

| کشور | تعداد کانفیگ | لینک |
|:-:|:-:|:-:|
"""
    for country in sorted(countries_protocols.keys()):
        if country in ['Vmess', 'Vless', 'Trojan', 'ShadowSocks', 'ShadowSocksR', 'Tuic', 'Hysteria2', 'WireGuard']:
            continue
        file_path = os.path.join(PROVIDERS_DIR, f"{country}.txt")
        count = len(open(file_path, 'r', encoding='utf-8').readlines()) if os.path.exists(file_path) else 0
        if count > 0:
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{CONFIGS_DIR}/{country}.yaml"
            flag_url = f"https://flagcdn.com/w20/{countries_protocols[country][1].lower()}.png"
            country_name = countries_protocols[country][2]
            readme_content += f"| <img src=\"{flag_url}\" width=\"20\" alt=\"{country} flag\"> {country} ({country_name}) | {count} | [`{country}.yaml`]({raw_url}) |\n"

    readme_content += """
---

### 🛠 راهنمای استفاده
1. لینک موردنظر را از بخش‌های بالا کپی کنید.
2. در کلاینت Clash Meta، لینک را در بخش **Subscriptions** وارد کنید.
3. کانفیگ‌ها به‌صورت خودکار بارگذاری و آماده استفاده می‌شوند.

### 📬 تماس و پشتیبانی
برای گزارش مشکلات یا پیشنهادات، به [صفحه Issues مخزن](https://github.com/{GITHUB_REPO}/issues) مراجعه کنید.

*تولید شده با ❤️ توسط ClashFactory*
"""

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("README.md updated successfully.")

if __name__ == "__main__":
    extract_configs()
    update_readme_with_countries()
