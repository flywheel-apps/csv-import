#!/usr/bin/env python
import csv
import logging
import os
import re

import chardet
import flywheel


log = logging.getLogger('flywheel:csv-import')


def main(context):
    # Read CSV bytes
    filepath = context.get_input_path('subject_csv')
    filename = os.path.basename(filepath)
    with open(filepath, mode='rb') as subject_csv:
        content = subject_csv.read()

    # Get encoding from config or auto-detect
    encoding = context.config.get('encoding') or chardet.detect(content)['encoding']

    log.info('Decoding contents using encoding %s', encoding)
    content = content.decode(encoding)

    # Get delimiter from config or auto-detect
    delimiter = context.config.get('delimiter') or csv.Sniffer().sniff(content).delimiter

    log.info('Loading CSV using delimiter %s', delimiter)
    reader = csv.DictReader(content.split('\n'), delimiter=delimiter)

    log.info('Parsed CSV headers: %s', reader.fieldnames)

    # Get match column from config or auto-detect
    match_column = context.config.get('match_column')
    if not match_column:
        match_re = re.compile(r'id|subject', flags=re.IGNORECASE)
        for column in reader.fieldnames:
            if match_re.search(column):
                match_column = column
                break
        else:
            log.error('Could not determine match column (id|subject)')
            sys.exit(1)
    log.info('Using column "%s" to match subject codes', match_column)

    # Get info key from config if set
    info_key = context.config.get('info_key')
    log.info('Using target field subject.info%s for import', ('.' + info_key) if info_key else '')

    # Determine project to work in based on the input CSV location
    input_hierarchy = context.get_input('subject_csv')['hierarchy']
    if input_hierarchy['type'] == 'project':
        project_id = input_hierarchy['id']
    else:
        container = context.client.get_container(input_hierarchy['id'])
        project_id = container.parents.project

    # Get existing subjects (assume unique and non-empty subject codes)
    log.info('Loading existing subjects from project %s', project_id)
    fw_subjects = {subj.code: subj for subj in context.client.get_project_subjects(project_id)}

    dry_run = context.config.get('dry_run')
    if dry_run:
        log.info('Running in dry-run mode - not updating subjects')

    for subject_info in reader:
        subject_code = subject_info.pop(match_column)
        if subject_code and subject_code in fw_subjects:
            subject_id = fw_subjects[subject_code].id
            log.info('Importing %s (%s)', subject_code, subject_id)
            if not dry_run:
                subject_update = {'info': {info_key: subject_info} if info_key else subject_info}
                context.client.modify_subject(subject_id, subject_update)
        else:
            log.info('Skipping %s (subject not found in project)', subject_code)
    msg = 'Imported subject metadata from {}'.format(filename)
    log.info(msg)
    if not dry_run:
        context.client.add_project_note(project_id, msg)


if __name__ == '__main__':
    with flywheel.GearContext() as context:
        context.init_logging()
        context.log_config()
        main(context)
