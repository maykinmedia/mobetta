def update_translations(icu_file, form_changes):
    """
    Takes in a ``mobetta.icu.models.IcuFile`` object and a list of changes to
    apply.

    Format of changes:
        [
            (<form>, [
                {
                'msgid': <msgid>,
                'field': '<field_name>',
                'from': '<old_value>',
                'to': '<new_value>',
                },
                ...
            ]),
            ...
        ]
    """
    applied_changes = []
    rejected_changes = []

    for form, changes in form_changes:
        for change in changes:
            key = change['msgid']
            if key not in icu_file.contents:
                raise RuntimeError("Entry not found")

            if change['field'] == 'translation':
                if change['from'] == icu_file.contents[key]:
                    icu_file.contents[key] = change['to']
                    applied_changes.append((form, change))
                else:
                    change['current_value'] = icu_file.contents[key]
                    rejected_changes.append((form, change))
            else:
                raise RuntimeError('Unexpected field changed!')
    return applied_changes, rejected_changes
