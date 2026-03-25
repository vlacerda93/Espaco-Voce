import reflex as rx
import sys
import os

# --- SETUP DE CAMINHO ---
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path: sys.path.insert(0, root_dir)

import Backend.banco_dados_pg as banco_dados
import Backend.LLM.ia_manager as ia_manager

class State(rx.State):
    usuario_id: int = 1
    nome_usuario: str = "Vinícius"
    user_input: str = ""
    messages: list[dict] = []
    is_processing: bool = False
    sentiment: str = "Neutro"
    interaction_count: int = 0
    
    # --- DYNAMIC THEMES ---
    # Opções: "light", "low_dark", "hacker", "zen_rose"
    tema: str = "hacker" 

    def set_tema(self, val): self.tema = val

    # --- AUTH STATE ---
    is_logged_in: bool = False
    
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
    
    # --- UI STATE ---
    is_processing: bool = False
    is_sending: bool = False
    user_input: str = ""
    messages: list[dict[str, str]] = []
    
    # --- INSIGHTS STATE ---
    insight_input: str = ""
    last_insight: str = "Tudo começa com um pequeno passo..."
    
    # --- TRILHA HISTORICAL STATE ---
    history_trail: list[dict] = []
    
    # --- PROJECT STATE (Espaço Você 3.0) ---
    projeto_id: int = 0
    projeto_nome: str = "Nenhum Projeto Ativo"
    projeto_objetivo: str = ""
    projeto_passo: int = 1
    projeto_frase: str = "Início da Jornada" # Frase curta sobre a fase
    jornada_passos: list[dict] = []
    
    # --- DYNAMIC PURPOSE ---
    proposito_sugerido: str = "Tudo começa com um pequeno passo..." # Frase que muda conforme Ikigai
    
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
    
    def set_onboarding_step(self, step: int): 
        self.onboarding_step = step

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

        # Carrega último insight do PostgreSQL
        entries = banco_dados.buscar_insights_usuario(self.usuario_id, limite=1)
        if entries:
            self.last_insight = entries[0][1]
            
        # Carrega Histórico de Resumos do PostgreSQL (Trilhas)
        ts = banco_dados.buscar_trilhas(self.usuario_id, limite=4)
        historico_invertido = list(reversed(ts))
        self.history_trail = []
        for i, t in enumerate(historico_invertido):
            resumo_curto = t[1][:75] + "..." if len(t[1]) > 75 else t[1]
            self.history_trail.append({"index": str(i+1), "title": f"Sessão {i+1}", "resumo": resumo_curto, "full": t[1]})

        # --- CARREGA ESTADO DO PROJETO 3.0 ---
        projeto_data = banco_dados.buscar_projeto_ativo(self.usuario_id)
        if projeto_data:
            self.projeto_id = projeto_data["id"]
            self.projeto_nome = projeto_data["nome_projeto"]
            self.projeto_objetivo = projeto_data["objetivo_geral"]
            self.projeto_passo = projeto_data["passo_atual"]
            
            # --- ATUALIZA FRASE DO STATUS (Ponto 3) ---
            fases = {
                1: "Plantando Sementes 🧬", 2: "Explorando Horizontes 🌏", 
                3: "Conectando Pontos 🔗", 4: "Manifestando Intenção ✨",
                5: "Colhendo Frutos 🍎"
            }
            self.projeto_frase = fases.get(self.projeto_passo, "Caminhando...")

            # --- GERA PROPÓSITO DINÂMICO (Ponto 2) ---
            if self.onboarding_gosta and self.onboarding_precisa:
                g_txt = self.onboarding_gosta.replace("Eu amo ", "").replace("Eu gosto de ", "").strip()
                p_txt = self.onboarding_precisa.replace("Eu sinto que o mundo precisa de ", "").replace("O mundo precisa de ", "").strip()
                
                # Slicing super generoso (250 chars) para frases completas
                g = (g_txt[:250] + "...") if len(g_txt) > 250 else g_txt
                p = (p_txt[:250] + "...") if len(p_txt) > 250 else p_txt
                
                self.proposito_sugerido = f"Use sua paixão por '{g}' para suprir a necessidade de '{p}' no mundo hoje."
            else:
                self.proposito_sugerido = "Baseado no seu Ikigai, hoje é um bom dia para focar no seu propósito."

            
        # Se chegamos aqui, o usuário já tem dados básicos, podemos considerar logado
        if perfil:
            self.is_logged_in = True
            
            # Carrega os passos concluídos da jornada
            if self.projeto_id:
                passos = banco_dados.buscar_jornada_passos(self.projeto_id)
                self.jornada_passos = [{"num": p[0], "resumo": p[1]} for p in passos]

    def logout(self):
        self.is_logged_in = False
        return rx.redirect("/")

    def login_mock(self, provider: str):
        # Mock de login social
        self.is_logged_in = True
        return rx.toast.info(f"Conectado via {provider}!")

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
        
        # --- INTERCEPTADOR DE TAGS (Espaço Você 3.0) 🔴 ---
        # Detecta se a IA decidiu avançar o passo do projeto
        if "[AVANÇAR_PASSO:" in res:
            try:
                # Extrai o resumo entre a tag
                tag_parts = res.split("[AVANÇAR_PASSO:")
                clean_res = tag_parts[0].strip()
                resumo_decisao = tag_parts[1].split("]")[0].strip()
                
                if self.projeto_id > 0:
                    # Gera o UPDATE no banco
                    novo_passo = self.projeto_passo + 1
                    banco_dados.atualizar_passo_projeto(self.projeto_id, novo_passo, resumo_decisao)
                    
                    # Atualiza o estado da UI na hora
                    self.projeto_passo = novo_passo
                    # Recarrega a jornada
                    passos = banco_dados.buscar_jornada_passos(self.projeto_id)
                    self.jornada_passos = [{"num": p[0], "resumo": p[1]} for p in passos]
                
                # Substitui a resposta pela versão limpa (sem a tag)
                res = clean_res
            except Exception as e:
                print(f"⚠️ Erro ao processar avanço de passo: {e}")

        if is_last_message:
            self.interaction_count = 0
            
        self.messages.append({"role": "assistant", "content": res})
        self.is_processing = False

    async def finish_session(self):
        """Dispara o resumo da IA e avança de passo na jornada."""
        self.is_sending = True
        resumo = await ia_manager.concluir_passo_com_resumo(self.usuario_id)
        
        # Atualiza a UI com os novos dados
        self.projeto_passo += 1
        passos = banco_dados.buscar_jornada_passos(self.projeto_id)
        self.jornada_passos = [{"num": p[0], "resumo": p[1]} for p in passos]
        
        self.is_sending = False
        return rx.redirect("/")

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
            rx.match(
                State.tema,
                ("hacker", rx.box(
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
                            class_name="ikigai-circle circle-1", on_click=lambda: State.select_pilar("PAIXÃO")
                        ),
                        # RENDA
                        rx.el.circle(
                            cx="110", cy="145", r="55", fill="rgba(0, 255, 65, 0.05)", stroke="#00FF41", stroke_width="1.5", stroke_dasharray="2 2",
                            class_name="ikigai-circle circle-2", on_click=lambda: State.select_pilar("RENDA")
                        ),
                        # TALENTO
                        rx.el.circle(
                            cx="75", cy="110", r="55", fill="rgba(0, 255, 65, 0.1)", stroke="#00FF41", stroke_width="1.5",
                            class_name="ikigai-circle circle-3", on_click=lambda: State.select_pilar("TALENTO")
                        ),
                        # MISSÃO
                        rx.el.circle(
                            cx="145", cy="110", r="55", fill="rgba(0, 255, 65, 0.05)", stroke="#00FF41", stroke_width="1.5", stroke_dasharray="2 2",
                            class_name="ikigai-circle circle-4", on_click=lambda: State.select_pilar("MISSÃO")
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
                )),
                ("low_dark", rx.box(
                    rx.el.svg(
                        rx.el.circle(
                            cx="110", cy="75", r="58", fill="rgba(63, 81, 181, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                            class_name="ikigai-circle circle-1", on_click=lambda: State.select_pilar("PAIXÃO")
                        ),
                        rx.el.circle(
                            cx="110", cy="145", r="58", fill="rgba(92, 107, 192, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                            class_name="ikigai-circle circle-2", on_click=lambda: State.select_pilar("RENDA")
                        ),
                        rx.el.circle(
                            cx="75", cy="110", r="58", fill="rgba(63, 81, 181, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                            class_name="ikigai-circle circle-3", on_click=lambda: State.select_pilar("TALENTO")
                        ),
                        rx.el.circle(
                            cx="145", cy="110", r="58", fill="rgba(92, 107, 192, 0.3)", stroke="#5C6BC0", stroke_width="1.5",
                            class_name="ikigai-circle circle-4", on_click=lambda: State.select_pilar("MISSÃO")
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
                )),
                ("zen_rose", rx.box(
                    rx.el.svg(
                        rx.el.defs(
                            rx.el.radial_gradient(rx.el.stop(offset="0%", stop_color="rgba(199, 125, 154, 0.2)"), rx.el.stop(offset="100%", stop_color="transparent"), id="glow-rose")
                        ),
                        rx.el.circle(cx="110", cy="110", r="100", fill="url(#glow-rose)", filter="blur(30px)"),
                        rx.el.circle(cx="110", cy="75", r="60", fill="rgba(199, 125, 154, 0.15)", stroke="#C77D9A", stroke_width="2", class_name="ikigai-circle circle-1", on_click=lambda: State.select_pilar("PAIXÃO")),
                        rx.el.circle(cx="110", cy="145", r="60", fill="rgba(252, 227, 138, 0.15)", stroke="#FCE38A", stroke_width="2", class_name="ikigai-circle circle-2", on_click=lambda: State.select_pilar("RENDA")),
                        rx.el.circle(cx="75", cy="110", r="60", fill="rgba(255, 133, 161, 0.15)", stroke="#FF85A1", stroke_width="2", class_name="ikigai-circle circle-3", on_click=lambda: State.select_pilar("TALENTO")),
                        rx.el.circle(cx="145", cy="110", r="60", fill="rgba(168, 164, 206, 0.15)", stroke="#A8A4CE", stroke_width="2", class_name="ikigai-circle circle-4", on_click=lambda: State.select_pilar("MISSÃO")),
                        rx.el.circle(cx="110", cy="110", r="32", fill="#FFFDF5", stroke="#C77D9A", stroke_width="2"),
                        rx.el.circle(cx="110", cy="110", r="28", fill="none", stroke="#FCE38A", stroke_width="1", stroke_dasharray="2 2"),
                        rx.el.text("IKIGAI", x="110", y="115", text_anchor="middle", font_size="10", font_weight="900", fill="#C77D9A"),
                        width="280", height="280", view_box="0 0 220 220"
                    ),
                    position="relative", width="300px", height="300px", display="flex", align_items="center", justify_content="center"
                )),
                # Default Light
                rx.box(
                    rx.el.svg(
                        rx.el.circle(
                            cx="110", cy="75", r="58", fill="rgba(112, 191, 182, 0.2)", stroke="#70BFB6",
                            class_name="ikigai-circle circle-1", on_click=lambda: State.select_pilar("PAIXÃO")
                        ),
                        rx.el.circle(
                            cx="110", cy="145", r="58", fill="rgba(151, 140, 185, 0.2)", stroke="#978CB9",
                            class_name="ikigai-circle circle-2", on_click=lambda: State.select_pilar("RENDA")
                        ),
                        rx.el.circle(
                            cx="75", cy="110", r="58", fill="rgba(102, 182, 206, 0.2)", stroke="#66B6CE",
                            class_name="ikigai-circle circle-3", on_click=lambda: State.select_pilar("TALENTO")
                        ),
                        rx.el.circle(
                            cx="145", cy="110", r="58", fill="rgba(238, 195, 115, 0.2)", stroke="#EEC373",
                            class_name="ikigai-circle circle-4", on_click=lambda: State.select_pilar("MISSÃO")
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
            ),
            padding_y="1.5em"
        ),
        # Display Area para o Pilar Selecionado
        rx.cond(
            State.selected_pilar != "",
            rx.vstack(
                rx.heading(f"Pilar: {State.selected_pilar}", size="4", color=rx.match(
                    State.tema,
                    ("hacker", "#00FF41"),
                    ("zen_rose", "#C77D9A"),
                    "inherit"
                )),
                rx.text(State.pilar_content, size="2", italic=True, text_align="center"),
                rx.button("Fechar", on_click=lambda: State.select_pilar(""), variant="soft", size="1"),
                padding="1.5em",
                bg=rx.match(
                    State.tema,
                    ("hacker", "rgba(0,255,65,0.05)"),
                    ("zen_rose", "rgba(255, 255, 255, 0.4)"),
                    "rgba(0,0,0,0.03)"
                ),
                backdrop_filter=rx.cond(State.tema == "zen_rose", "blur(10px)", "none"),
                border_radius="xl",
                border=rx.match(
                    State.tema,
                    ("hacker", "1px solid #00FF41"),
                    ("zen_rose", "1px solid rgba(255, 133, 161, 0.3)"),
                    "1px solid rgba(0,0,0,0.1)"
                ),
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
        rx.image(src="/logo.png", width="150px"),
        rx.spacer(),
        rx.segmented_control.root(
            rx.segmented_control.item("Hacker 💻", value="hacker"),
            rx.segmented_control.item("Low Dark 🌙", value="low_dark"),
            rx.segmented_control.item("Light ☀️", value="light"),
            rx.segmented_control.item("Zen Rose 🌸", value="zen_rose"),
            on_change=State.set_tema,
            value=State.tema,
            variant="classic",
            radius="large",
        ),
        rx.button(
            rx.icon(tag="log-out", size=18),
            on_click=State.logout,
            variant="ghost",
            color_scheme="ruby",
            radius="full",
            id="logout-button",
            _hover={"bg": "rgba(255,0,0,0.1)"}
        ),
        width="100%",
        padding="1.5em",
        bg=rx.match(
            State.tema,
            ("hacker", "black"),
            ("low_dark", "#1A1A1A"),
            ("zen_rose", "rgba(255, 253, 245, 0.8)"),
            "#F7FAFC"
        ),
        backdrop_filter=rx.cond(State.tema == "zen_rose", "blur(12px)", "none"),
        border_bottom=rx.match(
            State.tema,
            ("hacker", "1px solid #00FF41"),
            ("zen_rose", "1px solid rgba(199, 125, 154, 0.1)"),
            "none"
        ),
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
            bg=rx.match(
                State.tema,
                ("hacker", rx.cond(is_locked, "#001100", rx.cond(is_active, "#00FF41", "#003B00"))),
                ("zen_rose", rx.cond(is_locked, "rgba(255,255,255,0.4)", rx.cond(is_active, "#E5989B", "#FFB4A2"))),
                rx.cond(is_locked, "#EDF2F7", rx.cond(is_active, "#4895EF", "#A0AEC0"))
            ),
            color=rx.cond(is_active, "white", rx.match(State.tema, ("zen_rose", "#6D597A"), ("hacker", "#003B41"), "#718096")),
            box_shadow=rx.cond(is_active, rx.match(State.tema, ("zen_rose", "0 0 20px rgba(229, 152, 155, 0.4)"), "lg"), "none"),
            border=rx.cond(is_active, "2px solid white", "none"),
        ),
        rx.text(title, size="1", weight="medium", width="60px", text_align="center", color=rx.match(State.tema, ("zen_rose", "#C77D9A"), ("hacker", "#00FF41"), "#718096")),
        spacing="2",
        align_items="center",
    )

def meditation_trail() -> rx.Component:
    return rx.vstack(
        rx.text("Degraus do seu Ikigai", size="4", weight="bold", padding_bottom="1em"),
        
        rx.cond(
            State.jornada_passos.length() > 0, 
            rx.hstack(
                rx.foreach(State.jornada_passos, lambda item: rx.hstack(
                    rx.tooltip(
                        trail_item("Passo Concluído", is_active=False, is_locked=False),
                        content=item["resumo"]
                    ),
                    rx.box(width="30px", height="2px", bg="#EDF2F7", margin_top="-20px")
                )),
                rx.tooltip(
                    trail_item("Você está aqui", is_active=True, is_locked=False),
                    content="Aguardando a conclusão dos objetivos atuais."
                ),
                spacing="0", overflow_x="auto", width="100%", padding_x="1em", justify="start",
            ),
            rx.hstack(
                trail_item("Passo 1", is_active=True, is_locked=False),
                rx.text("Iniciando jornada...", size="2", italic=True, opacity=0.7)
            )
        ),
        
        bg=rx.match(
            State.tema,
            ("hacker", "black"),
            ("low_dark", "#1A1B26"),
            ("zen_rose", "rgba(255, 255, 255, 0.2)"),
            "rgba(255,255,255,0.4)"
        ),
        backdrop_filter=rx.cond(State.tema == "zen_rose", "blur(8px)", "none"),
        padding="2em",
        border_radius="15px",
        width="100%",
        border=rx.match(
            State.tema,
            ("hacker", "1px solid #00FF41"),
            ("zen_rose", "1px solid rgba(255, 255, 255, 0.3)"),
            "1px solid rgba(0,0,0,0.1)"
        ),
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
        bg=rx.match(
            State.tema,
            ("hacker", "black"),
            ("low_dark", "#1A1B26"),
            ("zen_rose", "rgba(255, 255, 255, 0.4)"),
            "white"
        ),
        backdrop_filter=rx.cond(State.tema == "zen_rose", "blur(10px)", "none"),
        padding="1.5em",
        border_radius="15px",
        box_shadow=rx.match(
            State.tema,
            ("hacker", "0 0 20px rgba(0,255,65,0.1)"),
            ("zen_rose", "0 10px 40px rgba(229, 152, 155, 0.15)"),
            "0 10px 30px rgba(0,0,0,0.06)"
        ),
        border=rx.match(
            State.tema,
            ("hacker", "1px solid #00FF41"),
            ("zen_rose", "1px solid rgba(255, 255, 255, 0.6)"),
            "1px solid rgba(72, 149, 239, 0.1)"
        ),
        width="100%",
        align_items="start",
    )



def onboarding_view() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Bem-vindo ao Espaço Você", size="8", weight="bold", color="#1A202C", text_align="center"),
            rx.text("Vamos iniciar sua jornada para encontrar seu Ikigai.", size="4", color="#4A5568", text_align="center"),
            
            rx.vstack( # Added this vstack to wrap all conditional steps
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
                spacing="4", width="100%" # Apply spacing and width to the wrapper vstack
            ), # Closing tag for the added vstack
            
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


# --- LOGIN PAGE (AUTH SOCIAL) ---
def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.image(src="/logo.png", width="250px", margin_bottom="2em"),
            rx.heading("Desperte seu Ikigai", size="8", weight="bold", color="white"),
            rx.text("Conecte-se para continuar sua jornada de autodescoberta.", size="3", color="white", opacity=0.8),
            
            rx.vstack(
                rx.button(
                    rx.hstack(
                        rx.icon(tag="chrome"),
                        rx.text("Entrar com Google"),
                        spacing="2"
                    ),
                    on_click=lambda: State.login_mock(provider="Google"),
                    width="100%",
                    size="4",
                    bg="white",
                    color="black",
                    _hover={"bg": "#f8f9fa", "transform": "scale(1.02)"},
                    radius="full",
                    id="google-login-button"
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="github"),
                        rx.text("Entrar com GitHub"),
                        spacing="2"
                    ),
                    on_click=lambda: State.login_mock(provider="GitHub"),
                    width="100%",
                    size="4",
                    bg="#24292e",
                    color="white",
                    _hover={"bg": "#1b1f23", "transform": "scale(1.02)"},
                    radius="full",
                    id="github-login-button"
                ),
                spacing="4",
                width="100%",
                padding_top="2em"
            ),
            
            spacing="4",
            padding="4em",
            bg="rgba(255, 255, 255, 0.05)",
            backdrop_filter="blur(20px)",
            border="1px solid rgba(255, 255, 255, 0.1)",
            border_radius="3xl",
            max_width="450px",
            align_items="center"
        ),
        width="100%",
        height="100vh",
        background="radial-gradient(circle at 50% 50%, #1E88E5 0%, #0F172A 100%)" # Azul Royal Pro para o login
    )

def index() -> rx.Component:
    return rx.box(
        rx.cond(
            State.is_logged_in,
            rx.cond(
                State.show_onboarding,
                onboarding_view(),
                rx.box(
                    # --- DASHBOARD CONTENT ---
                    # --- BACKGROUND (PRO 3.0) ---
                    rx.box(
                        position="fixed", top="0", left="0", width="100%", height="100%",
                    background=rx.match(
                        State.tema,
                        ("hacker", "radial-gradient(circle at 80% 10%, rgba(0,255,65,0.05), transparent 50%), #000"),
                        ("low_dark", "radial-gradient(circle at 20% 20%, rgba(92,107,192,0.1), transparent 50%), #0F172A"),
                        ("zen_rose", "#9B5DE5"), # ROXO VIBRANTE (TESTE)
                        "#1E88E5" # AZUL ROYAL (TESTE)
                    ),
                    z_index="-1",
                ),
                # Grain Overlay for Texture
                rx.box(
                    position="fixed", top="0", left="0", width="100%", height="100%",
                    opacity="0.03",
                    pointer_events="none",
                    background_image="url('https://grainy-gradients.vercel.app/noise.svg')",
                    z_index="0",
                ),
                navbar(),
                rx.container(
                    rx.vstack(
                        # --- HEADER ---
                        rx.vstack(
                            rx.heading(f"Olá de novo, {State.nome_usuario}!", size="9", weight="bold", color="white", on_click=lambda: State.set_show_onboarding(True), cursor="pointer"),
                            rx.text("O que vamos fazer aqui no seu espaço hoje?", size="4", weight="medium", color="white", opacity=0.9),
                            align_items="center",
                            padding_top="2em",
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
                                    "Status do Projeto",
                                    rx.vstack(
                                        rx.heading(State.projeto_nome, size="4", color=rx.match(State.tema, ("hacker", "#00FF41"), ("zen_rose", "#C77D9A"), "inherit")),
                                        rx.text(State.projeto_frase, size="2", weight="bold", color="grass"), # Frase da fase
                                        rx.text(f"Objetivo: {State.projeto_objetivo}", size="1", opacity=0.8),
                                        rx.badge(f"PASSO {State.projeto_passo}", color_scheme="grass", variant="outline"),
                                        width="100%",
                                        spacing="2",
                                    ),
                                    icon="rocket"
                                ),
                                card_custom(
                                    "Propósito Sugerido",
                                    rx.text(State.proposito_sugerido, size="2", italic=True),
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
                                background=rx.match(
                                    State.tema,
                                    ("hacker", "linear-gradient(90deg, #00FF41 0%, #008F11 100%)"),
                                    ("zen_rose", "linear-gradient(90deg, #C77D9A 0%, #E8B4CB 100%)"),
                                    "linear-gradient(90deg, #70BFB6 0%, #66B6CE 100%)"
                                ),
                                color="white",
                                padding_x="3em",
                                padding_y="1.5em",
                                box_shadow=rx.match(
                                    State.tema,
                                    ("hacker", "0 10px 30px rgba(0, 255, 65, 0.3)"),
                                    ("zen_rose", "0 10px 30px rgba(199, 125, 154, 0.3)"),
                                    "0 10px 30px rgba(112, 191, 182, 0.4)"
                                ),
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
                    )
                ),
            ),
            login_page()
        ),
        background="transparent",
        color=rx.match(
            State.tema,
            ("hacker", "#00FF41"),
            ("low_dark", "#A9B1D6"),
            ("zen_rose", "white"),
            "white" 
        ),
        on_mount=State.on_load
    )



# --- CHAT PAGE ---
def chat_page() -> rx.Component:
    return rx.box(
        rx.box(
            background=rx.match(
                State.tema,
                ("hacker", "black"),
                ("low_dark", "#0F172A"),
                ("zen_rose", "#9B5DE5"), # ROXO VIBRANTE
                "#1E88E5" # AZUL FORTE
            ),
            z_index="-1",
        ),
        rx.container(
            rx.vstack(
                rx.hstack(
                    rx.button(rx.icon(tag="arrow-left"), on_click=lambda: rx.redirect("/"), variant="ghost", color=rx.match(State.tema, ("hacker", "#00FF41"), ("zen_rose", "#E5989B"), "inherit")),
                    rx.image(src="/logo.png", width="150px"),
                    justify="start",
                    width="100%",
                    padding_y="1em",
                ),
                rx.vstack(
                    rx.foreach(State.messages, lambda m: rx.box(
                        rx.flex(
                            rx.box(
                                rx.markdown(m["content"]),
                                bg=rx.match(
                                    State.tema,
                                    ("hacker", rx.cond(m["role"]=="user", "#003B00", "#001100")),
                                    ("zen_rose", rx.cond(m["role"]=="user", "#C77D9A", "rgba(255, 253, 245, 0.6)")),
                                    rx.cond(m["role"]=="user", "#E2E8F0", "white")
                                ),
                                color=rx.match(State.tema, ("hacker", "#00FF41"), ("zen_rose", rx.cond(m["role"]=="user", "white", "#C77D9A")), "#1A202C"),
                                backdrop_filter=rx.cond(State.tema == "zen_rose", "blur(10px)", "none"),
                                padding="1.2em",
                                border_radius="15px",
                                border=rx.match(
                                    State.tema,
                                    ("hacker", "1px solid #00FF41"),
                                    ("zen_rose", "1px solid rgba(199, 125, 154, 0.1)"),
                                    "none"
                                ),
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
                        bg=rx.match(State.tema, ("hacker", "black"), ("zen_rose", "rgba(255,255,255,0.5)"), "white"),
                        color=rx.match(State.tema, ("hacker", "#00FF41"), ("zen_rose", "#C77D9A"), "inherit"),
                        border=rx.match(State.tema, ("hacker", "1px solid #00FF41"), ("zen_rose", "1px solid #C77D9A"), "none"),
                        on_key_down=State.handle_submit_enter,
                    ),
                    rx.button(
                        rx.cond(State.is_processing, rx.spinner(size="2"), rx.icon(tag="send")),
                        on_click=State.handle_submit,
                        radius="full",
                        color_scheme=rx.match(State.tema, ("zen_rose", "crimson"), "grass"),
                    ),
                    rx.button(
                        rx.icon(tag="check-check"),
                        on_click=State.finish_session,
                        radius="full",
                        variant="soft",
                        color_scheme="ruby",
                        tooltip="Encerrar Sessão e Avançar Passo",
                    ),
                    width="100%",
                    spacing="3",
                ),
                max_width="700px",
            ),
            bg=rx.match(
                State.tema,
                ("hacker", "rgba(0,0,0,0.9)"),
                ("low_dark", "rgba(15,23,42,0.9)"),
                ("zen_rose", "rgba(255, 253, 245, 0.7)"),
                "rgba(255,255,255,0.8)"
            ),
            backdrop_filter="blur(12px)",
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

