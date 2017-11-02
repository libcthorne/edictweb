from .models import Profile

def get_or_create_user_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile
