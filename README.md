# Análise Experimental do Cold Start em Runtimes Serverless sob Diferentes Condições do Kernel Linux 

## Hardware e Software

#### Máquina virtual (ambiente onde o experimento roda)
| Item | Requisito mínimo | Recomendado |
|---|---|---|
| vCPUs | 4 | 4 ou mais | 4 |
| Memória RAM | 4 GB | 8 GB | 4,2 GiB |
| Swap | Desativado durante as medições | Desativado | 
| Disco | 25 GB | 40 GB |
| Cache de E/S do hospedeiro | Desmarcado | Desmarcado |
| Virtualizador | VirtualBox | VirtualBox atualizado | 

### Sistema operacional e kernel

| Item | Requisito | Utilizado |
|---|---|---|
| Distribuição | Ubuntu Server LTS | Ubuntu Server 26.04.1 LTS |
| Kernel Linux | 5.15 ou superior | 7.0.0-38-generic |
| Controle de grupos | cgroup v2 (`cgroup2fs`) | cgroup v2, controladores `cpuset cpu io memory ...` |
| Acesso | root (`sudo`), necessário para o `drop_caches` | `sudo` |

### Software do hospedeiro (instalado na VM)

| Software | Versão | Função no experimento |
|---|---|---|
| Docker Engine (`docker-ce`) | 24.0 ou superior; utilizada: `29.9.2` | Cria e remove os containers de cada invocação |
| containerd / runc | utilizada: `v2.4.2`, `1.5.2` | Ciclo de vida do container; compõe o `t_create_ms` |
| Storage driver | overlayfs (containerd image store) | Armazenamento das camadas das imagens |
| Cgroup driver (Docker) | systemd | Isolamento de recursos dos containers |
| GNU Time (`/usr/bin/time`) | pacote `time` do Ubuntu | Conferência manual de tempo, RSS e page faults |
| strace | utilizada: `6.19` | Contagem de chamadas de sistema (passada separada) |
| perf (opcional) | pacote `linux-tools-$(uname -r)` | Conferência de page faults; não é usado nas métricas principais |
| curl | do repositório Ubuntu | Usada para transferir dados por meio de endereços web |

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
sudo apt install -y time strace linux-tools-common linux-tools-generic "linux-tools-$(uname -r)"

/usr/bin/time --version
strace --version
perf --version
```
  
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
