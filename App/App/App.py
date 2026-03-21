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
    
    humores: list[dict] = [
        {"e": "😊", "l": "Feliz"}, {"e": "😔", "l": "Triste"},
        {"e": "😤", "l": "Ansioso"}, {"e": "🤔", "l": "Reflexivo"}
    ]

    def set_user_input(self, val: str):
        self.user_input = val

    def set_sentiment(self, val: str):
        self.sentiment = val

    def on_load(self):
        perfil = banco_dados.buscar_dados_usuario(self.usuario_id)
        if perfil: self.nome_usuario = perfil['nome']
        hist = banco_dados.visualizar_reflexoes_usuario(self.usuario_id, limite=10)
        self.messages = [{"role": "user" if i%2==0 else "assistant", "content": h[2] if i%2==0 else h[3]} 
                         for i, h in enumerate(reversed(hist or []))]

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
        <div style="background: radial-gradient(circle, rgba(255,255,255,1) 0%, rgba(240,245,240,1) 100%); padding: 25px; border-radius: 50%; box-shadow: 0 10px 30px rgba(0,0,0,0.08);">
            <svg width="240" height="240" viewBox="0 0 220 220" style="filter: drop-shadow(0 4px 10px rgba(0,0,0,0.15));">
                <!-- Círculos com opacidade aumentada para 0.5 -->
                <circle cx="110" cy="75" r="55" fill="#FF7896" fill-opacity="0.5" stroke="#FF4D6D" stroke-width="2.5"/>
                <circle cx="110" cy="145" r="55" fill="#78FF96" fill-opacity="0.5" stroke="#2DCE89" stroke-width="2.5"/>
                <circle cx="75" cy="110" r="55" fill="#78B4FF" fill-opacity="0.5" stroke="#11CDEF" stroke-width="2.5"/>
                <circle cx="145" cy="110" r="55" fill="#FFDC78" fill-opacity="0.5" stroke="#FDBF5E" stroke-width="2.5"/>
                
                <text x="110" y="45" text-anchor="middle" font-size="11" fill="#C92A2A" font-weight="900" font-family="sans-serif">O QUE AMA</text>
                <text x="110" y="195" text-anchor="middle" font-size="11" fill="#099268" font-weight="900" font-family="sans-serif">POR QUE É PAGO</text>
                <text x="40" y="113" text-anchor="middle" font-size="11" fill="#1864AB" font-weight="900" font-family="sans-serif" transform="rotate(-90 40 113)">BOM EM</text>
                <text x="180" y="113" text-anchor="middle" font-size="11" fill="#DEB100" font-weight="900" font-family="sans-serif" transform="rotate(90 180 113)">PRECISA</text>
                
                <text x="110" y="118" text-anchor="middle" font-size="18" font-weight="1000" fill="#1A202C" font-family="sans-serif">IKIGAI</text>
            </svg>
        </div>
        """),
        padding_y="2.5em"
    )

def index() -> rx.Component:
    return rx.box(
        # --- BACKGROUND GRADIENT (Deepened) ---
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
                # --- HEADER ---
                rx.hstack(
                    rx.avatar(fallback="EV", variant="solid", color_scheme="grass", size="2"),
                    rx.heading("Espaço Você", size="8", weight="bold", color="#1A202C"),
                    justify="center",
                    width="100%",
                    padding_y="2em",
                ),
                
                # --- IKIGAI SECTION ---
                rx.vstack(
                    rx.text("Sua Jornada de Equilíbrio", size="5", weight="bold", color="#2D3748"),
                    ikigai(),
                    bg="rgba(255, 255, 255, 0.85)",
                    backdrop_filter="blur(12px)",
                    padding="2.5em",
                    border_radius="3xl",
                    width="100%",
                    box_shadow="0 15px 35px rgba(0,0,0,0.1)",
                    border="1px solid rgba(255,255,255,0.6)",
                    align_items="center",
                ),
                
                # --- CHAT SECTION ---
                rx.vstack(
                    rx.foreach(State.messages, lambda m: rx.box(
                        rx.flex(
                            rx.box(
                                rx.markdown(m["content"]),
                                bg=rx.cond(m["role"]=="user", "#E2E8F0", "white"),
                                color="#1A202C",
                                padding="1.2em",
                                border_radius="2xl",
                                border_bottom_right_radius=rx.cond(m["role"]=="user", "4px", "2xl"),
                                border_bottom_left_radius=rx.cond(m["role"]=="user", "2xl", "4px"),
                                max_width="90%",
                                box_shadow="0 4px 12px rgba(0,0,0,0.05)",
                                border="1px solid rgba(0,0,0,0.05)",
                            ),
                            justify=rx.cond(m["role"]=="user", "end", "start"),
                            width="100%",
                        ),
                        width="100%",
                    )),
                    width="100%",
                    spacing="6",
                    padding_y="3em",
                ),
                
                # Espaço para não cobrir pelo input fixo
                rx.box(height="200px"),
                width="100%",
                max_width="550px", 
                margin_x="auto",
            )
        ),
        
        # --- INPUT INTERACTION AREA ---
        rx.box(
            rx.container(
                rx.vstack(
                    # Mood Selection
                    rx.hstack(
                        rx.foreach(State.humores, lambda h: rx.button(
                            rx.text(h["e"], size="6"),
                            on_click=lambda: State.set_sentiment(h["l"]),
                            variant=rx.cond(State.sentiment==h["l"], "solid", "surface"),
                            color_scheme="grass",
                            border_radius="full",
                            size="3",
                            _hover={"transform": "scale(1.1)"},
                            transition="all 0.2s",
                        )),
                        justify="center",
                        width="100%",
                        spacing="4",
                        padding_bottom="0.8em",
                    ),
                    # Input field
                    rx.hstack(
                        rx.input(
                            placeholder="Como você se sente hoje?",
                            value=State.user_input,
                            on_change=State.set_user_input,
                            width="100%",
                            variant="surface",
                            size="3",
                            radius="full",
                            bg="white",
                            border="1px solid #E2E8F0",
                            on_key_down=State.handle_submit_enter,
                        ),
                        rx.button(
                            rx.cond(State.is_processing, rx.spinner(size="2"), rx.icon(tag="send", size=22)),
                            on_click=State.handle_submit,
                            size="3",
                            radius="full",
                            color_scheme="grass",
                            box_shadow="0 4px 10px rgba(0,128,0,0.2)",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    spacing="2",
                ),
                max_width="550px",
                margin_x="auto",
            ),
            position="fixed",
            bottom="0",
            width="100%",
            bg="rgba(255, 255, 255, 0.92)",
            backdrop_filter="blur(20px)",
            padding="2em",
            border_top="1px solid rgba(0,0,0,0.08)",
            z_index="10",
        ),
        min_height="100vh",
        on_mount=State.on_load
    )

app = rx.App(
    theme=rx.theme(
        accent_color="grass",
        radius="full",
        appearance="light",
    )
)
app.add_page(index)

