from . import queries

def profile(request):
    if request.user.is_authenticated:
        return {
            'profile': queries.get_or_create_user_profile(
                request.user
            )
        }
    else:
        return {}
