from crypt import crypt
from string import ascii_lowercase, ascii_uppercase, digits

from django.db import models

from ara.db.models import MetaDataModel

# Constant from ARAra project.
SALT_SET = "{}{}{}./".format(ascii_lowercase, ascii_uppercase, digits)


class LegacyUser(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "기존 사용자"
        verbose_name_plural = "기존 사용자 목록"

    """
    Model for ARAra DB migration.
    Methods here are exatly same as those in [User] model of ARAra, except for Python version update. (2.7 -> 3.6)
    Website: https://github.com/sparcs-kaist/arara/blob/master/arara/model.py
    """
    username = models.CharField(
        max_length=160,
        verbose_name="아이디",
        db_index=True,
    )
    password = models.CharField(
        max_length=200,
        verbose_name="패스워드",
    )
    nickname = models.CharField(
        max_length=160,
        verbose_name="닉네임",
    )

    @staticmethod
    def encrypt_password(raw_password, salt) -> str:
        """
        @type raw_password: string
        @type salt: string
        """
        pw = crypt(raw_password, salt)
        asc1 = pw[1:2]
        asc2 = pw[3:4]

        # XXX (combacsa): Temporary fix for strange pw values.
        #                 Don't know why "TypeError" occurs.
        i = ord("0") + ord("0")
        try:
            i = ord(asc1) + ord(asc2)
        except TypeError:
            pass
        while True:
            pw = crypt(pw, pw)
            i += 1
            if not (i % 13 != 0):
                break
        return pw

    def compare_password(self, password) -> bool:
        """
        @type password: string
        @rtype: bool
        """
        hash_from_user = self.encrypt_password(password, self.password)
        hash_from_db = self.password
        hash_from_user = smart_unicode(hash_from_user.strip())
        hash_from_db = smart_unicode(hash_from_db.strip())
        return hash_from_user == hash_from_db


def smart_unicode(_str) -> str:
    """
    Util function from ARAra project.
    Website: https://github.com/sparcs-kaist/arara/blob/master/libs/__init__.py
    """
    if isinstance(_str, str):
        return _str
    else:
        try:
            return str(_str, "utf-8")
        except UnicodeDecodeError:
            return str(_str, "cp949")
