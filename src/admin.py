import io
import logging
import sys

from telegram import ParseMode, Message, CallbackQuery
from telegram import ReplyKeyboardRemove
from telegram.error import TelegramError

from .enums import *
from .helpers import ConfigHelper, session_client, get_config_session, \
    get_user_session, get_user_id, set_config_session
from .models import Product, ProductCount, Courier, Location, User
from .keyboards import create_bot_config_keyboard, \
    create_bot_couriers_keyboard, create_bot_channels_keyboard, \
    create_bot_settings_keyboard

DEBUG = os.environ.get('DEBUG')
cat = gettext.GNUTranslations(open('he.mo', 'rb'))

_ = gettext.gettext
if not DEBUG:
    _ = cat.gettext


logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
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
    if not is_admin(bot, get_user_id(update)):
        logger.info('User %s, @%s rejected (not admin)',
                    update.message.from_user.id,
                    update.message.from_user.username)
        update.message.reply_text(text=_(
            'Sorry {}, you are not authorized to administrate this bot').format(
            update.message.from_user.first_name))
        return BOT_STATE_INIT


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
        product = Product.get(id=product_id)
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

    text = 'Enter courier telegram_id'
    update.message.reply_text(text=text)
    return ADMIN_TXT_COURIER_ID


def on_admin_txt_courier_id(bot, update, user_data):
    telegram_id = update.message.text
    user_data['add_courier']['telegram_id'] = telegram_id

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
    telegram_id = user_data['add_courier']['telegram_id']
    # check that location name is valid
    try:
        location = Location.get(id=location_id)
    except Location.DoesNotExist:
        update.message.reply_text(
            text='Invalid location id, please enter number')
        return ADMIN_TXT_COURIER_LOCATION
    try:
        Courier.get(username=username, telegram_id=telegram_id)
        update.message.reply_text(text='Courier with username @{} '
                                       'already added'.format(username))
    except Courier.DoesNotExist:
        Courier.create(username=username, location=location,
                       telegram_id=telegram_id)
        # clear new courier data
        del user_data['add_courier']
        bot.send_message(chat_id=update.message.chat_id,
                         text='Courier added',
                         reply_markup=create_bot_couriers_keyboard(),
                         parse_mode=ParseMode.MARKDOWN)
        return ADMIN_COURIERS

    bot.send_message(chat_id=update.message.chat_id,
                     text='Couriers',
                     reply_markup=create_bot_couriers_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_COURIERS


def on_admin_txt_delete_courier(bot, update):
    courier_id = update.message.text

    # check that courier id is valid
    try:
        courier = Courier.get(id=courier_id)
    except Courier.DoesNotExist:
        update.message.reply_text(
            text='Invalid courier id, please enter correct id')
        return ADMIN_TXT_DELETE_COURIER

    courier.delete_instance()
    bot.send_message(chat_id=update.message.chat_id,
                     text='Courier deleted',
                     reply_markup=create_bot_couriers_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_COURIERS


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


def set_welcome_message(bot, update):
    update.callback_query.message.reply_text(
        text='Enter new welcome text',
        parse_mode=ParseMode.MARKDOWN,
    )


def new_welcome_message(bot, update):
    new_text = update.message.text
    session = get_config_session()
    session['welcome_text'] = new_text
    session_client.json_set('config', session)
    return on_start_admin(bot, update)


def on_admin_select_channel_type(bot, update, user_data):
    channel_type = int(update.message.text)
    if channel_type in range(1, 5):
        user_data['add_channel'] = {}
        user_data['add_channel']['channel_type'] = channel_type - 1
        update.message.reply_text(
            text='Enter channel address',
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return ADMIN_CHANNELS_ADDRESS

    types = ['Reviews', 'Service', 'Customer', 'Vip customer', 'Courier']
    msg = ''
    for i, channel_type in enumerate(types, start=1):
        msg += '\n{} - {}'.format(i, channel_type)
    msg += '\nSelect channel type'
    update.message.reply_text(
        text=msg,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_CHANNELS_SELECT_TYPE


def on_admin_add_channel_address(bot, update, user_data):
    types = ['reviews_channel', 'service_channel', 'customers_channel',
             'vip_customers_channel', 'couriers_channel']
    channel_address = update.message.text
    channel_type = user_data['add_channel']['channel_type']
    config_session = get_config_session()
    config_session[types[channel_type]] = channel_address
    set_config_session(config_session)
    user_data['add_channel'] = {}
    bot.send_message(chat_id=update.message.chat_id,
                     text='Channels',
                     reply_markup=create_bot_channels_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_CHANNELS


def on_admin_remove_channel(bot, update, user_data):
    types = ['reviews_channel', 'service_channel', 'customers_channel',
             'vip_customers_channel', 'couriers_channel']
    channel_type = int(update.message.text)
    if channel_type in range(1, 5):
        config_session = get_config_session()
        config_session[types[channel_type - 1]] = None
        set_config_session(config_session)
        bot.send_message(chat_id=update.message.chat_id,
                         text='Channel was removed',
                         reply_markup=create_bot_channels_keyboard(),
                         parse_mode=ParseMode.MARKDOWN)
        return ADMIN_CHANNELS

    types = ['Reviews', 'Service', 'Customer', 'Vip customer', 'Courier']
    msg = ''
    for i, channel_type in enumerate(types, start=1):
        msg += '\n{} - {}'.format(i, channel_type)
    msg += '\nSelect channel type'
    update.message.reply_text(
        text=msg,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_CHANNELS_REMOVE


def on_admin_edit_working_hours(bot, update, user_data):
    new_working_hours = update.message.text
    config_session = get_config_session()
    config_session['working_hours'] = new_working_hours
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Working hours was changed',
                     reply_markup=create_bot_settings_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_BOT_SETTINGS


def on_admin_edit_contact_info(bot, update, user_data):
    contact_info = update.message.text
    config_session = get_config_session()
    config_session['contact_info'] = contact_info
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Contact info was changed',
                     reply_markup=create_bot_settings_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_BOT_SETTINGS


def on_admin_bot_on_off(bot, update, user_data):
    status = update.message.text
    if status in ['ON', 'OFF']:
        status = status == 'ON'
        config_session = get_config_session()
        config_session['bot_on_off'] = status
        set_config_session(config_session)
        bot.send_message(chat_id=update.message.chat_id,
                         text='Bot status was changed',
                         reply_markup=create_bot_settings_keyboard(),
                         parse_mode=ParseMode.MARKDOWN)
        return ADMIN_BOT_SETTINGS

    update.message.reply_text(
        text='Incorrect bot status, plz retype',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_BOT_ON_OFF
