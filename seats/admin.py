#*-* encoding: UTF-8 *-*
from django.contrib import admin
from randseats.seats.models import *
from datetime import datetime

class ExamRoomUsageInline(admin.TabularInline):
    model = ExamRoomUsage

class RoomRangeInline(admin.TabularInline):
    model = RoomRange

class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'starttime', 'endtime')
    inlines = ( ExamRoomUsageInline, )

class PaperAdmin(admin.ModelAdmin):
    list_display = ('exam', 'inuse', 'name', 'identifier')
    list_filter = ('exam', )

class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'nick', 'seatscount', 'width', 'height')
    inlines = ( RoomRangeInline, )

def roomseat_make_useable(modeladmin, request, queryset):
    queryset.update(useable = True)
roomseat_make_useable.short_description = u'标记为可用'

def roomseat_make_unuseable(modeladmin, request, queryset):
    queryset.update(useable = False)
roomseat_make_unuseable.short_description = u'标记为不可用'

class RoomSeatAdmin(admin.ModelAdmin):
    list_display = ('room', 'num', 'x', 'y', 'useable', 'range')
    list_filter = ('room', 'useable')
    ordering = ['num']
    actions = [roomseat_make_useable, roomseat_make_unuseable]

class StudentAdmin(admin.ModelAdmin):
    list_display = ('exam', 'idnumber', 'name', 'classnum', 'room', 'seat', 'paper')
    list_filter = ('exam', 'room', 'paper')
    search_fields = ('idnumber', 'name')

admin.site.register(Exam, ExamAdmin)
admin.site.register(Paper, PaperAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(RoomSeat, RoomSeatAdmin)
admin.site.register(Student, StudentAdmin)
