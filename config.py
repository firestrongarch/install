import subprocess

if __name__ == '__main__':
    subprocess.run('sudo cp ~/.dev-sidecar/dev-sidecar.ca.crt /usr/local/share/ca-certificates',shell=True)
    subprocess.run('sudo cp ~/.dev-sidecar/dev-sidecar.ca.key.pem /usr/local/share/ca-certificates',shell=True)
    subprocess.run('sudo update-ca-certificates',shell=True)

# sudo /opt/dev-sidecar/@docmirrordev-sidecar-gui --no-sandbox