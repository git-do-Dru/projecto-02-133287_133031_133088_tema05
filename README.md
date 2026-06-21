# Plataforma de Leilões Online em Tempo Real

Projeto desenvolvido no âmbito da unidade curricular de Laboratórios de Sistemas e Serviços.

Este projeto consiste numa plataforma de leilões online em tempo real, onde os utilizadores podem criar uma conta, consultar uma montra de leilões, entrar em salas de licitação e acompanhar lances em direto. A interface foi desenvolvida com inspiração em plataformas como o OLX, apresentando uma montra visual com vários produtos disponíveis, categorias, preços, localização e estado do leilão.

## Funcionalidades principais

A aplicação permite criar ou iniciar sessão com um nome de utilizador e palavra-passe. Cada utilizador pode entrar em leilões existentes, acompanhar os lances em tempo real e lançar novas ofertas. Também é possível criar novos leilões através de um formulário próprio, indicando título, descrição, preço inicial, categoria, localização e ícone representativo.

A página principal apresenta vários leilões ativos em formato de cartões, com informação sobre o produto, preço inicial, preço atual, categoria, localização e estado do leilão. Os leilões criados pelo próprio utilizador podem ser removidos pelo mesmo.

Existe também um sistema de bots que simula utilizadores a entrar em salas de leilão e a fazer licitações automaticamente. Estes bots permitem testar o funcionamento da aplicação em tempo real sem ser necessário ter vários utilizadores reais ligados ao mesmo tempo.

Quando os bots saem da sala e fica apenas um utilizador durante 3 segundos, o leilão é encerrado localmente nesse computador. Depois disso, aparece como leilão encerrado na página principal, mostrando o preço final e o vencedor. Esta informação é guardada no `localStorage` do navegador, ou seja, fica apenas guardada nesse computador/browser.

## Tecnologias utilizadas

* FastAPI
* WebSockets
* Redis Pub/Sub
* PostgreSQL
* SQLAlchemy
* Docker
* Docker Compose
* HTML
* CSS
* JavaScript

## Estrutura do projeto

```text
.
├── app/
│   ├── bots.py
│   ├── crud.py
│   ├── database.py
│   ├── index.html
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   └── schemas.py
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Como executar o projeto

Antes de iniciar, é necessário ter o Docker Desktop aberto e a funcionar.

No terminal, entrar na pasta do projeto:

```bash
cd ~/lss/projetos/projecto-02-133287_133031_133088_tema05 (Exemplo)
```

Depois iniciar os serviços com Docker Compose:

```bash
docker compose up --build
```

Quando aparecer a mensagem de que a aplicação arrancou corretamente, abrir no navegador:

```text
http://localhost:8000
```

A documentação automática da API pode ser consultada em:

```text
http://localhost:8000/docs
```

## Como ativar os bots

Com a aplicação principal já a correr, abrir um segundo terminal e entrar novamente na pasta do projeto:

```bash
cd ~/lss/projetos/projecto-02-133287_133031_133088_tema05 (Exemplo)
```

Depois executar:

```bash
docker compose exec api python app/bots.py
```

Os bots começam a entrar nas salas e a fazer lances automaticamente. Para parar os bots, basta carregar em:

```text
Ctrl + C
```

## Como utilizar a aplicação

Ao abrir o website, o utilizador deve criar ou iniciar sessão com um nome e uma palavra-passe. Se for uma conta nova, é necessário confirmar a palavra-passe.

Depois de entrar, aparece a montra de leilões disponíveis. Cada leilão apresenta o nome do produto, descrição, preço, categoria, localização e estado. O utilizador pode entrar numa sala de leilão e fazer ofertas em tempo real.

Também existe um botão para criar um novo leilão. O utilizador pode preencher os dados do produto e publicá-lo na montra. Se o leilão tiver sido criado pelo próprio utilizador, este também o pode remover.

## Encerramento dos leilões

Os leilões encerram localmente quando, numa sala, ficam apenas o utilizador real e todos os bots já saíram. Após 3 segundos nessa situação, o leilão é marcado como encerrado, ficando registado o preço final e o vencedor.

Este estado é guardado localmente no browser através do `localStorage`. Por isso, o encerramento é apenas local ao computador/navegador onde aconteceu.

## Autores

Projeto realizado por:

* 133287
* 133031
* 133088
