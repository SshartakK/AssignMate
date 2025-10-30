from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    #статус пользователя - преподаватель / студент

    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.avatar.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.avatar.path)

    def __str__(self):
        return self.user.username