from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()

from .models import Asistencia, PlanPago, Profile


class GymLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={"class": "input", "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "current-password"}),
    )


class PerfilAlumnoForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", max_length=150, required=True)
    last_name = forms.CharField(label="Apellidos", max_length=150, required=False)
    email = forms.EmailField(label="Correo electrónico", required=True)

    class Meta:
        model = Profile
        fields = (
            "edad",
            "fecha_nacimiento",
            "whatsapp",
        )
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "edad": forms.NumberInput(attrs={"class": "input"}),
            "whatsapp": forms.TextInput(attrs={"class": "input", "placeholder": "+51 ..."}),
        }


class EvaluacionFisicaForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "peso_kg",
            "talla_cm",
            "porcentaje_grasa",
            "masa_muscular_kg",
            "observaciones",
        )
        widgets = {
            "peso_kg": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "talla_cm": forms.NumberInput(attrs={"class": "input"}),
            "porcentaje_grasa": forms.NumberInput(attrs={"class": "input", "step": "0.1"}),
            "masa_muscular_kg": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "observaciones": forms.Textarea(attrs={"class": "input", "rows": 4, "placeholder": "Escriba aquí las observaciones físicas o del progreso..."}),
        }


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ("alumno", "fecha")
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "input"}),
            "alumno": forms.Select(attrs={"class": "input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alumno"].queryset = User.objects.filter(
            gym_profile__role=Profile.Role.ALUMNO
        ).order_by("first_name", "username")

    def clean(self):
        cleaned = super().clean()
        alumno = cleaned.get("alumno")
        fecha = cleaned.get("fecha")
        if alumno and fecha and Asistencia.objects.filter(alumno=alumno, fecha=fecha).exists():
            raise forms.ValidationError(
                "Ya consta asistencia para ese alumno en la fecha indicada."
            )
        return cleaned


class PlanPagoForm(forms.ModelForm):
    primera_cuota = forms.DateField(
        label="Vencimiento primera cuota",
        widget=forms.DateInput(attrs={"type": "date", "class": "input"}),
    )
    dias_entre_cuotas = forms.IntegerField(
        label="Días entre cuotas",
        initial=30,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={"class": "input"}),
    )

    class Meta:
        model = PlanPago
        fields = ("alumno", "monto_total", "num_cuotas")
        widgets = {
            "alumno": forms.Select(attrs={"class": "input"}),
            "monto_total": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "num_cuotas": forms.NumberInput(attrs={"class": "input", "min": 1, "max": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alumno"].queryset = User.objects.filter(
            gym_profile__role=Profile.Role.ALUMNO
        ).order_by("first_name", "username")

    def save(self, commit=True):
        from datetime import timedelta

        from .models import Cuota

        plan = super().save(commit=False)
        if commit:
            plan.save()
            primera = self.cleaned_data["primera_cuota"]
            gap = self.cleaned_data["dias_entre_cuotas"]
            n = plan.num_cuotas
            total = plan.monto_total
            per = (total / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            acum = Decimal("0")
            for i in range(1, n + 1):
                if i == n:
                    monto = total - acum
                else:
                    monto = per
                    acum += monto
                venc = primera + timedelta(days=gap * (i - 1))
                Cuota.objects.create(
                    plan=plan,
                    numero=i,
                    monto=monto,
                    fecha_vencimiento=venc,
                )
        return plan


class ServicioPersonalizadoForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("servicio_personalizado_inicio",)
        widgets = {
            "servicio_personalizado_inicio": forms.DateInput(
                attrs={"type": "date", "class": "input"}
            ),
        }


class CrearAlumnoForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "input"}),
    )
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "input"}),
    )
    email = forms.EmailField(
        label="Correo",
        required=False,
        widget=forms.EmailInput(attrs={"class": "input"}),
    )

    def clean_username(self):
        name = self.cleaned_data["username"]
        if User.objects.filter(username=name).exists():
            raise ValidationError("Ese nombre de usuario ya existe.")
        return name
