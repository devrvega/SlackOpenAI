import os
import urllib.request
import json
import bot
import boto3
from flask import Flask, request, jsonify

app = Flask(__name__)

user_chat_chains = {}
processed_messages = set()

client = boto3.client('secretsmanager')
secret_arn = os.environ['SECRET_ARN']
response = client.get_secret_value(SecretId=secret_arn)
secret_value = response['SecretString']
secret_data = json.loads(secret_value)

os.environ['BOT_TOKEN'] = secret_data['BOT_TOKEN']

SLACK_URL = "https://slack.com/api/chat.postMessage"

def send_text_response(channel_id, user, response_text):
    data = urllib.parse.urlencode({
        "token": os.environ['BOT_TOKEN'],
        "channel": channel_id,
        "text": response_text,
        "user": user,
        "link_names": True,

    })
    data = data.encode("ascii")
    request_ = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request_.add_header("Content-Type", "application/x-www-form-urlencoded")
    res = urllib.request.urlopen(request_).read()
    print('res:', res)

def check_message(text):
    if 'What is your name' in text:
        bot.clearMemory()
        return 'My name is Roboto! How can I help you?'
    return None
    
@app.route('/', methods=['POST'])
def slack_endpoint():

    print("Received request:", request.data)

    def check_for_bot_id(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'bot_id':
                    return True
                if isinstance(value, (dict, list)):
                    if check_for_bot_id(value):
                        return True
        elif isinstance(data, list):
            for item in data:
                if check_for_bot_id(item):
                    return True
        return False

    event_data = request.json

    client_msg_id = event_data.get("event", {}).get("client_msg_id")
    if client_msg_id:
        if client_msg_id in processed_messages:
            return jsonify({
                'statusCode': 200,
                'body': 'OK - Message already processed'
            })
        processed_messages.add(client_msg_id)

    # Used for Slack challenge verification.
    # Either comment or remove the conditional below on verification is complete.

    # Begin verification

    if event_data.get("type") == "url_verification":
        challengeAnswer = event_data['challenge']
        return {
            'statusCode': 200,
            'body': challengeAnswer
        }
    
    # End verification

    event = event_data.get("event", {})
    print('event', event)

    if check_for_bot_id(request.json):
        return jsonify({
            'statusCode': 200,
            'body': 'OK - Ignored bot message'
        })

    user_id = event["user"]

    if user_id not in user_chat_chains:
        user_chat_chains[user_id] = bot.initialize_chat_chain()
    
    message_response = check_message(event["text"])
    if not message_response:
        message_response = bot.slackMessage(event["text"], user_chat_chains[user_id])

    if message_response:
        send_text_response(event["channel"], event["user"], message_response)

    return jsonify({
        'statusCode': 200,
        'body': 'OK'
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK'
    }), 200