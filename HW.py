import requests
import base64
import urllib.parse
from typing import Iterator

# 提取常量，便于后续修改
API_URL = "https://snowd.com/api/locations.php"
TIMEOUT = 10

def fetch_and_process() -> Iterator[str]:
    # 增加 User-Agent，防止部分 API 拦截默认的 requests 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
        response.raise_for_status() # 检查 HTTP 状态码
        data = response.json()
    except requests.RequestException as e:
        # 网络请求失败时可以在这里加入日志打印
        # print(f"Request failed: {e}")
        return

    # 增强类型校验，确保 data['data'] 是一个列表
    if data.get('success') != 1 or not isinstance(data.get('data'), list):
        return

    for loc in data['data']:
        if not isinstance(loc, dict):
            continue
        
        accs = loc.get('accs')
        country = loc.get('country')
        if not accs or not country:
            continue
        
        parts = accs.split('@', 1)
        if len(parts) != 2:
            continue
        
        # 将解析逻辑放入独立的 try-except 块
        # 避免单个节点数据损坏（如 Base64 错误）导致整个程序中断退出
        try:
            # 第一部分通常为加密方式和密码的 Base64 编码
            decoded_creds = base64.b64decode(parts[0]).decode('utf-8')
            
            # 组合成 ss:// 要求的规范: base64(method:password@host:port)
            combined = f"{decoded_creds}@{parts[1]}"
            encoded_node = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
            
            # 使用 yield 变成生成器，边解析边输出，优化内存开销
            yield f"ss://{encoded_node}#{urllib.parse.quote(country)}"
            
        except (ValueError, TypeError, UnicodeDecodeError):
            # 遇到解析失败的脏数据直接跳过，继续处理下一个节点
            continue

if __name__ == "__main__":
    for result in fetch_and_process():
        print(result)
