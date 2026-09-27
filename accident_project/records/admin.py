from django.contrib import admin
from .models import AccidentRecord, Hospital, PoliceStation, Alert, Profile

admin.site.register(AccidentRecord)
admin.site.register(Hospital)
admin.site.register(PoliceStation)
admin.site.register(Alert)
admin.site.register(Profile)