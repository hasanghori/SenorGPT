from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
import firebase_admin
from firebase_admin import credentials, firestore
from AI_functions import AI_Assistant
import os

cred = credentials.Certificate(os.environ.get("PATH_TO_DATABASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
#ai_assistant = AI_Assistant(api_key)
ai_assistant = AI_Assistant(os.environ.get("OPENAI_API_KEY"))

db = firestore.client()
app = Flask(__name__)

LANGUAGES_TAUGHT = ['spanish', 'urdu', 'hindi', 'arabic']
LEVELS = ['Absolute Beginner', 'Novice', 'Intermediate', 'Advanced', 'Fluent']

@app.route("/")
def index():
    """Return a friendly HTTP greeting."""
    return render_template('index.html')

#ability to send and recieve whatsapp messages
@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    from_number = request.values.get('From', None)
    incoming_msg = request.values.get('Body', '').strip()

    # Append the incoming message to the conversation history
    append_to_conversation_history(from_number, incoming_msg, 'user')


    # Check if user exists
    users_ref = db.collection('users')
    user_doc = users_ref.document(from_number).get()
    history = ''


    if not user_doc.exists:
        # New user: ask for language and level
        response_msg = ask_about_language()
        add_new_user(from_number)  # Placeholder for adding a new user to the database
    else:
        user_data = user_doc.to_dict()
        language = user_data.get('language', '')
        level = user_data.get('level', '')
        history = conversation_history_to_string(get_conversation_history(from_number))

        if not language or not level:
            extracted_lang = item_declaration(incoming_msg, LANGUAGES_TAUGHT)
            extracted_level = item_declaration(incoming_msg, LEVELS)
            if extracted_lang and extracted_level:
                lesson_plan = ai_assistant.generate_teaching_plan(incoming_msg)
                update_user_language_level(from_number, extracted_lang, extracted_level, lesson_plan)

                response_msg = ai_assistant.generate_gpt_message(history, incoming_msg, daily_plan=lesson_plan)
            else:
                response_msg = ask_about_language()
        else:
            # Language and level are set; proceed with conversation

            lesson_plan = get_lesson_plan(from_number)
            response_msg = ai_assistant.generate_gpt_message(history, incoming_msg, daily_plan=lesson_plan)

    # Append the bot's response to the conversation history
    append_to_conversation_history(from_number, response_msg, 'bot')

    resp = MessagingResponse()
    resp.message(response_msg)
    return str(resp)

# Language Parsing
def ask_about_language():
    response_msg = "Welcome! What language would you like to learn and what is your current level? These are the languages we offer: "
    for lang in LANGUAGES_TAUGHT:
        response_msg += '\n ' + lang
    response_msg += '\n and these are our levels: '
    for level  in LEVELS:
        response_msg += '\n ' + level
    response_msg += '\n also describe to me your ability in the language. (make sure to keep all of this information in one message cuz i havent made this process multiple texts yet lol)'
    return response_msg

def item_declaration(msg, arr):
    """
    Simple item to check what item a user is choosing. Mainly used for choosing level or language

    Args:
    - msg: message from user.
    - arr: a list of items a user can choose from.
    Return:
    - declaration: item that the user chose
    """
    declaration = None
    for item in arr:
        if item in msg:
            declaration = item
            break
    return declaration

# database Items
def add_new_user(from_number):
    # Add a new user to the database
    users_ref = db.collection('users')
    users_ref.document(from_number).set({
        'phone_number': from_number,
        'language': None,
        'level': None,
        'current_lesson_plan': None,
        'conversation_history': [],
        # Add more fields as necessary
    })

def update_user_language_level(from_number, language=None, level=None, lesson_plan=None):
    '''
    Adds languages to a users profile
    '''
    users_ref = db.collection('users')
    user_doc_ref = users_ref.document(from_number)
    
    update_data = {}
    if language:
        update_data['language'] = language
    if level:
        update_data['level'] = level
    if lesson_plan:
        update_data['current_lesson_plan'] = lesson_plan

    user_doc_ref.update(update_data)

def get_conversation_history(from_number):
    users_ref = db.collection('users')
    user_doc = users_ref.document(from_number).get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        conversation_history = user_data.get('conversation_history', [])
        return conversation_history
    else:
        return []

def get_lesson_plan(from_number):
    users_ref = db.collection('users')
    user_doc = users_ref.document(from_number).get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        lesson_plan = user_data.get('current_lesson_plan', '')
        return lesson_plan
    else:
        return ''

def conversation_history_to_string(conversation_history):
    """
    Converts a conversation history array into a single string.
    
    Args:
    - conversation_history: A list of message dictionaries, 
      where each dictionary contains 'sender' and 'message'.
      
    Returns:
    - A string representing the entire conversation history.
    """
    conversation_str = ""
    for message in conversation_history:
        sender = message.get('sender', 'Unknown')
        text = message.get('message', '')
        # Format each message. Adjust this formatting to your needs.
        conversation_str += f"{sender}: {text}\n"
    return conversation_str


def append_to_conversation_history(from_number, message, sender):
    """
    Appends a message to the user's conversation history.

    Args:
    - from_number: The phone number of the user.
    - message: The message text to append.
    - sender: 'user' for incoming messages, 'bot' for outgoing messages.
    """
    users_ref = db.collection('users')
    user_doc = users_ref.document(from_number)

    # Atomically add a new message to the 'conversation_history' array field.
    user_doc.update({
        'conversation_history': firestore.ArrayUnion([{'sender': sender, 'message': message}])
    })


#I need to store the full conversation somewhere, prob in a database
if __name__ == "__main__":
    app.run(debug=True)
