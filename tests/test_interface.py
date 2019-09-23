#!/usr/bin/env python

import pytest
from yafi import FIXContext, FIXInterface


@pytest.fixture
def interface():
    context = FIXContext("4.2")
    interface = FIXInterface(context)
    return interface


def test_message_generator(interface):
    message = interface.generate_message("E")
    print(message.header_def)
    print(message.groups)
    print(
        json.dumps(
            eval(str(message.data).replace("DefaultOrderedDict", "list")), indent=4
        )
    )
