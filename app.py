import base64
import asyncio
import time
import io
import edge_tts
from PIL import Image
from flask import Flask, request, send_file, Response
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def resize_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((800, 800))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()

def text_to_speech(text):
    async def _tts():
        tts = edge_tts.Communicate(text, voice="th-TH-NiwatNeural", rate="-20%")
        await tts.save("/tmp/output.mp3")
    asyncio.run(_tts())

@app.route("/analyze", methods=["POST"])
def analyze():
    image_bytes = resize_image(request.data)
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt_encoded = request.headers.get("X-Prompt", "")
    prompt = base64.b64decode(prompt_encoded).decode() if prompt_encoded else "อธิบายภาพสั้นๆ 1 ประโยค"

    t1 = time.time()
    response = client.responses.create(
        model="gpt-4.1-nano",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"}
            ]
        }]
    )
    print(f"AI: {time.time()-t1:.1f}s")

    result = response.output_text
    print("Result:", result)

    text_to_speech(result)
    return send_file("/tmp/output.mp3", mimetype="audio/mpeg")

@app.route("/tts", methods=["GET"])
def tts():
    text = request.args.get("text", "")
    if not text:
        return "no text", 400

    async def _tts():
        tts = edge_tts.Communicate(text, voice="th-TH-NiwatNeural", rate="-20%")
        await tts.save("/tmp/tts.mp3")
    asyncio.run(_tts())

    return send_file("/tmp/tts.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)