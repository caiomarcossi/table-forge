from django.contrib import admin
from django.urls import path, include

urlpatterns = [
	path('admin/', admin.site.urls),
	path("rpg/", include('rpg_frontend.urls')),
	path("rpg/", include('rpg_backend.urls')),
]
