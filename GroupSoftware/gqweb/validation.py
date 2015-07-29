# *****************************************************************************
# The following is all for form validation of the user-input data
# *****************************************************************************

import re
from . import app

name_validate = lambda name: bool(re.match(r'^group_[a-z0-9_\.]+$', name))
new_name_validate = lambda name: bool(re.match(r'^[a-z0-9_]+$', name))
positive_int = lambda x: x > 0.0
non_zero_int = lambda x: x >= 1
non_negative = lambda x: x >= 0.0

type_map = {
    'priority': (float, positive_int, 'floating point value greater than zero'),
    'weight': (float, non_negative, 'non-negative floating point value'),
    'quota': (int, non_zero_int, 'integer greater than 0'),
    'new_name': (str, new_name_validate, 'string matching [a-z_]+'),
    'group_name': (str, name_validate, 'string matching [a-z_](.[a-z_])*'),
    'surplus_threshold': (int, non_negative, 'integer >= 0'),
    'accept_surplus': (lambda x: x == 'on', lambda x: True, 'boolean'),
}

group_defaults = {
    'group_name': None,
    'quota': None,
    'priority': 10.0,
    'weight': 0.0,
    'surplus_threshold': 0,
}


def validate_form_types(data):
    """ Take raw form data (@data) and validate & convert types of each """

    errors = list()
    for k, v in data.items():
        # XXX: Remove me?
        # if k == 'group_name':
        #     continue
        fn, valid, msg = type_map[k]
        try:
            data[k] = fn(v)
            if not valid(data[k]):
                raise ValueError
        except ValueError:
            estr = "<u>%s</u>, <i>%s</i> needs to be a %s" % \
                   (data['group_name'], k, msg)
            errors.append(estr)

    return data, errors


def set_quota_sums(db, root):
    """ Renormalize the sums in the group-tree (@root) of non-leaf nodes """
    for group in root:
        if not group.is_leaf:
            newquota = sum(x.quota for x in group.get_children())

# !! FIXME: and not user_sum_change_auth
            if newquota != group.quota and True:
                app.logger.info("Intermediate group sum %s: %d->%d",
                                group.full_name, group.quota, newquota)
                dbobj = next(x for x in db if x.group_name == group.full_name)
                dbobj.quota = newquota
                group.quota = newquota

            # If newly added group causes a former leaf that has non-zero
            # threshold to become a non-leaf then set it to zero!
            if group.surplus_threshold > 0:
                dbobj = next(x for x in db if x.group_name == group.full_name)
                dbobj.surplus_threshold = 0
