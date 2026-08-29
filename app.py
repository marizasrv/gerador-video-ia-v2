import os, tempfile
from pathlib import Path
import streamlit as st
import fal_client
import requests

st.set_page_config(page_title="Gerador de Vídeo IA", page_icon="🎬")
st.title("🎬 Gerador de Vídeo IA")
st.write("Transforme uma imagem em vídeo com movimento usando IA.")

try:
    FAL_KEY=str(st.secrets["FAL_KEY"]).strip()
except Exception:
    st.error("FAL_KEY não encontrada. Adicione em Manage app → Settings → Secrets.")
    st.stop()

os.environ["FAL_KEY"]=FAL_KEY

imagem=st.file_uploader("1. Envie a imagem",type=["jpg","jpeg","png","webp"])
prompt=st.text_area("2. Descreva o movimento",value="The character moves naturally, blinks and looks around. Hair and clothes move softly. Gentle cinematic camera movement. Preserve the same character appearance.",height=150)
formato=st.selectbox("3. Formato",["YouTube 16:9","Vertical 9:16","Automático"])
resolucao=st.selectbox("4. Qualidade",["720p","580p","480p"])
aspect={"YouTube 16:9":"16:9","Vertical 9:16":"9:16","Automático":"auto"}

if st.button("✨ Gerar vídeo com IA",type="primary",use_container_width=True):
    if imagem is None:
        st.error("Envie uma imagem primeiro."); st.stop()
    if not prompt.strip():
        st.error("Escreva o movimento desejado."); st.stop()
    try:
        with st.spinner("Enviando a imagem..."):
            suffix=Path(imagem.name).suffix or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as tmp:
                tmp.write(imagem.getbuffer()); image_path=tmp.name
            image_url=fal_client.upload_file(image_path)

        with st.spinner("Criando o vídeo. Pode levar alguns minutos..."):
            result=fal_client.subscribe(
                "fal-ai/wan/v2.2-a14b/image-to-video/turbo",
                arguments={
                    "image_url":image_url,
                    "prompt":prompt.strip(),
                    "resolution":resolucao,
                    "aspect_ratio":aspect[formato],
                    "enable_safety_checker":True,
                    "enable_output_safety_checker":True
                },
                with_logs=True
            )
        video_url=result["video"]["url"]
        st.success("✅ Vídeo criado!")
        st.video(video_url)
        r=requests.get(video_url,timeout=120); r.raise_for_status()
        st.download_button("⬇️ Baixar vídeo MP4",r.content,"video_ia.mp4","video/mp4",use_container_width=True)
    except Exception as e:
        st.error("Não foi possível gerar o vídeo.")
        msg=str(e)
        if "401" in msg or "Unauthorized" in msg:
            st.warning("Confira sua FAL_KEY nos Secrets.")
        elif "402" in msg or "credit" in msg.lower() or "payment" in msg.lower():
            st.warning("Sua conta fal pode precisar de créditos.")
        st.code(msg)
