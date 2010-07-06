from django.contrib import admin
from randseats.seats.models import *

class ExamRoomUsageInline(admin.TabularInline):
    model = ExamRoomUsage

class RoomRangeInline(admin.TabularInline):
    model = RoomRange

class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'starttime', 'endtime')
    inlines = ( ExamRoomUsageInline, )

class PaperAdmin(admin.ModelAdmin):
    list_display = ('exam', 'name', 'identifier')
    list_filter = ('exam', )

class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'nick', 'seatscount', 'width', 'height')
    inlines = ( RoomRangeInline, )

class RoomSeatAdmin(admin.ModelAdmin):
    list_display = ('room', 'num', 'x', 'y', 'useable', 'range')
    list_filter = ('room', )

class StudentAdmin(admin.ModelAdmin):
    list_display = ('exam', 'idnumber', 'name', 'classnum', 'room', 'seat', 'paper')
    list_filter = ('exam', 'room', 'paper')

admin.site.register(Exam, ExamAdmin)
admin.site.register(Paper, PaperAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(RoomSeat, RoomSeatAdmin)
admin.site.register(Student, StudentAdmin)
