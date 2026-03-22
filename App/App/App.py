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
    
    # --- DYNAMIC THEMES ---
    # Opções: "light", "low_dark", "hacker"
    tema: str = "hacker" 

    def set_tema(self, val): self.tema = val

    
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
    
    # --- INSIGHTS STATE ---
    insight_input: str = ""
    last_insight: str = "Tudo começa com um pequeno passo..."
    
    # --- CIRCLE INTERACTION ---
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
        # Para o MVP, assumimos user_id = 1
        self.show_onboarding = False 
        
        # Carrega perfil do SQLite
        perfil = banco_dados.buscar_dados_usuario(self.usuario_id)
        if perfil:
            self.nome_usuario = perfil["nome"]
            self.onboarding_nome = perfil["nome"]
            self.onboarding_gosta = perfil["gosta_fazer"]
            self.onboarding_bom = perfil["bom_em"]
            self.onboarding_precisa = perfil["mundo_precisa"]
            self.onboarding_pago = perfil["pago_para"]

        # Carrega último insight do SQLite
        entries = banco_dados.buscar_insights_usuario(self.usuario_id, limite=1)
        if entries:
            self.last_insight = entries[0][1]


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
    return rx.vstack(
        rx.html("""
        <style>
            @keyframes pulse-soft {
                0% { transform: scale(1); opacity: 0.8; }
                50% { transform: scale(1.02); opacity: 1; }
                100% { transform: scale(1); opacity: 0.8; }
            }
            .ikigai-circle { animation: pulse-soft 4s infinite ease-in-out; cursor: pointer; transition: all 0.3s; }
            .ikigai-circle:hover { filter: brightness(1.3); }
        </style>
        """),
        rx.center(
            rx.cond(
                State.tema == "hacker",
                rx.box(
                    rx.el.svg(
                        rx.el.defs(
                            rx.el.radial_gradient(
                                rx.el.stop(offset="0%", stop_color="rgba(0,255,65,0.1)"),
                                rx.el.stop(offset="70%", stop_color="transparent"),
                                id="glow-hacker"
                            )
                        ),
                        rx.el.circle(cx="110", cy="110", r="110", fill="url(#glow-hacker)", filter="blur(40px)"),
                        # PAIXÃO
                        rx.el.circle(
                            cx="110", cy="75", r="55", fill="rgba(0, 255, 65, 0.1)", stroke="#00FF41", stroke_width="1.5",
                            class_name="ikigai-circle circle-1", on_click=State.select_pilar("PAIXÃO")
                        ),
                        # RENDA
                        rx.el.circle(
                            cx="110", cy="145", r="55", fill="rgba(0, 255, 65, 0.05)", stroke="#00FF41", stroke_width="1.5", stroke_dasharray="2 2",
                            class_name="ikigai-circle circle-2", on_click=State.select_pilar("RENDA")
                        ),
                        # TALENTO
                        rx.el.circle(
                            cx="75", cy="110", r="55", fill="rgba(0, 255, 65, 0.1)", stroke="#00FF41", stroke_width="1.5",
                            class_name="ikigai-circle circle-3", on_click=State.select_pilar("TALENTO")
                        ),
                        # MISSÃO
                        rx.el.circle(
                            cx="145", cy="110", r="55", fill="rgba(0, 255, 65, 0.05)", stroke="#00FF41", stroke_width="1.5", stroke_dasharray="2 2",
                            class_name="ikigai-circle circle-4", on_click=State.select_pilar("MISSÃO")
                        ),
                        rx.el.circle(cx="110", cy="110", r="26", fill="black", stroke="#00FF41", stroke_width="2"),
                        rx.el.text("VAULT", x="110", y="114", text_anchor="middle", font_size="9", font_weight="800", fill="#00FF41", font_family="monospace"),
                        rx.el.text("PAIXÃO", x="110", y="45", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        rx.el.text("RENDA", x="110", y="178", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        rx.el.text("TALENTO", x="50", y="112", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        rx.el.text("MISSÃO", x="175", y="112", text_anchor="middle", font_size="7", fill="#00FF41", font_family="monospace"),
                        width="280", height="280", view_box="0 0 220 220"
                    ),
                    position="relative", width="300px", height="300px", display="flex", align_items="center", justify_content="center"
                ),
                rx.cond(
                    State.tema == "low_dark",
                    rx.box(
                        rx.el.svg(
                            rx.el.circle(
                                cx="110", cy="75", r="58", fill="rgba(63, 81, 181, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                                class_name="ikigai-circle circle-1", on_click=State.select_pilar("PAIXÃO")
                            ),
                            rx.el.circle(
                                cx="110", cy="145", r="58", fill="rgba(92, 107, 192, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                                class_name="ikigai-circle circle-2", on_click=State.select_pilar("RENDA")
                            ),
                            rx.el.circle(
                                cx="75", cy="110", r="58", fill="rgba(63, 81, 181, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                                class_name="ikigai-circle circle-3", on_click=State.select_pilar("TALENTO")
                            ),
                            rx.el.circle(
                                cx="145", cy="110", r="58", fill="rgba(92, 107, 192, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                                class_name="ikigai-circle circle-4", on_click=State.select_pilar("MISSÃO")
                            ),
                            rx.el.circle(cx="110", cy="110", r="30", fill="#1A1B26", stroke="#5C6BC0", stroke_width="2"),
                            rx.el.text("IKIGAI", x="110", y="114", text_anchor="middle", font_size="10", font_weight="800", fill="#A9B1D6"),
                            rx.el.text("PAIXÃO", x="110", y="45", text_anchor="middle", font_size="8", font_weight="700", fill="#E0E0E0"),
                            rx.el.text("RENDA", x="110", y="178", text_anchor="middle", font_size="8", font_weight="700", fill="#E0E0E0"),
                            rx.el.text("TALENTO", x="50", y="112", text_anchor="middle", font_size="8", font_weight="700", fill="#E0E0E0"),
                            rx.el.text("MISSÃO", x="175", y="112", text_anchor="middle", font_size="8", font_weight="700", fill="#E0E0E0"),
                            width="280", height="280", view_box="0 0 220 220"
                        ),
                        position="relative", width="300px", height="300px", display="flex", align_items="center", justify_content="center"
                    ),
                    # Light Mode
                    rx.box(
                        rx.el.svg(
                            rx.el.circle(
                                cx="110", cy="75", r="58", fill="rgba(112, 191, 182, 0.2)", stroke="#70BFB6",
                                class_name="ikigai-circle circle-1", on_click=State.select_pilar("PAIXÃO")
                            ),
                            rx.el.circle(
                                cx="110", cy="145", r="58", fill="rgba(151, 140, 185, 0.2)", stroke="#978CB9",
                                class_name="ikigai-circle circle-2", on_click=State.select_pilar("RENDA")
                            ),
                            rx.el.circle(
                                cx="75", cy="110", r="58", fill="rgba(102, 182, 206, 0.2)", stroke="#66B6CE",
                                class_name="ikigai-circle circle-3", on_click=State.select_pilar("TALENTO")
                            ),
                            rx.el.circle(
                                cx="145", cy="110", r="58", fill="rgba(238, 195, 115, 0.2)", stroke="#EEC373",
                                class_name="ikigai-circle circle-4", on_click=State.select_pilar("MISSÃO")
                            ),
                            rx.el.circle(cx="110", cy="110", r="28", fill="white", stroke="#E2E8F0"),
                            rx.el.text("IKIGAI", x="110", y="114", text_anchor="middle", font_size="10", font_weight="800", fill="#2D3748"),
                            rx.el.text("PAIXÃO", x="110", y="42", text_anchor="middle", font_size="8", font_weight="700", fill="#2D3748"),
                            rx.el.text("RENDA", x="110", y="181", text_anchor="middle", font_size="8", font_weight="700", fill="#2D3748"),
                            rx.el.text("TALENTO", x="50", y="112", text_anchor="middle", font_size="8", font_weight="700", fill="#2D3748"),
                            rx.el.text("MISSÃO", x="175", y="112", text_anchor="middle", font_size="8", font_weight="700", fill="#2D3748"),
                            width="280", height="280", view_box="0 0 220 220"
                        ),
                        position="relative", width="300px", height="300px", display="flex", align_items="center", justify_content="center"
                    )
                )
            ),
            padding_y="1.5em"
        ),
        # Display Area para o Pilar Selecionado
        rx.cond(
            State.selected_pilar != "",
            rx.vstack(
                rx.heading(f"Pilar: {State.selected_pilar}", size="4", color=rx.cond(State.tema=="hacker", "#00FF41", "inherit")),
                rx.text(State.pilar_content, size="2", italic=True, text_align="center"),
                rx.button("Fechar", on_click=State.select_pilar(""), variant="soft", size="1"),
                padding="1.5em",
                bg=rx.cond(State.tema=="hacker", "rgba(0,255,65,0.05)", "rgba(0,0,0,0.03)"),
                border_radius="xl",
                border=rx.cond(State.tema=="hacker", "1px solid #00FF41", "1px solid rgba(0,0,0,0.1)"),
                width="100%",
                max_width="400px",
                margin_x="auto",
                align_items="center",
                margin_top="-2em",
                margin_bottom="1.5em",
            )
        )
    )

def navbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon(tag="shield-check", color=rx.cond(State.tema=="hacker", "#00FF41", "#5C6BC0"), size=24),
            rx.heading("ANTIGRAVITY", size="5", weight="bold", color=rx.cond(State.tema=="hacker", "#00FF41", "#5C6BC0"), font_family="monospace"),
            spacing="3",
        ),
        rx.spacer(),
        rx.segmented_control.root(
            rx.segmented_control.item("Hacker", value="hacker"),
            rx.segmented_control.item("Low Dark", value="low_dark"),
            rx.segmented_control.item("Light", value="light"),
            on_change=State.set_tema,
            value=State.tema,
            variant="classic",
            radius="large",
        ),
        width="100%",
        padding="1.5em",
        bg=rx.cond(State.tema=="hacker", "black", rx.cond(State.tema=="low_dark", "#1A1A1A", "#F7FAFC")),
        border_bottom=rx.cond(State.tema=="hacker", "1px solid #00FF41", "none"),
    )



def trail_item(title: str, is_active: bool = False, is_locked: bool = True) -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.center(
                rx.icon(tag="lock" if is_locked else ("play" if is_active else "check"), size=15),
                width="100%", height="100%"
            ),
            width="45px",
            height="45px",
            border_radius="full",
            bg=rx.cond(is_locked, "#EDF2F7", rx.cond(is_active, "#70BFB6", "#A0AEC0")),
            color="white",
            box_shadow="lg" if is_active else "none",
            border=rx.cond(is_active, "2px solid white", "none"),
        ),
        rx.text(title, size="1", weight="medium", width="60px", text_align="center", color="#718096"),
        spacing="2",
        align_items="center",
    )

def meditation_trail() -> rx.Component:
    return rx.vstack(
        rx.text("Sua Jornada Espaço Você", size="4", weight="bold", padding_bottom="1em"),
        rx.hstack(
            trail_item("Calma Matinal", is_active=True, is_locked=False),
            rx.box(width="30px", height="2px", bg="#E2E8F0", margin_top="-20px"),
            trail_item("Foco Profundo"),
            rx.box(width="30px", height="2px", bg="#EDF2F7", margin_top="-20px"),
            trail_item("Sono Zen"),
            rx.box(width="30px", height="2px", bg="#EDF2F7", margin_top="-20px"),
            trail_item("Ikigai Pleno"),
            spacing="0",
            overflow_x="auto",
            width="100%",
            padding_x="1em",
            justify="center",
        ),
        bg=rx.cond(State.tema=="hacker", "black", rx.cond(State.tema=="low_dark", "#1A1B26", "rgba(255,255,255,0.4)")),
        padding="2em",
        border_radius="15px",
        width="100%",
        border=rx.cond(State.tema=="hacker", "1px solid #00FF41", "1px solid rgba(0,0,0,0.1)"),
    )


def card_custom(title: str, content: rx.Component, icon: str = "", footer: rx.Component = rx.box()) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(tag=icon, size=18) if icon else rx.box(),
            rx.text(title, size="4", weight="bold"),
            spacing="2",
            padding_bottom="0.5em",
        ),
        content,
        footer,
        bg=rx.cond(State.tema=="hacker", "black", rx.cond(State.tema=="low_dark", "#1A1B26", "white")),
        padding="1.5em",
        border_radius="15px",
        box_shadow=rx.cond(State.tema=="hacker", "0 0 20px rgba(0,255,65,0.1)", "0 8px 32px rgba(0,0,0,0.05)"),
        border=rx.cond(State.tema=="hacker", "1px solid #00FF41", "1px solid rgba(0,0,0,0.1)"),
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
                    rx.button("Próximo", on_click=lambda: State.set_onboarding_step(2), width="100%", color_scheme="grass", size="3"),
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
                        rx.button("Voltar", on_click=lambda: State.set_onboarding_step(1), variant="soft"),
                        rx.button("Próximo", on_click=lambda: State.set_onboarding_step(3), color_scheme="grass", flex="1"),
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
                        rx.button("Voltar", on_click=lambda: State.set_onboarding_step(2), variant="soft"),
                        rx.button("Próximo", on_click=lambda: State.set_onboarding_step(4), color_scheme="grass", flex="1"),
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
                        rx.button("Voltar", on_click=lambda: State.set_onboarding_step(3), variant="soft"),
                        rx.button("Próximo", on_click=lambda: State.set_onboarding_step(5), color_scheme="grass", flex="1"),
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
                        rx.button("Voltar", on_click=lambda: State.set_onboarding_step(4), variant="soft"),
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
            background="black",
        ),
        width="100%",
        height="100vh",
        background="black",
    )


def index() -> rx.Component:
    return rx.box(
        rx.cond(
            State.show_onboarding,
            onboarding_view(),
            rx.box(
                # --- BACKGROUND ---
                rx.box(
                    position="fixed", top="0", left="0", width="100%", height="100%",
                    background=rx.color_mode_cond(
                        "radial-gradient(circle at 80% 10%, rgba(238,195,115,0.15), transparent 50%), radial-gradient(circle at 10% 80%, rgba(112,191,182,0.15), transparent 50%), #F7FAFC",
                        "radial-gradient(circle at 20% 20%, rgba(112,191,182,0.1), transparent 50%), #0F172A"
                    ),
                    z_index="-1",
                ),
                navbar(),
                rx.container(
                    rx.vstack(
                        # --- HEADER ---
                        rx.vstack(
                            rx.text("Bem-vindo de volta", size="2", weight="medium", color="#718096", opacity=0.8),
                            rx.heading(f"Olá, {State.nome_usuario}", size="8", weight="bold"),
                            align_items="center",
                            padding_top="1em",
                        ),
                        
                        # --- IKIGAI DIAGRAM ---
                        ikigai(),
                        
                        # --- DASHBOARD GRID ---
                        rx.flex(
                            # Lado Esquerdo: Trilhas
                            rx.box(
                                card_custom(
                                    "Sua Jornada até aqui",
                                    meditation_trail(),
                                    icon="map"
                                ),
                                width=["100%", "100%", "58%"],
                            ),
                            # Lado Direito: Insights
                            rx.vstack(
                                card_custom(
                                    "Diário de Insights",
                                    rx.vstack(
                                        rx.text_area(
                                            value=State.insight_input,
                                            on_change=State.set_insight_input,
                                            placeholder="O que você descobriu hoje?",
                                            width="100%",
                                            height="120px",
                                            radius="large",
                                            variant="soft",
                                        ),
                                        rx.button(
                                            "Salvar Reflexão",
                                            on_click=State.save_insight,
                                            size="2",
                                            color_scheme="grass",
                                            width="100%",
                                            radius="full",
                                        ),
                                        spacing="3",
                                        width="100%",
                                    ),
                                    icon="notebook-pen",
                                    footer=rx.text(f"Último Insight: {State.last_insight}", size="1", italic=True, opacity=0.7, padding_top="1em")
                                ),
                                card_custom(
                                    "Propósito Sugerido",
                                    rx.text("Baseado no seu Ikigai, hoje é um bom dia para focar em ajudar pessoas com tecnologia.", size="2", italic=True),
                                    icon="sparkles"
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
                                "Conversar com Mentor",
                                size="4",
                                radius="full",
                                background="linear-gradient(90deg, #70BFB6 0%, #66B6CE 100%)",
                                color="white",
                                padding_x="3em",
                                padding_y="1.5em",
                                box_shadow="0 10px 30px rgba(112, 191, 182, 0.4)",
                                _hover={"transform": "scale(1.05)", "box_shadow": "0 15px 40px rgba(112, 191, 182, 0.5)"},
                                on_click=lambda: rx.redirect("/chat"), 
                            ),
                            rx.text("Inicie sua conversa diária", size="2", color="#718096", opacity=0.6),
                            padding_y="3em",
                            align_items="center",
                        ),
                        spacing="6",
                        width="100%",
                        max_width="750px", 
                        margin_x="auto",
                    )
                ),
            )
        ),
        background=rx.cond(State.tema=="hacker", "black", rx.cond(State.tema=="low_dark", "#1A1B26", "#F0F2F5")),
        color=rx.cond(State.tema=="hacker", "#00FF41", rx.cond(State.tema=="low_dark", "#A9B1D6", "#333")),
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
            background=rx.cond(State.tema=="hacker", "black", rx.cond(State.tema=="low_dark", "#0F172A", "linear-gradient(160deg, #FDFCFB 0%, #D8E5D8 100%)")),
            z_index="-1",
        ),
        rx.container(
            rx.vstack(
                rx.hstack(
                    rx.button(rx.icon(tag="arrow-left"), on_click=lambda: rx.redirect("/"), variant="ghost", color=rx.cond(State.tema=="hacker", "#00FF41", "inherit")),
                    rx.heading("Mentor IA", size="6", weight="bold", color=rx.cond(State.tema=="hacker", "#00FF41", "inherit")),
                    justify="start",
                    width="100%",
                    padding_y="1em",
                ),
                rx.vstack(
                    rx.foreach(State.messages, lambda m: rx.box(
                        rx.flex(
                            rx.box(
                                rx.markdown(m["content"]),
                                bg=rx.cond(
                                    m["role"]=="user", 
                                    rx.cond(State.tema=="hacker", "#003B00", "#E2E8F0"), 
                                    rx.cond(State.tema=="hacker", "#001100", "white")
                                ),
                                color=rx.cond(State.tema=="hacker", "#00FF41", "#1A202C"),
                                padding="1.2em",
                                border_radius="15px",
                                border=rx.cond(State.tema=="hacker", "1px solid #00FF41", "none"),
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
                        bg=rx.cond(State.tema=="hacker", "black", "white"),
                        color=rx.cond(State.tema=="hacker", "#00FF41", "inherit"),
                        border=rx.cond(State.tema=="hacker", "1px solid #00FF41", "none"),
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
            bg=rx.cond(State.tema=="hacker", "rgba(0,0,0,0.9)", rx.cond(State.tema=="low_dark", "rgba(15,23,42,0.9)", "rgba(255,255,255,0.8)")),
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

