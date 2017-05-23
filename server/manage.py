from flask_script import Manager

from myapp import app

manager = Manager(app)

@manager.command
def runserver():
    app.run()

if __name__ == "__main__":
    manager.run()
