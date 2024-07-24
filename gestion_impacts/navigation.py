from netbox.plugins import PluginMenuButton, PluginMenuItem, PluginMenu

gestion_impacts_button = PluginMenuButton(
    link='plugins:gestion_impacts:impact_add',
    title='Ajouter un impact',
    icon_class='mdi mdi-plus-thick',
)

# gestion_impacts_import_button = PluginMenuButton(
#     link='plugins:gestion_impacts:impact_import',
#     title='Importer des impacts',
#     icon_class='mdi mdi-upload',
# )

menu_impacts = PluginMenuItem(
    link='plugins:gestion_impacts:impact_list',
    link_text='Impacts',
    buttons=(gestion_impacts_button,),
)

menu = PluginMenu(
    label='Gestion des impacts',
    groups=(
        ('', (menu_impacts,)),
    ),
    icon_class='mdi mdi-alert'
)
