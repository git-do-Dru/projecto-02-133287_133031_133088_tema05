# Plataforma de Leilões Online em Tempo Real

Projeto desenvolvido no âmbito da unidade curricular de Laboratórios de Sistemas e Serviços.

Este projeto consiste numa plataforma de leilões online em tempo real, onde os utilizadores podem criar uma conta, consultar uma montra de leilões, entrar em salas de licitação e acompanhar lances em direto. A interface foi desenvolvida com inspiração em plataformas como o OLX, apresentando uma montra visual com vários produtos disponíveis, categorias, preços, localização e estado do leilão.

## Funcionalidades principais

A aplicação permite criar ou iniciar sessão com um nome de utilizador e palavra-passe. Cada utilizador começa com uma carteira de 10000€ para gastar em lances durante a sessão.

A página principal apresenta vários leilões ativos em formato de cartões, com informação sobre o produto, preço inicial, preço atual, categoria, localização e estado do leilão. Os leilões criados pelo próprio utilizador podem ser removidos pelo mesmo.

Os lances são gravados na base de dados. Assim, quando um utilizador entra numa sala, lança uma oferta e sai, o novo preço continua guardado e aparece depois na página principal. Ao voltar a entrar no mesmo leilão durante a mesma execução, o histórico dos lances também é carregado.

Existe também um sistema de bots que simula utilizadores a entrar em salas de leilão e a fazer licitações automaticamente. Estes bots permitem testar o funcionamento da aplicação em tempo real sem ser necessário ter vários utilizadores reais ligados ao mesmo tempo.

Para evitar testes sem concorrência, só é possível entrar e licitar em leilões quando os bots estão ativos. O backend recebe sinais periódicos dos bots e o frontend bloqueia os botões de entrada/licitação caso eles não estejam ligados.

Quando os bots saem da sala e fica apenas um utilizador durante 3 segundos, o leilão é encerrado na sessão atual. Depois disso, aparece como leilão encerrado na página principal, mostrando o preço final e o vencedor.

Sempre que o website é aberto numa nova sessão do browser, a demo é reiniciada automaticamente: utilizadores temporários, lances e estados locais anteriores são limpos, e os leilões voltam ao estado inicial.

## Tecnologias utilizadas

- FastAPI
- WebSockets
- Redis Pub/Sub
- PostgreSQL
- SQLAlchemy
- Docker
- Docker Compose
- HTML
- CSS
- JavaScript

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
│   ├── schemas.py
│   ├── script.js
│   └── style.css
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Como executar o projeto

Antes de iniciar, é necessário ter o Docker Desktop aberto e a funcionar.

No terminal, entrar na pasta do projeto:

```bash
cd ~/lss/projetos/projecto-02-133287_133031_133088_tema05
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

Atenção: caso o site não abra corretamente depois de correr `docker compose up --build`, ou caso o `localhost:8000` apareça como página de erro, basta correr o seguinte comando noutro terminal, dentro da pasta do projeto:

```bash
docker compose restart api
```

Depois é só atualizar a página no browser.

## Como ativar os bots

Com a aplicação principal já a correr, abrir um segundo terminal e entrar novamente na pasta do projeto:

```bash
cd ~/lss/projetos/projecto-02-133287_133031_133088_tema05
```

Depois executar:

```bash
docker compose exec api python app/bots.py
```

Os bots começam a entrar nas salas e a fazer lances automaticamente. Este terminal deve ficar aberto enquanto se quiser testar os leilões. Para parar os bots, basta carregar em:

```text
Ctrl + C
```

## Como utilizar a aplicação

Ao abrir o website, o utilizador deve criar ou iniciar sessão com um nome e uma palavra-passe. Se for uma conta nova, é necessário confirmar a palavra-passe.

Depois de entrar, aparece a montra de leilões disponíveis. Cada leilão apresenta o nome do produto, descrição, preço, categoria, localização e estado. O utilizador só consegue entrar nos leilões quando os bots estão ativos.

Dentro de uma sala de leilão, o utilizador pode fazer ofertas. O valor gasto é descontado da carteira do utilizador. Os bots também podem licitar e, se fizerem o maior lance antes de sair, podem ganhar o leilão.

Também existe um botão para criar um novo leilão. O utilizador pode preencher os dados do produto e publicá-lo na montra. Se o leilão tiver sido criado pelo próprio utilizador, este também o pode remover.

## Encerramento dos leilões

Os leilões encerram localmente quando, numa sala, ficam apenas o utilizador real e todos os bots já saíram. Após 3 segundos nessa situação, o leilão é marcado como encerrado, ficando registado o preço final e o vencedor.

Este estado é guardado apenas na sessão atual do browser. Ao abrir o website numa nova sessão, a demo é reiniciada.

## Autores

Projeto realizado por:

- 133287
- 133031
- 133088
