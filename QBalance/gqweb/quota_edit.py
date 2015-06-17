# ===========================================================================
# Methods to validate edited quota info from form data and trees
# ===========================================================================
import models
from gqweb import app


def validate_form_types(data):
    errors = list()
    for k, v in data.items():
        fn, valid, msg = models.type_map[k]
        try:
            data[k] = fn(v)
            if not valid(data[k]):
                raise ValueError
        except ValueError:
            errors.append((data['group_name'], k, msg))

    return data, errors


def set_params(db, formdata):
    for name, params in formdata.iteritems():
        dbobj = next(x for x in db if x.group_name == name)
        for param, val in params.iteritems():
            if param == 'group_name':
                continue
            setattr(dbobj, param, val)

        # NOTE: Since form value isn't present if not checked!
        dbobj.accept_surplus = 'accept_surplus' in params


def set_quota_sums(db, root):
    for group in root:
        if not group.is_leaf:
            newquota = sum(x.quota for x in group.get_children())

            # FIXME: and not user_sum_change_auth
            if newquota != group.quota and True:
                app.logger.info("Intermediate group sum %s: %d->%d",
                                group.full_name, group.quota, newquota)
                dbobj = next(x for x in db if x.group_name == group.full_name)
                dbobj.quota = newquota
                group.quota = newquota
