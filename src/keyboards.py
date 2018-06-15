import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardMarkup
from .enums import *
from .enums import _


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


def create_phone_number_request_keyboard():
    buttons = [
        [KeyboardButton(
            text=_('Allow to send my phone number'),
            request_contact=True
        )],
        [KeyboardButton(BUTTON_TEXT_BACK)],
        [KeyboardButton(BUTTON_TEXT_CANCEL)],
    ]

    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True)


def create_cancel_keyboard():
    button_row = [
        [
            KeyboardButton(BUTTON_TEXT_BACK),
            KeyboardButton(BUTTON_TEXT_CANCEL)
        ],
    ]
    return ReplyKeyboardMarkup(button_row, resize_keyboard=True)


def create_locations_keyboard(location_names):
    button_row = []
    for location_name in location_names:
        button_row.append([InlineKeyboardButton(_(location_name),
                          callback_data=location_name)])
    back_button = InlineKeyboardButton(_(BUTTON_TEXT_BACK),
                                       callback_data='back')
    cancel_button = InlineKeyboardButton(_(BUTTON_TEXT_CANCEL),
                                         callback_data='back')
    button_row.append([back_button, cancel_button])
    return InlineKeyboardMarkup(button_row)


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


def create_confirmation_inline_keyboard():
    buttons = [
        InlineKeyboardButton(_('Yes'),
                             callback_data='yes'),
        InlineKeyboardButton(_('No'),
                             callback_data='no'),
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


def create_main_keyboard(review_channel, is_admin=None, total_price=0):
    main_button_list = [
        [InlineKeyboardButton(_('🏪 Our products'),
                              callback_data='menu_products')],
        [InlineKeyboardButton(_('🛍 Checkout {}').format(total_price),
                              callback_data='menu_order')],
        [InlineKeyboardButton(_('⭐ Reviews'), url=review_channel)],
        [InlineKeyboardButton(_('⏰ Working hours'),
                              callback_data='menu_hours')],
        [InlineKeyboardButton(_('☎ Contact info'),
                              callback_data='menu_contact')],
    ]
    if is_admin:
        main_button_list.append(
            [InlineKeyboardButton(_('⚙️ Settings'),
                                  callback_data='menu_settings')])
    return InlineKeyboardMarkup(main_button_list)


<<<<<<< HEAD
def create_bot_language_keyboard():
    keyboard = [
        [InlineKeyboardButton(
            _("Hebrew"), callback_data='lng_he')],
        [InlineKeyboardButton(
            _("English"), callback_data='lng_en')]
    ]
    return InlineKeyboardMarkup(keyboard, resize_keyboard=True)


=======
>>>>>>> f6538122448b694bf81e63a4b0db0fc00c966ff9
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


def create_admin_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('📈 Statistics'),
                              callback_data='settings_statistics')],
        [InlineKeyboardButton(_('⚙ Bot settings'),
                              callback_data='settings_bot')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='settings_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_statistics_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('💵 Get statistics by all sells'),
                              callback_data='statistics_all_sells')],
        [InlineKeyboardButton(_('🛵 Get statistics by different couriers'),
                              callback_data='statistics_couriers')],
        [InlineKeyboardButton(_('🏠 Get statistics by locations'),
                              callback_data='statistics_locations')],
        [InlineKeyboardButton(_('🌕 Get statistics yearly'),
                              callback_data='statistics_yearly')],
        [InlineKeyboardButton(_('🌛 Get statistics monthly'),
                              callback_data='statistics_monthly')],
        [InlineKeyboardButton(_('🌝 Get statistics by user'),
                              callback_data='statistics_user')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='statistics_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_bot_settings_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('🛵 Couriers'),
                              callback_data='bot_settings_couriers')],
        [InlineKeyboardButton(_('✉️ Channels'),
                              callback_data='bot_settings_channels')],
        [InlineKeyboardButton(_('⏰ Edit working hours'),
                              callback_data='bot_settings_edit_working_hours')],
        [InlineKeyboardButton(_('💳 Order options'),
                              callback_data='bot_settings_order_options')],
        [InlineKeyboardButton(_('🔥 Client ban-list'),
                              callback_data='bot_settings_ban_list')],
        [InlineKeyboardButton(_('☎️ Edit contact info'),
                              callback_data='bot_settings_edit_contact_info')],
        [InlineKeyboardButton(_('⚡️ Bot ON/OFF'),
                              callback_data='bot_settings_bot_on_off')],
        [InlineKeyboardButton(_('💫 Reset all data'),
                              callback_data='bot_settings_reset_all_data')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='bot_settings_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_bot_couriers_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('🛵 View couriers'),
                              callback_data='bot_couriers_view')],
        [InlineKeyboardButton(_('➕ Add couriers'),
                              callback_data='bot_couriers_add')],
        [InlineKeyboardButton(_('➖ Remove couriers'),
                              callback_data='bot_couriers_delete')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='bot_couriers_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_bot_channels_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('✉️ View channels'),
                              callback_data='bot_channels_view')],
        [InlineKeyboardButton(_('➕ Add channel'),
                              callback_data='bot_channels_add')],
        [InlineKeyboardButton(_('➖ Remove channel'),
                              callback_data='bot_channels_remove')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='bot_channels_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_bot_locations_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('🎯️ View locations'),
                              callback_data='bot_locations_view')],
        [InlineKeyboardButton(_('➕ Add location'),
                              callback_data='bot_locations_add')],
        [InlineKeyboardButton(_('➖ Remove location'),
                              callback_data='bot_locations_delete')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='bot_locations_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_bot_order_options_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('➕️ Add new product'),
                              callback_data='bot_order_options_product')],
        [InlineKeyboardButton(_('➖️ Delete product'),
                              callback_data='bot_order_options_delete_product')],
        [InlineKeyboardButton(_('➕ Add discount'),
                              callback_data='bot_order_options_discount')],
        [InlineKeyboardButton(_('➕ Add delivery fee'),
                              callback_data='bot_order_options_delivery_fee')],
        [InlineKeyboardButton(_('🎯 locations'),
                              callback_data='bot_order_options_add_locations')],
        [InlineKeyboardButton(_('👨‍ Edit identify process'),
                              callback_data='bot_order_options_identify')],
        [InlineKeyboardButton(_('🔥 Edit Restricted area'),
                              callback_data='bot_order_options_restricted')],
        [InlineKeyboardButton(_('✉ Edit Welcome message'),
                              callback_data='bot_order_options_welcome')],
        [InlineKeyboardButton(_('✉ Edit Order details message'),
                              callback_data='bot_order_options_details')],
        [InlineKeyboardButton(_('✉ Edit Final message'),
                              callback_data='bot_order_options_final')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='bot_order_options_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(BUTTON_TEXT_CANCEL, callback_data='back')]
    ])


def create_on_off_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('ON', callback_data='on')],
        [InlineKeyboardButton('OFF', callback_data='off')],
        [InlineKeyboardButton(BUTTON_TEXT_CANCEL, callback_data='back')],
    ])


def create_ban_list_keyboard():
    main_button_list = [
        [InlineKeyboardButton(_('🔥 View ban list'),
                              callback_data='bot_ban_list_view')],
        [InlineKeyboardButton(_('➖ Remove from ban list'),
                              callback_data='bot_ban_list_remove')],
        [InlineKeyboardButton(_('➕ Add to ban list'),
                              callback_data='bot_ban_list_add')],
        [InlineKeyboardButton(_('↩ Back'),
                              callback_data='bot_ban_list_back')],
    ]

    return InlineKeyboardMarkup(main_button_list)


def create_service_channel_keyboard(order_id, show_order, is_vip):
    if show_order:
        main_button_list = [
            [InlineKeyboardButton(_('🛵 Send order to courier channel'),
                                  callback_data='admin_send_order_to_courier_channel')],
            [InlineKeyboardButton(_('🚀 Send order to specific courier'),
                                  callback_data='admin_send_order_to_courier')],
            [InlineKeyboardButton(_('🚕 Send order yourself'),
                                  callback_data='admin_send_order_to_self')],
            [InlineKeyboardButton(_('⭐ Add user to VIP {}').format(is_vip),
                                  callback_data='admin_add_client_to_vip')],
            [InlineKeyboardButton(_('🔥 Add client to ban-list'),
                                  callback_data='admin_add_client_to_ban_list')],
            [InlineKeyboardButton(_('💳 Hide Order №{}').format(order_id),
                                  callback_data='admin_hide_order')],
            [InlineKeyboardButton(_('✅ Order Finished'),
                                  callback_data='admin_mark_order_finished')],
        ]
        return InlineKeyboardMarkup(main_button_list)
    else:
        return InlineKeyboardMarkup([[InlineKeyboardButton(_('Show Order №{}').format(order_id),
                                                           callback_data='admin_show_order')]])


def create_courier_locations_keyboard(locations):
    main_button_list = []
    for location_name, location_id, is_picked in locations:
        if is_picked:
            is_picked = '➖'
        else:
            is_picked = '➕'

        location_callback = location_id
        location_name = '{} {}'.format(is_picked, location_name)
        main_button_list.append(
            [
                InlineKeyboardButton(
                    location_name,
                    callback_data=location_callback)
            ]
        )
    main_button_list.append(
        [
            InlineKeyboardButton(
                _('Done'),
                callback_data='location_end')
        ]
    )

    return InlineKeyboardMarkup(main_button_list)
