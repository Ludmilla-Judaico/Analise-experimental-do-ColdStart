# Análise Experimental do Cold Start em Runtimes Serverless sob Diferentes Condições do Kernel Linux 

## Hardware e Software

## Instalação de ferramentas necessárias
### Pacotes e pré-requisitos
```
  sudo apt update
  sudo apt install -y ca-certificates curl
```
### Docker
```
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
Testando Docker

```
sudo systemctl enable --now docker
sudo systemctl status docker --no-pager
sudo docker run hello-world
```

### Ferramentas de medição
```
sudo apt update
sudo apt install -y time strace linux-tools-common

/usr/bin/time --version
strace --version
perf --version
```
- Ubuntu xx.LTS
  
## Para rodar o projeto
- Abra um terminal e entre na pasta:
```
cd ~/Analise-experimental-do-ColdStart/experimento/
```
- Execute build_all.sh para criar as imagens dos apps:
```
./build_all.sh
```
- Após as imagens terem sido corretamente criadas, execute:
```
sudo taskset -c 0,1 python3 controller.py
```
- Execute as requisições pelo JMeter e veja o arquivo controller.csv ser criado com os resultados das requisições na pasta 
```
 ~/Analise-experimental-do-ColdStart/experimento/results/
```
- Para mais detalhes de como executar as requisições pelo JMeter, leia [README.md](experimento/jmeter/README.md)