import os
import sys
import requests
import base64
import urllib.parse
from typing import Iterator

API_URL = "https://snowd.com/api/locations.php"
TIMEOUT = 10

def fetch_and_process() -> Iterator[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"❌ 网络请求错误: {e}")
        return

    if data.get('success') != 1 or not isinstance(data.get('data'), list):
        print("❌ API 数据格式不正确或获取失败。")
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
        
        try:
            decoded_creds = base64.b64decode(parts[0]).decode('utf-8')
            combined = f"{decoded_creds}@{parts[1]}"
            encoded_node = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
            yield f"ss://{encoded_node}#{urllib.parse.quote(country)}"
            
        except (ValueError, TypeError, UnicodeDecodeError):
            continue

def get_run_dir() -> str:
    """获取程序当前的运行真实目录（完美兼容 PyInstaller 编译后的 exe）"""
    if getattr(sys, 'frozen', False):
        # 如果是 PyInstaller 打包运行，获取 exe 所在真实目录
        return os.path.dirname(sys.executable)
    else:
        # 如果是纯 Python 脚本运行，获取 py 文件所在目录
        return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    print("正在获取并解析节点信息，请稍候...\n")
    
    # 获取所有节点
    nodes = list(fetch_and_process())
    
    if nodes:
        # 准备保存路径
        run_dir = get_run_dir()
        txt_file = os.path.join(run_dir, "nodes.txt")
        sub_file = os.path.join(run_dir, "subscribe.txt")
        
        try:
            # 1. 保存为明文 txt
            with open(txt_file, "w", encoding="utf-8") as f:
                for node in nodes:
                    print(node)  # 在黑框里实时打印给用户看
                    f.write(node + "\n")
            
            # 2. 保存为 Base64 订阅格式 (很多客户端导入需要这个)
            raw_text = "\n".join(nodes)
            sub_base64 = base64.b64encode(raw_text.encode('utf-8')).decode('utf-8')
            with open(sub_file, "w", encoding="utf-8") as f:
                f.write(sub_base64)
            
            print(f"\n✅ 成功获取 {len(nodes)} 个节点！")
            print(f"📂 明文节点已保存至：{txt_file}")
            print(f"📂 订阅链接已保存至：{sub_file} (可直接供客户端读取)")
        
        except Exception as e:
            print(f"\n❌ 保存文件时发生错误：{e}")
    else:
        print("\n❌ 未能获取到任何可用节点。")
        
    # 防止编译成 exe 后运行完毕直接闪退，留出时间看输出
    print("\n")
    input("按回车键退出程序...")
