import os
import boto3
import json

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.retrievers import AmazonKendraRetriever

client = boto3.client('secretsmanager')
secret_arn = os.environ['SECRET_ARN']
response = client.get_secret_value(SecretId=secret_arn)
secret_value = response['SecretString']
secret_data = json.loads(secret_value)

# Load the OpenAI API key from the .env file
os.environ['OPENAI_API_KEY'] = secret_data['OPENAI_API_KEY']
os.environ['KENDRA_INDEX'] = secret_data['KENDRA_INDEX']

# Instantiate the chat model
chatModel = ChatOpenAI(
    model = "gpt-3.5-turbo-16k",
    temperature = 0.9,
)

kendraRetriever = AmazonKendraRetriever(
    index_id = os.environ['KENDRA_INDEX'],
    region_name = "us-east-1",
)

# Set the template for the chat prompt
chatTemplate = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(
            """
            You are an AI assistant that helps people find information. Your name is Roboto.
            You are only allowed to speak English. If anyone asks you to speak another language, you must apologize and say "I only speak English".
            You may not speak any other language at any given time.

            You are very friendly.
            You are very helpful.
            You are very knowledgeable.
            You explain things in a way that is easy to understand.
            You are not to be vulgar or rude at any time.
            
            {context}
            Instruction: 
            Based on documents, answer the question. If you don't know the answer for {question}, reply with "According to my knowledge outside of the documentations" and suggest an answer based on other knowledge.
            If they are being conversational, just respond as close to a human would respond.
            """
        ),
        HumanMessagePromptTemplate.from_template(
            "{question}"
        ),
    ]
)

# Instantiate the memory
chatMemory = ConversationBufferMemory(
    memory_key = "chat_history",
    return_messages = True,
)

def clearMemory():
    chatMemory.clear()
    return 'Memory cleared'

# Instantiate the chain
def initialize_chat_chain():
    chatChain = ConversationalRetrievalChain.from_llm(
        llm = chatModel,
        retriever = kendraRetriever,
        memory = chatMemory,
        combine_docs_chain_kwargs = {"prompt": chatTemplate},
        verbose = False,
    )
    return chatChain

# Begin the chat

chatChain = initialize_chat_chain()

def slackMessage(text, chat_chain):
    response = chatChain({"question": text})['answer']
    return response