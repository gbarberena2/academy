from config_db import app
import routes  # Importamos las rutas

if __name__ == "__main__":
    from config_db import probar_conexion
    probar_conexion()  # Verificamos conexión antes de ejecutar la app
    app.run(host='0.0.0.0', port=5516, debug=True)
