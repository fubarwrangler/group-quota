# ===========================================================================
# The following is all for form validation of the user-input data from forms
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
import re

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
