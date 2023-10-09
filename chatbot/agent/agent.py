from speakeasypy import Speakeasy, Chatroom
from typing import List
import time


DEFAULT_HOST_URL = 'https://speakeasy.ifi.uzh.ch'
listen_freq = 2


class Agent:
    def __init__(self, username, password, graph):
        self.username = username
        self.graph = graph
        # Initialize the Speakeasy Python framework and login.
        self.speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=username, password=password)
        self.speakeasy.login()  # This framework will help you log out automatically when the program terminates.


    def listen(self):
        while True:
            # only check active chatrooms (i.e., remaining_time > 0) if active=True.
            rooms: List[Chatroom] = self.speakeasy.get_rooms(active=True)
            for room in rooms:
                if not room.initiated:
                    # send a welcome message if room is not initiated
                    room.post_messages(f'Hello! This is a welcome message from {room.my_alias}.')
                    room.initiated = True
                # Retrieve messages from this chat room.
                # If only_partner=True, it filters out messages sent by the current bot.
                # If only_new=True, it filters out messages that have already been marked as processed.
                for message in room.get_messages(only_partner=True, only_new=True):
                    print(
                        f"\t- Chatroom {room.room_id} "
                        f"- new message #{message.ordinal}: '{message.message}' "
                        f"- {self.get_time()}")

                    # Implement your agent here #
                    # TODO: move implementation to a separate class
                    def convert_html_to_string(message):
                        if not isinstance(message, str):
                            return message.to_string()
                        else:
                            return message
                    
                    converted_message = convert_html_to_string(message.message)

                    if converted_message.startswith("PREFIX"):
                        
                        def convert_type(term):
                            d = term.datatype
                            if not d:
                                new_term = str(term)
                            elif 'integer' in d:
                                new_term = int(term)
                            else:
                                new_term = str(term)
                            return new_term
                        
                        try:
                            answer = [
                                [convert_type(t) for t in s] for s in self.graph.query(converted_message)
                            ]
                            room.post_messages(f"{answer}")
                        except:
                            room.post_messages(f"Sorry, I cannot parse your input. Please input a string.")

                    # Send a message to the corresponding chat room using the post_messages method of the room object.
                    else:
                        room.post_messages(f"Received your message: '{converted_message}' ")
                    
                    # Mark the message as processed, so it will be filtered out when retrieving new messages.
                    room.mark_as_processed(message)

                # Retrieve reactions from this chat room.
                # If only_new=True, it filters out reactions that have already been marked as processed.
                for reaction in room.get_reactions(only_new=True):
                    print(
                        f"\t- Chatroom {room.room_id} "
                        f"- new reaction #{reaction.message_ordinal}: '{reaction.type}' "
                        f"- {self.get_time()}")

                    # Implement your agent here #

                    room.post_messages(f"Received your reaction: '{reaction.type}' ")
                    room.mark_as_processed(reaction)

            time.sleep(listen_freq)

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())