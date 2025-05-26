from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .forms import order_form
from .models import Order, Angle
from django.db.models import Max

WORKDAYS = [0, 1, 2, 3, 4, 5]

def next_available_date():
    last_order = Order.objects.aggregate(Max('end_date'))['end_date_max']
    start = date(2025, 7, 1) if not last_order else last_order + timedelta(days=1)

    days = 0
    while True:
        test_days = [start + timedelta(days=i) for i in range(6)]
        valid = [d for d in test_days if d.weekday() in WORKDAYS]
        if len(valid) >= 4:
            return valid[0], valid[3]
        start += timedelta(days=1)

def create_order(request):
    if request.method == 'POST':
        form = order_form(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.start_date, order.end_date = next_available_date()
            order.total_price = calculate_price(order, request.POST)
            order.save()

            for i in range(1, 3):
                angle_type = request.POST.get(f'angle_{i}_type')
                angle_quantity = request.POST.get(f'angle_{i}_quantity')
                if angle_type and angle_quantity:
                    Angle.objects.create(order = order, type = angle_type, quantity = int(angle_quantity))
            return redirect('service_details', order_id = order.id)
    else:
        form = order_form()
    return render(request, 'service.html', {'form': form})

@login_required
def service_details(request, order_id):
    order = Order.objects.get(id = order_id, user = request.user)
    return render(request, 'service_details.html', {'order': order})

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
    if colour == 'RAL':
        colour = 'RAL'

    base = base_price[key][colour][order.size]
    price = order.length_m * base

    if order.is_gutter:
        brackets = (order.length_m * 2)
        if order.colour_type == 'медна':
            price += brackets * (6.90 if order.size == '5' else 7.80)
        else:
            price += brackets * (1.20 if order.size == '5' else 1.60)
    else:
        brackets = (order.length_m * 1)
        price += brackets * {
            'поцинкована': 1.40,
            'RAL': 1.80,
            'титан-цинк': 4.80,
            'медна': 5.20 if order.size == '80' else 5.90,
        }[order.colour_type]

    for i in range(1, 3):
        type = post_data.get(f'angle_{i}_type')
        quantity = int(post_data.get(f'angle_{i}_quantity') or 0)
        if quantity == 0:
            continue
        if type.startswith('gutter'):
            price += quantity * 15.30
        else:
            price += quantity * 4.80

    return round(price, 2)