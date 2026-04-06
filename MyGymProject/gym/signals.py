from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def crear_o_actualizar_perfil(sender, instance, created, **kwargs):
    if created:
        role = Profile.Role.ADMIN if instance.is_staff else Profile.Role.ALUMNO
        Profile.objects.create(user=instance, role=role)
        return
    profile, _ = Profile.objects.get_or_create(
        user=instance,
        defaults={
            "role": Profile.Role.ADMIN if instance.is_staff else Profile.Role.ALUMNO,
        },
    )
    if instance.is_staff and profile.role != Profile.Role.ADMIN:
        profile.role = Profile.Role.ADMIN
        profile.save(update_fields=["role"])
