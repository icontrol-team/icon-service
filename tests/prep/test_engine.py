# -*- coding: utf-8 -*-
# Copyright 2019 ICON Foundation
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

import random
import unittest
from typing import List, Tuple
from unittest import mock

from iconservice.base.address import AddressPrefix, Address
from iconservice.icon_constant import PREP_MAIN_PREPS, PREP_MAIN_AND_SUB_PREPS
from iconservice.icon_constant import PRepGrade
from iconservice.prep import PRepEngine
from iconservice.prep.data import PRep, PRepContainer


class TestEngine(unittest.TestCase):
    def setUp(self) -> None:
        size = 200
        self.new_preps = PRepContainer()

        # Create 200 dummy preps
        for i in range(size):
            address = Address.from_prefix_and_int(AddressPrefix.EOA, i)
            prep = PRep(address, block_height=i, irep_block_height=i)
            self.assertEqual(PRepGrade.CANDIDATE, prep.grade)
            self.assertEqual(0, prep.delegated)

            self.new_preps.add(prep)

    def tearDown(self) -> None:
        self.new_preps = None

    def test__update_prep_grades_1(self):
        old_prep_list = []
        delegated_list: List[Tuple[int, int]] = []
        new_preps: 'PRepContainer' = self.new_preps

        term = mock.MagicMock()
        term.preps = []

        context = mock.MagicMock()
        context.main_prep_count = PREP_MAIN_PREPS
        context.main_and_sub_prep_count = PREP_MAIN_AND_SUB_PREPS
        context.preps = new_preps
        context.term = term

        # Case0: Network has just decentralized without any delegation
        PRepEngine._update_prep_grades_on_term_ended(context)

        for i, prep in enumerate(new_preps):
            if i < PREP_MAIN_PREPS:
                self.assertEqual(PRepGrade.MAIN, prep.grade)
            elif i < PREP_MAIN_AND_SUB_PREPS:
                self.assertEqual(PRepGrade.SUB, prep.grade)
            else:
                self.assertEqual(PRepGrade.CANDIDATE, prep.grade)

        # Case1: Sort preps in descending order by prep.order()
        for i, prep in enumerate(new_preps):
            delegated: int = random.randint(0, 10_000)
            delegated_list.append((-delegated, i))

            old_prep_list.append(prep)
            new_preps.remove(prep.address)
            prep.delegated = delegated
            new_preps.add(prep)

        # Expected list in descending order by (delegated, block_height, tx_index)
        delegated_list.sort()

        for i in range(200):
            prep = old_prep_list[i]
            prep2 = new_preps.get_by_address(prep.address)
            self.assertEqual(id(prep), id(prep2))

        PRepEngine._update_prep_grades_on_term_ended(main_prep_count=PREP_MAIN_PREPS,
                                                     main_and_sub_prep_count=PREP_MAIN_AND_SUB_PREPS,
                                                     old_preps=old_prep_list,
                                                     new_preps=new_preps)

        i = 0
        for delegated, index in delegated_list:
            prep: 'PRep' = new_preps.get_by_index(i)
            prep_in_list: 'PRep' = old_prep_list[index]

            self.assertEqual(abs(delegated), prep.delegated)
            self.assertEqual(prep_in_list.address, prep.address)

            if i < PREP_MAIN_PREPS:
                self.assertEqual(PRepGrade.MAIN, prep.grade)
            elif i < PREP_MAIN_AND_SUB_PREPS:
                self.assertEqual(PRepGrade.SUB, prep.grade)
            else:
                self.assertEqual(PRepGrade.CANDIDATE, prep.grade)

            i += 1
