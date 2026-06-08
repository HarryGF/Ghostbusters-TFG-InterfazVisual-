import mysql.connector
import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
HOST     = os.getenv("DB_HOST")
PORT     = int(os.getenv("DB_PORT", 17254))
USUARIO  = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
BASE     = os.getenv("DB_NAME")
SSL_CA   = "ca.pem"

archivo = "partidas.sql"

try:
    conexion = mysql.connector.connect(
        host=HOST, port=PORT, user=USUARIO,
        password=PASSWORD, database=BASE, ssl_ca=SSL_CA
    )
    cursor = conexion.cursor()

    # 3. Leer el SQL
    with open(archivo, 'r', encoding='utf-8') as f:
        sql_script = f.read().strip()

    if not sql_script:
        sys.exit()

    cursor.execute(sql_script)
    conexion.commit()

    cursor.close()
    conexion.close()

except mysql.connector.Error as err:
    print(f"Error de base de datos: {err}")
except Exception as e:
    print(f"Ha ocurrido un error inesperado: {e}")