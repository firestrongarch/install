import subprocess

if __name__ == '__main__':
    subprocess.run('mkdir myswapfile',shell=True)
    subprocess.run('sudo dd if=/dev/zero of=./myswapfile/swapfile bs=1G count=1',shell=True)
    subprocess.run('sudo chmod 600 ./myswapfile/swapfile',shell=True)
    subprocess.run('sudo mkswap ./myswapfile/swapfile',shell=True)
    subprocess.run('sudo swapon ./myswapfile/swapfile',shell=True)
    subprocess.run('echo "./myswapfile/swapfile none swap defaults 0 0" | sudo tee -a /etc/fstab',shell=True)