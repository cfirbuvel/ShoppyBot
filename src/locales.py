from .helpers import session_client
from telegram.vendor.ptb_urllib3.urllib3.packages.six import wraps


def user_language(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        lang = session_client.json_get(update.message.ch)
        global _
        if lang == b"pt_BR":
            # If language is pt_BR, translates
            _ = lang_pt.gettext
        else:
            # If not, leaves as en_US
            def _(msg): return msg

            result = func(bot, update, *args, **kwargs)
            return result
        return wrapped

@user_language
def unknown(bot, update):
    """
        Placeholder command when the user sends an unknown command.
    """
    msg = _("Sorry, I don't know what you're asking for.")
    bot.send_message(chat_id=update.message.chat_id,
                     text=msg)



elif data == 'bot_settings_lng_en':

profile = User.get(telegram_id=update.user.telegram_id)
profile.locale = "he"
profile.save()

profile = User.get(telegram_id=update.user.telegram_id)
profile.locale = "en"
profile.save()
bot.edit_message_text(chat_id=query.message.chat_id,
                      message_id=query.message.message_id,
                      text='Languages',
                      reply_markup=create_bot_language_keyboard(),
                      parse_mode=ParseMode.MARKDOWN)
query.answer()
return ADMIN_MENU

media = []
if 'photo_id' in user_data['shipping']:
    # send_products to current chat
    product = Product.get():
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
image_data = Product.get()
image_stream = io.BytesIO(image_data)
media.append(InputMediaPhoto(user_data['shipping']['photo_id']))

if 'stage2_id' in user_data['shipping']:
    media.append(InputMediaPhoto(user_data['shipping']['stage2_id']))

if 'location' in user_data['shipping']:
    bot.send_location(
        config.get_service_channel(),
        location=user_data['shipping']['location']
    )
    if media:
        bot.send_photo(query.message.chat_id,
                       photo=image_stream)
        bot.send_media_group(config.get_service_channel(),
                             media=media
                             )

if media:
    bot.send_photo(query.message.chat_id,
                   photo=image_stream)
    bot.send_media_group(config.get_service_channel(),
                         media=media
                         )
