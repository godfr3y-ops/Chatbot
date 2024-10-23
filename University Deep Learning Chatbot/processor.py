import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import numpy as np
from keras.models import load_model
import json
import random
import logging
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a constant for the error threshold
ERROR_THRESHOLD = 0.50

# Load the pre-trained model and data
try:
    model = load_model('chatbot_model.h5')
    words = pickle.load(open('words.pkl', 'rb'))
    classes = pickle.load(open('classes.pkl', 'rb'))
    intents = json.loads(open('job_intents.json', encoding='utf-8').read())
except Exception as e:
    logger.error(f"Failed to load model or data: {str(e)}")
    exit(1)

# Define a function for cleaning up sentences
def clean_up_sentence(sentence):
    lemmatizer = WordNetLemmatizer()
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# Define a function for generating a bag of words array
def bow(sentence, words, show_details=False):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    logger.info(f"Found in bag: {w}")
    return np.array(bag)

# Define a function for predicting the class of a sentence
def predict_class(sentence, model):
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    if not return_list:  # Add this check
        return_list.append({"intent": "unknown", "probability": "0.0"})
    return return_list

# Define a function for getting a response based on the predicted intent
def get_response(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
        else:
            result = "Sorry, I don't have information on that topic. Please try rephrasing your question."
    return result

# Define the main chatbot response function
def chatbot_response(msg):
    try:
        ints = predict_class(msg, model)
        res = get_response(ints, intents)
        return res
    except Exception as e:
        logger.error(f"Failed to generate response: {str(e)}")
        return "Sorry, an error occurred. Please try again."

# Handle out-of-vocabulary words
def handle_oov(words, intents_json):
    oov_words = []
    for intent in intents_json['intents']:
        for pattern in intent['patterns']:
            words_in_pattern = clean_up_sentence(pattern)
            for word in words_in_pattern:
                if word not in words:
                    oov_words.append(word)
    return oov_words

# Implement context awareness
context = {}
def chatbot_response_with_context(msg):
    global context
    try:
        ints = predict_class(msg, model)
        res = get_response(ints, intents)
        if 'context' in ints[0]:
            context = ints[0]['context']
        return res
    except Exception as e:
        logger.error(f"Failed to generate response with context: {str(e)}")
        return "Sorry, an error occurred. Please try again."

# Handle out-of-vocabulary words
oov_words = handle_oov(words, intents)
logger.info("Out-of-vocabulary words: {}".format(oov_words))

# Add tests
def test_chatbot_response():
    assert chatbot_response("Hello") != ""
    assert chatbot_response("This is a test") != ""
    assert chatbot_response("unknown") == "Sorry, I don't have information on that topic. Please try rephrasing your question."

test_chatbot_response()