# -*- coding: utf-8 -*-

# Copyright 2018 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import abstractmethod
from typing import Union, TYPE_CHECKING, Optional

from iconservice.base.exception import InvalidParamsException
from iconservice.iconscore.container_db import K, V, ARRAY_DB_ID
from iconservice.iconscore.container_db.utils import Utils

if TYPE_CHECKING:
    from iconservice.database.db import IconScoreDatabase, IconScoreSubDatabase


class ArrayDBBase:
    @classmethod
    def get_cls_id(cls) -> bytes:
        return ARRAY_DB_ID

    def __init__(
            self,
            key: K,
            db: 'IconScoreDatabase',
            value_type: type
    ):
        prefix: bytes = self.create_db_prefix(key)
        self._db = db.get_sub_db(prefix)

        self.__value_type = value_type
        self.__size = self.__get_size_from_db()

    def put(self, value: V):
        size: int = self.__size
        self.__put(size, value)
        self.__set_size(size + 1)

    def pop(self) -> Optional[V]:
        size: int = self.__size
        if size == 0:
            return None

        index = size - 1
        last_val = self[index]

        key: bytes = self.get_encoded_key(index)
        self._db.delete(key)
        self.__set_size(index)
        return last_val

    def __get_size_from_db(self) -> int:
        key: bytes = self.get_size_key()
        value: bytes = self._db.get(key)
        return Utils.decode_object(value, int)

    def __set_size(self, size: int):
        self.__size: int = size
        key: bytes = self.get_size_key()
        value: bytes = Utils.encode_value(size)
        self._db.put(key, value)

    def __put(self, index: int, value: V):
        key: bytes = self.get_encoded_key(index)
        value = Utils.encode_value(value)
        self._db.put(key, value)

    def __iter__(self):
        return self._get_generator(self._db, self.__size, self.__value_type)

    def __len__(self):
        return self.__size

    def __setitem__(self, index: int, value: V):
        size: int = self.__size

        # Negative index means that you count from the right instead of the left.
        if index < 0:
            index += size

        if 0 <= index < size:
            self.__put(index, value)
        else:
            raise InvalidParamsException('ArrayDB out of index')

    def __getitem__(self, index: int) -> V:
        return self._get(self._db, self.__size, index, self.__value_type)

    def __contains__(self, item: V):
        for e in self:
            if e == item:
                return True
        return False

    @classmethod
    def _get(
            cls,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            size: int,
            index: int,
            value_type: type
    ) -> V:
        if not isinstance(index, int):
            raise InvalidParamsException('Invalid index type: not an integer')

        # Negative index means that you count from the right instead of the left.
        if index < 0:
            index += size

        if 0 <= index < size:
            key: bytes = cls.get_encoded_key(index)
            value: bytes = db.get(key)
            return Utils.decode_object(value, value_type)
        raise InvalidParamsException('ArrayDB out of index')

    @classmethod
    def _get_generator(
            cls,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            size: int,
            value_type: type
    ):
        for index in range(size):
            yield cls._get(db, size, index, value_type)

    @abstractmethod
    def create_db_prefix(
            self,
            key: K
    ) -> bytes:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_encoded_key(cls, key: K) -> bytes:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_size_key(cls) -> bytes:
        raise NotImplementedError()


class ArrayDBv1(ArrayDBBase):
    def create_db_prefix(
            self,
            key: K
    ) -> bytes:
        return Utils.create_db_prefix_v1(type(self), key)

    @classmethod
    def get_encoded_key(cls, key: K) -> bytes:
        return Utils.get_encoded_key_v1(key)

    @classmethod
    def get_size_key(cls) -> bytes:
        return cls.get_encoded_key("size")


class ArrayDBv2(ArrayDBBase):
    def create_db_prefix(
            self,
            key: K
    ) -> bytes:
        return Utils.create_db_prefix_v2(type(self), key)

    @classmethod
    def get_encoded_key(cls, key: K) -> bytes:
        return Utils.get_encoded_key_v2(key)

    @classmethod
    def get_size_key(cls) -> bytes:
        return b''
