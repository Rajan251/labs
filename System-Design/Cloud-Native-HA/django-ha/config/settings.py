import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("SECRET_KEY", "prod-insecure-key")
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'health', # Custom health check app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Database Configuration with Read Replicas
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("DB_NAME", "postgres"),
        'USER': os.environ.get("DB_USER", "postgres"),
        'HOST': os.environ.get("DB_HOST", "localhost"), # Writer
        'PORT': 5432,
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("DB_NAME", "postgres"),
        'USER': os.environ.get("DB_USER", "postgres"),
        'HOST': os.environ.get("DB_RO_HOST", "localhost"), # Reader
        'PORT': 5432,
    }
}

DATABASE_ROUTERS = ['config.routers.PrimaryReplicaRouter']

# Cache Configuration (High Availability)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Connection pooling is built-in
            "SOCKET_CONNECT_TIMEOUT": 5, 
            "SOCKET_TIMEOUT": 5,
        }
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
