from netbox.plugins import PluginConfig


class GestionImpactsConfig(PluginConfig):
    name = 'gestion_impacts'
    verbose_name = 'Gestion des impacts'
    description = 'Gestion des impacts'
    version = '0.1'
    base_url = 'gestion_impacts'
    required_settings = []
    default_settings = {}


config = GestionImpactsConfig
