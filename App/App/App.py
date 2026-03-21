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

def ikigai() -> rx.Component:
    return rx.center(rx.html("""
        <svg width="180" height="180" viewBox="0 0 200 200">
            <circle cx="100" cy="70" r="60" fill="rgba(255,182,193,0.3)" stroke="#FFB6C1"/>
            <circle cx="70" cy="110" r="60" fill="rgba(173,216,230,0.3)" stroke="#ADD8E6"/>
            <circle cx="130" cy="110" r="60" fill="rgba(255,255,224,0.3)" stroke="#FFFFE0"/>
            <circle cx="100" cy="140" r="60" fill="rgba(144,238,144,0.3)" stroke="#90EE90"/>
            <text x="100" y="110" text-anchor="middle" font-size="12" font-weight="bold">Ikigai</text>
        </svg>
    """))

def index() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.heading("Espaço Você", size="6", padding_y="1em"),
                rx.vstack(rx.heading("Seu Equilíbrio", size="3"), ikigai(), 
                          bg="white", padding="2em", border_radius="xl", width="100%", box_shadow="md"),
                rx.vstack(rx.foreach(State.messages, lambda m: rx.box(
                    rx.markdown(m["content"]), bg=rx.cond(m["role"]=="user", "gray.100", "white"),
                    padding="1em", border_radius="lg", width="100%", border="1px solid #EEE"
                )), width="100%", spacing="4", padding_y="2em"),
                padding_bottom="200px"
            )
        ),
        rx.box(
            rx.container(
                rx.vstack(
                    rx.hstack(rx.foreach(State.humores, lambda h: rx.button(
                        h["e"], on_click=lambda: State.set_sentiment(h["l"]),
                        variant=rx.cond(State.sentiment==h["l"], "solid", "ghost")
                    )), justify="center", width="100%"),
                    rx.hstack(
                        rx.input(value=State.user_input, on_change=State.set_user_input, width="100%"),
                        rx.button(rx.cond(State.is_processing, rx.spinner(), rx.icon(tag="send")), 
                                  on_click=State.handle_submit),
                        width="100%"
                    )
                )
            ),
            position="fixed", bottom="0", width="100%", bg="white", padding="1.5em", border_top="1px solid #EEE"
        ),
        bg="#F8FAF8", min_height="100vh", on_mount=State.on_load
    )

app = rx.App(theme=rx.theme(accent_color="grass"))
app.add_page(index)

