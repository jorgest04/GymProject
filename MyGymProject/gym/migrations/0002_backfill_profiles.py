from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("gym", "Profile")
    for u in User.objects.all():
        if Profile.objects.filter(user_id=u.pk).exists():
            continue
        role = "admin" if u.is_staff else "alumno"
        Profile.objects.create(user_id=u.pk, role=role)


class Migration(migrations.Migration):
    dependencies = [
        ("gym", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]
