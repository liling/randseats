from django.conf.urls.defaults import *
import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^randseats/', include('randseats.foo.urls')),
    (r'^exam/list$', 'randseats.seats.views.list_exams'),
    (r'^exam/(?P<exam_id>\d+)/$', 'randseats.seats.views.show_exam'),
    (r'^exam_import_students/(?P<exam_id>\d+)/$', 'randseats.seats.views.exam_import_students'),
    (r'^exam_clear_students/(?P<exam_id>\d+)/$', 'randseats.seats.views.exam_clear_students'),
    (r'^exam_shuffle_students/(?P<exam_id>\d+)/$', 'randseats.seats.views.exam_shuffle_students'),
    (r'^exam_export_students_for_moodle/(?P<exam_id>\d+)/$', 'randseats.seats.views.exam_export_sutdents_for_moodle'),
    (r'^exam_show_room_students/(?P<exam_id>\d+)/(?P<room_id>\d+)/$', 'randseats.seats.views.exam_show_room_students'),
    (r'^exam_export/(?P<exam_id>\d+)/$', 'randseats.seats.views.exam_export'),

    (r'^room/(?P<room_id>\d+)/$', 'randseats.seats.views.show_room'),
    (r'^room_add_seats/(?P<room_id>\d+)/$', 'randseats.seats.views.room_add_seats'),
    (r'^room/list$', 'randseats.seats.views.list_rooms'),
    (r'^room_clear_seats/(?P<room_id>\d+)/$', 'randseats.seats.views.room_clear_seats'), 
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),

    # This is for development only
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)
