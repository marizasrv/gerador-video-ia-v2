import os
import base64
import mimetypes
import streamlit as st
import fal_client
import requests

st.set_page_config(page_title="Gerador de Vídeo IA", page_icon="🎬", layout="centered")
st.title("🎬 Gerador de Vídeo IA — V5")
st.write("Transforme sua imagem em vídeo com IA, sem usar o upload separado da fal.ai.")

try:
    FAL_KEY = str(st.secrets["FAL_KEY"]).strip()
except Exception:
    st.error("FAL_KEY não encontrada. Adicione em Manage app → Settings → Secrets.")
    st.stop()

os.environ["FAL_KEY"] = FAL_KEY

imagem = st.file_uploader("1. Envie a imagem", type=["jpg", "jpeg", "png", "webp"])
prompt = st.text_area(
    "2. Descreva o movimento",
    value=(
        "The character moves naturally and gently, blinks and looks around. "
        "Hair and clothes move softly. Gentle cinematic camera movement. "
        "Preserve the same character appearance."
    ),
    height=150,
)
formato = st.selectbox("3. Formato", ["YouTube 16:9", "Vertical 9:16", "Automático"])
resolucao = st.selectbox("4. Qualidade", ["480p", "580p", "720p"], index=0)

aspect = {
    "YouTube 16:9": "16:9",
    "Vertical 9:16": "9:16",
    "Automático": "auto",
}

def imagem_para_data_uri(uploaded):
    raw = uploaded.getvalue()
    mime = uploaded.type or mimetypes.guess_type(uploaded.name)[0] or "image/jpeg"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"

if st.button("✨ Gerar vídeo com IA", type="primary", use_container_width=True):
    if imagem is None:
        st.error("Envie uma imagem primeiro.")
        st.stop()
    if not prompt.strip():
        st.error("Escreva o movimento desejado.")
        st.stop()

    st.info("Etapa 1/2 — preparando a imagem dentro do próprio app...")
    try:
        image_data_uri = imagem_para_data_uri(imagem)
        st.success("✅ Imagem preparada sem usar o storage da fal.ai.")
    except Exception as e:
        st.error("❌ Erro ao preparar a imagem.")
        st.code(str(e))
        st.stop()

    st.info("Etapa 2/2 — enviando a imagem diretamente para o modelo de vídeo...")
    try:
        result = fal_client.subscribe(
            "fal-ai/wan/v2.2-a14b/image-to-video/turbo",
            arguments={
                "image_url": image_data_uri,
                "prompt": prompt.strip(),
                "resolution": resolucao,
                "aspect_ratio": aspect[formato],
                "enable_safety_checker": True,
                "enable_output_safety_checker": True,
                "enable_prompt_expansion": False,
                "acceleration": "regular",
                "video_quality": "high",
                "video_write_mode": "balanced",
            },
            with_logs=True,
        )

        video_url = result["video"]["url"]
        st.success("✅ Vídeo criado!")
        st.video(video_url)

        try:
            response = requests.get(video_url, timeout=180)
            response.raise_for_status()
            st.download_button(
                "⬇️ Baixar vídeo MP4",
                data=response.content,
                file_name="video_ia.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        except Exception:
            st.info("O vídeo foi criado. Se o botão de download não aparecer, use o player acima.")

    except Exception as e:
        st.error("❌ A fal.ai recusou ou não conseguiu processar a geração.")
        msg = str(e)
        if "401" in msg:
            st.warning("Confira a FAL_KEY nos Secrets.")
        elif "403" in msg:
            st.warning("Agora o 403 ocorreu na chamada do modelo, não no upload da imagem.")
        elif "402" in msg or "credit" in msg.lower() or "payment" in msg.lower():
            st.warning("A conta pode precisar de créditos para usar este modelo.")
        st.code(msg)
