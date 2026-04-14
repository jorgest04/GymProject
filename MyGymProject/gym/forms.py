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


class EditarAlumnoForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", max_length=150, required=True, widget=forms.TextInput(attrs={"class": "input"}))
    last_name = forms.CharField(label="Apellidos", max_length=150, required=False, widget=forms.TextInput(attrs={"class": "input"}))
    email = forms.EmailField(label="Correo", required=False, widget=forms.EmailInput(attrs={"class": "input"}))

    class Meta:
        model = Profile
        fields = ("whatsapp", "edad", "fecha_nacimiento")
        widgets = {
            "whatsapp": forms.TextInput(attrs={"class": "input"}),
            "edad": forms.NumberInput(attrs={"class": "input"}),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "class": "input"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

class PlanPagoForm(forms.ModelForm):
    # Campos base para el plan
    class Meta:
        model = PlanPago
        fields = ("alumno", "monto_total", "num_cuotas")
        widgets = {
            "alumno": forms.HiddenInput(), # Lo pasaremos por URL/Vista
            "monto_total": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "num_cuotas": forms.NumberInput(attrs={"class": "input", "min": 1, "max": 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No necesitamos filtrar el queryset porque el alumno vendrá pre-asignado


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
