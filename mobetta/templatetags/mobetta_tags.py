from django import template
from django.template.base import token_kwargs

register = template.Library()


class ModalNode(template.Node):
    template = 'mobetta/include/modal.html'

    def __init__(self, nodelist, **kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()[1:]
        kwargs = token_kwargs(bits, parser)
        nodelist = parser.parse(('endmodal',))
        parser.delete_first_token()
        return cls(nodelist, **kwargs)

    def render(self, context):
        kwargs = {key: val.resolve(context) for key, val in self.kwargs.items()}
        modal_context = {
            'csrf_token': context.get('csrf_token'),
            'body': self.nodelist.render(context),
        }
        modal_context.update(kwargs)
        new_context = context.new(modal_context)
        template = context.template.engine.get_template(self.template)
        return template.render(new_context)


# @register.inclusion_tag('')
@register.tag
def modal(parser, token):
    return ModalNode.handle_token(parser, token)
