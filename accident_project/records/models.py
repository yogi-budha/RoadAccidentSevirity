from django.db import models
from django.contrib.auth.models import User


class AccidentRecord(models.Model):
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    location_name = models.CharField(max_length=200)
    road_name = models.CharField(max_length=100, default="Birendranagar")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    weather = models.CharField(max_length=20, default="Unknown")
    season = models.CharField(max_length=20, default="Normal")
    festival = models.CharField(max_length=20, null=True, blank=True)
    bs_date = models.CharField(max_length=12, default="")
    hour = models.IntegerField(null=True, blank=True)
    is_night = models.BooleanField(null=True, blank=True)
    cause = models.CharField(max_length=60, default="Unknown")
    vehicle_type = models.CharField(max_length=60, default="Unknown")
    deaths = models.IntegerField(default=0)
    serious = models.IntegerField(default=0)
    minor = models.IntegerField(default=0)
    injuries = models.IntegerField(default=0)
    predicted_severity = models.CharField(max_length=10, default="")
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.location_name}"


class Hospital(models.Model):
    name = models.CharField(max_length=150)
    latitude = models.FloatField()
    longitude = models.FloatField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name


class PoliceStation(models.Model):
    name = models.CharField(max_length=150)
    latitude = models.FloatField()
    longitude = models.FloatField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.name


class Alert(models.Model):
    LEVELS = [
        ("urgent", "Urgent"),
        ("high", "High"),
        ("info", "Info"),
    ]
    level = models.CharField(max_length=10, choices=LEVELS, default="info")
    message = models.TextField()
    accident = models.ForeignKey(AccidentRecord, on_delete=models.CASCADE,
                                 null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.message[:50]


class Profile(models.Model):
    ROLES = [
        ("police", "Traffic Police"),
        ("agency", "Government Agency"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default="police")

    def __str__(self):
        return f"{self.user.username} ({self.role})"