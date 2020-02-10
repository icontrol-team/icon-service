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

"""IconScoreEngine testcase
"""
from typing import TYPE_CHECKING

from iconservice import Address
from iconservice.base.exception import ExceptionCode
from iconservice.icon_constant import ICX_IN_LOOP, PREP_MAIN_PREPS, ConfigKey, Revision
from tests import create_address
from tests.integrate_test.iiss.test_iiss_base import TestIISSBase
from tests.integrate_test.test_integrate_base import EOAAccount

if TYPE_CHECKING:
    pass


class TestPreps(TestIISSBase):
    def _make_init_config(self) -> dict:
        config: dict = super()._make_init_config()
        config[ConfigKey.PREP_REGISTRATION_FEE] = 0
        return config

    def setUp(self):
        super().setUp()
        self.init_decentralized()

    def test_prep_register_node_key_before_rev_DIVIDE_NODE_KEY(self):
        account: 'EOAAccount' = self.create_eoa_account()
        self.distribute_icx(accounts=[account],
                            init_balance=1 * ICX_IN_LOOP)

        dummy_node: 'Address' = create_address()

        # register prep
        reg_data: dict = self.create_register_prep_params(account)
        reg_data["nodeKey"] = str(dummy_node)

        tx: dict = self.create_register_prep_tx(from_=account,
                                                reg_data=reg_data)

        _, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx])
        self.assertEqual(tx_results[1].failure.code, ExceptionCode.INVALID_PARAMETER)
        self.assertEqual(tx_results[1].failure.message, f"Mismatch nodeKey and address. "
                                                        f"'divide node key' revision need to be accepted"
                                                        f"(revision: 9)")

    def test_prep_set_node_key_before_rev_DIVIDE_NODE_KEY(self):
        self.distribute_icx(accounts=self._accounts[:PREP_MAIN_PREPS],
                            init_balance=1 * ICX_IN_LOOP)

        account: 'EOAAccount' = self._accounts[0]
        dummy_node: 'Address' = create_address()

        # set prep 1
        tx: dict = self.create_set_prep_tx(from_=account,
                                           set_data={"nodeKey": str(dummy_node)})

        _, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx])
        self.assertEqual(tx_results[1].failure.code, ExceptionCode.INVALID_PARAMETER)
        self.assertEqual(tx_results[1].failure.message, f"Mismatch nodeKey and address. "
                                                        f"'divide node key' revision need to be accepted"
                                                        f"(revision: 9)")

    def test_prep_register_node_key(self):
        self.set_revision(Revision.DIVIDE_NODE_KEY.value)
        account: 'EOAAccount' = self.create_eoa_account()
        self.distribute_icx(accounts=[account],
                            init_balance=1 * ICX_IN_LOOP)

        dummy_node: 'Address' = create_address()

        # register prep
        reg_data: dict = self.create_register_prep_params(account)
        reg_data["nodeKey"] = str(dummy_node)

        tx: dict = self.create_register_prep_tx(from_=account,
                                                reg_data=reg_data)

        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx])
        self.assertEqual(tx_results[1].status, True)

        self._write_precommit_state(block)

        ret: dict = self.get_prep(account.address)
        self.assertEqual(str(ret['nodeKey']), reg_data['nodeKey'])

    def test_prep_set_node_key(self):
        self.set_revision(Revision.DIVIDE_NODE_KEY.value)

        self.distribute_icx(accounts=self._accounts[:PREP_MAIN_PREPS],
                            init_balance=1 * ICX_IN_LOOP)

        account: 'EOAAccount' = self._accounts[0]
        dummy_node: 'Address' = create_address()

        # set prep 1
        tx: dict = self.create_set_prep_tx(from_=account,
                                           set_data={"nodeKey": str(dummy_node)})

        _, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx])
        self.assertEqual(tx_results[1].status, True)
        self.assertEqual(main_prep_as_dict["preps"][0]["id"], dummy_node)

    def test_prep_set_node_key_check_generator(self):
        self.set_revision(Revision.DIVIDE_NODE_KEY.value)

        self.distribute_icx(accounts=self._accounts[:PREP_MAIN_PREPS],
                            init_balance=1 * ICX_IN_LOOP)

        # 0 start change node_key
        account: 'EOAAccount' = self._accounts[0]
        dummy_node1: 'Address' = create_address()

        # set prep 1
        tx: dict = self.create_set_prep_tx(from_=account,
                                           set_data={"nodeKey": str(dummy_node1)})

        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx])
        self.assertEqual(tx_results[1].status, True)
        self.assertEqual(main_prep_as_dict["preps"][0]["id"], dummy_node1)
        self._write_precommit_state(block)

        # 1 before change node_key
        prev_block_generator = self._accounts[0].address
        prev_block_votes = [(x.address, True) for x in self._accounts[1:PREP_MAIN_PREPS]]
        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[],
                                                                                   prev_block_generator=prev_block_generator,
                                                                                   prev_block_validators=None,
                                                                                   prev_block_votes=prev_block_votes,
                                                                                   block=None)
        self.assertEqual(tx_results[0].status, True)
        self.assertEqual(main_prep_as_dict, None)

        self._write_precommit_state(block)

        # 2 after change node_key
        dummy_node2: 'Address' = create_address()
        prev_block_generator = dummy_node1

        # set prep 2
        tx: dict = self.create_set_prep_tx(from_=account,
                                           set_data={"nodeKey": str(dummy_node2)})

        prev_block_votes = [(x.address, True) for x in self._accounts[1:PREP_MAIN_PREPS]]
        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx],
                                                                                   prev_block_generator=prev_block_generator,
                                                                                   prev_block_validators=None,
                                                                                   prev_block_votes=prev_block_votes,
                                                                                   block=None)
        self.assertEqual(tx_results[0].status, True)
        self.assertEqual(main_prep_as_dict["preps"][0]["id"], dummy_node2)
        self._write_precommit_state(block)

    def test_prep_set_node_key_check_votes(self):
        self.set_revision(Revision.DIVIDE_NODE_KEY.value)

        self.distribute_icx(accounts=self._accounts[:PREP_MAIN_PREPS],
                            init_balance=1 * ICX_IN_LOOP)

        # 0 start change node_key
        account: 'EOAAccount' = self._accounts[1]
        dummy_node1: 'Address' = create_address()

        # set prep 1
        tx: dict = self.create_set_prep_tx(from_=account,
                                           set_data={"nodeKey": str(dummy_node1)})

        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx])
        self.assertEqual(tx_results[1].status, True)
        self.assertEqual(main_prep_as_dict["preps"][1]["id"], dummy_node1)
        self._write_precommit_state(block)

        # 1 before change node_key
        prev_block_generator = self._accounts[0].address
        prev_block_votes = [(x.address, True) for x in self._accounts[1:PREP_MAIN_PREPS]]
        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[],
                                                                                   prev_block_generator=prev_block_generator,
                                                                                   prev_block_validators=None,
                                                                                   prev_block_votes=prev_block_votes,
                                                                                   block=None)
        self.assertEqual(tx_results[0].status, True)
        self.assertEqual(main_prep_as_dict, None)

        self._write_precommit_state(block)

        # 2 after change node_key
        dummy_node2: 'Address' = create_address()
        prev_block_generator = dummy_node1

        # set prep 2
        tx: dict = self.create_set_prep_tx(from_=account,
                                           set_data={"nodeKey": str(dummy_node2)})

        prev_block_votes = [(x.address, True) for x in self._accounts[1:PREP_MAIN_PREPS]]
        block, tx_results, _, _, main_prep_as_dict = self.debug_make_and_req_block(tx_list=[tx],
                                                                                   prev_block_generator=prev_block_generator,
                                                                                   prev_block_validators=None,
                                                                                   prev_block_votes=prev_block_votes,
                                                                                   block=None)
        self.assertEqual(tx_results[0].status, True)
        self.assertEqual(main_prep_as_dict["preps"][1]["id"], dummy_node2)
        self._write_precommit_state(block)
