from friendly_id import FriendlyID

from django.shortcuts import render_to_response
from django.template import RequestContext

__all__ = ('FriendlyID', 'render_to')

def render_to(template):
    """
    Decorator for Django views that sends returned dict to render_to_response function
    with given template and RequestContext as context instance.

    If view doesn't return dict then decorator simply returns output.
    Additionally view can return two-tuple, which must contain dict as first
    element and string with template name as second. This string will
    override template name, given as parameter
    
    Example usage:

    @render_to('myapp/templatename.html')
    def my_view(request, tree_number):
        return locals()

    Credit to DjangoSnippet #TODO look up the snippet

    Changes made:
        view can simply return locals(), this decorator will make a copy (as we
        should never edit the locals() dict) and remove any item name 'request'
        from the output dict. This may not be desirable in cases, but I haven't
        come across any.
    """
    def renderer(func):
        def wrapper(request, *args, **kw):
            templ = template
            output = func(request, *args, **kw)
            if isinstance(output, (list, tuple)):
                templ, output = output
            if isinstance(output, dict):
                # Remove request if given, we are using the one given in the input 
                output = output.copy()
                output.pop('request', None)
                return render_to_response(template, output, RequestContext(request))
            return output
        return wrapper
    return renderer


