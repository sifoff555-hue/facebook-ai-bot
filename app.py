import os
import requests
from flask import Flask, request

from openai import OpenAI

app = Flask(__name__)

# المفاتيح نضيفوها لاحقًا في الاستضافة، ماشي هنا
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


@app.route("/", methods=["GET"])
def home():
    return "Facebook AI Bot is running!"


# Facebook يستعمل هذا الرابط للتأكد من الـ Webhook
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


# استقبال رسائل Messenger
@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()

    if not data:
        return "NO DATA", 200

    if data.get("object") != "page":
        return "NOT A PAGE EVENT", 200

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):

            sender = event.get("sender", {})
            sender_id = sender.get("id")

            message = event.get("message", {})
            text = message.get("text")

            # إذا كانت الرسالة نصية
            if sender_id and text:

                try:
                    # إرسال سؤال الشخص إلى الذكاء الاصطناعي
                    response = client.responses.create(
                        model="gpt-6-luna",
                        instructions=(
                            "أنت مساعد ذكي لصفحة فيسبوك. "
                            "أجب على أسئلة المستخدمين بطريقة واضحة ومفيدة. "
                            "يمكنك الرد بالعربية أو الدارجة الجزائرية حسب لغة المستخدم."
                        ),
                        input=text
                    )

                    answer = response.output_text

                except Exception as e:
                    print("OpenAI Error:", e)
                    answer = "سمحلي، صرات مشكلة مؤقتة. عاود ابعثلي رسالتك."

                # إرسال جواب الذكاء الاصطناعي إلى Messenger
                send_message(sender_id, answer)

    return "EVENT_RECEIVED", 200


def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v24.0/me/messages"

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }

    payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }

    try:
        response = requests.post(
            url,
            params=params,
            json=payload,
            timeout=20
        )

        print("Facebook response:", response.status_code)
        print(response.text)

    except Exception as e:
        print("Facebook Error:", e)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
          )
