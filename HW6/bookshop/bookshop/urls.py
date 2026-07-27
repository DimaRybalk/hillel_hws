from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns 

from books.views import books_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('silk/', include('silk.urls', namespace='silk')),
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', books_view, name='home'), 
    path('categories/', include('categories.urls')),
    path('books/', include('books.urls')), 
    path('orders/', include('order.urls')),
    path('basket/', include('basket.urls')),
    path('user/', include('user.urls')),
    path('payments/', include('payments.urls')),
    
    prefix_default_language=True 
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)