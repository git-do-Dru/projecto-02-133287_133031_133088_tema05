let utilizador = null;
let utilizadorAnterior = null;
let leiloes = [];
let leilaoAtual = null;
let ws = null;
let lanceMaisAlto = 0;
let nomeVencedor = "Ninguém";
let utilizadoresAtivos = new Set();

let temporizadorEncerramento = null;
let temporizadorSemLances = null;
let intervaloCountdownSemLances = null;
let segundosSemLancesRestantes = 30;

let houveSaidaNaSala = false;
let salaEncerrada = false;
let leiloesEncerrados = {};
let botsAtivos = false;
let intervaloMontra = null;
let intervaloBots = null;

const TEMPO_SOZINHO_PARA_ENCERRAR = 10000;
const TEMPO_SEM_LANCES_PARA_ENCERRAR = 30000;

const STORAGE_ENCERRADOS = "leiloesEncerradosSessao";
const STORAGE_USER = "utilizadorLeiloesSessao";
const STORAGE_USER_ANTERIOR = "utilizadorAnteriorLeiloesSessao";
const STORAGE_SESSAO = "sessaoLeiloesAtiva";

const pageLogin = document.getElementById("pageLogin");
const pageMarket = document.getElementById("pageMarket");
const pageCreate = document.getElementById("pageCreate");
const pageRoom = document.getElementById("pageRoom");

const dadosPorTitulo = {
    "rolex submariner": {
        categoria: "Luxo",
        localizacao: "Porto",
        emoji: "⌚",
        descricao: "Relógio de luxo automático, caixa em aço inoxidável, resistente à água e em excelente estado de conservação. Ideal para colecionadores ou para quem procura uma peça premium."
    },
    "playstation 5": {
        categoria: "Gaming",
        localizacao: "Aveiro",
        emoji: "🎮",
        descricao: "Consola PlayStation 5 praticamente nova, com comando DualSense incluído, cabos originais e caixa. Ideal para jogos atuais, 4K e tempos de carregamento rápidos."
    },
    "bicicleta de montanha santa cruz": {
        categoria: "Desporto",
        localizacao: "Coimbra",
        emoji: "🚲",
        descricao: "Bicicleta de montanha Santa Cruz em cor preta, com dupla suspensão Fox, travões de disco e quadro robusto. Indicada para trilhos, downhill ligeiro e uso desportivo."
    }
};

function limparEstadoAntigoDoBrowser() {
    localStorage.removeItem("utilizadorLeiloes");
    localStorage.removeItem("utilizadorAnteriorLeiloes");
    localStorage.removeItem("leiloesEncerradosLocal");
}

async function prepararSessaoNova() {
    limparEstadoAntigoDoBrowser();

    const jaExisteSessao = sessionStorage.getItem(STORAGE_SESSAO) === "1";

    if (!jaExisteSessao) {
        sessionStorage.removeItem(STORAGE_USER);
        sessionStorage.removeItem(STORAGE_USER_ANTERIOR);
        sessionStorage.removeItem(STORAGE_ENCERRADOS);

        try {
            await fetch("/demo/reset", { method: "POST" });
        } catch (erro) {
            console.warn("Não foi possível reiniciar a demo automaticamente.", erro);
        }

        sessionStorage.setItem(STORAGE_SESSAO, "1");
    }
}

function carregarLeiloesEncerrados() {
    try {
        const guardado = sessionStorage.getItem(STORAGE_ENCERRADOS);
        return guardado ? JSON.parse(guardado) : {};
    } catch (erro) {
        return {};
    }
}

function guardarLeiloesEncerrados() {
    sessionStorage.setItem(STORAGE_ENCERRADOS, JSON.stringify(leiloesEncerrados));
}

function obterEstadoEncerrado(leilaoId) {
    return leiloesEncerrados[String(leilaoId)] || null;
}

function formatarDataHora(iso) {
    if (!iso) {
        return "";
    }

    try {
        return new Date(iso).toLocaleString("pt-PT");
    } catch (erro) {
        return iso;
    }
}

function mostrarPagina(pagina) {
    pageLogin.classList.add("hidden");
    pageMarket.classList.add("hidden");
    pageCreate.classList.add("hidden");
    pageRoom.classList.add("hidden");
    pagina.classList.remove("hidden");
}

function textoCarteira() {
    const carteira = utilizador && utilizador.carteira !== undefined ? Number(utilizador.carteira) : 10000;
    return `${carteira.toFixed(0)}€`;
}

function atualizarTopo() {
    const topUser = document.getElementById("topUser");
    const btnTrocarUser = document.getElementById("btnTrocarUser");
    const roomWallet = document.getElementById("roomWallet");

    if (utilizador) {
        topUser.innerText = `Utilizador: ${utilizador.nome} | Carteira: ${textoCarteira()}`;
        btnTrocarUser.classList.remove("hidden");
    } else {
        topUser.innerText = "Não autenticado";
        btnTrocarUser.classList.add("hidden");
    }

    if (roomWallet) {
        roomWallet.innerText = `Carteira: ${textoCarteira()}`;
    }
}

function trocarUtilizador() {
    fecharWebSocket();

    utilizadorAnterior = utilizador;
    sessionStorage.setItem(STORAGE_USER_ANTERIOR, JSON.stringify(utilizadorAnterior));
    sessionStorage.removeItem(STORAGE_USER);

    utilizador = null;
    atualizarTopo();

    document.getElementById("inputNome").value = "";
    document.getElementById("inputPassword").value = "";
    document.getElementById("inputPasswordConfirm").value = "";
    document.getElementById("loginStatus").innerText = "";

    document.getElementById("btnVoltarHeader").classList.remove("hidden");
    document.getElementById("btnTrocarUser").classList.add("hidden");

    mostrarPagina(pageLogin);
}

async function voltarAoUtilizadorAnterior() {
    const guardado = sessionStorage.getItem(STORAGE_USER_ANTERIOR);

    if (!guardado) {
        return;
    }

    utilizador = JSON.parse(guardado);
    sessionStorage.setItem(STORAGE_USER, JSON.stringify(utilizador));

    document.getElementById("btnVoltarHeader").classList.add("hidden");

    atualizarTopo();
    await carregarEstadoBots();
    await carregarLeiloes();
    mostrarPagina(pageMarket);
}

function togglePassword(inputId, botao) {
    const input = document.getElementById(inputId);

    if (input.type === "password") {
        input.type = "text";
        botao.innerText = "🙈";
    } else {
        input.type = "password";
        botao.innerText = "👁️";
    }
}

function escapeHtml(texto) {
    return String(texto || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function normalizar(texto) {
    return String(texto || "").toLowerCase().trim();
}

function deveOcultarLeilao(leilao) {
    const titulo = normalizar(leilao.titulo);
    return titulo.includes("balenciaga") || titulo.includes("whiterose") || titulo.includes("teste");
}

function aplicarDadosExtra(leilao) {
    const chave = normalizar(leilao.titulo);
    const dados = dadosPorTitulo[chave];

    if (dados) {
        leilao.categoria = dados.categoria;
        leilao.localizacao = dados.localizacao;
        leilao.emoji = dados.emoji;
        leilao.descricao = dados.descricao;
    }

    leilao.categoria = leilao.categoria || "Geral";
    leilao.localizacao = leilao.localizacao || "Portugal";
    leilao.emoji = leilao.emoji || emojiProduto(leilao.titulo);
    leilao.descricao = leilao.descricao || "Sem descrição disponível.";

    return leilao;
}

function emojiProduto(titulo) {
    const t = String(titulo || "").toLowerCase();

    if (t.includes("rolex") || t.includes("relógio") || t.includes("relogio")) return "⌚";
    if (t.includes("playstation") || t.includes("ps5")) return "🎮";
    if (t.includes("bicicleta")) return "🚲";
    if (t.includes("iphone") || t.includes("telemóvel") || t.includes("telemovel")) return "📱";
    if (t.includes("macbook") || t.includes("portátil") || t.includes("portatil") || t.includes("computador") || t.includes("pc")) return "💻";
    if (t.includes("bmw") || t.includes("carro")) return "🚗";
    if (t.includes("samsung") || t.includes("televisão") || t.includes("televisao") || t.includes("tv")) return "📺";
    if (t.includes("fender") || t.includes("guitarra")) return "🎸";
    if (t.includes("ténis") || t.includes("tenis") || t.includes("sapatilhas")) return "👟";

    return "📦";
}

async function carregarEstadoBots() {
    try {
        const resposta = await fetch("/bots/status", { cache: "no-store" });
        const dados = await resposta.json();
        botsAtivos = dados.bots_ativos === true;
    } catch (erro) {
        botsAtivos = false;
    }

    const statusHero = document.getElementById("botsStatusHero");
    const warning = document.getElementById("botWarning");

    if (statusHero) {
        statusHero.innerText = botsAtivos ? "ON" : "OFF";
    }

    if (warning) {
        if (botsAtivos) {
            warning.classList.add("hidden");
        } else {
            warning.classList.remove("hidden");
        }
    }

    if (!pageMarket.classList.contains("hidden") && leiloes.length > 0) {
        desenharMontra();
    }

    if (!pageRoom.classList.contains("hidden") && !salaEncerrada) {
        atualizarEstadoBotoesLance();
    }
}

async function existeUtilizador(nome) {
    const resposta = await fetch(`/utilizadores/existe?nome=${encodeURIComponent(nome)}`);

    if (!resposta.ok) {
        return false;
    }

    const dados = await resposta.json();
    return dados.existe;
}

async function entrarPlataforma() {
    const nome = document.getElementById("inputNome").value.trim();
    const password = document.getElementById("inputPassword").value;
    const passwordConfirm = document.getElementById("inputPasswordConfirm").value;
    const status = document.getElementById("loginStatus");

    if (!nome) {
        status.innerText = "Escreve primeiro um nome de utilizador.";
        return;
    }

    if (!password) {
        status.innerText = "Escreve uma palavra-passe.";
        return;
    }

    try {
        const existe = await existeUtilizador(nome);

        if (!existe) {
            if (!passwordConfirm) {
                status.innerText = "Para criar conta tens de confirmar a palavra-passe.";
                return;
            }

            if (password !== passwordConfirm) {
                status.innerText = "As palavras-passe não coincidem.";
                return;
            }
        } else if (passwordConfirm && password !== passwordConfirm) {
            status.innerText = "As palavras-passe não coincidem.";
            return;
        }

        const resposta = await fetch("/entrar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nome, password })
        });

        if (!resposta.ok) {
            const erro = await resposta.json().catch(() => null);
            throw new Error(erro?.detail || "Erro ao entrar.");
        }

        utilizador = await resposta.json();
    } catch (erro) {
        status.innerText = erro.message || "Erro ao entrar na plataforma.";
        return;
    }

    sessionStorage.setItem(STORAGE_USER, JSON.stringify(utilizador));
    document.getElementById("btnVoltarHeader").classList.add("hidden");
    atualizarTopo();
    await carregarEstadoBots();
    await carregarLeiloes();
    mostrarPagina(pageMarket);
}

async function carregarLeiloes() {
    const grid = document.getElementById("auctionGrid");

    if (!grid) {
        return;
    }

    if (leiloes.length === 0) {
        grid.innerHTML = "<p>A carregar leilões...</p>";
    }

    try {
        const resposta = await fetch("/leiloes", { cache: "no-store" });

        if (!resposta.ok) {
            throw new Error("Erro ao carregar leilões.");
        }

        leiloes = await resposta.json();
        leiloes = leiloes
            .filter(leilao => !deveOcultarLeilao(leilao))
            .map(aplicarDadosExtra);
    } catch (erro) {
        console.warn("A rota /leiloes falhou.", erro);
        leiloes = [];
    }

    desenharMontra();
}

function desenharMontra() {
    const grid = document.getElementById("auctionGrid");

    if (!leiloes || leiloes.length === 0) {
        grid.innerHTML = "<p>Ainda não existem leilões disponíveis.</p>";
        document.getElementById("totalLeiloes").innerText = "0";
        return;
    }

    grid.innerHTML = "";

    leiloes.forEach(leilao => {
        leilao = aplicarDadosExtra(leilao);

        const estadoEncerrado = obterEstadoEncerrado(leilao.id);
        const encerrado = estadoEncerrado !== null;

        const card = document.createElement("div");
        card.className = encerrado ? "card auction-card ended" : "card auction-card";

        const titulo = escapeHtml(leilao.titulo);
        const descricao = escapeHtml(leilao.descricao);
        const precoAtualServidor = Number(leilao.preco_atual || leilao.preco_inicial || 0);
        const precoMostrar = encerrado ? Number(estadoEncerrado.preco_final || precoAtualServidor) : precoAtualServidor;
        const precoInicial = Number(leilao.preco_inicial || precoMostrar || 0);
        const categoria = escapeHtml(leilao.categoria);
        const localizacao = escapeHtml(leilao.localizacao);
        const emoji = escapeHtml(leilao.emoji);
        const criadoPeloUtilizador = utilizador && Number(leilao.dono_id) === Number(utilizador.id);

        const badgeEstado = encerrado
            ? `<span class="badge badge-ended">Leilão encerrado</span>`
            : `<span class="badge">Leilão ativo</span>`;

        const notaEncerrado = encerrado
            ? `<div class="ended-note">
                    Vencedor: ${escapeHtml(estadoEncerrado.vencedor || "Ninguém")}<br>
                    Encerrado: ${escapeHtml(formatarDataHora(estadoEncerrado.terminado_em))}
               </div>`
            : "";

        const textoBotao = encerrado
            ? "Ver resultado"
            : botsAtivos
                ? "Entrar no leilão"
                : "Ativa os bots primeiro";

        const botaoDesativado = !encerrado && !botsAtivos ? "disabled" : "";

        card.innerHTML = `
            <div class="auction-img">${emoji}</div>
            <div class="auction-info">
                <div>
                    ${badgeEstado}
                    <span class="category-tag">${categoria}</span>

                    <div class="auction-title">${titulo}</div>
                    <div class="auction-desc">${descricao}</div>
                </div>

                <div class="auction-bottom">
                    ${notaEncerrado}

                    <div class="auction-price">${precoMostrar.toFixed(0)}€</div>
                    <div class="starting-price">
                        ${encerrado ? "Preço final" : "Preço inicial"}: ${encerrado ? precoMostrar.toFixed(0) : precoInicial.toFixed(0)}€
                    </div>

                    <button class="${encerrado ? "btn-ended" : "btn-primary"}" style="width:100%;" onclick="abrirSala(${leilao.id})" ${botaoDesativado}>
                        ${textoBotao}
                    </button>

                    ${
                        criadoPeloUtilizador && !encerrado
                            ? `<button class="btn-remove" onclick="removerLeilao(${leilao.id})">Remover o meu leilão</button>
                               <div class="owner-note">Criado por ti</div>`
                            : ""
                    }

                    <div class="auction-meta">
                        <span>📍 ${localizacao}</span>
                        <span>${encerrado ? "🔒 Encerrado" : botsAtivos ? "⚡ Em direto" : "🤖 Bots OFF"}</span>
                    </div>
                </div>
            </div>
        `;

        grid.appendChild(card);
    });

    document.getElementById("totalLeiloes").innerText = leiloes.length;
}

function mostrarMontra() {
    cancelarTemporizadorEncerramento();
    cancelarTemporizadorSemLances();
    fecharWebSocket();
    carregarLeiloes();
    mostrarPagina(pageMarket);
}

function abrirCriarLeilao() {
    document.getElementById("inputTitulo").value = "";
    document.getElementById("inputDescricao").value = "";
    document.getElementById("inputPreco").value = "";
    document.getElementById("inputCategoria").value = "";
    document.getElementById("inputLocalizacao").value = "";
    document.getElementById("inputEmoji").value = "📦";
    document.getElementById("createStatus").innerText = "";
    mostrarPagina(pageCreate);
}

async function criarLeilao() {
    const titulo = document.getElementById("inputTitulo").value.trim();
    const descricao = document.getElementById("inputDescricao").value.trim();
    const preco = Number(document.getElementById("inputPreco").value);
    const categoria = document.getElementById("inputCategoria").value.trim() || "Geral";
    const localizacao = document.getElementById("inputLocalizacao").value.trim() || "Portugal";
    const emoji = document.getElementById("inputEmoji").value || emojiProduto(titulo);
    const status = document.getElementById("createStatus");

    if (!titulo || !preco || preco <= 0) {
        status.innerText = "Preenche pelo menos o título e um preço inicial válido.";
        return;
    }

    try {
        const resposta = await fetch(`/leiloes?dono_id=${utilizador.id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                titulo: titulo,
                descricao: descricao,
                preco_inicial: preco,
                categoria: categoria,
                localizacao: localizacao,
                emoji: emoji
            })
        });

        if (!resposta.ok) {
            throw new Error("Erro ao criar leilão.");
        }

        const novoLeilao = await resposta.json();
        leiloes.push(aplicarDadosExtra(novoLeilao));
        status.innerText = "Leilão criado com sucesso.";
    } catch (erro) {
        status.innerText = "Não foi possível criar o leilão.";
        return;
    }

    desenharMontra();
    mostrarPagina(pageMarket);
}

async function removerLeilao(id) {
    const leilao = leiloes.find(l => Number(l.id) === Number(id));

    if (!leilao) {
        alert("Leilão não encontrado.");
        return;
    }

    if (Number(leilao.dono_id) !== Number(utilizador.id)) {
        alert("Só podes remover leilões criados por ti.");
        return;
    }

    const confirmar = confirm(`Tens a certeza que queres remover o leilão "${leilao.titulo}"?`);

    if (!confirmar) {
        return;
    }

    try {
        const resposta = await fetch(`/leiloes/${id}?dono_id=${utilizador.id}`, {
            method: "DELETE"
        });

        if (!resposta.ok) {
            const erro = await resposta.json().catch(() => null);
            throw new Error(erro?.detail || "Erro ao remover leilão.");
        }

        leiloes = leiloes.filter(l => Number(l.id) !== Number(id));
        delete leiloesEncerrados[String(id)];
        guardarLeiloesEncerrados();
        desenharMontra();
    } catch (erro) {
        alert(erro.message || "Não foi possível remover o leilão.");
    }
}

async function carregarHistoricoLeilao(leilaoId) {
    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML = "";

    try {
        const resposta = await fetch(`/leiloes/${leilaoId}/historico`, { cache: "no-store" });

        if (!resposta.ok) {
            throw new Error("Erro ao carregar histórico.");
        }

        const historico = await resposta.json();

        if (historico.length === 0) {
            adicionarChat("Ainda não existem lances guardados neste leilão.");
            return;
        }

        historico.forEach(lance => {
            const nome = lance.utilizador_nome || "Utilizador";
            const valor = Number(lance.valor || 0);

            adicionarChat(`🔥 <strong>${escapeHtml(nome)}</strong> cobriu a oferta com ${valor.toFixed(0)}€`);

            if (valor >= lanceMaisAlto) {
                lanceMaisAlto = valor;
                nomeVencedor = nome;
            }
        });

        document.getElementById("valorAtual").innerText = `${lanceMaisAlto.toFixed(0)}€`;

        if (nomeVencedor && nomeVencedor !== "Ninguém") {
            document.getElementById("vencedorAtual").innerText = `Líder: ${escapeHtml(nomeVencedor)}`;
        }
    } catch (erro) {
        console.warn(erro);
        adicionarChat("Não foi possível carregar o histórico guardado.");
    }
}

async function abrirSala(id) {
    if (!botsAtivos) {
        alert("Tens de ativar os bots antes de entrar num leilão. Usa: docker compose exec api python app/bots.py");
        return;
    }

    leilaoAtual = leiloes.find(l => Number(l.id) === Number(id));

    if (!leilaoAtual) {
        alert("Leilão não encontrado.");
        return;
    }

    leilaoAtual = aplicarDadosExtra(leilaoAtual);

    const estadoEncerrado = obterEstadoEncerrado(leilaoAtual.id);

    lanceMaisAlto = estadoEncerrado
        ? Number(estadoEncerrado.preco_final || leilaoAtual.preco_atual || leilaoAtual.preco_inicial || 0)
        : Number(leilaoAtual.preco_atual || leilaoAtual.preco_inicial || 0);

    nomeVencedor = estadoEncerrado ? estadoEncerrado.vencedor : "Ninguém";
    utilizadoresAtivos.clear();
    utilizadoresAtivos.add(utilizador.nome);

    houveSaidaNaSala = false;
    salaEncerrada = estadoEncerrado !== null;
    cancelarTemporizadorEncerramento();
    cancelarTemporizadorSemLances();

    document.getElementById("roomTitle").innerText = `${leilaoAtual.emoji} ${leilaoAtual.titulo}`;
    document.getElementById("roomCategoria").innerText = `Categoria: ${leilaoAtual.categoria}`;
    document.getElementById("roomLocalizacao").innerText = `Localização: ${leilaoAtual.localizacao}`;
    document.getElementById("roomPrecoInicial").innerText = `Preço inicial: ${Number(leilaoAtual.preco_inicial).toFixed(0)}€`;
    document.getElementById("valorAtual").innerText = `${lanceMaisAlto.toFixed(0)}€`;
    document.getElementById("inputAumento").value = 50;
    document.getElementById("bidStatus").innerText = "";

    const painel = document.getElementById("painelPreco");
    painel.classList.remove("ended");
    painel.style.background = "linear-gradient(135deg, #e8fafa, #ffffff)";
    painel.style.borderColor = "#23e5db";

    atualizarTopo();
    atualizarContador();
    await carregarHistoricoLeilao(leilaoAtual.id);

    if (estadoEncerrado) {
        mostrarLeilaoEncerrado(estadoEncerrado);
        mostrarPagina(pageRoom);
        return;
    }

    desbloquearLances();
    atualizarEstadoBotoesLance();
    document.getElementById("textoPainel").innerText = "Lance mais alto atual";

    if (nomeVencedor && nomeVencedor !== "Ninguém") {
        document.getElementById("vencedorAtual").innerText = `Líder: ${escapeHtml(nomeVencedor)}`;
        reiniciarTemporizadorSemLances();
    } else {
        document.getElementById("vencedorAtual").innerText = "A aguardar lances.";
    }

    adicionarChat(`<strong>${escapeHtml(utilizador.nome)}</strong> entrou no leilão.`);
    abrirWebSocket(leilaoAtual.id);
    mostrarPagina(pageRoom);
}

function abrirWebSocket(leilaoId) {
    fecharWebSocket();

    const protocolo = window.location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${protocolo}://${window.location.host}/ws/leilao/${leilaoId}`);

    ws.onopen = function() {
        adicionarChat("Ligação em tempo real ativa.");
        ws.send(`ENTROU: ${utilizador.nome}`);
    };

    ws.onmessage = function(event) {
        processarMensagem(event.data);
    };

    ws.onclose = function() {
        if (!salaEncerrada) {
            adicionarChat("Ligação ao leilão fechada.");
        }
    };

    ws.onerror = function() {
        if (!salaEncerrada) {
            adicionarChat("Erro na ligação em tempo real.");
        }
    };
}

function fecharWebSocket() {
    if (ws) {
        try {
            ws.close();
        } catch (erro) {}
        ws = null;
    }
}

function processarMensagem(dados) {
    if (salaEncerrada) {
        return;
    }

    let texto = String(dados);

    try {
        const json = JSON.parse(texto);

        if (json.tipo === "entrou") {
            const nome = json.nome || "Utilizador";
            utilizadoresAtivos.add(nome);
            adicionarChat(`👋 <strong>${escapeHtml(nome)}</strong> juntou-se ao leilão.`);
            atualizarContador();
            return;
        }

        if (json.tipo === "saiu") {
            const nome = json.nome || "Utilizador";
            houveSaidaNaSala = true;
            utilizadoresAtivos.delete(nome);
            adicionarChat(`🚪 <strong>${escapeHtml(nome)}</strong> saiu da sala.`);
            atualizarContador();
            return;
        }

        if (json.tipo === "lance" && json.sucesso) {
            const nome = json.utilizador || json.nome || "Utilizador";
            const valor = Number(json.novo_preco || json.valor || 0);

            utilizadoresAtivos.add(nome);
            atualizarPreco(valor, nome);
            reiniciarTemporizadorSemLances();

            if (utilizador && json.utilizador_id === utilizador.id && json.carteira !== undefined) {
                utilizador.carteira = Number(json.carteira);
                sessionStorage.setItem(STORAGE_USER, JSON.stringify(utilizador));
                atualizarTopo();
            }

            adicionarChat(`🔥 <strong>${escapeHtml(nome)}</strong> cobriu a oferta com ${valor.toFixed(0)}€`);
            atualizarContador();
            return;
        }

        if (json.sucesso === false) {
            adicionarChat(`⚠️ ${escapeHtml(json.mensagem || "Erro no lance.")}`);
            document.getElementById("bidStatus").innerText = json.mensagem || "Erro no lance.";
            return;
        }

        if (json.tipo === "mensagem") {
            adicionarChat(`💬 ${escapeHtml(json.texto || "")}`);
            return;
        }
    } catch (erro) {}

    texto = limparPrefixosMensagem(texto);

    if (texto.startsWith("ENTROU: ")) {
        const nome = texto.replace("ENTROU: ", "").trim();
        utilizadoresAtivos.add(nome);
        adicionarChat(`👋 <strong>${escapeHtml(nome)}</strong> juntou-se ao leilão.`);
        atualizarContador();
        return;
    }

    if (texto.startsWith("SAIU: ")) {
        const nome = texto.replace("SAIU: ", "").trim();
        houveSaidaNaSala = true;
        utilizadoresAtivos.delete(nome);
        adicionarChat(`🚪 <strong>${escapeHtml(nome)}</strong> saiu da sala.`);
        atualizarContador();
        return;
    }

    const valor = extrairValor(texto);
    const nome = extrairNome(texto);

    if (valor !== null && valor > lanceMaisAlto) {
        atualizarPreco(valor, nome);
        reiniciarTemporizadorSemLances();
    }

    if (nome) {
        utilizadoresAtivos.add(nome);
    }

    adicionarChat(`⚡ ${escapeHtml(texto)}`);
    atualizarContador();
}

function limparPrefixosMensagem(texto) {
    return String(texto || "")
        .replace("Broadcast: Nova licitação recebida: ", "")
        .replace(/^Broadcast:\s*/i, "")
        .replace(/^[^\wÀ-ÿ\[]+/u, "")
        .trim();
}

function extrairValor(texto) {
    const match = texto.match(/(\d+(?:\.\d+)?)€/);

    if (!match) {
        return null;
    }

    return Number(match[1]);
}

function extrairNome(texto) {
    const matchComParenteses = texto.match(/\[([^\]]+)\]/);

    if (matchComParenteses) {
        return matchComParenteses[1];
    }

    const partes = texto.trim().split(" ");

    if (partes.length > 0) {
        return partes[0].replace(":", "");
    }

    return null;
}

function atualizarPreco(valor, nome) {
    lanceMaisAlto = Number(valor);
    nomeVencedor = nome || "Ninguém";

    if (leilaoAtual) {
        leilaoAtual.preco_atual = lanceMaisAlto;
    }

    document.getElementById("valorAtual").innerText = `${lanceMaisAlto.toFixed(0)}€`;
    document.getElementById("vencedorAtual").innerText = `Líder: ${escapeHtml(nomeVencedor)}`;
}

function atualizarContador() {
    const total = utilizadoresAtivos.size;

    document.getElementById("contadorPessoas").innerHTML = `
        <span class="live-dot"></span>
        👥 ${total} na sala
    `;

    verificarEncerramentoPorParticipantes();
}

function verificarEncerramentoPorParticipantes() {
    if (!leilaoAtual || salaEncerrada) {
        return;
    }

    const total = utilizadoresAtivos.size;

    if (total > 1) {
        cancelarTemporizadorEncerramento();
        return;
    }

    if (total === 1 && houveSaidaNaSala && !temporizadorEncerramento) {
        document.getElementById("bidStatus").innerText = "Só ficaste tu na sala. O leilão encerra em 10 segundos...";
        adicionarChat("⏳ Só resta um participante. O leilão vai encerrar em 10 segundos se ninguém entrar.");

        temporizadorEncerramento = setTimeout(function() {
            encerrarLeilaoAtual("Só ficou uma pessoa na sala durante 10 segundos.");
        }, TEMPO_SOZINHO_PARA_ENCERRAR);
    }
}

function reiniciarTemporizadorSemLances() {
    if (!leilaoAtual || salaEncerrada) {
        return;
    }

    if (!nomeVencedor || nomeVencedor === "Ninguém") {
        return;
    }

    cancelarTemporizadorSemLances();

    segundosSemLancesRestantes = 30;

    document.getElementById("bidStatus").innerText =
        `Último lance de ${nomeVencedor}. Se ninguém licitar, encerra em ${segundosSemLancesRestantes}s.`;

    intervaloCountdownSemLances = setInterval(function() {
        segundosSemLancesRestantes -= 1;

        if (!salaEncerrada && nomeVencedor && nomeVencedor !== "Ninguém") {
            document.getElementById("bidStatus").innerText =
                `Último lance de ${nomeVencedor}. Se ninguém licitar, encerra em ${segundosSemLancesRestantes}s.`;
        }

        if (segundosSemLancesRestantes <= 0) {
            clearInterval(intervaloCountdownSemLances);
            intervaloCountdownSemLances = null;
        }
    }, 1000);

    temporizadorSemLances = setTimeout(function() {
        encerrarLeilaoAtual("Passaram 30 segundos sem novos lances.");
    }, TEMPO_SEM_LANCES_PARA_ENCERRAR);
}

function cancelarTemporizadorSemLances() {
    if (temporizadorSemLances) {
        clearTimeout(temporizadorSemLances);
        temporizadorSemLances = null;
    }

    if (intervaloCountdownSemLances) {
        clearInterval(intervaloCountdownSemLances);
        intervaloCountdownSemLances = null;
    }
}

function cancelarTemporizadorEncerramento() {
    if (temporizadorEncerramento) {
        clearTimeout(temporizadorEncerramento);
        temporizadorEncerramento = null;
    }
}

function encerrarLeilaoAtual(motivo) {
    if (!leilaoAtual || salaEncerrada) {
        return;
    }

    cancelarTemporizadorEncerramento();
    cancelarTemporizadorSemLances();

    salaEncerrada = true;

    const estado = {
        id: leilaoAtual.id,
        titulo: leilaoAtual.titulo,
        preco_final: lanceMaisAlto,
        vencedor: nomeVencedor && nomeVencedor !== "Ninguém" ? nomeVencedor : utilizador.nome,
        terminado_em: new Date().toISOString(),
        motivo: motivo || "Leilão encerrado."
    };

    leiloesEncerrados[String(leilaoAtual.id)] = estado;
    guardarLeiloesEncerrados();

    mostrarLeilaoEncerrado(estado);
    adicionarChat(`✅ Leilão encerrado. Vencedor: <strong>${escapeHtml(estado.vencedor)}</strong> por <strong>${Number(estado.preco_final).toFixed(0)}€</strong>.`);

    fecharWebSocket();
}

function mostrarLeilaoEncerrado(estado) {
    salaEncerrada = true;
    bloquearLances();

    const painel = document.getElementById("painelPreco");
    painel.classList.add("ended");
    painel.style.background = "linear-gradient(135deg, #fff1f0, #ffffff)";
    painel.style.borderColor = "#e74c3c";

    document.getElementById("textoPainel").innerText = "Leilão encerrado";
    document.getElementById("valorAtual").innerText = `${Number(estado.preco_final || lanceMaisAlto).toFixed(0)}€`;
    document.getElementById("vencedorAtual").innerText = `Vencedor: ${estado.vencedor || "Ninguém"}`;
    document.getElementById("bidStatus").innerText = `Leilão encerrado. Motivo: ${estado.motivo || "Fim do leilão."}`;
}

function atualizarEstadoBotoesLance() {
    if (salaEncerrada) {
        bloquearLances();
        return;
    }

    const btn = document.getElementById("btnLancarOferta");
    const input = document.getElementById("inputAumento");

    if (!botsAtivos) {
        btn.disabled = true;
        input.disabled = true;
        btn.innerText = "Ativa os bots primeiro";
        document.querySelectorAll(".quick-bid").forEach(botao => botao.disabled = true);
        document.getElementById("bidStatus").innerText = "Os bots têm de estar ativos para poderes licitar.";
    } else {
        desbloquearLances();
    }
}

function bloquearLances() {
    document.getElementById("inputAumento").disabled = true;
    document.getElementById("btnLancarOferta").disabled = true;
    document.getElementById("btnLancarOferta").innerText = "Leilão encerrado";

    document.querySelectorAll(".quick-bid").forEach(function(botao) {
        botao.disabled = true;
    });
}

function desbloquearLances() {
    document.getElementById("inputAumento").disabled = false;
    document.getElementById("btnLancarOferta").disabled = false;
    document.getElementById("btnLancarOferta").innerText = "Lançar oferta";

    document.querySelectorAll(".quick-bid").forEach(function(botao) {
        botao.disabled = false;
    });
}

function preencherAumento(valor) {
    if (salaEncerrada || !botsAtivos) {
        return;
    }

    document.getElementById("inputAumento").value = valor;
}

async function fazerLance() {
    const aumento = Number(document.getElementById("inputAumento").value);
    const status = document.getElementById("bidStatus");

    if (!botsAtivos) {
        status.innerText = "Os bots têm de estar ativos para poderes licitar.";
        return;
    }

    if (salaEncerrada) {
        status.innerText = "Este leilão já terminou.";
        return;
    }

    if (!aumento || aumento <= 0) {
        status.innerText = "Insere um aumento válido.";
        return;
    }

    if (utilizador && aumento > Number(utilizador.carteira || 0)) {
        status.innerText = `Saldo insuficiente. Tens ${textoCarteira()} na carteira.`;
        return;
    }

    const novoValor = lanceMaisAlto + aumento;

    status.innerText = "A guardar lance na base de dados...";

    try {
        const resposta = await fetch(`/leiloes/${leilaoAtual.id}/licitar`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                utilizador_id: utilizador.id,
                nome: utilizador.nome,
                valor: novoValor
            })
        });

        const dados = await resposta.json().catch(() => null);

        if (!resposta.ok) {
            throw new Error(dados?.detail || "Erro ao guardar lance.");
        }

        if (dados.carteira !== undefined) {
            utilizador.carteira = Number(dados.carteira);
            sessionStorage.setItem(STORAGE_USER, JSON.stringify(utilizador));
            atualizarTopo();
        }

        status.innerText = "Lance guardado. A aguardar atualização em tempo real...";

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            processarMensagem(JSON.stringify(dados));
        }
    } catch (erro) {
        status.innerText = erro.message || "Não foi possível guardar o lance.";
    }
}

function sairLeilao() {
    cancelarTemporizadorEncerramento();
    cancelarTemporizadorSemLances();

    if (ws && ws.readyState === WebSocket.OPEN && !salaEncerrada) {
        ws.send(`SAIU: ${utilizador.nome}`);
    }

    fecharWebSocket();
    mostrarMontra();
}

function adicionarChat(html) {
    const chatBox = document.getElementById("chatBox");
    const item = document.createElement("div");

    item.className = "chat-item";
    item.innerHTML = html;

    chatBox.appendChild(item);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function reiniciarSiteLeiloes() {
    const confirmar = confirm(
        "Queres mesmo reiniciar o site/leilões?\n\nIsto vai apagar os lances, repor os preços iniciais, repor as carteiras para 10000€ e voltar ao login."
    );

    if (!confirmar) {
        return;
    }

    cancelarTemporizadorEncerramento();
    cancelarTemporizadorSemLances();
    fecharWebSocket();

    try {
        await fetch("/demo/reset", {
            method: "POST"
        });
    } catch (erro) {
        alert("Não foi possível reiniciar a demo pelo backend. Vou limpar o browser na mesma.");
    }

    sessionStorage.removeItem(STORAGE_USER);
    sessionStorage.removeItem(STORAGE_USER_ANTERIOR);
    sessionStorage.removeItem(STORAGE_ENCERRADOS);
    sessionStorage.removeItem(STORAGE_SESSAO);

    localStorage.removeItem("utilizadorLeiloes");
    localStorage.removeItem("utilizadorAnteriorLeiloes");
    localStorage.removeItem("leiloesEncerradosLocal");

    location.reload();
}

function iniciarAtualizacoesAutomaticas() {
    if (intervaloBots) {
        clearInterval(intervaloBots);
    }

    if (intervaloMontra) {
        clearInterval(intervaloMontra);
    }

    intervaloBots = setInterval(carregarEstadoBots, 3000);

    intervaloMontra = setInterval(function() {
        if (utilizador && !pageMarket.classList.contains("hidden")) {
            carregarLeiloes();
        }
    }, 5000);
}

window.onload = async function() {
    await prepararSessaoNova();
    leiloesEncerrados = carregarLeiloesEncerrados();

    const guardado = sessionStorage.getItem(STORAGE_USER);

    await carregarEstadoBots();
    iniciarAtualizacoesAutomaticas();

    if (guardado) {
        utilizador = JSON.parse(guardado);
        atualizarTopo();
        await carregarLeiloes();
        mostrarPagina(pageMarket);
    } else {
        atualizarTopo();
        mostrarPagina(pageLogin);
    }
};