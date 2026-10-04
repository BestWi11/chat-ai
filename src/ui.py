"""Módulo de Interface Gráfica com Gradio."""

import os
import gradio as gr
from typing import List, Dict, Tuple, Generator
from src.config_loader import AssistantConfig
from src.llm_client import LLMClient


def create_ui(config: AssistantConfig) -> gr.Blocks:
    """Constrói a interface web Gradio a partir do objeto AssistantConfig."""

    llm_client = LLMClient(config)

    # Cores personalizadas
    primary = config.theme.primary_color
    secondary = config.theme.secondary_color
    bg = config.theme.background_color
    text_c = config.theme.text_color

    custom_css = f"""
    :root {{
        --primary-color: {primary};
        --secondary-color: {secondary};
        --bg-color: {bg};
        --text-color: {text_c};
    }}
    body, .gradio-container {{
        background-color: {bg} !important;
        color: {text_c} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .header-container {{
        text-align: center;
        padding: 24px 16px 12px 16px;
        margin-bottom: 8px;
    }}
    .header-logo {{
        display: block;
        margin: 0 auto 12px auto;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }}
    .header-title {{
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 6px;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }}
    .header-desc {{
        font-size: 15px;
        color: #94A3B8;
        max-width: 650px;
        margin: 0 auto;
        line-height: 1.5;
    }}
    .chatbot-wrapper {{
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 14px !important;
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(8px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3) !important;
    }}
    .example-btn {{
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #E2E8F0 !important;
        font-size: 13px !important;
        border-radius: 20px !important;
        padding: 6px 14px !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
    }}
    .example-btn:hover {{
        background: {primary} !important;
        border-color: {secondary} !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }}
    .send-btn {{
        background: {primary} !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    .send-btn:hover {{
        background: {secondary} !important;
    }}
    """

    theme = gr.themes.Soft(
        primary_hue="blue",
        neutral_hue="slate",
    ).set(
        body_background_fill=bg,
        block_background_fill="rgba(30, 41, 59, 0.8)",
        block_border_color="rgba(255, 255, 255, 0.1)",
        input_background_fill="rgba(15, 23, 42, 0.6)",
        button_primary_background_fill=primary,
        button_primary_background_fill_hover=secondary,
        button_primary_text_color="#FFFFFF",
    )

    with gr.Blocks(theme=theme, css=custom_css, title=config.app.title) as demo:
        # Cabeçalho
        with gr.Column(elem_classes=["header-container"]):
            if config.app.logo_path and os.path.exists(config.app.logo_path):
                gr.HTML(
                    f"""
                    <img src="file/{config.app.logo_path}" 
                         width="{config.app.logo_width}" 
                         class="header-logo" 
                         alt="Logo {config.app.title}"/>
                    """
                )
            gr.HTML(f"<h1 class='header-title'>{config.app.title}</h1>")
            gr.HTML(f"<p class='header-desc'>{config.app.description}</p>")

        # Chatbot
        chatbot = gr.Chatbot(
            elem_classes=["chatbot-wrapper"],
            height=480,
            show_label=False,
            bubble_full_width=False,
            avatar_images=(
                None,
                config.app.logo_path if (config.app.logo_path and os.path.exists(config.app.logo_path)) else None
            ),
            render_markdown=True,
        )

        # Sugestões de Perguntas
        if config.example_questions:
            gr.HTML("<div style='font-size: 13px; color: #94A3B8; margin-top: 10px; margin-bottom: 6px; font-weight: 600;'>💡 Sugestões de perguntas:</div>")
            with gr.Row():
                example_buttons = []
                for q_text in config.example_questions:
                    btn = gr.Button(q_text, size="sm", elem_classes=["example-btn"])
                    example_buttons.append((btn, q_text))

        # Campo de Mensagem e Ações
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Digite sua dúvida sobre Engenharia de Dados ou Inteligência Artificial...",
                show_label=False,
                scale=9,
                lines=1,
                max_lines=4,
                container=False,
                autofocus=True
            )
            submit_btn = gr.Button("Enviar 🚀", scale=2, variant="primary", elem_classes=["send-btn"])
            clear_btn = gr.Button("Limpar 🗑️", scale=1, variant="secondary")

        # Handlers de conversação
        def user_message(user_msg: str, chat_history: List[Tuple[str, str]]):
            if not user_msg or not user_msg.strip():
                return "", chat_history or []
            history = list(chat_history) if chat_history else []
            return "", history + [(user_msg.strip(), "")]

        def bot_response(chat_history: List[Tuple[str, str]]) -> Generator[List[Tuple[str, str]], None, None]:
            if not chat_history:
                return

            history = list(chat_history)
            user_msg = str(history[-1][0])
            # Monta histórico estruturado para a API
            api_history = []
            for u, b in history[:-1]:
                if u:
                    api_history.append({"role": "user", "content": str(u)})
                if b:
                    api_history.append({"role": "assistant", "content": str(b)})
            api_history.append({"role": "user", "content": user_msg})

            accumulated_response = ""
            for chunk in llm_client.stream_chat(api_history):
                accumulated_response += chunk
                history[-1] = (user_msg, accumulated_response)
                yield history

        # Eventos do botão Enviar e tecla Enter
        msg_input.submit(
            user_message,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot],
            queue=False
        ).then(
            bot_response,
            inputs=[chatbot],
            outputs=[chatbot]
        )

        submit_btn.click(
            user_message,
            inputs=[msg_input, chatbot],
            outputs=[msg_input, chatbot],
            queue=False
        ).then(
            bot_response,
            inputs=[chatbot],
            outputs=[chatbot]
        )

        # Botão Limpar conversa
        def clear_chat():
            return []

        clear_btn.click(clear_chat, outputs=[chatbot], queue=False)

        # Eventos para os botões de perguntas sugeridas
        if config.example_questions:
            for btn, q_text in example_buttons:
                def make_example_handler(prompt_text: str):
                    def handle_example_click(chat_h):
                        curr = list(chat_h) if chat_h else []
                        return "", curr + [(prompt_text, "")]
                    return handle_example_click

                btn.click(
                    make_example_handler(q_text),
                    inputs=[chatbot],
                    outputs=[msg_input, chatbot],
                    queue=False
                ).then(
                    bot_response,
                    inputs=[chatbot],
                    outputs=[chatbot]
                )

    return demo
