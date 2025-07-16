import os
import sys
import requests
import time
from urllib.parse import urlparse, quote_plus
from datetime import datetime  # برای زمان به‌روزرسانی

# مسیرهای جدید در پوشه Files
FILES_DIR = 'Files'
TEMPLATE_FILE = os.path.join(FILES_DIR, 'template.yaml')
SUBS_FILE = os.path.join(FILES_DIR, 'subscriptions.txt')
FORMAT_FILE = os.path.join(FILES_DIR, 'format.txt')
OUTPUT_DIR = 'output'
PROVIDERS_DIR = 'providers'
README_FILE = 'README.md'
GITHUB_REPO = os.environ.get('GITHUB_REPOSITORY')

def get_filename_from_url(url):
    """استخراج نام فایل از URL"""
    path = urlparse(url).path
    filename = os.path.basename(path)
    return os.path.splitext(filename)[0]

def update_readme(output_files):
    """به‌روزرسانی فایل README.md با لینک‌های کانفیگ و زمان به‌روزرسانی"""
    if not GITHUB_REPO:
        sys.exit("Critical Error: GITHUB_REPOSITORY environment variable is not set.")

    print(f"Updating README.md for repository: {GITHUB_REPO}")

    # زمان به‌روزرسانی پویا
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %z")
    links_md_content = f"# 📊 نتایج استخراج (آخرین به‌روزرسانی: {current_time})\n\n"
    links_md_content += "این فایل به صورت خودکار ایجاد شده است.\n\n"
    links_md_content += "## 🔗 لینک‌های کانفیگ آماده (Raw)\n\n"
    links_md_content += "برای استفاده، لینک‌های زیر را مستقیما در کلش کپی کنید.\n\n"
    for filename in sorted(output_files):
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{OUTPUT_DIR}/{filename}"
        title = os.path.splitext(filename)[0]
        links_md_content += f"* **{title}**: `{raw_url}`\n"

    try:
        with open(README_FILE, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        sys.exit(f"CRITICAL ERROR: The '{README_FILE}' file was not found.")

    start_marker = "<!-- START_LINKS -->"
    end_marker = "<!-- END_LINKS -->"

    if start_marker not in readme_content or end_marker not in readme_content:
        sys.exit(f"CRITICAL ERROR: Markers not found in {README_FILE}.")

    before_part = readme_content.split(start_marker)[0]
    after_part = readme_content.split(end_marker)[1]

    new_readme_content = (
        before_part + start_marker + "\n\n" +
        links_md_content + "\n" + end_marker + after_part
    )

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(new_readme_content)

    print("README.md updated successfully.")

def main():
    """
    تابع اصلی برای تولید کانفیگ‌ها
    """
    print("Starting robust generation process with retry logic...")
    
    # ایجاد پوشه Files
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROVIDERS_DIR, exist_ok=True)

    try:
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        with open(FORMAT_FILE, 'r', encoding='utf-8') as f:
            format_string = f.read().strip()
            
        if "[URL]" not in format_string:
            print(f"Warning: Placeholder [URL] not found in {FORMAT_FILE}.")
            format_string = "[URL]"
            
    except FileNotFoundError as e:
        sys.exit(f"CRITICAL ERROR: A required file is missing: {e.filename}")

    try:
        with open(SUBS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        sys.exit(f"CRITICAL ERROR: Subscription file '{SUBS_FILE}' not found.")
        
    generated_files = []

    for sub_line in subscriptions:
        custom_name = None
        if ',' in sub_line:
            original_url, custom_name = [part.strip() for part in sub_line.split(',', 1)]
        else:
            original_url = sub_line
        
        file_name_base = custom_name if custom_name else get_filename_from_url(original_url)
        if not file_name_base:
            print(f"Warning: Could not determine a filename for URL: {original_url}. Skipping.")
            continue
        
        wrapped_url = format_string.replace("[URL]", quote_plus(original_url))
        
        print(f"Processing: {original_url}")
        print(f"  -> Wrapped URL: {wrapped_url}")
        
        provider_filename = f"{file_name_base}.txt"
        provider_path = os.path.join(PROVIDERS_DIR, provider_filename)
        
        # منطق تلاش مجدد
        response = None
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = requests.get(wrapped_url, timeout=45)
                response.raise_for_status()
                print(f"  -> Successfully downloaded on attempt {attempt + 1}.")
                break
            except requests.RequestException as e:
                print(f"  -> Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"  -> Waiting for {retry_delay} seconds before retrying...")
                    time.sleep(retry_delay)
                else:
                    print(f"  -> All retries failed. Skipping this subscription.")

        if response is None or not response.ok:
            continue

        with open(provider_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"  -> Successfully saved content to {provider_path}")

        if not GITHUB_REPO:
            continue

        raw_provider_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{provider_path}"
        
        modified_content = template_content
        modified_content = modified_content.replace("%%URL_PLACEHOLDER%%", raw_provider_url)
        modified_content = modified_content.replace("%%PATH_PLACEHOLDER%%", f"./{provider_path}")

        output_filename = f"{file_name_base}.yaml"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
            
        generated_files.append(output_filename)
        print(f"  -> Generated final config: {output_path}\n")

    if generated_files:
        update_readme(generated_files)

if __name__ == "__main__":
    main()
