import os
import importlib
from pathlib import Path

try:
    decouple_module = importlib.import_module('decouple')
    decouple_config = getattr(decouple_module, 'config', None)
except Exception:
    decouple_config = None

BASE_DIR = Path(__file__).resolve().parent.parent


def carregar_arquivo_env(caminho):
    if not caminho.exists():
        return

    for linha in caminho.read_text(encoding='utf-8').splitlines():
        conteudo = linha.strip()
        if not conteudo or conteudo.startswith('#') or '=' not in conteudo:
            continue
        chave, valor = conteudo.split('=', 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave, valor)


carregar_arquivo_env(BASE_DIR / '.env')
carregar_arquivo_env(BASE_DIR.parent / '.env')


def config(chave, default=None, cast=str):
    if decouple_config is not None:
        try:
            return decouple_config(chave, default=default, cast=cast)
        except Exception:
            pass

    valor = os.getenv(chave, default)
    if cast is bool:
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() in {'1', 'true', 'yes', 'on'}

    if valor is None:
        return None

    try:
        return cast(valor)
    except Exception:
        return valor

SECRET_KEY = config('SECRET_KEY', default='troque_esta_chave_em_producao')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [origem.strip() for origem in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if origem.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'aplicacoes.autenticacao',
    'aplicacoes.usuarios',
    'aplicacoes.pacientes',
    'aplicacoes.triagens',
    'aplicacoes.encaminhamentos',
    'aplicacoes.sintomas',
    'aplicacoes.classificacao_risco',
    'aplicacoes.chat_ia',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'aplicacoes.chat_ia.middleware.TempoRespostaChatIAMiddleware',
]

ROOT_URLCONF = 'configuracao.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'configuracao.wsgi.application'
ASGI_APPLICATION = 'configuracao.asgi.application'

db_engine = config('DB_ENGINE', default='django.db.backends.postgresql')

if db_engine == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': config('DB_NAME', default='triagem_medica'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5433'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'estaticos/'
STATICFILES_DIRS = [BASE_DIR / 'estaticos']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'midia/'
MEDIA_ROOT = BASE_DIR / 'midia'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True

OLLAMA_URL = config('OLLAMA_URL', default='http://localhost:11434')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3.1:8b')
OLLAMA_TIMEOUT_SECONDS = config('OLLAMA_TIMEOUT_SECONDS', default=45, cast=int)
OLLAMA_MAX_HISTORY_MESSAGES = config('OLLAMA_MAX_HISTORY_MESSAGES', default=3, cast=int)
OLLAMA_MAX_INPUT_CHARS = config('OLLAMA_MAX_INPUT_CHARS', default=700, cast=int)
OLLAMA_NUM_PREDICT = config('OLLAMA_NUM_PREDICT', default=180, cast=int)
OLLAMA_NUM_CTX = config('OLLAMA_NUM_CTX', default=1024, cast=int)
OLLAMA_TEMPERATURE = config('OLLAMA_TEMPERATURE', default=0.1, cast=float)

OLLAMA_NUM_PREDICT_FAST = config('OLLAMA_NUM_PREDICT_FAST', default=140, cast=int)
OLLAMA_RETRY_ATTEMPTS = config('OLLAMA_RETRY_ATTEMPTS', default=2, cast=int)
OLLAMA_RETRY_BACKOFF_SECONDS = config('OLLAMA_RETRY_BACKOFF_SECONDS', default=0.4, cast=float)
OLLAMA_KEEP_ALIVE = config('OLLAMA_KEEP_ALIVE', default='10m')
CHAT_IA_SLOW_REQUEST_MS = config('CHAT_IA_SLOW_REQUEST_MS', default=12000, cast=int)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'aplicacoes.chat_ia': {
            'handlers': ['console'],
            'level': config('CHAT_IA_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}


CHAT_IA_MODO_RAPIDO_LOCAL = config('CHAT_IA_MODO_RAPIDO_LOCAL', default=True, cast=bool)



