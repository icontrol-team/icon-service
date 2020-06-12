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
from typing import TYPE_CHECKING, Optional, Union

from ...base.exception import InvalidParamsException, AccessDeniedException
from ...icon_constant import Revision
from ...iconscore.context.context import ContextGetter

if TYPE_CHECKING:
    from ...base.address import Address
    from ..db import DatabaseObserver, ContextDatabase, IconScoreDatabase, IconScoreSubDatabase


class ScoreDBBase(ContextGetter):
    def __init__(
            self,
            address: 'Address',
            context_db: 'ContextDatabase'
    ):
        self.address = address
        self._context_db = context_db
        self._observer: Optional['DatabaseObserver'] = None
        self._prefix: bytes = address.to_bytes()

    @property
    def is_root(self) -> bool:
        return True

    @property
    def is_v2(self) -> bool:
        return self._revision >= Revision.CONTAINER_DB_RLP.value

    @property
    def _revision(self) -> int:
        if self._context.is_revision_changed(Revision.CONTAINER_DB_RLP.value):
            return self._context.revision - 1
        else:
            return self._context.revision

    def get(self, key: bytes) -> bytes:
        """
        Gets the value for the specified key

        :param key: key to retrieve
        :return: value for the specified key, or None if not found
        """
        hashed_key: bytes = self._hash_key(key)
        value: Optional[bytes] = self._context_db.get(self._context, hashed_key)

        if self._observer:
            self._observer.on_get(self._context, key, value)
        return value

    def put(self, key: bytes, value: bytes):
        """
        Sets a value for the specified key.

        :param key: key to set
        :param value: value to set
        """

        self._validate_ownership()
        hashed_key: bytes = self._hash_key(key)

        if self._observer:
            old_value = self._context_db.get(self._context, hashed_key)
            if value:
                self._observer.on_put(self._context, key, old_value, value)
            elif old_value:
                # If new value is None, then deletes the field
                self._observer.on_delete(self._context, key, old_value)
        self._context_db.put(self._context, hashed_key, value)

    def delete(self, key: bytes):
        """
        Deletes the key/value pair for the specified key.

        :param key: key to delete
        """
        self._validate_ownership()
        hashed_key: bytes = self._hash_key(key)

        if self._observer:
            old_value = self._context_db.get(self._context, hashed_key)
            # If old value is None, won't fire the callback
            if old_value:
                self._observer.on_delete(self._context, key, old_value)
        self._context_db.delete(self._context, hashed_key)

    def close(self):
        self._context_db.close(self._context)

    def set_observer(self, observer: 'DatabaseObserver'):
        self._observer = observer

    def _validate_ownership(self):
        """Prevent a SCORE from accessing the database of another SCORE
        """
        if self._context.current_address != self.address:
            raise AccessDeniedException(f"Invalid database ownership: {self._context.current_address}, {self.address}")

    @abstractmethod
    def _hash_key(self, key: bytes) -> bytes:
        pass


class ScoreDBv1(ScoreDBBase):
    def _hash_key(self, key: bytes) -> bytes:
        """All key is hashed and stored
        to StateDB to avoid key conflicts among SCOREs

        :params key: key passed by SCORE
        :return: key bytes
        """
        return b'|'.join((self._prefix, key))


class ScoreDBv2(ScoreDBBase):
    def _hash_key(self, key: bytes) -> bytes:
        return b''.join((self._prefix, key))


class ScoreSubDBBase:
    def __init__(
            self,
            address: 'Address',
            score_db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            prefix: bytes
    ):

        if prefix is None:
            raise InvalidParamsException("Invalid prefix")

        self.address: 'Address' = address
        self._score_db: Union['IconScoreDatabase', 'IconScoreSubDatabase'] = score_db
        self._prefix: bytes = prefix

    @property
    def is_root(self) -> bool:
        return False

    @property
    def is_v2(self) -> bool:
        return self._score_db.is_v2

    def get(self, key: bytes) -> bytes:
        """
        Gets the value for the specified key

        :param key: key to retrieve
        :return: value for the specified key, or None if not found
        """
        hashed_key: bytes = self._hash_key(key)
        return self._score_db.get(hashed_key)

    def put(self, key: bytes, value: bytes):
        """
        Sets a value for the specified key.

        :param key: key to set
        :param value: value to set
        """
        hashed_key: bytes = self._hash_key(key)
        self._score_db.put(hashed_key, value)

    def delete(self, key: bytes):
        """
        Deletes the key/value pair for the specified key.

        :param key: key to delete
        """
        hashed_key: bytes = self._hash_key(key)
        self._score_db.delete(hashed_key)

    def close(self):
        self._score_db.close()

    @abstractmethod
    def _hash_key(self, key: bytes) -> bytes:
        pass


class ScoreSubDBv1(ScoreSubDBBase):
    def _hash_key(self, key: bytes) -> bytes:
        """All key is hashed and stored
        to StateDB to avoid key conflicts among SCOREs

        :params key: key passed by SCORE
        :return: key bytes
        """
        return b'|'.join((self._prefix, key))


class ScoreSubDBv2(ScoreSubDBBase):
    def _hash_key(self, key: bytes) -> bytes:
        return b''.join((self._prefix, key))
