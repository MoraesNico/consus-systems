// Consus — utilitários progressivos (contracts/layout-e-htmx.md §8). Sem regra de negócio.
(() => {
  "use strict";
  const ICONES = { sucesso: "circle-check", info: "info", alerta: "triangle-alert", erro: "octagon-x" };
  const global = () => document.getElementById("toasts");
  const dialogo = () => document.getElementById("dialogo");
  let acionador = null;

  // Saída animada (005): .toast--saindo; remove ao fim da animação (ou já, sem animação).
  function sair(el) {
    el.classList.add("toast--saindo");
    const duracao = parseFloat(getComputedStyle(el).animationDuration) || 0;
    if (duracao) el.addEventListener("animationend", () => el.remove(), { once: true }); else el.remove();
  }

  function temporizar(el, ms) {
    let restante = ms, inicio = 0, id = null;
    const iniciar = () => { if (id) return; inicio = Date.now(); id = setTimeout(() => sair(el), restante); };
    const pausar = () => { if (!id) return; clearTimeout(id); id = null; restante -= Date.now() - inicio; };
    ["mouseenter", "focusin"].forEach((nome) => el.addEventListener(nome, pausar));
    ["mouseleave", "focusout"].forEach((nome) => el.addEventListener(nome, iniciar));
    iniciar();
  }

  function toast(nivel, texto) {
    const modelo = document.getElementById("modelo-toast"), raiz = global();
    if (!modelo || !raiz || !texto) return;
    if (!ICONES[nivel]) nivel = "info";
    const d = dialogo();
    const regiao = (d && d.open && d.querySelector("[data-toasts]")) || raiz;
    const el = modelo.content.firstElementChild.cloneNode(true);
    el.className = `toast toast--${nivel}`;
    el.querySelector("[data-toast-texto]").textContent = texto;
    const uso = el.querySelector("[data-toast-icone] use");
    if (uso) uso.setAttribute("href", uso.getAttribute("href").replace(/#.*$/, `#${ICONES[nivel]}`));
    if (nivel === "alerta" || nivel === "erro") el.setAttribute("role", "alert");
    el.querySelector("[data-toast-fechar]").addEventListener("click", () => sair(el));
    regiao.prepend(el);
    const maximo = Number(raiz.dataset.maximo || 3);
    const atuais = regiao.querySelectorAll("[data-toast]");
    for (let i = maximo; i < atuais.length; i++) atuais[i].remove();
    if (nivel === "sucesso" || nivel === "info") temporizar(el, Number(raiz.dataset.duracaoMs || 5000));
  }

  function converterMensagens() {
    document.querySelectorAll("[data-mensagens] .aviso").forEach((aviso) => {
      const nivel = (aviso.className.match(/aviso--(\w+)/) || [])[1];
      toast(nivel, aviso.textContent.trim().replace(/\s+/g, " "));
      aviso.remove();
    });
  }

  document.addEventListener("DOMContentLoaded", converterMensagens);
  document.addEventListener("htmx:load", converterMensagens);

  // Eventos do servidor (HX-Trigger). O toast espera o fechar-dialogo do mesmo cabeçalho.
  document.addEventListener("toast", (e) => setTimeout(() => toast(e.detail.nivel, e.detail.texto), 0));
  document.addEventListener("fechar-dialogo", () => { const d = dialogo(); if (d && d.open) d.close(); });

  // Diálogo: abre ao receber conteúdo, foca o campo certo, devolve o foco ao fechar.
  document.addEventListener("htmx:beforeRequest", (e) => {
    const d = dialogo();
    if (d && e.detail.target === d && !d.open) acionador = e.detail.elt;
  });
  document.addEventListener("htmx:afterSwap", (e) => {
    const d = dialogo();
    if (!d || e.detail.target !== d || !d.firstElementChild) return;
    if (!d.open) d.showModal();
    const foco = d.querySelector('[aria-invalid="true"], [autofocus]') || d.querySelector("input, select, textarea, button");
    if (foco) foco.focus();
  });
  document.addEventListener("close", (e) => {
    if (e.target !== dialogo()) return;
    e.target.replaceChildren();
    if (acionador && acionador.isConnected) acionador.focus();
    acionador = null;
  }, true);

  // Falhas de rede/servidor viram toast de erro (exceto regiões silenciosas, como polling).
  document.addEventListener("htmx:responseError", (e) => {
    if (e.detail.elt && e.detail.elt.closest("[data-silencioso]")) return;
    toast("erro", `Não foi possível concluir a ação (erro ${e.detail.xhr.status}).`);
  });
  document.addEventListener("htmx:sendError", (e) => {
    if (e.detail.elt && e.detail.elt.closest("[data-silencioso]")) return;
    toast("erro", "Sem conexão com o servidor.");
  });

  // Atalhos declarativos: data-atalho="<tecla>" foca campos ou aciona links/botões.
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return;
    if (e.target.closest("input, textarea, select, [contenteditable]") || (dialogo() && dialogo().open)) return;
    const alvo = document.querySelector(`[data-atalho="${CSS.escape(e.key)}"]`);
    if (!alvo) return;
    e.preventDefault();
    if (alvo.matches("input, textarea, select")) alvo.focus(); else alvo.click();
  });

  // Login (006): mostrar/ocultar senha e aviso de Caps Lock.
  document.addEventListener("click", (e) => {
    const botao = e.target.closest("[data-alternar-senha]");
    const campo = botao && document.getElementById(botao.getAttribute("aria-controls"));
    if (!campo) return;
    const mostrar = campo.type === "password";
    campo.type = mostrar ? "text" : "password";
    botao.setAttribute("aria-pressed", String(mostrar));
    botao.querySelector("use").setAttribute("href", botao.querySelector("use").getAttribute("href").replace(/#.*$/, mostrar ? "#eye-off" : "#eye"));
    botao.querySelector(".visualmente-oculto").textContent = mostrar ? "Ocultar senha" : "Mostrar senha";
    campo.focus();
  });
  ["keydown", "keyup"].forEach((nome) => document.addEventListener(nome, (e) => {
    if (!e.target.matches || !e.target.matches("[data-senha]") || !e.getModifierState) return;
    const aviso = document.getElementById("aviso-caps");
    if (aviso) aviso.hidden = !e.getModifierState("CapsLock");
  }));
})();
