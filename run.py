import os

from blog import create_app
from blog.config import DevConfig, ProdConfig, TestConfig

if os.environ.get("WORK_ENV") == "PROD":
    config = ProdConfig()
elif os.environ.get("WORK_ENV") == "TEST":
    config = TestConfig()
else:
    config = DevConfig()

app = create_app(config)

if __name__ == "__main__":
    app.run()
