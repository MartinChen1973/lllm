"""
Selenium 登录网站快速入门示例
演示最常见的登录场景
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time


# ⬇️ 方法1: 最简单的登录方式 - 通过登录界面
def simple_login_example():
    """最简单的登录示例"""
    
    # 设置浏览器
    options = Options()
    options.add_argument('--headless')  # 无头模式
    driver = webdriver.Chrome(options=options)
    
    try:
        # 1. 访问登录页面
        driver.get('https://example.com/login')
        
        # 2. 等待并填写用户名
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'username'))  # 根据实际网站修改
        )
        username_input.send_keys('your_username')
        
        # 3. 填写密码
        password_input = driver.find_element(By.ID, 'password')  # 根据实际网站修改
        password_input.send_keys('your_password')
        
        # 4. 点击登录按钮
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # 5. 等待登录完成
        time.sleep(3)
        
        # 6. 保存 cookies（重要！）
        cookies = driver.get_cookies()
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)
        print("Cookies 已保存")
        
        # 7. 现在可以访问受保护的页面了
        driver.get('https://example.com/protected-page')
        print("成功访问受保护页面")
        print(driver.page_source[:500])  # 打印前500个字符
        
    finally:
        driver.quit()


# ⬇️ 方法2: 使用已保存的 cookies（推荐！避免每次登录）
def use_saved_cookies_example():
    """使用已保存的 cookies，跳过登录界面"""
    
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    try:
        # 1. 先访问网站主页（必须，用于设置 cookies 的域名）
        driver.get('https://example.com')
        time.sleep(1)
        
        # 2. 加载之前保存的 cookies
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            # 移除可能导致问题的字段
            cookie.pop('sameSite', None)
            try:
                driver.add_cookie(cookie)
            except:
                pass  # 忽略无法添加的 cookie
        
        # 3. 刷新页面使 cookies 生效
        driver.refresh()
        time.sleep(2)
        
        # 4. 直接访问受保护页面（无需登录！）
        driver.get('https://example.com/protected-page')
        print("使用 cookies 成功访问受保护页面")
        print(driver.page_source[:500])
        
    finally:
        driver.quit()


# ⬇️ 方法3: 使用 requests + cookies（最快，无需浏览器）
def requests_with_cookies_example():
    """使用 requests 库 + cookies，比 Selenium 快得多"""
    
    import requests
    from bs4 import BeautifulSoup
    
    # 1. 加载 cookies
    with open('cookies.json', 'r') as f:
        selenium_cookies = json.load(f)
    
    # 2. 转换为 requests 格式
    cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    
    # 3. 发送请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(
        'https://example.com/protected-page',
        cookies=cookies_dict,
        headers=headers
    )
    
    # 4. 解析内容
    soup = BeautifulSoup(response.text, 'html.parser')
    print("使用 requests 成功获取页面")
    print(soup.prettify()[:500])


# ⬇️ 方法4: 处理需要验证码的登录
def login_with_captcha_example():
    """处理需要验证码的登录（需要手动输入）"""
    
    options = Options()
    # 注意：处理验证码时不要用 headless 模式，需要看到验证码
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get('https://example.com/login')
        
        # 填写用户名密码
        driver.find_element(By.ID, 'username').send_keys('your_username')
        driver.find_element(By.ID, 'password').send_keys('your_password')
        
        # 等待用户手动输入验证码
        print("请手动输入验证码...")
        input("输入完成后按 Enter 继续...")
        
        # 点击登录
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(3)
        
        # 保存 cookies
        cookies = driver.get_cookies()
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)
        print("登录成功，cookies 已保存")
        
    finally:
        driver.quit()


# ⬇️ 方法5: 处理动态加载的登录表单
def login_with_dynamic_form_example():
    """处理动态加载的登录表单（需要等待元素出现）"""
    
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get('https://example.com/login')
        
        # 等待登录表单完全加载
        username_input = wait.until(
            EC.element_to_be_clickable((By.ID, 'username'))
        )
        
        # 填写表单
        username_input.send_keys('your_username')
        password_input = wait.until(
            EC.presence_of_element_located((By.ID, 'password'))
        )
        password_input.send_keys('your_password')
        
        # 等待登录按钮可点击
        login_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        login_button.click()
        
        # 等待登录成功（检查 URL 变化或特定元素出现）
        wait.until(
            lambda d: 'login' not in d.current_url.lower() or 
                     d.find_elements(By.CSS_SELECTOR, '.user-profile')  # 登录后的元素
        )
        
        # 保存 cookies
        cookies = driver.get_cookies()
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f)
        print("登录成功")
        
    finally:
        driver.quit()


if __name__ == '__main__':
    print("选择要运行的示例：")
    print("1. 简单登录示例")
    print("2. 使用已保存的 cookies")
    print("3. 使用 requests + cookies（最快）")
    print("4. 处理验证码登录")
    print("5. 处理动态加载表单")
    
    choice = input("请输入数字 (1-5): ")
    
    if choice == '1':
        simple_login_example()
    elif choice == '2':
        use_saved_cookies_example()
    elif choice == '3':
        requests_with_cookies_example()
    elif choice == '4':
        login_with_captcha_example()
    elif choice == '5':
        login_with_dynamic_form_example()
    else:
        print("无效选择")
