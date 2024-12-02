import subprocess
import yaml

def processChoice(selection):
    if selection['type'] == 'git':
        name = selection['name']
        url = selection['url']
        version = selection['version']
        subprocess.run(f'sudo wget {url}/releases/download/{version}/{name} -O /tmp/{name}',shell=True)
        subprocess.run(f'sudo apt install /tmp/{name} -y',shell=True)
    elif selection['type'] == 'config':
        for cmd in selection['cmd']:
            subprocess.run(cmd,shell=True)
    else :
        print('不支持的类型')

if __name__ == '__main__':
    dic = yaml.load(open('packages.yaml', 'r'),Loader=yaml.FullLoader)
    menu = {}
    index = 1
    for key,value in dic.items():
        menu[index] = f'{key} - {value['des']}'
        index += 1

    while True:
        for key,val in menu.items():
            print(f'[{key}]:{val}')
        print(' ')
        choice = input('请输入序号(输入0退出):')
        if choice == '0':
            break
        else :
            key = menu[int(choice)].split(' ')[0]
            processChoice(dic[key])

