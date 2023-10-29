from chatbot.agent.agent import Agent
from chatbot.agent.responsor import Responsor


def DemoBot():
    demo_bot = Agent("torch-staccato-mushroom_bot", "ofmkiY2qPQeiRg")
    demo_bot.listen()


def ResponsorBot():
    return Responsor()
