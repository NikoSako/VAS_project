from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from .forms import order_form
from .models import Order, Angle
from django.db.models import Max
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from .serializers import OrderSerializer
import locale
from datetime import date

WORKDAYS = [0, 1, 2, 3, 4, 5]

BG_MONTHS = {
    'January': 'януари', 'February': 'февруари', 'March': 'март', 'April': 'април',
    'May': 'май', 'June': 'юни', 'July': 'юли', 'August': 'август',
    'September': 'септември', 'October': 'октомври', 'November': 'ноември', 'December': 'декември'
}
BG_DAYS = {
    'Monday': 'Понеделник', 'Tuesday': 'Вторник', 'Wednesday': 'Сряда', 'Thursday': 'Четвъртък',
    'Friday': 'Петък', 'Saturday': 'Събота', 'Sunday': 'Неделя'
}

def format_date_bg(d):
    try:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'C')
    formatted = d.strftime("%A, %d %B %Y")
    for en, bg in BG_MONTHS.items():
        formatted = formatted.replace(en, bg)
    for en, bg in BG_DAYS.items():
        formatted = formatted.replace(en, bg)
    return formatted

def next_available_date():
    result = Order.objects.aggregate(latest_end=Max('end_date'))
    last_order = result['latest_end']
    
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
            order.size = form.cleaned_data['size']
            order.length_m = form.cleaned_data['length_m']
            order.save()

            order.angles.all().delete()

            for key in request.POST:
                if key.startswith("angle_") and key.endswith("_quantity"):
                    angle_type = key.replace("_quantity", "").replace("angle", "")
                    quantity = int(request.POST.get(key))
                    if quantity > 0:
                        Angle.objects.create(order=order, type=angle_type, quantity=quantity)
                        
            return redirect('service_details', order_id = order.id)
    else:
        form = order_form()

    is_gutter = form['is_gutter'].value() == 'True' if form['is_gutter'].value() else True
    angles_for_display = [
        ('gutter_inner_90', 'Вътрешен ъгъл 90°'),
        ('gutter_outer_90', 'Външен ъгъл 90°'),
    ]if is_gutter else [
                ('pipe_45', 'Кривка 45°'),
                ('pipe_72', 'Кривка 72°'),
                ('pipe_90', 'Кривка 90°'),
            ]

    return render(request, 'service.html', {'form': form, 'is_gutter': is_gutter, 'angles': angles_for_display})

@login_required
def service_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_superuser and order.user != request.user:
        return redirect('dashboard')

    angles = Angle.objects.filter(order=order)

    start_date_bg = format_date_bg(order.start_date) if order.start_date else ''
    end_date_bg = format_date_bg(order.end_date) if order.end_date else ''

    return render(request, 'service_details.html', {
        'order': order,
        'angles': angles,
        'start_date_bg': start_date_bg,
        'end_date_bg': end_date_bg,
    })

@login_required
def dashboard(request):
    if request.user.is_superuser:
        orders = Order.objects.all().order_by('-id')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-id')

    print(f"DEBUG dashboard: fetched {orders.count()} order(s) for user {request.user}")
    for order in orders:
        order.start_date_bg = format_date_bg(order.start_date)
        order.end_date_bg = format_date_bg(order.end_date)

    return render(request, 'dashboard.html', {'orders': orders})

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
        quantity = post_data.get(f'angle_{key}_quantity')
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

    base = base_price[key][order.colour_type][order.size]
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
        price += quantity * (15.30 if angle_type.startswith('gutter') else 4.80)

    return round(price, 2)

@require_POST
def preview_order(request):
    form = order_form(request.POST)
    if form.is_valid():
        order_data = request.POST.copy()
        request.session['order_data'] = order_data

        order = form.save(commit=False)
        order.user = request.user
        start, end = next_available_date()
        order.start_date, order.end_date = start, end

        total_price = calculate_price(order, order_data)

        angles = extract_angles(order_data)

        try:
            length = float(order_data.get('length_m', 0))
        except (TypeError, ValueError):
            length = 0

        if order.service_type == 'gutter':
            bracket_count = int(length * 2)
        else:
            bracket_count = int(length)

        return render(request, 'preview_order.html', {
            'form': form,
            'order': order,
            'size': order_data.get('size'),
            'length_m': order_data.get('length_m'),
            'bracket_count': bracket_count,
            'angles': {
                'Вътрешен ъгъл 90°': angles.get('gutter_inner_90', 0),
                'Външен ъгъл 90°': angles.get('gutter_outer_90', 0),
                'Кривка 45°': angles.get('pipe_45', 0),
                'Кривка 72°': angles.get('pipe_72', 0),
                'Кривка 90°': angles.get('pipe_90', 0),
            },
            'total_price': total_price,
            'start_date_bg': format_date_bg(start),
            'end_date_bg': format_date_bg(end),
        })
    return redirect('create_order')

@require_POST
@login_required
def confirm_order(request):
    post_data = request.session.get('order_data')
    if not post_data:
        print("DEBUG: order_data not found in session")
        return redirect('create_order')
    
    form = order_form(post_data)
    if form.is_valid():
        order = form.save(commit=False)
        order.user = request.user
        order.start_date, order.end_date = next_available_date()
        order.total_price = calculate_price(order, post_data)
        order.save()
        print(f"DEBUG: Order saved - ID: {order.id}")

        Angle.objects.filter(order=order).delete()

        angles = extract_angles(post_data)
        for angle_type, quantity in angles.items():
            if quantity > 0:
                Angle.objects.create(order=order, type=angle_type, quantity=quantity)

        del request.session['order_data']
        return redirect('service_details', order_id=order.id)
    
    return redirect('dashboard')

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def order_api(request, order_id=None):
    if request.method == 'GET':
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if not request.user.is_superuser and order.user != request.user:
                    return Response(
                        {"error": "Нямате достъп до тази поръчка"},
                        status=status.HTTP_403_FORBIDDEN
                    )
                serializer = OrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except:
                return Response(
                    {"error": "Поръчката не е намерена"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if request.user.is_superuser:
                orders = Order.objects.all()
            else:
                orders = Order.objects.filter(user=request.user)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method in ['PUT', 'PATCH']:
        if not order_id:
            return Response(
                {"error": "Изисква се ID на поръчка"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.get(id=order_id)
            if not request.user.is_superuser and order.user != request.user:
                return Response(
                    {"error": "Нямате достъп до тази поръчка"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = OrderSerializer(
                order,
                data=request.data,
                partial=request.method == 'PATCH'
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except ObjectDoesNotExist:
            return Response(
                {"error": "Поръчката не е намерена"},
                status=status.HTTP_404_NOT_FOUND
            )
        
    elif request.method == 'DELETE':
        if not order_id:
            return Response(
                {"error": "Изисква се ID на поръчка"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            order = Order.objects.get(id=order_id)
            if not request.user.is_superuser and order.user != request.user:
                return Response(
                    {"error": "Нямате достъп до тази поръчка"},
                    status=status.HTTP_403_FORBIDDEN
                )
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except ObjectDoesNotExist:
            return Response(
                {"error": "ПОръчката не е намерена"},
                status=status.HTTP_404_NOT_FOUND
            )
    