from django.db import models

class ApiLog(models.Model):
    endpoint = models.CharField(max_length=255)
    duration = models.IntegerField()  # tiempo en milisegundos
    status_code = models.IntegerField(null=True, blank=True)
    success = models.BooleanField()
    error = models.TextField(blank=True)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.endpoint} - {self.duration}ms"
