from django import forms
from .models import Order, Angle, ALUMINIUM_COLOURS, RAL_COLOURS, GUTTER_SIZES, PIPE_SIZES, CORNER_TYPES

class order_form(forms.ModelForm):
    ral_code = forms.ChoiceField(
        choices=RAL_COLOURS,
        required=False,
        label="RAL код"
    )

    ALL_ANGLES = {
        True: [
            ('gutter_inner_90', 'Вътрешен ъгъл 90°'),
            ('gutter_outer_90', 'Външен ъгъл 90°')
        ],
        False: [
            ('pipe_45', 'Кривка 45°'),
            ('pipe_72', 'Кривка 72°'),
            ('pipe_90', 'Кривка 90°')
        ]
    }

    class Meta:
        model = Order
        fields = ['is_gutter', 'colour_type', 'ral_code', 'size', 'length_m']
        labels = {
            'is_gutter': 'Улуци или тръби',
            'colour_type': 'Тип алуминий',
            'size': 'Размер',
            'length_m': 'Дължина (в метри)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.fields['is_gutter'].widget = forms.Select(choices=[(True, 'Улуци'), (False, 'Водосточни тръби')])

        is_gutter = self.initial.get('is_gutter', True)
        if isinstance(is_gutter, str):
            is_gutter = is_gutter == 'True'
    
        if is_gutter:
            self.fields['size'].widget = forms.Select(choices=GUTTER_SIZES)
        else:
            self.fields['size'].widget = forms.Select(choices=PIPE_SIZES)

        colour = self.data.get('colour_type', '') if self.data else self.initial.get('colour_type', '')
        if colour == 'RAL':
            self.fields['ral_code'].choices = RAL_COLOURS
            self.fields['ral_code'].widget.attrs.pop('style', None)
        else:
            self.fields['ral_code'].widget.attrs.update({'style': 'display:none;'})
            self.fields['ral_code'].required = False

    def clean(self):
        cleaned_data = super().clean()
        colour_type = cleaned_data.get('colour_type')
        ral_code = cleaned_data.get('ral_code')
        if colour_type == 'RAL' and not ral_code:
            raise forms.ValidationError("Моля, изберете код по RAL")
        return cleaned_data