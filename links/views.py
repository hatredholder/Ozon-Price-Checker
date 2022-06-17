from multiprocessing import Pool

from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from .forms import AddLinkForm
from .models import Link
from .utils import get_info


def home_view(request):
    """Home view"""
    no_discounted = 0
    error = None

    form = AddLinkForm(request.POST or None)

    # Add a URL
    if request.method == 'POST':
        try:
            form_name, form_current_price = get_info(form['url'].value().split('/')[4])
            form = form.save(commit=False)
            form.url = "/".join(form.url.split('/')[:5])
            form.name, form.current_price = form_name, form_current_price
            form.save()
        except AttributeError as e:
            print(e)
            error = "Ой! Не удалось получить название или цену товара.."
        except Exception as e: 
            print(e)
            error = "Ой! Ссылка которую вы ввели недействительна.."
    
    form = AddLinkForm()

    qs = Link.objects.all()
    items_no = qs.count()

    # Add item to discount list
    discount_list = []
    if items_no > 0:
        for item in qs:
            if item.old_price > item.current_price:
                discount_list.append(item)
            no_discounted = len(discount_list)

    context = {
        'qs':qs,
        'items_no':items_no,
        'no_discounted':no_discounted,
        'discount_list': discount_list,
        'form':form,
        'error':error
    }

    return render(request, 'links/main.html', context)

class LinkDeleteView(DeleteView):
    """URL Deletion view"""
    model = Link
    success_url = reverse_lazy('home')

def update_prices(request):
    """Update all the prices view"""
    qs = Link.objects.all()
    result = []

    # Updating the prices with the use of multiprocessing
    for i in qs:
        result.append(get_info(i.url.split('/')[4]))

    num = 0
    for i in qs:
        if result[num][1] != i.current_price:
            i.old_price = i.current_price
            i.current_price = result[num][1]
            diff = result[num][1] - i.old_price
            i.price_difference = round(diff, 2)
            i.save()
        num += 1
    return redirect('home')
