from chatbot.agent.agent import Agent
from chatbot.agent.responsor import Responsor


def DemoBot():
    demo_bot = Agent("NAME OF bot", "PASSWORD")
    demo_bot.listen()


def ResponsorBot():
    return Responsor()
