from flask import Flask, redirect, url_for, render_template
from routes import routes

app = Flask(__name__)

app.register_blueprint(routes, url_prefix="/routes")

app.secret_key = "t87y894ur940ur4rur90tu0tu"

@app.route("/home")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, port=8000)



