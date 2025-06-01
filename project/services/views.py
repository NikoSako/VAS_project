from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .forms import order_form
from .models import Order, Angle
from django.db.models import Max

WORKDAYS = [0, 1, 2, 3, 4, 5]

def next_available_date():
    last_order = Order.objects.aggregate(Max('end_date'))['end_date_max']
    start = date(2025, 7, 1) if not last_order else last_order + timedelta(days=1)

    workdays = []
    while len(workdays) < 4:
        if start.weekday() in WORKDAYS:
            workdays.append(start)
        start += timedelta(days=1)
    return workdays[0], workdays[-1]

def create_order(request):
    if request.method == 'POST':
        form = order_form(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.start_date, order.end_date = next_available_date()
            order.total_price = calculate_price(order, request.POST)
            order.save()

            order.angles.all().delete()

            for key in request.POST:
                if key.startswith("angle_"):
                    quantity = int(request.POST.get(key) or 0)
                    if quantity > 0:
                        angle_type = key.replace("angle_", "")
                        Angle.objects.create(order=order, type=angle_type, quantity=quantity)
                        
            return redirect('service_details', order_id = order.id)
    else:
        form = order_form()

    angles_for_display = []
    if request.method == 'POST':
        is_gutter_1 = request.POST.get('is_gutter')
        if is_gutter_1 == 'True':
            angles_for_display = [
                ('gutter_inner_90', 'Вътрешен ъгъл 90°'),
                ('gutter_outer_90', 'Външен ъгъл 90°'),
            ]
        else:
            angles_for_display = [
                ('pipe_45', 'Кривка 45°'),
                ('pipe_72', 'Кривка 72°'),
                ('pipe_90', 'Кривка 90°'),
            ]
    else:
        angles_for_display = [
            ('gutter_inner_90', 'Вътрешен ъгъл 90°'),
            ('gutter_outer_90', 'Външен ъгъл 90°'),
        ]
    
    is_gutter = form['is_gutter'].value() == 'True' if form['is_gutter'].value() else True

    return render(request, 'service.html', {'form': form, 'is_gutter': is_gutter, 'angles': angles_for_display})

@login_required
def service_details(request, order_id):
    order = get_object_or_404(Order, id = order_id, user = request.user)
    return render(request, 'service_details.html', {'order': order})

def extract_angles(post_data):
    angle_keys = [
        'gutter_inner_90',
        'gutter_outer_90',
        'pipe_45',
        'pipe_72',
        'pipe_90',
    ]
    angles = {}
    for key in angle_keys:
        quantity = post_data.get(f'angle_{key}')
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = 0
        angles[key] = quantity if quantity >= 0 else 0
    return angles

def calculate_price(order, post_data):
    base_price = {
        'улуци': {
            'поцинкована': {'5': 6.00, '6': 7.20},
            'RAL': {'5': 8.70, '6': 11.80},
            'титан-цинк': {'5': 35.90, '6': 45.10},
            'медна': {'5': 46.20, '6': 56.20},
        },
        'тръби': {
            'поцинкована': {'80': 6.70, '100': 7.15},
            'RAL': {'80': 8.00, '100': 8.90},
            'титан-цинк': {'80': 43.50, '100': 47.00},
            'медна': {'80': 52.00, '100': 56.00},
        },
    }

    if order.is_gutter:
        key = 'улуци'
    else:
        key = 'тръби'

    colour = order.colour_type

    base = base_price[key][colour][order.size]
    price = order.length_m * base

    if order.is_gutter:
        brackets = (order.length_m * 2)
        if order.colour_type == 'медна':
            price += brackets * (6.90 if order.size == '5' else 7.80)
        else:
            price += brackets * (1.20 if order.size == '5' else 1.60)
    else:
        brackets = order.length_m
        bracket_prices =  {
            'поцинкована': 1.40,
            'RAL': 1.80,
            'титан-цинк': 4.80,
            'медна': 5.20 if order.size == '80' else 5.90,
        }
        price += brackets * bracket_prices[order.colour_type]

    angles = extract_angles(post_data)
    for angle_type, quantity in angles.items():
        if quantity == 0:
            continue
        if angle_type.startswith('gutter'):
            price += quantity * 15.30
        else:
            price += quantity * 4.80

    return round(price, 2)