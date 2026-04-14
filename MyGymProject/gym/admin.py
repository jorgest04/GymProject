from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Asistencia, Cuota, PlanPago, Profile

admin.site.site_header = "GymProject — administración"
admin.site.site_title = "GymProject"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "servicio_personalizado_inicio",
        "plan_congelado_display",
        "editar_planes_link",
    )
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "whatsapp")
    readonly_fields = ("editar_planes_link",)

    @admin.display(description="Congelado", boolean=True)
    def plan_congelado_display(self, obj):
        return obj.plan_congelado()

    @admin.display(description="Planes")
    def editar_planes_link(self, obj: Profile):
        """
        Acceso directo a los planes de pago del alumno (User) relacionado.
        """
        if not obj or not getattr(obj, "user_id", None):
            return "-"
        url = (
            reverse("admin:gym_planpago_changelist")
            + f"?alumno__id__exact={obj.user_id}"
        )
        return format_html('<a class="button" href="{}">Editar planes</a>', url)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "fecha")
    list_filter = ("fecha",)
    search_fields = ("alumno__username",)


class CuotaInline(admin.TabularInline):
    model = Cuota
    extra = 0


@admin.register(PlanPago)
class PlanPagoAdmin(admin.ModelAdmin):
    list_display = ("alumno", "monto_total", "num_cuotas", "creado")
    list_filter = ("creado", "num_cuotas")
    search_fields = ("alumno__username", "alumno__first_name", "alumno__last_name")
    inlines = [CuotaInline]
