import requests
import os
import re
from datetime import datetime
import pytz

# مسیر فایل‌ها
SUBSCRIPTIONS_FILE = os.path.join('Files', 'subscriptions.txt')
FORMAT_FILE = os.path.join('Files', 'format.txt')
TEMPLATE_FILE = os.path.join('Files', 'template.yaml')
PROVIDERS_DIR = 'providers'
OUTPUT_DIR = 'output'
GITHUB_REPO = os.environ.get('GITHUB_REPOSITORY')

# ایجاد پوشه‌ها
os.makedirs(PROVIDERS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# خواندن فایل قالب
with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
    template_content = f.read()

# خواندن فایل فرمت
with open(FORMAT_FILE, 'r', encoding='utf-8') as f:
    url_format = f.read().strip()

# خواندن فایل subscriptions
with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
    subscriptions = [line.strip() for line in f if line.strip() and not line.startswith('#')]

def fetch_configs(url, max_retries=3):
    """دریافت کانفیگ‌ها از URL با تلاش مجدد"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text.splitlines()
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt + 1 == max_retries:
                print(f"Failed to fetch {url} after {max_retries} attempts.")
                return []
    return []

def process_subscription(subscription):
    """پردازش یک URL اشتراک"""
    if ',' in subscription:
        url, name = subscription.rsplit(',', 1)
    else:
        url = subscription
        name = re.sub(r'[^a-zA-Z0-9_-]', '_', url.split('/')[-1].split('.')[0])
    
    # تولید URL نهایی
    final_url = url_format.replace('[URL]', url)
    print(f"Processing: {url}")
    print(f"  -> Wrapped URL: {final_url}")
    
    # دریافت کانفیگ‌ها
    configs = fetch_configs(final_url)
    if not configs:
        print(f"  -> No configs retrieved for {url}")
        return None, None
    
    print(f"  -> Successfully downloaded on attempt 1.")
    
    # ذخیره فایل ارائه‌دهنده
    provider_filename = f"{name}.txt"
    provider_path = os.path.join(PROVIDERS_DIR, provider_filename)
    with open(provider_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(configs))
    print(f"  -> Successfully saved content to {provider_path}")
    
    # تولید فایل YAML
    yaml_content = template_content
    yaml_content = yaml_content.replace("%%URL_PLACEHOLDER%%", f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{provider_path}")
    yaml_content = yaml_content.replace("%%PATH_PLACEHOLDER%%", f"./{provider_path}")
    
    yaml_filename = f"{name}.yaml"
    yaml_path = os.path.join(OUTPUT_DIR, yaml_filename)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    print(f"  -> Generated final config: {yaml_path}")
    
    return name, yaml_path

def update_readme():
    """به‌روزرسانی README با لینک‌های output"""
    if not GITHUB_REPO:
        print("Warning: GITHUB_REPOSITORY not set. README update skipped.")
        return

    iran_tz = pytz.timezone('Asia/Tehran')
    current_time = datetime.now(iran_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    readme_content = f"""
# 🚀 ClashFactory: کانفیگ‌های Clash Meta

**ClashFactory** ابزاری خودکار برای تولید و به‌روزرسانی کانفیگ‌های Clash Meta است. این پروژه با دریافت URLهای اشتراک از منابع معتبر، فایل‌های YAML آماده‌ای تولید می‌کند که به‌راحتی در کلاینت Clash Meta قابل استفاده هستند. کانفیگ‌ها بر اساس کشورها تفکیک شده‌اند تا انتخاب سرور موردنظر شما ساده‌تر شود.

**آخرین به‌روزرسانی**: {current_time} به وقت ایران

---

## ✨ ویژگی‌های پروژه
- 🛠 **تولید خودکار**: تبدیل URLهای اشتراک به فایل‌های YAML سازگار با Clash Meta.
- 🌍 **تفکیک بر اساس کشورها**: ارائه کانفیگ‌های جداگانه برای هر کشور (مانند `Iran.yaml`، `USA.yaml`).
- 🔄 **به‌روزرسانی روزانه**: اجرای خودکار با GitHub Actions برای اطمینان از تازگی کانفیگ‌ها.
- 📋 **دسترسی آسان**: لینک‌های خام (Raw) برای کپی مستقیم در کلاینت Clash Meta.

---

## 🔗 لینک‌های کانفیگ آماده (Raw)
لینک‌های زیر را در کلاینت Clash Meta کپی کنید تا به سرورهای موردنظر متصل شوید:

"""
    excluded_configs = ['Iran.yaml', 'UK.yaml', 'USA.yaml']
    for filename in sorted(os.listdir(OUTPUT_DIR)):
        if filename.endswith('.yaml') and filename not in excluded_configs:
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/output/{filename}"
            title = os.path.splitext(filename)[0]
            readme_content += f"- **{title}**: `{raw_url}`\n"

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
    print("README.md updated successfully (main.py).")

if __name__ == "__main__":
    print("Starting robust generation process with retry logic...")
    for subscription in subscriptions:
        process_subscription(subscription)
    update_readme()
