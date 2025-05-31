from django.db import models
from django.contrib.auth.models import User

ALUMINIUM_COLOURS = [
    ('поцинкована', 'Поцинкована'),
    ('титан-цинк', 'Титан-цинк'),
    ('медна', 'Медна'),
    ('RAL', 'Цвят по RAL'),
]

RAL_COLOURS = [
    ('9010', 'RAL9010 - Бяло'),
    ('9007', 'RAL9007 - Алуминиево сиво'),
    ('9006', 'RAL9006 - Алуминиево бяло'),
    ('9002', 'RAL9002 - Сиво-бяло'),
    ('7043', 'RAL7043 - Тъмно сиво'),
    ('7024', 'RAL7024 - Графитено сиво'),
    ('7016', 'RAL7016 - Антрацит'),
    ('8017', 'RAL8017 - Тъмно кафяво'),
    ('3000', 'RAL3000 - Огнено червено'),
]

GUTTER_SIZES = [
    ('5', '5"'),
    ('6', '6"'),
]

PIPE_SIZES = [
    ('80', 'Ф80'),
    ('100', 'Ф100'),
]

CORNER_TYPES = [
    ('gutter_inner_90', 'Улук вътрешен ъгъл 90°'),
    ('gutter_outer_90', 'Улук външен ъгъл 90°'),
    ('pipe_45', 'Кривка 45°'),
    ('pipe_72', 'Кривка 72°'),
    ('pipe_90', 'Кривка 90°'),
]

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    is_gutter = models.BooleanField()
    colour_type = models.CharField(max_length=20, choices=ALUMINIUM_COLOURS)
    ral_code = models.CharField(max_length=10, blank=True, null=False)
    size = models.CharField(max_length=10)
    length_m = models.FloatField()
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.FloatField()

    def __str__(self):
        return f"Поръчка на {self.user.username} от {self.created_on.date}"
    
class Angle(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="angles")
    type = models.CharField(max_length=20, choices=CORNER_TYPES)
    quantity = models.IntegerField()