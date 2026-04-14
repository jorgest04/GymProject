# 🏋️‍♂️ Resumen Técnico del Proyecto: FitnessIQ / GymProject

Este documento sirve como memoria de configuración y guía de mantenimiento para el sistema de gestión de gimnasio.

## 📁 Estructura y Entorno
- **Ubicación Local:** `C:\Users\ansit\Python\GymProject\`
- **Entorno Virtual:** Ubicado en `venv\`. Activar con `.\venv\Scripts\Activate.ps1`.
- **Aplicación Principal:** `MyGymProject` (Django 4.2.29).

## 🗄️ Base de Datos (Neon - PostgreSQL)
El proyecto está conectado a una base de datos en la nube (Neon).
- **Nombre de la DB:** `myGymProject`
- **Configuración:** Los datos de conexión están en el archivo oculto `.env` (variable `DATABASE_URL`).
- **Importante:** El archivo `.env` NO se sube a GitHub por seguridad.

## 👤 Usuarios y Credenciales (Base de Datos Actual)
Se han creado dos usuarios iniciales para pruebas:
1. **Administrador:**
   - Usuario: `admin`
   - Contraseña: `admin_gym123`
2. **Alumno:**
   - Usuario: `alumno`
   - Contraseña: `alumno_gym123`

## 🚀 Despliegue en Render
- **Dominio Personalizado:** `https://fitnessiq.site`
- **Root Directory en Render:** `MyGymProject`
- **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
- **Start Command:** `gunicorn MyGymProject.wsgi`
- **Variable de Entorno en Render:** Se debe configurar `DATABASE_URL` con la cadena de conexión de Neon.

## 🛠️ Funcionalidades Personalizadas Implementadas
1. **Gestión de Planes:** Moneda cambiada a **Soles (S/.)**. El concepto de "Servicio" se unificó bajo "Plan".
2. **Pagos Automatizados:** Al registrar un pago, se guarda automáticamente la fecha y hora actual (`timezone.now`).
3. **Evaluación Física (Admin):** Formulario exclusivo para que el administrador registre Peso, Talla, % Grasa y Masa Muscular.
4. **Sistema de Observaciones:** El administrador registra notas de progreso que el alumno puede ver en su portal.
5. **Estética y Logo:**
   - Logo ubicado en `gym/static/gym/imgs/logo.jpg`.
   - Aparece en el encabezado (superior izquierda) y en la pantalla de inicio de sesión.
   - Fondo decorado y tarjetas visuales mejoradas.
6. **Archivos Estáticos:** Configurado con `whitenoise` para que el logo y el CSS se vean correctamente en internet.

## 🐙 GitHub
- **Repositorio:** `https://github.com/jorgest04/GymProject.git`
- **Rama principal:** `main`
- **Autenticación:** Requiere un *Personal Access Token (PAT)* de GitHub para hacer `git push`.

---
*Documento generado el 05 de Abril de 2026.*
