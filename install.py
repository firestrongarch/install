import subprocess
import yaml
import time
import os


def get_current_proxy(dic):
    """获取当前代理URL"""
    proxy_config = dic.get('proxy', {})
    if not proxy_config.get('enabled', False):
        return ""
    urls = proxy_config.get('urls', [""])
    index = proxy_config.get('current_index', 0)
    if index < len(urls):
        return urls[index]
    return ""


def get_all_proxies(dic):
    """获取所有代理URL列表"""
    proxy_config = dic.get('proxy', {})
    urls = proxy_config.get('urls', [""])
    return urls


def test_proxy(proxy_url, test_url="https://github.com"):
    """测试代理是否可用，优先使用 wget"""
    url = proxy_url + test_url if proxy_url else test_url
    print(f"  测试: {proxy_url if proxy_url else '直接连接'}")
    try:
        # 优先使用 wget
        result = subprocess.run(
            f'wget --timeout=5 --tries=1 --spider "{url}" 2>&1',
            shell=True, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"  ✓ 可用")
            return True

        # wget 失败，尝试 curl
        result = subprocess.run(
            f'curl -sI --connect-timeout 5 --max-time 10 "{url}" 2>&1 | head -1',
            shell=True, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and ('200' in result.stdout or '302' in result.stdout or '301' in result.stdout):
            print(f"  ✓ 可用")
            return True
        else:
            print(f"  ✗ 失败")
            return False
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False


def find_working_proxy(dic, selection):
    """自动寻找可用的代理"""
    proxy_config = dic.get('proxy', {})
    if not proxy_config.get('enabled', False):
        return ""

    urls = proxy_config.get('urls', [""])
    current_index = proxy_config.get('current_index', 0)

    # 测试当前代理
    test_url = selection['url']
    current_proxy = urls[current_index] if current_index < len(urls) else ""

    print(f"\n正在测试连接...")
    if test_proxy(current_proxy, test_url):
        return current_proxy

    # 当前代理失败，尝试其他代理
    print(f"\n当前代理不可用，正在尝试其他代理...")
    for i, proxy in enumerate(urls):
        if i == current_index:
            continue
        if test_proxy(proxy, test_url):
            # 更新当前索引
            proxy_config['current_index'] = i
            dic['proxy'] = proxy_config
            with open('packages.yaml', 'w') as f:
                yaml.dump(dic, f, allow_unicode=True, sort_keys=False)
            print(f"已自动切换到代理: {proxy if proxy else '直接连接'}")
            return proxy

    print("所有代理都不可用，将尝试直接连接")
    return ""


def download_file(url, output_path):
    """使用 wget 下载文件"""
    print(f"使用 wget 下载...")
    result = subprocess.run(
        f'sudo wget -O "{output_path}" "{url}" 2>&1',
        shell=True
    )
    return result.returncode == 0


def processChoice(selection, dic):
    """处理安装选择，自动切换代理"""
    proxy_url = ""

    # 对于git和archive类型，尝试自动寻找可用代理
    if selection['type'] in ('git', 'archive'):
        proxy_url = find_working_proxy(dic, selection)

    if selection['type'] == 'git':
        name = selection['name']
        url = proxy_url + selection['url']
        version = selection['version']
        download_url = f'{url}/releases/download/{version}/{name}'
        print(f'\n正在下载: {download_url}')

        if download_file(download_url, f'/tmp/{name}'):
            subprocess.run(f'sudo apt install /tmp/{name} -y', shell=True)
        else:
            print("下载失败，请检查网络连接或手动切换代理")
            return
    elif selection['type'] == 'wget':
        # wget类型直接使用原始URL
        url = selection['url']
        name = url.split('/')[-1]
        print(f'\n正在下载: {url}')

        if download_file(url, f'/tmp/{name}'):
            subprocess.run(f'sudo apt install /tmp/{name} -y', shell=True)
        else:
            print("下载失败")
            return
    elif selection['type'] == 'config':
        for cmd in selection['cmd']:
            subprocess.run(cmd, shell=True)
    elif selection['type'] == 'archive':
        # 压缩包类型（如 ROS2）
        name = selection['name']
        url = proxy_url + selection['url']
        version = selection['version']
        install_path = selection.get('install_path', '/opt')
        # 展开用户主目录路径
        install_path = os.path.expanduser(install_path)
        download_url = f'{url}/releases/download/{version}/{name}'
        print(f'\n正在下载: {download_url}')

        if download_file(download_url, f'/tmp/{name}'):
            # 创建安装目录（用户目录不需要sudo）
            subprocess.run(f'mkdir -p {install_path}', shell=True)
            # 解压到安装目录
            print(f'正在解压到 {install_path}...')
            subprocess.run(
                f'tar -xjf /tmp/{name} -C {install_path}', shell=True)
            print(f'ROS2 安装完成！')
            print(f'使用方式: {selection.get("setup_cmd", "")}')
            print(
                f'建议添加到 ~/.zshrc: echo "{selection.get("setup_cmd", "")}" >> ~/.zshrc')
        else:
            print("下载失败")
            return
    else:
        print('不支持的类型')


def toggle_proxy(dic):
    """切换代理状态"""
    proxy_config = dic.get('proxy', {})
    current_status = proxy_config.get('enabled', False)
    proxy_config['enabled'] = not current_status
    dic['proxy'] = proxy_config

    with open('packages.yaml', 'w') as f:
        yaml.dump(dic, f, allow_unicode=True, sort_keys=False)

    status = "启用" if proxy_config['enabled'] else "禁用"
    print(f'代理已{status}')
    return dic


def switch_proxy(dic):
    """手动切换代理"""
    proxy_config = dic.get('proxy', {})
    urls = proxy_config.get('urls', [""])
    current_index = proxy_config.get('current_index', 0)

    print("\n可用代理列表:")
    for i, url in enumerate(urls):
        marker = " (当前)" if i == current_index else ""
        display = "直接连接" if url == "" else url
        print(f"  [{i}]: {display}{marker}")

    choice = input("\n请选择代理序号: ")
    try:
        new_index = int(choice)
        if 0 <= new_index < len(urls):
            proxy_config['current_index'] = new_index
            dic['proxy'] = proxy_config
            with open('packages.yaml', 'w') as f:
                yaml.dump(dic, f, allow_unicode=True, sort_keys=False)
            display = "直接连接" if urls[new_index] == "" else urls[new_index]
            print(f'已切换到: {display}')
        else:
            print("无效的选择")
    except ValueError:
        print("请输入数字")

    return dic


def show_proxy_status(dic):
    """显示当前代理状态"""
    proxy_config = dic.get('proxy', {})
    enabled = proxy_config.get('enabled', False)
    urls = proxy_config.get('urls', [""])
    current_index = proxy_config.get('current_index', 0)

    if not enabled:
        return "已禁用"

    if current_index < len(urls):
        current = urls[current_index]
        return "直接连接" if current == "" else current
    return "未知"


if __name__ == '__main__':
    with open('packages.yaml', 'r') as f:
        dic = yaml.load(f, Loader=yaml.FullLoader)

    menu = {}
    index = 1
    for key, value in dic.items():
        if key == 'proxy':
            continue
        menu[index] = f'{key} - {value["des"]}'
        index += 1

    while True:
        proxy_status = show_proxy_status(dic)
        print(f'\n===== 软件包安装工具 =====')
        print(f'当前代理: {proxy_status}')
        print('')
        for key, val in menu.items():
            print(f'[{key}]: {val}')
        print('[p]: 切换代理开关')
        print('[s]: 手动选择代理')
        print('[0]: 退出')
        print(' ')
        choice = input('请输入序号: ')

        if choice == '0':
            break
        elif choice == 'p':
            dic = toggle_proxy(dic)
        elif choice == 's':
            dic = switch_proxy(dic)
        elif choice.isdigit() and int(choice) in menu:
            key = menu[int(choice)].split(' - ')[0]
            processChoice(dic[key], dic)
        else:
            print('无效的选择，请重新输入')
