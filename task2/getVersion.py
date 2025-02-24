import re
import json
import logging
import subprocess
import tomli
from datetime import datetime, timezone

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # 日志内容由我们自己构造
    handlers=[
        logging.FileHandler('package_updates.log'),
        logging.StreamHandler()
    ]
)

def get_current_timestamp():
    """获取当前时间戳，ISO 8601 格式，精确到毫秒。"""
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def parse_nvchecker_output(output):
    """
    解析 nvchecker -c 的输出，提取软件包名和更新后的版本。
    """
    pattern = re.compile(r'\[I .*\] (\S+): updated to (\S+)(?: url=(\S+))?')
    matches = pattern.findall(output)
    return matches

def read_toml_config(file_path):
    """
    读取并解析 TOML 配置文件。
    """
    with open(file_path, 'rb') as f:
        return tomli.load(f)

def run_nvchecker(config_path):
    """
    运行 nvchecker 命令并捕获输出。
    """
    command = ['nvchecker', '-c', config_path]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running nvchecker: {e}")
        return None

def log_package_updates(updates, config):
    """
    将软件包更新信息记录到日志中，使用结构化日志格式，每条日志占一行。
    """
    for package, version, url in updates:
        package_config = config.get(package, {})
        log_entry = {
            "timestamp": get_current_timestamp(),
            "level": "INFO",
            "package": package,
            "version": version,
            "url": url if url else "N/A",
            "config": package_config
        }
        # 将日志记录为格式化 JSON，并添加换行符
        logging.info(json.dumps(log_entry, indent=2, ensure_ascii=False) + "\n")

def main():
    config_path = 'config.toml'  # TOML 配置文件路径

    # 实时运行 nvchecker 并捕获输出
    nvchecker_output = run_nvchecker(config_path)
    if not nvchecker_output:
        return  # 如果命令失败，直接退出

    updates = parse_nvchecker_output(nvchecker_output)
    config = read_toml_config(config_path)
    log_package_updates(updates, config)

if __name__ == "__main__":
    main()
