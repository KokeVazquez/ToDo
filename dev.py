import os
import sys
import time
import subprocess

# Archivo a vigilar y ejecutar
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(DIR_ACTUAL, "ToDo.py")

def obtener_mtime():
    try:
        return os.path.getmtime(TARGET)
    except OSError:
        return 0

def main():
    print("=" * 60)
    print("🚀 MODO DESARROLLO (Auto-Recarga Activa)")
    print(f"👀 Observando: {os.path.basename(TARGET)}")
    print("💡 Cada vez que guardes el archivo (Ctrl + S), la app se reiniciará.")
    print("🛑 Para detenerlo, presiona Ctrl + C en esta terminal.")
    print("=" * 60)

    mtime_anterior = obtener_mtime()
    proceso = subprocess.Popen([sys.executable, TARGET])
    aviso_cierre_mostrado = False

    try:
        while True:
            time.sleep(0.4)
            mtime_actual = obtener_mtime()

            # Si detectamos que se modificó ToDo.py
            if mtime_actual != mtime_anterior:
                mtime_anterior = mtime_actual
                aviso_cierre_mostrado = False
                print("\n🔄 [AUTO-RELOAD] Cambios detectados en ToDo.py. Reiniciando...")

                # Cerramos el proceso anterior si sigue abierto
                if proceso.poll() is None:
                    proceso.terminate()
                    try:
                        proceso.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proceso.kill()

                # Lanzamos la nueva versión
                proceso = subprocess.Popen([sys.executable, TARGET])

            # Si el usuario cerró la ventana manualmente
            elif proceso.poll() is not None and not aviso_cierre_mostrado:
                print("⏸️  [PAUSA] Ventana cerrada. Guarda cambios en ToDo.py (Ctrl + S) para relanzarla...")
                aviso_cierre_mostrado = True

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo modo desarrollo...")
        if proceso.poll() is None:
            proceso.terminate()
            try:
                proceso.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proceso.kill()
        print("✅ Sesión finalizada.")

if __name__ == "__main__":
    main()

