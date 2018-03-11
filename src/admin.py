import io
import logging
import sys

from telegram import ParseMode, Message, CallbackQuery
from telegram import ReplyKeyboardRemove
from telegram.error import TelegramError
from telegram.ext import ConversationHandler

from .enums import *
from .helpers import ConfigHelper, session_client, get_config_session, \
    get_user_session, get_user_id, set_config_session
from .models import Product, ProductCount, Courier, Location, CourierLocation
from .keyboards import create_bot_config_keyboard, create_back_button, \
    create_bot_couriers_keyboard, create_bot_channels_keyboard, \
    create_bot_settings_keyboard, create_bot_order_options_keyboard, \
    create_ban_list_keyboard

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


def on_admin_order_options(bot, update):
    query = update.callback_query
    data = query.data
    if data == 'bot_order_options_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text='Bot settings',
                              reply_markup=create_bot_settings_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_SETTINGS
    elif data == 'bot_order_options_product':
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text='Enter new product title',
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_back_button(),
        )
        return ADMIN_TXT_PRODUCT_TITLE
    elif data == 'bot_order_options_delete_product':
        products = Product.select()
        if products.count() == 0:
            query = update.callback_query
            bot.edit_message_text(chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  text='No products to delete',
                                  reply_markup=create_bot_order_options_keyboard(),
                                  parse_mode=ParseMode.MARKDOWN)
            return ADMIN_ORDER_OPTIONS
        else:
            text = 'Choose product ID to delete:'
            for product in products:
                text += '\n'
                text += '{}. {}'.format(product.id, product.title)
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_back_button(),
        )
        return ADMIN_TXT_DELETE_PRODUCT
    elif data == 'bot_order_options_discount':
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=('Enter discount like:\n'
                  '50 > 500: all deals above 500$ will be -100$\n'
                  '10% > 500: all deals above 500% will be -10%\n'
                  'Current discount: {}'.format(config.get_discount())),
            reply_markup=create_back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        query.answer()
        return ADMIN_ADD_DISCOUNT
    elif data == 'bot_order_options_delivery_fee':
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=('Enter delivery fee like:\n'
                  '50 > 500: all deals above 500$ no fee\n'
                  'if 0: all the deals have no fee\n'
                  'Current fee: {}'.format(config.get_delivery_fee())),
            reply_markup=create_back_button(),
            parse_mode=ParseMode.MARKDOWN,
        )
        query.answer()
        return ADMIN_ADD_DELIVERY_FEE
    elif data == 'bot_order_options_identify':
        first = config.get_identification_required()
        second = config.get_identification_stage2_required()
        question = config.get_identification_stage2_question()
        first = 'Enabled' if first else 'Disabled'
        second = 'Enabled' if second else 'Disabled'
        msg = 'First stage: {}\n' \
              'Second stage: {}\n' \
              'Identification question:{}\n' \
              'Enter like this: 0/1 0/1 text (first, second, question)' \
              ''.format(first, second, question)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_EDIT_IDENTIFICATION
    elif data == 'bot_order_options_restricted':
        only_for_customers = 'Enabled' if config.get_only_for_customers() \
            else 'Disabled'
        only_for_vip_customers = 'Enabled' if config.get_vip_customers() \
            else 'Disabled'
        msg = 'Only for customers option: {}\n' \
              'Vip customers option: {}\n' \
              'Type new rules: 0/1 0/1 (customers, vip customers)'.format(
                only_for_customers, only_for_vip_customers)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_EDIT_RESTRICTION
    elif data == 'bot_order_options_welcome':
        msg = 'Type new welcome message.\n' \
              'Current message: {}'.format(config.get_welcome_text())
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_EDIT_WELCOME_MESSAGE
    elif data == 'bot_order_options_details':
        msg = 'Type new order details message.\n' \
              'Current message: {}'.format(config.get_order_text())
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_EDIT_ORDER_DETAILS
    elif data == 'bot_order_options_final':
        msg = 'Type new final message.\n' \
              'Current message: {}'.format(config.get_order_complete_text())
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_EDIT_FINAL_MESSAGE

    return ConversationHandler.END


def on_admin_txt_product_title(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        query = update.callback_query
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text='Order options',
                              reply_markup=create_bot_order_options_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_ORDER_OPTIONS

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

    bot.send_message(chat_id=update.message.chat_id,
                     text='Product created',
                     reply_markup=create_bot_settings_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


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


def on_admin_txt_delete_product(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        query = update.callback_query
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text='Order options',
                              reply_markup=create_bot_order_options_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_ORDER_OPTIONS
    product_id = update.message.text
    try:
        # get title to check if product is valid
        product = Product.get(id=product_id)
        product_title = product.title
        product.delete_instance()
        update.message.reply_text(
            text='Product {} - {} was deleted'.format(product_id, product_title))
        logger.info('Product %s - %s was deleted', product_id, product_title)
        update.message.reply_text(
            text='Order options',
            reply_markup=create_bot_order_options_keyboard(),
            parse_mode=ParseMode.MARKDOWN,
        )
        return ADMIN_ORDER_OPTIONS
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

    text = 'Enter location ID for this courier (choose number or list of ' \
           'numbers from list below, example: 1 or 1, 2):'

    for location in Location:
        text += '\n'
        text += '{}. {}'.format(location.id, location.title)

    update.message.reply_text(text=text)
    return ADMIN_TXT_COURIER_LOCATION


def on_admin_txt_courier_location(bot, update, user_data):
    location_ids = update.message.text.split(', ')
    user_data['add_courier']['location_ids'] = location_ids
    username = user_data['add_courier']['name']
    telegram_id = user_data['add_courier']['telegram_id']
    # check that location name is valid
    locations = Location.filter(id__in=location_ids)
    try:
        Courier.get(username=username, telegram_id=telegram_id)
        update.message.reply_text(text='Courier with username @{} '
                                       'already added'.format(username))
    except Courier.DoesNotExist:
        courier = Courier.create(username=username, telegram_id=telegram_id)
        for location in locations:
            CourierLocation.create(courier=courier, location=location)
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
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_settings_keyboard,
            'Bot settings')
        return ADMIN_BOT_SETTINGS

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
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_settings_keyboard,
            'Bot settings')
        return ADMIN_BOT_SETTINGS

    contact_info = update.message.text
    config_session = get_config_session()
    config_session['contact_info'] = contact_info
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Contact info was changed',
                     reply_markup=create_bot_settings_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_BOT_SETTINGS


def on_admin_add_discount(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    discount = update.message.text
    config_session = get_config_session()
    config_session['discount'] = discount
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Discount was changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_add_delivery(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    delivery_fee = update.message.text
    config_session = get_config_session()
    config_session['delivery_fee'] = delivery_fee
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Delivery fee was changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_bot_on_off(bot, update, user_data):
    query = update.callback_query
    if query.data == 'back':
        option_back_function(
            bot, update, create_bot_settings_keyboard,
            'Bot settings')
        return ADMIN_BOT_SETTINGS

    status = query.data == 'on'
    config_session = get_config_session()
    config_session['bot_on_off'] = status
    set_config_session(config_session)
    bot.send_message(chat_id=query.message.chat_id,
                     message_id=query.message.chat_id,
                     text='Bot status was changed',
                     reply_markup=create_bot_settings_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_BOT_SETTINGS


def option_back_function(bot, update, return_fnc, return_title):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=return_title,
                          reply_markup=return_fnc(),
                          parse_mode=ParseMode.MARKDOWN)


def on_admin_edit_welcome_message(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    welcome_message = update.message.text
    config_session = get_config_session()
    config_session['welcome_text'] = welcome_message
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Welcome message fee was changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_edit_order_message(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    order_message = update.message.text
    config_session = get_config_session()
    config_session['order_text'] = order_message
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Order message was changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_edit_final_message(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    final_message = update.message.text
    config_session = get_config_session()
    config_session['order_complete_text'] = final_message
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Final message was changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_edit_identification(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    message = update.message.text.split(maxsplit=2)
    first, second, question = message

    config_session = get_config_session()
    config_session['identification_required'] = first
    config_session['identification_stage2_required'] = second
    config_session['identification_stage2_question'] = question
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Identification was changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_edit_restriction(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_bot_order_options_keyboard,
            'Order options')
        return ADMIN_ORDER_OPTIONS

    message = update.message.text.split(maxsplit=1)
    first, second = message

    config_session = get_config_session()
    config_session['only_for_customers'] = first
    config_session['vip_customers'] = second
    set_config_session(config_session)
    bot.send_message(chat_id=update.message.chat_id,
                     text='Restriction options ware changed',
                     reply_markup=create_bot_order_options_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_ORDER_OPTIONS


def on_admin_add_ban_list(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_ban_list_keyboard,
            'Ban list')
        return ADMIN_BAN_LIST

    username = update.message.text.replace('@', '').replace(' ', '')
    banned = config.get_banned_users()
    if username not in banned:
        banned.append(username)
    config_session = get_config_session()
    config_session['banned'] = banned
    set_config_session(config_session)

    bot.send_message(chat_id=update.message.chat_id,
                     text='@{} was banned'.format(username),
                     reply_markup=create_ban_list_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_BAN_LIST


def on_admin_remove_ban_list(bot, update, user_data):
    if update.callback_query and update.callback_query.data == 'back':
        option_back_function(
            bot, update, create_ban_list_keyboard,
            'Ban list')
        return ADMIN_BAN_LIST

    username = update.message.text.replace('@', '').replace(' ', '')
    banned = config.get_banned_users()
    banned = [ban for ban in banned if ban != username]
    config_session = get_config_session()
    config_session['banned'] = banned
    set_config_session(config_session)

    bot.send_message(chat_id=update.message.chat_id,
                     text='@{} was unbanned'.format(username),
                     reply_markup=create_ban_list_keyboard(),
                     parse_mode=ParseMode.MARKDOWN)
    return ADMIN_BAN_LIST
