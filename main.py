import os
import json
import bot
import boto3
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

client = boto3.client('secretsmanager')
secret_arn = os.environ['SECRET_ARN']
response = client.get_secret_value(SecretId=secret_arn)
secret_value = response['SecretString']
secret_data = json.loads(secret_value)

bot_token = secret_data['BOT_TOKEN']

app = App(token=bot_token, signing_secret=secret_data['SLACK_SIGNING_SECRET'])

user_chat_chains = {}
processed_messages = set()

def check_message(text):
    return None

# Example of a slash command

## Begin slash command
@app.command("/hello")
def hello_command(ack, body, respond):
    ack()

    user_id = body["user_id"]
    channel_id = body["channel_id"]

    respond(f"Hello, <@{user_id}>!")
## End slash command

@app.event("message")
def handle_message(body, say, message):
    user = message["user"]
    channel = message["channel"]
    text = message["text"]

    # Prevent bot from processing its own messages
    if "bot_id" in message:
        return

    client_msg_id = message.get("client_msg_id")
    if client_msg_id and client_msg_id in processed_messages:
        return

    processed_messages.add(client_msg_id)
    
    if user not in user_chat_chains:
        user_chat_chains[user] = bot.initialize_chat_chain()

    print(f"User: {user}, Channel: {channel}, Message: {text}")
    
    message_response = check_message(text)
    if not message_response:
        message_response = bot.slackMessage(text, user_chat_chains[user])

    if message_response:
        say(text=message_response, channel=channel)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "OK"
    }, 200

@flask_app.route("/", methods=["POST"])
def slack_events():
    return handler.handle(request)