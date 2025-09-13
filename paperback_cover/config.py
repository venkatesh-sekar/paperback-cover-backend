from dynaconf import Dynaconf

settings = Dynaconf(
    environments=True,
    envvar_prefix=False,
    load_dotenv=True,
    dotenv_override=True,
    dotenv_verbose=True,
    env_switcher="PAPERBACK_COVER_ENV",
    # dotenv_path='.envs/local/.env',
    settings_files=[
        "settings.yaml",
        "settings.prod.yaml",
        "settings.local.yaml",
        ".secrets.yaml",
    ],
    merge_enabled=True,
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
