# ==========================================
# BLOQUE 1: CONFIGURACIÓN E IMPORTACIONES
# ==========================================
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
import customtkinter as ctk
import winsound
from PIL import Image

try:
    from plyer import notification

    HAY_PLYER = True
except Exception:
    HAY_PLYER = False

CARPETA_DATOS = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "KokeToDo")
os.makedirs(CARPETA_DATOS, exist_ok=True)

ARCHIVO_TAREAS = os.path.join(CARPETA_DATOS, "tareas.json")
ARCHIVO_CONFIG = os.path.join(CARPETA_DATOS, "config.json")
tareas = []
secciones_abiertas = {}

recordatorio_actual = {"hora": "", "anticipacion": 0}

DIAS_ESPANOL = {
    0: "Lun",
    1: "Mar",
    2: "Mié",
    3: "Jue",
    4: "Vie",
    5: "Sáb",
    6: "Dom",
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
hoy_dt = datetime.now().date()
opciones_menu = {}

for i in range(14):
    dia_obj = hoy_dt + timedelta(days=i)
    clave_fecha = dia_obj.strftime("%Y-%m-%d")
    nom_dia = DIAS_ESPANOL[dia_obj.weekday()]
    formato_fecha = f"{nom_dia} {dia_obj.strftime('%d/%m')}"

    if i == 0:
        etiqueta = f"Hoy ({formato_fecha})"
    elif i == 1:
        etiqueta = f"Mañana ({formato_fecha})"
    else:
        etiqueta = formato_fecha

    opciones_menu[etiqueta] = clave_fecha

lista_dias_etiquetas = list(opciones_menu.keys())


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
    if os.path.exists(ARCHIVO_TAREAS):
        try:
            with open(ARCHIVO_TAREAS, "r", encoding="utf-8") as f:
                datos = json.load(f)
                tareas.clear()
                tareas.extend(datos)
        except Exception:
            tareas.clear()
    else:
        tareas.clear()


def guardar_tareas():
    with open(ARCHIVO_TAREAS, "w", encoding="utf-8") as f:
        json.dump(tareas, f, indent=4, ensure_ascii=False)


def agregar_tarea(nombre, fecha, hora="", anticipacion=0):
    nueva_tarea = {
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


def alternar_tarea(nombre_tarea):
    for t in tareas:
        if t["nombre"] == nombre_tarea:
            t["completada"] = not t["completada"]
            guardar_tareas()
            break


def eliminar_tarea(nombre_tarea):
    for i, t in enumerate(tareas):
        if t["nombre"] == nombre_tarea:
            tareas.pop(i)
            guardar_tareas()
            break


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


def mostrar_alerta_modal(tarea_nombre, detalle_hora):
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass

    modal_alerta = ctk.CTkToplevel(app)
    modal_alerta.title("¡RECORDATORIO!")
    modal_alerta.transient(app)
    modal_alerta.attributes("-topmost", True)
    modal_alerta.grab_set()

    ancho_a, alto_a = 320, 230
    pos_x = app.winfo_x() + int((app.winfo_width() - ancho_a) / 2)
    pos_y = app.winfo_y() + int((app.winfo_height() - alto_a) / 2)
    modal_alerta.geometry(f"{ancho_a}x{alto_a}+{pos_x}+{pos_y}")
    modal_alerta.resizable(False, False)

    if tema_actual == "Hello Kitty":
        bg_banner = "#E11D48"
        bg_card = "#F472B6"
        txt_main = "#831843"
        txt_sub = "#500724"
        btn_bg = "#831843"
        btn_hover = "#500724"
        btn_txt = "#FFFFFF"
    else:
        bg_banner = "#D97706"
        bg_card = "#F59E0B"
        txt_main = "#1C1917"
        txt_sub = "#451A03"
        btn_bg = "#1C1917"
        btn_hover = "#292524"
        btn_txt = "#FFFFFF"

    modal_alerta.configure(fg_color=bg_card)

    banner = ctk.CTkFrame(modal_alerta, fg_color=bg_banner, height=40, corner_radius=0)
    banner.pack(fill="x")
    ctk.CTkLabel(
        banner,
        text="🔔  ¡RECORDATORIO ACTIVO!",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=13, weight="bold"),
        text_color="#FFFFFF",
    ).pack(pady=8)

    cuerpo = ctk.CTkFrame(modal_alerta, fg_color="transparent")
    cuerpo.pack(fill="both", expand=True, padx=20, pady=8)

    ctk.CTkLabel(
        cuerpo,
        text=tarea_nombre,
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=16, weight="bold"),
        text_color=txt_main,
        wraplength=270,
        justify="center",
    ).pack(expand=True)

    ctk.CTkLabel(
        cuerpo,
        text=detalle_hora,
        font=ctk.CTkFont(family="Segoe UI Variable Text", size=12, weight="bold"),
        text_color=txt_sub,
    ).pack(pady=(0, 4))

    ctk.CTkButton(
        modal_alerta,
        text="Aceptar y Cerrar",
        height=34,
        corner_radius=8,
        fg_color=btn_bg,
        hover_color=btn_hover,
        text_color=btn_txt,
        font=ctk.CTkFont(size=12, weight="bold"),
        command=modal_alerta.destroy,
    ).pack(fill="x", padx=20, pady=(0, 14))


def lanzar_notificacion(titulo, mensaje):
    mostrar_alerta_modal(titulo.replace("🔔 ", ""), mensaje)
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


def verificar_recordatorios():
    ahora = datetime.now()
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

    selector_dia.configure(
        fg_color=t["bg_card"],
        button_color=t["border_card"],
        button_hover_color=t["border_input"],
        dropdown_fg_color=t["bg_card"],
        dropdown_hover_color=t["border_card"],
        text_color=t["text_main"],
        dropdown_text_color=t["text_main"],
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


def abrir_selector_hora(tarea_a_editar=None):
    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])
    modal = ctk.CTkToplevel(app)
    modal.title("Reprogramar Hora" if tarea_a_editar else "Definir Hora")
    modal.transient(app)
    modal.attributes("-topmost", True)
    modal.grab_set()

    ancho_m, alto_m = 290, 420
    pos_x = app.winfo_x() + int((app.winfo_width() - ancho_m) / 2)
    pos_y = app.winfo_y() + int((app.winfo_height() - alto_m) / 2)
    modal.geometry(f"{ancho_m}x{alto_m}+{pos_x}+{pos_y}")
    modal.configure(fg_color=t["bg_card"])
    modal.resizable(False, False)

    titulo_modal = (
        f"⏰ {tarea_a_editar['nombre'][:18]}..." if tarea_a_editar else "⏰ Elegir Hora"
    )
    ctk.CTkLabel(
        modal,
        text=titulo_modal,
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=14, weight="bold"),
        text_color=t["text_main"],
    ).pack(pady=(10, 4))

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

    ctk.CTkLabel(
        modal,
        text="Avisarme:",
        font=ctk.CTkFont(size=11),
        text_color=t["text_muted"],
    ).pack(anchor="w", padx=24, pady=(6, 2))

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
            tarea_a_editar["hora"] = h_final
            tarea_a_editar["anticipacion"] = ant_final
            tarea_a_editar["notificado"] = False
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
            etiqueta_sel = selector_dia.get()
            fecha_iso = opciones_menu.get(etiqueta_sel, hoy_dt.strftime("%Y-%m-%d"))
            agregar_tarea(
                texto,
                fecha_iso,
                hora=h_final,
                anticipacion=ant_final,
            )
            entrada_tarea.delete(0, "end")
            recordatorio_actual["hora"] = ""
            recordatorio_actual["anticipacion"] = 0
            actualizar_boton_hora()
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
            "Listo"
            if tarea_a_editar
            else ("Guardar tarea" if entrada_tarea.get().strip() else "Fijar hora")
        ),
        height=32,
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
        ).pack(fill="x", padx=24, pady=(0, 10))


def obtener_etiqueta_dinamica(fecha_str):
    try:
        f = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        dias_dif = (f - hoy_dt).days
        nom_dia = DIAS_ESPANOL[f.weekday()]

        if dias_dif < 0:
            return "Atrasadas", f.strftime("%Y-%m-%d")
        elif dias_dif == 0:
            return "Hoy", f.strftime("%Y-%m-%d")
        elif dias_dif == 1:
            return "Mañana", f.strftime("%Y-%m-%d")
        else:
            return (
                f"{nom_dia} {f.strftime('%d')}",
                f.strftime("%Y-%m-%d"),
            )
    except Exception:
        return fecha_str, "9999-99-99"


def alternar_seccion(etiqueta, card_widget=None):
    abriendo = not secciones_abiertas.get(etiqueta, False)
    secciones_abiertas[etiqueta] = abriendo
    actualizar_lista()

    if abriendo and card_widget:
        app.update_idletasks()
        macro_tareas._parent_canvas.yview_moveto(1.0)


def borrar_click(nombre):
    eliminar_tarea(nombre)
    actualizar_lista()


def toggle_click(nombre):
    alternar_tarea(nombre)
    actualizar_lista()


def abrir_ajustes():
    ventana_ajustes = ctk.CTkToplevel(app)
    ventana_ajustes.title("Ajustes")

    ventana_ajustes.transient(app)
    ventana_ajustes.attributes("-topmost", True)
    ventana_ajustes.grab_set()

    app.update_idletasks()
    ancho_aj = 310
    alto_aj = 340
    pos_x = app.winfo_x() + int((app.winfo_width() - ancho_aj) / 2)
    pos_y = app.winfo_y() + int((app.winfo_height() - alto_aj) / 2)
    ventana_ajustes.geometry(f"{ancho_aj}x{alto_aj}+{pos_x}+{pos_y}")

    ventana_ajustes.configure(fg_color="#0F1115")
    ventana_ajustes.resizable(False, False)

    ventana_ajustes.after(10, ventana_ajustes.lift)
    ventana_ajustes.after(20, ventana_ajustes.focus_force)

    ctk.CTkLabel(
        ventana_ajustes,
        text="Configuracion",
        font=ctk.CTkFont(family="Segoe UI Variable Display", size=16, weight="bold"),
        text_color="#F9FAFB",
    ).pack(pady=(16, 10))

    ctk.CTkLabel(
        ventana_ajustes,
        text="Tu nombre:",
        font=ctk.CTkFont(size=12),
        text_color="#9CA3AF",
    ).pack(anchor="w", padx=24)
    entry_nombre = ctk.CTkEntry(ventana_ajustes, height=32, corner_radius=8)
    entry_nombre.insert(0, nombre_usuario)
    entry_nombre.pack(fill="x", padx=24, pady=(4, 10))

    ctk.CTkLabel(
        ventana_ajustes,
        text="Tamano de ventana:",
        font=ctk.CTkFont(size=12),
        text_color="#9CA3AF",
    ).pack(anchor="w", padx=24)
    menu_tamano = ctk.CTkOptionMenu(
        ventana_ajustes,
        values=["Compacto (400x400)", "Normal (500x650)", "Grande (1000x900)"],
        height=30,
        corner_radius=8,
    )
    menu_tamano.pack(fill="x", padx=24, pady=(4, 10))

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
    menu_tema.pack(fill="x", padx=24, pady=(4, 16))

    def guardar_ajustes():
        global nombre_usuario
        nuevo_nombre = entry_nombre.get().strip() or "Koke"
        nombre_usuario = nuevo_nombre

        seleccion = menu_tamano.get()
        if "Compacto" in seleccion:
            app.geometry("400x400")
        elif "Grande" in seleccion:
            app.geometry("1000x900")
        else:
            app.geometry("500x650")

        nuevo_tema = menu_tema.get()
        aplicar_tema(nuevo_tema)

        with open(ARCHIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(
                {"nombre": nuevo_nombre, "tema": nuevo_tema},
                f,
                indent=4,
                ensure_ascii=False,
            )

        app.title(f"{nuevo_nombre}'s To-Do List")
        ventana_ajustes.destroy()

    ctk.CTkButton(
        ventana_ajustes,
        text="Guardar",
        command=guardar_ajustes,
        fg_color="#10B981",
        hover_color="#059669",
        height=32,
        corner_radius=8,
    ).pack(fill="x", padx=24)


def agregar_con_enter(event=None):
    texto = entrada_tarea.get().strip()
    etiqueta_sel = selector_dia.get()
    fecha_iso = opciones_menu.get(etiqueta_sel, hoy_dt.strftime("%Y-%m-%d"))

    if texto:
        agregar_tarea(
            texto,
            fecha_iso,
            hora=recordatorio_actual["hora"],
            anticipacion=recordatorio_actual["anticipacion"],
        )
        entrada_tarea.delete(0, "end")
        recordatorio_actual["hora"] = ""
        recordatorio_actual["anticipacion"] = 0
        actualizar_boton_hora()
        actualizar_lista()


def actualizar_lista():
    for elemento in macro_tareas.winfo_children():
        elemento.destroy()

    t = TEMAS.get(tema_actual, TEMAS["Obsidian"])

    pendientes = len([t_item for t_item in tareas if not t_item.get("completada")])
    color_contador = "#199423" if pendientes == 0 else t.get("badge_alert", "#F87171")
    lbl_contador.configure(
        text=f"{pendientes} Pendiente{'s' if pendientes != 1 else ''}",
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

    grupos = {}
    for item in tareas:
        etiqueta, orden_clave = obtener_etiqueta_dinamica(item.get("fecha", ""))
        if etiqueta not in grupos:
            grupos[etiqueta] = {"orden": orden_clave, "tareas": []}
        grupos[etiqueta]["tareas"].append(item)

    grupos_ordenados = sorted(grupos.items(), key=lambda x: x[1]["orden"])

    for etiqueta, datos in grupos_ordenados:
        tareas_grupo = datos["tareas"]
        abierto = secciones_abiertas.get(etiqueta, False)
        incompletas = len([it for it in tareas_grupo if not it.get("completada")])
        color_badge = (
            t.get("badge_ok", "#34D399")
            if incompletas == 0
            else t.get("badge_alert", "#F87171")
        )

        card_dia = ctk.CTkFrame(
            macro_tareas,
            fg_color=t["bg_card"],
            corner_radius=10,
            border_width=2,
            border_color=t["border_card"],
        )
        card_dia.pack(fill="x", pady=4, padx=4)

        header_row = ctk.CTkFrame(card_dia, fg_color="transparent", height=32)
        header_row.pack(fill="x", padx=10, pady=6)

        icono_tema = t.get("icono", "•" if abierto else "◦")
        simbolo = f"{icono_tema} " if abierto else "◦"
        lbl_seccion = ctk.CTkLabel(
            header_row,
            text=f"{simbolo}  {etiqueta}",
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=12, weight="bold"),
            text_color=t["text_muted"],
            cursor="hand2",
        )
        lbl_seccion.pack(side="left")
        lbl_seccion.bind(
            "<Button-1>", lambda event, e=etiqueta, c=card_dia: alternar_seccion(e, c)
        )
        header_row.bind(
            "<Button-1>", lambda event, e=etiqueta, c=card_dia: alternar_seccion(e, c)
        )

        lbl_badge = ctk.CTkLabel(
            header_row,
            text=str(incompletas),
            font=ctk.CTkFont(family="Segoe UI Variable Text", size=11, weight="bold"),
            text_color=color_badge,
        )
        lbl_badge.pack(side="right")

        if abierto:
            for task in tareas_grupo:
                esta_lista = task["completada"]

                fila = ctk.CTkFrame(card_dia, fg_color="transparent")
                fila.pack(fill="x", pady=2, padx=6)

                casilla = ctk.CTkCheckBox(
                    fila,
                    text="",
                    width=20,
                    checkbox_width=18,
                    checkbox_height=18,
                    corner_radius=9,
                    border_width=1,
                    border_color="#374151" if not esta_lista else "#10B981",
                    fg_color="#10B981" if tema_actual != "Hello Kitty" else "#EC4899",
                    hover_color=(
                        "#059669" if tema_actual != "Hello Kitty" else "#DB2777"
                    ),
                    command=lambda n=task["nombre"]: toggle_click(n),
                )
                if esta_lista:
                    casilla.select()
                casilla.pack(side="left", padx=(4, 6), pady=4)

                btn_del = ctk.CTkButton(
                    fila,
                    text="✕",
                    width=22,
                    height=22,
                    corner_radius=5,
                    fg_color="transparent",
                    text_color="#6B7280" if tema_actual != "Hello Kitty" else "#DB2777",
                    hover_color=(
                        "#374151" if tema_actual != "Hello Kitty" else "#FCE7F3"
                    ),
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda n=task["nombre"]: borrar_click(n),
                )
                btn_del.pack(side="right", padx=(2, 4))

                if task.get("hora"):
                    btn_hora_item = ctk.CTkButton(
                        fila,
                        text=f"⏰ {task['hora']}",
                        width=56,
                        height=20,
                        corner_radius=5,
                        fg_color="transparent",
                        hover_color=t["border_card"],
                        text_color=t["text_muted"],
                        font=ctk.CTkFont(size=10, weight="bold"),
                        command=lambda tk=task: abrir_selector_hora(tk),
                    )
                    btn_hora_item.pack(side="right", padx=(2, 4))
                else:
                    btn_hora_item = ctk.CTkButton(
                        fila,
                        text="⏰",
                        width=22,
                        height=20,
                        corner_radius=5,
                        fg_color="transparent",
                        hover_color=t["border_card"],
                        text_color=t.get("placeholder", "#4B5563"),
                        font=ctk.CTkFont(size=11),
                        command=lambda tk=task: abrir_selector_hora(tk),
                    )
                    btn_hora_item.pack(side="right", padx=(2, 4))

                texto_color = "#4B5563" if esta_lista else t["text_main"]
                texto_tarea = ctk.CTkLabel(
                    fila,
                    text=task["nombre"],
                    anchor="w",
                    justify="left",
                    wraplength=190,
                    text_color=texto_color,
                    font=ctk.CTkFont(
                        family="Segoe UI Variable Text",
                        size=13,
                        weight="bold" if not esta_lista else "normal",
                        slant="italic" if esta_lista else "roman",
                    ),
                )
                texto_tarea.pack(side="left", fill="x", expand=True, pady=4)


# ==========================================
# BLOQUE 4: INTERFAZ PRINCIPAL
# ==========================================
ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.geometry("400x400+1480+300")
app.attributes("-topmost", True)

nombre_usuario = cargar_configuracion()
app.title(f"{nombre_usuario}'s To-Do List")

header = ctk.CTkFrame(app, fg_color="transparent")
header.pack(fill="x", padx=20, pady=(18, 4))

lbl_titulo = ctk.CTkLabel(
    header,
    text=f"¡Hola, {nombre_usuario}!",
    font=ctk.CTkFont(family="Segoe UI Variable Display", size=18, weight="bold"),
    text_color="#F9FAFB",
)
lbl_titulo.pack(side="left")
lbl_kitty_header = ctk.CTkLabel(header, text="", fg_color="transparent")

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
    placeholder_text="Escribe aqui...",
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
    command=abrir_selector_hora,
)
btn_hora.pack(side="right", padx=(0, 4), pady=3)

selector_dia = ctk.CTkOptionMenu(
    marco_input,
    values=lista_dias_etiquetas,
    width=110,
    height=26,
    corner_radius=7,
    fg_color="#1D222A",
    button_color="#242B35",
    button_hover_color="#2E3744",
    dropdown_fg_color="#13161C",
    dropdown_hover_color="#1D222A",
    font=ctk.CTkFont(family="Segoe UI Variable Text", size=11),
    text_color="#D1D5DB",
)
selector_dia.pack(side="right", padx=(0, 4), pady=3)

footer = ctk.CTkFrame(app, fg_color="transparent", height=28)
footer.pack(side="bottom", fill="x", padx=16, pady=(0, 10))

btn_ajustes = ctk.CTkButton(
    footer,
    text="⚙",
    width=24,
    height=24,
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

cargar_tareas()
aplicar_tema(tema_actual)
verificar_recordatorios()

app.mainloop()
