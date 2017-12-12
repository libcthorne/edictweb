from django.test import TestCase

from .models import(
    Profile,
    User,
)

def get_stub_user():
    return User.objects.create()

class ProfileTests(TestCase):
    def test_get_default_image_url(self):
        profile = Profile.objects.create(
            user=get_stub_user(),
            display_name="test",
        )

        url = profile.get_image_or_default_url()
        self.assertEqual(url, "/static/images/default_profile_image.png")

    def test_get_custom_image_url(self):
        profile = Profile.objects.create(
            user=get_stub_user(),
            display_name="test",
            image="images/hello.jpg",
        )

        url = profile.get_image_or_default_url()
        self.assertEqual(url, "/uploads/images/hello.jpg")

    def test_str(self):
        profile = Profile.objects.create(
            user=get_stub_user(),
            display_name="My display name",
        )

        self.assertEqual(str(profile), "My display name")
