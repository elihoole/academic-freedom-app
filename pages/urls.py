from django.urls import path
from .views import (
    HomePageView,
    AboutPageView,
    JudgementListView,
)

urlpatterns = [
    path(
        "academic_freedom_judgements/",
        JudgementListView.as_view(),
        name="academic_freedom_judgements",
    ),
    path("about/", AboutPageView.as_view(), name="about"),
    path("", HomePageView.as_view(), name="home"),
    # path("search_form/", search_form),
    # path("judgements_search/", judgements_search, name="judgements_search"),
]
