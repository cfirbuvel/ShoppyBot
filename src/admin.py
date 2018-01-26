import io
import logging
import sys
import os

from telegram import ParseMode
from telegram import ReplyKeyboardRemove
from telegram.error import TelegramError

from .enums import *
from .helpers import ConfigHelper
from .models import Product, ProductCount, Courier, Location


DEBUG = os.environ.get('DEBUG')
cat = gettext.GNUTranslations(open('he.mo', 'rb'))

_ = gettext.gettext
if not DEBUG:
    _ = cat.gettext


logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

DEBUG = True

if DEBUG:
    config = ConfigHelper(cfgfilename='test_conf.conf')
else:
    config = ConfigHelper()


def is_admin(bot, user_id):
    chat_id = config.get_service_channel()

    try:
        member = bot.getChatMember(chat_id, user_id)
        if member.status == 'left':
            return False
        else:
            return True
    except TelegramError as e:
        logger.error("Failed to check admin id: %s", e)
        return False


def on_start_admin(bot, update):
    if not is_admin(bot, update.message.from_user.id):
        logger.info('User %s, @%s rejected (not admin)',
                    update.message.from_user.id,
                    update.message.from_user.username)
        update.message.reply_text(text=_(
            'Sorry {}, you are not authorized to administrate this bot').format(
            update.message.from_user.first_name))
        return BOT_STATE_INIT

    msg = "\n".join([
        'Entering admin mode',
        'Use following commands:',
        '/addproduct - add new product',
        '/delproduct - delete product',
        '/addcourier - add courier',
        '/delcourier - delete courier',
        '/on - enable shopping',
        '/off - disable shopping',
    ])
    update.message.reply_text(
        text=msg, reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_INIT


def on_admin_cmd_add_product(bot, update):
    update.message.reply_text(
        text='Enter new product title',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_TXT_PRODUCT_TITLE


def on_admin_txt_product_title(bot, update, user_data):
    title = update.message.text
    # initialize new product data
    user_data['add_product'] = {}
    user_data['add_product']['title'] = title
    update.message.reply_text(
        text='Enter new product prices one per line in the format *COUNT '
             'PRICE*, e.g. *1 10.0*',
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_TXT_PRODUCT_PRICES


def on_admin_txt_product_prices(bot, update, user_data):
    prices = update.message.text

    # check that prices are valid
    prices_list = []
    for line in prices.split('\n'):
        try:
            count_str, price_str = line.split()
            count = int(count_str)
            price = float(price_str)
            prices_list.append((count, price))
        except ValueError as e:
            update.message.reply_text(
                text='Could not read prices, please try again')
            return ADMIN_TXT_PRODUCT_PRICES

    user_data['add_product']['prices'] = prices_list
    update.message.reply_text(
        text='Send the new product photo',
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_TXT_PRODUCT_PHOTO


def on_admin_txt_product_photo(bot, update, user_data):
    photo_file = bot.get_file(update.message.photo[-1].file_id)
    stream = io.BytesIO()
    photo_file.download(out=stream)

    title = user_data['add_product']['title']
    prices = user_data['add_product']['prices']
    image_data = stream.getvalue()

    product = Product.create(title=title, image=image_data)
    for count, price in prices:
        ProductCount.create(product=product, price=price, count=count)

    # clear new product data
    del user_data['add_product']

    update.message.reply_text(
        text='Product created, type /cancel to leave admin mode')
    logger.info("Product created: %s", title)
    return ADMIN_INIT


def on_admin_cmd_delete_product(bot, update):
    products = Product.select()
    if products.count() == 0:
        update.message.reply_text(text='No products to delete')
        return ADMIN_INIT
    else:
        text = 'Choose product ID to delete:'
        for product in products:
            text += '\n'
            text += '{}. {}'.format(product.id, product.title)
        update.message.reply_text(text=text)
        return ADMIN_TXT_DELETE_PRODUCT


def on_admin_cmd_bot_on(bot, update):
    global BOT_ON
    BOT_ON = True
    update.message.reply_text(text='Bot switched on')
    return ADMIN_INIT


def on_admin_cmd_bot_off(bot, update):
    global BOT_ON
    BOT_ON = False
    update.message.reply_text(text='Bot switched off')
    return ADMIN_INIT


def on_admin_cmd_add_courier(bot, update):
    update.message.reply_text(text='Enter new courier nickname')
    return ADMIN_TXT_COURIER_NAME


def on_admin_cmd_delete_courier(bot, update):
    text = 'Choose courier ID to delete:'

    for courier in Courier.select():
        text += '\n'
        text += '{}. {}'.format(courier.id, courier.username)

    update.message.reply_text(text=text)
    return ADMIN_TXT_DELETE_COURIER


def on_admin_txt_delete_product(bot, update):
    product_id = update.message.text
    try:
        # get title to check if product is valid
        product = Product.get(id=product_id).title
        product_title = product.title
        product.delete_instance()
        update.message.reply_text(
            text='Product {} - {} is deleted'.format(product_id, product_title))
        logger.info('Product %s - %s is deleted', product_id, product_title)
        return ADMIN_INIT
    except Product.DoesNotExist:
        update.message.reply_text(
            text='Invalid product id, please enter number')
        return ADMIN_TXT_DELETE_PRODUCT


def on_admin_txt_courier_name(bot, update, user_data):
    name = update.message.text
    # initialize new courier data
    user_data['add_courier'] = {}
    user_data['add_courier']['name'] = name

    text = 'Enter location ID for this courier (choose number from list below):'

    for location in Location:
        text += '\n'
        text += '{}. {}'.format(location.id, location.title)

    update.message.reply_text(text=text)
    return ADMIN_TXT_COURIER_LOCATION


def on_admin_txt_courier_location(bot, update, user_data):
    location_id = update.message.text
    user_data['add_courier']['location_id'] = location_id
    username = user_data['add_courier']['name']
    # check that location name is valid
    try:
        location = Location.get(id=location_id)
    except Location.DoesNotExist:
        update.message.reply_text(
            text='Invalid location id, please enter number')
        return ADMIN_TXT_COURIER_LOCATION

    Courier.create(username=username, location=location)
    # clear new courier data
    del user_data['add_courier']

    update.message.reply_text(text='Courier added')
    return ADMIN_INIT


def on_admin_txt_delete_courier(bot, update):
    courier_id = update.message.text

    # check that courier id is valid
    try:
        courier = Courier.get(id=courier_id)
    except Courier.DoesNotExist:
        update.message.reply_text(
            text='Invalid courier id, please enter number')
        return ADMIN_TXT_DELETE_COURIER

    courier.delete_instance()
    update.message.reply_text(text='Courier deleted')
    return ADMIN_INIT


# additional cancel handler for admin commands
def on_admin_cancel(bot, update):
    update.message.reply_text(
        text='Admin command cancelled, to enter admin mode again type /admin',
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN,
    )
    return BOT_STATE_INIT


def on_admin_fallback(bot, update):
    update.message.reply_text(
        text='Unknown input, type /cancel to exit admin mode',
        reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_INIT
