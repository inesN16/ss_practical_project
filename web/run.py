from app import app


if __name__ == "__main__":
    app = app.create_app()
    #app.run(host="0.0.0.0", port=8000, debug=True)
    #---adicionei---
    #app.run(host="127.0.0.1", port=8000, debug=True)
    app.run(host="0.0.0.0", port=8000, debug=True)
