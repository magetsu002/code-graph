from django.urls import path
from views import direct_view, generated_view


def build_extra_routes():
    return [
        path("generated/", generated_view, name="generated"),
    ]


urlpatterns = [
    path("direct/", direct_view, name="direct"),
]
urlpatterns += build_extra_routes()
