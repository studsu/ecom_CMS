#If any plugin/app ships a template at templates/hooks/<hook_name>.html, we can include it with {% render_hook "hook_name" %}.


from django import template
from django.template.loader import select_template, TemplateDoesNotExist

register = template.Library()

@register.simple_tag(takes_context=True)
def render_hook(context, hook_name, **kwargs):
    """
    Renders the first found template named hooks/<hook_name>.html across app template dirs.
    Plugins can inject UI by shipping templates at that path.
    """
    candidates = [f"hooks/{hook_name}.html"]
    try:
        t = select_template(candidates)
        new_ctx = context.flatten()
        new_ctx.update(kwargs)
        return t.render(new_ctx)
    except TemplateDoesNotExist:
        return ""  # no-op if nothing provides this hook
