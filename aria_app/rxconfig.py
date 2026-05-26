import reflex as rx

# Reflex 0.9+: theme is configured through RadixThemesPlugin, not App(theme=...).
_PLUGINS: list = []
try:
    from reflex.plugins import RadixThemesPlugin  # type: ignore

    _PLUGINS.append(
        RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                has_background=False,
                radius="large",
                accent_color="orange",
            )
        )
    )
except Exception:
    pass  # older reflex — App(theme=...) is still used in aria_app.py

# Disable sitemap plugin to silence the default-on warning.
_DISABLE: list = []
try:
    from reflex.plugins.sitemap import SitemapPlugin  # type: ignore
    _DISABLE = [SitemapPlugin]
except Exception:
    pass

config = rx.Config(
    app_name="aria_app",
    frontend_port=3000,
    backend_port=8000,
    tailwind=None,
    show_built_with_reflex=False,
    plugins=_PLUGINS,
    disable_plugins=_DISABLE,
)
