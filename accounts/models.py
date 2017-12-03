from django.db import models
from django.contrib.auth.models import User
from django.contrib.staticfiles.templatetags.staticfiles import static

from django_resized import ResizedImageField

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=64, blank=True)
    image = ResizedImageField(
        size=[100, 100],
        upload_to='images/', null=True, blank=True
    )

    def get_image_or_default_url(self):
        if self.image:
            return self.image.url
        else:
            return static('images/default_profile_image.png')

    def __str__(self):
        return self.display_name
