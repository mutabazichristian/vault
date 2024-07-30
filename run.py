from flaskr import create_app
import os
import logging

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    logging.info(f"Running on port {port}")
    app.run(port=port)
