from django.contrib import admin
from .models import Coach, LessonBooking, LessonProgram


admin.site.register(Coach)
admin.site.register(LessonProgram)
admin.site.register(LessonBooking)
