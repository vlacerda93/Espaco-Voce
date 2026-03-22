import reflex as rx
import sys
import os

# --- SETUP DE CAMINHO ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path: sys.path.insert(0, root_dir)

import Backend.banco_dados as banco_dados
import Backend.LLM.ia_manager as ia_manager

class State(rx.State):
    usuario_id: int = 1
    nome_usuario: str = "Vinícius"
    user_input: str = ""
    messages: list[dict] = []
    is_processing: bool = False
    sentiment: str = "Neutro"
    
    # --- ONBOARDING STATE ---
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

    def set_user_input(self, val: str): self.user_input = val
    def set_sentiment(self, val: str): self.sentiment = val
    def set_onboarding_nome(self, val: str): self.onboarding_nome = val
    def set_onboarding_gosta(self, val: str): self.onboarding_gosta = val
    def set_onboarding_bom(self, val: str): self.onboarding_bom = val
    def set_onboarding_precisa(self, val: str): self.onboarding_precisa = val
    def set_onboarding_pago(self, val: str): self.onboarding_pago = val
    
    def set_onboarding_step(self, step: int): self.onboarding_step = step

    def on_load(self):
        perfil = banco_dados.buscar_dados_usuario(self.usuario_id)
        if perfil:
            self.nome_usuario = perfil['nome']
            self.onboarding_nome = perfil['nome']
            # Se não tiver preenchido o Ikigai, mostra onboarding
            if not perfil['gosta_fazer']:
                self.show_onboarding = True
            else:
                self.show_onboarding = False
        
        hist = banco_dados.visualizar_reflexoes_usuario(self.usuario_id, limite=10)
        self.messages = [{"role": "user" if i%2==0 else "assistant", "content": h[2] if i%2==0 else h[3]} 
                         for i, h in enumerate(reversed(hist or []))]

    def finish_onboarding(self):
        success = banco_dados.atualizar_perfil_ikigai(
            self.usuario_id, self.onboarding_nome, self.onboarding_gosta,
            self.onboarding_bom, self.onboarding_precisa, self.onboarding_pago
        )
        if success:
            self.nome_usuario = self.onboarding_nome
            self.show_onboarding = False
            return rx.toast.info("Perfil Ikigai atualizado! Bem-vindo.", position="top-center")

    async def handle_submit(self):
        if not self.user_input: return
        self.is_processing = True
        txt = self.user_input
        self.user_input = ""
        self.messages.append({"role": "user", "content": txt})
        yield
        res = await ia_manager.analisar_sentimento_e_salvar(txt, self.usuario_id, self.sentiment)
        self.messages.append({"role": "assistant", "content": res})
        self.is_processing = False

    def handle_submit_enter(self, key: str):
        if key == "Enter":
            return State.handle_submit

def ikigai() -> rx.Component:
    return rx.center(
        rx.html("""
        <div style="position: relative; width: 280px; height: 280px; display: flex; align-items: center; justify-content: center;">
            <!-- Glow background -->
            <div style="position: absolute; width: 200px; height: 200px; background: radial-gradient(circle, rgba(112,191,182,0.2) 0%, rgba(238,195,115,0.1) 100%); filter: blur(35px); border-radius: 50%;"></div>
            
            <svg width="250" height="250" viewBox="0 0 220 220" style="z-index: 1;">
                <!-- Círculos com cores suaves e bordas finas -->
                <circle cx="110" cy="75" r="55" fill="rgba(112, 191, 182, 0.35)" stroke="#70BFB6" stroke-width="1"/>
                <circle cx="110" cy="145" r="55" fill="rgba(151, 140, 185, 0.35)" stroke="#978CB9" stroke-width="1"/>
                <circle cx="75" cy="110" r="55" fill="rgba(102, 182, 206, 0.35)" stroke="#66B6CE" stroke-width="1"/>
                <circle cx="145" cy="110" r="55" fill="rgba(238, 195, 115, 0.35)" stroke="#EEC373" stroke-width="1"/>
                
                <!-- Textos por Quadrante com tspan para multi-linha -->
                <!-- Topo: O que você ama -->
                <text x="110" y="45" text-anchor="middle" font-size="7" font-weight="700" fill="#2D3748" font-family="sans-serif">
                    <tspan x="110" dy="0">O QUE</tspan>
                    <tspan x="110" dy="9">VOCÊ AMA</tspan>
                </text>
                
                <!-- Baixo: Pelo que pode ser pago -->
                <text x="110" y="178" text-anchor="middle" font-size="7" font-weight="700" fill="#2D3748" font-family="sans-serif">
                    <tspan x="110" dy="0">SER PAGO</tspan>
                    <tspan x="110" dy="9">POR ISSO</tspan>
                </text>
                
                <!-- Esquerda: No que é bom -->
                <text x="50" y="112" text-anchor="middle" font-size="7" font-weight="700" fill="#2D3748" font-family="sans-serif">
                    <tspan x="50" dy="0">NO QUE</tspan>
                    <tspan x="50" dy="9">É BOM</tspan>
                </text>
                
                <!-- Direita: O que o mundo precisa -->
                <text x="175" y="112" text-anchor="middle" font-size="7" font-weight="700" fill="#2D3748" font-family="sans-serif">
                    <tspan x="175" dy="0">O MUNDO</tspan>
                    <tspan x="175" dy="9">PRECISA</tspan>
                </text>
                
                <!-- Bolha Central "Ikigai" -->
                <circle cx="110" cy="110" r="24" fill="white" filter="drop-shadow(0 4px 6px rgba(0,0,0,0.1))"/>
                <text x="110" y="113" text-anchor="middle" font-size="10" font-weight="800" fill="#1A202C" font-family="sans-serif">Ikigai</text>
            </svg>
        </div>
        """),
        padding_y="1em"
    )

def card_custom(title: str, content: rx.Component, icon: str = "") -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(tag=icon, size=18) if icon else rx.box(),
            rx.text(title, size="4", weight="bold", color="#1A202C"),
            spacing="2",
            padding_bottom="0.5em",
        ),
        content,
        bg="rgba(249, 249, 244, 0.8)",
        backdrop_filter="blur(10px)",
        padding="1.5em",
        border_radius="25px",
        box_shadow="0 4px 20px rgba(0,0,0,0.03)",
        border="1px solid rgba(255,255,255,0.6)",
        width="100%",
        align_items="start",
    )

def onboarding_view() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Bem-vindo ao Espaço Você", size="8", weight="bold", color="#1A202C", text_align="center"),
            rx.text("Vamos iniciar sua jornada para encontrar seu Ikigai.", size="4", color="#4A5568", text_align="center"),
            
            # --- STEP 1: NOME ---
            rx.cond(
                State.onboarding_step == 1,
                rx.vstack(
                    rx.input(value=State.onboarding_nome, on_change=State.set_onboarding_nome, placeholder="Seu nome...", size="3", width="100%", radius="large"),
                    rx.button("Próximo", on_click=State.set_onboarding_step(2), width="100%", color_scheme="grass", size="3"),
                    spacing="4", width="100%"
                )
            ),
            
            # --- STEP 2: O QUE AMA ---
            rx.cond(
                State.onboarding_step == 2,
                rx.vstack(
                    rx.text("❤️ O que você ama fazer?", weight="bold", size="5"),
                    rx.text("Suas paixões, hobbies e interesses.", size="2", opacity=0.8),
                    rx.text_area(value=State.onboarding_gosta, on_change=State.set_onboarding_gosta, placeholder="Eu amo...", size="3", width="100%", height="120px"),
                    rx.hstack(
                        rx.button("Voltar", on_click=State.set_onboarding_step(1), variant="soft"),
                        rx.button("Próximo", on_click=State.set_onboarding_step(3), color_scheme="grass", flex="1"),
                        width="100%"
                    ),
                    spacing="4", width="100%"
                )
            ),
            
            # --- STEP 3: BOM EM ---
            rx.cond(
                State.onboarding_step == 3,
                rx.vstack(
                    rx.text("💪 No que você é bom?", weight="bold", size="5"),
                    rx.text("Suas habilidades, talentos e competências.", size="2", opacity=0.8),
                    rx.text_area(value=State.onboarding_bom, on_change=State.set_onboarding_bom, placeholder="Eu sou bom em...", size="3", width="100%", height="120px"),
                    rx.hstack(
                        rx.button("Voltar", on_click=State.set_onboarding_step(2), variant="soft"),
                        rx.button("Próximo", on_click=State.set_onboarding_step(4), color_scheme="grass", flex="1"),
                        width="100%"
                    ),
                    spacing="4", width="100%"
                )
            ),
            
            # --- STEP 4: MUNDO PRECISA ---
            rx.cond(
                State.onboarding_step == 4,
                rx.vstack(
                    rx.text("🌍 O que o mundo precisa?", weight="bold", size="5"),
                    rx.text("Sua contribuição para o bem-estar da sociedade.", size="2", opacity=0.8),
                    rx.text_area(value=State.onboarding_precisa, on_change=State.set_onboarding_precisa, placeholder="O mundo precisa de...", size="3", width="100%", height="120px"),
                    rx.hstack(
                        rx.button("Voltar", on_click=State.set_onboarding_step(3), variant="soft"),
                        rx.button("Próximo", on_click=State.set_onboarding_step(5), color_scheme="grass", flex="1"),
                        width="100%"
                    ),
                    spacing="4", width="100%"
                )
            ),
            
            # --- STEP 5: PAGO PARA ---
            rx.cond(
                State.onboarding_step == 5,
                rx.vstack(
                    rx.text("💰 Pelo que você pode ser pago?", weight="bold", size="5"),
                    rx.text("Sua profissão, trabalho ou fontes de renda estimadas.", size="2", opacity=0.8),
                    rx.text_area(value=State.onboarding_pago, on_change=State.set_onboarding_pago, placeholder="Eu posso ser pago por...", size="3", width="100%", height="120px"),
                    rx.hstack(
                        rx.button("Voltar", on_click=State.set_onboarding_step(4), variant="soft"),
                        rx.button("Finalizar", on_click=State.finish_onboarding, color_scheme="grass", flex="1"),
                        width="100%"
                    ),
                    spacing="4", width="100%"
                )
            ),
            
            bg="white",
            padding="3em",
            border_radius="3xl",
            box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            width="100%",
            max_width="450px",
            spacing="6",
        ),
        width="100%",
        height="100vh",
        background="linear-gradient(160deg, #D8E5D8 0%, #FDFCFB 100%)",
    )

def index() -> rx.Component:
    return rx.box(
        rx.cond(
            State.show_onboarding,
            onboarding_view(),
            rx.box(
                # --- BACKGROUND GRADIENT (Refined Glow) ---
                rx.box(
                    position="fixed",
                    top="0",
                    left="0",
                    width="100%",
                    height="100%",
                    background="radial-gradient(circle at 80% 10%, rgba(238,195,115,0.1) 0%, transparent 40%), radial-gradient(circle at 10% 80%, rgba(112,191,182,0.1) 0%, transparent 40%), #FFFFFF",
                    z_index="-1",
                ),
                rx.container(
                    rx.vstack(
                        # --- HEADER (Reference Match) ---
                        rx.vstack(
                            rx.text("Bem-vindo ao Ikigai", size="2", weight="medium", color="#718096", opacity=0.8),
                            rx.heading("Sua Jornada para o Ikigai", size="8", weight="bold", color="#1A202C"),
                            align_items="center",
                            padding_top="2em",
                        ),
                        
                        # --- IKIGAI DIAGRAM ---
                        ikigai(),
                        
                        # --- DASHBOARD GRID ---
                        rx.flex(
                            # Lado Esquerdo: Biblioteca
                            rx.box(
                                card_custom(
                                    "Biblioteca de Sessões",
                                    rx.vstack(
                                        rx.text("Caminhos para o Equilíbrio", size="3", color="#4A5568", weight="medium"),
                                        rx.box(
                                            rx.hstack(rx.icon(tag="users", size=14), rx.text("Exploração do 'O que você ama'", size="2"), spacing="2"),
                                            rx.hstack(rx.icon(tag="trophy", size=14), rx.text("Desenvolvimento de Talentos", size="2"), spacing="2"),
                                            rx.hstack(rx.icon(tag="globe", size=14), rx.text("Ação no Mundo", size="2"), spacing="2"),
                                            rx.hstack(rx.icon(tag="banknote", size=14), rx.text("Pelo que você pode ser pago", size="2"), spacing="2"),
                                            spacing="2",
                                            padding_top="0.5em",
                                            color="#718096"
                                        ),
                                        spacing="3",
                                        align_items="start",
                                    ),
                                    icon="users"
                                ),
                                width=["100%", "100%", "58%"],
                            ),
                            # Lado Direito: Insights e Toggle
                            rx.vstack(
                                card_custom(
                                    "Diário de Insights",
                                    rx.text("Suas últimas reflexões estão guardadas aqui.", size="2", color="#718096"),
                                    icon="notebook-pen"
                                ),
                                rx.box(
                                    rx.hstack(
                                        rx.icon(tag="sun", size=16),
                                        rx.hstack(
                                            rx.text("MODO: CLARO | ESCURO", size="1", weight="bold", color="#718096"),
                                            rx.switch(color_scheme="gray", size="1"),
                                            spacing="2",
                                        ),
                                        rx.icon(tag="moon", size=16),
                                        justify="between",
                                        width="100%",
                                    ),
                                    padding="1em",
                                    bg="rgba(249, 249, 244, 0.8)",
                                    border_radius="xl",
                                    width="100%",
                                ),
                                card_custom(
                                    "",
                                    rx.text("Registro de Descobertas de Hoje", size="3", color="#718096", italic=True),
                                ),
                                spacing="4",
                                width=["100%", "100%", "38%"],
                            ),
                            width="100%",
                            spacing="4",
                            flex_wrap="wrap",
                            justify="center",
                        ),
                        
                        # --- FOOTER BUTTON ---
                        rx.vstack(
                            rx.button(
                                "Start Journey",
                                size="4",
                                radius="full",
                                background="linear-gradient(90deg, #70BFB6 0%, #66B6CE 100%)",
                                color="white",
                                padding_x="3em",
                                padding_y="1.5em",
                                box_shadow="0 10px 30px rgba(112, 191, 182, 0.4)",
                                _hover={"transform": "scale(1.05)", "box_shadow": "0 15px 40px rgba(112, 191, 182, 0.5)"},
                                # Ao clicar, abre o chat
                                on_click=lambda: rx.redirect("/chat"), 
                            ),
                            rx.text("Começar Minha Descoberta", size="2", color="#718096", opacity=0.6),
                            padding_y="3em",
                            align_items="center",
                        ),
                        
                        spacing="6",
                        width="100%",
                        max_width="650px", 
                        margin_x="auto",
                    )
                ),
            )
        ),
        min_height="100vh",
        on_mount=State.on_load
    )

# --- CHAT PAGE ---
def chat_page() -> rx.Component:
    return rx.box(
        rx.box(
            position="fixed",
            top="0",
            left="0",
            width="100%",
            height="100%",
            background="linear-gradient(160deg, #FDFCFB 0%, #D8E5D8 100%)",
            z_index="-1",
        ),
        rx.container(
            rx.vstack(
                rx.hstack(
                    rx.button(rx.icon(tag="arrow-left"), on_click=lambda: rx.redirect("/"), variant="ghost"),
                    rx.heading("Mentor IA", size="6", weight="bold"),
                    justify="start",
                    width="100%",
                    padding_y="1em",
                ),
                rx.vstack(
                    rx.foreach(State.messages, lambda m: rx.box(
                        rx.flex(
                            rx.box(
                                rx.markdown(m["content"]),
                                bg=rx.cond(m["role"]=="user", "#E2E8F0", "white"),
                                color="#1A202C",
                                padding="1.2em",
                                border_radius="2xl",
                                max_width="90%",
                                box_shadow="sm",
                            ),
                            justify=rx.cond(m["role"]=="user", "end", "start"),
                            width="100%",
                        ),
                        width="100%",
                    )),
                    width="100%",
                    spacing="4",
                ),
                rx.box(height="120px"),
            )
        ),
        rx.box(
            rx.container(
                rx.hstack(
                    rx.input(
                        placeholder="Como você se sente hoje?",
                        value=State.user_input,
                        on_change=State.set_user_input,
                        width="100%",
                        radius="full",
                        bg="white",
                        on_key_down=State.handle_submit_enter,
                    ),
                    rx.button(
                        rx.cond(State.is_processing, rx.spinner(size="2"), rx.icon(tag="send")),
                        on_click=State.handle_submit,
                        radius="full",
                        color_scheme="grass",
                    ),
                    width="100%",
                    spacing="3",
                ),
                max_width="600px",
            ),
            position="fixed",
            bottom="0",
            width="100%",
            padding="2em",
            bg="rgba(255,255,255,0.8)",
            backdrop_filter="blur(10px)",
        )
    )

app = rx.App(
    theme=rx.theme(
        accent_color="grass",
        radius="full",
        appearance="light",
    )
)
app.add_page(index, route="/")
app.add_page(chat_page, route="/chat")

