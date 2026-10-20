"""Renderizador de formulários do Consus (research R12).

Com ele, `{{ form }}` e `{{ form.campo.as_field_group }}` já saem com rótulo, ajuda, erro,
`aria-describedby` e `aria-invalid` em todas as features.
"""

from django.forms.renderers import TemplatesSetting


class RenderizadorConsus(TemplatesSetting):
    form_template_name = "components/formulario.html"
    field_template_name = "components/campo.html"
