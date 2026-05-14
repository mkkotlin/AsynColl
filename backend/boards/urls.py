from rest_framework.routers import  DefaultRouter
from boards.views import BoardViewSet, CardViewSet, ListViewSet, UserViewSet

router = DefaultRouter()
router.register(r'boards', BoardViewSet)
router.register(r'lists', ListViewSet)
router.register(r'cards', CardViewSet)
router.register(r'users', UserViewSet)

urlpatterns = router.urls