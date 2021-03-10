from flask import Flask, render_template
from forms.message_form import MessageForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route('/send', methods=['POST', 'GET'])
def send():
    form = MessageForm()
    if form.validate_on_submit():
        pass
    return render_template('send.html', form=form)


if __name__ == '__main__':
    app.run('127.0.0.1', 8080, debug=True)
