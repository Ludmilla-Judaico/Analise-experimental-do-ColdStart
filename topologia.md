Uma possibilidade bastante interessante seria desenvolver um experimento para avaliar o impacto de diferentes configurações e mecanismos do kernel Linux sobre a latência de cold start de aplicações serverless.

Esse experimento pode ser realizado em um único computador Linux, utilizando containers Docker, sem necessidade de uma infraestrutura de nuvem pública. Entretanto, para que os resultados tenham relevância científica, é importante reproduzir algumas características fundamentais de uma plataforma serverless, especialmente a criação de instâncias sob demanda, a execução de funções e a destruição ou reutilização dos ambientes de execução.

Minha sugestão seria estruturar o experimento em três componentes:

1. Aplicação serverless: uma função simples, implementada em Python, Go ou C, disponibilizada por meio de uma API HTTP.
2. Ambiente de execução: containers Linux criados sob demanda, utilizando Docker ou containerd, ou uma plataforma como OpenFaaS ou Knative.
3. Instrumentação do kernel: ferramentas como eBPF, perf e ftrace, para identificar quais operações do kernel contribuem mais significativamente para a latência de inicialização.

## 1. O que exatamente medir?

O cold start ocorre quando uma requisição chega e não existe uma instância pronta para executar a função.

Fluxo de execução de uma função serverless

A latência observada pelo cliente pode ser decomposta em:

\\[ T\_{\mathrm{total}} = T\_{\mathrm{provisionamento}} + T\_{\mathrm{runtime}} + T\_{\mathrm{função}} + T\_{\mathrm{comunicação}} \\]

Essa é uma decomposição simplificada. O provisionamento pode envolver operações como criação de namespaces, configuração de cgroups, montagem de sistemas de arquivos e inicialização de processos.

O objetivo principal seria identificar quanto cada subsistema do kernel contribui para o tempo de inicialização e como essa contribuição varia em diferentes condições de operação.

## 2. Como simular uma aplicação serverless?

Eu consideraria duas abordagens complementares.

### Abordagem A — Simulador simplificado utilizando Docker

É a alternativa que recomendo para começar, pois permite isolar o impacto do kernel sem introduzir toda a complexidade de uma plataforma de orquestração.

A ideia é implementar um pequeno controlador que recebe requisições HTTP e inicia um container para executar a função solicitada.

Arquitetura do experimento

Gerador de carga

HTTP / Python / k6

Controlador Serverless

Recebe requisição e cria container sob demanda

Função A

Container

Função B

Container

Função C

Container

Kernel Linux

Scheduler · cgroups · Memória · VFS · Rede

Instrumentação eBPF / perf

O controlador executaria as seguintes operações:

1. Recebe uma requisição HTTP.
2. Verifica se existe uma instância da função disponível.
3. Caso não exista, solicita a criação de um container.
4. Aguarda a inicialização do ambiente de execução.
5. Encaminha a requisição para a função.
6. Retorna o resultado ao cliente.
7. Remove o container após a execução ou um período de inatividade.

Isso permite simular dois cenários:

- Cold start: nenhuma instância disponível; é necessário iniciar um container.
- Warm start: uma instância já está disponível para receber a requisição.

### Exemplo de uma função serverless

Uma função Python utilizando Flask:

```
# app.pyfrom flask import Flask, jsonifyimport timeimport osapp = Flask(__name__)@app.route("/invoke")def invoke():    start = time.perf_counter_ns()    result = sum(i * i for i in range(10000))    elapsed = time.perf_counter_ns() - start    return jsonify({        "result": result,        "execution_ns": elapsed,        "pid": os.getpid()    })if __name__ == "__main__":    app.run(host="0.0.0.0", port=8080)
```

O Dockerfile correspondente:

```
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY app.py .

CMD ["python", "app.py"]
```

Para construir a imagem:

```
docker build -t serverless-function .
```

Para um primeiro experimento, podemos utilizar um script Python que cria um container, aguarda a disponibilidade da função, executa uma requisição e remove o container.

```
import subprocessimport requestsimport timedef cold_start():    start = time.perf_counter_ns()    container_id = subprocess.check_output([        "docker", "run", "-d",        "-p", "127.0.0.1::8080",        "serverless-function"    ], text=True).strip()    try:        port_info = subprocess.check_output([            "docker", "port", container_id, "8080/tcp"        ], text=True).strip()        port = port_info.splitlines()[0].rsplit(":", 1)[1]        url = f"http://127.0.0.1:{port}/invoke"        deadline = time.monotonic() + 30        while True:            try:                response = requests.get(url, timeout=1)                response.raise_for_status()                break            except requests.RequestException:                if time.monotonic() >= deadline:                    raise TimeoutError("Function startup timeout")                time.sleep(0.01)        elapsed = (time.perf_counter_ns() - start) / 1e6        return elapsed    finally:        subprocess.run(            ["docker", "rm", "-f", container_id],            stdout=subprocess.DEVNULL,            stderr=subprocess.DEVNULL        )for i in range(100):    latency = cold_start()    print(f"Iteration {i}: {latency:.2f} ms")
```

Esse script mede o tempo entre a solicitação de criação do container e a primeira resposta bem-sucedida da função.

É importante observar que esse valor não representa exclusivamente a latência do kernel. Ele inclui Docker, runtime, inicialização da aplicação, comunicação HTTP e execução da função. O experimento pressupõe que a imagem já esteja disponível localmente.

O controlador completo precisaria de uma etapa adicional: receber a requisição original e encaminhá-la à função criada. O script apresentado é um protótipo para medir a inicialização, não uma plataforma serverless completa.

## 3. Quais condições do kernel Linux poderiam ser avaliadas?

Aqui está a parte mais interessante do ponto de vista de pesquisa.

Eu organizaria os experimentos em cinco dimensões.

| Dimensão                 | Condições experimentais                                             | Hipótese                                                      |
| ------------------------ | ------------------------------------------------------------------- | ------------------------------------------------------------- |
| Escalonamento de CPU     | Sistema ocioso, carga moderada e elevada                            | Contenção de CPU aumenta o tempo de inicialização             |
| Gerenciamento de memória | Memória disponível, pressão de memória e reclaim                    | Page faults e reclaim aumentam o cold start                   |
| Sistema de arquivos      | Cache aquecido, cache frio e diferentes mecanismos de armazenamento | A inicialização é sensível ao acesso a arquivos               |
| cgroups                  | Diferentes limites de CPU e memória                                 | Restrições de recursos podem aumentar a latência              |
| Concorrência             | 1, 5, 10, 20 e 50 inicializações simultâneas                        | A contenção dos recursos do kernel prejudica a escalabilidade |

Um aspecto importante seria distinguir a configuração do kernel do estado de operação do kernel. Por exemplo, aumentar a carga de CPU não altera a configuração do escalonador, mas modifica as condições em que ele executa.

### Exemplo: impacto da contenção de CPU

Com `stress-ng`, podemos produzir diferentes níveis de carga:

```
# Carga concorrente de CPU
stress-ng --cpu 4 --timeout 120s
```

Durante a execução, o controlador realiza sucessivas inicializações das funções.

Podemos comparar:

- Cold start com CPU ociosa.
- Cold start com carga concorrente moderada.
- Cold start com carga concorrente elevada.

Também seria interessante limitar os recursos do container:

```
docker run --cpus="0.5" serverless-function
```

Nesse caso, estamos avaliando o impacto das restrições de CPU impostas pelo mecanismo de cgroups.

### Exemplo: impacto da memória

Para gerar pressão de memória:

```
stress-ng --vm 2 \
          --vm-bytes 512M \
          --timeout 120s
```

A quantidade de memória utilizada deve ser ajustada à RAM disponível.

Podemos monitorar:

```
cat /proc/pressure/memory
cat /proc/pressure/cpu
cat /proc/pressure/io
```

Essas interfaces fornecem informações de Pressure Stall Information (PSI), permitindo relacionar os períodos de espera por recursos com a latência observada.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://cdn.kernel.org\&sz=32)

The Linux Kernel documentation

+1



## 4. Como utilizar eBPF para investigar o cold start?

Uma contribuição científica relevante seria não apenas medir o cold start, mas identificar quais operações internas do kernel são responsáveis pelo aumento da latência.

Por exemplo:

| Subsistema          | Eventos a investigar                       | Informações                       |
| ------------------- | ------------------------------------------ | --------------------------------- |
| Scheduler           | `sched_switch`, `sched_wakeup`             | Tempo de espera por CPU           |
| Processos           | `sched_process_fork`, `sched_process_exec` | Criação e execução de processos   |
| Memória             | Page faults, reclaim                       | Custo de inicialização e alocação |
| Sistema de arquivos | Operações de abertura e leitura            | Acesso a bibliotecas e arquivos   |
| Rede                | Eventos TCP e processamento de pacotes     | Custo de comunicação              |

Uma abordagem inicial seria utilizar `bpftrace`:

```
sudo bpftrace -e '
tracepoint:sched:sched_process_exec
{
    printf("PID=%d COMM=%s\n", pid, comm);
}'
```

Isso permite identificar a execução de novos programas durante a inicialização dos containers.

Entretanto, para medir precisamente o tempo gasto nas diferentes etapas, seria necessário correlacionar os eventos do kernel com os identificadores dos containers, PIDs e timestamps coletados pelo controlador.

Uma implementação mais avançada poderia utilizar programas eBPF baseados em libbpf, registrando os eventos em buffers e associando-os a cada invocação serverless.

## 5. Abordagem B — Utilizando Knative

Depois de validar o experimento simplificado, seria interessante utilizar uma plataforma serverless real.

O Knative Serving oferece o mecanismo de scale to zero, permitindo reduzir o número de instâncias a zero quando não existem requisições.

Quando uma nova requisição chega, o sistema inicia novamente as instâncias necessárias.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://knative.dev\&sz=32)

Knative

+1



Isso permitiria comparar dois ambientes:

| Característica           | Simulador Docker              | Knative                    |
| ------------------------ | ----------------------------- | -------------------------- |
| Criação sob demanda      | Implementada pelo experimento | Nativa                     |
| Scale to zero            | Implementado pelo controlador | Nativo                     |
| Controle experimental    | Elevado                       | Menor                      |
| Complexidade             | Baixa                         | Moderada/alta              |
| Overhead de orquestração | Reduzido                      | Presente                   |
| Representatividade       | Modelo simplificado           | Plataforma serverless real |

A vantagem científica seria investigar se os gargalos identificados no simulador também aparecem em uma plataforma real.

Uma ressalva: o Knative introduz componentes adicionais, como autoscaler e Activator. Portanto, sua latência de inicialização não deve ser comparada diretamente à do Docker como se ambos executassem exatamente o mesmo processo.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



## 6. Como organizar a avaliação experimental?

Eu começaria com uma matriz experimental relativamente pequena.

Matriz experimental inicial

Configurável

Selecione os cenários que deseja incluir na primeira campanha de medições.

CPU ociosa

CPU sob carga

Memória sem pressão

Memória sob pressão

Cache aquecido

Cache frio

Repetições por cenário

100

Total de execuções planejadas

# 600

Distribuídas em 6 cenários experimentais

Elaborar protocolo para os cenários selecionados&#x20;

Para cada cenário, recomendo registrar:

- Latência total do cold start, em milissegundos.
- Tempo de criação e inicialização do container.
- Tempo de inicialização da aplicação.
- Tempo de execução da função.
- Número de context switches e page faults.
- Utilização e pressão de CPU, memória e I/O.

A análise deve apresentar mediana, média, desvio-padrão, percentis P95 e P99 e intervalos de confiança.

Também recomendo randomizar a ordem dos cenários, executar rodadas independentes e manter constantes as versões do kernel, Docker e runtime. Para o cenário de cache frio, é necessário definir exatamente quais caches serão controlados, evitando confundir cache de imagens Docker com page cache do Linux.

## 7. Possível contribuição científica

O experimento poderia evoluir para um tema de pesquisa com o seguinte título:

Investigating Linux Kernel Resource Management Effects on Serverless Cold Start Latency

Uma questão central seria:

How do Linux kernel resource management mechanisms influence serverless cold start latency under different resource contention conditions?

A partir dessa questão, seria possível investigar não apenas o desempenho, mas também oportunidades de otimização.

Por exemplo, utilizar métricas coletadas via eBPF para orientar decisões de alocação de recursos ou de manutenção de instâncias aquecidas.

Isso permitiria uma evolução em duas etapas: inicialmente caracterizar os gargalos e, posteriormente, propor e avaliar um mecanismo de otimização.

## 8. Minha sugestão de implementação

Para um trabalho experimental com foco no kernel Linux, eu seguiria esta sequência:

1. Fase 1: implementar o controlador serverless simplificado com Docker e uma função HTTP.
2. Fase 2: instrumentar o controlador para decompor a latência de inicialização.
3. Fase 3: utilizar eBPF para correlacionar os tempos com eventos do kernel.
4. Fase 4: executar os cenários de contenção de CPU, memória e I/O.
5. Fase 5: reproduzir os experimentos mais relevantes em Knative.

O ponto que considero mais promissor é a correlação entre os eventos internos do kernel e a degradação da latência de cold start, principalmente em condições de contenção de recursos.

Uma distinção metodológica fundamental é separar a latência da primeira invocação, observada pelo cliente, da latência de inicialização propriamente dita. Isso ajudaria a demonstrar quais componentes são realmente afetados pelo kernel.

Para a primeira implementação, eu utilizaria Docker + Python + bpftrace + stress-ng, mantendo o Knative para a etapa de validação. Essa combinação permite montar um testbed reprodutível, com controle dos cenários experimentais, sem depender inicialmente de Kubernetes ou de infraestrutura de nuvem pública.
