from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # импорт сигналов, если используете синхронизацию с Supabase
        try:
            import api.signals  # noqa
        except Exception:
            pass
