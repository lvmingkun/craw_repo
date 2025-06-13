# ***
# 作者：FH
# 时间：2025/6/12  21:07
# ***

import subprocess
import os
import time
import psutil
import signal
import sys  # 导入 sys 模块

# 打开文件并打印内容
file_path = 'progress.txt'  # 你要读取的文件路径
# conda_env_name = 'your_conda_env'  # 替换为实际的环境名

# 检查是否安装了Google Chrome和ChromeDriver
def check_chrome_and_driver():
    try:
        # 检查ChromeDriver是否存在
        driver_path = subprocess.check_output('where chromedriver', shell=True,
                                              stderr=subprocess.DEVNULL).decode().strip()
        if not driver_path:
            print("没有找到ChromeDriver，请前往官网下载并安装： https://sites.google.com/chromium.org/driver/, 如果没有谷歌浏览器请一并下载.")
        else:
            print("ChromeDriver已安装，路径为：", driver_path)

    except subprocess.CalledProcessError as e:
        print("检测Google Chrome或ChromeDriver时发生错误，错误信息, 如果程序可以正常运行请忽略：", e)


# 检查需要的Python包是否已安装
def check_and_install_packages():
    required_packages = ['selenium', 'openpyxl']
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'show', package])
        except subprocess.CalledProcessError:
            print(f"缺少必要的包：{package}。请运行以下命令安装：")
            print(f"pip install {package}")


# Windows系统
def is_program_running(script_path):
    """
    检查程序是否正在运行
    """
    abs_script_path = os.path.abspath(script_path)

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python.exe' in proc.info['name'] and any(script_path in cmd for cmd in proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
            pass
    return False


def restart_program(program_cmd):
    """
    重新启动程序
    """
    try:
        # if conda_env_name:
        #     # 添加 Conda 激活命令
        #     program_cmd = f"cmd.exe /c \"conda activate {conda_env_name} && {program_cmd}\""
        process = subprocess.Popen(program_cmd, shell=True)  # 启动子进程并返回 Popen 对象
        return process
    except Exception as e:
        print(f"启动程序时出现错误: {e}")
        return None


def terminate_subprocess(process):
    """
    强制终止子进程
    """
    try:
        if process:
            # 尝试终止子进程
            print("尝试终止子进程...")
            process.terminate()  # 尝试终止子进程
            process.wait(timeout=5)  # 等待5秒以确保进程有时间退出

            # 如果进程没有响应 terminate()，则使用 kill() 强制终止
            if process.poll() is None:  # 检查进程是否仍在运行
                print("进程未终止，强制杀死子进程...")
                process.kill()  # 强制杀死子进程
                process.wait()  # 等待进程完全结束

            print("子进程已停止。")
    except Exception as e:
        print(f"停止子进程时出现错误: {e}")


def main():
    # 检查Google Chrome和ChromeDriver
    check_chrome_and_driver()

    # 检查是否安装了必需的包
    check_and_install_packages()

    program_name = './craw.py'  # 要检查的程序名
    program_cmd = 'python ' + program_name  # 启动命令，避免使用 start
    time_interval = 180  # 每隔 3 min 判断一次
    process = None  # 用于保存子进程

    try:
        while True:
            if not is_program_running(program_name):
                print(f"{program_name} 没有在运行，正在尝试重新启动...")
                process = restart_program(program_cmd)  # 重启程序并保存子进程
                if process:
                    print(f"{program_name} 已重新启动。")
            else:
                print(f"{program_name} 正在运行。")

            # 打印文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()  # 读取整个文件内容
                    print(f"当前进度：{content}")  # 打印文件内容
            except FileNotFoundError:
                print(f"文件 {file_path} 未找到。")
            except Exception as e:
                print(f"发生错误: {e}")

            time.sleep(time_interval)

    except KeyboardInterrupt:
        print("程序已被手动停止。")
    except Exception as e:
        print(f"程序出现错误: {e}")
    finally:
        # 在程序结束时确保子进程被终止
        terminate_subprocess(process)

if __name__ == "__main__":
    main()




