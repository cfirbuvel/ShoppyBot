import gettext
import os

DEBUG = os.environ.get('DEBUG')
cat = gettext.GNUTranslations(open('he.mo', 'rb'))

_ = gettext.gettext
if not DEBUG:
    _ = cat.gettext

(BOT_STATE_INIT,
 BOT_STATE_CHECKOUT_SHIPPING,
 BOT_STATE_CHECKOUT_LOCATION,
 BOT_STATE_CHECKOUT_LOCATION_PICKUP,
 BOT_STATE_CHECKOUT_LOCATION_DELIVERY,
 BOT_STATE_CHECKOUT_TIME,
 BOT_STATE_CHECKOUT_PHONE_NUMBER_TEXT,
 BOT_STATE_CHECKOUT_TIME_TEXT,
 BOT_STATE_CHECKOUT_IDENTIFY_STAGE1,
 BOT_STATE_CHECKOUT_IDENTIFY_STAGE2,
 BOT_STATE_ORDER_CONFIRMATION,

 ADMIN_INIT,
 ADMIN_TXT_PRODUCT_TITLE,
 ADMIN_TXT_PRODUCT_PRICES,
 ADMIN_TXT_PRODUCT_PHOTO,
 ADMIN_TXT_DELETE_PRODUCT,
 ADMIN_TXT_COURIER_NAME,
 ADMIN_TXT_COURIER_ID,
 ADMIN_TXT_COURIER_LOCATION,
 ADMIN_TXT_DELETE_COURIER,
 ADMIN_MENU,
 ADMIN_STATISTICS,
 ADMIN_COURIERS,
 ADMIN_CHANNELS,
 ADMIN_CHANNELS_SELECT_TYPE,
 ADMIN_CHANNELS_ADDRESS,
 ADMIN_CHANNELS_REMOVE,
 ADMIN_EDIT_WORKING_HOURS,
 ADMIN_EDIT_CONTACT_INFO,
 ADMIN_BOT_ON_OFF,
 ADMIN_BOT_SETTINGS,
 ADMIN_RESET_OPTIONS,
 ADMIN_ORDER_OPTIONS,
 ADMIN_ADD_DISCOUNT,
 ADMIN_ADD_DELIVERY_FEE,
 ADMIN_EDIT_WELCOME_MESSAGE,
 ADMIN_EDIT_ORDER_DETAILS,
 ADMIN_EDIT_FINAL_MESSAGE,
 ADMIN_EDIT_IDENTIFICATION,
 ADMIN_EDIT_RESTRICTION,
 ADMIN_BAN_LIST,
 ADMIN_BAN_LIST_VIEW,
 ADMIN_BAN_LIST_REMOVE,
 ADMIN_BAN_LIST_ADD,
 ADMIN_SET_WELCOME_MESSAGE) = range(45)

BUTTON_TEXT_PICKUP      = _('🏪 Pickup')
BUTTON_TEXT_DELIVERY    = _('🚚 Delivery')
BUTTON_TEXT_NOW         = _('⏰ Now')
BUTTON_TEXT_SETTIME     = _('📅 Set time')
BUTTON_TEXT_BACK        = _('↩ Back')
BUTTON_TEXT_CONFIRM     = _('✅ Confirm')
BUTTON_TEXT_CANCEL      = _('❌ Cancel')
