from .utils import get_field_value


def group_by(qset, *fields, **kwargs):
    """ group_by iterator with support for multiple nested fields """
    ix = kwargs.get('ix', 0)
    if ix is 0:
        qset = qset.order_by(*fields)
    group = []
    first = True
    for obj in qset:
        try:
            current = get_field_value(obj, fields[ix])
        except AttributeError:
            # Intermediary relation does not exists
            current = None
        if first or current == previous:
            group.append(obj)
        else:
            if ix < len(fields)-1:
                group = group_by(group, *fields, ix=ix+1)
            yield previous, group
            group = [obj]
        previous = current
        first = False
    if ix < len(fields)-1:
        group = group_by(group, *fields, ix=ix+1)
    yield previous, group
