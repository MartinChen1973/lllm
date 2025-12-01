"""
Web scraper for agicto.com model pricing information.
Fetches model cards from the website and extracts structured data.
Uses Selenium to handle JavaScript-rendered content.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Try to import Selenium, fall back to requests if not available
SELENIUM_AVAILABLE = False
SELENIUM_ERROR = None

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_ERROR = f"Selenium import failed: {e}"
    print(f"ERROR: {SELENIUM_ERROR}")
    print("Install with: pip install selenium webdriver-manager")


def fetch_page(url: str, max_retries: int = 3, use_selenium: bool = True) -> str:
    """
    Fetch HTML content from the URL, waiting for JavaScript to render if needed.
    
    Args:
        url: The URL to fetch
        max_retries: Maximum number of retry attempts
        use_selenium: Whether to use Selenium for JavaScript-rendered pages
        
    Returns:
        HTML content as string (after JavaScript rendering)
        
    Raises:
        requests.RequestException: If the request fails after all retries
    """
    # Use Selenium if available and requested
    if use_selenium:
        if not SELENIUM_AVAILABLE:
            error_msg = f"Selenium不可用: {SELENIUM_ERROR or '未安装'}"
            print(f"ERROR: {error_msg}")
            print("安装命令: pip install selenium webdriver-manager")
            raise Exception(error_msg)
        else:
            try:
                print("正在使用 Selenium 获取页面...")
                return fetch_page_with_selenium(url)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"ERROR: Selenium 获取失败: {e}")
                print(f"详细错误:\n{error_trace}")
                raise Exception(f"Selenium 获取失败: {e}")
    
    # Fallback to requests (won't work for JS-rendered content, but good for error handling)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=(60, 120))
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                print(f"Timeout on attempt {attempt + 1}/{max_retries}, retrying...")
                time.sleep(2 * (attempt + 1))
            else:
                raise requests.RequestException(f"Request timed out after {max_retries} attempts: {e}")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request failed on attempt {attempt + 1}/{max_retries}: {e}, retrying...")
                time.sleep(2 * (attempt + 1))
            else:
                raise


def fetch_page_with_selenium(url: str) -> str:
    """
    Fetch HTML content using Selenium, waiting for JavaScript to render.
    
    Args:
        url: The URL to fetch
        
    Returns:
        HTML content as string after JavaScript rendering
        
    Raises:
        Exception: If Selenium fails to initialize or fetch the page
    """
    print(f"Using Selenium to fetch {url}...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    driver = None
    try:
        # Try to use ChromeDriver with webdriver-manager (recommended)
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager
            print("正在通过 webdriver-manager 安装/检查 ChromeDriver...")
            try:
                driver_path = ChromeDriverManager().install()
                print(f"✓ ChromeDriver 路径: {driver_path}")
                service = ChromeService(driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✓ ChromeDriver 初始化成功")
            except Exception as e:
                error_str = str(e)
                if "chrome" in error_str.lower() and ("not found" in error_str.lower() or "cannot find" in error_str.lower()):
                    raise Exception(f"Chrome 浏览器未找到。请安装 Chrome 浏览器。错误详情: {e}")
                else:
                    raise Exception(f"ChromeDriver 初始化失败: {e}")
        except ImportError:
            # Fallback: assume ChromeDriver is in PATH
            print("webdriver-manager 未安装，尝试从 PATH 查找 ChromeDriver...")
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("✓ ChromeDriver 在 PATH 中找到")
            except Exception as e:
                error_str = str(e)
                if "chromedriver" in error_str.lower():
                    raise Exception(f"ChromeDriver 未找到。请安装: pip install webdriver-manager。错误: {e}")
                elif "chrome" in error_str.lower() and "not found" in error_str.lower():
                    raise Exception(f"Chrome 浏览器未找到。请安装 Chrome 浏览器。")
                else:
                    raise Exception(f"ChromeDriver 初始化失败: {e}")
        except Exception as e:
            error_str = str(e)
            if "chrome" in error_str.lower() and "not found" in error_str.lower():
                raise Exception(f"Chrome 浏览器未找到。请安装 Chrome 浏览器。")
            else:
                raise Exception(f"ChromeDriver 初始化失败: {e}")
        
        print(f"正在加载页面: {url}...")
        try:
            driver.get(url)
            print("✓ 页面加载完成")
        except Exception as e:
            raise Exception(f"无法加载页面: {e}")
        
        # Wait for content to load - wait for ant-col divs or h4 tags to appear
        print("等待页面内容加载（最多30秒）...")
        wait = WebDriverWait(driver, 30)  # Wait up to 30 seconds
        
        content_loaded = False
        try:
            # Wait for ant-col divs to appear (indicates model cards are loaded)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.ant-col")))
            print("✓ 找到 ant-col divs（模型卡片已加载）")
            content_loaded = True
        except TimeoutException:
            print("未找到 ant-col divs，尝试查找 h4 标签...")
            try:
                # Fallback: wait for h4 tags
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h4")))
                print("✓ 找到 h4 标签")
                content_loaded = True
            except TimeoutException:
                # Check what's actually on the page
                page_title = driver.title
                page_url = driver.current_url
                print(f"警告: 等待超时。页面标题: {page_title}, URL: {page_url}")
                
                # Try to find any content
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text[:200]
                    print(f"页面内容预览: {body_text}...")
                except:
                    pass
                
                if not content_loaded:
                    raise Exception("页面内容加载超时。可能原因：1) 网络连接问题 2) 网站结构变化 3) 需要更长的等待时间")
        
        # Additional wait for dynamic content to settle
        print("等待动态内容稳定...")
        time.sleep(2)
        
        # Get the page source after JavaScript has rendered
        html_content = driver.page_source
        print(f"✓ 获取到 {len(html_content)} 字符的 HTML（JavaScript 已渲染）")
        
        # Verify we got meaningful content
        if len(html_content) < 1000:
            raise Exception(f"获取的 HTML 内容过短（{len(html_content)} 字符），可能页面未正确加载")
        
        return html_content
        
    finally:
        if driver:
            driver.quit()
            print("Selenium driver closed")


def parse_pricing(card_element) -> Dict:
    """
    Parse pricing information from a model card.
    Handles three types:
    1. Token-based pricing (input/output per million tokens)
    2. Per-use pricing (fixed price per use)
    3. Image pricing (multiple tiers with different sizes/qualities)
    
    Args:
        card_element: BeautifulSoup element containing the model card
        
    Returns:
        Dictionary with pricing information
    """
    pricing = {"type": None}
    
    # Look for pricing divs
    pricing_divs = card_element.find_all('div', class_=lambda x: x and 'flex items-end' in x)
    
    if not pricing_divs:
        # Check for token-based pricing with "输入：¥X/k" or "输出：¥X/k" format
        all_spans = card_element.find_all('span')
        input_price_k = None
        output_price_k = None
        
        for span in all_spans:
            text = span.get_text(strip=True)
            # Match "输入：¥0.0016/k" or "输入：¥0.0016/K"
            input_match = re.search(r'输入[：:]\s*[¥￥]?\s*([\d.]+)\s*/k', text, re.IGNORECASE)
            if input_match:
                input_price_k = float(input_match.group(1))
            
            # Match "输出：¥0.01/k" or "输出：¥0.01/K"
            output_match = re.search(r'输出[：:]\s*[¥￥]?\s*([\d.]+)\s*/k', text, re.IGNORECASE)
            if output_match:
                output_price_k = float(output_match.group(1))
        
        if input_price_k is not None or output_price_k is not None:
            pricing = {
                "type": "tokens",
                "unit": "k"
            }
            if input_price_k is not None:
                pricing["input"] = {"price": input_price_k, "unit": "k"}
            if output_price_k is not None:
                pricing["output"] = {"price": output_price_k, "unit": "k"}
            return pricing
        
        # Check for per-use pricing in features
        features_spans = card_element.find_all('span', class_=lambda x: x and 'text-red-700' in str(x))
        for span in features_spans:
            text = span.get_text(strip=True)
            if '￥/次' in text or '/次' in text:
                # Extract price
                price_match = re.search(r'([\d.]+)\s*￥/次', text)
                if price_match:
                    pricing = {
                        "type": "per_use",
                        "price": float(price_match.group(1)),
                        "unit": "次"
                    }
                    return pricing
        
        # Check for image pricing: "X/张" format
        for span in all_spans:
            text = span.get_text(strip=True)
            # Match "0.2/张" or similar patterns
            img_match = re.match(r'^([\d.]+)\s*/张$', text)
            if img_match:
                pricing = {
                    "type": "image",
                    "tiers": [{
                        "tier": "default",
                        "price": float(img_match.group(1)),
                        "unit": "张"
                    }]
                }
                return pricing
        
        # Check for image pricing tiers
        image_pricing_spans = card_element.find_all('span', class_=lambda x: x and ('text-blue-700' in str(x) or 
                                                                                    'text-green-700' in str(x) or
                                                                                    'text-yellow-700' in str(x) or
                                                                                    'text-purple-700' in str(x) or
                                                                                    'text-pink-700' in str(x) or
                                                                                    'text-indigo-700' in str(x) or
                                                                                    'text-gray-700' in str(x) or
                                                                                    'text-teal-700' in str(x)))
        if image_pricing_spans:
            tiers = []
            for span in image_pricing_spans:
                text = span.get_text(strip=True)
                # Match pattern like "low-1024x1024：0.0803￥/张"
                match = re.match(r'([^：]+)：([\d.]+)￥/张', text)
                if match:
                    tiers.append({
                        "tier": match.group(1).strip(),
                        "price": float(match.group(2)),
                        "unit": "张"
                    })
            if tiers:
                pricing = {
                    "type": "image",
                    "tiers": tiers
                }
                return pricing
        
        return pricing
    
    # Parse token-based pricing (input/output)
    input_price = None
    output_price = None
    
    for div in pricing_divs:
        # Look for "输入" or "输出" labels
        input_label = div.find('span', string=lambda x: x and '输入' in str(x))
        output_label = div.find('span', string=lambda x: x and '输出' in str(x))
        
        # Extract price value
        price_spans = div.find_all('span', class_=lambda x: x and 'text-2xl' in str(x))
        if price_spans:
            price_text = price_spans[0].get_text(strip=True)
            try:
                price_value = float(price_text)
                
                if input_label or (div.find_parent() and '输入' in div.find_parent().get_text()):
                    input_price = price_value
                elif output_label or (div.find_parent() and '输出' in div.find_parent().get_text()):
                    output_price = price_value
            except ValueError:
                pass
    
    # Get unit information
    unit_text = ""
    unit_spans = card_element.find_all('span', string=lambda x: x and '/百万tokens' in str(x))
    if unit_spans:
        unit_text = unit_spans[0].get_text(strip=True)
    
    if input_price is not None or output_price is not None:
        pricing = {
            "type": "tokens",
            "unit": unit_text if unit_text else "百万tokens"
        }
        if input_price is not None:
            pricing["input"] = {"price": input_price, "unit": pricing["unit"]}
        if output_price is not None:
            pricing["output"] = {"price": output_price, "unit": pricing["unit"]}
    
    return pricing


def parse_model_card(card_element) -> Optional[Dict]:
    """
    Extract data from a single model card element.
    Handles both <a> tags (old structure) and <div> elements (new structure).
    
    Args:
        card_element: BeautifulSoup element containing the model card (<a> or <div>)
        
    Returns:
        Dictionary with model data, or None if parsing fails
    """
    try:
        # Extract model name from <h4> tag
        # Try multiple ways to find h4 tag
        h4_tag = card_element.find('h4', class_=lambda x: x and 'text-[#140E35]' in str(x))
        if not h4_tag:
            # Try finding any h4 tag
            h4_tag = card_element.find('h4')
        if not h4_tag:
            print(f"  Debug: No h4 tag found in card element")
            return None
        
        model_name = h4_tag.get_text(strip=True)
        if not model_name:
            print(f"  Debug: h4 tag found but no text content")
            return None
        
        # Extract model URL from href attribute
        # If card_element is an <a> tag, get href directly
        # If it's a <div>, find the <a> tag inside it (could be nested in .btn div)
        model_url = ''
        if card_element.name == 'a':
            model_url = card_element.get('href', '')
        else:
            # Find <a> tag inside the div - look for href="/model/..."
            a_tag = card_element.find('a', href=lambda x: x and x.startswith('/model/'))
            if a_tag:
                model_url = a_tag.get('href', '')
            else:
                # Try to find any <a> tag and check its href
                all_a_tags = card_element.find_all('a')
                for a in all_a_tags:
                    href = a.get('href', '')
                    if href.startswith('/model/'):
                        model_url = href
                        break
        
        # Extract features from badge spans
        features = []
        # Look for feature badges (support text/image, context length, etc.)
        feature_spans = card_element.find_all('span', class_=lambda x: x and ('bg-[#b1e2ff]' in str(x) or 
                                                                              'text-red-700' in str(x) or
                                                                              'text-blue-700' in str(x) or
                                                                              'text-green-700' in str(x) or
                                                                              'text-yellow-700' in str(x) or
                                                                              'text-purple-700' in str(x) or
                                                                              'text-pink-700' in str(x) or
                                                                              'text-indigo-700' in str(x) or
                                                                              'text-gray-700' in str(x) or
                                                                              'text-teal-700' in str(x)))
        
        for span in feature_spans:
            text = span.get_text(strip=True)
            if text and text not in features:
                # Always include context length
                if '上下文长度' in text:
                    features.append(text)
                    continue
                
                # Skip error features
                if text == '逆' or text == '支持':
                    continue
                
                # Skip pricing patterns
                is_pricing = (
                    '￥' in text or '¥' in text or  # Contains currency symbol
                    bool(re.search(r'输入[：:]', text)) or  # Contains "输入："
                    bool(re.search(r'输出[：:]', text)) or  # Contains "输出："
                    bool(re.search(r'/\s*(张|k|K|次)', text)) or  # Contains "/张", "/k", "/次"
                    bool(re.match(r'^[\d.]+\s*/张$', text))  # Matches "0.2/张"
                )
                
                # Only add if it's not pricing
                if not is_pricing:
                    features.append(text)
        
        # Extract pricing information
        pricing = parse_pricing(card_element)
        
        # Extract provider name
        provider = ""
        provider_div = card_element.find('div', class_=lambda x: x and 'group-hover:hidden' in str(x) and 'items-center' in str(x))
        if provider_div:
            provider_img = provider_div.find('img')
            provider_text = provider_div.find('span', class_=lambda x: x and 'text-[12px]' in str(x))
            if provider_text:
                provider = provider_text.get_text(strip=True)
            elif provider_img and provider_img.get('alt'):
                provider = provider_img.get('alt')
        
        return {
            "name": model_name,
            "url": model_url,
            "features": features,
            "pricing": pricing,
            "provider": provider
        }
    
    except (AttributeError, ValueError, KeyError) as e:
        print(f"Error parsing model card: {e}")
        return None


def extract_all_models(html_content: str) -> List[Dict]:
    """
    Find all model card elements and parse each.
    Handles both old structure (<a> tags) and new structure (<div> containing <a> tags).
    
    Args:
        html_content: HTML content as string
        
    Returns:
        List of dictionaries containing model data
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Debug: Check what's actually in the HTML
    html_lower = html_content.lower()
    if 'react' in html_lower or 'vue' in html_lower or 'angular' in html_lower:
        print("Warning: Page might be JavaScript-rendered. Content may not be in initial HTML.")
    
    # Debug: Check for ant-col in the raw HTML
    if 'ant-col' in html_content:
        print("Found 'ant-col' string in raw HTML")
    else:
        print("'ant-col' NOT found in raw HTML - content likely loaded via JavaScript")
    
    # Debug: Check for model-related content
    if '/model/' in html_content:
        print("Found '/model/' in raw HTML")
    else:
        print("'/model/' NOT found in raw HTML")
    
    # Debug: Check for h4 tags
    all_h4 = soup.find_all('h4')
    print(f"Found {len(all_h4)} total <h4> tags in parsed HTML")
    if len(all_h4) > 0:
        print("Sample h4 tags:")
        for i, h4 in enumerate(all_h4[:3]):
            print(f"  {i+1}. Text: '{h4.get_text(strip=True)}', Classes: {h4.get('class', [])}")
    
    # Debug: Check all divs and their classes
    all_divs = soup.find_all('div')
    print(f"Found {len(all_divs)} total <div> tags")
    
    # Check how classes are stored - BeautifulSoup can store them as list or string
    ant_col_count = 0
    for div in all_divs[:100]:  # Check first 100 divs
        classes = div.get('class', [])
        if classes:
            class_str = ' '.join(classes) if isinstance(classes, list) else str(classes)
            if 'ant-col' in class_str:
                ant_col_count += 1
                if ant_col_count <= 3:
                    print(f"  Found ant-col div #{ant_col_count}: classes={classes}")
    
    model_cards = []
    seen_cards = set()  # Track cards we've already added to avoid duplicates
    
    # Strategy 1: Find divs with ant-col classes that contain h4 tags (new structure)
    # BeautifulSoup stores classes as a list, so we need to check properly
    ant_col_divs = soup.find_all('div', class_=lambda x: x and ('ant-col' in x if isinstance(x, list) else 'ant-col' in str(x)))
    print(f"Found {len(ant_col_divs)} divs with 'ant-col' classes (using find_all)")
    
    for div in ant_col_divs:
        # Check if this div contains an h4 tag (model name)
        h4_tag = div.find('h4')
        if h4_tag:
            # Check if it also contains an <a> tag with /model/ href
            a_tag = div.find('a', href=lambda x: x and x.startswith('/model/'))
            if a_tag and div not in seen_cards:
                model_cards.append(div)
                seen_cards.add(div)
                print(f"Found model card in ant-col div: {h4_tag.get_text(strip=True)}")
    
    # Strategy 2: If no ant-col divs found, try finding divs with "relative flex flex-col" classes
    if not model_cards:
        relative_divs = soup.find_all('div', class_=lambda x: x and isinstance(x, (list, str)) and 'relative' in str(x) and 'flex' in str(x) and 'flex-col' in str(x))
        print(f"Found {len(relative_divs)} divs with 'relative flex flex-col' classes")
        
        for div in relative_divs:
            h4_tag = div.find('h4')
            if h4_tag:
                # Find parent div that might contain the <a> tag
                parent = div.find_parent('div')
                while parent:
                    a_tag = parent.find('a', href=lambda x: x and x.startswith('/model/'))
                    if a_tag and parent not in seen_cards:
                        model_cards.append(parent)
                        seen_cards.add(parent)
                        print(f"Found model card in relative div parent: {h4_tag.get_text(strip=True)}")
                        break
                    parent = parent.find_parent('div')
    
    # Strategy 3: Fallback - find all <a> tags with /model/ href and find their parent divs
    if not model_cards:
        a_tags = soup.find_all('a', href=lambda x: x and x.startswith('/model/'))
        print(f"Found {len(a_tags)} <a> tags with /model/ href (fallback)")
        
        for a_tag in a_tags:
            # Find parent div that contains both this <a> and an h4
            parent = a_tag.find_parent('div')
            while parent:
                h4_tag = parent.find('h4')
                if h4_tag and parent not in seen_cards:
                    model_cards.append(parent)
                    seen_cards.add(parent)
                    print(f"Found model card via <a> tag parent: {h4_tag.get_text(strip=True)}")
                    break
                parent = parent.find_parent('div')
    
    print(f"Total model cards found: {len(model_cards)}")
    
    models = []
    for card in model_cards:
        model_data = parse_model_card(card)
        if model_data:
            models.append(model_data)
        else:
            print(f"Failed to parse a model card")
    
    return models


def main():
    """
    Orchestrate fetching, parsing, and saving JSON.
    """
    url = "https://agicto.com/model?companyId=0&typeId=0&freeType=0"
    
    print(f"Fetching page: {url}")
    try:
        html_content = fetch_page(url)
        print("Page fetched successfully")
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return
    
    print("Extracting model data...")
    models = extract_all_models(html_content)
    print(f"Found {len(models)} models")
    
    # Create output dictionary
    output = {
        "models": models
    }
    
    # Save to JSON file in the same directory as the script
    script_dir = Path(__file__).parent
    output_file = script_dir / "agicto_models.json"
    
    print(f"Saving to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully saved {len(models)} models to {output_file}")


if __name__ == "__main__":
    main()

