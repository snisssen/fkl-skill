import json
from os.path import dirname, join

class Database:
    """
    This module manages the data.json file where cards and topics 
    are stored.

    Sections:
        File handling   take care of read / write operations
        Checks          methods to assert specific conditions
        Read            methods to read from data.json
        Add             methods to write to data.json
        Del             methods to remove data from data.json
        Guess           method to actualize the number of correct guesses
    """

    def __init__(self):
        self.CARD_JSON_PATH = join(dirname(__file__), 'data.json')
        try:
            # Load topic data from data.json
            self.json_data = self.read_data()
        except FileNotFoundError:
            # If file not found, create an empty data.json
            self.json_data = {}
            self.write_data()

    ## FILE HANDLING
    def read_data(self):
        with open(self.CARD_JSON_PATH, 'r') as json_file:
            return json.load(json_file)

    def write_data(self):
        with open(self.CARD_JSON_PATH, 'w') as json_file:
            json.dump(self.json_data, json_file)

    ## CHECKS
    def card_exists(self, topic, card):
        return True if card in self.json_data[topic] else False

    def no_topics(self):
        return True if len(list(self.json_data.keys())) == 0 else False

    def topic_empty(self, topic):
        return True if len(self.json_data.get(topic)) == 0 else False

    def topic_exists(self, topic):
        return True if topic in self.json_data.keys() else False

    ## READ
    def read_cards(self, topic):
        return self.json_data.get(topic)

    def read_topics(self):
        return list(self.json_data.keys())

    ## ADD
    def add_card(self, topic, card):
        self.json_data[topic].append(card)
        self.write_data()

    def add_topic(self, topic):
        self.json_data[topic] = []
        self.write_data()

    ## DEL
    def del_card(self, topic, card):
        card_index = self.json_data[topic].index(card)
        del self.json_data[topic][card_index]
        self.write_data()

    def del_topic(self, topic):
        del self.json_data[topic]
        self.write_data()

    ## GUESS
    def guess(self, topic, card, newCard):
        card_index = self.json_data[topic].index(card)
        self.json_data[topic][card_index] = newCard
        self.write_data()




