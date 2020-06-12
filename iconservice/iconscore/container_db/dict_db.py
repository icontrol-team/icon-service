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
from typing import Any, Union, TYPE_CHECKING

from iconservice.iconscore.container_db import K, V, DICT_DB_ID
from iconservice.iconscore.container_db.utils import Utils

if TYPE_CHECKING:
    from iconservice.database.db import IconScoreDatabase, IconScoreSubDatabase


class DictDBBase:

    @classmethod
    def get_cls_id(cls) -> bytes:
        return DICT_DB_ID

    def __init__(
            self,
            key: K,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            value_type: type,
            depth: int = 1
    ):
        prefix: bytes = self.create_db_prefix(db, key)
        self._db = db.get_sub_db(prefix)

        self.__value_type = value_type
        self.__depth = depth

    def remove(self, key: K):
        self._remove(key)

    def _remove(self, key: K):
        key: bytes = self.get_encoded_key(key)
        self._db.delete(key)

    def __setitem__(self, key: K, value: V):
        key: bytes = self.get_encoded_key(key)
        value: bytes = Utils.encode_value(value)
        self._db.put(key, value)

    def __getitem__(self, key: K) -> Any:
        key: bytes = self.get_encoded_key(key)
        value: bytes = self._db.get(key)
        return Utils.decode_object(value, self.__value_type)

    def __delitem__(self, key: K):
        self._remove(key)

    def __contains__(self, key: K) -> bool:
        key: bytes = self.get_encoded_key(key)
        value: bytes = self._db.get(key)
        return value is not None

    @property
    def is_leaf(self) -> bool:
        return self.__depth == 1

    @property
    def params(self) -> list:
        return [self._db, self.__value_type, self.__depth - 1]

    @abstractmethod
    def create_db_prefix(
            self,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            key: K
    ) -> bytes:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_encoded_key(cls, key: K) -> bytes:
        raise NotImplementedError()


class DictDBv1(DictDBBase):
    def create_db_prefix(
            self,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            key: K
    ) -> bytes:
        return Utils.create_db_prefix_v1(type(self), key)

    @classmethod
    def get_encoded_key(cls, key: K) -> bytes:
        return Utils.get_encoded_key_v1(key)


class DictDBv2(DictDBBase):
    def create_db_prefix(
            self,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            key: K
    ) -> bytes:
        if db.is_root:
            return Utils.create_db_prefix_v2(type(self), key)
        else:
            return self.get_encoded_key(key)

    @classmethod
    def get_encoded_key(cls, key: K) -> bytes:
        return Utils.get_encoded_key_v2(key)
