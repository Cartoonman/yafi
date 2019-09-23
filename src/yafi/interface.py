#!/usr/bin/env python
from yafi.utils import DefaultOrderedDict
import time, datetime
import copy


class Tag(object):
    def __init__(self, FIX_id=None, FIX_name=None, FIX_type=None, FIX_data=None):
        self.data = FIX_data
        self.id_ = FIX_id
        self.name = FIX_name
        self.type = FIX_type

    def set_data(self, x):
        # self.check(x) TODO
        self.data = x

    def get_data(self):
        return self.data

    def gen_fix(self):
        return str(self.id_) + "=" + str(self.data) + "\x01"

    def length(self):
        return len(self.gen_fix())

    def is_none(self):
        return self.data == None

    def __repr__(self):
        return "Tag [{}({}): {}]".format(self.name, self.id_, self.data)


class Group(object):
    def __init__(self, id_, name, group_def, tag_context):
        self.data = DefaultOrderedDict(dict)
        self.tag_dict = tag_context
        self.id_ = id_
        self.name = name
        for k, v in group_def.items():
            self.data[k]["data"] = None
            if "members" in v:
                self.data[k]["members"] = []
                self.data[k]["template"] = Group(
                    k, self.tag_dict[k]["name"], v["members"], tag_context
                )

    def add_subgroup(self, group):
        self.data[group.id_]["members"].append(copy.deepcopy(group.data))

    def get_subgroup_template(self, key):
        if isinstance(key, str):
            try:
                key = int(key)
            except ValueError:
                key = self.tag_dict[key]["n_id"]
        return copy.deepcopy(self.data[key]["template"])

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                key = int(key)
            except ValueError:
                key = self.tag_dict[key]["n_id"]

        return data[key]["data"]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            try:
                key = int(key)
            except ValueError:
                key = self.tag_dict[key]["n_id"]

        self.data[key]["data"] = value

    def __repr__(self):
        return self.data.__repr__()
class Message(object):
    def __init__(
        self,
        header,
        trailer,
        req_tags,
        opt_tags,
        groups,
        msg_cat,
        id_,
        name,
        tag_context,
    ):
        self.id_ = id_
        self.name = name
        self.data = {
            "header": DefaultOrderedDict(dict),
            "tags": DefaultOrderedDict(dict),
            "trailer": DefaultOrderedDict(dict),
        }
        self.fix_msg_payload = None
        self.tag_dict = tag_context

        for k, v in header["n_id"].items():
            self.data["header"][k]["data"] = None
        for k, v in trailer["n_id"].items():
            self.data["trailer"][k]["data"] = None
        for k, v in {**req_tags["tags_id"], **opt_tags["tags_id"]}.items():
            self.data["tags"][k]["data"] = None
            if "members" in v:
                self.data["tags"][k]["members"] = []
                self.data["tags"][k]["template"] = Group(
                    k, tag_context[k]["name"], groups[k], tag_context
                )

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                key = int(key)
            except ValueError:
                key = self.tag_dict[key]["n_id"]
        merged_data = {
            **self.data["header"],
            **self.data["tags"],
            **self.data["trailer"],
        }

        if key in merged_data:
            return merged_data[key]["data"]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            try:
                key = int(key)
            except ValueError:
                key = self.tag_dict[key]["n_id"]

        if key in self.data["header"]:
            self.data["header"][key]["data"] = value
        elif key in self.data["trailer"]:
            self.data["trailer"][key]["data"] = value
        elif key in self.data["tags"]:
            self.data["tags"][key]["data"] = value

    def add_group(self, group):
        group_data = copy.deepcopy(group.data)
        if group.id_ in self.data["tags"]:
            self.data["tags"][group.id_]["members"].append(group_data)
        elif group.id_ in self.data["header"]:
            self.data["header"][group.id_]["members"].append(group_data)
        elif group.id_ in self.data["trailer"]:
            self.data["trailer"][group.id_]["members"].append(group_data)

    def get_group_template(self, tag_id):
        if isinstance(tag_id, str):
            try:
                tag_id = int(tag_id)
            except ValueError:
                tag_id = self.tag_dict[tag_id]["n_id"]
        return copy.deepcopy(
            {**self.data["header"], **self.data["tags"], **self.data["trailer"]}[
                tag_id
            ]["template"]
        )

    def ready_pkg(self):
        temp_set = self.required_tags
        for tag in self.tags.keys():
            temp_set.discard(tag)
        if len(temp_set) != 0:
            return False, temp_set
        else:
            return True, None

    def ready_send(self):
        temp_set_header = self.header.required_tags
        for tag in self.header.tags.keys():
            temp_set_header.discard(tag)
        if len(temp_set_header) != 0:
            return False, "HEAD", temp_set_header

        pkg_state, msg_set = self.ready_pkg()
        if not pkg_state:
            return False, "MSG", msg_set

        temp_set_trailer = self.trailer.required_tags
        for tag in self.trailer.tags.keys():
            temp_set_trailer.discard(tag)
        if len(temp_set_trailer) != 0:
            return False, "TAIL", temp_set_trailer

        return True, None, None

    def __str__(self):
        tabs = "\t"
        print_msg = f"Message [{self.name}({self.id_})]: \n[\n{tabs}"
        print_msg += f"HEADER: "
        tabs += "\t"
        for k, v in self.data["header"].items():
            print_msg += f"\n{tabs}"
            print_msg += f"{k}: {v['data']}"
        tabs = tabs[:-1]
        print_msg += f"\n{tabs}MSG: "
        tabs += "\t"
        for k, v in self.data["tags"].items():
            print_msg += f"\n{tabs}"
            print_msg += f"{k}: {v['data']}"
            if "members" in v:
                # recursion
                print_msg = self._print_recurse(print_msg, v, tabs)

        tabs = tabs[:-1]
        print_msg += f"\n{tabs}TRAILER: "
        tabs += "\t"
        for k, v in self.data["trailer"].items():
            print_msg += f"\n{tabs}"
            print_msg += f"{k}: {v['data']}"

        tabs = tabs[:-1]
        print_msg += "\n]\n"

        return print_msg

    def _print_recurse(self, print_msg, data, tabs):
        print_msg += f"\n{tabs}["
        tabs += "\t"
        for grp in data["members"]:
            print_msg += f"\n{tabs}{{"
            tabs += "\t"
            for kx, vx in grp.items():
                print_msg += f"\n{tabs}"
                print_msg += f"{kx}: {vx['data']}"
                if "members" in vx:
                    print_msg = self._print_recurse(print_msg, vx, tabs)
            tabs = tabs[:-1]
            print_msg += f"\n{tabs}}}"
        tabs = tabs[:-1]
        print_msg += f"\n{tabs}]"
        return print_msg


class FIXInterface(object):
    def __init__(self, context):
        self._context = context

    def generate_message(self, id_in):
        # Check if name is in context
        if id_in in self._context._protocol_msgs["admin"]:
            msg_cat = "admin"
        elif id_in in self._context._protocol_msgs["app"]:
            msg_cat = "app"
        else:
            pass
            # throw exception message invalid

        # Check if we have name or ID
        msg_def = self._context._protocol_msgs[msg_cat][id_in]
        if "name" in msg_def:
            msg_type = id_in
            name = msg_def["name"]
        elif "msgtype" in msg_def:
            msg_type = msg_def["msgtype"]
            name = id_in
        else:
            raise KeyError(f"Unknown error related to {id_in}")
            # throw unknown exception

        # Set Header and Trailer Defs
        header = self._context._protocol_header
        trailer = self._context._protocol_trailer

        # Set req and opt tags
        req_tags = {"tags_name": {}, "tags_id": {}}
        opt_tags = {"tags_name": {}, "tags_id": {}}

        req_tags["tags_name"].update(
            dict(
                filter(
                    lambda x: x[1]["required"] == "Y",
                    self._context._protocol_msgs[msg_cat][msg_type][
                        "tags_name"
                    ].items(),
                )
            )
        )
        req_tags["tags_id"].update(
            dict(
                filter(
                    lambda x: x[1]["required"] == "Y",
                    self._context._protocol_msgs[msg_cat][msg_type]["tags_id"].items(),
                )
            )
        )
        opt_tags["tags_name"].update(
            dict(
                filter(
                    lambda x: x[1]["required"] == "N",
                    self._context._protocol_msgs[msg_cat][msg_type][
                        "tags_name"
                    ].items(),
                )
            )
        )
        opt_tags["tags_id"].update(
            dict(
                filter(
                    lambda x: x[1]["required"] == "N",
                    self._context._protocol_msgs[msg_cat][msg_type]["tags_id"].items(),
                )
            )
        )

        merged_tags_id = {**req_tags["tags_id"], **opt_tags["tags_id"]}
        groups = {}
        for k, v in merged_tags_id.items():
            if "members" in v:
                groups[k] = v["members"]

        return Message(
            header=header,
            trailer=trailer,
            req_tags=req_tags,
            opt_tags=opt_tags,
            groups=groups,
            id_=msg_type,
            name=name,
            msg_cat=msg_cat,
            tag_context=self._context._protocol_tags,
        )

    def load_message(self, msg_array):
        message_type = msg_array[2].split("=", 1)[1]
        message = self.generate_message(message_type)

        # Passes
        for tag in msg_array:
            id_ = tag.split("=", 1)[0]
            data = tag.split("=", 1)[1]
            if id_ in message.header.required_tags.union(message.header.optional_tags):
                self.add_tag(id_, data, message.header)
            if id_ in message.required_tags.union(message.optional_tags):
                self.add_tag(id_, data, message)
            if id_ in message.trailer.required_tags.union(
                message.trailer.optional_tags
            ):
                self.add_tag(id_, data, message.trailer)

        # Check for orphaned tags.
        total_msg_tags = set(
            list(message.header.tags.keys())
            + list(message.tags.keys())
            + list(message.trailer.tags.keys())
        )
        for tag in msg_array:
            if tag.split("=", 1)[0] not in total_msg_tags:
                print(
                    "WARN: {} NOT IN MESSAGE DEFINITION. MESSAGE: {}".format(
                        tag, message
                    )
                )

        return message

    def _prepare_ctrl_msg(self, ctrl_msg_def, msg_id):
        required_tags = ctrl_msg_def["required"]
        optional_tags = ctrl_msg_def["optional"]
        # Fix for potentially blank entries.
        if len(required_tags) == 1 and required_tags[0] == "":
            required_tags = set([])
        if len(optional_tags) == 1 and optional_tags[0] == "":
            optional_tags = set([])
        return self.Message(
            None,
            None,
            set(required_tags),
            set(optional_tags),
            ctrl_msg_def["id"],
            ctrl_msg_def["name"],
            ctrl_msg_def["description"],
        )

    def _prepare_msg(self, msg_def, header, trailer):
        required_tags = msg_def["required"]
        optional_tags = msg_def["optional"]
        # Fix for potentially blank entries.
        if len(required_tags) == 1 and required_tags[0] == "":
            required_tags = set([])
        if len(optional_tags) == 1 and optional_tags[0] == "":
            optional_tags = set([])
        return self.Message(
            header,
            trailer,
            set(required_tags),
            set(optional_tags),
            msg_def["id"],
            msg_def["name"],
            msg_def["description"],
        )

    def decode(self, id_):
        return self.FIX_Context._protocol_tags[id_]["FIX_name"]

    def _gen_tag(self, id_, data=None):
        tag_struct = self.FIX_Context._protocol_tags[id_]
        return self.Tag(
            tag_struct["FIX_id"],
            tag_struct["FIX_name"],
            tag_struct["FIX_type"],
            tag_struct["FIX_description"],
            data,
        )

    def add_tag(self, id_, data, message):
        if str(id_) in message.required_tags.union(message.optional_tags):
            if not message._primed:
                message.tags[str(id_)].append(self._gen_tag(str(id_), data))
            else:
                raise ReadOnlyError("Message cannot be modified after primed state.")
        else:
            raise InvalidTag(f"Tag {str(id_)} is not in Message {message.name}")

    def prepare(self, message, seq, timestamp):
        # Check if ready (all req tags set in msg)
        if message.ready_pkg()[0] is not True:
            raise MessageNotReady("Message does not pass ready_pkg() check.")

        # Fill in rest of Header
        self.add_tag(34, seq, message.header)
        self.add_tag(52, timestamp, message.header)
        self.add_tag(35, message.id_, message.header)

        body_length = self.calc_body_length(message)

        self.add_tag(9, body_length, message.header)
        self.add_tag(8, "FIX.4.2", message.header)

        # Calculate CheckSum
        checksum = self.gen_checksum(message)
        self.add_tag(10, checksum, message.trailer)

        # Generate Raw Fix Msg
        fix_msg = self.gen_raw_fix(message)
        message.fix_msg_payload = fix_msg
        message._primed = True

    def calc_body_length(self, message):
        # Calculate body length
        body_length = sum(
            [
                tag.length()
                for taglist in [
                    message.header.tags.values(),
                    message.tags.values(),
                    message.trailer.tags.values(),
                ]
                for tags in taglist
                for tag in tags
            ]
        )
        # Remove length of tags 8, 9, and 10 if already in message.
        for id_ in ["8", "9"]:
            if id_ in message.header.tags.keys():
                body_length -= message.header.tags[id_][0].length()
        if "10" in message.trailer.tags.keys():
            body_length -= message.trailer.tags["10"][0].length()
        return body_length

    def gen_checksum(self, message):
        checksum = sum(
            [
                ord(char)
                for taglist in [
                    message.header.tags.values(),
                    message.tags.values(),
                    message.trailer.tags.values(),
                ]
                for tags in taglist
                for tag in tags
                for char in tag.gen_fix()
            ]
        )
        # Take out the checksum itself if it exists already.
        if "10" in message.trailer.tags.keys():
            checksum -= sum(
                [ord(char) for char in message.trailer.tags["10"][0].gen_fix()]
            )
        checksum = str(checksum % 256)
        while len(checksum) < 3:
            checksum = "0" + checksum
        return checksum

    def gen_raw_fix(self, message):
        # Generate first 3 tags
        fix_msg = (
            message.header.tags["8"][0].gen_fix()
            + message.header.tags["9"][0].gen_fix()
            + message.header.tags["35"][0].gen_fix()
        )

        # Generate Header
        for k, v in message.header.tags.items():
            if k in ["8", "9", "35"]:
                continue
            for tag in v:
                fix_msg += tag.gen_fix()

        # Generate Msg
        fix_msg += "".join(
            [tag.gen_fix() for tags in message.tags.values() for tag in tags]
        )

        # Generate Trailer
        for k, v in message.trailer.tags.items():
            if k in ["10"]:
                continue
            for tag in v:
                fix_msg += tag.gen_fix()
        # Generate Checksum
        fix_msg += message.trailer.tags["10"][0].gen_fix()
        fix_msg = fix_msg.encode("ascii")
        return fix_msg

    def validate(self, message):
        calculated_checksum = self.gen_checksum(message)
        calculated_body_length = self.calc_body_length(message)
        if calculated_checksum != message.trailer.tags["10"][0].get():
            print(
                f"CHECKSUM MISMATCH: CALCULATED {calculated_checksum}, GIVEN {message.trailer.tags['10'][0].get()}"
            )
            return False
        if calculated_body_length != int(message.header.tags["9"][0].get()):
            print(
                (
                    f"BODY LENGTH MISMATCH: CALCULATED {calculated_body_length}, GIVEN {message.header.tags['9'][0].get()}"
                )
            )
            return False
        return True

    def parse(self, input_response):
        working_data = input_response.decode("ascii")
        pointers_front = []
        pointers_rear = []
        del_rear = None
        messages = []
        working_data_arr = [x for x in working_data.split("\x01")]
        for tag in range(len(working_data_arr)):
            if working_data_arr[tag][:2] == "8=":  # Needs to be another check here
                pointers_front.append(tag)
            if working_data_arr[tag][:3] == "10=" and len(working_data_arr[tag]) == 6:
                pointers_rear.append(tag)

        for front, rear in zip(pointers_front, pointers_rear):
            message = self.load_message(working_data_arr[front : rear + 1])
            # Check checksum and message length matches for security.
            del_rear = rear
            if not (self.validate(message)):
                continue
            else:
                messages.append(message)

        # Clear buffer if all we got was junk with no front tag found.
        if len(working_data_arr) != 0 and len(pointers_front) == 0 and del_rear is None:
            working_data_arr = []

        # Remove the corresponding data from original working data. (reconstruct remaining?)
        if del_rear is not None:
            working_data_arr = working_data_arr[del_rear + 1 :]
        # Take care of trailing control char case.
        if len(working_data_arr) == 1 and working_data_arr[0] == "":
            working_data_arr = []

        remainder_buffer = ""
        # Reconstruct the remainder in buffer
        if len(working_data_arr) != 0:
            remainder_buffer = "\x01".join(working_data_arr)
        remainder_buffer = remainder_buffer.encode("ascii")

        # Return results
        # (messages_array, remaining string buffer)
        return messages, remainder_buffer

    def _get_req_tags(self, id_):
        return {
            i: self._gen_tag(i)
            for i in self.FIX_Context._protocol_msgs[id_]["required"]
        }

    def _get_opt_tags(self, id_, opt_tag_list):
        return {
            i: self._gen_tag(i)
            for i in [
                str(tag)
                for tag in opt_tag_list
                if str(tag) in self.FIX_Context._protocol_msgs[id_]["optional"]
            ]
        }
