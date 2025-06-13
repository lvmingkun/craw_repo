# ***
# 作者：FH
# 时间：2025/6/10  15:14
# ***

import csv
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import openpyxl  # 用于读取Excel文件

# ==================== 文件路径配置 ====================
# 日志文件路径
LOG_FILE = 'journal_crawler.log'
# 进度文件路径
PROGRESS_FILE = 'progress.txt'
# 期刊列表Excel文件路径
JOURNAL_LIST_FILE = './lists.xlsx'
# 输出文件目录
OUTPUT_DIR = 'F:\\top\\'

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')     # 要是报错可能有验证码，就注释掉这行
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    #options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    )

    # 伪装 WebDriver 信息
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        });
        Object.defineProperty(navigator, 'languages', {
          get: () => ['zh-CN', 'zh']
        });
        Object.defineProperty(navigator, 'plugins', {
          get: () => [1, 2, 3]
        });
        '''})

    #driver.maximize_window()
    return driver


def wait_and_click(driver, xpath, timeout=5):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception as e:
        logger.error(f"无法点击元素 {xpath}: {str(e)}")
        return False


def wait_for_articles(driver, timeout=12):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//dl[@id='CataLogContent']//div//dd//span[@class='name']/a"))
        )
        return True
    except TimeoutException:
        logger.error("等待文章列表超时")
        return False


def scrape_article(driver, article_url):
    try:
        driver.execute_script(f"window.open('{article_url}');")
        driver.switch_to.window(driver.window_handles[-1])

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='wx-tit']/h1"))
        )

        try:
            title = driver.find_element(By.XPATH, "//div[@class='wx-tit']/h1").text
        except Exception as e:
            logger.error(f"提取标题失败: {e}")
            title = "未找到标题"

        try:
            abstract = driver.find_element(By.ID, "ChDivSummary").text
        except Exception as e:
            logger.error(f"提取摘要失败: {e}")
            abstract = "未找到摘要"

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return title.strip(), abstract.strip()

    except Exception as e:
        logger.error(f"爬取文章出错: {str(e)}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return None, None


def get_journal_list():
    """从Excel文件中读取期刊列表，并去除前后空格"""
    try:
        wb = openpyxl.load_workbook(JOURNAL_LIST_FILE)  # 期刊列表名， 里面没有原表前面的数字加点
        sheet = wb.active
        journals = []

        for row in sheet.iter_rows(values_only=True):
            cell = row[0]
            if cell:
                # 去除半角和全角空格
                clean_name = str(cell).strip().replace('\u3000', '')
                if clean_name:
                    journals.append(clean_name)

        return journals

    except Exception as e:
        logger.error(f"读取Excel文件失败: {str(e)}")
        return []


def save_progress(journal_name):
    """保存当前进度到文件"""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(journal_name)
        logger.info(f"已保存进度: {journal_name}")
    except Exception as e:
        logger.error(f"保存进度失败: {str(e)}")


def load_progress():
    """从进度文件中读取上次的进度"""
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"读取进度文件失败: {str(e)}")
        return None


def search_journal(driver, journal_name):
    """搜索期刊并获取第一个结果的链接"""
    try:
        # 清空并输入期刊名称
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='txt_1_value1']"))
        )
        search_input.clear()
        search_input.send_keys(journal_name)

        # 点击搜索按钮
        if not wait_and_click(driver, "//input[@id='btnSearch']"):
            logger.error("无法点击搜索按钮")
            return None

        # 等待结果加载
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[2]/div[2]/div[1]/div[2]/ul/li[1]"))
            )
        except TimeoutException:
            logger.warning(f"未找到期刊 '{journal_name}' 的搜索结果")
            return None

        # 获取第一个结果的链接
        try:
            first_result = driver.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div[2]/div[1]/div[2]/ul/li[1]/a")
            journal_url = first_result.get_attribute('href')
            return journal_url
        except NoSuchElementException:
            logger.warning(f"期刊 '{journal_name}' 无搜索结果")
            return None

    except Exception as e:
        logger.error(f"搜索期刊 '{journal_name}' 时出错: {str(e)}")
        return None


def scrape_journal_articles(driver, journal_name):
    """爬取单个期刊的文章"""
    output_file = f"{OUTPUT_DIR}{journal_name}.csv"  # 使用配置的输出目录

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['标题', '摘要'])

        # 获取2025年的期数
        try:
            year_2025_issues = driver.find_elements(By.XPATH,
                                                    "/html/body/div[2]/div[2]/div[3]/div[3]/div/div[1]/div/div[1]/dl[1]/dd/a")
            click_times_2025 = len(year_2025_issues) - 1  # 需要点击的次数
        except Exception as e:
            logger.error(f"获取2025年期数失败: {str(e)}")
            click_times_2025 = 0

        # 点击2025年按钮
        if click_times_2025 > 0:
            if not wait_and_click(driver, "//dl[@id='2025_Year_Issue']/dt", 5):
                logger.error("无法点击2025年按钮")
            else:
                time.sleep(0.5)
                logger.info(f"开始爬取 {journal_name} 2025年（共{click_times_2025 + 1}期）")

                for _ in range(click_times_2025 + 1):
                    if not wait_for_articles(driver):
                        logger.warning("2025年某期未能加载文章")
                        continue

                    article_elements = driver.find_elements(By.XPATH,
                                                            "//dl[@id='CataLogContent']//div//dd//span[@class='name']/a")
                    article_urls = [a.get_attribute('href') for a in article_elements if a.get_attribute('href')]
                    logger.info(f"找到 {len(article_urls)} 篇文章")

                    seen = set()
                    for i, article_url in enumerate(article_urls):
                        if article_url in seen:
                            continue
                        seen.add(article_url)

                        title, abstract = scrape_article(driver, article_url)
                        if title and abstract:
                            writer.writerow([title, abstract])
                            logger.info(f"2025年第{i + 1}篇：{title[:30]}...")
                        time.sleep(0.2)

                    # 如果不是最后一期，点击上一期
                    if _ < click_times_2025:
                        if not wait_and_click(driver, "//span[@id='larrow']", 5):
                            logger.error("无法切换到上一期")
                            break
                        time.sleep(0.5)
        if click_times_2025 < 11:
            # 获取2024年的期数
            try:
                year_2024_issues = driver.find_elements(By.XPATH,
                                                        "/html/body/div[2]/div[2]/div[3]/div[3]/div/div[1]/div/div[1]/dl[2]/dd/a")
                click_times_2024 = len(year_2024_issues) - 1  # 需要点击的次数
            except Exception as e:
                logger.error(f"获取2024年期数失败: {str(e)}")
                click_times_2024 = 0

            # 点击2024年按钮
            if click_times_2024 > 0:
                if not wait_and_click(driver, "//dl[@id='2024_Year_Issue']/dt", 5):
                    logger.error("无法点击2024年按钮")
                else:
                    time.sleep(0.5)
                    logger.info(f"开始爬取 {journal_name} 2024年（共{click_times_2024 + 1}期）")

                    for _ in range(click_times_2024 + 1):
                        if not wait_for_articles(driver):
                            logger.warning("2024年某期未能加载文章")
                            continue

                        article_elements = driver.find_elements(By.XPATH,
                                                                "//dl[@id='CataLogContent']//div//dd//span[@class='name']/a")
                        article_urls = [a.get_attribute('href') for a in article_elements if a.get_attribute('href')]
                        logger.info(f"找到 {len(article_urls)} 篇文章")

                        seen = set()
                        for i, article_url in enumerate(article_urls):
                            if article_url in seen:
                                continue
                            seen.add(article_url)

                            title, abstract = scrape_article(driver, article_url)
                            if title and abstract:
                                writer.writerow([title, abstract])
                                logger.info(f"2024年第{i + 1}篇：{title[:30]}...")
                            time.sleep(0.2)

                        # 如果不是最后一期，点击上一期
                        if _ < click_times_2024:
                            if not wait_and_click(driver, "//span[@id='larrow']", 5):
                                logger.error("无法切换到上一期")
                                break
                            time.sleep(0.5)

    logger.info(f"{journal_name} 爬取完成，结果保存于: {output_file}")


def main():
    driver = None
    try:
        driver = init_driver()

        # 加载进度
        last_journal = load_progress()
        journal_list = get_journal_list()

        if not journal_list:
            logger.error("未找到期刊列表，请检查lists.xlsx文件")
            return

        # 如果有进度，从上次中断的期刊开始
        if last_journal and last_journal in journal_list:
            idx = journal_list.index(last_journal)
            journal_list = journal_list[idx:]
            logger.info(f"从上次中断的期刊继续: {last_journal}")
        elif last_journal:
            logger.warning(f"进度文件中的期刊 {last_journal} 不在当前列表中")

        for journal_name in journal_list:
            logger.info(f"开始处理期刊: {journal_name}")

            # 保存当前进度
            save_progress(journal_name)

            # 打开搜索页面
            driver.get("https://navi.cnki.net/knavi/journals/search?uniplatform=NZKPT")
            time.sleep(1)

            # 搜索期刊
            journal_url = search_journal(driver, journal_name)
            if not journal_url:
                logger.warning(f"跳过期刊 {journal_name}，未找到搜索结果")
                # continue
                raise RuntimeError(f"未找到期刊 {journal_name} 的搜索结果，程序终止。")  # 不会跳刊

            # 进入期刊页面
            driver.get(journal_url)
            time.sleep(1)

            # 爬取该期刊的文章
            scrape_journal_articles(driver, journal_name)

        logger.info("所有期刊处理完成")

    except Exception as e:
        logger.error(f"程序发生未捕获的异常: {str(e)}", exc_info=True)
        raise  # 重新抛出异常，停止程序

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    logger.info("程序启动")
    try:
        main()
    except Exception as e:
        logger.error(f"程序异常终止: {str(e)}", exc_info=True)
    logger.info("程序结束")