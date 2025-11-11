from django import forms

class TailwindFormMixin(forms.Form):
    """
    APPLY STYLES AUTOMATICALLY: This Mixin finds every non-checkbox field 
    and injects the 'form-input' class, simplifying all future templates.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Loop through every field defined in the form
        for field_name, field in self.fields.items():
            # Exclude checkboxes/radio buttons, as they require custom styling logic
            if not isinstance(field.widget, (forms.widgets.CheckboxInput, forms.widgets.RadioSelect)):
                
                # Get existing classes (if any) and append our Tailwind class
                current_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{current_classes} form-input' 