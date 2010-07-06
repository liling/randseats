#-*- encoding: UTF-8 -*-

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django import forms
from django.contrib import messages

import os, string, tempfile, datetime
from randseats.seats.models import *

def list_rooms(request):
    pass

def show_room(request, room_id):
    room = Room.objects.get(pk=room_id)
    roommap = room.get_seats_map()
    seats = ''
    for row in roommap:
        seats += '<tr>'
        for seat in row:
            if seat:
                if seat.useable:
                    seats += '<td><span class="num">%d</span></td>' % seat.num
                else:
                    seats += '<td class="not-useable"><span class="num">%d</span></td>' % seat.num
            else:
                seats += '<td class="no-seat">&nbsp;</td>';
        seats += '</tr>'
    return render_to_response('seats/room.html', {'room':room, 'seats':seats})

def room_add_seats(request, room_id):

    class AddSeatsForm(forms.Form):
        range = forms.ModelChoiceField(RoomRange.objects.filter(room=room_id))
        start_number = forms.CharField()
        direction = forms.ChoiceField(choices = ((1, 'Left to right first'), (2, 'Up to down first')))
        reverse_left_right = forms.BooleanField(required = False)
        reverse_top_down = forms.BooleanField(required = False)
    
    if request.method == 'POST':
        form = AddSeatsForm(request.POST)
        if form.is_valid():
            range = form.cleaned_data['range']
            startnum = string.atoi(form.cleaned_data['start_number'])
            direction = string.atoi(form.cleaned_data['direction'])
            rlr = form.cleaned_data['reverse_left_right']
            rtd = form.cleaned_data['reverse_top_down']
            count = range.add_seats(startnum, direction, rlr, rtd)
            return HttpResponse('Successfully add %d seats' % count)
    else:
        form = AddSeatsForm()

    return render_to_response('seats/add_seats.html', {'room_id' : room_id, 'form': form})

def room_clear_seats(request, room_id):

    class ClearSeatsForm(forms.Form):
        range = forms.ModelChoiceField(RoomRange.objects.filter(room=room_id))

    if request.method == 'POST':
        form = ClearSeatsForm(request.POST)
        if form.is_valid():
            range = form.cleaned_data['range']
            range.clear_seats()
            return HttpResponse('Successfully clear seats')
    else:
        form = ClearSeatsForm()
    return render_to_response('seats/clear_room.html', {'room_id' : room_id, 'form' : form})

def list_exams(request):
    future_exams = Exam.objects.filter(
        starttime__gt=datetime.datetime.now()).order_by('-starttime');
    finished_exams = Exam.objects.filter(
        endtime__lt=datetime.datetime.now()).order_by('-starttime');

    return render_to_response(
        'seats/list_exams.html',
        {'future_exams': future_exams, 'finished_exams': finished_exams})

def show_exam(request, exam_id):
    exam = Exam.objects.get(pk=exam_id)
    papers = Paper.objects.filter(exam=exam)
    roomusage = ExamRoomUsage.objects.filter(exam=exam)
    return render_to_response(
        'seats/exam.html',
        {'exam':exam, 'papers': papers, 'roomusage':roomusage},
        context_instance=RequestContext(request))

def exam_import_students(request, exam_id):

    class StudentImportForm(forms.Form):
        csv_file = forms.FileField()
        force_paper = forms.ModelChoiceField(Paper.objects.filter(exam=exam_id), required=False)

    exam = Exam.objects.get(pk=exam_id)
    if request.POST.has_key('cancel'):
        messages.info(request, '导入考生数据操作取消')
        return redirect(exam)

    if request.method == 'POST':
        form = StudentImportForm(request.POST, request.FILES)
        if form.is_valid():

            # 取得一个临时文件
            csvfile = tempfile.NamedTemporaryFile()
            tempname = csvfile.name
            csvfile.close()

            csvfile = file(tempname, 'wb')
            uploaded = request.FILES['csv_file']
            if uploaded.multiple_chunks():
                for chunk in uploaded.chunks():
                    csvfile.write(chunk)
            else:
                csvfile.write(uploaded.read())
            csvfile.close()

            force_paper = form.cleaned_data['force_paper']
            count = exam.import_students(tempname, force_paper)

            os.unlink(tempname)
            
            return HttpResponse('Successfully import %d students' % count)
    else:
        form = StudentImportForm()

    return render_to_response(
        'seats/student_import.html', {'exam_id':exam_id, 'form':form},
        context_instance=RequestContext(request))

def exam_clear_students(request, exam_id):
    exam = Exam.objects.get(pk = exam_id)
    confirmed = request.GET.has_key('confirmed')
    canceled = request.GET.has_key('canceled')
    if canceled:
        messages.info(request, '清空学生数据操作已经取消')
        return redirect(exam)
    if confirmed:
        Student.objects.filter(exam = exam_id).delete()
        messages.success(request, '成功清空学生数据')
        return redirect(exam)
    else:
        return render_to_response('seats/student_clear.html', {'exam': exam})

def exam_shuffle_students(request, exam_id):
    exam = Exam.objects.get(pk = exam_id)
    c = exam.shuffle_students()
    if c == False:
        messages.error(request, '无法为考生排座位')
        return redirect(exam)
    else:
        messages.success(request, '已经成功为 %d 个考生排座位' % c)
        return redirect(exam)

def exam_show_room_students(request, exam_id, room_id):
    exam = Exam.objects.get(pk = exam_id)
    room = Room.objects.get(pk = room_id)
    smap = room.get_students_map(exam)
    seats = ''
    for row in smap:
        seats += '<tr>'
        for s in row:
            if isinstance(s, int):
                seats += ''
            elif isinstance(s, RoomSeat):
                if s.useable:
                    clazz = 'empty'
                else:
                    clazz = 'not-useable'
                seats += '<td class="%s"><span class="num">%d</span></td>' % (clazz, s.num)
            else:
                lastname = s.name[:1]; firstname = s.name[1:]
                seats += '<td><span class="num">%d</span><span class="name">%s<br/>%s</span></td>' % (s.seat.num, lastname, firstname)
        seats += '</tr>'
    return render_to_response('seats/room.html', {'room':room, 'seats':seats})

def exam_export(request, exam_id):
    class ExamExportForm(forms.Form):
        report = forms.ChoiceField(choices = (
                    (1, 'Room Seat Report Sort by ID Number'),
                    (2, 'Student Names Report Sort by Seat')))
        room = forms.ModelChoiceField(Room.objects, required=False)
        format = forms.ChoiceField(choices = (
                    (1, 'HTML Two Columns'), (2, 'CSV Two Columns'),
                    (3, 'CSV Data Only'), (4, 'PDF Two Columns')))

    if request.method == 'POST':
        form = ExamExportForm(request.POST)
        if form.is_valid():
            exam = Exam.objects.get(pk=exam_id)
            report = string.atoi(form.cleaned_data['report'])
            room = form.cleaned_data['room']
            format = string.atoi(form.cleaned_data['format'])

            if report == 1:
                data = exam.report_room_seat_by_idnumber(room)
                context = { 'data' : data }
                report_template_prefix = 'seats/report_roomseat_'
            elif report == 2:
                data = exam.report_student_names_by_room_seat(room)
                context = { 'data' : data }
                report_template_prefix = 'seats/report_studentname_'

            print len(data['students'])
            if format in (1, 2, 4):
                pages = []
                for i in range(0, len(data['students']), 50):
                    page = {}

                    page['column1'] = data['students'][i:i+25]
                    page['column2'] = data['students'][i+25:i+50]
                    if len(page['column2']) == 0: del page['column2']
                    page['first'] = page['column1'][0]
                    if page.has_key('column2'):
                        page['last'] = page['column2'][-1]
                    else:
                        page['last'] = page['column1'][-1]

                    rows = []
                    for i in range(len(page['column1'])):
                        row = [page['column1'][i]]
                        if page.has_key('column2') and i < len(page['column2']):
                            row.append(page['column2'][i])
                        rows.append(row)
                    page['rows'] = rows

                    pages.append(page)
                context['pages'] = pages

            if format == 1:
                template = report_template_prefix + 'html2c.html'
                mime = 'text/html'
            elif format == 2:
                template = report_template_prefix + 'csv2c.txt'
                mime = 'text/csv'
            elif format == 3:
                template = report_template_prefix + 'csvdata.txt'
                mime = 'text/csv'
            elif format == 4:
                template = report_template_prefix + 'latex.txt'
                mime = 'text/plain'

            return render_to_response(template, context, mimetype=mime)
    else:
        form = ExamExportForm()

    return render_to_response('seats/exam_export.html', {'exam_id' : exam_id, 'form' : form})
