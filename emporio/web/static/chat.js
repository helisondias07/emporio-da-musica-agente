const thread = document.querySelector("#thread");
const form = document.querySelector("#composer");
const texto = document.querySelector("#texto");
const enviar = document.querySelector("#enviar");
const statusEl = document.querySelector("#status");
const chips = document.querySelector("#chips");
const limpar = document.querySelector("#limpar");

const SUGESTOES = [
  "Quais violões disponíveis até R$ 1000?",
  "Qual o endereço e o horário de sábado?",
  "Quanto custa o Takamine GD20?",
  "Pedido 7, recebi em 17/02/2026. Posso devolver?",
];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function addMessage(kind, who, body, extra) {
  const item = el("article", `msg ${kind}`);
  item.append(el("p", "who", who));
  item.append(el("p", "body", body));
  if (extra) item.append(el("p", "trace", extra));
  thread.append(item);
  thread.scrollTop = thread.scrollHeight;
  return item;
}

function opening() {
  thread.replaceChildren();
  addMessage(
    "balcao",
    "Balcão",
    "Oi. Pode falar do instrumento, do pedido ou de uma dúvida da loja."
  );
}

function renderChips() {
  chips.replaceChildren();
  for (const sugestao of SUGESTOES) {
    const button = el("button", null, sugestao);
    button.type = "button";
    button.addEventListener("click", () => send(sugestao));
    chips.append(button);
  }
}

async function loadStatus() {
  try {
    const response = await fetch("/api/estado");
    const data = await response.json();
    if (data.pronto) {
      statusEl.textContent = `Hoje na loja, ${data.hoje}`;
      statusEl.classList.remove("off");
    } else {
      statusEl.textContent = "Sem modelo nesta máquina";
      statusEl.classList.add("off");
    }
  } catch (_error) {
    statusEl.textContent = "Balcão sem resposta";
    statusEl.classList.add("off");
  }
}

async function send(value) {
  const mensagem = (value ?? texto.value).trim();
  if (!mensagem || enviar.disabled) return;
  texto.value = "";
  addMessage("cliente", "Você", mensagem);
  enviar.disabled = true;
  const pending = addMessage("balcao pending", "Balcão", "Um instante.");
  try {
    const response = await fetch("/api/mensagens", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto: mensagem }),
    });
    const data = await response.json();
    pending.remove();
    const kind = data.ok ? "balcao" : "balcao aviso";
    addMessage(kind, "Balcão", data.resposta || "Não consegui responder.", data.consulta);
  } catch (_error) {
    pending.remove();
    addMessage("balcao aviso", "Balcão", "Não consegui falar com o balcão agora.");
  } finally {
    enviar.disabled = false;
    texto.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  send();
});

texto.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    send();
  }
});

limpar.addEventListener("click", async () => {
  await fetch("/api/limpar", { method: "POST" });
  opening();
  texto.focus();
});

opening();
renderChips();
loadStatus();
texto.focus();
