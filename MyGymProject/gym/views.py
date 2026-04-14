from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AsistenciaForm,
    CrearAlumnoForm,
    EvaluacionFisicaForm,
    GymLoginForm,
    PerfilAlumnoForm,
    PlanPagoForm,
    ServicioPersonalizadoForm,
    EditarAlumnoForm,
)
from .models import Asistencia, Cuota, PlanPago, Profile, EvaluacionFisica

def _profile(user):
    return getattr(user, "gym_profile", None)

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("gym:login")
        p = _profile(request.user)
        if not p or p.role != Profile.Role.ADMIN:
            return HttpResponseForbidden("Acceso solo para administradores.")
        return view_func(request, *args, **kwargs)
    return wrapper

def alumno_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("gym:login")
        p = _profile(request.user)
        if not p or p.role != Profile.Role.ALUMNO:
            return HttpResponseForbidden("Acceso solo para alumnos.")
        return view_func(request, *args, **kwargs)
    return wrapper

def vista_login(request):
    if request.user.is_authenticated:
        p = _profile(request.user)
        if p and p.role == Profile.Role.ADMIN:
            return redirect("gym:admin_dashboard")
        return redirect("gym:alumno_portal")
    form = GymLoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        p = _profile(user)
        if p and p.role == Profile.Role.ADMIN:
            messages.success(request, "Bienvenido, administrador.")
            return redirect("gym:admin_dashboard")
        messages.success(request, "Bienvenido.")
        return redirect("gym:alumno_portal")
    return render(request, "gym/login.html", {"form": form, "titulo": "Acceso — Gimnasio"})

def vista_logout(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect("gym:login")

@admin_required
def admin_dashboard(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    asistencias_hoy = Asistencia.objects.filter(fecha=today).count()
    asistencias_semana = Asistencia.objects.filter(fecha__gte=week_start, fecha__lte=today).count()
    alumnos = User.objects.filter(gym_profile__role=Profile.Role.ALUMNO).select_related("gym_profile").order_by("-id")
    ultimas_notas = Profile.objects.filter(role=Profile.Role.ALUMNO).exclude(observaciones="").order_by("-id")[:5]
    return render(request, "gym/admin_dashboard.html", {
        "asistencias_hoy": asistencias_hoy,
        "asistencias_semana": asistencias_semana,
        "alumnos": alumnos,
        "ultimas_notas": ultimas_notas,
        "today": today,
    })

@admin_required
def admin_asistencia_nueva(request):
    form = AsistenciaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Asistencia registrada.")
        return redirect("gym:admin_asistencias")
    return render(request, "gym/admin_asistencia_form.html", {"form": form})

@admin_required
def admin_asistencias_lista(request):
    alumno_id = request.GET.get("alumno")
    qs = Asistencia.objects.select_related("alumno")
    if alumno_id:
        qs = qs.filter(alumno_id=alumno_id)
    qs = qs.order_by("-fecha")[:200]
    return render(request, "gym/admin_asistencias_lista.html", {"asistencias": qs})

from decimal import Decimal, ROUND_HALF_UP

@admin_required
def admin_plan_pago_nuevo(request):
    user_id = request.GET.get("alumno")
    alumno = get_object_or_404(User, pk=user_id) if user_id else None
    
    # VALIDACIÓN: Verificar si el alumno ya tiene un plan
    if alumno:
        plan_existente = PlanPago.objects.filter(alumno=alumno).first()
        if plan_existente:
            ultima_cuota = plan_existente.cuotas.order_by("-fecha_vencimiento").first()
            fecha_venc = ultima_cuota.fecha_vencimiento.strftime("%d/%m/%Y") if ultima_cuota else "desconocida"
            messages.warning(request, f"⚠️ El alumno {alumno.first_name} ya tiene un plan activo. El vencimiento de su última cuota es el {fecha_venc}. No se puede crear otro plan hasta finalizar el actual.")
            return redirect("gym:admin_dashboard")

    form = PlanPagoForm(request.POST or None, initial={"alumno": alumno})
    
    if request.method == "POST" and form.is_valid():
        # (Re-verificación por seguridad en el POST)
        if PlanPago.objects.filter(alumno=form.cleaned_data['alumno']).exists():
            messages.error(request, "Error: Este alumno ya cuenta con un plan registrado.")
            return redirect("gym:admin_dashboard")
            
        plan = form.save()
        n = plan.num_cuotas
        total = plan.monto_total
        per = (total / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        acum = Decimal("0")
        
        # En esta versión, generamos las cuotas. 
        # La personalización de fechas se hace aquí mismo recibiendo listas del POST si fuera necesario,
        # pero para mayor control, dejaremos que se creen y el admin las edite en la lista de planes.
        for i in range(1, n + 1):
            if i == n: monto = total - acum
            else:
                monto = per
                acum += monto
            
            # Fecha personalizada: si viene del POST como 'fecha_1', 'fecha_2', etc.
            f_key = f"fecha_{i}"
            fecha_venc = request.POST.get(f_key)
            if not fecha_venc:
                fecha_venc = timezone.localdate() + timedelta(days=30 * (i-1))
            
            Cuota.objects.create(
                plan=plan,
                numero=i,
                monto=monto,
                fecha_vencimiento=fecha_venc,
            )
        
        messages.success(request, f"Plan personalizado creado para {plan.alumno.first_name}.")
        return redirect("gym:admin_planes")
    
    return render(request, "gym/admin_plan_form.html", {"form": form, "alumno": alumno})

@admin_required
def admin_planes_lista(request):
    alumno_id = request.GET.get("alumno")
    planes = PlanPago.objects.select_related("alumno").prefetch_related("cuotas")
    if alumno_id:
        planes = planes.filter(alumno_id=alumno_id)
    planes = planes.order_by("-creado")[:100]
    return render(request, "gym/admin_planes_lista.html", {"planes": planes})

@admin_required
def admin_cuota_marcar_pagada(request, pk):
    cuota = get_object_or_404(Cuota.objects.select_related("plan"), pk=pk)
    if not cuota.pagado:
        cuota.pagado = True
        cuota.fecha_pago = timezone.now()
        cuota.save(update_fields=["pagado", "fecha_pago"])
        # Formateamos la fecha para el mensaje de éxito
        fecha_str = timezone.localtime(cuota.fecha_pago).strftime('%d/%m/%Y %H:%M')
        messages.success(request, f"¡Pago registrado con éxito! Fecha: {fecha_str}")
    return redirect("gym:admin_planes")

@admin_required
def admin_evaluacion_alumno(request, user_id):
    alumno = get_object_or_404(User, pk=user_id)
    profile = alumno.gym_profile
    form = EvaluacionFisicaForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        # Actualizamos el perfil (datos actuales)
        profile = form.save()
        
        # Guardamos en el historial (nueva evaluación)
        EvaluacionFisica.objects.create(
            alumno=alumno,
            peso_kg=profile.peso_kg or 0,
            talla_cm=profile.talla_cm or 0,
            porcentaje_grasa=profile.porcentaje_grasa or 0,
            masa_muscular_kg=profile.masa_muscular_kg or 0,
            observaciones=profile.observaciones
        )
        
        messages.success(request, f"Evaluación de {alumno.get_full_name() or alumno.username} guardada e historial registrado.")
        return redirect("gym:admin_dashboard")
    return render(request, "gym/admin_evaluacion_form.html", {"form": form, "alumno": alumno})

@admin_required
def admin_crear_alumno(request):
    form = CrearAlumnoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        u = User.objects.create_user(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data.get("last_name") or "",
            email=form.cleaned_data.get("email") or "",
            is_staff=False,
        )
        messages.success(request, f"Alumno «{u.username}» creado.")
        return redirect("gym:admin_dashboard")
    return render(request, "gym/admin_crear_alumno.html", {"form": form})

@admin_required
def admin_editar_alumno(request, user_id):
    alumno = get_object_or_404(User, pk=user_id)
    profile = alumno.gym_profile
    form = EditarAlumnoForm(request.POST or None, instance=profile, user=alumno)
    if request.method == "POST" and form.is_valid():
        form.save()
        alumno.first_name = form.cleaned_data["first_name"]
        alumno.last_name = form.cleaned_data["last_name"]
        alumno.email = form.cleaned_data["email"]
        alumno.save()
        messages.success(request, f"Datos de {alumno.username} actualizados.")
        return redirect("gym:admin_dashboard")
    return render(
        request,
        "gym/admin_crear_alumno.html",
        {
            "form": form,
            "titulo": f"Editar Alumno: {alumno.username}",
            "es_edicion": True,
            "alumno": alumno,
        },
    )

@admin_required
def admin_asistencias_por_alumno(request):
    data = Asistencia.objects.values("alumno__username", "alumno__first_name").annotate(total=Count("id")).order_by("-total")[:50]
    return render(request, "gym/admin_asistencias_stats.html", {"data": data})

@alumno_required
def alumno_portal(request):
    profile = request.user.gym_profile
    dias_efectivos = profile.dias_efectivos_servicio()
    cuotas = Cuota.objects.filter(plan__alumno=request.user).select_related("plan").order_by("fecha_vencimiento")
    mis_asistencias = Asistencia.objects.filter(alumno=request.user).order_by("-fecha")[:30]
    
    # Datos para los gráficos
    evaluaciones = EvaluacionFisica.objects.filter(alumno=request.user).order_by("fecha")
    labels = [ev.fecha.strftime("%d/%m") for ev in evaluaciones]
    pesos = [float(ev.peso_kg) for ev in evaluaciones]
    grasas = [float(ev.porcentaje_grasa) for ev in evaluaciones]
    musculo = [float(ev.masa_muscular_kg) for ev in evaluaciones]

    return render(request, "gym/alumno_portal.html", {
        "profile": profile,
        "dias_efectivos": dias_efectivos,
        "cuotas": cuotas,
        "mis_asistencias": mis_asistencias,
        "chart_labels": labels,
        "chart_pesos": pesos,
        "chart_grasas": grasas,
        "chart_musculo": musculo,
    })

@alumno_required
def alumno_perfil(request):
    profile = request.user.gym_profile
    form = PerfilAlumnoForm(request.POST or None, instance=profile, initial={
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "email": request.user.email,
    })
    if request.method == "POST" and form.is_valid():
        form.save()
        request.user.first_name = form.cleaned_data["first_name"]
        request.user.last_name = form.cleaned_data.get("last_name") or ""
        request.user.email = form.cleaned_data["email"]
        request.user.save(update_fields=["first_name", "last_name", "email"])
        messages.success(request, "Perfil actualizado.")
        return redirect("gym:alumno_portal")
    return render(request, "gym/alumno_perfil.html", {"form": form})

@alumno_required
def alumno_congelar(request):
    profile = request.user.gym_profile
    if profile.plan_congelado(): return redirect("gym:alumno_portal")
    if request.method == "POST":
        profile.congelado_desde = timezone.now()
        profile.save(update_fields=["congelado_desde"])
        return redirect("gym:alumno_portal")
    return render(request, "gym/alumno_congelar_confirm.html", {"profile": profile})

@alumno_required
def alumno_descongelar(request):
    profile = request.user.gym_profile
    if not profile.plan_congelado(): return redirect("gym:alumno_portal")
    if request.method == "POST":
        fin = timezone.localdate()
        inicio = timezone.localdate(profile.congelado_desde)
        dias = max(0, (fin - inicio).days)
        profile.dias_congelados_acumulados += dias
        profile.congelado_desde = None
        profile.save(update_fields=["dias_congelados_acumulados", "congelado_desde"])
        return redirect("gym:alumno_portal")
    return render(request, "gym/alumno_descongelar_confirm.html", {"profile": profile})

def home(request):
    if request.user.is_authenticated:
        p = _profile(request.user)
        if p and p.role == Profile.Role.ADMIN: return redirect("gym:admin_dashboard")
        return redirect("gym:alumno_portal")
    return redirect("gym:login")
