from os.path import dirname, abspath
from enum import Enum
from peewee import Model, CharField, IntegerField, SqliteDatabase, \
    ForeignKeyField, DecimalField, BlobField, BooleanField

d = dirname(dirname(abspath(__file__)))
db = SqliteDatabase(d + '/db.sqlite')


# TODO fill example database with new data


class DeliveryMethod(Enum):
    PICKUP = 1
    DELIVERY = 2


class BaseModel(Model):
    class Meta:
        database = db


class Location(BaseModel):
    title = CharField()


class User(BaseModel):
    username = CharField()
    telegram_id = IntegerField()
    phone_number = CharField(null=True)


class Courier(User):
    location = ForeignKeyField(Location, null=True)


class Product(BaseModel):
    title = CharField()
    image = BlobField(null=True)


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


class OrderItem(BaseModel):
    order = ForeignKeyField(Order, related_name='order_items')
    product = ForeignKeyField(Product, related_name='product_items')
    count = IntegerField(default=1)
    total_price = DecimalField(default=0)


def create_tables():
    db.connect()
    db.create_tables([
        Location, User, Courier, Product, ProductCount, Order, OrderItem],
        safe=True
    )
