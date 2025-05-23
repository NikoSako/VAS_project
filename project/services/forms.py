from django import forms
from .models import Order, Angle, ALUMINIUM_COLOURS, RAL_COLOURS, GUTTER_SIZES, PIPE_SIZES, CORNER_TYPES

class order_form(forms.ModelForm):
    angle_1_type = forms.ChoiceField(choices=CORNER_TYPES, label="Тип ъгъл 1", required=False)
    angle_1_quantity = forms.IntegerField(min_value=0, label="Брой 1", required=False)

    angle_2_type = forms.ChoiceField(choices=CORNER_TYPES, label="Тип ъгъл 2", required=False)
    angle_2_quantity = forms.IntegerField(min_value=0, label="Брой 2", required=False)

    class Meta:
        model = Order
        fields = ['is_gutter', 'colour_type', 'ral_code', 'size', 'length_m']

    def clean(self):
        cleaned_data = super().clean()
        colour_type = cleaned_data.get('colour_type')
        ral_code = cleaned_data.get('ral_code')
        if colour_type == 'RAL' and not ral_code:
            raise forms.ValidationError("Моля, изберете цвят(код) по RAL")
        return cleaned_data