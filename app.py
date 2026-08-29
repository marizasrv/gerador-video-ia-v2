import os
import tempfile
from pathlib import Path

import streamlit as st
from huggingface_hub import InferenceClient

st.set_page_config(page_title="Gerador Vídeo IA V2", page_icon="🎬", layout="centered")
st.title("🎬 Gerador de Vídeo IA — V2")
st.write("Transforme uma imagem em um pequeno vídeo usando IA.")

try:
    HF_TOKEN = str(st.secrets["HF_TOKEN"]).strip()
except Exception:
    st.error("HF_TOKEN não encontrado. Adicione sua chave nos Secrets do Streamlit.")
    st.stop()

if not HF_TOKEN.startswith("hf_"):
    st.error("A chave HF_TOKEN parece inválida.")
    st.stop()

provider = st.selectbox("Provedor", ["fal-ai", "replicate"])
model = st.text_input("Modelo", value="Wan-AI/Wan2.2-TI2V-5B")

imagem = st.file_uploader("1. Envie a imagem da cena", type=["jpg", "jpeg", "png", "webp"])
prompt = st.text_area(
    "2. Descreva o movimento",
    value="The character moves naturally, blinks and looks around. Gentle cinematic camera movement, smooth motion, consistent character appearance."
)

st.caption("Dica: descreva movimentos simples. Ex.: Luna caminha lentamente, olha para o espelho e levanta a varinha.")

if st.button("✨ Gerar vídeo com IA", type="primary", use_container_width=True):
    if imagem is None:
        st.error("Envie uma imagem primeiro.")
        st.stop()
    if not prompt.strip():
        st.error("Escreva o movimento desejado.")
        st.stop()

    client = InferenceClient(provider=provider, api_key=HF_TOKEN)

    with st.spinner("A IA está criando o vídeo. Isso pode levar alguns minutos..."):
        try:
            # Salva o upload temporariamente. Alguns providers/modelos aceitam
            # entrada combinada de imagem+texto; disponibilidade varia por provider.
            tmp = Path(tempfile.mkdtemp())
            img_path = tmp / imagem.name
            img_path.write_bytes(imagem.getbuffer())

            # Tenta image_to_video quando disponível no cliente/provider.
            if hasattr(client, "image_to_video"):
                video = client.image_to_video(
                    image=str(img_path),
                    prompt=prompt,
                    model=model,
                )
            else:
                st.error("Sua versão do huggingface_hub não possui image_to_video. Atualize requirements.txt.")
                st.stop()

            if isinstance(video, (bytes, bytearray)):
                data = bytes(video)
            elif hasattr(video, "read"):
                data = video.read()
            else:
                # Algumas versões retornam um caminho/objeto semelhante a arquivo.
                p = Path(str(video))
                data = p.read_bytes()

            st.success("✅ Vídeo criado!")
            st.video(data)
            st.download_button(
                "⬇️ Baixar vídeo MP4",
                data=data,
                file_name="cena_video_ia.mp4",
                mime="video/mp4",
                use_container_width=True
            )
        except Exception as e:
            st.error("Não foi possível gerar o vídeo com este modelo/provedor.")
            st.code(str(e))
            st.info("Tente outro modelo/provedor. Geração de vídeo pode exigir créditos no provedor escolhido.")
