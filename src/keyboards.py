import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup
from .enums import *
from .helpers import get_username, get_user_id

DEBUG = os.environ.get('DEBUG')
cat = gettext.GNUTranslations(open('he.mo', 'rb'))

_ = gettext.gettext
if not DEBUG:
    _ = cat.gettext


def create_time_keyboard():
    button_row = [
        [
            KeyboardButton(BUTTON_TEXT_NOW)
        ],
        [
            KeyboardButton(BUTTON_TEXT_SETTIME)
        ],
        [
            KeyboardButton(BUTTON_TEXT_BACK),
            KeyboardButton(BUTTON_TEXT_CANCEL)
        ],
    ]
    return ReplyKeyboardMarkup(button_row, resize_keyboard=True)


def create_confirmation_keyboard():
    button_row = [
        [KeyboardButton(BUTTON_TEXT_CONFIRM)],
        [
            KeyboardButton(BUTTON_TEXT_BACK),
            KeyboardButton(BUTTON_TEXT_CANCEL)
        ]
    ]
    return ReplyKeyboardMarkup(button_row, resize_keyboard=True)


def create_cancel_keyboard():
    button_row = [
        [
            KeyboardButton(BUTTON_TEXT_BACK),
            KeyboardButton(BUTTON_TEXT_CANCEL)
        ],
    ]
    return ReplyKeyboardMarkup(button_row, resize_keyboard=True)


def create_pickup_location_keyboard(location_names):
    button_column = []
    for location_name in location_names:
        button_column.append([KeyboardButton(location_name)])

    button_column.append(
        [
            KeyboardButton(BUTTON_TEXT_BACK),
            KeyboardButton(BUTTON_TEXT_CANCEL)
        ])
    return ReplyKeyboardMarkup(button_column, resize_keyboard=True)


def create_shipping_keyboard():
    button_row = [
        [KeyboardButton(BUTTON_TEXT_PICKUP)],
        [KeyboardButton(BUTTON_TEXT_DELIVERY)],
        [KeyboardButton(BUTTON_TEXT_CANCEL)],
    ]
    return ReplyKeyboardMarkup(button_row, resize_keyboard=True)


def create_service_notice_keyboard(update, user_id, order_id):
    buttons = [
        [
            InlineKeyboardButton(
                _('Take Responsibility'),
                callback_data='courier|{}|{}'.format(user_id, order_id))
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def create_courier_confirmation_keyboard(order_id, courier_name):
    buttons = [
        InlineKeyboardButton(_('Yes'),
                             callback_data='confirmed|{}|{}'.format(
                                 order_id, courier_name)),
        InlineKeyboardButton(_('No'),
                             callback_data='notconfirmed|{}|{}'.format(
                                 order_id, courier_name)),
    ]
    return InlineKeyboardMarkup([buttons])


def create_drop_responsibility_keyboard(user_id, courier_nickname, order_id):
    buttons = [
        [InlineKeyboardButton(_('Assigned to @{}').format(courier_nickname),
                              url='https://t.me/{}'.format(courier_nickname))],
        [InlineKeyboardButton(_('Drop responsibility'),
                              callback_data='dropped|{}'.format(order_id))],
    ]
    return InlineKeyboardMarkup(buttons)


def create_main_keyboard(review_channel, is_admin):
    main_button_list = [
        [InlineKeyboardButton(_('🏪 Our products'),
                              callback_data='menu_products')],
        [InlineKeyboardButton(_('🛍 Checkout'),
                              callback_data='menu_order')],
        [InlineKeyboardButton(_('⭐ Reviews'), url=review_channel)],
        [InlineKeyboardButton(_('⏰ Working hours'),
                              callback_data='menu_hours')],
        [InlineKeyboardButton(_('☎ Contact info'),
                              callback_data='menu_contact')],
    ]
    # if is_admin:
    #     main_button_list.append(
    #         [InlineKeyboardButton(_('☎ Settings'),
    #                               callback_data='settings')])
    return InlineKeyboardMarkup(main_button_list)


def create_product_keyboard(product_id, user_data, cart):
    button_row = []

    if cart.get_product_count(user_data, product_id) > 0:
        button = InlineKeyboardButton(
            _('➕ Add more'), callback_data='product_add|{}'.format(product_id))
        button_row.append(button)
    else:
        button = InlineKeyboardButton(
            _('🛍 Add to cart'),
            callback_data='product_add|{}'.format(product_id))
        button_row.append(button)

    if cart.get_product_count(user_data, product_id) > 0:
        button = InlineKeyboardButton(
            _('➖ Remove'), callback_data='product_remove|{}'.format(product_id))
        button_row.append(button)

    return InlineKeyboardMarkup([button_row])


def create_bot_config_keyboard(session):
    button_row = [
        [InlineKeyboardButton(
            _('Set welcome message'),
            callback_data='setwelcomemessage'
        )],
    ]
    return InlineKeyboardMarkup(button_row, resize_keyboard=True)


# def admin_create_bot_config_keyboard():
#     button_row = [
#         [InlineKeyboardButton(_('Set welcome message'), callback_data='setwelcomemessage')],
#         [InlineKeyboardButton(_('Add courier'), callback_data='setwelcomemessage')],
#         [InlineKeyboardButton(_('Delete courier'), callback_data='setwelcomemessage')],
#         [InlineKeyboardButton(_('Turn ON/OFF bot'), callback_data='turnonoff')],
#         [InlineKeyboardButton(_('Back'), callback_data='goback')],
#     ]
#     return InlineKeyboardMarkup(button_row)
