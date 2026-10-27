# ==========================================
# BLOQUE 1: CONFIGURACIÓN E IMPORTACIONES
# ==========================================
import calendar
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
import urllib.request
import uuid
import webbrowser
from datetime import datetime, timedelta
import customtkinter as ctk
import winsound
from PIL import Image, ImageDraw

try:
    from plyer import notification

    HAY_PLYER = True
except Exception:
    HAY_PLYER = False

try:
    import pystray

    HAY_PYSTRAY = True
except Exception:
    HAY_PYSTRAY = False

VERSION_ACTUAL = "1.2.0"

CARPETA_DATOS = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "KokeToDo")
os.makedirs(CARPETA_DATOS, exist_ok=True)

ARCHIVO_TAREAS = os.path.join(CARPETA_DATOS, "tareas.json")
ARCHIVO_CONFIG = os.path.join(CARPETA_DATOS, "config.json")

CARPETA_STARTUP = os.path.join(
    os.getenv("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"
)
ACCESO_STARTUP_VBS = os.path.join(CARPETA_STARTUP, "KokeToDoBackground.vbs")

tareas = []
secciones_abiertas = {}
meses_abiertos = {}
widgets_dias = {}
recordatorio_actual = {"hora": "", "anticipacion": 0}
fecha_seleccionada_nueva = {"iso": datetime.now().date().strftime("%Y-%m-%d")}
tray_icon = None
popup_eliminar_activo = None
_aviso_bandeja_mostrado = False
ultimo_dia_verificado = {"dia": None}
modo_widget = False
geometria_previa = "420x620"
filtro_busqueda = ""
busqueda_activa = False

DIAS_ESPANOL = {
    0: "Lun",
    1: "Mar",
    2: "Mié",
    3: "Jue",
    4: "Vie",
    5: "Sáb",
    6: "Dom",
}

DIAS_COMPLETOS = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

MESES_ESPANOL = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

TEMAS = {
    "Obsidian": {
        "bg_app": "#0A0C0E",
        "bg_card": "#14171E",
        "border_card": "#1F232B",
        "bg_input": "#13161C",
        "border_input": "#1F242D",
        "text_main": "#F9FAFB",
        "text_muted": "#9CA3AF",
        "placeholder": "#4B5563",
        "badge_ok": "#34D399",
        "badge_alert": "#F87171",
        "icono": "•",
    },
    "Midnight": {
        "bg_app": "#0B111E",
        "bg_card": "#131C2E",
        "border_card": "#1E2B45",
        "bg_input": "#111827",
        "border_input": "#1F2D44",
        "text_main": "#F1F5F9",
        "text_muted": "#94A3B8",
        "placeholder": "#4B5563",
        "badge_ok": "#38BDF8",
        "badge_alert": "#FB7185",
        "icono": "•",
    },
    "Forest": {
        "bg_app": "#0A120E",
        "bg_card": "#121F18",
        "border_card": "#1C3026",
        "bg_input": "#0F1A14",
        "border_input": "#1B2F25",
        "text_main": "#F2FBF6",
        "text_muted": "#86A795",
        "placeholder": "#4B5563",
        "badge_ok": "#34D399",
        "badge_alert": "#F87171",
        "icono": "•",
    },
    "Grafito": {
        "bg_app": "#121212",
        "bg_card": "#1E1E1E",
        "border_card": "#2C2C2C",
        "bg_input": "#181818",
        "border_input": "#2A2A2A",
        "text_main": "#EDEDED",
        "text_muted": "#A0A0A0",
        "placeholder": "#5A5A5A",
        "badge_ok": "#4ADE80",
        "badge_alert": "#F87171",
        "icono": "•",
    },
    "Hello Kitty": {
        "bg_app": "#FCD8E2",
        "bg_card": "#FFE4ED",
        "border_card": "#FFE4ED",
        "bg_input": "#FFFFFF",
        "border_input": "#F472B6",
        "text_main": "#831843",
        "text_muted": "#DB2777",
        "placeholder": "#BB6E8C",
        "badge_ok": "#EC4899",
        "badge_alert": "#E11D48",
        "icono": "🎀",
    },
}

tema_actual = "Obsidian"


def obtener_texto_boton_fecha(fecha_iso):
    hoy_d = datetime.now().date()
    try:
        f = datetime.strptime(fecha_iso, "%Y-%m-%d").date()
        dias_dif = (f - hoy_d).days
        nom_d = DIAS_ESPANOL[f.weekday()]
        fmt = f.strftime("%d/%m")
        if dias_dif == 0:
            return f"📅 Hoy ({nom_d} {fmt})"
        elif dias_dif == 1:
            return f"📅 Mañana ({nom_d} {fmt})"
        else:
            return f"📅 {nom_d} {fmt}"
    except Exception:
        return "📅 Elegir Fecha"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def obtener_ruta_imagen_kitty():
    for ext in ["kitty_bg.png", "kitty_bg.jpg", "kitty_bg.jpeg"]:
        p = resource_path(ext)
        if os.path.exists(p):
            return p
    return None


# ==========================================
# INICIO CON WINDOWS (SEGUNDO PLANO)
# ==========================================
def esta_en_inicio_windows():
    return os.path.exists(ACCESO_STARTUP_VBS)


def configurar_inicio_windows(activar: bool):
    try:
        if activar:
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            script_path = os.path.abspath(__file__)
            vbs_content = f'CreateObject("Wscript.Shell").Run """{pythonw}"" ""{script_path}"" --tray", 0, False\n'
            os.makedirs(CARPETA_STARTUP, exist_ok=True)
            with open(ACCESO_STARTUP_VBS, "w", encoding="utf-8") as f:
                f.write(vbs_content)
        else:
            if os.path.exists(ACCESO_STARTUP_VBS):
                os.remove(ACCESO_STARTUP_VBS)
        return True
    except Exception:
        return False


# ==========================================
# BLOQUE 2: GESTIÓN DE DATOS (JSON)
# ==========================================
def cargar_configuracion():
    global tema_actual
    if os.path.exists(ARCHIVO_CONFIG):
        try:
            with open(ARCHIVO_CONFIG, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                tema_actual = cfg.get("tema", "Obsidian")
                nombre = cfg.get("nombre")
                if nombre:
                    return nombre
        except Exception:
            pass

    dialogo = ctk.CTkInputDialog(
        text="¿Cómo te llamas?", title="Bienvenido a tu To-Do List"
    )
    nombre_ingresado = dialogo.get_input()
    nombre_final = (
        nombre_ingresado.strip()
        if (nombre_ingresado and nombre_ingresado.strip())
        else "Koke"
    )

    with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(
            {"nombre": nombre_final, "tema": "Obsidian"},
            f,
            indent=4,
            ensure_ascii=False,
        )

    return nombre_final


def cargar_tareas():
    global tareas
    if os.path.exists(ARCHIVO_TAREAS):
        try:
            with open(ARCHIVO_TAREAS, "r", encoding="utf-8") as f:
                datos = json.load(f)
                tareas.clear()
                for item in datos:
                    if "id" not in item:
                        item["id"] = uuid.uuid4().hex[:8]
                    tareas.append(item)
        except Exception:
            tareas.clear()
    else:
        tareas.clear()


def guardar_tareas():
    with open(ARCHIVO_TAREAS, "w", encoding="utf-8") as f:
        json.dump(tareas, f, indent=4, ensure_ascii=False)


def agregar_tarea(nombre, fecha, hora="", anticipacion=0):
    nueva_tarea = {
        "id": uuid.uuid4().hex[:8],
        "nombre": nombre,
        "categoria": "General",
        "fecha": fecha,
        "hora": hora,
        "anticipacion": anticipacion,
        "completada": False,
        "notificado": False,
    }
    tareas.append(nueva_tarea)
    guardar_tareas()
    return nueva_tarea


def alternar_tarea(tarea_id):
    for t in tareas:
        if t.get("id") == tarea_id:
            t["completada"] = not t["completada"]
            guardar_tareas()
            break


def eliminar_tarea(tarea_id):
    global tareas
    tareas = [t for t in tareas if t.get("id") != tarea_id]
    guardar_tareas()


# ==========================================
# POPUP CONTEXTUAL: PRIORIDADES Y ELIMINAR
# ==========================================
def mostrar_popup_eliminar(event, task):
    """Muestra un popup minimalista flotante con selector de prioridad y opción de eliminar."""
    global popup_eliminar_activo
    if popup_eliminar_activo:
        try:
            popup_eliminar_activo.destroy()
        except Exception:
            pass
        popup_eliminar_activo = None

    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    popup = ctk.CTkToplevel(app)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup_eliminar_activo = popup

    ancho_p, alto_p = 168, 92
    x = min(event.x_root, app.winfo_screenwidth() - ancho_p - 10)
    y = min(event.y_root, app.winfo_screenheight() - alto_p - 10)
    popup.geometry(f"{ancho_p}x{alto_p}+{x}+{y}")
    popup.configure(fg_color=t["bg_card"])

    marco = ctk.CTkFrame(
        popup,
        fg_color=t["bg_card"],
        border_width=1,
        border_color=t.get("border_card", "#2C2C2C"),
        corner_radius=8,
    )
    marco.pack(fill="both", expand=True, padx=2, pady=2)

    # Selector de Prioridad (Rojo / Amarillo / Verde)
    ctk.CTkLabel(
        marco,
        text="Prioridad:",
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=10, weight="bold"),
        text_color=t["text_muted"],
    ).pack(anchor="w", padx=8, pady=(4, 2))

    fila_prio = ctk.CTkFrame(marco, fg_color="transparent")
    fila_prio.pack(fill="x", padx=6, pady=(0, 4))

    def cambiar_prioridad(prio_val):
        global popup_eliminar_activo
        if popup_eliminar_activo:
            try:
                popup_eliminar_activo.destroy()
            except Exception:
                pass
            popup_eliminar_activo = None
        task["prioridad"] = prio_val
        guardar_tareas()
        actualizar_lista()

    prio_actual = task.get("prioridad", "verde")

    btn_rojo = ctk.CTkButton(
        fila_prio,
        text="🔴 Alta",
        width=46,
        height=22,
        corner_radius=5,
        fg_color="#3B151A" if prio_actual == "rojo" else "transparent",
        hover_color="#501820",
        border_width=1 if prio_actual == "rojo" else 0,
        border_color="#EF4444",
        text_color="#F87171",
        font=ctk.CTkFont(size=10, weight="bold"),
        command=lambda: cambiar_prioridad("rojo"),
    )
    btn_rojo.pack(side="left", padx=1, expand=True, fill="x")
    btn_rojo.bind("<Button-1>", lambda e: cambiar_prioridad("rojo"))

    btn_amarillo = ctk.CTkButton(
        fila_prio,
        text="🟡 Med",
        width=46,
        height=22,
        corner_radius=5,
        fg_color="#38250B" if prio_actual == "amarillo" else "transparent",
        hover_color="#4D320E",
        border_width=1 if prio_actual == "amarillo" else 0,
        border_color="#F59E0B",
        text_color="#FBBF24",
        font=ctk.CTkFont(size=10, weight="bold"),
        command=lambda: cambiar_prioridad("amarillo"),
    )
    btn_amarillo.pack(side="left", padx=1, expand=True, fill="x")
    btn_amarillo.bind("<Button-1>", lambda e: cambiar_prioridad("amarillo"))

    btn_verde = ctk.CTkButton(
        fila_prio,
        text="🟢 Normal",
        width=46,
        height=22,
        corner_radius=5,
        fg_color="#0F291E" if prio_actual == "verde" else "transparent",
        hover_color="#14382A",
        border_width=1 if prio_actual == "verde" else 0,
        border_color="#10B981",
        text_color="#34D399",
        font=ctk.CTkFont(size=10, weight="bold"),
        command=lambda: cambiar_prioridad("verde"),
    )
    btn_verde.pack(side="left", padx=1, expand=True, fill="x")
    btn_verde.bind("<Button-1>", lambda e: cambiar_prioridad("verde"))

    # Separador horizontal sutil
    ctk.CTkFrame(marco, height=1, fg_color=t.get("border_card", "#2C2C2C")).pack(
        fill="x", padx=6, pady=2
    )

    def accion_eliminar(e=None):
        global popup_eliminar_activo
        if popup_eliminar_activo:
            try:
                popup_eliminar_activo.destroy()
            except Exception:
                pass
            popup_eliminar_activo = None
        tid = task.get("id")
        eliminar_tarea(tid)
        actualizar_lista()

    btn_del = ctk.CTkButton(
        marco,
        text="🗑️  Eliminar tarea",
        height=24,
        corner_radius=5,
        fg_color="transparent",
        hover_color="#374151",
        text_color=t.get("badge_alert", "#F87171"),
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
        command=accion_eliminar,
    )
    btn_del.pack(fill="x", padx=4, pady=(1, 3))
    btn_del.bind("<Button-1>", accion_eliminar)

    def verificar_click_fuera(e):
        global popup_eliminar_activo
        if not popup_eliminar_activo:
            return
        try:
            px = popup_eliminar_activo.winfo_rootx()
            py = popup_eliminar_activo.winfo_rooty()
            pw = popup_eliminar_activo.winfo_width()
            ph = popup_eliminar_activo.winfo_height()
            if not (px <= e.x_root <= px + pw and py <= e.y_root <= py + ph):
                popup_eliminar_activo.destroy()
                popup_eliminar_activo = None
        except Exception:
            pass

    app.bind_all("<Button-1>", verificar_click_fuera, add="+")
    popup.bind("<Escape>", lambda e: popup.destroy())


# ==========================================
# CALENDARIO INTERACTIVO (POPUP)
# ==========================================
def abrir_selector_calendario(callback, fecha_inicial=None):
    """Muestra un calendario interactivo en un popup para seleccionar cualquier día."""
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    cal_modal = ctk.CTkToplevel(app)
    cal_modal.title("Seleccionar Fecha")
    cal_modal.transient(app)
    cal_modal.attributes("-topmost", True)
    cal_modal.grab_set()

    ancho_c, alto_c = 300, 320
    pos_x = max(10, app.winfo_x() + int((app.winfo_width() - ancho_c) / 2))
    pos_y = max(10, app.winfo_y() + int((app.winfo_height() - alto_c) / 2))
    cal_modal.geometry(f"{ancho_c}x{alto_c}+{pos_x}+{pos_y}")
    cal_modal.configure(fg_color=t["bg_card"])
    cal_modal.resizable(False, False)

    try:
        dt_ini = (
            datetime.strptime(fecha_inicial, "%Y-%m-%d").date()
            if fecha_inicial
            else datetime.now().date()
        )
    except Exception:
        dt_ini = datetime.now().date()

    estado_cal = {
        "anio": dt_ini.year,
        "mes": dt_ini.month,
        "sel": dt_ini,
    }

    frame_nav = ctk.CTkFrame(cal_modal, fg_color="transparent")
    frame_nav.pack(fill="x", padx=12, pady=(10, 4))

    def cambiar_mes(delta):
        nuevo_mes = estado_cal["mes"] + delta
        if nuevo_mes > 12:
            estado_cal["anio"] += 1
            estado_cal["mes"] = 1
        elif nuevo_mes < 1:
            estado_cal["anio"] -= 1
            estado_cal["mes"] = 12
        else:
            estado_cal["mes"] = nuevo_mes
        renderizar_mes()

    btn_ant = ctk.CTkButton(
        frame_nav,
        text="◀",
        width=28,
        height=26,
        corner_radius=5,
        fg_color=t["bg_app"],
        text_color=t["text_main"],
        hover_color=t["border_card"],
        command=lambda: cambiar_mes(-1),
    )
    btn_ant.pack(side="left")

    lbl_mes_anio = ctk.CTkLabel(
        frame_nav,
        text="",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
        text_color=t["text_main"],
    )
    lbl_mes_anio.pack(side="left", expand=True)

    btn_sig = ctk.CTkButton(
        frame_nav,
        text="▶",
        width=28,
        height=26,
        corner_radius=5,
        fg_color=t["bg_app"],
        text_color=t["text_main"],
        hover_color=t["border_card"],
        command=lambda: cambiar_mes(1),
    )
    btn_sig.pack(side="right")

    frame_dias_sem = ctk.CTkFrame(cal_modal, fg_color="transparent")
    frame_dias_sem.pack(fill="x", padx=10, pady=(4, 2))
    dias_cortos = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
    for dc in dias_cortos:
        ctk.CTkLabel(
            frame_dias_sem,
            text=dc,
            width=38,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=t["text_muted"],
        ).pack(side="left", padx=1)

    frame_grid = ctk.CTkFrame(cal_modal, fg_color="transparent")
    frame_grid.pack(padx=10, pady=(2, 6))

    def elegir_dia(dia_num):
        f_res = f"{estado_cal['anio']:04d}-{estado_cal['mes']:02d}-{dia_num:02d}"
        callback(f_res)
        cal_modal.destroy()

    hoy_real = datetime.now().date()

    def renderizar_mes():
        for w in frame_grid.winfo_children():
            w.destroy()

        nom_m = MESES_ESPANOL[estado_cal["mes"]]
        lbl_mes_anio.configure(text=f"{nom_m.upper()} {estado_cal['anio']}")

        semanas = calendar.monthcalendar(estado_cal["anio"], estado_cal["mes"])
        color_acento = "#10B981" if tema_actual != "Hello Kitty" else "#EC4899"

        for sem in semanas:
            f_fila = ctk.CTkFrame(frame_grid, fg_color="transparent")
            f_fila.pack(pady=1)
            for d in sem:
                if d == 0:
                    lbl_espacio = ctk.CTkLabel(f_fila, text="", width=38, height=24)
                    lbl_espacio.pack(side="left", padx=1)
                else:
                    es_hoy = (
                        estado_cal["anio"] == hoy_real.year
                        and estado_cal["mes"] == hoy_real.month
                        and d == hoy_real.day
                    )
                    es_sel = (
                        estado_cal["anio"] == estado_cal["sel"].year
                        and estado_cal["mes"] == estado_cal["sel"].month
                        and d == estado_cal["sel"].day
                    )

                    fg_b = (
                        color_acento
                        if es_sel
                        else ("transparent" if not es_hoy else t["border_card"])
                    )
                    txt_b = (
                        "#FFFFFF"
                        if es_sel
                        else (color_acento if es_hoy else t["text_main"])
                    )

                    b_dia = ctk.CTkButton(
                        f_fila,
                        text=str(d),
                        width=38,
                        height=24,
                        corner_radius=6,
                        fg_color=fg_b,
                        text_color=txt_b,
                        hover_color=t["border_card"],
                        font=ctk.CTkFont(
                            size=11, weight="bold" if (es_hoy or es_sel) else "normal"
                        ),
                        command=lambda dn=d: elegir_dia(dn),
                    )
                    b_dia.pack(side="left", padx=1)

    renderizar_mes()

    btn_hoy = ctk.CTkButton(
        cal_modal,
        text="📅 Ir a Hoy",
        height=26,
        corner_radius=6,
        fg_color=t["bg_app"],
        text_color=t["text_muted"],
        hover_color=t["border_card"],
        font=ctk.CTkFont(size=11),
        command=lambda: (
            callback(hoy_real.strftime("%Y-%m-%d")),
            cal_modal.destroy(),
        ),
    )
    btn_hoy.pack(fill="x", padx=16, pady=(2, 8))


# ==========================================
# VENTANA DE HISTORIAL DE COMPLETADAS (POR MES Y DÍA)
# ==========================================
def abrir_ventana_completadas():
    """Abre la ventana dedicada a tareas completadas organizadas por mes y día."""
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    ventana_comp = ctk.CTkToplevel(app)
    ventana_comp.title("Historial de Tareas Completadas")
    ventana_comp.transient(app)
    ventana_comp.attributes("-topmost", True)

    ancho_vc, alto_vc = 420, 580
    pos_x = max(10, app.winfo_x() + int((app.winfo_width() - ancho_vc) / 2))
    pos_y = max(10, app.winfo_y() + int((app.winfo_height() - alto_vc) / 2))
    ventana_comp.geometry(f"{ancho_vc}x{alto_vc}+{pos_x}+{pos_y}")
    ventana_comp.configure(fg_color=t["bg_app"])

    head = ctk.CTkFrame(ventana_comp, fg_color="transparent")
    head.pack(fill="x", padx=18, pady=(16, 8))

    tareas_comp = [tk for tk in tareas if tk.get("completada")]
    total_comp = len(tareas_comp)

    ctk.CTkLabel(
        head,
        text="✓ Tareas Completadas",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=16, weight="bold"),
        text_color=t.get("badge_ok", "#34D399"),
    ).pack(side="left")

    lbl_badge_top = ctk.CTkLabel(
        head,
        text=f"{total_comp} lista{'s' if total_comp != 1 else ''}",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=t["text_muted"],
    )
    lbl_badge_top.pack(side="right")

    scroll_comp = ctk.CTkScrollableFrame(
        ventana_comp,
        fg_color=t["bg_app"],
        corner_radius=12,
    )
    scroll_comp.pack(fill="both", expand=True, padx=14, pady=(4, 10))

    if not tareas_comp:
        ctk.CTkLabel(
            scroll_comp,
            text="Aún no has completado tareas ✨",
            font=ctk.CTkFont(size=13),
            text_color=t["text_muted"],
        ).pack(pady=70)
        return

    # Agrupar por mes y luego por día
    meses_comp = {}
    for tk in tareas_comp:
        f_str = tk.get("fecha", "")
        try:
            dt_f = datetime.strptime(f_str, "%Y-%m-%d").date()
            clave_m = dt_f.strftime("%Y-%m")
            nom_m = MESES_ESPANOL[dt_f.month].upper()
            nombre_m = f"{nom_m} {dt_f.year}"
        except Exception:
            clave_m = "9999-99"
            nombre_m = "OTRAS FECHAS"

        if clave_m not in meses_comp:
            meses_comp[clave_m] = {"nombre": nombre_m, "dias": {}}

        if f_str not in meses_comp[clave_m]["dias"]:
            etiqueta_d, _ = obtener_etiqueta_dinamica(f_str)
            meses_comp[clave_m]["dias"][f_str] = {
                "etiqueta": etiqueta_d.replace("⚠️ ", "")
                .replace(" (Atrasado)", "")
                .replace("Hoy • ", "")
                .replace("Mañana • ", ""),
                "tareas": [],
            }
        meses_comp[clave_m]["dias"][f_str]["tareas"].append(tk)

    for clave_m, d_mes in sorted(meses_comp.items(), key=lambda x: x[0], reverse=True):
        banner_m = ctk.CTkFrame(scroll_comp, fg_color="transparent")
        banner_m.pack(fill="x", pady=(10, 4), padx=2)

        ctk.CTkLabel(
            banner_m,
            text=f"🗓️ {d_mes['nombre']}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=t["text_main"],
        ).pack(side="left", padx=(4, 8))

        ctk.CTkFrame(banner_m, height=1, fg_color=t["border_card"]).pack(
            side="left", fill="x", expand=True, padx=(4, 8)
        )

        for f_dia, d_dia in sorted(
            d_mes["dias"].items(), key=lambda x: x[0], reverse=True
        ):
            secc_d = ctk.CTkFrame(
                scroll_comp,
                fg_color=t["bg_card"],
                corner_radius=10,
                border_width=1,
                border_color=t["border_card"],
            )
            secc_d.pack(fill="x", pady=4, padx=4)

            h_d = ctk.CTkFrame(secc_d, fg_color="transparent")
            h_d.pack(fill="x", padx=10, pady=(6, 4))
            ctk.CTkLabel(
                h_d,
                text=d_dia["etiqueta"],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=t["text_muted"],
            ).pack(side="left")

            for task in d_dia["tareas"]:
                caps = ctk.CTkFrame(
                    secc_d,
                    fg_color=t["bg_input"],
                    corner_radius=8,
                    border_width=1,
                    border_color=t["border_input"],
                    cursor="hand2",
                )
                caps.pack(fill="x", pady=2, padx=6)

                tid = task.get("id")

                def desmarcar(tid_val=tid):
                    alternar_tarea(tid_val)
                    actualizar_lista()
                    ventana_comp.destroy()
                    abrir_ventana_completadas()

                cb = ctk.CTkCheckBox(
                    caps,
                    text="",
                    width=20,
                    checkbox_width=18,
                    checkbox_height=18,
                    corner_radius=9,
                    fg_color="#10B981" if tema_actual != "Hello Kitty" else "#EC4899",
                    command=desmarcar,
                )
                cb.select()
                cb.pack(side="left", padx=(8, 4), pady=6)

                lbl_t = ctk.CTkLabel(
                    caps,
                    text=task.get("nombre", ""),
                    anchor="w",
                    justify="left",
                    wraplength=260,
                    text_color="#6B7280",
                    font=ctk.CTkFont(size=12, slant="italic"),
                )
                lbl_t.pack(side="left", fill="x", expand=True, padx=4, pady=6)

                caps.bind(
                    "<Button-3>",
                    lambda event, tk_item=task: mostrar_popup_eliminar(event, tk_item),
                )
                lbl_t.bind(
                    "<Button-3>",
                    lambda event, tk_item=task: mostrar_popup_eliminar(event, tk_item),
                )


# ==========================================
# BLOQUE 3: LÓGICA DE VISTA Y CONTROLADORES
# ==========================================
def obtener_imagen_tenue(ruta_img, opacidad=0.18, tamano=(200, 200)):
    if not ruta_img or not os.path.exists(ruta_img):
        return None
    try:
        img = Image.open(ruta_img).convert("RGBA")
        img = img.resize(tamano, Image.Resampling.LANCZOS)
        r, g, b, a = img.split()
        a = a.point(lambda p: int(p * opacidad))
        img.putalpha(a)
        return ctk.CTkImage(light_image=img, dark_image=img, size=tamano)
    except Exception:
        return None


def mostrar_alerta_modal(tarea_nombre, detalle_hora, tarea=None):
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass

    modal_alerta = ctk.CTkToplevel()
    modal_alerta.title("¡RECORDATORIO!")
    modal_alerta.attributes("-topmost", True)

    ancho_a, alto_a = 340, 240
    sw = modal_alerta.winfo_screenwidth()
    sh = modal_alerta.winfo_screenheight()
    pos_x = max(10, int((sw - ancho_a) / 2))
    pos_y = max(10, int((sh - alto_a) / 2))
    modal_alerta.geometry(f"{ancho_a}x{alto_a}+{pos_x}+{pos_y}")
    modal_alerta.resizable(False, False)

    if tema_actual == "Hello Kitty":
        bg_banner = "#E11D48"
        bg_card = "#FCE7F3"
        txt_main = "#831843"
        txt_sub = "#500724"
        btn_bg = "#EC4899"
        btn_hover = "#DB2777"
        btn_txt = "#FFFFFF"
    else:
        bg_banner = "#10B981"
        bg_card = "#161920"
        txt_main = "#F9FAFB"
        txt_sub = "#9CA3AF"
        btn_bg = "#10B981"
        btn_hover = "#059669"
        btn_txt = "#FFFFFF"

    modal_alerta.configure(fg_color=bg_card)

    banner = ctk.CTkFrame(modal_alerta, fg_color=bg_banner, height=36, corner_radius=0)
    banner.pack(fill="x")
    ctk.CTkLabel(
        banner,
        text="🔔  ¡RECORDATORIO!",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
        text_color="#FFFFFF",
    ).pack(pady=7)

    cuerpo = ctk.CTkFrame(modal_alerta, fg_color="transparent")
    cuerpo.pack(fill="both", expand=True, padx=18, pady=8)

    ctk.CTkLabel(
        cuerpo,
        text=tarea_nombre,
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=15, weight="bold"),
        text_color=txt_main,
        wraplength=300,
        justify="center",
    ).pack(expand=True)

    ctk.CTkLabel(
        cuerpo,
        text=detalle_hora,
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=11),
        text_color=txt_sub,
    ).pack(pady=(0, 6))

    fila_botones = ctk.CTkFrame(modal_alerta, fg_color="transparent")
    fila_botones.pack(fill="x", padx=16, pady=(0, 14))

    def marcar_lista():
        if tarea:
            tarea["completada"] = True
            guardar_tareas()
            actualizar_lista()
        modal_alerta.destroy()

    def posponer_5():
        if tarea:
            ahora_m5 = datetime.now() + timedelta(minutes=5)
            tarea["hora"] = ahora_m5.strftime("%H:%M")
            tarea["fecha"] = ahora_m5.strftime("%Y-%m-%d")
            tarea["notificado"] = False
            guardar_tareas()
            actualizar_lista()
        modal_alerta.destroy()

    if tarea:
        ctk.CTkButton(
            fila_botones,
            text="✓ Lista",
            width=80,
            height=32,
            corner_radius=8,
            fg_color=btn_bg,
            hover_color=btn_hover,
            text_color=btn_txt,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=marcar_lista,
        ).pack(side="left", padx=(0, 6), expand=True, fill="x")

        ctk.CTkButton(
            fila_botones,
            text="💤 +5 min",
            width=85,
            height=32,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#F3F4F6",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=posponer_5,
        ).pack(side="left", padx=(0, 6), expand=True, fill="x")

    ctk.CTkButton(
        fila_botones,
        text="Cerrar",
        width=70,
        height=32,
        corner_radius=8,
        fg_color="transparent",
        hover_color="#2D333E",
        text_color=txt_sub,
        font=ctk.CTkFont(size=11),
        command=modal_alerta.destroy,
    ).pack(side="left", expand=True, fill="x")


def lanzar_notificacion(titulo, mensaje, tarea=None):
    if HAY_PLYER:
        try:
            notification.notify(
                title=titulo,
                message=mensaje,
                app_name="To-Do List",
                timeout=10,
            )
        except Exception:
            pass

    # SOLO muestra el popup del recordatorio (NO restaura la ventana principal)
    mostrar_alerta_modal(
        titulo.replace("🔔 ", "").replace("⏰ ", ""),
        mensaje,
        tarea=tarea,
    )


# ==========================================
# SISTEMA DE AUTO-ACTUALIZACIÓN
# ==========================================
def mostrar_modal_actualizacion(info_update):
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    modal = ctk.CTkToplevel()
    modal.title("Actualización disponible")
    modal.attributes("-topmost", True)
    ancho, alto = 340, 260
    sw = modal.winfo_screenwidth()
    sh = modal.winfo_screenheight()
    modal.geometry(f"{ancho}x{alto}+{int((sw-ancho)/2)}+{int((sh-alto)/2)}")
    modal.configure(fg_color=t["bg_card"])
    modal.resizable(False, False)

    v_remota = info_update.get("version", "Nueva")
    novedades = info_update.get("novedades", "• Mejoras generales y correcciones.")
    url_descarga = info_update.get("url_descarga", "")

    banner = ctk.CTkFrame(
        modal,
        fg_color="#10B981" if tema_actual != "Hello Kitty" else "#EC4899",
        height=38,
        corner_radius=0,
    )
    banner.pack(fill="x")
    ctk.CTkLabel(
        banner,
        text=f"🚀  ¡Nueva versión {v_remota} disponible!",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
        text_color="#FFFFFF",
    ).pack(pady=8)

    cuerpo = ctk.CTkFrame(modal, fg_color="transparent")
    cuerpo.pack(fill="both", expand=True, padx=18, pady=10)

    ctk.CTkLabel(
        cuerpo,
        text=f"Tu versión actual es v{VERSION_ACTUAL}. Novedades:",
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
        text_color=t["text_main"],
        anchor="w",
    ).pack(fill="x")

    lbl_nov = ctk.CTkLabel(
        cuerpo,
        text=novedades,
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=11),
        text_color=t["text_muted"],
        justify="left",
        anchor="w",
        wraplength=300,
    )
    lbl_nov.pack(fill="x", pady=(4, 8))

    def descargar():
        if url_descarga:
            webbrowser.open(url_descarga)
        modal.destroy()

    ctk.CTkButton(
        modal,
        text="📥 Descargar actualización",
        height=32,
        corner_radius=8,
        fg_color="#10B981" if tema_actual != "Hello Kitty" else "#EC4899",
        hover_color="#059669" if tema_actual != "Hello Kitty" else "#DB2777",
        font=ctk.CTkFont(size=12, weight="bold"),
        command=descargar,
    ).pack(fill="x", padx=18, pady=(0, 6))

    ctk.CTkButton(
        modal,
        text="Más tarde",
        height=26,
        corner_radius=8,
        fg_color="transparent",
        hover_color=t["border_card"],
        text_color=t["text_muted"],
        font=ctk.CTkFont(size=11),
        command=modal.destroy,
    ).pack(fill="x", padx=18, pady=(0, 12))


def _modal_aviso_info(titulo, mensaje):
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    m = ctk.CTkToplevel()
    m.title(titulo)
    m.attributes("-topmost", True)
    ancho, alto = 280, 140
    sw = m.winfo_screenwidth()
    sh = m.winfo_screenheight()
    m.geometry(f"{ancho}x{alto}+{int((sw-ancho)/2)}+{int((sh-alto)/2)}")
    m.configure(fg_color=t["bg_card"])
    m.resizable(False, False)

    ctk.CTkLabel(
        m,
        text=titulo,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=t["text_main"],
    ).pack(pady=(16, 6))
    ctk.CTkLabel(
        m,
        text=mensaje,
        font=ctk.CTkFont(size=11),
        text_color=t["text_muted"],
        wraplength=240,
        justify="center",
    ).pack(pady=(0, 12))
    ctk.CTkButton(
        m,
        text="Entendido",
        height=28,
        corner_radius=6,
        command=m.destroy,
        fg_color="#374151",
    ).pack(padx=20)


def parse_version(v):
    try:
        return [int(x) for x in str(v).strip().lstrip("v").split(".")]
    except Exception:
        return [0, 0, 0]


def verificar_actualizaciones(mostrar_si_al_dia=False):
    def _tarea_check():
        url_version = "https://raw.githubusercontent.com/KokeVazquez/ToDo/main/version.json"
        try:
            req = urllib.request.Request(
                url_version, headers={"User-Agent": "KokeToDo-App"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    remota = data.get("version", "1.0.0")
                    if parse_version(remota) > parse_version(VERSION_ACTUAL):
                        app.after(0, lambda: mostrar_modal_actualizacion(data))
                    elif mostrar_si_al_dia:
                        app.after(
                            0,
                            lambda: _modal_aviso_info(
                                "Estás al día ✨",
                                f"Tienes la versión más reciente (v{VERSION_ACTUAL}).",
                            ),
                        )
        except Exception:
            if mostrar_si_al_dia:
                app.after(
                    0,
                    lambda: _modal_aviso_info(
                        "Sin conexión",
                        "No se pudo comprobar si hay actualizaciones en este momento.",
                    ),
                )

    threading.Thread(target=_tarea_check, daemon=True).start()


def verificar_recordatorios():
    ahora = datetime.now()
    hoy_actual = ahora.date()

    if hoy_actual != ultimo_dia_verificado["dia"]:
        ultimo_dia_verificado["dia"] = hoy_actual
        actualizar_boton_calendario_principal()
        actualizar_lista()

    cambio = False

    for t in tareas:
        if t.get("completada") or t.get("notificado") or not t.get("hora"):
            continue

        try:
            fecha_t = t.get("fecha")
            hora_t = t.get("hora")
            dt_tarea = datetime.strptime(f"{fecha_t} {hora_t}", "%Y-%m-%d %H:%M")
            anticipo = int(t.get("anticipacion", 0))
            dt_alerta = dt_tarea - timedelta(minutes=anticipo)

            if ahora >= dt_alerta:
                t["notificado"] = True
                cambio = True

                detalle = (
                    f"Faltan {anticipo} min ({hora_t})"
                    if anticipo > 0
                    else f"Programada para las {hora_t}"
                )
                lanzar_notificacion(
                    f"🔔 {t['nombre']}",
                    detalle,
                    tarea=t,
                )
        except Exception:
            pass

    if cambio:
        guardar_tareas()

    app.after(5000, verificar_recordatorios)


def aplicar_tema(nombre_tema):
    global tema_actual, nombre_usuario
    if nombre_tema not in TEMAS:
        return
    tema_actual = nombre_tema
    t = TEMAS[tema_actual]

    app.configure(fg_color=t["bg_app"])

    prefijo = "🎀 " if nombre_tema == "Hello Kitty" else ""
    lbl_titulo.configure(
        text=f"{prefijo}¡Hola, {nombre_usuario}!", text_color=t["text_main"]
    )

    btn_ajustes.configure(
        text_color=t["text_muted"],
        hover_color=t["border_card"],
    )

    marco_input.configure(
        fg_color=t["bg_input"], border_color=t["border_input"], border_width=2
    )
    macro_tareas.configure(fg_color=t["bg_app"])

    btn_calendario.configure(
        fg_color=t["bg_card"],
        hover_color=t["border_card"],
        text_color=t["text_main"],
    )

    entrada_tarea.configure(
        fg_color=t["bg_card"],
        text_color=t["text_main"],
        placeholder_text_color=t.get("placeholder", "#9CA3AF"),
    )

    actualizar_boton_hora()

    if nombre_tema == "Hello Kitty":
        lbl_watermark.pack(side="left", expand=True)
    else:
        lbl_watermark.pack_forget()

    if "btn_buscar" in globals():
        btn_buscar.configure(
            text_color=t.get("accent", "#60A5FA") if busqueda_activa else t["text_muted"],
            hover_color=t.get("border_card", "#1F232B"),
        )
    if "marco_busqueda" in globals():
        marco_busqueda.configure(
            fg_color=t["bg_card"],
            border_color=t.get("border_card", "#2C2C2C"),
        )
        entrada_busqueda.configure(
            text_color=t["text_main"],
            placeholder_text_color=t.get("placeholder", "#9CA3AF"),
        )
        btn_cerrar_busqueda.configure(
            text_color=t["text_muted"],
            hover_color=t.get("border_card", "#1F232B"),
        )

    try:
        import ctypes

        hwnd = ctypes.windll.user32.GetParent(app.winfo_id())
        hex_c = t["bg_app"].lstrip("#")
        r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        color_bgr = (b << 16) | (g << 8) | r
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(ctypes.c_int(color_bgr)), 4
        )
    except Exception:
        pass

    actualizar_lista()


def actualizar_boton_hora():
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    if recordatorio_actual["hora"]:
        btn_hora.configure(
            text=f"⏰ {recordatorio_actual['hora']}",
            text_color="#10B981" if tema_actual != "Hello Kitty" else "#E11D48",
            fg_color=t["border_card"],
        )
    else:
        btn_hora.configure(
            text="⏰",
            text_color=t["text_muted"],
            fg_color="transparent",
        )


def actualizar_boton_calendario_principal():
    btn_calendario.configure(
        text=obtener_texto_boton_fecha(fecha_seleccionada_nueva["iso"])
    )


def click_calendario_principal():
    def al_elegir(f_nueva):
        fecha_seleccionada_nueva["iso"] = f_nueva
        actualizar_boton_calendario_principal()

    abrir_selector_calendario(al_elegir, fecha_seleccionada_nueva["iso"])


def abrir_modal_edicion(tarea_a_editar=None):
    """Abre el modal para editar texto, fecha (con calendario), hora y anticipación."""
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    modal = ctk.CTkToplevel(app)
    modal.title("Editar Recordatorio" if tarea_a_editar else "Definir Hora")
    modal.transient(app)
    modal.attributes("-topmost", True)
    modal.grab_set()

    ancho_m = 320
    alto_m = 520 if tarea_a_editar else 420
    pos_x = max(10, app.winfo_x() + int((app.winfo_width() - ancho_m) / 2))
    pos_y = max(10, app.winfo_y() + int((app.winfo_height() - alto_m) / 2))
    modal.geometry(f"{ancho_m}x{alto_m}+{pos_x}+{pos_y}")
    modal.configure(fg_color=t["bg_card"])
    modal.resizable(False, False)

    titulo_modal = "✏️ Modificar Tarea" if tarea_a_editar else "⏰ Definir Hora"
    ctk.CTkLabel(
        modal,
        text=titulo_modal,
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=15, weight="bold"),
        text_color=t["text_main"],
    ).pack(pady=(12, 6))

    entry_nombre_edicion = None
    if tarea_a_editar:
        ctk.CTkLabel(
            modal,
            text="Nombre de la tarea:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=t["text_muted"],
        ).pack(anchor="w", padx=24, pady=(2, 2))

        entry_nombre_edicion = ctk.CTkEntry(
            modal,
            height=32,
            corner_radius=7,
            fg_color=t["bg_app"],
            text_color=t["text_main"],
            border_color=t["border_card"],
            border_width=1,
            font=ctk.CTkFont(size=12),
        )
        entry_nombre_edicion.insert(0, tarea_a_editar.get("nombre", ""))
        entry_nombre_edicion.pack(fill="x", padx=24, pady=(0, 6))

    ahora_dt = datetime.now()
    hora_inicial = (
        tarea_a_editar.get("hora", "")
        if tarea_a_editar
        else recordatorio_actual["hora"]
    )

    if hora_inicial:
        try:
            dt_p = datetime.strptime(hora_inicial, "%H:%M")
            h_24, m_val = dt_p.hour, dt_p.minute
        except Exception:
            h_24, m_val = ahora_dt.hour, ahora_dt.minute
    else:
        h_24, m_val = ahora_dt.hour, ahora_dt.minute

    periodo_actual = "PM" if h_24 >= 12 else "AM"
    h_12 = h_24 % 12
    h_12 = 12 if h_12 == 0 else h_12

    sel_h = {"val": h_12}
    sel_m = {"val": m_val}
    sel_p = {"val": periodo_actual}

    frame_pickers = ctk.CTkFrame(modal, fg_color="transparent")
    frame_pickers.pack(pady=4)

    f_h = ctk.CTkScrollableFrame(
        frame_pickers,
        width=58,
        height=85,
        fg_color=t["bg_app"],
        corner_radius=6,
    )
    f_h.pack(side="left", padx=3)

    btns_h = {}

    def seleccionar_h(val):
        sel_h["val"] = val
        for v, b in btns_h.items():
            es_sel = v == val
            b.configure(
                fg_color=(t["border_input"] if es_sel else "transparent"),
                text_color=(
                    "#FFFFFF"
                    if es_sel and tema_actual != "Hello Kitty"
                    else (t["text_main"] if es_sel else t["text_muted"])
                ),
            )

    for h in range(1, 13):
        btn = ctk.CTkButton(
            f_h,
            text=f"{h:02d}",
            width=38,
            height=22,
            corner_radius=4,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda v=h: seleccionar_h(v),
        )
        btn.pack(pady=1)
        btns_h[h] = btn

    ctk.CTkLabel(
        frame_pickers,
        text=":",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=t["text_main"],
    ).pack(side="left", padx=1)

    f_m = ctk.CTkScrollableFrame(
        frame_pickers,
        width=58,
        height=85,
        fg_color=t["bg_app"],
        corner_radius=6,
    )
    f_m.pack(side="left", padx=3)

    btns_m = {}

    def seleccionar_m(val):
        sel_m["val"] = val
        for v, b in btns_m.items():
            es_sel = v == val
            b.configure(
                fg_color=(t["border_input"] if es_sel else "transparent"),
                text_color=(
                    "#FFFFFF"
                    if es_sel and tema_actual != "Hello Kitty"
                    else (t["text_main"] if es_sel else t["text_muted"])
                ),
            )

    for m in range(60):
        btn = ctk.CTkButton(
            f_m,
            text=f"{m:02d}",
            width=44,
            height=22,
            corner_radius=4,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda v=m: seleccionar_m(v),
        )
        btn.pack(pady=1)
        btns_m[m] = btn

    f_p = ctk.CTkFrame(frame_pickers, fg_color="transparent")
    f_p.pack(side="left", padx=4)

    def cambiar_periodo(p):
        sel_p["val"] = p
        btn_am.configure(
            fg_color=(t["border_input"] if p == "AM" else t["bg_app"]),
            text_color=(t["text_main"] if p == "AM" else t["text_muted"]),
        )
        btn_pm.configure(
            fg_color=(t["border_input"] if p == "PM" else t["bg_app"]),
            text_color=(t["text_main"] if p == "PM" else t["text_muted"]),
        )

    btn_am = ctk.CTkButton(
        f_p,
        text="AM",
        width=38,
        height=26,
        corner_radius=5,
        font=ctk.CTkFont(size=11, weight="bold"),
        command=lambda: cambiar_periodo("AM"),
    )
    btn_am.pack(pady=(0, 4))

    btn_pm = ctk.CTkButton(
        f_p,
        text="PM",
        width=38,
        height=26,
        corner_radius=5,
        font=ctk.CTkFont(size=11, weight="bold"),
        command=lambda: cambiar_periodo("PM"),
    )
    btn_pm.pack()

    seleccionar_h(h_12)
    seleccionar_m(m_val)
    cambiar_periodo(periodo_actual)

    def auto_scroll():
        modal.update_idletasks()
        frac_h = max(0.0, min(1.0, (h_12 - 1) / 11))
        frac_m = max(0.0, min(1.0, m_val / 59))
        f_h._parent_canvas.yview_moveto(frac_h)
        f_m._parent_canvas.yview_moveto(frac_m)

    modal.after(20, auto_scroll)

    # SELECTOR DE FECHA CON CALENDARIO EN EL MODAL DE EDICIÓN
    fecha_edicion = {
        "iso": (
            tarea_a_editar.get("fecha", datetime.now().date().strftime("%Y-%m-%d"))
            if tarea_a_editar
            else fecha_seleccionada_nueva["iso"]
        )
    }

    if tarea_a_editar:
        ctk.CTkLabel(
            modal,
            text="Fecha programada:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=t["text_muted"],
        ).pack(anchor="w", padx=24, pady=(6, 2))

        def actualizar_txt_btn_edicion():
            btn_fecha_edicion.configure(
                text=obtener_texto_boton_fecha(fecha_edicion["iso"])
            )

        def click_cambiar_fecha_edicion():
            def al_elegir(f_nueva):
                fecha_edicion["iso"] = f_nueva
                actualizar_txt_btn_edicion()

            abrir_selector_calendario(al_elegir, fecha_edicion["iso"])

        btn_fecha_edicion = ctk.CTkButton(
            modal,
            text=obtener_texto_boton_fecha(fecha_edicion["iso"]),
            height=30,
            corner_radius=7,
            fg_color=t["bg_app"],
            text_color=t["text_main"],
            border_color=t["border_card"],
            border_width=1,
            hover_color=t["border_card"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=click_cambiar_fecha_edicion,
        )
        btn_fecha_edicion.pack(fill="x", padx=24, pady=(0, 6))

    ctk.CTkLabel(
        modal,
        text="Avisarme:",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=t["text_muted"],
    ).pack(anchor="w", padx=24, pady=(4, 2))

    opciones_anticipo = {
        "A la hora exacta": 0,
        "5 min antes": 5,
        "10 min antes": 10,
        "15 min antes": 15,
        "30 min antes": 30,
    }
    menu_aviso = ctk.CTkOptionMenu(
        modal,
        values=list(opciones_anticipo.keys()),
        height=28,
        fg_color=t["bg_app"],
        text_color=t["text_main"],
        dropdown_fg_color=t["bg_card"],
        dropdown_text_color=t["text_main"],
    )
    ant_val = (
        tarea_a_editar.get("anticipacion", 0)
        if tarea_a_editar
        else recordatorio_actual["anticipacion"]
    )
    for k, v in opciones_anticipo.items():
        if v == ant_val:
            menu_aviso.set(k)
            break
    menu_aviso.pack(fill="x", padx=24, pady=(0, 10))

    def aplicar():
        hora_calc = sel_h["val"]
        if sel_p["val"] == "PM" and hora_calc < 12:
            hora_calc += 12
        elif sel_p["val"] == "AM" and hora_calc == 12:
            hora_calc = 0

        h_final = f"{hora_calc:02d}:{sel_m['val']:02d}"
        ant_final = opciones_anticipo.get(menu_aviso.get(), 0)

        if tarea_a_editar:
            if entry_nombre_edicion:
                nuevo_nom = entry_nombre_edicion.get().strip()
                if nuevo_nom:
                    tarea_a_editar["nombre"] = nuevo_nom

            tarea_a_editar["hora"] = h_final
            tarea_a_editar["anticipacion"] = ant_final
            tarea_a_editar["notificado"] = False
            tarea_a_editar["fecha"] = fecha_edicion["iso"]

            guardar_tareas()
            actualizar_lista()
            modal.destroy()
            return

        recordatorio_actual["hora"] = h_final
        recordatorio_actual["anticipacion"] = ant_final
        actualizar_boton_hora()
        modal.destroy()

        texto = entrada_tarea.get().strip()
        if texto:
            agregar_tarea(
                texto,
                fecha_seleccionada_nueva["iso"],
                hora=h_final,
                anticipacion=ant_final,
            )
            entrada_tarea.delete(0, "end")
            recordatorio_actual["hora"] = ""
            recordatorio_actual["anticipacion"] = 0
            actualizar_boton_hora()
            fecha_seleccionada_nueva["iso"] = datetime.now().date().strftime("%Y-%m-%d")
            actualizar_boton_calendario_principal()
            actualizar_lista()

    def quitar_recordatorio():
        if tarea_a_editar:
            tarea_a_editar["hora"] = ""
            tarea_a_editar["anticipacion"] = 0
            tarea_a_editar["notificado"] = False
            guardar_tareas()
            actualizar_lista()
        else:
            recordatorio_actual["hora"] = ""
            recordatorio_actual["anticipacion"] = 0
            actualizar_boton_hora()
        modal.destroy()

    ctk.CTkButton(
        modal,
        text=(
            "Guardar Cambios"
            if tarea_a_editar
            else ("Guardar tarea" if entrada_tarea.get().strip() else "Fijar hora")
        ),
        height=34,
        corner_radius=8,
        fg_color="#10B981" if tema_actual != "Hello Kitty" else "#EC4899",
        hover_color="#059669" if tema_actual != "Hello Kitty" else "#DB2777",
        font=ctk.CTkFont(size=12, weight="bold"),
        command=aplicar,
    ).pack(fill="x", padx=24, pady=(0, 6))

    if hora_inicial:
        ctk.CTkButton(
            modal,
            text="Quitar hora",
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color=t["border_card"],
            text_color=t.get("badge_alert", "#F87171"),
            font=ctk.CTkFont(size=11),
            command=quitar_recordatorio,
        ).pack(fill="x", padx=24, pady=(0, 6))

    if tarea_a_editar:

        def borrar_desde_modal():
            modal.destroy()
            eliminar_tarea(tarea_a_editar.get("id"))
            actualizar_lista()

        ctk.CTkButton(
            modal,
            text="🗑️ Eliminar esta tarea",
            height=28,
            corner_radius=8,
            fg_color="transparent",
            hover_color=t["border_card"],
            text_color=t.get("badge_alert", "#F87171"),
            font=ctk.CTkFont(size=11, weight="bold"),
            command=borrar_desde_modal,
        ).pack(fill="x", padx=24, pady=(2, 10))


def obtener_etiqueta_dinamica(fecha_str):
    """Calcula la etiqueta del día en formato elegante."""
    hoy = datetime.now().date()
    try:
        f = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        dias_dif = (f - hoy).days
        nom_dia = DIAS_COMPLETOS[f.weekday()]
        nom_mes = MESES_ESPANOL[f.month]
        texto_fecha = f"{nom_dia} {f.day} de {nom_mes}"

        if dias_dif < 0:
            return f"⚠️ {texto_fecha} (Atrasado)", f.strftime("%Y-%m-%d")
        elif dias_dif == 0:
            return f"Hoy • {texto_fecha}", f.strftime("%Y-%m-%d")
        elif dias_dif == 1:
            return f"Mañana • {texto_fecha}", f.strftime("%Y-%m-%d")
        else:
            return texto_fecha, f.strftime("%Y-%m-%d")
    except Exception:
        return "Otras fechas", "9999-99-99"


def hacer_scroll_a_clave(clave):
    """Ajusta suavemente el scroll para mostrar el encabezado de la sección recién abierta."""
    app.update_idletasks()
    widget = widgets_dias.get(clave)
    if not widget:
        return
    try:
        if not widget.winfo_exists():
            return
        canvas = macro_tareas._parent_canvas
        bbox = canvas.bbox("all")
        if not bbox:
            return
        total_h = bbox[3] - bbox[1]
        if total_h <= 0:
            return

        canvas_y = canvas.canvasy(0)
        w_y = widget.winfo_rooty() - canvas.winfo_rooty() + canvas_y
        frac = max(0.0, min(1.0, (w_y - 8) / total_h))
        canvas.yview_moveto(frac)
    except Exception:
        pass


def alternar_mes(clave_mes):
    """Alterna el estado abierto/cerrado de un mes en el primer clic."""
    mes_actual_iso = datetime.now().strftime("%Y-%m")
    estado_defecto = clave_mes == mes_actual_iso
    estado_actual = meses_abiertos.get(clave_mes, estado_defecto)
    nuevo_estado = not estado_actual
    meses_abiertos[clave_mes] = nuevo_estado
    actualizar_lista()
    if nuevo_estado:
        app.after(50, lambda: hacer_scroll_a_clave(f"mes_{clave_mes}"))


def alternar_seccion(clave_orden, card_widget=None):
    """Alterna el estado abierto/cerrado de un día en el primer clic y acomoda la vista."""
    hoy_iso = datetime.now().date().strftime("%Y-%m-%d")
    estado_defecto = clave_orden == hoy_iso
    estado_actual = secciones_abiertas.get(clave_orden, estado_defecto)
    nuevo_estado = not estado_actual
    secciones_abiertas[clave_orden] = nuevo_estado
    actualizar_lista()
    if nuevo_estado:
        app.after(50, lambda: hacer_scroll_a_clave(clave_orden))


def borrar_click(tarea_id):
    eliminar_tarea(tarea_id)
    actualizar_lista()


def toggle_click(tarea_id):
    alternar_tarea(tarea_id)
    actualizar_lista()


def abrir_ajustes():
    ventana_ajustes = ctk.CTkToplevel(app)
    ventana_ajustes.title("Configuración")

    ventana_ajustes.transient(app)
    ventana_ajustes.attributes("-topmost", True)
    ventana_ajustes.grab_set()

    app.update_idletasks()
    ancho_aj = 330
    alto_aj = 470
    pos_x = max(10, app.winfo_x() + int((app.winfo_width() - ancho_aj) / 2))
    pos_y = max(10, app.winfo_y() + int((app.winfo_height() - alto_aj) / 2))
    ventana_ajustes.geometry(f"{ancho_aj}x{alto_aj}+{pos_x}+{pos_y}")

    ventana_ajustes.configure(fg_color="#0F1115")
    ventana_ajustes.resizable(False, False)

    ventana_ajustes.after(10, ventana_ajustes.lift)
    ventana_ajustes.after(20, ventana_ajustes.focus_force)

    ctk.CTkLabel(
        ventana_ajustes,
        text="Configuración",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=16, weight="bold"),
        text_color="#F9FAFB",
    ).pack(pady=(14, 8))

    ctk.CTkLabel(
        ventana_ajustes,
        text="Tu nombre:",
        font=ctk.CTkFont(size=12),
        text_color="#9CA3AF",
    ).pack(anchor="w", padx=24)
    entry_nombre = ctk.CTkEntry(ventana_ajustes, height=30, corner_radius=8)
    entry_nombre.insert(0, nombre_usuario)
    entry_nombre.pack(fill="x", padx=24, pady=(3, 8))

    ctk.CTkLabel(
        ventana_ajustes,
        text="Tamaño de ventana:",
        font=ctk.CTkFont(size=12),
        text_color="#9CA3AF",
    ).pack(anchor="w", padx=24)
    menu_tamano = ctk.CTkOptionMenu(
        ventana_ajustes,
        values=[
            "Compacto (420x480)",
            "Normal (420x620)",
            "Grande (600x750)",
            "Amplio (900x800)",
        ],
        height=30,
        corner_radius=8,
    )
    menu_tamano.set("Normal (420x620)")
    menu_tamano.pack(fill="x", padx=24, pady=(3, 8))

    ctk.CTkLabel(
        ventana_ajustes,
        text="Tema de color:",
        font=ctk.CTkFont(size=12),
        text_color="#9CA3AF",
    ).pack(anchor="w", padx=24)
    menu_tema = ctk.CTkOptionMenu(
        ventana_ajustes,
        values=list(TEMAS.keys()),
        height=30,
        corner_radius=8,
    )
    menu_tema.set(tema_actual)
    menu_tema.pack(fill="x", padx=24, pady=(3, 10))

    chk_startup = ctk.CTkCheckBox(
        ventana_ajustes,
        text="Iniciar en segundo plano con Windows",
        font=ctk.CTkFont(size=11),
        text_color="#D1D5DB",
        checkbox_width=18,
        checkbox_height=18,
        corner_radius=4,
    )
    if esta_en_inicio_windows():
        chk_startup.select()
    chk_startup.pack(anchor="w", padx=24, pady=(4, 14))

    def guardar_ajustes():
        global nombre_usuario
        nuevo_nombre = entry_nombre.get().strip() or "Koke"
        nombre_usuario = nuevo_nombre

        seleccion = menu_tamano.get()
        if "Compacto" in seleccion:
            app.geometry("420x480")
        elif "Grande" in seleccion:
            app.geometry("600x750")
        elif "Amplio" in seleccion:
            app.geometry("900x800")
        else:
            app.geometry("420x620")

        nuevo_tema = menu_tema.get()
        aplicar_tema(nuevo_tema)

        configurar_inicio_windows(chk_startup.get() == 1)

        with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "nombre": nuevo_nombre,
                    "tema": nuevo_tema,
                    "inicio_windows": (chk_startup.get() == 1),
                },
                f,
                indent=4,
                ensure_ascii=False,
            )

        app.title(f"{nuevo_nombre}'s To-Do List")
        ventana_ajustes.destroy()

    ctk.CTkButton(
        ventana_ajustes,
        text="Guardar Cambios",
        command=guardar_ajustes,
        fg_color="#10B981",
        hover_color="#059669",
        height=32,
        corner_radius=8,
    ).pack(fill="x", padx=24, pady=(0, 6))

    ctk.CTkButton(
        ventana_ajustes,
        text=f"🔄 Buscar actualizaciones (v{VERSION_ACTUAL})",
        command=lambda: verificar_actualizaciones(mostrar_si_al_dia=True),
        fg_color="transparent",
        hover_color="#1F242D",
        text_color="#9CA3AF",
        height=26,
        corner_radius=8,
        font=ctk.CTkFont(size=11),
    ).pack(fill="x", padx=24, pady=(0, 6))

    ctk.CTkButton(
        ventana_ajustes,
        text="Cerrar app por completo",
        command=salir_por_completo,
        fg_color="transparent",
        hover_color="#374151",
        text_color="#F87171",
        height=26,
        corner_radius=8,
        font=ctk.CTkFont(size=11),
    ).pack(fill="x", padx=24)


def agregar_con_enter(event=None):
    texto = entrada_tarea.get().strip()
    if texto:
        agregar_tarea(
            texto,
            fecha_seleccionada_nueva["iso"],
            hora=recordatorio_actual["hora"],
            anticipacion=recordatorio_actual["anticipacion"],
        )
        entrada_tarea.delete(0, "end")
        recordatorio_actual["hora"] = ""
        recordatorio_actual["anticipacion"] = 0
        actualizar_boton_hora()
        fecha_seleccionada_nueva["iso"] = datetime.now().date().strftime("%Y-%m-%d")
        actualizar_boton_calendario_principal()
        actualizar_lista()


def renderizar_tarjeta_dia(parent, datos_dia, es_hoy=False):
    """Renderiza la tarjeta de un día con su encabezado interactivo y píldoras."""
    clave_orden = datos_dia["orden"]
    etiqueta = datos_dia["etiqueta"]
    tareas_grupo = datos_dia["tareas"]
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    hoy_iso = datetime.now().date().strftime("%Y-%m-%d")

    def clave_orden_tarea(tk):
        esta_lista = tk.get("completada", False)
        prio_map = {"rojo": 0, "amarillo": 1, "verde": 2}
        prio_val = prio_map.get(tk.get("prioridad", "verde"), 2)
        tiene_hora = 0 if tk.get("hora") else 1
        h = tk.get("hora", "")
        return (1 if esta_lista else 0, prio_val, tiene_hora, h)

    tareas_grupo.sort(key=clave_orden_tarea)

    es_atrasada = clave_orden < hoy_iso
    abierto = True if filtro_busqueda.strip() else secciones_abiertas.get(clave_orden, es_hoy)
    incompletas = len([tk for tk in tareas_grupo if not tk.get("completada")])

    if es_atrasada:
        if incompletas == 0:
            color_badge = t.get("badge_ok", "#34D399")
            texto_badge = "✓"
            color_titulo = t["text_muted"]
            etiqueta_mostrar = etiqueta.replace("⚠️ ", "").replace(" (Atrasado)", "")
        else:
            color_badge = t.get("badge_alert", "#F87171")
            texto_badge = str(incompletas)
            color_titulo = t.get("badge_alert", "#F87171")
            etiqueta_mostrar = etiqueta
    else:
        color_badge = (
            t.get("badge_ok", "#34D399")
            if incompletas == 0
            else t.get("badge_alert", "#F87171")
        )
        texto_badge = (
            str(incompletas) if incompletas > 0 else ("✓" if tareas_grupo else "0")
        )
        color_titulo = t["text_main"] if es_hoy else t["text_muted"]
        etiqueta_mostrar = etiqueta

    seccion_dia = ctk.CTkFrame(parent, fg_color="transparent")
    seccion_dia.pack(fill="x", pady=(6, 2), padx=4)
    widgets_dias[clave_orden] = seccion_dia

    # HEADER DEL DÍA: NOMBRE + LÍNEA + BADGE
    header_row = ctk.CTkFrame(seccion_dia, fg_color="transparent", cursor="hand2")
    header_row.pack(fill="x", padx=4, pady=(2, 4))

    simbolo_flecha = "▼" if abierto else "▶"
    lbl_flecha = ctk.CTkLabel(
        header_row,
        text=simbolo_flecha,
        font=ctk.CTkFont(size=10, weight="bold"),
        text_color=color_titulo,
    )
    lbl_flecha.pack(side="left", padx=(2, 6))

    lbl_seccion = ctk.CTkLabel(
        header_row,
        text=etiqueta_mostrar,
        font=ctk.CTkFont(
            family="Segoe UI Variable Display",
            size=12,
            weight="bold",
        ),
        text_color=color_titulo,
    )
    lbl_seccion.pack(side="left", padx=(0, 6))

    linea_divisoria = ctk.CTkFrame(
        header_row,
        height=1,
        fg_color=t.get("border_card", "#2C2C2C"),
    )
    linea_divisoria.pack(side="left", fill="x", expand=True, padx=(4, 8))

    lbl_badge = ctk.CTkLabel(
        header_row,
        text=texto_badge,
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
        text_color=color_badge,
    )
    lbl_badge.pack(side="right", padx=(2, 4))

    for widget_header in [
        header_row,
        lbl_flecha,
        lbl_seccion,
        linea_divisoria,
        lbl_badge,
    ]:
        widget_header.bind(
            "<Button-1>",
            lambda event, cl=clave_orden: alternar_seccion(cl),
        )

    # TARJETA CON LAS PÍLDORAS (Marco normal para que nunca se corte)
    if abierto:
        card_dia = ctk.CTkFrame(
            seccion_dia,
            fg_color=t["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=t["border_card"],
        )
        card_dia.pack(fill="x", padx=4, pady=(2, 6))

        if es_hoy:
            listas_h = len([tk for tk in tareas_grupo if tk.get("completada")])
            tot_h = len(tareas_grupo)
            pct = listas_h / tot_h if tot_h > 0 else 0

            if tot_h > 0:
                frame_progreso = ctk.CTkFrame(
                    card_dia,
                    fg_color=t["bg_app"],
                    corner_radius=8,
                )
                frame_progreso.pack(fill="x", padx=8, pady=(8, 4))

                row_prog = ctk.CTkFrame(frame_progreso, fg_color="transparent")
                row_prog.pack(fill="x", padx=10, pady=(6, 2))

                ctk.CTkLabel(
                    row_prog,
                    text=f"🎯 Progreso de hoy: {listas_h}/{tot_h} ({int(pct * 100)}%)",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=t["text_muted"],
                ).pack(side="left")

                color_barra = "#10B981" if tema_actual != "Hello Kitty" else "#EC4899"
                prog_bar = ctk.CTkProgressBar(
                    frame_progreso,
                    height=6,
                    corner_radius=3,
                    progress_color=color_barra,
                    fg_color=t["bg_card"],
                )
                prog_bar.set(pct)
                prog_bar.pack(fill="x", padx=10, pady=(2, 6))

        if not tareas_grupo:
            if es_hoy:
                ctk.CTkLabel(
                    card_dia,
                    text="No tienes tareas pendientes para hoy ✨\nEscribe arriba y presiona Enter para agregar una.",
                    font=ctk.CTkFont(family="Segoe UI Variable Text", size=11),
                    text_color=t["text_muted"],
                    justify="center",
                ).pack(pady=12)
        else:
            for task in tareas_grupo:
                tid = task.get("id")
                esta_lista = task.get("completada", False)

                prio = task.get("prioridad", "verde")
                color_tag = None
                if prio == "rojo":
                    color_tag = "#EF4444"
                elif prio == "amarillo":
                    color_tag = "#F59E0B"

                borde_capsula = (
                    t["border_input"]
                    if not esta_lista
                    else ("#222731" if tema_actual != "Hello Kitty" else "#F9A8D4")
                )
                if color_tag and not esta_lista:
                    borde_capsula = "#7F1D1D" if prio == "rojo" else "#78350F"

                capsula = ctk.CTkFrame(
                    card_dia,
                    fg_color=(
                        t["bg_input"]
                        if not esta_lista
                        else ("#161920" if tema_actual != "Hello Kitty" else "#FCE7F3")
                    ),
                    corner_radius=8,
                    border_width=1,
                    border_color=borde_capsula,
                    cursor="hand2",
                )
                capsula.pack(fill="x", pady=3, padx=6)

                # Clic izquierdo normal: Modificar tarea
                capsula.bind(
                    "<Button-1>",
                    lambda event, tk=task: abrir_modal_edicion(tk),
                )
                # Clic derecho: Popup con Prioridad y Eliminar
                capsula.bind(
                    "<Button-3>",
                    lambda event, tk=task: mostrar_popup_eliminar(event, tk),
                )

                if color_tag and not esta_lista:
                    tag_bar = ctk.CTkFrame(
                        capsula,
                        width=3,
                        height=18,
                        fg_color=color_tag,
                        corner_radius=2,
                    )
                    tag_bar.pack(side="left", padx=(6, 0), pady=6)
                    tag_bar.bind(
                        "<Button-1>",
                        lambda event, tk=task: abrir_modal_edicion(tk),
                    )
                    tag_bar.bind(
                        "<Button-3>",
                        lambda event, tk=task: mostrar_popup_eliminar(event, tk),
                    )

                casilla = ctk.CTkCheckBox(
                    capsula,
                    text="",
                    width=20,
                    checkbox_width=18,
                    checkbox_height=18,
                    corner_radius=9,
                    border_width=1,
                    border_color="#374151",
                    fg_color=("#10B981" if tema_actual != "Hello Kitty" else "#EC4899"),
                    hover_color=(
                        "#059669" if tema_actual != "Hello Kitty" else "#DB2777"
                    ),
                    command=lambda tid_val=tid: toggle_click(tid_val),
                )
                if esta_lista:
                    casilla.select()
                else:
                    casilla.deselect()

                casilla.pack(side="left", padx=(8, 4), pady=7)
                casilla.bind(
                    "<Button-3>",
                    lambda event, tk=task: mostrar_popup_eliminar(event, tk),
                )

                if task.get("hora"):
                    lbl_hora_item = ctk.CTkLabel(
                        capsula,
                        text=f"⏰ {task['hora']}",
                        font=ctk.CTkFont(
                            size=11,
                            weight="normal" if esta_lista else "bold",
                            overstrike=esta_lista,
                        ),
                        text_color=(
                            "#6B7280"
                            if esta_lista
                            else (
                                "#10B981" if tema_actual != "Hello Kitty" else "#E11D48"
                            )
                        ),
                        cursor="hand2",
                    )
                    lbl_hora_item.pack(side="right", padx=(2, 12), pady=6)
                    lbl_hora_item.bind(
                        "<Button-1>",
                        lambda event, tk=task: abrir_modal_edicion(tk),
                    )
                    lbl_hora_item.bind(
                        "<Button-3>",
                        lambda event, tk=task: mostrar_popup_eliminar(event, tk),
                    )

                texto_tarea = ctk.CTkLabel(
                    capsula,
                    text=task.get("nombre", ""),
                    anchor="w",
                    justify="left",
                    wraplength=220,
                    text_color="#6B7280" if esta_lista else t["text_main"],
                    cursor="hand2",
                    font=ctk.CTkFont(
                        family="Segoe UI Variable Text",
                        size=12,
                        weight="normal" if esta_lista else "bold",
                        slant="italic" if esta_lista else "roman",
                        overstrike=esta_lista,
                    ),
                )
                texto_tarea.pack(
                    side="left",
                    fill="x",
                    expand=True,
                    padx=4,
                    pady=7,
                )
                texto_tarea.bind(
                    "<Button-1>",
                    lambda event, tk=task: abrir_modal_edicion(tk),
                )
                texto_tarea.bind(
                    "<Button-3>",
                    lambda event, tk=task: mostrar_popup_eliminar(event, tk),
                )


def actualizar_lista():
    if modo_widget:
        actualizar_contenido_widget()
        return

    for elemento in macro_tareas.winfo_children():
        elemento.destroy()

    widgets_dias.clear()
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])

    pendientes_totales = len(
        [t_item for t_item in tareas if not t_item.get("completada")]
    )

    color_contador = (
        "#199423" if pendientes_totales == 0 else t.get("badge_alert", "#F87171")
    )
    lbl_contador.configure(
        text=f"{pendientes_totales} Pendiente{'s' if pendientes_totales != 1 else ''}",
        text_color=color_contador,
    )

    ruta_img = obtener_ruta_imagen_kitty()

    # CASO 1: NO HAY TAREAS -> Imagen grande centrada
    if not tareas:
        lbl_kitty_header.pack_forget()

        if tema_actual == "Hello Kitty" and ruta_img:
            img_centro = obtener_imagen_tenue(
                ruta_img, opacidad=0.45, tamano=(230, 230)
            )
            if img_centro:
                lbl_img = ctk.CTkLabel(
                    macro_tareas,
                    text="",
                    image=img_centro,
                    fg_color="transparent",
                )
                lbl_img.pack(pady=(25, 5))

        lbl_vacio = ctk.CTkLabel(
            macro_tareas,
            text="Sin pendientes por ahora ✨",
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=13),
            text_color="#4B5563" if tema_actual != "Hello Kitty" else "#DB2777",
        )
        lbl_vacio.pack(
            pady=(5 if (tema_actual == "Hello Kitty" and ruta_img) else 70, 0)
        )
        return

    # CASO 2: SÍ HAY TAREAS -> Sticker pequeño en esquina superior derecha
    if tema_actual == "Hello Kitty" and ruta_img:
        img_pequena = obtener_imagen_tenue(ruta_img, opacidad=0.90, tamano=(38, 38))
        if img_pequena:
            lbl_kitty_header.configure(image=img_pequena)
            lbl_kitty_header.pack(side="right")
    else:
        lbl_kitty_header.pack_forget()

    hoy_dt = datetime.now().date()
    hoy_iso = hoy_dt.strftime("%Y-%m-%d")
    mes_actual_iso = hoy_dt.strftime("%Y-%m")

    # 1. Asegurar que "Hoy" siempre exista en su grupo
    etiqueta_hoy, _ = obtener_etiqueta_dinamica(hoy_iso)
    grupos_por_dia = {
        hoy_iso: {
            "etiqueta": etiqueta_hoy,
            "orden": hoy_iso,
            "tareas": [],
        }
    }

    texto_filtro = filtro_busqueda.strip().lower()

    # Agrupar TODAS las tareas (o las que coincidan con la búsqueda)
    for item in tareas:
        if texto_filtro and texto_filtro not in item.get("nombre", "").lower():
            continue
        f_item = item.get("fecha", "")
        etiqueta, orden_clave = obtener_etiqueta_dinamica(f_item)
        if orden_clave not in grupos_por_dia:
            grupos_por_dia[orden_clave] = {
                "etiqueta": etiqueta,
                "orden": orden_clave,
                "tareas": [],
            }
        grupos_por_dia[orden_clave]["tareas"].append(item)

    if texto_filtro and not any(d["tareas"] for d in grupos_por_dia.values()):
        lbl_vacio_b = ctk.CTkLabel(
            macro_tareas,
            text=f"🔍 Sin resultados para:\n\"{filtro_busqueda}\"",
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=13),
            text_color=t["text_muted"],
            justify="center",
        )
        lbl_vacio_b.pack(pady=60)
        return

    # 2. Agrupar días por mes (TODOS los días quedan dentro de su mes correspondiente)
    meses = {}

    for clave_dia, datos_dia in grupos_por_dia.items():
        if clave_dia != hoy_iso and not datos_dia["tareas"]:
            continue

        try:
            dt_dia = datetime.strptime(clave_dia, "%Y-%m-%d").date()
            clave_mes = dt_dia.strftime("%Y-%m")
            nom_m = MESES_ESPANOL[dt_dia.month].upper()
            nombre_mes = f"{nom_m} {dt_dia.year}"
        except Exception:
            clave_mes = "9999-99"
            nombre_mes = "OTRAS FECHAS"

        if clave_mes not in meses:
            meses[clave_mes] = {
                "clave": clave_mes,
                "nombre": nombre_mes,
                "dias": [],
            }
        meses[clave_mes]["dias"].append(datos_dia)

    # 3. Ordenar meses de MAYOR a MENOR (Noviembre arriba, luego Octubre, etc.)
    for clave_mes, datos_mes in sorted(meses.items(), key=lambda x: x[0], reverse=True):
        if not datos_mes["dias"]:
            continue

        # Ordenar los días dentro del mes:
        # - Hoy siempre hasta arriba dentro de su mes
        # - Los demás días de mayor a menor (31, 30, 28, etc.)
        def criterio_dia(d):
            c = d["orden"]
            if c == hoy_iso:
                return (0, 0)
            try:
                val = -int(c.replace("-", ""))
            except Exception:
                val = 0
            return (1, val)

        datos_mes["dias"].sort(key=criterio_dia)

        total_pendientes_mes = sum(
            len([tk for tk in d["tareas"] if not tk.get("completada")])
            for d in datos_mes["dias"]
        )

        es_mes_actual = clave_mes == mes_actual_iso
        mes_abierto = True if texto_filtro else meses_abiertos.get(clave_mes, es_mes_actual)

        contenedor_mes = ctk.CTkFrame(macro_tareas, fg_color="transparent")
        contenedor_mes.pack(fill="x", pady=(10, 4), padx=2)
        widgets_dias[f"mes_{clave_mes}"] = contenedor_mes

        banner_mes = ctk.CTkFrame(
            contenedor_mes, fg_color="transparent", cursor="hand2"
        )
        banner_mes.pack(fill="x", padx=4, pady=(4, 6))

        flecha_mes = "▼" if mes_abierto else "▶"
        lbl_flecha_mes = ctk.CTkLabel(
            banner_mes,
            text=flecha_mes,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=t["text_main"] if es_mes_actual else t["text_muted"],
        )
        lbl_flecha_mes.pack(side="left", padx=(2, 6))

        lbl_nombre_mes = ctk.CTkLabel(
            banner_mes,
            text=f"🗓️  {datos_mes['nombre']}",
            font=ctk.CTkFont(
                family="Segoe UI Variable Display", size=15, weight="bold"
            ),
            text_color=t["text_main"] if es_mes_actual else t["text_muted"],
        )
        lbl_nombre_mes.pack(side="left", padx=(0, 8))

        linea_mes = ctk.CTkFrame(
            banner_mes,
            height=2,
            fg_color=t.get("border_card", "#2C2C2C"),
        )
        linea_mes.pack(side="left", fill="x", expand=True, padx=(4, 8))

        texto_badge_mes = f"{total_pendientes_mes} pendiente{'s' if total_pendientes_mes != 1 else ''}"
        color_badge_mes = (
            t["badge_ok"] if total_pendientes_mes == 0 else t["badge_alert"]
        )
        lbl_badge_mes = ctk.CTkLabel(
            banner_mes,
            text=texto_badge_mes,
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
            text_color=color_badge_mes,
        )
        lbl_badge_mes.pack(side="right", padx=(2, 4))

        for w_m in [
            banner_mes,
            lbl_flecha_mes,
            lbl_nombre_mes,
            linea_mes,
            lbl_badge_mes,
        ]:
            w_m.bind("<Button-1>", lambda event, cm=clave_mes: alternar_mes(cm))

        # SI EL MES ESTÁ ABIERTO, SE MUESTRAN SUS DÍAS DE MAYOR A MENOR (CON HOY HASTA ARRIBA)
        if mes_abierto:
            for datos_dia in datos_mes["dias"]:
                renderizar_tarjeta_dia(
                    contenedor_mes,
                    datos_dia,
                    es_hoy=(datos_dia["orden"] == hoy_iso),
                )


# ==========================================
# BLOQUE 4: SEGUNDO PLANO Y BANDEJA (TRAY)
# ==========================================
def crear_icono_bandeja():
    ruta_img = obtener_ruta_imagen_kitty()
    if ruta_img and os.path.exists(ruta_img):
        try:
            img = Image.open(ruta_img).convert("RGBA")
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            return img
        except Exception:
            pass

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill="#10B981")
    d.line([(18, 33), (28, 44), (46, 20)], fill="#FFFFFF", width=6)
    return img


def mostrar_ventana(icon=None, item=None):
    app.after(0, _restaurar_ventana_principal)


def _restaurar_ventana_principal():
    app.deiconify()
    app.state("normal")
    app.lift()
    app.focus_force()


def minimizar_a_bandeja():
    global _aviso_bandeja_mostrado
    app.withdraw()
    if not _aviso_bandeja_mostrado and HAY_PLYER:
        _aviso_bandeja_mostrado = True
        try:
            notification.notify(
                title="To-Do List activa en segundo plano",
                message="Seguirás recibiendo tus recordatorios aquí junto al reloj.",
                app_name="To-Do List",
                timeout=5,
            )
        except Exception:
            pass


def salir_por_completo(icon=None, item=None):
    global tray_icon
    if tray_icon:
        try:
            tray_icon.stop()
        except Exception:
            pass
    app.after(0, app.destroy)


def inicializar_tray():
    global tray_icon
    if not HAY_PYSTRAY:
        return
    try:
        icono_img = crear_icono_bandeja()
        menu = pystray.Menu(
            pystray.MenuItem("Abrir To-Do List", mostrar_ventana, default=True),
            pystray.MenuItem("Salir", salir_por_completo),
        )
        tray_icon = pystray.Icon(
            "KokeToDo",
            icono_img,
            f"{nombre_usuario}'s To-Do List",
            menu,
        )
        tray_icon.run_detached()
    except Exception:
        pass


# ==========================================
# BLOQUE 5: INTERFAZ PRINCIPAL
# ==========================================
ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.geometry("420x620+1460+180")
app.attributes("-topmost", True)

app.protocol("WM_DELETE_WINDOW", minimizar_a_bandeja)

nombre_usuario = cargar_configuracion()
app.title(f"{nombre_usuario}'s To-Do List")


def alternar_modo_widget(e=None):
    """Alterna entre la ventana completa y el mini-widget flotante minimalista."""
    global modo_widget, geometria_previa
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    if not modo_widget:
        modo_widget = True
        geometria_previa = app.geometry()
        # Ocultar elementos de vista completa
        if busqueda_activa:
            marco_busqueda.pack_forget()
        header.pack_forget()
        marco_input.pack_forget()
        macro_tareas.pack_forget()
        footer.pack_forget()

        app.attributes("-topmost", True)
        try:
            partes = geometria_previa.split("+")
            if len(partes) >= 3:
                pos_x, pos_y = partes[1], partes[2]
                app.geometry(f"360x76+{pos_x}+{pos_y}")
            else:
                app.geometry("360x76")
        except Exception:
            app.geometry("360x76")

        lbl_widget_titulo.configure(
            text=f"📌 ¡Hola, {nombre_usuario}!", text_color=t["text_main"]
        )
        marco_widget.pack(fill="both", expand=True, padx=8, pady=6)
        actualizar_contenido_widget()
    else:
        modo_widget = False
        marco_widget.pack_forget()
        try:
            app.geometry(geometria_previa)
        except Exception:
            app.geometry("420x620")

        # Restaurar vista completa
        header.pack(fill="x", padx=20, pady=(18, 4))
        if busqueda_activa:
            marco_busqueda.pack(before=marco_input, fill="x", padx=20, pady=(0, 6))
        marco_input.pack(pady=10, padx=20, fill="x")
        macro_tareas.pack(fill="both", expand=True, padx=14, pady=(4, 6))
        footer.pack(side="bottom", fill="x", padx=16, pady=(0, 10))
        actualizar_lista()


def actualizar_contenido_widget():
    """Actualiza la tarea prioritaria mostrada en el widget flotante."""
    if not modo_widget or "marco_widget_contenido" not in globals():
        return
    for w in marco_widget_contenido.winfo_children():
        w.destroy()

    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    hoy_iso = datetime.now().date().strftime("%Y-%m-%d")
    prio_map = {"rojo": 0, "amarillo": 1, "verde": 2}

    pendientes_hoy = [
        tk for tk in tareas if tk.get("fecha") == hoy_iso and not tk.get("completada")
    ]
    tarea_top = None
    if pendientes_hoy:
        pendientes_hoy.sort(
            key=lambda tk: (
                prio_map.get(tk.get("prioridad", "verde"), 2),
                0 if tk.get("hora") else 1,
                tk.get("hora", ""),
            )
        )
        tarea_top = pendientes_hoy[0]
    else:
        otras_pendientes = [tk for tk in tareas if not tk.get("completada")]
        if otras_pendientes:
            otras_pendientes.sort(
                key=lambda tk: (
                    prio_map.get(tk.get("prioridad", "verde"), 2),
                    tk.get("fecha", ""),
                    tk.get("hora", ""),
                )
            )
            tarea_top = otras_pendientes[0]

    if tarea_top:
        prio = tarea_top.get("prioridad", "verde")
        color_prio = (
            "#EF4444"
            if prio == "rojo"
            else ("#F59E0B" if prio == "amarillo" else "#10B981")
        )

        fila_tk = ctk.CTkFrame(
            marco_widget_contenido,
            fg_color=t["bg_input"],
            corner_radius=8,
            border_width=1,
            border_color=(
                "#7F1D1D"
                if prio == "rojo"
                else ("#78350F" if prio == "amarillo" else t["border_input"])
            ),
            height=34,
        )
        fila_tk.pack(fill="x", padx=4, pady=2)

        tag_b = ctk.CTkFrame(
            fila_tk, width=3, height=18, fg_color=color_prio, corner_radius=2
        )
        tag_b.pack(side="left", padx=(4, 0), pady=4)

        def completar_desde_widget(tid=tarea_top["id"]):
            toggle_click(tid)
            actualizar_contenido_widget()

        chk = ctk.CTkCheckBox(
            fila_tk,
            text="",
            width=18,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=8,
            border_width=1,
            border_color="#374151",
            fg_color="#10B981" if tema_actual != "Hello Kitty" else "#EC4899",
            hover_color="#059669" if tema_actual != "Hello Kitty" else "#DB2777",
            command=completar_desde_widget,
        )
        chk.pack(side="left", padx=(6, 4), pady=5)

        txt_nombre = tarea_top.get("nombre", "")
        if len(txt_nombre) > 26:
            txt_nombre = txt_nombre[:24] + "…"
        lbl_nom = ctk.CTkLabel(
            fila_tk,
            text=txt_nombre,
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
            text_color=t["text_main"],
            anchor="w",
            cursor="hand2",
        )
        lbl_nom.pack(side="left", fill="x", expand=True, padx=(2, 4))
        lbl_nom.bind("<Button-1>", lambda e, tk=tarea_top: abrir_modal_edicion(tk))

        if tarea_top.get("hora"):
            lbl_h = ctk.CTkLabel(
                fila_tk,
                text=f"⏰ {tarea_top['hora']}",
                font=ctk.CTkFont(family="Segoe UI Variable Text", size=10),
                text_color=t.get("accent", "#60A5FA"),
            )
            lbl_h.pack(side="right", padx=(2, 6))
    else:
        fila_vacia = ctk.CTkFrame(marco_widget_contenido, fg_color="transparent")
        fila_vacia.pack(fill="x", pady=4)
        ctk.CTkLabel(
            fila_vacia,
            text="✨ ¡Todo listo por hoy!",
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
            text_color=t.get("badge_ok", "#34D399"),
        ).pack(side="left", padx=8)


def alternar_barra_busqueda(e=None):
    """Muestra u oculta la barra de búsqueda minimalista (o con Ctrl+F)."""
    global busqueda_activa, filtro_busqueda
    if modo_widget:
        alternar_modo_widget()

    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    if not busqueda_activa:
        busqueda_activa = True
        marco_busqueda.pack(before=marco_input, fill="x", padx=20, pady=(0, 6))
        entrada_busqueda.delete(0, "end")
        entrada_busqueda.focus()
        btn_buscar.configure(text_color=t.get("accent", "#60A5FA"))
    else:
        busqueda_activa = False
        filtro_busqueda = ""
        entrada_busqueda.delete(0, "end")
        marco_busqueda.pack_forget()
        btn_buscar.configure(text_color=t["text_muted"])
        actualizar_lista()
        app.focus()


def al_escribir_busqueda(event=None):
    global filtro_busqueda
    filtro_busqueda = entrada_busqueda.get()
    actualizar_lista()


header = ctk.CTkFrame(app, fg_color="transparent")
header.pack(fill="x", padx=20, pady=(18, 4))

lbl_titulo = ctk.CTkLabel(
    header,
    text=f"¡Hola, {nombre_usuario}!",
    font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold"),
    text_color="#F9FAFB",
    cursor="hand2",
)
lbl_titulo.pack(side="left")
lbl_titulo.bind("<Button-1>", alternar_modo_widget)

btn_buscar = ctk.CTkButton(
    header,
    text="🔍",
    width=26,
    height=26,
    corner_radius=6,
    fg_color="transparent",
    text_color="#6B7280",
    hover_color="#1F232B",
    font=ctk.CTkFont(size=12),
    command=alternar_barra_busqueda,
)
btn_buscar.pack(side="right", padx=(4, 0))

lbl_kitty_header = ctk.CTkLabel(header, text="", fg_color="transparent")

# Barra de Búsqueda minimalista (oculta inicialmente, se abre con 🔍 o Ctrl+F)
marco_busqueda = ctk.CTkFrame(
    app,
    fg_color="#13161C",
    corner_radius=10,
    border_width=1,
    border_color="#1F242D",
    height=32,
)

lbl_icono_b = ctk.CTkLabel(
    marco_busqueda,
    text="🔍",
    font=ctk.CTkFont(size=11),
    text_color="#6B7280",
    width=20,
)
lbl_icono_b.pack(side="left", padx=(8, 2))

entrada_busqueda = ctk.CTkEntry(
    marco_busqueda,
    placeholder_text="Buscar tarea... (Esc para salir)",
    placeholder_text_color="#4B5563",
    fg_color="transparent",
    border_width=0,
    font=ctk.CTkFont(family="Segoe UI Variable Text", size=11),
    height=28,
)
entrada_busqueda.pack(side="left", fill="x", expand=True, padx=2)
entrada_busqueda.bind("<KeyRelease>", al_escribir_busqueda)
entrada_busqueda.bind("<Escape>", lambda e: alternar_barra_busqueda())

btn_cerrar_busqueda = ctk.CTkButton(
    marco_busqueda,
    text="✕",
    width=22,
    height=22,
    corner_radius=6,
    fg_color="transparent",
    hover_color="#222732",
    text_color="#6B7280",
    font=ctk.CTkFont(size=11),
    command=alternar_barra_busqueda,
)
btn_cerrar_busqueda.pack(side="right", padx=(2, 6))

app.bind("<Control-f>", lambda e: alternar_barra_busqueda())
app.bind("<Control-F>", lambda e: alternar_barra_busqueda())

# Marco Widget flotante minimalista (se activa al tocar el saludo)
marco_widget = ctk.CTkFrame(app, fg_color="transparent")

fila_widget_sup = ctk.CTkFrame(marco_widget, fg_color="transparent", height=18)
fila_widget_sup.pack(fill="x", padx=2, pady=(0, 2))

lbl_widget_titulo = ctk.CTkLabel(
    fila_widget_sup,
    text=f"📌 ¡Hola, {nombre_usuario}!",
    font=ctk.CTkFont(family="Segoe UI Variable Display", size=11, weight="bold"),
    text_color="#F9FAFB",
    cursor="hand2",
)
lbl_widget_titulo.pack(side="left")
lbl_widget_titulo.bind("<Button-1>", alternar_modo_widget)

btn_widget_expandir = ctk.CTkButton(
    fila_widget_sup,
    text="⛶",
    width=20,
    height=18,
    corner_radius=4,
    fg_color="transparent",
    hover_color="#222732",
    text_color="#9CA3AF",
    font=ctk.CTkFont(size=11),
    command=alternar_modo_widget,
)
btn_widget_expandir.pack(side="right")

marco_widget_contenido = ctk.CTkFrame(marco_widget, fg_color="transparent")
marco_widget_contenido.pack(fill="x", expand=True)

marco_input = ctk.CTkFrame(
    app,
    fg_color="#13161C",
    corner_radius=12,
    border_width=2,
    border_color="#1F242D",
)
marco_input.pack(pady=10, padx=20, fill="x")

entrada_tarea = ctk.CTkEntry(
    marco_input,
    placeholder_text="Escribe aquí...",
    placeholder_text_color="#4B5563",
    fg_color="transparent",
    border_width=0,
    font=ctk.CTkFont(family="Segoe UI Variable Text", size=12),
    height=36,
)
entrada_tarea.pack(side="left", fill="x", expand=True, padx=(12, 2), pady=3)
entrada_tarea.bind("<Return>", agregar_con_enter)

btn_hora = ctk.CTkButton(
    marco_input,
    text="⏰",
    width=32,
    height=26,
    corner_radius=6,
    fg_color="transparent",
    text_color="#9CA3AF",
    hover_color="#1F232B",
    font=ctk.CTkFont(size=12),
    command=lambda: abrir_modal_edicion(None),
)
btn_hora.pack(side="right", padx=(0, 4), pady=3)

# Botón interactivo de calendario
btn_calendario = ctk.CTkButton(
    marco_input,
    text=obtener_texto_boton_fecha(fecha_seleccionada_nueva["iso"]),
    width=110,
    height=26,
    corner_radius=7,
    fg_color="#1D222A",
    hover_color="#2E3744",
    text_color="#D1D5DB",
    font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
    command=click_calendario_principal,
)
btn_calendario.pack(side="right", padx=(0, 4), pady=3)

# FOOTER: ENGRANE (IZQ) | PENDIENTES (DER)
footer = ctk.CTkFrame(app, fg_color="transparent", height=28)
footer.pack(side="bottom", fill="x", padx=16, pady=(0, 10))

btn_ajustes = ctk.CTkButton(
    footer,
    text="⚙",
    width=26,
    height=26,
    corner_radius=6,
    fg_color="transparent",
    text_color="#6B7280",
    hover_color="#1F232B",
    font=ctk.CTkFont(size=14),
    command=abrir_ajustes,
)
btn_ajustes.pack(side="left")

lbl_contador = ctk.CTkLabel(
    footer,
    text="0 Pendientes",
    font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
    text_color="#34D399",
)
lbl_contador.pack(side="right")

lbl_watermark = ctk.CTkLabel(
    footer,
    text="🎀  Hello Kitty",
    font=ctk.CTkFont(family="Segoe UI Variable Text", size=10, weight="bold"),
    text_color="#FBCFE8",
)

macro_tareas = ctk.CTkScrollableFrame(
    app,
    fg_color="#0F1115",
    corner_radius=12,
)
macro_tareas.pack(fill="both", expand=True, padx=14, pady=(4, 6))

if __name__ == "__main__":
    cargar_tareas()
    ultimo_dia_verificado["dia"] = datetime.now().date()
    aplicar_tema(tema_actual)
    verificar_recordatorios()
    inicializar_tray()

    # Comprobación sutil de actualizaciones al inicio (en segundo plano)
    app.after(3000, lambda: verificar_actualizaciones(mostrar_si_al_dia=False))

    if "--tray" in sys.argv:
        app.withdraw()

    app.mainloop()
