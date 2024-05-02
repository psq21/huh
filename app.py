from huh import app
import os

HOST = os.getenv('HUH_HOST') or '0.0.0.0'
PORT = int(os.getenv('HUH_PORT') or 5000)

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
