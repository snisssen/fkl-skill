from importlib.metadata import requires
from wsgiref.validate import validator

from pkg_resources import safe_extra
from mycroft import MycroftSkill, intent_handler
from adapt.intent import IntentBuilder
from mycroft.util.format import join_list
from os.path import dirname, join
from lingua_franca.parse import fuzzy_match

import sys
from os.path import dirname, abspath
sys.path.append(dirname(abspath(__file__)))
from cardDatabase import Database


class flashCardLearning(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.db = Database()
        self.reload_skill = False

    @intent_handler(IntentBuilder('read')
        .require('what')
        .require('topic')
        .optionally('topic_name'))
    def handle_read(self, message):
        data = {'topic_name': message.data.get('topic_name')}

        # If the user specified a topic, read the cards on that topic
        if data['topic_name']:
            # Check that the topic exists
            if not self.db.topic_exists(data['topic_name']):
                self.speak_dialog('topic.not.found', data)

            # Check that the topic is not empty
            elif self.db.topic_empty(data['topic_name']):
                self.speak_dialog('no.cards', data)

            else:
                data['cards'] = join_list(
                    self.db.read_cards(data['topic_name']),
                    self.translate('and'), lang=self.lang)
                self.speak_dialog('read.cards', data)

        # Alternatively, simply read topics names
        else:
            # Check if there are topics at all
            if self.db.no_topics():
                self.speak_dialog('no.topics')

            else:
                topics = self.db.read_topics()
                data['topics_names'] = join_list(topics, self.translate('and'),
                                                lang=self.lang)
                data['topic'] = self.plural_singular_form(topics)
                self.speak_dialog('read.topics', data)

    @intent_handler(IntentBuilder('add')
        .require('add')
        .require('topic')
        .require('topic_name')
        .optionally('card_name'))
    def handle_add(self, message):
        data = {'topic_name': message.data.get('topic_name'),
                'card_name': message.data.get('card_name')}

        # If the user specified an card, add it to a topic
        if data['card_name']:
            # Check if the topic exists
            if not self.db.topic_exists(data['topic_name']):
                self.speak_dialog('topic.not.found', data)

            else:
                if self.db.card_exists(data['topic_name'], data['card_name']):
                    self.speak_dialog('card.already.exists', data)
                else:
                    self.db.add_card(data['topic_name'], data['card_name'])
                    self.speak_dialog('add.card', data)

        # Alternatively, simply add a new topic
        else:
            # Check if the topic exists (we don't want to overwrite it)
            if self.db.topic_exists(data['topic_name']):
                self.speak_dialog('topic.found', data)

            else:
                self.db.add_topic(data['topic_name'])
                self.speak_dialog('add.topic', data)

    @intent_handler(IntentBuilder('del')
        .optionally('card_name')
        .require('del')
        .require('topic')
        .require('topic_name'))
    def handle_del(self, message):
        data = {'topic_name': message.data.get('topic_name'),
                'card_name': message.data.get('card_name')}

        # If the user specified a question, delete it from the topic
        if data['card_name']:
            mycard = None
            if self.db.topic_exists(data['topic_name']):
                # Check that the question exist
                cards = self.db.read_cards(data['topic_name'])
                for card in cards:
                    if card['question'] == data['card_name']:
                        mycard = card
                        break

                if mycard == None:
                    self.speak_dialog('card.not.found', data)
                else:
                    if self.confirm_deletion(data['card_name']):
                        self.db.del_card(data['topic_name'],mycard)
                        self.speak_dialog('del.card', data)
            else:
                self.speak_dialog('topic.not.found')

        # Alternatively, simply delete the topic
        else:
            # Check that the topic exists
            if not self.db.topic_exists(data['topic_name']):
                self.speak_dialog('topic.not.found', data)

            else:
                if self.confirm_deletion(data['topic_name']):
                    self.db.del_topic(data['topic_name'])
                    self.speak_dialog('del.topic', data)

    def plural_singular_form(self, topics):
        """ Return singular or plural form as necessary """

        value = self.translate_namedvalues('topic.or.topics', delim=',')
        return value.get('singular') if len(topics) == 1 else value.get('plural')

    def confirm_deletion(self, element):
        """ Make sure the user really wants to delete 'element' """

        resp = self.ask_yesno('confirm.deletion', data={'element': element})
        if resp == 'yes':
            return True
        else:
            self.speak_dialog('cancelled')
        return False

    @intent_handler(IntentBuilder('newcard')
        .require('newCard')
        .optionally('topic_name'))
    def handle_newcard(self,message):
        data = {'topic_name': message.data.get('topic_name')}
        
        #check if user specified topic, else ask for topic
        if not data['topic_name']:
            topic = self.get_response('what.topic') 
        else:
            topic = data['topic_name']
        self.log.info(type(topic))

        #check if topic exists
        if not self.db.topic_exists(topic):
            self.speak_dialog('topic.not.found', topic)

        else:

            #asks for question
            question = self.get_response('define.question')

            #asks for correct answer
            answer = self.get_response('define.answer')

            #save card
            myNewCard = {
                'question': question,
                'answer': answer,
                'correctGuesses': 0
            }
            self.db.add_card(topic, myNewCard)
            self.speak_dialog('add.card')

    @intent_handler(IntentBuilder('practiseCards')
        .require('practise')
        .optionally('badCards')
        .optionally('topic_name'))
    def handle_practiceCards(self,message):
        data = {'topic_name': message.data.get('topic_name'),
                'bad': (message.data.get('badCards') != None )}

        #check if user only wants to practise bad cards
        if data['bad']:
            maxCorG = 3
        else:
            maxCorG = 5
        #check if user specified topic
        specifiedTopic = True
        if data['topic_name']:
            topic = data['topic_name']
        else:
            resp = self.ask_yesno('special.topic')
            if resp == 'no':
                specifiedTopic = False
            else:
                topic = self.get_response('what.topic.practise')
        
        #check if specified topic exists
        if specifiedTopic:
            if not self.db.topic_exists(topic):
                self.speak_dialog('topic.not.found')
             
        #check that the topic is not empty
            elif self.db.topic_empty(topic):            
                self.speak_dialog('no.cards', topic)
            else:
            #start practising topic
                testList = self.db.read_cards(topic)
                correctQuestions = 0
                numQuestions = 0 #Number of questions asked
                for card in testList:
                    if card['correctGuesses'] < maxCorG:
                        #correctAnswer = Boolean, if question was answerd correctly
                        goOn, correctAnswer = self.practise(card, topic)
                        if not goOn:
                            break
                        numQuestions += 1
                        if correctAnswer:
                            correctQuestions += 1
                self.practiseFinished(correctQuestions, numQuestions)

        else:
            #start practising all
            topics = self.db.read_topics()
            correctQuestions = 0
            numQuestions = 0
            for topic in topics:
                testList = self.db.read_cards(topic)
                for card in testList:
                    if card['correctGuesses'] <= maxCorG:
                        goOn, correctAnswer = self.practise(card, topic)
                        if not goOn:
                            break
                        numQuestions += 1
                        if correctAnswer:
                            correctQuestions += 1
                if not goOn:
                    break

            self.practiseFinished(correctQuestions, numQuestions)

    def practise(self, card, topic):
        correctAnswer = False
        answer = self.get_response(card['question'])

        if answer == 'stop':
            return (False, correctAnswer)

        tempFuzz= fuzzy_match(answer, card['answer'])            
        if tempFuzz >= 0.966:
            self.speak_dialog('correct')
            newCard = card            
            newCard['correctGuesses'] += 1
            correctAnswer = True
            self.db.guess(topic, card, newCard)
        elif tempFuzz > 0.566:
            answerData = {'answer': card['answer']}
            self.speak_dialog('not.sure')
            newCard = card
            yesno = self.ask_yesno('ask.correct', answerData)
            if  yesno == 'yes':
               newCard['correctGuesses'] += 1
               correctAnswer = True
            else:
                newCard['correctGuesses'] = 0
            self.db.guess(topic, card, newCard)
            self.speak_dialog('alright')
        else:
            answerData = {'answer': card['answer']}
            self.speak_dialog('wrong', answerData)
            newCard = card
            newCard['correctGuesses'] = 0
            self.db.guess(topic, card, newCard)

        return (True, correctAnswer)

    def practiseFinished(self, correctQuestions, numQuestions):

        if correctQuestions == 0:
            data = {'percentage': 0, 'correctQuestions': 0}
            self.speak_dialog('practice.finished.0', data)
            return

        percentage = round(100 * correctQuestions/numQuestions)
        data = {'percentage': percentage, 'correctQuestions': correctQuestions}

        #value = self.translate_namedvalues('practice.finished.1', delim=',')
        #data['card'] = value.get('singular') if correctQuestions == 1 else value.get('plural')

        if percentage == 100:
            self.speak_dialog('practise.finished.100', data)
        elif percentage > 80:
            self.speak_dialog('practice.finished.80', data)
        elif percentage > 60:
            self.speak_dialog('practice.finished.60', data)
        elif percentage > 20:
            self.speak_dialog('practice.finished.20', data)
        else:
            self.speak_dialog('practice.finished.1', data)
        return
    
    @intent_handler(IntentBuilder('test')
        .require('test'))
    def handle_test(self):
        self.practiseFinished(70, 100)

def create_skill():
    return flashCardLearning()