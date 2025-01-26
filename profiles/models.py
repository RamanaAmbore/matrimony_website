from django.db import models
from users.models import CustomUser

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    dob = models.DateField()
    nakshatram = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    blurred_image = models.ImageField(upload_to='blurred_images/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.full_name
