import datetime
from os.path import dirname, abspath
from enum import Enum
from peewee import Model, CharField, IntegerField, SqliteDatabase, \
    ForeignKeyField, DecimalField, BlobField, BooleanField, DateField

d = dirname(dirname(abspath(__file__)))
db = SqliteDatabase(join(d, 'db.sqlite'))


class DeliveryMethod(Enum):
    PICKUP = 1
    DELIVERY = 2


class BaseModel(Model):
    class Meta:
        database = db


class Location(BaseModel):
    title = CharField()


class User(BaseModel):
    username = CharField(null=True)
    telegram_id = IntegerField()
    locale = CharField(max_length=4)
    phone_number = CharField(null=True)

    # def save(self, force_insert=False, only=None):
    #     if self.locale not in (self.HEBREW, self.ENGLISH):
    #         self.locale = self.HEBREW
    #         super().save(force_insert=force_insert, only=only)


class Courier(User):
    location = ForeignKeyField(Location, null=True)


class CourierLocation(BaseModel):
    location = ForeignKeyField(Location)
    courier = ForeignKeyField(Courier)


class Product(BaseModel):
    title = CharField()
    image = BlobField(null=True)
    is_active = BooleanField(default=True)


class ProductCount(BaseModel):
    product = ForeignKeyField(Product, related_name='product_counts')
    count = IntegerField()
    price = DecimalField()


class Order(BaseModel):
    user = ForeignKeyField(User, related_name='user_orders')
    courier = ForeignKeyField(User, related_name='courier_orders', null=True)
    shipping_method = IntegerField(default=DeliveryMethod.PICKUP.value,
                                   choices=DeliveryMethod)
    shipping_time = CharField(null=True)
    location = ForeignKeyField(Location, null=True)
    confirmed = BooleanField(default=False)
    date_created = DateField(default=datetime.datetime.now, null=True)


class OrderItem(BaseModel):
    order = ForeignKeyField(Order, related_name='order_items')
    product = ForeignKeyField(Product, related_name='product_items')
    count = IntegerField(default=1)
    total_price = DecimalField(default=0,
                               verbose_name='total price for each item')


def create_tables():
    db.connect()
    db.create_tables(
        [
            Location, CourierLocation, User, Courier, Product, ProductCount,
            Order, OrderItem
        ], safe=True
    )
