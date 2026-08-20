"""Quiz URL routes."""

from rest_framework.routers import DefaultRouter

from quizzes.api.views import QuizViewSet

router = DefaultRouter()
router.register("quizzes", QuizViewSet, basename="quiz")

urlpatterns = router.urls
