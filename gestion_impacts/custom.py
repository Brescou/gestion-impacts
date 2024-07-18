from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.urls import reverse
from django.utils.http import quote
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from netbox.tables import columns
from utilities.permissions import get_permission_for_model
from utilities.views import get_viewname

from gestion_impacts.models import Impact


class CustomActionsColumn(columns.ActionsColumn):

    def render(self, record, table, **kwargs):
        # Skip dummy records (e.g. available VLANs) or those with no actions
        if not getattr(record, 'pk', None) or not self.actions:
            return ''

        model = table.Meta.model
        if request := getattr(table, 'context', {}).get('request'):
            return_url = request.GET.get('return_url', request.get_full_path())
            url_appendix = f'?return_url={quote(return_url)}'
        else:
            url_appendix = ''

        html = ''

        # Compile actions menu
        button = None
        dropdown_class = 'secondary'
        dropdown_links = []
        user = getattr(request, 'user', AnonymousUser())

        # Retrieve the related Impact instance
        impact_id = None
        if hasattr(record, 'impact'):
            impact = Impact.objects.filter(ip_address=record).first()
            if impact:
                impact_id = impact.pk

        for idx, (action, attrs) in enumerate(self.actions.items()):
            permission = get_permission_for_model(model, attrs.permission)
            if attrs.permission is None or user.has_perm(permission):
                # Customize the URL creation for 'edit' and 'delete' actions
                if impact_id is not None:
                    url = reverse(f'plugins:gestion_impacts:impact_{action}', kwargs={'pk': impact_id})
                else:
                    # Redirect to the Impact creation view with the IP address as a parameter
                    url = f"{reverse('plugins:gestion_impacts:impact_add')}?ip_address={record.pk}"

                # Render a separate button if a) only one action exists, or b) if split_actions is True
                if len(self.actions) == 1 or (self.split_actions and idx == 0):
                    dropdown_class = attrs.css_class
                    button = (
                        f'<a class="btn btn-sm btn-{attrs.css_class}" href="{url}{url_appendix}" type="button">'
                        f'<i class="mdi mdi-{attrs.icon}"></i></a>'
                    )

                # Add dropdown menu items
                else:
                    dropdown_links.append(
                        f'<li><a class="dropdown-item" href="{url}{url_appendix}">'
                        f'<i class="mdi mdi-{attrs.icon}"></i> {attrs.title}</a></li>'
                    )

        # Create the actions dropdown menu
        toggle_text = _('Toggle Dropdown')
        if button and dropdown_links:
            html += (
                f'<span class="btn-group dropdown">'
                f'  {button}'
                f'  <a class="btn btn-sm btn-{dropdown_class} dropdown-toggle" type="button" data-bs-toggle="dropdown" style="padding-left: 2px">'
                f'  <span class="visually-hidden">{toggle_text}</span></a>'
                f'  <ul class="dropdown-menu">{"".join(dropdown_links)}</ul>'
                f'</span>'
            )
        elif button:
            html += button
        elif dropdown_links:
            html += (
                f'<span class="btn-group dropdown">'
                f'  <a class="btn btn-sm btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">'
                f'  <span class="visually-hidden">{toggle_text}</span></a>'
                f'  <ul class="dropdown-menu">{"".join(dropdown_links)}</ul>'
                f'</span>'
            )

        # Render any extra buttons from template code
        if self.extra_buttons:
            template = Template(self.extra_buttons)
            context = getattr(table, "context", Context())
            context.update({'record': record})
            html = template.render(context) + html

        return mark_safe(html)
