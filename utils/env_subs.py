# coding=utf-8
from past.builtins import basestring


def perform_dict_substitutions(d):
    # collect unique names and use them to do substitutions
    vars = {}

    def flat_dict(d):
        """ Recursively iterate dictionary and flat it to vars """
        for k, v in d.items():
            if isinstance(v, dict):
                flat_dict(v)  # recurse on sub-dictionary
            elif isinstance(v, basestring):
                vars[k] = v

    flat_dict(d)  # so everything is in flat

    def substitute(d):
        """ Do substitution until something change """
        while True:
            something_changed = False
            for k, v in d.items():
                if isinstance(v, dict):
                    substitute(v)  # recurse on sub-dictionary
                elif isinstance(v, basestring):
                    old_value = v
                    v = v.format(**vars)
                    if v != old_value:
                        vars[k] = v
                        something_changed = True
                        d[k] = v
            if not something_changed:
                break

    substitute(d)
