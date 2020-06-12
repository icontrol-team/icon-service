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

from typing import Optional, Any, Union, TYPE_CHECKING

from .container_db import K, V
from .container_db.array_db import ArrayDBv1, ArrayDBv2
from .container_db.dict_db import DictDBv1, DictDBv2
from .container_db.var_db import VarDBv1, VarDBv2
from ..base.exception import InvalidContainerAccessException, InvalidParamsException

if TYPE_CHECKING:
    from ..database.db import IconScoreDatabase, IconScoreSubDatabase


class DictDB:
    """
    Utility classes wrapping the state DB.
    DictDB behaves more like python dict.
    DictDB does not maintain order.

    :K: [int, str, Address, bytes]
    :V: [int, str, Address, bytes, bool]
    """

    def __init__(
            self,
            var_key: K,
            db: Union['IconScoreDatabase', 'IconScoreSubDatabase'],
            value_type: type,
            depth: int = 1
    ):
        if db.is_v2:
            self._db = DictDBv2(
                key=var_key,
                db=db,
                value_type=value_type,
                depth=depth
            )
        else:
            self._db = DictDBv1(
                key=var_key,
                db=db,
                value_type=value_type,
                depth=depth
            )

    def remove(self, key: K):
        if not self._db.is_leaf:
            raise InvalidContainerAccessException('DictDB depth mismatch')
        self._db.remove(key)

    def __setitem__(self, key: K, value: V):
        if not self._db.is_leaf:
            raise InvalidContainerAccessException('DictDB depth mismatch')
        self._db.__setitem__(key, value)

    def __getitem__(self, key: K) -> Any:
        if not self._db.is_leaf:
            return DictDB(key, *self._db.params)
        return self._db.__getitem__(key)

    def __delitem__(self, key: K):
        self._db.__delitem__(key)

    def __contains__(self, key: K) -> bool:
        return self._db.__contains__(key)

    def __iter__(self):
        raise InvalidContainerAccessException("Iteration not supported in DictDB")


class ArrayDB:
    """
    Utility classes wrapping the state DB.
    ArrayDB supports length and iterator, maintains order.

    :K: [int, str, Address, bytes]
    :V: [int, str, Address, bytes, bool]
    """

    def __init__(
            self,
            var_key: K,
            db: 'IconScoreDatabase',
            value_type: type
    ):
        if db.is_v2:
            self._db = ArrayDBv2(
                key=var_key,
                db=db,
                value_type=value_type
            )
        else:
            self._db = ArrayDBv1(
                key=var_key,
                db=db,
                value_type=value_type
            )

    def put(self, value: V):
        """
        Puts the value at the end of array

        :param value: value to add
        """
        self._db.put(value)

    def pop(self) -> Optional[V]:
        """
        Gets and removes last added value

        :return: last added value
        """
        return self._db.pop()

    def get(self, index: int = 0) -> V:
        """
        Gets the value at index

        :param index: index
        :return: value at the index
        """
        return self._db.__getitem__(index)

    def __iter__(self):
        return self._db.__iter__()

    def __len__(self):
        return self._db.__len__()

    def __setitem__(self, index: int, value: V):
        if not isinstance(index, int):
            raise InvalidParamsException('Invalid index type: not an integer')
        return self._db.__setitem__(index, value)

    def __getitem__(self, index: int) -> V:
        return self._db.__getitem__(index)

    def __contains__(self, item: V) -> bool:
        return self._db.__contains__(item)


class VarDB:
    """
    Utility classes wrapping the state DB.
    VarDB can be used to store simple key-value state.

    :K: [int, str, Address, bytes]
    :V: [int, str, Address, bytes, bool]
    """

    def __init__(
            self,
            var_key: K,
            db: 'IconScoreDatabase',
            value_type: type
    ):
        if db.is_v2:
            self._db = VarDBv2(
                key=var_key,
                db=db,
                value_type=value_type
            )
        else:
            self._db = VarDBv1(
                key=var_key,
                db=db,
                value_type=value_type
            )

    def set(self, value: V):
        """
        Sets the value

        :param value: a value to be set
        """
        self._db.set(value)

    def get(self) -> Optional[V]:
        """
        Gets the value

        :return: value of the var db
        """
        return self._db.get()

    def remove(self):
        """
        Deletes the value
        """
        self._db.remove()
