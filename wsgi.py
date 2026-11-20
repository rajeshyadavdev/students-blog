import os

from blog import create_app
from blog.config import DevConfig, ProdConfig

env = os.environ.get("FLASK_ENV", "production").lower()
config_class = DevConfig if env == "development" else ProdConfig

app = create_app(config_class)