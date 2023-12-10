from flask import Flask
from chatbot import cache, chatbot
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


app = Flask("chatbot")
cache.init_app(app)

# chatbot.DemoBot()

responsor_bot = chatbot.ResponsorBot()
while True:
    print('Enter your question:')
    message_text = input()
    answer = responsor_bot.response(message_text)
    print(answer)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)