#!/usr/bin/env python

import pytest
from yafi import FIXContext, FIXInterface
import json

context = FIXContext('4.2')
interface = FIXInterface(context)





message = interface.generate_message('E')

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


#print(json.dumps(eval(str(message.data).replace("DefaultOrderedDict", "list")), indent=4))#

