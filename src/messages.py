import gettext
import os

DEBUG = os.environ.get('DEBUG')
cat = gettext.GNUTranslations(open('he.mo', 'rb'))

_ = gettext.gettext
if not DEBUG:
    _ = cat.gettext


def create_product_description(product_title, product_prices, product_count,
                               subtotal, delivery_fee):
    text = _('Product:\n{}').format(product_title)
    text += '\n\n'
    text += '〰️'
    text += '\n'
    text += _('<b>Delivery Fee: {}$</b>').format(delivery_fee)
    text += '\n'
    text += _('for orders blow 500$')
    text += '\n'
    text += '〰️'
    text += '\n'
    text += _('Price:')
    text += '\n'

    for q, price in product_prices:
        text += '\n'
        text += _('x {} = ${}').format(q, int(price))

    q = product_count
    if q > 0:
        text += '\n'
        text += _('Count: <b>{}</b>').format(q)
        text += '\n'
        text += _('Subtotal: <b>${}</b>').format(int(subtotal))
        text += '\n'

    return text


def create_confirmation_text(is_pickup, shipping_data, total, delivery_cost,
                             product_info):

    text = _('<b>Please confirm your order:</b>')
    text += '\n\n'
    text += '〰〰〰〰〰〰〰〰〰〰〰〰️'
    text += '\n'
    text += _('Items in cart:')
    text += '\n'

    for title, product_count, price in product_info:
        text += '\n'
        text += _('Product:\n{}').format(title)
        text += '\n'
        text += _('x {} = ${}').format(product_count, product_count * price, )
        text += '\n'
    text += '〰〰〰〰〰〰〰〰〰〰〰〰️'

    is_vip = False
    for key, value in shipping_data.items():
        if key == 'vip':
            is_vip = True

    if total < 500:
        if is_pickup:
            text += '\n\n'
            text += _('Total: <b>${}</b>').format(total)
        else:
            if is_vip:
                text += '\n\n'
                text += _('Total: <b>${}</b>').format(total)
            else:
                text += '\n\n'
                text += _('<b>Delivery Fee: {}$</b>').format(delivery_cost)
                text += '\n'
                text += _('Total: <b>${}</b>').format(total + delivery_cost)
    else:
        text += '\n\n'
        text += _('Total: <b>${}</b>').format(total)

    return text


def create_service_notice(is_pickup, order_id, product_info, shipping_data,
                          total, delivery_cost):

    text = _('<b>Order №{} notice:</b>'.format(order_id))
    text += '\n\n'
    text += '〰〰〰〰〰〰〰〰〰〰〰〰️'
    text += '\n'
    text += _('Items in cart:')
    text += '\n'

    for title, product_count, price in product_info:
        text += '\n'
        text += _('Product:\n{}').format(title)
        text += '\n'
        text += _('x {} = ${}').format(product_count, product_count * price, )
        text += '\n'

    is_vip = False
    for key, value in shipping_data.items():
        if key == 'vip':
            is_vip = True

    if total < 500:
        if is_pickup:
            text += '\n\n'
            text += _('Total: <b>${}</b>').format(total)
        else:
            if is_vip:
                text += '\n\n'
                text += _('Total: <b>${}</b>').format(total)
            else:
                text += '\n\n'
                text += _('<b>Delivery Fee: {}$</b>').format(delivery_cost)
                text += '\n'
                text += _('Total: <b>${}</b>').format(total + delivery_cost)
    else:
        text += '\n\n'
        text += _('Total: <b>${}</b>').format(total)
    text += '\n'
    text += '〰〰〰〰〰〰〰〰〰〰〰〰️'

    text += '\n\n'
    text += _('Shipping details:')
    text += '\n\n'

    for key, value in shipping_data.items():
        if key == 'vip':
            text += _('Vip Costumer')
            text += '\n'
        if key == 'photo_question':
            text += _('Photo question: ')
            text += value
            text += '\n'
        if key == 'method':
            text += _('Pickup/Delivery: ')
            text += value
            text += '\n'
        if key == 'pickup_location':
            text += _('Pickup location: ')
            text += value
            text += '\n'
        if key == 'address':
            text += _('Address: ')
            text += value
            text += '\n'
        if key == 'time':
            text += _('When: ')
            text += value
            text += '\n'
        if key == 'time_text':
            text += _('Time: ')
            text += value
            text += '\n'
        if key == 'phone_number':
            text += _('Phone number: ')
            text += value
            text += '\n'

    return text
