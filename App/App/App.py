import reflex as rx
import sys
import os
from dotenv import load_dotenv

# --- SETUP DE CAMINHO ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(root_dir, ".env")) # Carrega do root
if root_dir not in sys.path: sys.path.insert(0, root_dir)

import Backend.banco_dados_pg as banco_dados
import Backend.LLM.ia_manager as ia_manager
import Backend.auth_manager as auth_manager

# --- FIREBASE SETUP ---
firebase_script = f"""
import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import {{ getAuth, GoogleAuthProvider, signInWithPopup }} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";

const firebaseConfig = {{
  apiKey: "{os.getenv('FIREBASE_API_KEY')}",
  authDomain: "{os.getenv('FIREBASE_AUTH_DOMAIN')}",
  projectId: "{os.getenv('FIREBASE_PROJECT_ID')}",
  storageBucket: "{os.getenv('FIREBASE_STORAGE_BUCKET')}",
  messagingSenderId: "{os.getenv('FIREBASE_MESSAGING_SENDER_ID')}",
  appId: "{os.getenv('FIREBASE_APP_ID')}"
}};

const firebaseApp = initializeApp(firebaseConfig);
const firebaseAuth = getAuth(firebaseApp);
const googleProvider = new GoogleAuthProvider();

// Armazena o token globalmente para o Reflex buscar via callback
window._googleIdToken = null;

window.loginWithGoogle = async () => {{
  try {{
    const result = await signInWithPopup(firebaseAuth, googleProvider);
    const token = await result.user.getIdToken();
    window._googleIdToken = token;
    return token;
  }} catch (error) {{
    console.error("Erro no login Google:", error);
    alert("Falha no login: " + error.message);
    return null;
  }}
}};
"""

def firebase_init():
    return rx.script(firebase_script, type="module")

def auth_bridge():
    """Script vazio - o login agora é feito diretamente via on_click com callback do Reflex."""
    return rx.fragment()

class State(rx.State):
    usuario_id: int = 0
    login_username: str = ""
    nome_usuario: str = "Visitante"
    user_input: str = ""
    messages: list[dict] = []
    is_processing: bool = False
    sentiment: str = "Neutro"
    interaction_count: int = 0
    tema: str = "hacker" 

    def set_tema(self, val): self.tema = val
    is_logged_in: bool = False
    show_onboarding: bool = False
    onboarding_step: int = 1
    onboarding_nome: str = ""
    onboarding_gosta: str = ""
    onboarding_bom: str = ""
    onboarding_precisa: str = ""
    onboarding_pago: str = ""
    
    humores: list[dict] = [
        {"e": "😊", "l": "Feliz"}, {"e": "😔", "l": "Triste"},
        {"e": "😤", "l": "Ansioso"}, {"e": "🤔", "l": "Reflexivo"}
    ]
    
    is_sending: bool = False
    insight_input: str = ""
    last_insight: str = "Tudo começa com um pequeno passo..."
    history_trail: list[dict] = []
    projeto_id: int = 0
    projeto_nome: str = "Nenhum Projeto Ativo"
    projeto_objetivo: str = ""
    projeto_passo: int = 1
    projeto_frase: str = "Início da Jornada"
    jornada_passos: list[dict] = []
    proposito_sugerido: str = "Tudo começa com um pequeno passo..."
    selected_pilar: str = ""
    pilar_content: str = ""

    def select_pilar(self, pilar: str):
        self.selected_pilar = pilar
        if pilar == "PAIXÃO": self.pilar_content = self.onboarding_gosta or "Você ainda não definiu o que ama."
        elif pilar == "TALENTO": self.pilar_content = self.onboarding_bom or "Você ainda não definiu no que é bom."
        elif pilar == "MISSÃO": self.pilar_content = self.onboarding_precisa or "Você ainda não definiu o que o mundo precisa."
        elif pilar == "RENDA": self.pilar_content = self.onboarding_pago or "Você ainda não definiu pelo que pode ser pago."
        else: self.pilar_content = ""

    def set_insight_input(self, val: str): self.insight_input = val
    def set_user_input(self, val: str): self.user_input = val
    def set_sentiment(self, val: str): self.sentiment = val
    def set_onboarding_nome(self, val: str): self.onboarding_nome = val
    def set_onboarding_gosta(self, val: str): self.onboarding_gosta = val
    def set_onboarding_bom(self, val: str): self.onboarding_bom = val
    def set_onboarding_precisa(self, val: str): self.onboarding_precisa = val
    def set_onboarding_pago(self, val: str): self.onboarding_pago = val
    def set_onboarding_step(self, step: int): self.onboarding_step = step
    def next_onboarding_step(self): self.onboarding_step += 1
    def prev_onboarding_step(self): self.onboarding_step -= 1

    def finish_onboarding(self):
        success = banco_dados.atualizar_perfil_ikigai(
            self.usuario_id, self.onboarding_nome, self.onboarding_gosta,
            self.onboarding_bom, self.onboarding_precisa, self.onboarding_pago
        )
        if success:
            self.nome_usuario = self.onboarding_nome
            self.show_onboarding = False
            return rx.toast.info("Perfil Ikigai atualizado! Bem-vindo.", position="top-center")

    def save_insight(self):
        if not self.insight_input: return
        success = banco_dados.adicionar_insight(self.usuario_id, self.insight_input)
        if success:
            self.last_insight = self.insight_input
            self.insight_input = ""
            return rx.toast.success("Insight guardado com carinho.")

    def on_load(self):
        if self.usuario_id == 0:
            self.is_logged_in = False
            return
        self.show_onboarding = False 
        perfil = banco_dados.buscar_dados_usuario(self.usuario_id)
        if perfil:
            self.nome_usuario = perfil["nome"]
            self.onboarding_nome = perfil["nome"]
            self.onboarding_gosta = perfil["gosta_fazer"]
            self.onboarding_bom = perfil["bom_em"]
            self.onboarding_precisa = perfil["mundo_precisa"]
            self.onboarding_pago = perfil["pago_para"]
            self.is_logged_in = True
        entries = banco_dados.buscar_insights_usuario(self.usuario_id, limite=1)
        if entries:
            self.last_insight = entries[0][1]
        ts = banco_dados.buscar_trilhas(self.usuario_id, limite=4)
        historico_invertido = list(reversed(ts))
        self.history_trail = []
        for i, t in enumerate(historico_invertido):
            resumo_curto = t[1][:75] + "..." if len(t[1]) > 75 else t[1]
            self.history_trail.append({"index": str(i+1), "title": f"Sessão {i+1}", "resumo": resumo_curto, "full": t[1]})
        projeto_data = banco_dados.buscar_projeto_ativo(self.usuario_id)
        if projeto_data:
            self.projeto_id = projeto_data["id"]
            self.projeto_nome = projeto_data["nome_projeto"]
            self.projeto_objetivo = projeto_data["objetivo_geral"]
            self.projeto_passo = projeto_data["passo_atual"]
            fases = {1: "Plantando Sementes 🧬", 2: "Explorando Horizontes 🌏", 3: "Conectando Pontos 🔗", 4: "Manifestando Intenção ✨", 5: "Colhendo Frutos 🍎"}
            self.projeto_frase = fases.get(self.projeto_passo, "Caminhando...")
            if self.onboarding_gosta and self.onboarding_precisa:
                g_txt = self.onboarding_gosta.replace("Eu amo ", "").replace("Eu gosto de ", "").strip()
                p_txt = self.onboarding_precisa.replace("Eu sinto que o mundo precisa de ", "").replace("O mundo precisa de ", "").strip()
                g = (g_txt[:250] + "...") if len(g_txt) > 250 else g_txt
                p = (p_txt[:250] + "...") if len(p_txt) > 250 else p_txt
                self.proposito_sugerido = f"Use sua paixão por '{g}' para suprir a necessidade de '{p}' no mundo hoje."
            else:
                self.proposito_sugerido = "Baseado no seu Ikigai, hoje é um bom dia para focar no seu propósito."
        if self.projeto_id:
            passos = banco_dados.buscar_jornada_passos(self.projeto_id)
            self.jornada_passos = [{"num": p[0], "resumo": p[1]} for p in passos]

    def logout(self):
        self.is_logged_in = False
        self.usuario_id = 0
        self.messages = []
        yield rx.redirect("/")

    def handle_google_login(self, id_token: str):
        if not id_token:
            return rx.toast.error("Login cancelado ou token inválido.")
        user_info = auth_manager.verify_google_token(id_token)
        if not user_info or "error" in user_info:
            msg = user_info.get("error", "Falha na autenticação.") if user_info else "Falha na autenticação."
            return rx.toast.error(msg)
        firebase_uid = user_info.get("uid")
        email = user_info.get("email")
        nome = user_info.get("name")
        username = email.split("@")[0] if email else f"user_{firebase_uid[:8]}"
        user_data = banco_dados.buscar_ou_criar_usuario(username=username, firebase_uid=firebase_uid, email=email, nome=nome)
        if user_data:
            self.usuario_id = user_data["id"]
            self.nome_usuario = user_data["nome"]
            self.is_logged_in = True
            if user_data.get("is_new"):
                self.show_onboarding = True
            return [rx.toast.success(f"Conectado como {self.nome_usuario} 🎉"), rx.redirect("/")]
        return rx.toast.error("Erro ao sincronizar perfil.")

    def set_login_username(self, val: str): self.login_username = val

    async def handle_submit(self):
        if not self.user_input: return
        self.is_processing = True
        txt = self.user_input
        self.user_input = ""
        self.messages.append({"role": "user", "content": txt})
        yield
        self.interaction_count += 1
        is_last_message = (self.interaction_count >= 8)
        res = await ia_manager.analisar_sentimento_e_salvar(txt, self.usuario_id, self.sentiment, is_last_message)
        if "[AVANÇAR_PASSO:" in res:
            try:
                tag_parts = res.split("[AVANÇAR_PASSO:")
                clean_res = tag_parts[0].strip()
                resumo_decisao = tag_parts[1].split("]")[0].strip()
                if self.projeto_id > 0:
                    novo_passo = self.projeto_passo + 1
                    banco_dados.atualizar_passo_projeto(self.projeto_id, novo_passo, resumo_decisao)
                    self.projeto_passo = novo_passo
                    passos = banco_dados.buscar_jornada_passos(self.projeto_id)
                    self.jornada_passos = [{"num": p[0], "resumo": p[1]} for p in passos]
                res = clean_res
            except Exception as e: print(f"⚠️ Erro ao processar avanço de passo: {e}")
        if is_last_message: self.interaction_count = 0
        self.messages.append({"role": "assistant", "content": res})
        self.is_processing = False

    async def finish_session(self):
        yield rx.toast.info("Salvando informações da sessão e encerrando...", position="top-center")
        self.is_sending = True
        yield
        try:
            resumo = await ia_manager.concluir_passo_com_resumo(self.usuario_id)
            self.projeto_passo += 1
            passos = banco_dados.buscar_jornada_passos(self.projeto_id)
            self.jornada_passos = [{"num": p[0], "resumo": p[1]} for p in passos]
            self.messages = []
            self.interaction_count = 0
            yield rx.toast.success("Sessão finalizada com sucesso! Sua jornada avançou.", position="top-center")
        except Exception as e:
            print(f"Erro ao encerrar sessão: {e}")
            yield rx.toast.error("Houve um problema ao salvar a sessão, mas estamos voltando.")
        self.is_sending = False
        yield rx.redirect("/")

    def handle_submit_enter(self, key: str):
        if key == "Enter": return State.handle_submit

def ikigai() -> rx.Component:
    return rx.vstack(
        rx.html("<style>@keyframes pulse-soft {0% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.02); opacity: 1; } 100% { transform: scale(1); opacity: 0.8; }} .ikigai-circle { animation: pulse-soft 4s infinite ease-in-out; cursor: pointer; transition: all 0.3s; } .ikigai-circle:hover { filter: brightness(1.3); }</style>"),
        rx.center(
            rx.match(
                State.tema,
                ("hacker", rx.box(
                    rx.el.svg(
                        rx.el.defs(rx.el.radial_gradient(rx.el.stop(offset="0%", stop_color="rgba(0,255,65,0.1)"), rx.el.stop(offset="70%", stop_color="transparent"), id="glow-hacker")),
                        rx.el.circle(cx="110", cy="110", r="110", fill="url(#glow-hacker)", filter="blur(40px)"),
                        rx.el.circle(cx="110", cy="75", r="55", fill="rgba(0, 255, 65, 0.1)", stroke="#00FF41", stroke_width="1.5", class_name="ikigai-circle", on_click=lambda: State.select_pilar("PAIXÃO")),
                        rx.el.circle(cx="110", cy="145", r="55", fill="rgba(0, 255, 65, 0.05)", stroke="#00FF41", stroke_width="1.5", stroke_dasharray="2 2", class_name="ikigai-circle", on_click=lambda: State.select_pilar("RENDA")),
                        rx.el.circle(cx="75", cy="110", r="55", fill="rgba(0, 255, 65, 0.1)", stroke="#00FF41", stroke_width="1.5", class_name="ikigai-circle", on_click=lambda: State.select_pilar("TALENTO")),
                        rx.el.circle(cx="145", cy="110", r="55", fill="rgba(0, 255, 65, 0.05)", stroke="#00FF41", stroke_width="1.5", stroke_dasharray="2 2", class_name="ikigai-circle", on_click=lambda: State.select_pilar("MISSÃO")),
                        rx.el.circle(cx="110", cy="110", r="26", fill="black", stroke="#00FF41", stroke_width="2"),
                        rx.el.text("VAULT", x="110", y="114", text_anchor="middle", font_size="9", font_weight="800", fill="#00FF41", font_family="monospace"),
                        rx.el.text("PAIXÃO", x="110", y="45", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        rx.el.text("RENDA", x="110", y="178", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        rx.el.text("TALENTO", x="50", y="112", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        rx.el.text("MISSÃO", x="175", y="112", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        width="280", height="280", view_box="0 0 220 220"
                    )
                )),
                ("zen_rose", rx.box(
                    rx.el.svg(
                        rx.el.defs(rx.el.radial_gradient(rx.el.stop(offset="0%", stop_color="rgba(199, 125, 154, 0.2)"), rx.el.stop(offset="100%", stop_color="transparent"), id="glow-rose")),
                        rx.el.circle(cx="110", cy="110", r="100", fill="url(#glow-rose)", filter="blur(30px)"),
                        rx.el.circle(cx="110", cy="75", r="60", fill="rgba(199, 125, 154, 0.15)", stroke="#C77D9A", stroke_width="2", class_name="ikigai-circle", on_click=lambda: State.select_pilar("PAIXÃO")),
                        rx.el.circle(cx="110", cy="145", r="60", fill="rgba(252, 227, 138, 0.15)", stroke="#FCE38A", stroke_width="2", class_name="ikigai-circle", on_click=lambda: State.select_pilar("RENDA")),
                        rx.el.circle(cx="75", cy="110", r="60", fill="rgba(255, 133, 161, 0.15)", stroke="#FF85A1", stroke_width="2", class_name="ikigai-circle", on_click=lambda: State.select_pilar("TALENTO")),
                        rx.el.circle(cx="145", cy="110", r="60", fill="rgba(168, 164, 206, 0.15)", stroke="#A8A4CE", stroke_width="2", class_name="ikigai-circle", on_click=lambda: State.select_pilar("MISSÃO")),
                        rx.el.circle(cx="110", cy="110", r="32", fill="#FFFDF5", stroke="#C77D9A", stroke_width="2"),
                        rx.el.text("IKIGAI", x="110", y="115", text_anchor="middle", font_size="10", font_weight="900", fill="#C77D9A"),
                        width="280", height="280", view_box="0 0 220 220"
                    )
                )),
                rx.box(rx.el.svg(
                    rx.el.circle(cx="110", cy="75", r="58", fill="rgba(63, 81, 181, 0.2)", stroke="#5C6BC0", class_name="ikigai-circle", on_click=lambda: State.select_pilar("PAIXÃO")),
                    rx.el.circle(cx="110", cy="145", r="58", fill="rgba(92, 107, 192, 0.2)", stroke="#5C6BC0", class_name="ikigai-circle", on_click=lambda: State.select_pilar("RENDA")),
                    rx.el.circle(cx="75", cy="110", r="58", fill="rgba(63, 81, 181, 0.2)", stroke="#5C6BC0", class_name="ikigai-circle", on_click=lambda: State.select_pilar("TALENTO")),
                    rx.el.circle(cx="145", cy="110", r="58", fill="rgba(92, 107, 192, 0.2)", stroke="#5C6BC0", class_name="ikigai-circle", on_click=lambda: State.select_pilar("MISSÃO")),
                    rx.el.circle(cx="110", cy="110", r="28", fill="white", stroke="#E2E8F0"),
                    rx.el.text("IKIGAI", x="110", y="114", text_anchor="middle", font_size="10", font_weight="800", fill="#2D3748"),
                    width="280", height="280", view_box="0 0 220 220"
                ))
            )
        )
    )

def navbar() -> rx.Component:
    return rx.hstack(
        rx.image(src="/logo.png", width="150px"), rx.spacer(),
        rx.segmented_control.root(rx.segmented_control.item("Hacker 💻", value="hacker"), rx.segmented_control.item("Low Dark 🌙", value="low_dark"), rx.segmented_control.item("Light ☀️", value="light"), rx.segmented_control.item("Zen Rose 🌸", value="zen_rose"), on_change=State.set_tema, value=State.tema, variant="classic", radius="large"),
        rx.button(rx.icon(tag="log-out", size=18), on_click=State.logout, variant="ghost", color_scheme="ruby", radius="full"),
        width="100%", padding="1.5em", bg=rx.match(State.tema, ("hacker", "black"), ("low_dark", "#1A1A1A"), ("zen_rose", "rgba(255, 253, 245, 0.8)"), "#F7FAFC"), backdrop_filter=rx.cond(State.tema == "zen_rose", "blur(12px)", "none")
    )

def trail_item(title: str, is_active: bool = False, is_locked: bool = True) -> rx.Component:
    return rx.vstack(
        rx.box(rx.center(rx.icon(tag="lock" if is_locked else ("play" if is_active else "check"), size=15), width="100%", height="100%"), width="45px", height="45px", border_radius="full", bg=rx.match(State.tema, ("hacker", rx.cond(is_locked, "#001100", rx.cond(is_active, "#00FF41", "#003B00"))), ("zen_rose", rx.cond(is_locked, "rgba(255,255,255,0.4)", rx.cond(is_active, "#E5989B", "#FFB4A2"))), rx.cond(is_locked, "#EDF2F7", rx.cond(is_active, "#4895EF", "#A0AEC0"))), color=rx.cond(is_active, "white", rx.match(State.tema, ("zen_rose", "#6D597A"), ("hacker", "#003B41"), "#718096")), border=rx.cond(is_active, "2px solid white", "none")),
        rx.text(title, size="1", weight="medium", width="60px", text_align="center", color=rx.match(State.tema, ("zen_rose", "#C77D9A"), ("hacker", "#00FF41"), "#718096")), align_items="center"
    )

def meditation_trail() -> rx.Component:
    return rx.vstack(
        rx.text("Degraus do seu Ikigai", size="4", weight="bold", padding_bottom="1em"),
        rx.cond(State.jornada_passos, rx.hstack(rx.foreach(State.jornada_passos, lambda item: rx.hstack(rx.tooltip(trail_item("Passo Concluído", is_active=False, is_locked=False), content=item["resumo"]), rx.box(width="30px", height="2px", bg="#EDF2F7", margin_top="-20px"))), rx.tooltip(trail_item("Você está aqui", is_active=True, is_locked=False), content="Aguardando a conclusão dos objetivos atuais."), spacing="0", overflow_x="auto", width="100%", padding_x="1em", justify="start"), rx.hstack(trail_item("Passo 1", is_active=True, is_locked=False), rx.text("Iniciando jornada...", size="2", italic=True, opacity=0.7))),
        bg=rx.match(State.tema, ("hacker", "black"), ("low_dark", "#1A1B26"), ("zen_rose", "rgba(255, 255, 255, 0.2)"), "rgba(255,255,255,0.4)"), padding="2em", border_radius="15px", width="100%"
    )

def card_custom(title: str, content: rx.Component, icon: str = "", footer: rx.Component = rx.box()) -> rx.Component:
    return rx.vstack(rx.hstack(rx.icon(tag=icon, size=18) if icon else rx.box(), rx.text(title, size="4", weight="bold"), spacing="2", padding_bottom="0.5em"), content, footer, bg=rx.match(State.tema, ("hacker", "black"), ("low_dark", "#1A1B26"), ("zen_rose", "rgba(255, 255, 255, 0.4)"), "white"), padding="1.5em", border_radius="15px", width="100%", align_items="start")

def onboarding_view() -> rx.Component:
    return rx.center(rx.vstack(rx.heading("Bem-vindo ao Espaço Você", size="8", weight="bold"), rx.text("Vamos iniciar sua jornada para encontrar seu Ikigai.", size="4"), rx.vstack(rx.cond(State.onboarding_step == 1, rx.vstack(rx.input(value=State.onboarding_nome, on_change=State.set_onboarding_nome, placeholder="Seu nome...", width="100%"), rx.button("Próximo", on_click=lambda: State.set_onboarding_step(2), width="100%"), spacing="4", width="100%")), rx.cond(State.onboarding_step == 2, rx.vstack(rx.text("❤️ O que você ama fazer?", weight="bold"), rx.text_area(value=State.onboarding_gosta, on_change=State.set_onboarding_gosta, placeholder="Eu amo...", width="100%"), rx.hstack(rx.button("Voltar", on_click=lambda: State.set_onboarding_step(1)), rx.button("Próximo", on_click=lambda: State.set_onboarding_step(3), flex="1"), width="100%"), spacing="4", width="100%")), rx.cond(State.onboarding_step == 3, rx.vstack(rx.text("💪 No que você é bom?", weight="bold"), rx.text_area(value=State.onboarding_bom, on_change=State.set_onboarding_bom, placeholder="Eu sou bom em...", width="100%"), rx.hstack(rx.button("Voltar", on_click=lambda: State.set_onboarding_step(2)), rx.button("Próximo", on_click=lambda: State.set_onboarding_step(4), flex="1"), width="100%"), spacing="4", width="100%")), rx.cond(State.onboarding_step == 4, rx.vstack(rx.text("🌍 O que o mundo precisa?", weight="bold"), rx.text_area(value=State.onboarding_precisa, on_change=State.set_onboarding_precisa, placeholder="O mundo precisa de...", width="100%"), rx.hstack(rx.button("Voltar", on_click=lambda: State.set_onboarding_step(3)), rx.button("Próximo", on_click=lambda: State.set_onboarding_step(5), flex="1"), width="100%"), spacing="4", width="100%")), rx.cond(State.onboarding_step == 5, rx.vstack(rx.text("💰 Pelo que você pode ser pago?", weight="bold"), rx.text_area(value=State.onboarding_pago, on_change=State.set_onboarding_pago, placeholder="Eu posso ser pago por...", width="100%"), rx.hstack(rx.button("Voltar", on_click=lambda: State.set_onboarding_step(4)), rx.button("Finalizar", on_click=State.finish_onboarding, flex="1"), width="100%"), spacing="4", width="100%")), width="100%"), bg="white", padding="3em", border_radius="3xl", background="black"), width="100%", height="100vh", background="black")

def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.image(src="/logo.png", width="250px"),
            rx.heading("Desperte seu Ikigai", size="8", weight="bold", color="white"),
            rx.text("Conecte-se com sua conta Google.", color="white", opacity=0.8),
            rx.button(
                rx.hstack(rx.icon(tag="chrome"), rx.text("Entrar com Google"), spacing="2"),
                on_click=rx.call_script("loginWithGoogle()", callback=State.handle_google_login),
                width="100%", size="4", bg="white", color="black", radius="full"
            ),
            spacing="4", padding="4em", bg="rgba(255, 255, 255, 0.05)", backdrop_filter="blur(20px)", border_radius="3xl", align_items="center"
        ),
        firebase_init(),
        auth_bridge(),
        width="100%", height="100vh", background="radial-gradient(circle at 50% 50%, #1E88E5 0%, #0F172A 100%)"
    )

def index() -> rx.Component:
    return rx.box(
        rx.cond(
            State.is_logged_in,
            rx.cond(
                State.show_onboarding,
                onboarding_view(),
                rx.box(
                    rx.box(position="fixed", top="0", left="0", width="100%", height="100%", background=rx.match(State.tema, ("hacker", "radial-gradient(circle at 80% 10%, rgba(0,255,65,0.05), transparent 50%), #000"), ("low_dark", "radial-gradient(circle at 20% 20%, rgba(92,107,192,0.1), transparent 50%), #0F172A"), ("zen_rose", "#9B5DE5"), "#1E88E5"), z_index="-1"),
                    navbar(),
                    rx.container(
                        rx.vstack(
                            rx.vstack(rx.heading(f"Olá de novo, {State.nome_usuario}!", size="9", weight="bold", color="white"), rx.text("O que vamos fazer aqui no seu espaço hoje?", size="4", color="white", opacity=0.9), align_items="center", padding_top="2em"),
                            ikigai(),
                            rx.flex(
                                rx.box(card_custom("Sua Jornada até aqui", meditation_trail(), icon="map"), width=["100%", "100%", "58%"]),
                                rx.vstack(
                                    card_custom("Diário de Insights", rx.vstack(rx.text_area(value=State.insight_input, on_change=State.set_insight_input, placeholder="O que você descobriu hoje?", width="100%", height="120px"), rx.button("Salvar Reflexão", on_click=State.save_insight, color_scheme="grass", width="100%"), spacing="3", width="100%"), icon="notebook-pen", footer=rx.text(f"Último Insight: {State.last_insight}", size="1", italic=True)),
                                    card_custom("Status do Projeto", rx.vstack(rx.heading(State.projeto_nome, size="4"), rx.text(State.projeto_frase, weight="bold", color="grass"), rx.text(f"Objetivo: {State.projeto_objetivo}", size="1"), rx.badge(f"PASSO {State.projeto_passo}", color_scheme="grass"), spacing="2"), icon="rocket"),
                                    card_custom("Propósito Sugerido", rx.text(State.proposito_sugerido, italic=True), icon="sparkles"),
                                    spacing="4", width=["100%", "100%", "38%"]
                                ),
                                width="100%", spacing="4", flex_wrap="wrap", justify="center"
                            ),
                            rx.vstack(rx.button("Conversar com Mentor", size="4", radius="full", on_click=lambda: rx.redirect("/chat")), rx.text("Inicie sua conversa diária", size="2", color="#718096", opacity=0.6), padding_y="3em", align_items="center"),
                            spacing="6", width="100%", max_width="750px", margin_x="auto"
                        )
                    )
                )
            ),
            login_page()
        ),
        firebase_init(),
        auth_bridge(),
        on_mount=State.on_load,
    )

def chat_page() -> rx.Component:
    return rx.box(
        rx.box(background=rx.match(State.tema, ("hacker", "black"), ("low_dark", "#0F172A"), ("zen_rose", "#9B5DE5"), "#1E88E5"), z_index="-1"),
        rx.container(
            rx.vstack(
                rx.hstack(rx.button(rx.icon(tag="arrow-left"), on_click=lambda: rx.redirect("/"), variant="ghost"), rx.image(src="/logo.png", width="150px"), justify="start", width="100%", padding_y="1em"),
                rx.vstack(
                    rx.foreach(State.messages, lambda m: rx.box(rx.flex(rx.box(rx.markdown(m["content"]), bg=rx.match(State.tema, ("hacker", rx.cond(m["role"]=="user", "#003B00", "#001100")), ("zen_rose", rx.cond(m["role"]=="user", "#C77D9A", "rgba(255, 253, 245, 0.6)")), rx.cond(m["role"]=="user", "#E2E8F0", "white")), padding="1.2em", border_radius="15px", max_width="90%"), justify=rx.cond(m["role"]=="user", "end", "start"), width="100%"), width="100%")),
                    width="100%", spacing="4"
                ),
                rx.box(height="120px")
            )
        ),
        rx.box(rx.container(rx.hstack(rx.input(placeholder="Como você se sente hoje?", value=State.user_input, on_change=State.set_user_input, width="100%", radius="full", on_key_down=State.handle_submit_enter), rx.button(rx.cond(State.is_processing, rx.spinner(size="2"), rx.icon(tag="send")), on_click=State.handle_submit, radius="full"), rx.button(rx.icon(tag="check-check"), on_click=State.finish_session, radius="full", variant="soft", color_scheme="ruby"), width="100%", spacing="3"), max_width="700px"), backdrop_filter="blur(12px)"),
        firebase_init(),
        auth_bridge(),
    )

app = rx.App(theme=rx.theme(accent_color="grass", radius="full", appearance="light"))
app.add_page(index, route="/")
app.add_page(chat_page, route="/chat")
app.add_page(login_page, route="/login")
