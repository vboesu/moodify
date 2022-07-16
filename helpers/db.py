import datetime
from peewee import *

from .palettes import Color

db = SqliteDatabase("moodify.db", pragmas={"foreign_keys": 1})


class Base(Model):
    class Meta:
        database = db


class User(Base):
    user_id = AutoField()
    email = CharField(unique=True)
    password = CharField()
    created = DateTimeField(default=datetime.datetime.now)

    class Meta:
        table_name = "users"


class SavedPalette(Base):
    palette_id = AutoField()
    user_id = ForeignKeyField(
        User, backref="saved_palettes", on_delete="CASCADE", on_update="CASCADE"
    )
    created = DateTimeField(default=datetime.datetime.now)

    @property
    def colors(self):
        return [
            c
            for c in SavedPaletteColor.select().where(
                SavedPaletteColor.palette_id == self.palette_id
            )
        ]

    @property
    def to_dict(self):
        return {
            "id": self.palette_id,
            "colors": [
                {"hex": c.hex, "lightness": c.color.lightness} for c in self.colors
            ],
            "created": self.created,
        }

    class Meta:
        table_name = "saved_palettes"


class SavedColor(Base):
    color_id = AutoField()
    user_id = ForeignKeyField(
        User, backref="saved_colors", on_delete="CASCADE", on_update="CASCADE"
    )
    hex = CharField()
    created = DateTimeField(default=datetime.datetime.now)

    @property
    def color(self):
        return Color(self.hex)

    @property
    def to_dict(self):
        return {
            "id": self.color_id,
            "hex": self.hex,
            "lightness": self.color.lightness,
            "created": self.created,
        }

    class Meta:
        table_name = "saved_colors"


class SavedPaletteColor(Base):
    color_id = AutoField()
    palette = ForeignKeyField(
        SavedPalette,
        backref="saved_palettes_colors",
        on_delete="CASCADE",
        on_update="CASCADE",
    )
    hex = CharField()

    @property
    def color(self):
        return Color(self.hex)

    class Meta:
        table_name = "saved_palettes_colors"


def get_user(user_id=None, email=None):
    if not any([user_id, email]):
        raise ValueError("either user_id or email must be not None")

    if user_id:
        return User.get_or_none(User.user_id == user_id)
    elif email:
        return User.get_or_none(User.email == email)


db.connect()
db.create_tables([User, SavedPalette, SavedColor, SavedPaletteColor])