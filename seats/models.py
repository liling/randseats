#*-* encoding: UTF-8 *-*
from django.db import models

class Exam(models.Model):
    class Meta:
        verbose_name = '考试'
        verbose_name_plural = '考试'

    name = models.CharField('名称', max_length = 60)
    starttime = models.DateTimeField('开始时间')
    endtime = models.DateTimeField('结束时间')

    @models.permalink
    def get_absolute_url(self):
        return ('randseats.seats.views.show_exam', [str(self.id)])

    def __unicode__(self):
        return self.name

    def students_count(self):
        return Student.objects.filter(exam=self).count()

    def import_students(self, filename, forcepaper = None):
        from csv import reader
        c = 0
        for row in reader(file(filename)):
            idnumber, name, classnum = row
            s = Student(exam = self, idnumber = idnumber, name = name,
                        classnum = classnum, paper = forcepaper)
            s.save()
            c = c + 1
        return c
    
    def shuffle_students(self):
        from random import shuffle

        students = []
        for s in Student.objects.filter(exam=self,seat=None):
            students.append(s)
        shuffle(students)

        c = 0
        try:
            for usage in ExamRoomUsage.objects.filter(exam=self):
                map = usage.room.get_paper_map(Paper.objects.filter(exam=self, inuse=True))
                if not map: return False
                for seat in RoomSeat.objects.filter(room=usage.room,useable=True).order_by('num')[:usage.requiredseats]:
                    s = students.pop()
                    s.room = seat.room
                    s.seat = seat
                    if s.paper == None: s.paper = map[seat.x][seat.y]
                    s.save()
                    c = c + 1
        except IndexError:
            pass

        return c

    def report_room_seat_by_idnumber(self, room):
        """生成报表数据，该报表以学生班级、学号为序，输出学生的考场和座位号"""
        data = {}
        data['report_title'] = '考场座位名单'
        data['exam'] = self
        if room == None:
            students = Student.objects.filter(exam=self).order_by('idnumber')
        else:
            students = Student.objects.filter(exam=self, room=room).order_by('idnumber')
        data['students'] = students
        return data

    def report_student_names_by_room_seat(self, room):
        """生成报表数据，该报表以学生班级、学号为序，输出学生的考场和座位号"""
        data = {}
        data['report_title'] = '考生签到名单'
        data['exam'] = self
        data['room'] = room
        students = Student.objects.filter(exam=self, room=room).order_by('seat__num')
        print room.id
        data['students'] = students
        return data

class Room(models.Model):
    class Meta:
        verbose_name = '考场'
        verbose_name_plural = '考场'

    name = models.CharField('名称', max_length = 60)
    place = models.CharField('位置', max_length = 210)
    nick = models.CharField('简称', max_length = 5)
    seatscount = models.IntegerField('座位数')
    width = models.IntegerField('横向座位数')
    height = models.IntegerField('纵向座位数')

    def __unicode__(self):
        return self.name

    def get_seats_map(self):
        r = []
        for i in range(0, self.height + 2):
            r.append([0] * (self.width + 2))
        for s in RoomSeat.objects.filter(room = self):
            r[s.x][s.y] = s

        return r

    def get_paper_map(self, papers):
        r = []
        for i in xrange(0, self.height + 2):
            r.append([0] * (self.width + 2))

        for range in RoomRange.objects.filter(room=self):
            range_r = range.get_paper_map(len(papers))
            if not range_r: return False
            for i in xrange(1, len(range_r) - 1):
                for j in xrange(1, len(range_r[i]) - 1):
                    r[i+range.x-1][j+range.y-1] = papers[range_r[i][j] - 1]

        return r

    def get_students_map(self, exam):
        r = []
        for i in range(0, self.height + 2):
            r.append([0] * (self.width + 2))
        for s in RoomSeat.objects.filter(room = self):
            r[s.x][s.y] = s

        for student in Student.objects.filter(exam = exam, room = self):
            s = student.seat
            r[s.x][s.y] = student

        return r

    def useable_seats_count(self):
        return RoomSeat.objects.filter(room=self, useable=True).count()

    def total_seats_count(self):
        return RoomSeat.objects.filter(room=self).count()

class RoomRange(models.Model):
    class Meta:
        verbose_name = '考场区域'
        verbose_name_plural = '考场区域'

    room = models.ForeignKey(Room)
    seq = models.IntegerField('编号')
    x = models.IntegerField('横向起点')
    y = models.IntegerField('纵向起点')
    width = models.IntegerField('横向座位数')
    height = models.IntegerField('纵向座位数')

    def __unicode__(self):
        return u'%s 第%d区域' % (self.room, self.seq)

    def add_seats(self, startnum, direction, reverse_rl, reverse_td):

        # 准备一个空的二维数组
        r = []
        for i in range(0, self.height + 2):
            r.append([0] * (self.width + 2))

        # 根据方向填入座位号
        num = startnum
        if direction == 1:
            for i in range(1, self.height + 1):
                for j in range(1, self.width + 1):
                    r[i][j] = num
                    num = num + 1
        elif direction == 2:
            for j in range(1, self.width + 1):
                for i in range(1, self.height + 1):
                    r[i][j] = num
                    num = num + 1

        # 根据需要做翻转
        if reverse_rl:
            for i in range(len(r)):
                r[i].reverse()
        if reverse_td:
            r.reverse()

        # 将座位写入数据库
        for i in range(1, self.height + 1):
            for j in range(1, self.width + 1):
                if r[i][j] == 0: continue
                s = RoomSeat(room = self.room, range = self,
                             num = r[i][j], useable = True,
                             x = self.x + i - 1, y = self.y + j - 1)
                s.save()

        return num - startnum

    def clear_seats(self):
        RoomSeat.objects.filter(range = self).delete()

    def get_paper_map(self, papercount):
        r = []
        for i in range(0, self.height + 2):
            r.append([0] * (self.width + 2))

        pi = 1
        for i in range(1, self.height + 1):
            for j in range(1, self.width + 1):
                # dead 变量用于判断是否发生了无法分配考卷的情况
                dead = False
                while pi in (r[i-1][j], r[i+1][j], r[i][j-1], r[i][j+1]):
                    pi = pi + 1
                    if pi > papercount:
                        pi = 1
                        if dead: return False
                        dead = True
                r[i][j] = pi
        return r

class RoomSeat(models.Model):
    class Meta:
        verbose_name = '考场座位'
        verbose_name_plural = '考场座位'

    room = models.ForeignKey(Room)
    range = models.ForeignKey(RoomRange)
    num = models.IntegerField('编号')
    x = models.IntegerField('横向坐标')
    y = models.IntegerField('纵向坐标')
    useable = models.BooleanField()

    def __unicode__(self):
        return u"%d" % self.num

class Paper(models.Model):
    class Meta:
        verbose_name = '考卷'
        verbose_name_plural = '考卷'

    exam = models.ForeignKey(Exam)
    name = models.CharField('名称', max_length = 12)
    identifier = models.CharField('外部ID', max_length = 21)
    inuse = models.BooleanField('使用中')

    def __unicode__(self):
        return u"%s %s" % (self.exam, self.name)

class Student(models.Model):
    class Meta:
        verbose_name = '考生'
        verbose_name_plural = '考生'
    
    exam = models.ForeignKey(Exam)
    idnumber = models.CharField(max_length = 20)
    name = models.CharField('姓名', max_length = 39)
    classnum = models.CharField('班级', max_length = 20)
    room = models.ForeignKey(Room, null = True)
    seat = models.ForeignKey(RoomSeat, null = True)
    paper = models.ForeignKey(Paper, null = True)

class ExamRoomUsage(models.Model):
    exam = models.ForeignKey(Exam)
    room = models.ForeignKey(Room)
    requiredseats = models.IntegerField('需要座位数')

    def __unicode__(self):
        return u"%s %s" % (self.exam, self.room)

    def students_count(self):
        return Student.objects.filter(exam=self.exam, room=self.room).count()

    def empty_seats_count(self):
        return self.room.useable_seats_count() - self.students_count()

    def empty_seats_percent(self):
        sc = self.students_count()
        if sc:
            return round(100.0 * self.empty_seats_count() / self.students_count(), 1)
        else:
            return 100.0;
