import os


def is_cloud_env() -> bool:
    if bool(os.getenv("NPIAI_SERVICE_MODE")):
        return True
    return False
