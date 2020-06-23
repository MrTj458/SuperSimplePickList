import os
from uuid import uuid4
from urllib.parse import urlencode
import requests
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import Shop


def pick_list(request):
    """Get all of the products and create the pick list"""
    shop = Shop.objects.get(name=request.GET.get('shop'))
    ids = ','.join(request.GET.getlist('ids[]'))  # Format id's

    # Make request for orders
    res = requests.get(
        f'https://{shop.name}/admin/api/2020-04/orders.json?ids={ids}',
        headers={
            'X-Shopify-Access-Token': shop.access_token
        }
    )
    orders = res.json()['orders']

    # Create list
    pl = {}
    for order in orders:
        for product in order['line_items']:
            if pl.get(product['product_id']) is None:
                # Add product to pick list
                pl[product['product_id']] = {
                    'title': product['title'],
                    'product_id': product['product_id'],
                    'images': requests.get(f'https://{shop.name}/admin/api/2020-04/products/{product["product_id"]}/images.json?fields=src', headers={'X-Shopify-Access-Token': shop.access_token}).json(),
                    'variants': {}
                }

            if pl.get(product['product_id'])['variants'].get(product['variant_id']) is None:
                # Add variant to pick list
                pl[product['product_id']]['variants'][product['variant_id']] = {
                    'title': product['variant_title'],
                    'sku': product['sku'],
                    'quantity': product['quantity'],
                }
            else:
                # Variant already in list, increment quantity
                pl[product['product_id']]['variants'][product['variant_id']
                                                      ]['quantity'] += product['quantity']

    return render(request, 'app/list.html', {'pick_list': pl})


def app(request):
    """Main app page"""
    shop_name = request.GET.get('shop')
    shop = Shop.objects.filter(name=shop_name)

    # The shop is not in the database or is missing an api key
    if len(shop) == 0 or shop[0].access_token == '':
        # re-build the url to pass query params to auth route
        base_url = reverse('app:auth')
        query = urlencode(request.GET)
        url = f'{base_url}?{query}'
        return redirect(url)

    return render(request, 'app/app.html')


def auth(request):
    """Begin the oauth process with shopify."""
    shop_name = request.GET.get('shop')
    shop_list = Shop.objects.filter(name=shop_name)

    nonce = uuid4()
    scope = 'read_orders,read_products'

    # Check if the shop has been created before
    if len(shop_list) == 0:
        shop = Shop(name=shop_name, nonce=nonce)
    else:
        shop = shop_list[0]
        shop.nonce = nonce

    shop.save()

    url = f"https://{shop_name}/admin/oauth/authorize?client_id={os.environ.get('SHOPIFY_API_KEY')}&scope={scope}&redirect_uri=https://6756426a3ae1.ngrok.io/app/authcallback&state={nonce}"

    return redirect(url)


def auth_callback(request):
    """Retrieve access token with code given after user accepts app install."""
    shop_name = request.GET.get('shop')
    nonce = request.GET.get('state')
    shop = Shop.objects.get(name=shop_name)

    # Check valid nonce
    if shop.nonce != nonce:
        return HttpResponseBadRequest('Nonce values do not match.')

    # Everything valid request access token
    code = request.GET.get('code')
    res = requests.post(f"https://{shop_name}/admin/oauth/access_token", {
        'client_id': os.environ.get('SHOPIFY_API_KEY'),
        'client_secret': os.environ.get('SHOPIFY_SECRET'),
        'code': code,
    })

    token = res.json().get('access_token')
    scope = res.json().get('scope')

    # Save access token and scope
    shop.access_token = token
    shop.scope = scope
    shop.save()

    # Setup the app/uninstalled webhook
    res = requests.post(
        f'https://{shop.name}/admin/api/2020-04/webhooks.json',
        json={
            'webhook': {
                'topic': 'app/uninstalled',
                'address': 'https://6756426a3ae1.ngrok.io/app/uninstalled/',
                'format': 'json',
            }
        },
        headers={'X-Shopify-Access-Token': shop.access_token}
    )

    # Return to the index page as an embedded page on shopify.
    return redirect(f'https://{shop.name}/admin/apps/{os.environ.get("SHOPIFY_API_KEY")}')


@csrf_exempt
def uninstalled(request):
    """Web hook route when a shop uninstalls the app."""

    # Clear out shop in database.
    shop = Shop.objects.get(
        name=request.META.get('HTTP_X_SHOPIFY_SHOP_DOMAIN'))
    shop.access_token = ''
    shop.nonce = ''
    shop.scope = ''
    shop.save()

    return HttpResponse('Bye!')
