import configparser
import redis
import json

from .models import ProductCount, Product, Order, OrderItem, Courier


class JsonRedis(redis.StrictRedis):

    def json_get(self, name):
        value = self.get(name)
        if value:
            value = json.loads(value.decode("utf-8"))
        return value

    def json_set(self, name, value):
        value = json.dumps(value)
        return self.set(name, value)


class ConfigHelper:
    def __init__(self, cfgfilename='shoppybot.conf'):
        self.config = configparser.ConfigParser(
            defaults={'api_token': None, 'reviews_channel': None,
                      'service_channel': None, 'customers_channel': None,
                      'vip_customers_channel': None, 'couriers_channel': None,
                      'welcome_text': 'Welcome text not configured yet',
                      'order_text': 'Order text not configured yet',
                      'order_complete_text': 'Order text not configured yet',
                      'working_hours': 'Working hours not configured yet',
                      'contact_info': 'Contact info not configured yet',
                      'phone_number_required': True,
                      'identification_required': True,
                      'identification_stage2_required': False,
                      'identification_stage2_question': None,
                      'only_for_customers': False, 'delivery_fee': 0, })
        self.config.read(cfgfilename, encoding='utf-8')
        self.section = 'Settings'

    def get_api_token(self):
        value = self.config.get(self.section, 'api_token')
        return value.strip()

    def get_reviews_channel(self):
        value = self.config.get(self.section, 'reviews_channel')
        return value.strip()

    def get_service_channel(self):
        value = self.config.get(self.section, 'service_channel')
        return value.strip()

    def get_customers_channel(self):
        value = self.config.get(self.section, 'customers_channel')
        return value.strip()

    def get_vip_customers_channel(self):
        value = self.config.get(self.section, 'vip_customers_channel')
        return value.strip()

    def get_couriers_channel(self):
        value = self.config.get(self.section, 'couriers_channel')
        return value.strip()

    def get_welcome_text(self):
        value = self.config.get(self.section, 'welcome_text')
        return value.strip()

    def get_order_text(self):
        value = self.config.get(self.section, 'order_text')
        return value.strip()

    def get_order_complete_text(self):
        value = self.config.get(self.section, 'order_complete_text')
        return value.strip()

    def get_working_hours(self):
        value = self.config.get(self.section, 'working_hours')
        return value.strip()

    def get_contact_info(self):
        value = self.config.get(self.section, 'contact_info')
        return value.strip()

    def get_phone_number_required(self):
        value = self.config.getboolean(self.section, 'phone_number_required')
        return value

    def get_identification_required(self):
        value = self.config.getboolean(self.section, 'identification_required')
        return value

    def get_identification_stage2_required(self):
        value = self.config.getboolean(self.section,
                                       'identification_stage2_required')
        return value

    def get_identification_stage2_question(self):
        value = self.config.get(self.section, 'identification_stage2_question')
        return value

    def get_only_for_customers(self):
        value = self.config.getboolean(self.section, 'only_for_customers')
        return value

    def get_vip_customers(self):
        value = self.config.getboolean(self.section, 'vip_customers')
        return value

    def get_delivery_fee(self):
        value = self.config.get(self.section, 'delivery_fee')
        return int(value.strip())


class CartHelper:
    def __init__(self):
        pass

    def check_cart(self, user_data):
        # check that cart is still here in case we've restarted
        if 'cart' not in user_data:
            user_data['cart'] = {}
        return user_data['cart']

    def add(self, user_data, product_id):
        cart = self.check_cart(user_data)
        product_id = str(product_id)
        prices = ProductCount.select().where(
            ProductCount.product == product_id).order_by(
            ProductCount.count.asc())
        counts = [x.count for x in prices]
        min_count = counts[0]

        if product_id not in cart:
            # add minimum product count (usually 1)
            cart[product_id] = min_count
        else:
            # add more
            current_count = cart[product_id]
            current_count_index = counts.index(current_count)
            # iterate through possible product counts for next price
            next_count_index = (current_count_index + 1) % len(counts)
            cart[product_id] = counts[next_count_index]
        user_data['cart'] = cart

        return user_data

    def remove(self, user_data, product_id):
        cart = self.check_cart(user_data)
        product_id = str(product_id)

        prices = ProductCount.select().where(
            ProductCount.product == product_id).order_by(
            ProductCount.count.asc())
        counts = [x.count for x in prices]

        if product_id in cart:
            current_count = cart[product_id]
            current_count_index = counts.index(current_count)

            if current_count_index == 0:
                del cart[product_id]
            else:
                next_count_index = current_count_index - 1
                cart[product_id] = counts[next_count_index]
        user_data['cart'] = cart

        return user_data

    def get_products_info(self, user_data, for_order=False):
        product_ids = self.get_product_ids(user_data)
        product_info = []
        for product_id in product_ids:
            product_info.append(
                self.get_product_info(user_data, product_id, for_order))

        return product_info

    def get_product_info(self, user_data, product_id, for_order=False):
        product_title = Product.get(id=product_id).title
        product_count = self.get_product_count(user_data, product_id)
        product_price = ProductCount.get(
            product_id=product_id, count=product_count).price
        if for_order:
            result = product_id, product_count, product_price
        else:
            result = product_title, product_count, product_price
        return result

    def product_full_info(self, user_data, product_id):
        product_title = Product.get(id=product_id).title
        rows = ProductCount.select(
            ProductCount.count, ProductCount.price).where(
            ProductCount.product == product_id).tuples()
        return product_title, rows

    def get_product_ids(self, user_data):
        cart = self.check_cart(user_data)

        return cart.keys()

    def get_product_count(self, user_data, product_id):
        cart = self.check_cart(user_data)
        product_id = str(product_id)

        if product_id not in cart:
            return 0
        else:
            return cart[product_id]

    def is_full(self, user_data):
        cart = self.check_cart(user_data)

        return len(cart) > 0

    def get_product_subtotal(self, user_data, product_id):
        count = self.get_product_count(user_data, product_id)

        rows = ProductCount.filter(product_id=product_id)
        min_price = 0
        for row in rows:
            price, product_count = row.price, row.count
            if count >= product_count:
                min_price = price

        return min_price

    def get_cart_total(self, user_data):
        cart = self.check_cart(user_data)

        total = 0
        for product_id in cart:
            subtotal = self.get_product_subtotal(user_data, product_id)
            total += subtotal
        return total

    def fill_order(self, user_data, order):
        products = self.get_products_info(user_data, for_order=True)
        for p_id, p_count, p_price in products:
            OrderItem.create(order=order, product_id=p_id, count=p_count,
                             total_price=p_price)


session_client = JsonRedis(host='localhost', port=6379, db=0)


def get_user_session(user_id):
    user_session = session_client.json_get(user_id)
    updated = False

    if not user_session:
        session_client.json_set(user_id, {})
        user_session = session_client.json_get(user_id)

    if not user_session.get('cart'):
        user_session["cart"] = {}
        updated = True

    if not user_session.get('shipping'):
        user_session["shipping"] = {}
        updated = True

    if updated:
        session_client.json_set(user_id, user_session)

    return user_session


def get_courier_nickname(location):
    courier_location = Courier.location

    return courier_location

def get_username(update):
    if update.callback_query is not None:
        username = update.callback_query.from_user.username
    else:
        username = update.message.from_user.username

    return username


def get_user_id(update):
    if update.callback_query is not None:
        user_id = update.callback_query.from_user.id
    else:
        user_id = update.message.from_user.id

    return user_id
