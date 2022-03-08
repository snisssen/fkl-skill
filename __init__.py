from mycroft import MycroftSkill, intent_file_handler


class Fkl(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('fkl.intent')
    def handle_fkl(self, message):
        self.speak_dialog('fkl')


def create_skill():
    return Fkl()

