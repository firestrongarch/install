import subprocess
import yaml
import time
import os

# ANSI 颜色定义
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'


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
    display = f"{proxy_url}" if proxy_url else f"{BLUE}直接连接{RESET}"
    print(f"  {YELLOW}测试:{RESET} {display}")
    try:
        # 优先使用 wget
        result = subprocess.run(
            f'wget --timeout=5 --tries=1 --spider "{url}" 2>&1',
            shell=True, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"  {GREEN}✓ 可用{RESET}")
            return True

        # wget 失败，尝试 curl
        result = subprocess.run(
            f'curl -sI --connect-timeout 5 --max-time 10 "{url}" 2>&1 | head -1',
            shell=True, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and ('200' in result.stdout or '302' in result.stdout or '301' in result.stdout):
            print(f"  {GREEN}✓ 可用{RESET}")
            return True
        else:
            print(f"  {RED}✗ 失败{RESET}")
            return False
    except Exception as e:
        print(f"  {RED}✗ 错误:{RESET} {e}")
        return False


def find_working_proxy(dic, selection):
    """自动寻找可用的代理"""
    proxy_config = dic.get('proxy', {})
    if not proxy_config.get('enabled', False):
        return ""

    urls = proxy_config.get('urls', [""])
    current_index = proxy_config.get('current_index', 0)

    # 根据类型获取测试URL
    if 'url' in selection:
        test_url = selection['url']
    elif 'repos_url' in selection:
        test_url = selection['repos_url']
    else:
        test_url = "https://github.com"

    current_proxy = urls[current_index] if current_index < len(urls) else ""

    print(f"\n{CYAN}正在测试连接...{RESET}")
    if test_proxy(current_proxy, test_url):
        return current_proxy

    # 当前代理失败，尝试其他代理
    print(f"\n{YELLOW}当前代理不可用，正在尝试其他代理...{RESET}")
    for i, proxy in enumerate(urls):
        if i == current_index:
            continue
        if test_proxy(proxy, test_url):
            # 更新当前索引
            proxy_config['current_index'] = i
            dic['proxy'] = proxy_config
            with open('packages.yaml', 'w') as f:
                yaml.dump(dic, f, allow_unicode=True, sort_keys=False)
            display = f"{BLUE}直接连接{RESET}" if proxy == "" else proxy
            print(f"{GREEN}已自动切换到代理:{RESET} {display}")
            return proxy

    print(f"{RED}所有代理都不可用，将尝试直接连接{RESET}")
    return ""


def download_file(url, output_path):
    """使用 wget 下载文件"""
    print(f"{BLUE}使用 wget 下载...{RESET}")
    result = subprocess.run(
        f'sudo wget -O "{output_path}" "{url}" 2>&1',
        shell=True
    )
    return result.returncode == 0


def processChoice(selection, dic):
    """处理安装选择，自动切换代理"""
    proxy_url = ""

    # 对于git、archive、source和gazebo_source类型，尝试自动寻找可用代理
    if selection['type'] in ('git', 'archive', 'source', 'gazebo_source'):
        proxy_url = find_working_proxy(dic, selection)

    if selection['type'] == 'git':
        name = selection['name']
        url = proxy_url + selection['url']
        version = selection['version']
        download_url = f'{url}/releases/download/{version}/{name}'
        print(f'\n{CYAN}正在下载:{RESET} {download_url}')

        if download_file(download_url, f'/tmp/{name}'):
            subprocess.run(f'sudo apt install /tmp/{name} -y', shell=True)
        else:
            print(f"{RED}下载失败，请检查网络连接或手动切换代理{RESET}")
            return
    elif selection['type'] == 'wget':
        # wget类型直接使用原始URL
        url = selection['url']
        name = url.split('/')[-1]
        print(f'\n{CYAN}正在下载:{RESET} {url}')

        if download_file(url, f'/tmp/{name}'):
            subprocess.run(f'sudo apt install /tmp/{name} -y', shell=True)
        else:
            print(f"{RED}下载失败{RESET}")
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
        print(f'\n{CYAN}正在下载:{RESET} {download_url}')

        if download_file(download_url, f'/tmp/{name}'):
            # 创建安装目录（用户目录不需要sudo）
            subprocess.run(f'mkdir -p {install_path}', shell=True)
            # 解压到安装目录
            print(f'{BLUE}正在解压到 {install_path}...{RESET}')
            subprocess.run(
                f'tar -xjf /tmp/{name} -C {install_path}', shell=True)
            print(f'{GREEN}✓ ROS2 安装完成！{RESET}')
            print(f'{BLUE}使用方式:{RESET} {selection.get("setup_cmd", "")}')
            print(
                f'{YELLOW}建议添加到 ~/.zshrc:{RESET} echo "{selection.get("setup_cmd", "")}" >> ~/.zshrc')
        else:
            print(f"{RED}下载失败{RESET}")
            return
    elif selection['type'] == 'source':
        # 源码编译安装（如 ROS2）
        workspace = os.path.expanduser(
            selection.get('workspace', '~/source_build'))
        repos_url = proxy_url + selection['repos_url']

        print(f'\n{CYAN}=== ROS2 Rolling 源码编译安装 ==={RESET}')
        print(f'{BLUE}工作目录:{RESET} {workspace}')

        # 1. 系统设置
        print(f'\n{YELLOW}[1/6]{RESET} 设置系统环境...')
        subprocess.run(
            'sudo apt update && sudo apt install -y locales', shell=True)
        subprocess.run('sudo locale-gen en_US en_US.UTF-8', shell=True)
        subprocess.run(
            'sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8', shell=True)

        # 2. 添加 ROS2 apt 仓库
        print(f'\n{YELLOW}[2/6]{RESET} 添加 ROS2 apt 仓库...')
        subprocess.run(
            'sudo apt install -y software-properties-common curl', shell=True)
        subprocess.run('sudo add-apt-repository -y universe', shell=True)

        # 下载并安装 ros2-apt-source
        apt_source_deb = '/tmp/ros2-apt-source.deb'
        apt_source_url = proxy_url + \
            'https://github.com/ros-infrastructure/ros-apt-source/releases/latest/download/ros2-apt-source_latest_all.deb'
        if download_file(apt_source_url, apt_source_deb):
            subprocess.run(f'sudo dpkg -i {apt_source_deb}', shell=True)

        # 3. 安装开发工具
        print(f'\n{YELLOW}[3/6]{RESET} 安装开发工具...')
        subprocess.run('sudo apt update', shell=True)
        subprocess.run('sudo apt install -y python3-mypy python3-pip python3-pytest python3-pytest-cov python3-pytest-mock python3-pytest-repeat python3-pytest-rerunfailures python3-pytest-runner python3-pytest-timeout ros-dev-tools python3-vcstool python3-colcon-common-extensions', shell=True)

        # 4. 创建工作空间并下载源码
        print(f'\n{YELLOW}[4/6]{RESET} 创建工作空间并下载源码...')
        src_path = os.path.join(workspace, 'src')
        subprocess.run(f'mkdir -p {src_path}', shell=True)
        subprocess.run(f'wget -O /tmp/ros2.repos "{repos_url}"', shell=True)
        # 使用浅克隆 (--shallow) 加快下载速度
        subprocess.run(
            f'cd {workspace} && vcs import --shallow --input /tmp/ros2.repos src', shell=True)

        # 5. 安装依赖
        print(f'\n{YELLOW}[5/6]{RESET} 安装依赖...')
        subprocess.run('sudo rosdep init 2>/dev/null || true', shell=True)
        subprocess.run('rosdep update', shell=True)
        subprocess.run(
            f'cd {workspace} && rosdep install --from-paths src --ignore-src -y --skip-keys "fastcdr rti-connext-dds-7.7.0 urdfdom_headers"', shell=True)

        # 6. 编译
        print(f'\n{YELLOW}[6/6]{RESET} 编译 ROS2（这可能需要较长时间）...')
        result = subprocess.run(
            f'cd {workspace} && colcon build --symlink-install --packages-skip image_tools intra_process_demo', shell=True)

        if result.returncode == 0:
            print(f'\n{GREEN}✓ ROS2 源码编译安装完成！{RESET}')
            print(f'{BLUE}使用方式:{RESET} {selection.get("setup_cmd", "")}')
            print(
                f'{YELLOW}建议添加到 ~/.zshrc:{RESET} echo "{selection.get("setup_cmd", "")}" >> ~/.zshrc')
        else:
            print(f'\n{RED}✗ 编译失败，请检查错误信息{RESET}')
    elif selection['type'] == 'gazebo_source':
        # Gazebo 源码编译安装
        workspace = os.path.expanduser(
            selection.get('workspace', '~/gazebo_workspace'))
        repos_url = proxy_url + selection['repos_url']

        print(f'\n{CYAN}=== Gazebo Jetty 源码编译安装 ==={RESET}')
        print(f'{BLUE}工作目录:{RESET} {workspace}')

        # 1. 安装通用工具
        print(f'\n{YELLOW}[1/7]{RESET} 安装通用工具...')
        subprocess.run(
            'sudo apt update && sudo apt install -y python3-pip python3-venv lsb-release gnupg curl git', shell=True)

        # 2. 安装 vcstool 和 colcon
        print(f'\n{YELLOW}[2/7]{RESET} 安装 vcstool 和 colcon...')
        subprocess.run(
            'sudo apt install -y python3-vcstool python3-colcon-common-extensions', shell=True)

        # 3. 创建工作空间
        print(f'\n{YELLOW}[3/7]{RESET} 创建工作空间...')
        src_path = os.path.join(workspace, 'src')
        subprocess.run(f'mkdir -p {src_path}', shell=True)

        # 4. 下载源码
        print(f'\n{YELLOW}[4/7]{RESET} 下载 Gazebo 源码...')
        repos_file = os.path.join(workspace, 'collection-jetty.yaml')
        subprocess.run(
            f'wget -O "{repos_file}" "{repos_url}"', shell=True)
        subprocess.run(
            f'cd {src_path} && vcs import --shallow < "{repos_file}"', shell=True)

        # 5. 添加 Gazebo apt 仓库并安装 rosdep
        print(f'\n{YELLOW}[5/7]{RESET} 添加 Gazebo apt 仓库并安装 rosdep...')
        subprocess.run(
            'sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg', shell=True)
        subprocess.run(
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null', shell=True)
        subprocess.run('sudo apt-get update', shell=True)
        subprocess.run('sudo apt install -y python3-rosdep', shell=True)

        # 6. 使用 rosdep 安装依赖
        print(f'\n{YELLOW}[6/7]{RESET} 使用 rosdep 安装依赖...')
        subprocess.run('sudo rosdep init 2>/dev/null || true', shell=True)
        subprocess.run('rosdep update', shell=True)
        # 安装编译必需的依赖（protobuf等）
        print(f'  {BLUE}安装编译依赖（protobuf, jsoncpp等）...{RESET}')
        subprocess.run(
            'sudo apt install -y libprotobuf-dev protobuf-compiler libprotoc-dev libjsoncpp-dev libzip-dev', shell=True)
        subprocess.run(
            f'cd {workspace} && rosdep install -i --from-path src -y --skip-keys "gz-cmake3 DART libogre-dev libogre-next-2.3-dev"', shell=True)

        # 7. 编译
        print(f'\n{YELLOW}[7/7]{RESET} 编译 Gazebo（这可能需要较长时间，可能需要16GB内存）...')
        print(f'{YELLOW}提示:{RESET} 如果内存不足，可先执行 export CMAKE_BUILD_PARALLEL_LEVEL=1')
        result = subprocess.run(
            f'cd {workspace} && colcon build --cmake-args \' -DBUILD_TESTING=OFF\' --merge-install', shell=True)

        if result.returncode == 0:
            print(f'\n{GREEN}✓ Gazebo 源码编译安装完成！{RESET}')
            print(f'{BLUE}使用方式:{RESET} {selection.get("setup_cmd", "")}')
            print(
                f'{YELLOW}建议添加到 ~/.zshrc:{RESET} echo "{selection.get("setup_cmd", "")}" >> ~/.zshrc')
            print(f'\n{CYAN}启动 Gazebo 仿真:{RESET}')
            print(f'  {GREEN}gz sim{RESET}    # 启动仿真器')
        else:
            print(f'\n{RED}✗ 编译失败，请检查错误信息{RESET}')
    else:
        print(f'{RED}不支持的类型: {selection["type"]}{RESET}')


def toggle_proxy(dic):
    """切换代理状态"""
    proxy_config = dic.get('proxy', {})
    current_status = proxy_config.get('enabled', False)
    proxy_config['enabled'] = not current_status
    dic['proxy'] = proxy_config

    with open('packages.yaml', 'w') as f:
        yaml.dump(dic, f, allow_unicode=True, sort_keys=False)

    status = f"{GREEN}启用{RESET}" if proxy_config['enabled'] else f"{RED}禁用{RESET}"
    print(f'{CYAN}代理已{status}{RESET}')
    return dic


def switch_proxy(dic):
    """手动切换代理"""
    proxy_config = dic.get('proxy', {})
    urls = proxy_config.get('urls', [""])
    current_index = proxy_config.get('current_index', 0)

    print(f"\n{CYAN}可用代理列表:{RESET}")
    for i, url in enumerate(urls):
        marker = f" {YELLOW}(当前){RESET}" if i == current_index else ""
        display = f"{BLUE}直接连接{RESET}" if url == "" else url
        print(f"  [{YELLOW}{i}{RESET}]: {display}{marker}")

    choice = input(f"\n{YELLOW}请选择代理序号:{RESET} ")
    try:
        new_index = int(choice)
        if 0 <= new_index < len(urls):
            proxy_config['current_index'] = new_index
            dic['proxy'] = proxy_config
            with open('packages.yaml', 'w') as f:
                yaml.dump(dic, f, allow_unicode=True, sort_keys=False)
            display = f"{BLUE}直接连接{RESET}" if urls[new_index] == "" else urls[new_index]
            print(f'{GREEN}已切换到:{RESET} {display}')
        else:
            print(f"{RED}无效的选择{RESET}")
    except ValueError:
        print(f"{RED}请输入数字{RESET}")

    return dic


def show_proxy_status(dic):
    """显示当前代理状态"""
    proxy_config = dic.get('proxy', {})
    enabled = proxy_config.get('enabled', False)
    urls = proxy_config.get('urls', [""])
    current_index = proxy_config.get('current_index', 0)

    if not enabled:
        return f"{RED}已禁用{RESET}"

    if current_index < len(urls):
        current = urls[current_index]
        return f"{BLUE}直接连接{RESET}" if current == "" else current
    return f"{YELLOW}未知{RESET}"


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
        print(f'\n{CYAN}===== 软件包安装工具 ====={RESET}')
        print(f'{BLUE}当前代理:{RESET} {proxy_status}')
        print('')
        for key, val in menu.items():
            print(f'{YELLOW}[{key}]{RESET}: {val}')
        print(f'{MAGENTA}[p]{RESET}: 切换代理开关')
        print(f'{MAGENTA}[s]{RESET}: 手动选择代理')
        print(f'{MAGENTA}[0]{RESET}: 退出')
        print(' ')
        choice = input(f'{YELLOW}请输入序号:{RESET} ')

        if choice == '0':
            print(f'{GREEN}再见！{RESET}')
            break
        elif choice == 'p':
            dic = toggle_proxy(dic)
        elif choice == 's':
            dic = switch_proxy(dic)
        elif choice.isdigit() and int(choice) in menu:
            key = menu[int(choice)].split(' - ')[0]
            processChoice(dic[key], dic)
        else:
            print(f'{RED}无效的选择，请重新输入{RESET}')
