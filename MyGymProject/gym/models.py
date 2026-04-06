from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ALUMNO = "alumno", "Alumno"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gym_profile",
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.ALUMNO,
    )
    edad = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    peso_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso (kg)",
    )
    talla_cm = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Talla (cm)",
    )
    whatsapp = models.CharField(max_length=32, blank=True, verbose_name="WhatsApp")
    # Datos físicos (Gestionados por Admin)
    porcentaje_grasa = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name="% Grasa")
    masa_muscular_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Masa Muscular (kg)")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones del Admin")
    
    servicio_personalizado_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name="Inicio servicio personalizado (4 semanas)",
    )
    congelado_desde = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Congelado desde",
    )
    dias_congelados_acumulados = models.PositiveIntegerField(
        default=0,
        verbose_name="Días congelados acumulados",
    )

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"{self.user.get_username()} ({self.get_role_display()})"

    def dias_efectivos_servicio(self):
        if not self.servicio_personalizado_inicio:
            return 0
        today = timezone.now().date()
        total_calendario = (today - self.servicio_personalizado_inicio).days
        extra_congelacion_actual = 0
        if self.congelado_desde:
            extra_congelacion_actual = (today - timezone.localdate(self.congelado_desde)).days
        return max(
            0,
            total_calendario - int(self.dias_congelados_acumulados) - extra_congelacion_actual,
        )

    def servicio_finalizado(self):
        return self.dias_efectivos_servicio() >= 28

    def plan_congelado(self):
        return self.congelado_desde is not None


class Asistencia(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asistencias",
    )
    fecha = models.DateField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        constraints = [
            models.UniqueConstraint(
                fields=["alumno", "fecha"],
                name="unique_asistencia_alumno_fecha",
            ),
        ]
        ordering = ["-fecha", "alumno_id"]

    def __str__(self):
        return f"{self.alumno} — {self.fecha}"


class PlanPago(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="planes_pago",
    )
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    num_cuotas = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plan de pago"
        verbose_name_plural = "Planes de pago"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.alumno} — {self.monto_total} ({self.num_cuotas} cuotas)"


class Cuota(models.Model):
    plan = models.ForeignKey(
        PlanPago,
        on_delete=models.CASCADE,
        related_name="cuotas",
    )
    numero = models.PositiveSmallIntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ["plan_id", "numero"]

    def __str__(self):
        estado = "Pagada" if self.pagado else "Pendiente"
        return f"Cuota {self.numero} — {self.monto} ({estado})"
