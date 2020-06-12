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
from typing import TYPE_CHECKING, Optional

from iconservice.base.exception import InvalidParamsException
from iconservice.iconscore.container_db import K, V, VAR_DB_ID
from iconservice.iconscore.container_db.utils import Utils

if TYPE_CHECKING:
    from iconservice.database.db import IconScoreDatabase


class VarDBBase:
    @classmethod
    def get_cls_id(cls) -> bytes:
        raise InvalidParamsException(f'Unsupported container class: {VarDBBase}')

    def __init__(
            self,
            key: K,
            db: 'IconScoreDatabase',
            value_type: type
    ):
        # Use var_key as a db prefix in the case of VarDB
        self._db = db.get_sub_db(VAR_DB_ID)
        self.__key = self.get_encoded_key(key)
        self.__value_type = value_type

    def set(self, value: V):
        value: bytes = Utils.encode_value(value)
        self._db.put(self.__key, value)

    def get(self) -> Optional[V]:
        value: bytes = self._db.get(self.__key)
        return Utils.decode_object(value, self.__value_type)

    def remove(self):
        self._db.delete(self.__key)

    @classmethod
    @abstractmethod
    def get_encoded_key(cls, key: K) -> bytes:
        raise NotImplementedError()


class VarDBv1(VarDBBase):
    @classmethod
    def get_encoded_key(cls, key: K) -> bytes:
        return Utils.get_encoded_key_v1(key)


class VarDBv2(VarDBBase):
    @classmethod
    def get_encoded_key(cls, key: K) -> bytes:
        return Utils.get_encoded_key_v2(key)
