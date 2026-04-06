from .models import Profile


def gym_role(request):
    if not request.user.is_authenticated:
        return {"gym_role": None}
    try:
        return {"gym_role": request.user.gym_profile.role}
    except Profile.DoesNotExist:
        return {"gym_role": None}
