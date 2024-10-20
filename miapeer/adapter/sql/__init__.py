from os import environ as env

ifnull = "isnull" if env.get("MIAPEER_ENV") == "Production" else "ifnull"
substr = "substring" if env.get("MIAPEER_ENV") == "Production" else "substr"
