from django import forms
from .models import Order, GUTTER_SIZES, PIPE_SIZES, ALUMINIUM_COLOURS, RAL_COLOURS

class order_form(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['is_gutter', 'colour_type', 'ral_code', 'size', 'length_m']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['ral_code'].required = False
        self.fields['ral_code'].widget = forms.Select(choices=RAL_COLOURS)
        self.fields['ral_code'].label = "RAL код"

        self.fields['colour_type'].label = "Вид алуминий"
        self.fields['is_gutter'].label = "Продукт (улуци или тръби)"
        self.fields['size'].label = "Размер"
        self.fields['length_m'].label = "Дължина (в метри)"

        is_gutter_val = self.data.get('is_gutter') or self.initial.get('is_gutter')
        is_gutter = is_gutter_val == 'True' or is_gutter_val is True

        self.fields['size'].widget = forms.Select(choices=GUTTER_SIZES if is_gutter else PIPE_SIZES)

    def clean(self):
        cleaned_data = super().clean()
        colour_type = cleaned_data.get('colour_type')
        ral_code = cleaned_data.get('ral_code')
        if colour_type == 'RAL' and not ral_code:
            raise forms.ValidationError("Моля, изберете код по RAL")
        return cleaned_data