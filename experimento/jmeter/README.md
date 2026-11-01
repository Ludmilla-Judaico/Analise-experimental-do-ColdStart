# Automação dos experimentos com Apache JMeter

## Requisitos
- Apache JMeter instalado.
- Controller experimental em execução na VM Ubuntu.
- Docker instalado e imagens experimentais construídas.
- Arquivo `experimento.csv` disponível.

## Configuração
1. Abra o arquivo `cold-start-test-plan.jmx` no Apache JMeter.
2. Configure o endereço IP da VM no HTTP Request.
3. Verifique o caminho do arquivo `experimento.csv` no CSV Data Set Config.
4. Confira as configurações do Thread Group.

## Execução
Execute o plano de testes pelo Apache JMeter.

O arquivo CSV contém 480 execuções experimentais, considerando quatro runtimes, dois workloads, dois estados de cache e 30 repetições.

## Resultados
Os resultados das medições são armazenados pelo controller na VM. Os resultados de requisições do JMeter podem ser exportados separadamente.