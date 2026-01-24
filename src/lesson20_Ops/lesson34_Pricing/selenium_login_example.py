"""
Selenium 登录网站并爬取内容的示例
演示多种登录和认证方法
"""

import json
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup


class WebScraperWithLogin:
    """支持登录的网页爬虫类"""
    
    def __init__(self, headless: bool = True, cookies_file: Optional[str] = None):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            cookies_file: Cookies 文件路径（用于保存/加载登录状态）
        """
        self.cookies_file = cookies_file
        self.driver = None
        self.session = requests.Session()
        self._setup_driver(headless)
    
    def _setup_driver(self, headless: bool):
        """设置 Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    # ⬇️ 方法1: 使用 Selenium 通过登录界面登录
    def login_with_selenium(self, login_url: str, username: str, password: str, 
                           username_selector: str, password_selector: str, 
                           submit_selector: str, wait_after_login: int = 3) -> bool:
        """
        使用 Selenium 通过登录界面登录
        
        Args:
            login_url: 登录页面 URL
            username: 用户名
            password: 密码
            username_selector: 用户名输入框的 CSS 选择器
            password_selector: 密码输入框的 CSS 选择器
            submit_selector: 提交按钮的 CSS 选择器
            wait_after_login: 登录后等待时间（秒）
            
        Returns:
            是否登录成功
        """
        try:
            print(f"正在访问登录页面: {login_url}")
            self.driver.get(login_url)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            
            # 输入用户名
            print("正在输入用户名...")
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, username_selector))
            )
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(0.5)
            
            # 输入密码
            print("正在输入密码...")
            password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)
            
            # 点击登录按钮
            print("正在提交登录表单...")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, submit_selector)
            submit_button.click()
            
            # 等待登录完成
            print(f"等待 {wait_after_login} 秒以确保登录完成...")
            time.sleep(wait_after_login)
            
            # 检查是否登录成功（可以通过检查 URL 变化或特定元素出现来判断）
            current_url = self.driver.current_url
            print(f"当前 URL: {current_url}")
            
            # 保存 cookies
            if self.cookies_file:
                self.save_cookies()
            
            return True
            
        except TimeoutException as e:
            print(f"登录超时: {e}")
            return False
        except NoSuchElementException as e:
            print(f"找不到登录元素: {e}")
            return False
        except Exception as e:
            print(f"登录失败: {e}")
            return False
    
    # ⬇️ 方法2: 保存 cookies 到文件
    def save_cookies(self, file_path: Optional[str] = None):
        """保存当前浏览器的 cookies 到文件"""
        file_path = file_path or self.cookies_file
        if not file_path:
            print("未指定 cookies 文件路径")
            return
        
        cookies = self.driver.get_cookies()
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"Cookies 已保存到: {file_path}")
    
    # ⬇️ 方法3: 从文件加载 cookies
    def load_cookies(self, file_path: Optional[str] = None) -> bool:
        """
        从文件加载 cookies 到浏览器
        
        Args:
            file_path: Cookies 文件路径
            
        Returns:
            是否成功加载
        """
        file_path = file_path or self.cookies_file
        if not file_path or not Path(file_path).exists():
            print(f"Cookies 文件不存在: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # 先访问网站域名（必须访问后才能设置 cookies）
            if cookies:
                # 从第一个 cookie 获取域名
                domain = cookies[0].get('domain', '')
                if domain:
                    # 访问域名主页
                    self.driver.get(f"https://{domain.lstrip('.')}")
                    time.sleep(1)
            
            # 添加 cookies
            for cookie in cookies:
                try:
                    # 移除可能导致问题的字段
                    cookie.pop('sameSite', None)
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加 cookie 失败（跳过）: {e}")
            
            print(f"Cookies 已从 {file_path} 加载")
            return True
            
        except Exception as e:
            print(f"加载 cookies 失败: {e}")
            return False
    
    # ⬇️ 方法4: 使用已保存的 cookies 直接访问（无需登录界面）
    def access_with_saved_cookies(self, target_url: str, cookies_file: Optional[str] = None) -> bool:
        """
        使用已保存的 cookies 直接访问目标页面（跳过登录界面）
        
        Args:
            target_url: 目标页面 URL
            cookies_file: Cookies 文件路径
            
        Returns:
            是否成功访问
        """
        cookies_file = cookies_file or self.cookies_file
        if not cookies_file:
            print("未指定 cookies 文件")
            return False
        
        try:
            # 先访问目标网站的主页或登录页（用于设置 cookies）
            from urllib.parse import urlparse
            parsed_url = urlparse(target_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            print(f"正在访问基础 URL: {base_url}")
            self.driver.get(base_url)
            time.sleep(1)
            
            # 加载 cookies
            if not self.load_cookies(cookies_file):
                return False
            
            # 刷新页面使 cookies 生效
            self.driver.refresh()
            time.sleep(2)
            
            # 访问目标页面
            print(f"正在访问目标页面: {target_url}")
            self.driver.get(target_url)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"使用 cookies 访问失败: {e}")
            return False
    
    # ⬇️ 方法5: 使用 requests + cookies（更高效，无需浏览器）
    def scrape_with_requests_and_cookies(self, target_url: str, 
                                        cookies_file: Optional[str] = None) -> Optional[str]:
        """
        使用 requests 库 + cookies 爬取内容（比 Selenium 更快）
        
        Args:
            target_url: 目标页面 URL
            cookies_file: Cookies 文件路径（JSON 格式）
            
        Returns:
            页面 HTML 内容
        """
        cookies_file = cookies_file or self.cookies_file
        if not cookies_file or not Path(cookies_file).exists():
            print(f"Cookies 文件不存在: {cookies_file}")
            return None
        
        try:
            # 加载 cookies
            with open(cookies_file, 'r', encoding='utf-8') as f:
                selenium_cookies = json.load(f)
            
            # 将 Selenium cookies 格式转换为 requests cookies 格式
            cookies_dict = {}
            for cookie in selenium_cookies:
                cookies_dict[cookie['name']] = cookie['value']
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            }
            
            # 发送请求
            print(f"正在使用 requests 获取页面: {target_url}")
            response = self.session.get(target_url, cookies=cookies_dict, headers=headers, timeout=10)
            response.raise_for_status()
            
            print(f"成功获取页面，状态码: {response.status_code}")
            return response.text
            
        except Exception as e:
            print(f"使用 requests 获取页面失败: {e}")
            return None
    
    # ⬇️ 方法6: 手动设置 cookies（适用于已知的认证 token）
    def set_cookies_manually(self, cookies_dict: dict, base_url: str):
        """
        手动设置 cookies（适用于已知的认证 token 或 session）
        
        Args:
            cookies_dict: Cookies 字典，格式: {'name': 'value', ...}
            base_url: 基础 URL（用于设置 cookies 的域名）
        """
        self.driver.get(base_url)
        time.sleep(1)
        
        for name, value in cookies_dict.items():
            cookie = {
                'name': name,
                'value': value,
                'domain': self._extract_domain(base_url)
            }
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"设置 cookie {name} 失败: {e}")
        
        print("手动设置的 cookies 已添加")
    
    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lstrip('www.')
    
    def get_page_content(self, url: str) -> str:
        """获取页面内容"""
        self.driver.get(url)
        time.sleep(2)  # 等待页面加载
        return self.driver.page_source
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()


# ⬇️ 使用示例
def example_usage():
    """使用示例"""
    
    # 示例1: 通过登录界面登录
    print("=" * 60)
    print("示例1: 通过登录界面登录")
    print("=" * 60)
    
    scraper = WebScraperWithLogin(
        headless=False,  # 设置为 False 可以看到浏览器操作过程
        cookies_file='cookies.json'
    )
    
    try:
        # 登录（需要根据实际网站修改选择器）
        success = scraper.login_with_selenium(
            login_url='https://example.com/login',
            username='your_username',
            password='your_password',
            username_selector='#username',  # 根据实际网站修改
            password_selector='#password',  # 根据实际网站修改
            submit_selector='button[type="submit"]',  # 根据实际网站修改
            wait_after_login=3
        )
        
        if success:
            # 爬取内容
            content = scraper.get_page_content('https://example.com/protected-page')
            print("成功获取页面内容")
            # 处理 content...
        
    finally:
        scraper.close()
    
    # 示例2: 使用已保存的 cookies（跳过登录界面）
    print("\n" + "=" * 60)
    print("示例2: 使用已保存的 cookies 直接访问")
    print("=" * 60)
    
    scraper2 = WebScraperWithLogin(headless=True, cookies_file='cookies.json')
    
    try:
        # 直接使用 cookies 访问（无需登录）
        success = scraper2.access_with_saved_cookies(
            target_url='https://example.com/protected-page'
        )
        
        if success:
            content = scraper2.get_page_content('https://example.com/protected-page')
            print("成功获取页面内容")
            # 处理 content...
        
    finally:
        scraper2.close()
    
    # 示例3: 使用 requests + cookies（最快，无需浏览器）
    print("\n" + "=" * 60)
    print("示例3: 使用 requests + cookies（推荐，最快）")
    print("=" * 60)
    
    scraper3 = WebScraperWithLogin(cookies_file='cookies.json')
    
    try:
        # 使用 requests 获取页面（比 Selenium 快得多）
        content = scraper3.scrape_with_requests_and_cookies(
            target_url='https://example.com/protected-page'
        )
        
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            # 解析内容...
            print("成功获取并解析页面内容")
        
    finally:
        scraper3.close()
    
    # 示例4: 手动设置 cookies（适用于已知 token）
    print("\n" + "=" * 60)
    print("示例4: 手动设置 cookies")
    print("=" * 60)
    
    scraper4 = WebScraperWithLogin(headless=True)
    
    try:
        # 手动设置已知的认证 cookies
        scraper4.set_cookies_manually(
            cookies_dict={
                'session_id': 'your_session_id_here',
                'auth_token': 'your_auth_token_here'
            },
            base_url='https://example.com'
        )
        
        # 访问受保护页面
        content = scraper4.get_page_content('https://example.com/protected-page')
        print("成功获取页面内容")
        
    finally:
        scraper4.close()


if __name__ == '__main__':
    example_usage()
