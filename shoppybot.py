#! /usr/bin/env python3
import random
import os

from telegram.ext import CallbackQueryHandler, CommandHandler,\
    ConversationHandler, Filters, MessageHandler, Updater

from src.admin import *
from src.enums import *
from src.messages import create_confirmation_text, create_product_description, \
    create_service_notice
from src.helpers import CartHelper, session_client, get_user_session, \
    get_user_id, get_username
from src.keyboards import create_drop_responsibility_keyboard, \
    create_service_notice_keyboard, create_main_keyboard, \
    create_pickup_location_keyboard, create_product_keyboard, \
    create_shipping_keyboard, create_cancel_keyboard, create_time_keyboard, \
    create_confirmation_keyboard, create_courier_confirmation_keyboard
from src.models import create_tables, User, Courier, Order, OrderItem, \
    Product, ProductCount

logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

cat = gettext.GNUTranslations(open('he.mo', 'rb'))
DEBUG = os.environ.get('DEBUG')

_ = gettext.gettext
if not DEBUG:
    _ = cat.gettext

#
# global variable for on/off
#
BOT_ON = True

if DEBUG:
    config = ConfigHelper(cfgfilename='test_conf.conf')
else:
    config = ConfigHelper()

cart = CartHelper()


#
# bot helper functions
# 

def is_vip_customer(bot, user_id):
    if not config.get_vip_customers():
        return True

    chat_id = config.get_vip_customers_channel()

    try:
        member = bot.getChatMember(chat_id, user_id)
        if member.status == 'left':
            return False
        else:
            return True
    except TelegramError as e:
        logger.error("Failed to check vip customer id: %s", e)
        return False


def is_customer(bot, user_id):
    if not config.get_only_for_customers():
        return True

    chat_id = config.get_customers_channel()

    try:
        member = bot.getChatMember(chat_id, user_id)
        if member.status == 'left':
            return False
        else:
            return True
    except TelegramError as e:
        logger.error("Failed to check customer id: %s", e)
        return False


# we assume people in service channel can administrate the bot


def create_photo_question():
    q1 = _('👍')
    q2 = _('🤘')
    q3 = _('✌️')
    q4 = _('👌')
    return random.choice([q1, q2, q3, q4])


def resend_responsibility_keyboard(bot, update, user_data):
    query = update.callback_query
    data = query.data
    label, order_id = data.split('|')
    user_id = get_user_id(update)
    session = get_user_session(user_id)
    try:
        order = Order.get(id=order_id)
    except Order.DoesNotExist:
        logger.info('Order № {} not found!'.format(order_id))
    else:
        order.courier = None
        order.save()
    bot.delete_message(config.get_couriers_channel(),
                       message_id=query.message.message_id)
    bot.send_message(config.get_couriers_channel(),
                     text=query.message.text,
                     parse_mode=ParseMode.HTML,
                     reply_markup=create_service_notice_keyboard(
                         update, user_id, order_id),
                     )


def make_confirm(bot, update, user_data):
    query = update.callback_query
    data = query.data
    label, order_id, courier_name = data.split('|')
    bot.delete_message(config.get_service_channel(),
                       message_id=query.message.message_id)
    try:
        order = Order.get(id=order_id)
    except Order.DoesNotExist:
        logger.info('Order № {} not found!'.format(order_id))
    else:
        order.confirmed = True
        order.save()

        user_id = order.user.telegram_id
        bot.send_message(
            user_id,
            text=_('Courier @{} assigned to your order').format(courier_name),
            parse_mode=ParseMode.HTML,
        )


def make_unconfirm(bot, update, user_data):
    query = update.callback_query
    data = query.data
    label, order_id, courier_name = data.split('|')
    bot.delete_message(config.get_service_channel(),
                       message_id=query.message.message_id)
    try:
        order = Order.get(id=order_id)
    except Order.DoesNotExist:
        logger.info('Order № {} not found!'.format(order_id))
    else:
        user_id = order.user.telegram_id
        bot.send_message(config.get_couriers_channel(),
                         text='The admin did not confirm. Please retake '
                              'responsibility for order №{}'.format(order_id),
                         reply_markup=create_service_notice_keyboard(
                             update, user_id, order_id), 
                         )

#
# bot handlers
# 


def on_start(bot, update, user_data):
    user_id = get_user_id(update)
    username = get_username(update)
    user_data = get_user_session(user_id)
    try:
        user = User.get(telegram_id=user_id)
    except User.DoesNotExist:
        user = User(telegram_id=user_id, username=username)
        user.save()
    if BOT_ON:
        if is_customer(bot, user_id) or is_vip_customer(bot, user_id):
            logger.info('Starting session for user %s, language: %s',
                        update.message.from_user.id,
                        update.message.from_user.language_code)
            update.message.reply_text(
                text=config.get_welcome_text().format(
                    update.message.from_user.first_name),
                reply_markup=create_main_keyboard(config.get_reviews_channel()),
            )
            return BOT_STATE_INIT
        else:
            logger.info('User %s rejected (not a customer)',
                        update.message.from_user.id)
            update.message.reply_text(
                text=_('Sorry {}\nYou are not authorized to use '
                       'this bot').format(update.message.from_user.first_name),
                reply_markup=None,
                parse_mode=ParseMode.HTML,
            )
            return ConversationHandler.END
    else:
        update.message.reply_text(
            text=_('Sorry {}, the bot is currently switched off').format(
                update.message.from_user.first_name),
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END


def on_menu(bot, update, user_data=None):
    query = update.callback_query
    data = query.data
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if BOT_ON:
        if is_customer(bot, user_id) or is_vip_customer(bot, user_id):
            if data == 'menu_products':
                # the menu disappears
                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=_('Our products:'),
                                      parse_mode=ParseMode.MARKDOWN, )

                # send_products to current chat
                for product in Product.select():
                    product_count = cart.get_product_count(
                        user_data, product.id)
                    subtotal = cart.get_product_subtotal(
                        user_data, product.id)
                    delivery_fee = config.get_delivery_fee()
                    product_title, prices = cart.product_full_info(
                        user_data, product.id)
                    image_data = product.image
                    image_stream = io.BytesIO(image_data)
                    bot.send_photo(query.message.chat_id,
                                   photo=image_stream)
                    bot.send_message(query.message.chat_id,
                                     text=create_product_description(
                                         product_title, prices,
                                         product_count, subtotal,
                                         delivery_fee),
                                     reply_markup=create_product_keyboard(
                                         product.id, user_data, cart),
                                     parse_mode=ParseMode.HTML,
                                     timeout=20, )

                # send menu again as a new message
                bot.send_message(query.message.chat_id,
                                 text=config.get_order_text().format(
                                     _('#Our_Species:')),
                                 reply_markup=create_main_keyboard(
                                     config.get_reviews_channel()),
                                 parse_mode=ParseMode.HTML, )
            elif data == 'menu_order':
                if cart.is_full(user_data):
                    # we are not using enter_state_... here because it relies
                    #  on update.message
                    bot.send_message(query.message.chat_id,
                                     text=_('Please choose pickup or delivery'),
                                     reply_markup=create_shipping_keyboard(),
                                     parse_mode=ParseMode.MARKDOWN, )
                    query.answer()
                    return BOT_STATE_CHECKOUT_SHIPPING
                else:
                    bot.answer_callback_query(
                        query.id,
                        text=_('Your cart is empty. '
                               'Please add something to the cart.'),
                        parse_mode=ParseMode.MARKDOWN, )
                    return BOT_STATE_INIT
            elif data == 'menu_hours':
                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=config.get_working_hours(),
                                      reply_markup=create_main_keyboard(
                                          config.get_reviews_channel()),
                                      parse_mode=ParseMode.MARKDOWN, )
            elif data == 'menu_contact':
                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=config.get_contact_info(),
                                      reply_markup=create_main_keyboard(
                                          config.get_reviews_channel()),
                                      parse_mode=ParseMode.MARKDOWN, )
            elif data.startswith('product_add'):
                product_id = int(data.split('|')[1])
                user_data = cart.add(user_data, product_id)
                session_client.json_set(user_id, user_data)

                subtotal = cart.get_product_subtotal(user_data, product_id)
                delivery_fee = config.get_delivery_fee()
                product_title, prices = cart.product_full_info(
                    user_data, product_id)
                product_count = cart.get_product_count(user_data, product_id)

                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=create_product_description(
                                             product_title, prices,
                                             product_count, subtotal,
                                             delivery_fee),
                                      reply_markup=create_product_keyboard(
                                          product_id, user_data, cart),
                                      parse_mode=ParseMode.HTML, )
            elif data.startswith('product_remove'):
                product_id = int(data.split('|')[1])
                user_data = cart.remove(user_data, product_id)
                session_client.json_set(user_id, user_data)

                subtotal = cart.get_product_subtotal(user_data, product_id)
                delivery_fee = config.get_delivery_fee()
                product_title, prices = cart.product_full_info(
                    user_data, product_id)
                product_count = cart.get_product_count(user_data, product_id)

                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=create_product_description(
                                             product_title, prices,
                                             product_count, subtotal,
                                             delivery_fee),
                                      reply_markup=create_product_keyboard(
                                          product_id, user_data, cart),
                                      parse_mode=ParseMode.HTML, )
            else:
                logger.warn('Unknown query: %s', query.data)
        else:
            logger.info('User %s rejected (not a customer)', user_id)
            bot.send_message(
                query.message.chat_id,
                text=_('Sorry {}\nYou are not authorized '
                       'to use this bot').format(query.from_user.first_name),
                reply_markup=None,
                parse_mode=ParseMode.HTML,
            )
            return ConversationHandler.END
    else:
        bot.send_message(
            query.message.chat_id,
            text=_('Sorry, the bot is currently switched off').format(
                query.from_user.first_name),
            reply_markup=None,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END
    query.answer()
    # we want to remain in init state here
    return BOT_STATE_INIT


def on_error(bot, update, error):
    logger.error('Error: %s', error)


# will be called when conversation context is lost (e.g. bot is restarted)
# and the user clicks menu buttons
def fallback_query_handler(bot, update, user_data):
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)
    return on_menu(bot, update, user_data)


#
# state entry functions, use them to enter various stages of checkout
# or return to previous states
#

def enter_state_shipping_method(bot, update, user_data):
    update.message.reply_text(text=_('Please choose pickup or delivery:'),
                              reply_markup=create_shipping_keyboard(),
                              parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_SHIPPING


def enter_state_courier_location(bot, update, user_data):
    locations = Location.select()
    location_names = [x.title for x in locations]
    update.message.reply_text(
        text=_('Please choose where do you want to pickup your order:'),
        reply_markup=create_pickup_location_keyboard(location_names),
        parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_LOCATION_PICKUP


def enter_state_location_delivery(bot, update, user_data):
    update.message.reply_text(
        text=_('Please enter delivery address as text or send a location.'),
        reply_markup=create_cancel_keyboard(), parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_LOCATION_DELIVERY


def enter_state_shipping_time(bot, update, user_data):
    update.message.reply_text(text=_('When do you want to pickup your order?'),
                              reply_markup=create_time_keyboard(),
                              parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_TIME


def enter_state_shipping_time_text(bot, update, user_data):
    update.message.reply_text(text=_(
        'When do you want your order delivered? Please send the time as text.'),
        reply_markup=create_cancel_keyboard(), parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_TIME_TEXT


def enter_state_phone_number_text(bot, update, user_data):
    update.message.reply_text(text=_('Please send your phone number.'),
                              reply_markup=create_cancel_keyboard(),
                              parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_PHONE_NUMBER_TEXT


def enter_state_identify_photo(bot, update, user_data):
    user_id = get_user_id(update)
    session = get_user_session(user_id)
    if 'photo_question' not in session['shipping']:
        session['shipping']['photo_question'] = create_photo_question()
    else:
        session['shipping']['photo_question'] = {}
        session['shipping']['photo_question'] = create_photo_question()

    text = _('Please provide an identification picture. {}').format(
        session['shipping']['photo_question'])
    update.message.reply_text(text=text, reply_markup=create_cancel_keyboard(),
                              parse_mode=ParseMode.MARKDOWN, )
    return BOT_STATE_CHECKOUT_IDENTIFY_STAGE1


def enter_state_identify_stage2(bot, update, user_data):
    update.message.reply_text(text=config.get_identification_stage2_question(),
                              reply_markup=create_cancel_keyboard(),
                              parse_mode=ParseMode.MARKDOWN,
                              )

    return BOT_STATE_CHECKOUT_IDENTIFY_STAGE2


def enter_state_order_confirm(bot, update, user_data):
    is_pickup = user_data['shipping']['method'] == BUTTON_TEXT_PICKUP
    shipping_data = user_data['shipping']
    total = cart.get_cart_total(user_data)
    delivery_cost = config.get_delivery_fee()
    product_info = cart.get_products_info(user_data)
    update.message.reply_text(
        text=create_confirmation_text(
            is_pickup, shipping_data, total, delivery_cost, product_info),
        reply_markup=create_confirmation_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    return BOT_STATE_ORDER_CONFIRMATION


def enter_state_init_order_confirmed(bot, update, user_data):
    bot.send_message(
        update.message.chat_id,
        text=config.get_order_complete_text().format(
            update.message.from_user.first_name),
        reply_markup=ReplyKeyboardRemove(),
    )
    bot.send_message(
        update.message.chat_id,
        text='〰〰〰〰〰〰〰〰〰〰〰〰️',
        reply_markup=create_main_keyboard(config.get_reviews_channel()),
    )

    return BOT_STATE_INIT


def enter_state_init_order_cancelled(bot, update, user_data):
    update.message.reply_text(text=_('<b>Order cancelled</b>'),
                              reply_markup=ReplyKeyboardRemove(),
                              parse_mode=ParseMode.HTML, )
    # send menu again as a new message
    bot.send_message(update.message.chat_id,
                     text=config.get_welcome_text().format(
                         update.message.from_user.first_name),
                     reply_markup=create_main_keyboard(
                         config.get_reviews_channel()), )
    return BOT_STATE_INIT

#
# confirmation handlers
#


def on_shipping_method(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)
    if key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    else:
        user_data['shipping']['method'] = key
        session_client.json_set(user_id, user_data)
        return enter_state_courier_location(bot, update, user_data)


def on_shipping_pickup_location(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_BACK:
        return enter_state_shipping_method(bot, update, user_data)
    elif key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    else:
        user_data['shipping']['pickup_location'] = key
        session_client.json_set(user_id, user_data)

        if user_data['shipping']['method'] == BUTTON_TEXT_DELIVERY:
            return enter_state_location_delivery(bot, update, user_data)
        else:
            return enter_state_shipping_time(bot, update, user_data)


def on_shipping_delivery_address(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if update.message.location:
        location = update.message.location
        user_data['shipping']['location'] = location
        session_client.json_set(user_id, user_data)

        return enter_state_shipping_time(bot, update, user_data)
    else:
        if key == BUTTON_TEXT_BACK:
            return enter_state_shipping_method(bot, update, user_data)
        elif key == BUTTON_TEXT_CANCEL:
            return enter_state_init_order_cancelled(bot, update, user_data)
        else:
            address = update.message.text
            user_data['shipping']['address'] = address
            session_client.json_set(user_id, user_data)

            return enter_state_shipping_time(bot, update, user_data)


def on_checkout_time(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)
    if key == BUTTON_TEXT_BACK:
        return enter_state_shipping_method(bot, update, user_data)
    elif key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    elif key == BUTTON_TEXT_NOW:
        user_data['shipping']['time'] = key
        session_client.json_set(user_id, user_data)

        if config.get_phone_number_required():
            return enter_state_phone_number_text(bot, update, user_data)
        else:
            if config.get_identification_required():
                return enter_state_identify_photo(bot, update, user_data)
            else:
                return enter_state_order_confirm(bot, update, user_data)
    elif key == BUTTON_TEXT_SETTIME:
        user_data['shipping']['time'] = key
        session_client.json_set(user_id, user_data)

        return enter_state_shipping_time_text(bot, update, user_data)
    else:
        logger.warn("Unknown input %s", key)


def on_shipping_time_text(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_BACK:
        return enter_state_shipping_time(bot, update, user_data)
    elif key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    else:
        user_data['shipping']['time_text'] = key
        session_client.json_set(user_id, user_data)

        return enter_state_phone_number_text(bot, update, user_data)


def on_phone_number_text(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    elif key == BUTTON_TEXT_BACK:
        return enter_state_shipping_time(bot, update, user_data)
    else:
        phone_number_text = update.message.text
        user_data['shipping']['phone_number'] = phone_number_text
        session_client.json_set(user_id, user_data)

        if is_vip_customer(bot, user_id):
            vip = _('vip costumer')
            user_data['shipping']['vip'] = vip
            session_client.json_set(user_id, user_data)

            return enter_state_order_confirm(bot, update, user_data)
        elif config.get_identification_required():
            return enter_state_identify_photo(bot, update, user_data)
        else:
            return enter_state_order_confirm(bot, update, user_data)


def on_shipping_identify_photo(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    elif key == BUTTON_TEXT_BACK:
        if config.get_phone_number_required():
            return enter_state_phone_number_text(bot, update, user_data)
        else:
            return enter_state_shipping_time(bot, update, user_data)
    if update.message.photo:
        photo_file = bot.get_file(update.message.photo[-1].file_id)
        user_data['shipping']['photo_id'] = photo_file.file_id
        session_client.json_set(user_id, user_data)
        #
        if config.get_identification_stage2_required():
            return enter_state_identify_stage2(bot, update, user_data)
        else:
            return enter_state_order_confirm(bot, update, user_data)
    else:
        # No photo, ask the user again
        return enter_state_identify_photo(bot, update, user_data)


def on_shipping_identify_stage2(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    elif key == BUTTON_TEXT_BACK:
        return enter_state_identify_photo(bot, update, user_data)

    if update.message.photo:
        photo_file = bot.get_file(update.message.photo[-1].file_id)
        user_data['shipping']['stage2_id'] = photo_file.file_id
        session_client.json_set(user_id, user_data)

        return enter_state_order_confirm(bot, update, user_data)
    else:
        # No photo, ask the user again

        return enter_state_identify_stage2(bot, update, user_data)


def on_confirm_order(bot, update, user_data):
    key = update.message.text

    # order data
    user_id = get_user_id(update)
    username = get_username(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_CONFIRM:
        try:
            user = User.get(telegram_id=user_id)
        except User.DoesNotExist:
            if not username:
                user = User.create(telegram_id=user_id, username=_('No User Name'))
            else:
                user = User.create(telegram_id=user_id, username=username)
        try:
            location = Location.get(
                title=user_data.get('shipping', {}).get('pickup_location'))
        except Location.DoesNotExist:
            location = None
        order = Order.create(user=user, location=location)
        order_id = order.id
        cart.fill_order(user_data, order)
        is_pickup = user_data['shipping']['method'] == BUTTON_TEXT_PICKUP
        product_info = cart.get_products_info(user_data)
        shipping_data = user_data['shipping']
        total = cart.get_cart_total(user_data)
        delivery_cost = config.get_delivery_fee()
        # ORDER CONFIRMED, send the details to service channel
        bot.send_message(config.get_service_channel(),
                         text=_('Order confirmed from (@{})').format(
                             update.message.from_user.username),
                         parse_mode=ParseMode.MARKDOWN, )

        bot.send_message(config.get_service_channel(),
                         text=create_service_notice(
                             is_pickup, order_id, product_info, shipping_data,
                             total, delivery_cost),
                         parse_mode=ParseMode.HTML,
                         )

        if 'photo_id' in user_data['shipping']:
            bot.send_photo(config.get_service_channel(),
                           photo=user_data['shipping']['photo_id'],
                           caption=_('Stage 1 Identification - Selfie'),
                           parse_mode=ParseMode.MARKDOWN, )


        if 'stage2_id' in user_data['shipping']:
            bot.send_photo(
                config.get_service_channel(),
                photo=user_data['shipping']['stage2_id'],
                caption=_('Stage 2 Identification - FB'),
                parse_mode=ParseMode.MARKDOWN, )

        if 'location' in user_data['shipping']:
            bot.send_location(
                config.get_service_channel(),
                location=user_data['shipping']['location']
            )

        if config.get_has_courier_option():
            bot.send_message(config.get_couriers_channel(),
                             text=_('Order confirmed from (@{})').format(
                                 update.message.from_user.username),
                             parse_mode=ParseMode.MARKDOWN, )
            bot.send_message(config.get_couriers_channel(),
                             text=create_service_notice(
                                 is_pickup, order_id, product_info, shipping_data,
                                 total, delivery_cost),
                             parse_mode=ParseMode.HTML,
                             reply_markup=create_service_notice_keyboard(
                                 update, user_id, order_id),
                             )
            if 'photo_id' in user_data['shipping']:
                bot.send_photo(config.get_couriers_channel(),
                               photo=user_data['shipping']['photo_id'],
                               caption=_('Stage 1 Identification - Selfie'),
                               parse_mode=ParseMode.MARKDOWN, )

            if 'location' in user_data['shipping']:
                bot.send_location(
                    config.get_couriers_channel(),
                    location=user_data['shipping']['location']
                )

        # clear cart and shipping data
        user_data['cart'] = {}
        user_data['shipping'] = {}
        session_client.json_set(user_id, user_data)

        return enter_state_init_order_confirmed(bot, update, user_data)

    elif key == BUTTON_TEXT_CANCEL:
        # ORDER CANCELLED, send nothing
        # and only clear shipping details
        user_data['shipping'] = {}
        session_client.json_set(user_id, user_data)

        return enter_state_init_order_cancelled(bot, update, user_data)
    elif key == BUTTON_TEXT_BACK:
        if config.get_identification_required():
            if config.get_identification_stage2_required():
                return enter_state_identify_stage2(bot, update, user_data)
            else:
                return enter_state_identify_photo(bot, update, user_data)
        elif config.get_phone_number_required():
            return enter_state_phone_number_text(bot, update, user_data)
        else:
            return enter_state_shipping_time(bot, update, user_data)
    else:
        logger.warn("Unknown input %s", key)


def on_cancel(bot, update, user_data):
    return enter_state_init_order_cancelled(bot, update, user_data)


def checkout_fallback_command_handler(bot, update, user_data):
    query = update.callback_query
    bot.answer_callback_query(query.id, text=_(
        'Cannot process commands when checking out'))


#
# handle couriers
#

def service_channel_courier_query_handler(bot, update, user_data):
    query = update.callback_query
    data = query.data
    label, user_id, courier_id, order_id, courier_nickname = data.split('|')
    try:
        if order_id:
            order = Order.get(id=order_id)
        else:
            raise Order.DoesNotExist()
    except Order.DoesNotExist:
        logger.info('Order №{} not found!'.format(order_id))
    else:
        try:
            courier = Courier.get(telegram_id=courier_id)
        except Courier.DoesNotExist:
            courier = Courier.create(
                telegram_id=courier_id, username=courier_nickname)
        if courier.location == order.location:
            order.courier = courier
            order.save()
            bot.delete_message(config.get_couriers_channel(),
                               message_id=query.message.message_id)
            bot.send_message(config.get_couriers_channel(),
                             text=query.message.text, parse_mode=ParseMode.HTML,
                             reply_markup=create_drop_responsibility_keyboard(
                                 user_id, courier_nickname, order_id),
                             )
            bot.send_message(config.get_service_channel(),
                             text='Courier: {}, apply for order №{}. '
                                  'Confirm this?'.format(
                                 courier_nickname, order_id),
                             reply_markup=create_courier_confirmation_keyboard(
                                 order_id, courier_nickname),
                             )
            bot.answer_callback_query(
                query.id,
                text=_('Courier {} assigned').format(courier_nickname))
        else:
            bot.send_message(config.get_couriers_channel(),
                             text='{} your location and customer locations are '
                                  'different'.format(courier_nickname),
                             parse_mode=ParseMode.HTML
                             )


#
# main
#

def main():
    user_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', on_start, pass_user_data=True),
                      CommandHandler('admin', on_start_admin),
                      CallbackQueryHandler(fallback_query_handler,
                                           pattern='^(menu|product)',
                                           pass_user_data=True)],
        states={
            BOT_STATE_INIT: [
                CommandHandler('start', on_start, pass_user_data=True),
                CommandHandler('admin', on_start_admin),
                CallbackQueryHandler(
                    on_menu, pattern='^(menu|product)', pass_user_data=True)
            ],
            BOT_STATE_CHECKOUT_SHIPPING: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text, on_shipping_method,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_LOCATION_PICKUP: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text, on_shipping_pickup_location,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_LOCATION_DELIVERY: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text | Filters.location,
                               on_shipping_delivery_address,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_TIME: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text, on_checkout_time,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_TIME_TEXT: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text, on_shipping_time_text,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_PHONE_NUMBER_TEXT: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text, on_phone_number_text,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_IDENTIFY_STAGE1: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.all, on_shipping_identify_photo,
                               pass_user_data=True),
            ],
            BOT_STATE_CHECKOUT_IDENTIFY_STAGE2: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.all, on_shipping_identify_stage2,
                               pass_user_data=True),
            ],
            BOT_STATE_ORDER_CONFIRMATION: [
                CallbackQueryHandler(checkout_fallback_command_handler,
                                     pass_user_data=True),
                MessageHandler(Filters.text, on_confirm_order,
                               pass_user_data=True),
            ],

            #
            # admin states
            #
            ADMIN_INIT: [
                CommandHandler('addproduct', on_admin_cmd_add_product),
                CommandHandler('delproduct', on_admin_cmd_delete_product),
                CommandHandler('addcourier', on_admin_cmd_add_courier),
                CommandHandler('delcourier', on_admin_cmd_delete_courier),
                CommandHandler('on', on_admin_cmd_bot_on),
                CommandHandler('off', on_admin_cmd_bot_off),
                CommandHandler('cancel', on_admin_cancel),
                MessageHandler(Filters.all, on_admin_fallback),
            ],
            ADMIN_TXT_PRODUCT_TITLE: [
                MessageHandler(Filters.text, on_admin_txt_product_title,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_PRODUCT_PRICES: [
                MessageHandler(Filters.text, on_admin_txt_product_prices,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_PRODUCT_PHOTO: [
                MessageHandler(Filters.photo, on_admin_txt_product_photo,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_DELETE_PRODUCT: [
                MessageHandler(Filters.text, on_admin_txt_delete_product),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_COURIER_NAME: [
                MessageHandler(Filters.text, on_admin_txt_courier_name,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_COURIER_LOCATION: [
                MessageHandler(Filters.text, on_admin_txt_courier_location,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_DELETE_COURIER: [
                MessageHandler(Filters.text, on_admin_txt_delete_courier),
                CommandHandler('cancel', on_admin_cancel),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', on_cancel, pass_user_data=True),
            CommandHandler('start', on_start, pass_user_data=True)
        ])

    updater = Updater(config.get_api_token())
    updater.dispatcher.add_handler(user_conversation_handler)
    updater.dispatcher.add_handler(
        CallbackQueryHandler(service_channel_courier_query_handler,
                             pattern='^courier',
                             pass_user_data=True))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(resend_responsibility_keyboard,
                             pattern='^dropped',
                             pass_user_data=True))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(make_confirm,
                             pattern='^confirmed',
                             pass_user_data=True))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(make_unconfirm,
                             pattern='^notconfirmed',
                             pass_user_data=True))
    updater.dispatcher.add_error_handler(on_error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    create_tables()
    main()
