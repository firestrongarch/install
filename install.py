import subprocess
import yaml

if __name__ == '__main__':
    dic = yaml.load(open('packages.yaml', 'r'),Loader=yaml.FullLoader)
    menu = {}
    index = 1
    for key,value in dic.items():
        menu[index] = f'{key} - {value['des']}'
        index += 1
    for key,val in menu.items():
        print(f'[{key}]:{val}')

    while True:
        print(' ')
        choice = input('请输入序号(输入0退出):')
        if choice == '0':
            break
        else :
            key = menu[int(choice)].split(' ')[0]
            name = dic[key]['name']
            url = dic[key]['url']
            version = dic[key]['version']
            subprocess.run(f'sudo wget {url}/releases/download/{version}/{name} -O /tmp/{name}',shell=True)
            subprocess.run(f'sudo apt install /tmp/{name} -y',shell=True)
