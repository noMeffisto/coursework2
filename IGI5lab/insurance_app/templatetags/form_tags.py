from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adds a CSS class to a form field's widget.
    """
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder_text):
    """
    Adds a placeholder attribute to a form field's widget.
    """
    return field.as_widget(attrs={"placeholder": placeholder_text}) 