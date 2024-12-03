import subprocess

if __name__ == '__main__':
    subprocess.run('sudo dd if=/dev/zero of=/opt/myswapfile/swapfile bs=1G count=16',shell=True)
    subprocess.run('sudo chmod 600 /opt/myswapfile/swapfile',shell=True)
    subprocess.run('sudo mkswap /opt/myswapfile/swapfile',shell=True)
    subprocess.run('sudo swapon /opt/myswapfile/swapfile',shell=True)
    subprocess.run('echo "/opt/myswapfile/swapfile none swap defaults 0 0" | sudo tee -a /etc/fstab',shell=True)
