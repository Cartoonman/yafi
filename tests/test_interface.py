#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2019 Carl Colena
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import pytest
import yafi
from yafi import FIXContext, FIXInterface


@pytest.fixture
def interface_42():
    context = FIXContext("4.2")
    interface = FIXInterface(context)
    return interface


def test_message_generator(interface_42):
    interface = interface_42
    message = interface.generate_message("E")
    assert message is not None
    with pytest.raises(KeyError): interface.generate_message("ZZZ")


def test_message_basics(interface_42):
    interface = interface_42
    message = interface.generate_message("E")

    assert message['ListID'] == None
    assert message[66] == None
    assert message["66"] == None
    assert message['66'] == None

    message['ListID'] = "A1J2Z5"

    assert message['ListID'] == "A1J2Z5"
    assert message[66] == "A1J2Z5"
    assert message["66"] == "A1J2Z5"
    assert message['66'] == "A1J2Z5"

    message[66] = "G6F8H6"

    assert message[66] != "A1J2Z5"
    assert message['ListID'] != "A1J2Z5"
    assert message[66] == "G6F8H6"
    assert message['ListID'] == "G6F8H6"

    data = message['ListID']

    assert data == "G6F8H6"

    with pytest.raises(KeyError): message['Adjustment']
    with pytest.raises(KeyError): message[45]
    with pytest.raises(KeyError): message['EncodedUnderlyingSecurityDesc']
    with pytest.raises(KeyError): message['listid']
    with pytest.raises(KeyError): message['45']
    with pytest.raises(KeyError): message[list]
    with pytest.raises(TypeError): message[[66]]
    with pytest.raises(TypeError): message[['ListID']]

def test_message_group(interface_42):
    interface = interface_42
    message = interface.generate_message("IOI")
    group = message.get_group_template('NoIOIQualifiers')
    assert isinstance(group, yafi.interface.Group)

    with pytest.raises(KeyError): group['Adjustment']
    with pytest.raises(KeyError): group[45]
    with pytest.raises(KeyError): group['EncodedUnderlyingSecurityDesc']
    with pytest.raises(KeyError): group['listid']
    with pytest.raises(KeyError): group['45']
    with pytest.raises(KeyError): group[list]
    with pytest.raises(TypeError): group[[66]]
    with pytest.raises(TypeError): group[['ListID']]

    group['IOIQualifier'] = "X"

    assert group['IOIQualifier'] == "X"
    assert group[104] == "X"
    assert group["104"] == "X"
    assert group['104'] == "X"


    data = group['IOIQualifier']

    assert data == "X"

    assert group is not interface.generate_message("IOI")

    message.add_group(group)

    



if __name__ == '__main__':
    context = FIXContext("4.2")
    interface = FIXInterface(context)


    message = interface.generate_message("E")

    grp = message.get_group_template(73)
    grp[11] = 5000
    subgrp = grp.get_subgroup_template(78)
    subgrp[79] = "BERK"
    subgrp[80] = 536
    grp.add_subgroup(subgrp)
    subgrp[79] = "HATH"
    subgrp[80] = 255
    grp.add_subgroup(subgrp)
    message.add_group(grp)
    # print(json.dumps(eval(str(message.data).replace("DefaultOrderedDict", "list")), indent=4))#   