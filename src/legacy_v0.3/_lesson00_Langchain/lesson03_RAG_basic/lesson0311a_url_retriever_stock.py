# 1. 从百度搜索页面提取指定class的div元素（使用Selenium等待JavaScript加载）

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import os
import webbrowser

# 百度搜索页面的URL
url = "https://www.baidu.com/s?wd=%E4%B8%8A%E8%AF%81%E6%8C%87%E6%95%B0&rsv_spt=1&rsv_iqid=0x959ee4d0000068ad&issp=1&f=8&rsv_bp=1&rsv_idx=2&ie=utf-8&rqlang=cn&tn=68018901_16_pg&rsv_dl=tb&rsv_enter=1&oq=%25E7%2599%25BE%25E5%25BA%25A6%25E6%258C%2587%25E6%2595%25B0&rsv_btype=t&inputT=48202&rsv_t=bf5cI%2FkJ5NUZLOoyAuFVgeQj6%2Fcg%2F2VCUt7QeRVli5XDE28Sofao052xM5ZGMcVRbpFummE&rsv_sug3=10&rsv_sug1=6&rsv_sug7=100&rsv_pq=cddc5f4800003ea0&prefixsug=%25E7%2599%25BE%25E5%25BA%25A6%25E6%258C%2587%25E6%2595%25B0&rsp=3&rsv_sug4=48202"

# 配置Chrome选项
chrome_options = Options()
chrome_options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

# 创建WebDriver实例
driver = webdriver.Chrome(options=chrome_options)

try:
    # 打开网页
    driver.get(url)
    
    # 等待页面加载，直到找到目标div元素（等待"加载中..."消失）
    wait = WebDriverWait(driver, 20)
    # 等待包含指定class的div出现，并且文本内容不是"加载中..."
    wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, 'div.fold_2sM3F.animationBox_1c8uQ.small_71Gtb.container_4yQ84') and 
               '加载中' not in d.find_element(By.CSS_SELECTOR, 'div.fold_2sM3F.animationBox_1c8uQ.small_71Gtb.container_4yQ84').text)
    
    # 额外等待一下，确保内容完全加载
    time.sleep(2)
    
    # 找到包含"成分代码"的div元素（使用Selenium定位，以便后续悬停）
    component_element = None
    component_divs = driver.find_elements(By.CSS_SELECTOR, 'div.fold_2sM3F.animationBox_1c8uQ.small_71Gtb.container_4yQ84')
    print(f"找到 {len(component_divs)} 个匹配的div元素")
    for div in component_divs:
        if '成分代码' in div.text:
            component_element = div
            print("找到包含'成分代码'的元素")
            break
    
    # 如果找到元素，执行鼠标悬停操作以显示更多内容
    if component_element:
        try:
            # 滚动到元素可见
            driver.execute_script("arguments[0].scrollIntoView(true);", component_element)
            time.sleep(0.5)
            
            # 模拟鼠标悬停
            actions = ActionChains(driver)
            actions.move_to_element(component_element).perform()
            
            # 等待内容加载（悬停后可能需要时间加载更多股票）
            time.sleep(2)
            
            # 可以尝试多次悬停或等待，确保所有内容都加载
            # 等待直到股票数量不再增加
            previous_count = 0
            for _ in range(5):  # 最多尝试5次
                current_text = component_element.text
                current_count = current_text.count('SH') + current_text.count('SZ')
                if current_count == previous_count and current_count > 0:
                    break  # 数量不再变化，说明加载完成
                previous_count = current_count
                time.sleep(1)
        except Exception as e:
            print(f"悬停操作出现异常（继续执行）: {e}")
    
    # 重新获取页面源码（悬停后内容可能已更新）
    page_source = driver.page_source
    
    # 使用BeautifulSoup解析
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # 查找class同时包含"fold_2sM3F"、"animationBox_1c8uQ"、"small_71Gtb"和"container_4yQ84"的div元素
    divs = soup.find_all('div', class_=['fold_2sM3F', 'animationBox_1c8uQ', 'small_71Gtb', 'container_4yQ84'])
    print(f"BeautifulSoup找到 {len(divs)} 个匹配的div元素")
    
    # 查找包含"成分代码"的div元素
    component_div = None
    for div in divs:
        text_content = div.get_text(strip=True)
        if '成分代码' in text_content:
            component_div = div
            print("BeautifulSoup找到包含'成分代码'的元素")
            break
    
    # 如果Selenium没找到，但BeautifulSoup找到了，重新用Selenium查找一次
    if not component_element and component_div:
        print("尝试重新用Selenium查找元素...")
        component_divs = driver.find_elements(By.CSS_SELECTOR, 'div.fold_2sM3F.animationBox_1c8uQ.small_71Gtb.container_4yQ84')
        for div in component_divs:
            if '成分代码' in div.text:
                component_element = div
                print("重新找到包含'成分代码'的元素")
                break
    
    # 如果找到元素，提取完整的HTML并创建完整的HTML文档
    if component_element:
        # 获取完整的HTML（包括div本身及其所有子元素）
        div_html = component_element.get_attribute('outerHTML')
    elif component_div:
        # 如果Selenium没找到，但BeautifulSoup找到了，使用BeautifulSoup的HTML
        print("使用BeautifulSoup提取的HTML")
        div_html = str(component_div)
    else:
        div_html = None
    
    if div_html:
        # 提取页面中的CSS样式（从style标签）
        style_contents = []
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            style_content = style_tag.string if style_tag.string else style_tag.get_text()
            if style_content:
                style_contents.append(style_content)
        
        # 提取link标签中的CSS引用
        css_links = []
        link_tags = soup.find_all('link', rel='stylesheet')
        for link_tag in link_tags:
            href = link_tag.get('href', '')
            if href:
                # 如果是相对路径，转换为绝对路径
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://www.baidu.com' + href
                elif not href.startswith('http'):
                    href = 'https://www.baidu.com/' + href
                css_links.append(f'    <link rel="stylesheet" href="{href}">')
        
        # 提取script标签中的JS引用
        js_scripts = []
        script_tags = soup.find_all('script', src=True)
        for script_tag in script_tags:
            src = script_tag.get('src', '')
            if src:
                # 如果是相对路径，转换为绝对路径
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.baidu.com' + src
                elif not src.startswith('http'):
                    src = 'https://www.baidu.com/' + src
                js_scripts.append(f'    <script src="{src}"></script>')
        
        # 提取元素及其所有子元素使用的CSS类，确保相关样式都被包含
        used_classes = set()
        if component_element:
            try:
                # 获取元素及其所有子元素的类名
                all_classes = driver.execute_script("""
                    var element = arguments[0];
                    var classes = new Set();
                    function collectClasses(el) {
                        if (el.className && typeof el.className === 'string') {
                            el.className.split(' ').forEach(function(cls) {
                                if (cls.trim()) classes.add(cls.trim());
                            });
                        }
                        for (var i = 0; i < el.children.length; i++) {
                            collectClasses(el.children[i]);
                        }
                    }
                    collectClasses(element);
                    return Array.from(classes);
                """, component_element)
                used_classes = set(all_classes)
                print(f"提取到 {len(used_classes)} 个CSS类")
            except Exception as e:
                print(f"提取CSS类时出现异常: {e}")
        
        # 从页面样式中提取相关类的样式规则
        relevant_styles = []
        if used_classes and style_contents:
            import re
            for style_content in style_contents:
                # 查找包含这些类的样式规则
                for cls in used_classes:
                    # 匹配类选择器（.classname）的样式规则
                    pattern = rf'\.{re.escape(cls)}[^{{]*\{{[^}}]*\}}'
                    matches = re.findall(pattern, style_content, re.DOTALL)
                    relevant_styles.extend(matches)
        
        # 去重并合并相关样式
        if relevant_styles:
            unique_styles = '\n'.join(set(relevant_styles))
            style_contents.append(unique_styles)
        
        # 创建完整的HTML文档，保持原始页面的样式
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票成分代码信息</title>
{chr(10).join(css_links)}
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f5f5f5;
        }}
{chr(10).join(style_contents)}
    </style>
</head>
<body>
        {div_html}
{chr(10).join(js_scripts)}
</body>
</html>"""
        
        # 保存HTML文件
        output_file = 'stock_component_info.html'
        file_path = os.path.abspath(output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML文件已保存到: {file_path}")
        
        # 使用系统默认浏览器打开HTML文件
        file_url = f"file:///{file_path.replace(os.sep, '/')}"
        webbrowser.open(file_url)
        print("已在浏览器中打开HTML文件")
    else:
        print("未找到包含'成分代码'的div元素")
        
finally:
    # 关闭浏览器
    driver.quit()
