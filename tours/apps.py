from django.apps import AppConfig


class ToursConfig(AppConfig):
    name = "tours"

    def ready(self):
        import tours.signals.handlers  # noqa
