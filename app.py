from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Привет, мир! Я - твой первый под в Kubernetes, блять!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
