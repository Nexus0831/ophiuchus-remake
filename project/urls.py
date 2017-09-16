from django.conf.urls import url, include
from . import views
from django.contrib.auth.views import login, logout


urlpatterns = [
    url(r'^login/$', login,{'template_name': 'login.html'},name='login'),
    url(r'^logout/$', logout,{'template_name': 'logout.html'}, name='logout'),
    url(r'', include('social_django.urls', namespace='social')),
    url(r'^user/profile/(?P<user>.+)/$', views.profile_detail, name='profile_detail'),
    url(r'^user/invitation$', views.invitation_list, name='Message'),

    url(r'^$', views.project_list, name='project_list'),
    url(r'^project/(?P<pk>[0-9]+)/$', views.project_detail, name='project_detail'),
    url(r'^project/del/(?P<pk>[0-9]+)/$', views.project_delete, name='project_delete'),
    url(r'^project/complete/(?P<pk>[0-9]+)/$', views.project_complete, name='project_complete'),

    url(r'^process/complete/(?P<pk>[0-9]+)/$', views.process_complete, name='process_complete'),
    url(r'^process/del/(?P<pk>[0-9]+)/$', views.process_delete, name='process_delete'),

    url(r'^lounge/$', views.lounge, name='lounge')
]