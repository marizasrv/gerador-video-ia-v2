import os, tempfile
from pathlib import Path
import streamlit as st
import fal_client
import requests

st.set_page_config(page_title="Gerador de Vídeo IA", page_icon="🎬")
st.title("🎬 Gerador de Vídeo IA")
st.write("Imagem → vídeo com diagnóstico de cada etapa.")

try:
    FAL_KEY=str(st.secrets["FAL_KEY"]).strip()
except Exception:
    st.error("FAL_KEY não encontrada em Manage app → Settings → Secrets.")
    st.stop()

os.environ["FAL_KEY"]=FAL_KEY

imagem=st.file_uploader("1. Envie a imagem", type=["jpg","jpeg","png","webp"])
prompt=st.text_area(
    "2. Descreva o movimento",
    value="The character moves naturally and gently, blinks and looks around. Hair and clothes move softly. Gentle cinematic camera movement. Preserve the same character appearance.",
    height=150
)
formato=st.selectbox("3. Formato",["YouTube 16:9","Vertical 9:16","Automático"])
resolucao=st.selectbox("4. Qualidade",["480p","580p","720p"], index=0)
aspect={"YouTube 16:9":"16:9","Vertical 9:16":"9:16","Automático":"auto"}

if st.button("✨ Gerar vídeo com IA",type="primary",use_container_width=True):
    if imagem is None:
        st.error("Envie uma imagem primeiro."); st.stop()

    # ETAPA 1
    st.info("Etapa 1/3 — enviando a imagem para a fal.ai...")
    try:
        suffix=Path(imagem.name).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as tmp:
            tmp.write(imagem.getbuffer())
            image_path=tmp.name
        image_url=fal_client.upload_file(image_path)
        st.success("✅ Etapa 1 concluída: imagem enviada.")
    except Exception as e:
        st.error("❌ O erro aconteceu na ETAPA 1: upload da imagem.")
        st.code(str(e))
        st.stop()

    # ETAPA 2
    st.info("Etapa 2/3 — solicitando a geração do vídeo...")
    try:
        result=fal_client.subscribe(
            "fal-ai/wan/v2.2-a14b/image-to-video/turbo",
            arguments={
                "image_url":image_url,
                "prompt":prompt.strip(),
                "resolution":resolucao,
                "aspect_ratio":aspect[formato],
                "enable_safety_checker":True,
                "enable_output_safety_checker":True,
            },
            with_logs=True,
        )
        video_url=result["video"]["url"]
        st.success("✅ Etapa 2 concluída: vídeo gerado.")
        st.video(video_url)
    except Exception as e:
        st.error("❌ O erro aconteceu na ETAPA 2: geração do vídeo.")
        st.code(str(e))
        st.stop()

    # ETAPA 3
    st.info("Etapa 3/3 — preparando o MP4...")
    try:
        r=requests.get(video_url,timeout=120)
        r.raise_for_status()
        st.success("✅ Tudo pronto!")
        st.download_button(
            "⬇️ Baixar vídeo MP4",
            data=r.content,
            file_name="video_ia.mp4",
            mime="video/mp4",
            use_container_width=True
        )
    except Exception as e:
        st.error("❌ O vídeo foi gerado, mas houve erro ao preparar o download.")
        st.code(str(e))
