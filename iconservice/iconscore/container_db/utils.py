from typing import Optional, Any, Union, TYPE_CHECKING

from . import V, K
from ...base.address import Address
from ...base.exception import InvalidParamsException
from ...utils import int_to_bytes, bytes_to_int

if TYPE_CHECKING:
    from ...database.db import IconScoreDatabase, IconScoreSubDatabase


class Utils:
    @classmethod
    def get_container_id(cls, container_cls: type) -> bytes:
        return container_cls.get_cls_id()

    @classmethod
    def create_db_prefix_v1(cls, container_cls: type, var_key: K) -> bytes:
        """Create a prefix used
        as a parameter of IconScoreDatabase.get_sub_db()

        :param container_cls: ArrayDB, DictDB, VarDB
        :param var_key:
        :return:
        """
        container_id: bytes = cls.get_container_id(container_cls)
        encoded_key: bytes = cls.get_encoded_key_v1(var_key)
        return b'|'.join([container_id, encoded_key])

    @classmethod
    def create_db_prefix_v2(cls, container_cls: type, var_key: K) -> bytes:
        """Create a prefix used
        as a parameter of IconScoreDatabase.get_sub_db()

        :param container_cls: ArrayDB, DictDB, VarDB
        :param var_key:
        :return:
        """
        container_id: bytes = cls.get_container_id(container_cls)
        encoded_key: bytes = cls.get_encoded_key_v2(var_key)
        return b''.join([container_id, encoded_key])

    @classmethod
    def encode_key(cls, key: K) -> bytes:
        """Create a key passed to DB

        :param key:
        :return:
        """
        if key is None:
            raise InvalidParamsException('key is None')

        if isinstance(key, int):
            bytes_key = int_to_bytes(key)
        elif isinstance(key, str):
            bytes_key = key.encode('utf-8')
        elif isinstance(key, Address):
            bytes_key = key.to_bytes()
        elif isinstance(key, bytes):
            bytes_key = key
        else:
            raise InvalidParamsException(f'Unsupported key type: {type(key)}')
        return bytes_key

    @classmethod
    def encode_value(cls, value: V) -> bytes:
        if isinstance(value, int):
            byte_value = int_to_bytes(value)
        elif isinstance(value, str):
            byte_value = value.encode('utf-8')
        elif isinstance(value, Address):
            byte_value = value.to_bytes()
        elif isinstance(value, bool):
            byte_value = int_to_bytes(int(value))
        elif isinstance(value, bytes):
            byte_value = value
        else:
            raise InvalidParamsException(f'Unsupported value type: {type(value)}')
        return byte_value

    @classmethod
    def decode_object(cls, value: bytes, value_type: type) -> Optional[Union[K, V]]:
        if value is None:
            return cls.get_default_value(value_type)

        obj_value = None
        if value_type == int:
            obj_value = bytes_to_int(value)
        elif value_type == str:
            obj_value = value.decode()
        elif value_type == Address:
            obj_value = Address.from_bytes(value)
        if value_type == bool:
            obj_value = bool(bytes_to_int(value))
        elif value_type == bytes:
            obj_value = value
        return obj_value

    @classmethod
    def get_encoded_key_v2(cls, key: V) -> bytes:
        bytes_key = Utils.encode_key(key)
        return cls.rlp_encode_bytes(bytes_key)

    @classmethod
    def get_encoded_key_v1(cls, key: V) -> bytes:
        return Utils.encode_key(key)

    @classmethod
    def get_default_value(cls, value_type: type) -> Any:
        if value_type == int:
            return 0
        elif value_type == str:
            return ""
        elif value_type == bool:
            return False
        return None

    @classmethod
    def rlp_encode_bytes(cls, b: bytes) -> bytes:
        blen = len(b)
        if blen == 1 and b[0] < 0x80:
            return b
        elif blen <= 55:
            return bytes([blen + 0x80]) + b
        len_bytes = cls.rlp_get_bytes(blen)
        return bytes([len(len_bytes) + 0x80 + 55]) + len_bytes + b

    @classmethod
    def rlp_get_bytes(cls, x: int) -> bytes:
        if x == 0:
            return b''
        else:
            return cls.rlp_get_bytes(int(x / 256)) + bytes([x % 256])

    @classmethod
    def remove_prefix_from_iters(cls, iter_items: iter) -> iter:
        return ((cls.__remove_prefix_from_key(key), value) for key, value in iter_items)

    @classmethod
    def __remove_prefix_from_key(cls, key_from_bytes: bytes) -> bytes:
        return key_from_bytes[:-1]

    @classmethod
    def put_to_db(
            cls,
            db: 'IconScoreDatabase',
            db_key: str,
            container: iter
    ):
        sub_db = db.get_sub_db(cls.encode_key(db_key))
        if isinstance(container, dict):
            cls.__put_to_db_internal(sub_db, container.items())
        elif isinstance(container, (list, set, tuple)):
            cls.__put_to_db_internal(sub_db, enumerate(container))

    @classmethod
    def get_from_db(
            cls,
            db: 'IconScoreDatabase',
            db_key: str,
            *args,
            value_type: type
    ) -> Optional[K]:
        sub_db = db.get_sub_db(cls.encode_key(db_key))
        *args, last_arg = args
        for arg in args:
            sub_db = sub_db.get_sub_db(cls.encode_key(arg))

        byte_key = sub_db.get(cls.encode_key(last_arg))
        if byte_key is None:
            return cls.get_default_value(value_type)
        return cls.decode_object(byte_key, value_type)

    @classmethod
    def __put_to_db_internal(
            cls,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            iters: iter
    ):
        for key, value in iters:
            sub_db = db.get_sub_db(cls.encode_key(key))
            if isinstance(value, dict):
                cls.__put_to_db_internal(sub_db, value.items())
            elif isinstance(value, (list, set, tuple)):
                cls.__put_to_db_internal(sub_db, enumerate(value))
            else:
                db_key = cls.encode_key(key)
                db_value = cls.encode_value(value)
                db.put(db_key, db_value)
