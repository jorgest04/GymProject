from django.contrib import admin

from .models import Asistencia, Cuota, PlanPago, Profile

admin.site.site_header = "GymProject — administración"
admin.site.site_title = "GymProject"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "servicio_personalizado_inicio", "plan_congelado_display")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "whatsapp")

    @admin.display(description="Congelado", boolean=True)
    def plan_congelado_display(self, obj):
        return obj.plan_congelado()


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
    inlines = [CuotaInline]
