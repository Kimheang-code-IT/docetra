from app.core.config import settings
def cors_options(): return {"allow_origins":settings.cors_allowed_origins,"allow_credentials":True,"allow_methods":["GET","POST","PUT","PATCH","DELETE","OPTIONS"]}
