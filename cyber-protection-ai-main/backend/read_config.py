"""
read_config.py - Lee _pcp_config.ini y lo imprime como pares CLAVE=VALOR,
para que start_pcp.bat los capture con un simple 'for /f' y arme las
variables PG_PASS / PG_PORT / PG_DB / PG_USER.

Uso:
    python read_config.py "ruta\\a\\_pcp_config.ini"
"""
import sys
import configparser

if len(sys.argv) < 2:
    print("ERROR: falta la ruta al archivo de configuracion", file=sys.stderr)
    sys.exit(1)

config = configparser.ConfigParser()
leidos = config.read(sys.argv[1], encoding="utf-8-sig")

if not leidos:
    print("ERROR: no se pudo leer el archivo de configuracion", file=sys.stderr)
    sys.exit(1)

pg = config["postgresql"]
print(f"PG_PASS={pg.get('password', '')}")
print(f"PG_PORT={pg.get('puerto', '5432')}")
print(f"PG_DB={pg.get('base_datos', 'cyber_protection_ai')}")
print(f"PG_USER={pg.get('usuario', 'postgres')}")
