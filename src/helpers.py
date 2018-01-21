# helper classes for shoppybot
import sqlite3
import configparser
import redis
import json


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
        return float(value.strip())


class DBHelper:
    def __init__(self, dbname='shoppybot_db.sqlite'):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname, check_same_thread=False)

    def get_products(self):
        sql = 'SELECT id, title FROM products'
        return [x for x in self.conn.execute(sql)]

    def get_product_title(self, id):
        sql = 'SELECT title FROM products WHERE id = {}'.format(id)
        value = self.conn.execute(sql).fetchone()
        if value:
            return value[0]
        else:
            raise RuntimeError('Unknown product id')

    def get_product_images(self, id):
        sql = 'SELECT image_data FROM product_images WHERE id = {}'.format(id)
        return [x[0] for x in self.conn.execute(sql)]

    def get_product_image(self, id):
        sql = 'SELECT image_data FROM product_images WHERE id = {}'.format(id)
        value = self.conn.execute(sql).fetchone()
        if value:
            return value[0]
        else:
            raise RuntimeError('Unknown product id')

    def get_product_prices(self, id):
        sql = 'SELECT count,price FROM product_prices WHERE id = {} ORDER BY ' \
              'count'.format(id)
        return [x for x in self.conn.execute(sql)]

    def get_pickup_locations(self):
        sql = 'SELECT id, name FROM locations'
        return [x for x in self.conn.execute(sql)]

    def get_pickup_location_name(self, location_id):
        sql = 'SELECT name FROM locations WHERE id = {}'.format(location_id)
        value = self.conn.execute(sql).fetchone()
        if value:
            return value[0]
        else:
            raise RuntimeError('Unknown location id')

    def get_couriers(self):
        sql = 'SELECT id, nickname FROM couriers'
        return [x for x in self.conn.execute(sql)]

    def get_courier_nickname(self, courier_id):
        sql = 'SELECT nickname FROM couriers WHERE id = {}'.format(courier_id)
        value = self.conn.execute(sql).fetchone()
        if value:
            return value[0]
        else:
            raise RuntimeError('Unknown courier id')

    def get_couriers_for_location(self, location_id):
        sql = 'SELECT nickname FROM couriers WHERE location = {}'.format(
            location_id)
        return [x for x in self.conn.execute(sql)]

    def get_couriers_for_location_name(self, location_name):
        location_id = None
        value = self.conn.execute('SELECT id FROM locations WHERE name=?',
                                  (location_name,)).fetchone()
        if value:
            location_id = value[0]
        else:
            raise RuntimeError('Unknown location name')

        sql = 'SELECT nickname FROM couriers WHERE location = {}'.format(
            location_id)
        return [x[0] for x in self.conn.execute(sql)]

    def delete_courier(self, courier_id):
        self.conn.execute('DELETE FROM couriers WHERE ID=?', courier_id)
        self.conn.commit()

    def add_new_product(self, title, prices, image_data):
        sql = 'SELECT MAX(id) FROM products'

        max_id = self.conn.execute(sql).fetchone()[0]
        if max_id:
            max_id = max_id
        else:
            max_id = 0

        new_product_id = max_id + 1
        self.conn.execute('INSERT INTO products(id, title) VALUES (?, ?)',
                          (new_product_id, title))

        for count, price in prices:
            self.conn.execute(
                'INSERT INTO product_prices(id, count, price) VALUES (?, ?, ?)',
                (new_product_id, count, price))

        self.conn.execute(
            'INSERT INTO product_images(id, image_data) VALUES (?, ?)',
            (new_product_id, image_data))
        self.conn.commit()

    def delete_product(self, product_id):
        self.conn.execute('DELETE FROM products WHERE ID=?', product_id)
        self.conn.execute('DELETE FROM product_prices WHERE ID=?', product_id)
        self.conn.execute('DELETE FROM product_images WHERE ID=?', product_id)
        self.conn.commit()

    def add_new_courier(self, name, location_id):
        self.conn.execute(
            'INSERT INTO couriers(nickname, location) VALUES (?, ?)',
            (name, location_id))
        self.conn.commit()


# This class currently provides methods that modify user_data directly
# It can be improved to have its own expiring cache for per-user carts
class CartHelper:
    def __init__(self):
        self.db = DBHelper()

    def check_cart(self, user_data):
        # check that cart is still here in case we've restarted
        if 'cart' not in user_data:
            user_data['cart'] = {}
        return user_data['cart']

    def add(self, user_data, product_id):
        cart = self.check_cart(user_data)
        product_id = str(product_id)
        prices = self.db.get_product_prices(product_id)
        counts = [x[0] for x in prices]
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

        return user_data

    def remove(self, user_data, product_id):
        cart = self.check_cart(user_data)
        product_id = str(product_id)

        prices = self.db.get_product_prices(product_id)
        counts = [x[0] for x in prices]

        if product_id not in cart:
            pass
        else:
            current_count = cart[product_id]
            current_count_index = counts.index(current_count)

            if current_count_index == 0:
                del cart[product_id]
            else:
                next_count_index = current_count_index - 1
                cart[product_id] = counts[next_count_index]

        return user_data

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
        cart = self.check_cart(user_data)
        product_id = str(product_id)

        count = 0
        if product_id in cart:
            count = cart[product_id]

        prices = self.db.get_product_prices(product_id)
        min_price = 0
        for q, price in prices:
            if count >= q:
                min_price = price

        return min_price

    def get_cart_total(self, user_data):
        cart = self.check_cart(user_data)

        total = 0
        for product_id in cart:
            subtotal = self.get_product_subtotal(user_data, product_id)
            total += subtotal
        return total


session_client = JsonRedis(host='localhost', port=6379, db=0)


def get_user_session(user_id):
    user_session = session_client.json_get(user_id)
    updated = False

    if not user_session:
        session_client.json_set(user_id, user_id)
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
