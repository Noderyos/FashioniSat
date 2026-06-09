from flask_login import LoginManager, UserMixin

login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, id):
        self.id = id
