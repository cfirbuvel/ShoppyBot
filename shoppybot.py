#! /usr/bin/env python3
import random
import datetime

from telegram import InputMediaPhoto
from telegram.ext import CallbackQueryHandler, CommandHandler, \
    ConversationHandler, Filters, MessageHandler, Updater, BaseFilter

from src.admin import *
from src.enums import *
from src.messages import create_confirmation_text, create_product_description, \
    create_service_notice
from src.helpers import session_client, get_user_session, \
    get_user_id, get_username
from src.keyboards import create_drop_responsibility_keyboard, \
    create_service_notice_keyboard, create_main_keyboard, \
    create_pickup_location_keyboard, create_product_keyboard, \
    create_shipping_keyboard, create_cancel_keyboard, create_time_keyboard, \
    create_confirmation_keyboard, create_courier_confirmation_keyboard, \
    create_admin_keyboard, create_statistics_keyboard, \
    create_bot_settings_keyboard, create_bot_couriers_keyboard, \
    create_bot_channels_keyboard, create_bot_order_options_keyboard, \
    create_back_button, create_on_off_buttons, create_ban_list_keyboard, create_service_channel_keyboard, \
    create_bot_locations_keyboard, create_locations_keyboard

from src.models import create_tables, User, Courier, Order, OrderItem, \
    Product, ProductCount


# logging.basicConfig(stream=sys.stderr, format='%(asctime)s %(message)s',
#                     level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# cat = gettext.GNUTranslations(open('he.mo', 'rb'))
# # DEBUG = os.environ.get('DEBUG')
#
# # if not DEBUG:
# #     _ = cat.gettext
#
# # if DEBUG:
# config = ConfigHelper(cfgfilename='test_conf.conf')
# # else:
# #     config = ConfigHelper()

_ = gettext.gettext

#
# bot helper functions
#


def is_vip_customer(bot, user_id):
    if not config.get_vip_customers():
        return False

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
            text=_('Courier @{} assigned for order № {}').format(courier_name, order_id),
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
    try:
        user = User.get(telegram_id=user_id)
    except User.DoesNotExist:
        user = User(telegram_id=user_id, username=username)
        user.save()
    BOT_ON = config.get_bot_on_off() and username not in config.get_banned_users()
    if BOT_ON or is_admin(bot, user_id):
        if is_customer(bot, user_id) or is_vip_customer(bot, user_id):
            total = cart.get_cart_total(get_user_session(user_id))
            logger.info('Starting session for user %s, language: %s',
                        update.message.from_user.id,
                        update.message.from_user.language_code)

            # TODO: Send photo with caption and the keyboard
            photo_link = 'https://2.bp.blogspot.com/-XZN2TA7nQZ0/WGSL3ia76KI/AAAAAAAAGuE' \
                         '/8pxmxtrizn8Yu1Y6iIArXYBgsL3Rhww3ACLcB/s1600/telegram-bot.png '
            bot.send_photo(
                chat_id=update.message.chat_id,
                photo=photo_link,
                caption=config.get_welcome_text().format(
                    update.message.from_user.first_name),
            )
            update.message.reply_text(
                text=config.get_welcome_text().format(
                    update.message.from_user.first_name),
                reply_markup=create_main_keyboard(config.get_reviews_channel(),
                                                  is_admin(bot, user_id),
                                                  total),
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
    BOT_ON = config.get_bot_on_off()
    total = cart.get_cart_total(get_user_session(user_id))
    if BOT_ON or is_admin(bot, user_id):
        if is_customer(bot, user_id) or is_vip_customer(bot, user_id):
            if data == 'menu_products':
                # the menu disappears
                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=_('Our products:'),
                                      parse_mode=ParseMode.MARKDOWN, )

                # send_products to current chat
                for product in Product.filter(is_active=True):
                    product_count = cart.get_product_count(
                        user_data, product.id)
                    subtotal = cart.get_product_subtotal(
                        user_data, product.id)
                    delivery_fee = config.get_delivery_fee()
                    delivery_min = config.get_delivery_min()
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
                                         delivery_min, delivery_fee),
                                     reply_markup=create_product_keyboard(
                                         product.id, user_data, cart),
                                     parse_mode=ParseMode.HTML,
                                     timeout=20, )

                # send menu again as a new message
                bot.send_message(query.message.chat_id,
                                 text=config.get_order_text(),
                                 reply_markup=create_main_keyboard(
                                     config.get_reviews_channel(),
                                     is_admin(bot, user_id), total),
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
                                          config.get_reviews_channel(),
                                          is_admin(bot, user_id), total),
                                      parse_mode=ParseMode.MARKDOWN, )
            elif data == 'menu_contact':
                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=config.get_contact_info(),
                                      reply_markup=create_main_keyboard(
                                          config.get_reviews_channel(),
                                          is_admin(bot, user_id), total),
                                      parse_mode=ParseMode.MARKDOWN, )
            elif data.startswith('product_add'):
                product_id = int(data.split('|')[1])
                user_data = cart.add(user_data, product_id)
                session_client.json_set(user_id, user_data)

                subtotal = cart.get_product_subtotal(user_data, product_id)
                delivery_fee = config.get_delivery_fee()
                delivery_min = config.get_delivery_min()
                product_title, prices = cart.product_full_info(
                    user_data, product_id)
                product_count = cart.get_product_count(user_data, product_id)

                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=create_product_description(
                                          product_title, prices,
                                          product_count, subtotal,
                                          delivery_min, delivery_fee),
                                      reply_markup=create_product_keyboard(
                                          product_id, user_data, cart),
                                      parse_mode=ParseMode.HTML, )
            elif data.startswith('product_remove'):
                product_id = int(data.split('|')[1])
                user_data = cart.remove(user_data, product_id)
                session_client.json_set(user_id, user_data)

                subtotal = cart.get_product_subtotal(user_data, product_id)
                delivery_fee = config.get_delivery_fee()
                delivery_min = config.get_delivery_min()
                product_title, prices = cart.product_full_info(
                    user_data, product_id)
                product_count = cart.get_product_count(user_data, product_id)

                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=create_product_description(
                                          product_title, prices,
                                          product_count, subtotal,
                                          delivery_min, delivery_fee),
                                      reply_markup=create_product_keyboard(
                                          product_id, user_data, cart),
                                      parse_mode=ParseMode.HTML, )
            elif data == 'menu_settings':
                bot.edit_message_text(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      text=_('⚙️ Settings'),
                                      reply_markup=create_admin_keyboard(),
                                      parse_mode=ParseMode.MARKDOWN, )
                query.answer()
                return ADMIN_MENU
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
                              reply_markup=create_phone_number_request_keyboard(),
                            )
    return BOT_STATE_CHECKOUT_PHONE_NUMBER_TEXT


def enter_state_identify_photo(bot, update, user_data):
    user_id = get_user_id(update)
    session = get_user_session(user_id)
    if 'photo_question' not in session['shipping']:
        session['shipping']['photo_question'] = create_photo_question()
    else:
        session['shipping']['photo_question'] = {}
        session['shipping']['photo_question'] = create_photo_question()
    session_client.json_set(user_id, session)
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
    delivery_min = config.get_delivery_min()
    product_info = cart.get_products_info(user_data)
    update.message.reply_text(
        text=create_confirmation_text(
            is_pickup, shipping_data, total, delivery_cost, delivery_min, product_info),
        reply_markup=create_confirmation_keyboard(),
        parse_mode=ParseMode.HTML,
    )

    return BOT_STATE_ORDER_CONFIRMATION


def enter_state_init_order_confirmed(bot, update, user_data):
    user_id = get_user_id(update)
    total = cart.get_cart_total(get_user_session(user_id))
    bot.send_message(
        update.message.chat_id,
        text=config.get_order_complete_text().format(
            update.message.from_user.first_name),
        reply_markup=ReplyKeyboardRemove(),
    )
    bot.send_message(
        update.message.chat_id,
        text='〰〰〰〰〰〰〰〰〰〰〰〰️',
        reply_markup=create_main_keyboard(
            config.get_reviews_channel(), is_admin(bot, user_id), total),
    )

    return BOT_STATE_INIT


def enter_state_init_order_cancelled(bot, update, user_data):
    user_id = get_user_id(update)
    total = cart.get_cart_total(get_user_session(user_id))
    user_data['cart'] = {}
    user_data['shipping'] = {}
    session_client.json_set(user_id, user_data)
    update.message.reply_text(text=_('<b>Order cancelled</b>'),
                              reply_markup=ReplyKeyboardRemove(),
                              parse_mode=ParseMode.HTML, )
    # send menu again as a new message
    bot.send_message(update.message.chat_id,
                     text=config.get_welcome_text().format(
                         update.message.from_user.first_name),
                     reply_markup=create_main_keyboard(
                         config.get_reviews_channel(), is_admin(bot, user_id),
                         total))
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
    elif key == BUTTON_TEXT_PICKUP or key == BUTTON_TEXT_DELIVERY:
        user_data['shipping']['method'] = key
        session_client.json_set(user_id, user_data)
        return enter_state_courier_location(bot, update, user_data)
    else:
        return enter_state_shipping_method(bot, update, user_data)



def on_bot_language_change(bot, update, user_data):
    query = update.callback_query
    data = query.data
    # user_id = get_user_id(update)
    # user_data = get_user_session(user_id)
    global _
    if data == 'lng_en':
        _ = gettext.gettext
    elif data == 'lng_he':
        _ = cat.gettext
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=_('⚙ Bot settings'),
                          reply_markup=create_bot_settings_keyboard(),
                          parse_mode=ParseMode.MARKDOWN)
    query.answer()
    return ADMIN_BOT_SETTINGS
    
def on_shipping_pickup_location(bot, update, user_data):
    key = update.message.text
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)
    locations = Location.select()
    location_names = [x.title for x in locations]

    if key == BUTTON_TEXT_BACK:
        return enter_state_shipping_method(bot, update, user_data)
    elif key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    elif any(key in s for s in location_names):
        user_data['shipping']['pickup_location'] = key
        session_client.json_set(user_id, user_data)

        if user_data['shipping']['method'] == BUTTON_TEXT_DELIVERY:
            return enter_state_location_delivery(bot, update, user_data)
        else:
            return enter_state_shipping_time(bot, update, user_data)
    else:
        return enter_state_courier_location(bot, update, user_data)


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
        return enter_state_shipping_time(bot, update, user_data)


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


def on_phone_number_text(bot, update):
    key = update.message.text       # karoxa try-ov ylni kaxvats contact em tvel te back u cancel em arel
    user_id = get_user_id(update)
    user_data = get_user_session(user_id)

    if key == BUTTON_TEXT_CANCEL:
        return enter_state_init_order_cancelled(bot, update, user_data)
    elif key == BUTTON_TEXT_BACK:
        return enter_state_shipping_time(bot, update, user_data)
    else:
        phone_number_text = update.message.contact.phone_number
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
        order = Order.create(user=user, location=location,
                             date_created=datetime.datetime.now())
        order_id = order.id
        cart.fill_order(user_data, order)
        is_pickup = user_data['shipping']['method'] == BUTTON_TEXT_PICKUP
        product_info = cart.get_products_info(user_data)
        shipping_data = user_data['shipping']
        total = cart.get_cart_total(user_data)
        delivery_cost = config.get_delivery_fee()
        delivery_min = config.get_delivery_min()

        # Test New Keyboard

        # is_vip = False
        # show_order = False
        # if is_vip_customer(bot, user_id):
        #     is_vip = True
        # bot.send_message(config.get_service_channel(),
        #                  text=_('Order confirmed from (@{}), order id {}').format(
        #                      update.message.from_user.username, order_id),
        #                  parse_mode=ParseMode.MARKDOWN,
        #                  reply_markup=create_service_channel_keyboard(order_id, show_order, is_vip)
        #                  )

        # ORDER CONFIRMED, send the details to service channel
        txt = _('Order confirmed from (@{})\n\n').format(update.message.from_user.username)
        bot.send_message(config.get_service_channel(),
                         text=txt + create_service_notice(
                             is_pickup, order_id, product_info, shipping_data,
                             total, delivery_min, delivery_cost),
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
                                 is_pickup, order_id, product_info,
                                 shipping_data, total, delivery_min, delivery_cost),
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
    courier_nickname = get_username(update)
    courier_id = get_user_id(update)
    label, user_id, order_id = data.split('|')
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
            pass

        else:
            try:
                CourierLocation.get(courier=courier, location=order.location)
                order.courier = courier
                order.save()
                bot.delete_message(config.get_couriers_channel(),
                                   message_id=query.message.message_id)
                bot.send_message(
                    config.get_couriers_channel(),
                    text=query.message.text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=create_drop_responsibility_keyboard(
                        user_id, courier_nickname, order_id),
                )
                bot.send_message(
                    config.get_service_channel(),
                    text='Courier: {}, apply for order №{}. '
                         'Confirm this?'.format(
                        courier_nickname, order_id),
                    reply_markup=create_courier_confirmation_keyboard(
                        order_id, courier_nickname),
                )
                bot.answer_callback_query(
                    query.id,
                    text=_('Courier {} assigned').format(courier_nickname))
            except CourierLocation.DoesNotExist:
                bot.send_message(
                    config.get_couriers_channel(),
                    text='{} your location and customer locations are '
                         'different'.format(courier_nickname),
                    parse_mode=ParseMode.HTML
                )


def send_welcome_message(bot, update):
    if str(update.message.chat_id) == config.get_couriers_channel():
        users = update.message.new_chat_members
        for user in users:
            if user:
                bot.send_message(
                    config.get_couriers_channel(),
                    text=_('Hello `@{}`\nID number `{}`').format(
                        user.username, user.id),
                    parse_mode=ParseMode.MARKDOWN)


def on_settings_menu(bot, update):
    query = update.callback_query
    data = query.data
    user_id = get_user_id(update)
    total = cart.get_cart_total(get_user_session(user_id))
    if data == 'settings_statistics':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('📈 Statistics'),
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS
    elif data == 'settings_bot':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('⚙ Bot settings'),
                              reply_markup=create_bot_settings_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_SETTINGS
    elif data == 'settings_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=config.get_welcome_text().format(
                                  update.callback_query.from_user.first_name),
                              reply_markup=create_main_keyboard(
                                  config.get_reviews_channel(),
                                  is_admin(bot, user_id), total),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return BOT_STATE_INIT
    else:
        logger.info('Unknown command - {}'.format(data))
        bot.send_message(
            query.message.chat_id,
            text=_('Unknown command'),
            reply_markup=None,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END


def on_statistics_menu(bot, update):
    query = update.callback_query
    data = query.data
    if data == 'statistics_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('⚙️ Settings'),
                              reply_markup=create_admin_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_MENU
    elif data == 'statistics_all_sells':
        orders_count = Order.select().where(Order.confirmed == True).count()
        total_price = 0
        orders_items = OrderItem.select().join(Order).where(
            Order.confirmed == True)
        for order_item in orders_items:
            total_price += order_item.count * order_item.total_price
        message = _('Total confirmed orders\n\ncount: {}\ntotal cost: {}').format(
            orders_count, total_price)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=message,
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS
    elif data == 'statistics_couriers':
        msg = ''
        couriers = Courier.select()
        for courier in couriers:
            orders_count = Order.select().where(Order.courier == courier,
                                                Order.confirmed == True).count()
            total_price = 0
            orders_items = OrderItem.select().join(Order).where(
                Order.confirmed == True, Order.courier == courier)
            for order_item in orders_items:
                total_price += order_item.count * order_item.total_price
            msg += _('Courier: `@{}`\nOrders: {}, orders cost {}').format(
                courier.username, orders_count, total_price)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS
    elif data == 'statistics_locations':
        msg = ''
        locations = Location.select()
        for location in locations:
            orders_count = Order.select().where(Order.location == location,
                                                Order.confirmed == True).count()
            total_price = 0
            orders_items = OrderItem.select().join(Order).where(
                Order.confirmed == True, Order.location == location)
            for order_item in orders_items:
                total_price += order_item.count * order_item.total_price
            msg += _('Location: {}\nOrders: {}, orders cost {}').format(
                location.title, orders_count, total_price)
            msg += '\n\n'
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS
    elif data == 'statistics_yearly':
        now = datetime.datetime.now()
        orders_count = Order.select().where(Order.date_created.year == now.year,
                                            Order.confirmed == True).count()
        total_price = 0
        orders_items = OrderItem.select().join(Order).where(
            Order.confirmed == True, Order.date_created.year == now.year)
        for order_item in orders_items:
            total_price += order_item.count * order_item.total_price
        msg = _('Orders: {}, orders cost {}').format(
            orders_count, total_price)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS
    elif data == 'statistics_monthly':
        now = datetime.datetime.now()
        orders_count = Order.select().where(Order.date_created.year == now.month,
                                            Order.confirmed == True).count()
        total_price = 0
        orders_items = OrderItem.select().join(Order).where(
            Order.confirmed == True, Order.date_created.year == now.month)
        for order_item in orders_items:
            total_price += order_item.count * order_item.total_price
        msg = _('Orders: {}, orders cost {}').format(
            orders_count, total_price)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS
    elif data == 'statistics_user':
        msg = ''
        users = User.select()
        for user in users:
            orders_count = Order.select().where(Order.user == user,
                                                Order.confirmed == True).count()
            total_price = 0
            orders_items = OrderItem.select().join(Order).where(
                Order.confirmed == True, Order.location == user)
            for order_item in orders_items:
                total_price += order_item.count * order_item.total_price
            msg += '\nUser: @{}, orders: {}, orders cost {}'.format(
                user.username, orders_count, total_price)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_statistics_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_STATISTICS

    return ConversationHandler.END


def on_bot_settings_menu(bot, update):
    query = update.callback_query
    data = query.data
    # user_id = get_user_id(update)
    if data == 'bot_settings_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('⚙️ Settings'),
                              reply_markup=create_admin_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_MENU
    elif data == 'bot_settings_couriers':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('🛵 Couriers'),
                              reply_markup=create_bot_couriers_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_COURIERS
    elif data == 'bot_settings_channels':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('✉️ Channels'),
                              reply_markup=create_bot_channels_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_CHANNELS
    elif data == 'bot_settings_order_options':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('💳 Order options'),
                              reply_markup=create_bot_order_options_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_ORDER_OPTIONS
    elif data == 'bot_settings_edit_working_hours':
        msg = _('Now:\n\n`{}`\n\n').format(config.get_working_hours())
        msg += _('Type new working hours')
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_EDIT_WORKING_HOURS
    elif data == 'bot_settings_ban_list':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text='Ban list',
                              reply_markup=create_ban_list_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BAN_LIST
    elif data == 'bot_settings_edit_contact_info':
        msg = _('Now:\n\n`{}`\n\n').format(config.get_contact_info())
        msg += _('Type new contact info')
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_EDIT_CONTACT_INFO
    elif data == 'bot_settings_bot_on_off':
        bot_status = config.get_bot_on_off()
        bot_status = _('ON') if bot_status else _('OFF')
        msg = _('Bot status: {}').format(bot_status)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_on_off_buttons(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_ON_OFF
    
    elif data == 'bot_settings_reset_all_data':
        set_config_session({})
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text='Config options were deleted',
                              reply_markup=create_bot_settings_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_SETTINGS

    return ConversationHandler.END


def on_admin_locations(bot, update):
    query = update.callback_query
    data = query.data
    if data == 'bot_locations_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('💳 Order options'),
                              reply_markup=create_bot_order_options_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_ORDER_OPTIONS
    elif data == 'bot_locations_view':
        locations = Location.select()
        location_names = [x.title for x in locations]
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('Your locations:\n\n{}').format(location_names),
                              reply_markup=create_bot_locations_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_LOCATIONS
    elif data == 'bot_locations_add':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('Enter new location'),
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=create_back_button()
                              ),
        query.answer()
        return ADMIN_TXT_ADD_LOCATION
    elif data == 'bot_locations_delete':
        locations = Location.select()
        location_names = [x.title for x in locations]

        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('Choose location to delete'),
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=create_locations_keyboard(location_names)
                              )
        query.answer()
        return ADMIN_TXT_DELETE_LOCATION

    return ConversationHandler.END


def on_admin_couriers(bot, update):
    query = update.callback_query
    data = query.data
    if data == 'bot_couriers_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('⚙ Bot settings'),
                              reply_markup=create_bot_settings_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_SETTINGS
    elif data == 'bot_couriers_view':
        msg = ''
        couriers = Courier.select()
        for courier in couriers:
            locations = CourierLocation.filter(courier=courier)
            locations = [item.location.title for item in locations]
            msg += _('name:\n`@{}`\n').format(courier.username)
            msg += _('courier ID:\n`{}`\n').format(courier.id)
            msg += _('telegram ID:\n`{}`\n').format(courier.telegram_id)
            msg += _('locations:\n{}\n').format(locations)
            # msg += _('locale:\n`{}`').format(courier.locale)
            msg += '~~~~~~\n\n'
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_bot_couriers_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_COURIERS
    elif data == 'bot_couriers_add':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('Enter new courier nickname'),
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=create_back_button()
                              ),

        return ADMIN_TXT_COURIER_NAME
    elif data == 'bot_couriers_delete':

        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('Choose courier ID to delete'),
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=create_back_button()
                              )

        return ADMIN_TXT_DELETE_COURIER

    return ConversationHandler.END


def on_admin_channels(bot, update):
    query = update.callback_query
    data = query.data
    if data == 'bot_channels_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('⚙ Bot settings'),
                              reply_markup=create_bot_settings_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_SETTINGS
    elif data == 'bot_channels_view':
        # msg = u'Reviews channel: {}'.format(config.get_reviews_channel())
        msg = _('Service channel ID:\n`{}`\n\n').format(config.get_service_channel())
        msg += _('Customer channel:\n`@{}`\n\n').format(config.get_customers_channel())
        msg += _('Vip customer channel ID:\n`{}`\n\n').format(
            config.get_vip_customers_channel())
        msg += _('Courier group ID:\n`{}`\n\n').format(config.get_couriers_channel())

        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_bot_channels_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_CHANNELS
    elif data == 'bot_channels_add':
        types = [_('Service'), _('Customer'), _('Vip Customer'), _('Courier')]
        msg = ''
        for i, channel_type in enumerate(types, start=1):
            msg += '\n{} - {}'.format(i, channel_type)
        msg += _('\n\nSelect channel type')
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=create_back_button()
                              )

        return ADMIN_CHANNELS_SELECT_TYPE
    elif data == 'bot_channels_remove':
        types = [_('Service'), _('Customer'), _('Vip Customer'), _('Courier')]
        msg = ''
        for i, channel_type in enumerate(types, start=1):
            msg += '\n{} - {}'.format(i, channel_type)
        msg += _('\n\nSelect channel type')
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              parse_mode=ParseMode.MARKDOWN,
                              reply_markup=create_back_button()
                              )

        return ADMIN_CHANNELS_REMOVE

    return ConversationHandler.END


def on_admin_ban_list(bot, update):
    query = update.callback_query
    data = query.data
    if data == 'bot_ban_list_back':
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=_('⚙ Bot settings'),
                              reply_markup=create_bot_settings_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BOT_SETTINGS
    elif data == 'bot_ban_list_view':
        banned = config.get_banned_users()
        banned = ['@{}'.format(ban) for ban in banned]
        msg = ', '.join(banned)
        msg = 'Banned users: {}'.format(msg)
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_ban_list_keyboard(),
                              parse_mode=ParseMode.MARKDOWN)
        query.answer()
        return ADMIN_BAN_LIST
    elif data == 'bot_ban_list_remove':
        msg = 'Type username: @username or username'
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_BAN_LIST_REMOVE
    elif data == 'bot_ban_list_add':
        msg = 'Type username: @username or username'
        bot.edit_message_text(chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              text=msg,
                              reply_markup=create_back_button(),
                              parse_mode=ParseMode.MARKDOWN)
        return ADMIN_BAN_LIST_ADD

    return ConversationHandler.END


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
                MessageHandler(Filters.text or Filters.location,
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
                # MessageHandler(Filters.text, on_phone_number_text,
                #                pass_user_data=True),
                MessageHandler(Filters.contact, on_phone_number_text),
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
            ADMIN_MENU: [CallbackQueryHandler(
                on_settings_menu, pattern='^settings')],
            ADMIN_STATISTICS: [CallbackQueryHandler(
                on_statistics_menu, pattern='^statistics')],
            ADMIN_BOT_SETTINGS: [CallbackQueryHandler(
                on_bot_settings_menu, pattern='^bot_settings')],
            ADMIN_COURIERS: [
                CallbackQueryHandler(
                    on_admin_couriers, pattern='^bot_couriers')],
            ADMIN_LOCATIONS: [
                CallbackQueryHandler(
                    on_admin_locations, pattern='^bot_locations')],
            ADMIN_CHANNELS: [
                CallbackQueryHandler(on_admin_channels, pattern='^bot_channels')
            ],
            ADMIN_CHANNELS_SELECT_TYPE: [
                CallbackQueryHandler(
                    on_admin_select_channel_type, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_select_channel_type,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_CHANNELS_ADDRESS: [
                MessageHandler(Filters.text, on_admin_add_channel_address,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_CHANNELS_REMOVE: [
                CallbackQueryHandler(
                    on_admin_remove_channel, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_remove_channel,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_BAN_LIST: [
                CallbackQueryHandler(on_admin_ban_list, pattern='^bot_ban_list')
            ],
            ADMIN_BAN_LIST_REMOVE: [
                CallbackQueryHandler(
                    on_admin_remove_ban_list, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_remove_ban_list,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_BAN_LIST_ADD: [
                CallbackQueryHandler(
                    on_admin_add_ban_list, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_add_ban_list,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_EDIT_WORKING_HOURS: [
                CallbackQueryHandler(
                    on_admin_edit_working_hours, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_working_hours,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_EDIT_CONTACT_INFO: [
                CallbackQueryHandler(
                    on_admin_edit_contact_info, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_contact_info,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_BOT_ON_OFF: [
                CallbackQueryHandler(
                    on_admin_bot_on_off, pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel)
            ],
            ADMIN_ORDER_OPTIONS: [
                CallbackQueryHandler(
                    on_admin_order_options, pattern='^bot_order_options')
            ],
            ADMIN_ADD_DISCOUNT: [
                CallbackQueryHandler(
                    on_admin_add_discount, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_add_discount,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_EDIT_IDENTIFICATION: [
                CallbackQueryHandler(
                    on_admin_edit_identification, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_identification,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_EDIT_RESTRICTION: [
                CallbackQueryHandler(
                    on_admin_edit_restriction, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_restriction,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_ADD_DELIVERY_FEE: [
                CallbackQueryHandler(
                    on_admin_add_delivery, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_add_delivery,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_EDIT_WELCOME_MESSAGE: [
                CallbackQueryHandler(
                    on_admin_edit_welcome_message, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_welcome_message,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_EDIT_ORDER_DETAILS: [
                CallbackQueryHandler(
                    on_admin_edit_order_message, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_order_message,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_EDIT_FINAL_MESSAGE: [
                CallbackQueryHandler(
                    on_admin_edit_final_message, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_edit_final_message,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
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
                CallbackQueryHandler(
                    on_admin_txt_product_title, pass_user_data=True),
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
                CallbackQueryHandler(
                    on_admin_txt_delete_product, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_txt_delete_product,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_COURIER_NAME: [
                CallbackQueryHandler(
                    on_admin_txt_courier_name, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_txt_courier_name,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_ADD_LOCATION: [
                CallbackQueryHandler(
                    on_admin_txt_location, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_txt_location,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_DELETE_LOCATION: [
                CallbackQueryHandler(
                    on_admin_txt_delete_location, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_txt_delete_location,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_COURIER_ID: [
                MessageHandler(Filters.text, on_admin_txt_courier_id,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_COURIER_LOCATION: [
                CallbackQueryHandler(
                    on_admin_btn_courier_location, pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
            ADMIN_TXT_DELETE_COURIER: [
                CallbackQueryHandler(
                    on_admin_txt_delete_courier, pass_user_data=True),
                MessageHandler(Filters.text, on_admin_txt_delete_courier,
                               pass_user_data=True),
                CommandHandler('cancel', on_admin_cancel),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', on_cancel, pass_user_data=True),
            CommandHandler('start', on_start, pass_user_data=True)
        ])

    updater = Updater(config.get_api_token())
    updater.dispatcher.add_handler(MessageHandler(
        Filters.status_update, send_welcome_message))
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
