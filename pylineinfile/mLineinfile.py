import logging
import os
import re
import tempfile
import shutil


logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)
logger = logging.getLogger("lineinfile")

#def check_file_attrs(changed, message, diff):
#
#    file_args = module.load_file_common_arguments(module.params)
#    if module.set_fs_attributes_if_different(file_args, False, diff=diff):
#
#        if changed:
#            message += " and "
#        changed = True
#        message += "ownership, perms or SE linux context changed"
#    return message, changed


def write_changes(b_lines, dest):

    tmpfd, tmpfile = tempfile.mkstemp()
    f = os.fdopen(tmpfd, 'wb')
    f.writelines(b_lines)
    f.flush()
    os.fsync(f.fileno())
    f.close()

    shutil.move(tmpfile, dest)
    #validate = None #module.params.get('validate', None)
    #valid = not validate
    #if validate:
    #    if "%s" not in validate:
    #        logging.error("validate must contain %%s: %s" % (validate))
    #        exit(1)
    #    (rc, out, err) = module.run_command((validate % tmpfile).encode(errors='surrogate_or_strict'))
    #    valid = rc == 0
    #    if rc != 0:
    #        module.fail_json(msg='failed to validate: '
    #                             'rc:%s error:%s' % (rc, err))
    #if valid:
    #    module.atomic_move(tmpfile,
    #                       to_native(os.path.realpath(dest.encode(errors='surrogate_or_strict'), errors='surrogate_or_strict'),
    #                       unsafe_writes=module.params['unsafe_writes'])

def present(dest, regexp, line, insertafter, insertbefore, create,
            backup, backrefs, firstmatch):
    logger.debug("present")
    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    if not os.path.exists(dest):
        if not create:
            logger.error(rc=257, msg='Destination %s does not exist !' % dest)
            exit(1)
        b_destpath = os.path.dirname(dest)
        if not os.path.exists(b_destpath):
            try:
                os.makedirs(b_destpath)
            except Exception as e:
                logger.error(
                    msg='Error creating %s Error code: %s Error description: %s' % (b_destpath, e[0], e[1]))

        b_lines = []
    else:
        f = open(dest, 'rb')
        b_lines = f.readlines()
        f.close()

    if regexp is not None:
        bre_m = re.compile(regexp.encode())

    if insertafter not in (None, 'BOF', 'EOF'):
        bre_ins = re.compile(insertafter.encode())
    elif insertbefore not in (None, 'BOF'):
        bre_ins = re.compile(insertbefore.encode())
    else:
        bre_ins = None

    # index[0] is the line num where regexp has been found
    # index[1] is the line num where insertafter/inserbefore has been found
    index = [-1, -1]
    m = None
    b_line = line.encode()
    for lineno, b_cur_line in enumerate(b_lines):
        if regexp is not None:
            match_found = bre_m.search(b_cur_line)
        else:
            match_found = b_line == b_cur_line.rstrip('\r\n')
        if match_found:
            index[0] = lineno
            m = match_found
        elif bre_ins is not None and bre_ins.search(b_cur_line):
            if insertafter:
                # + 1 for the next line
                index[1] = lineno + 1
                if firstmatch:
                    break
            if insertbefore:
                # index[1] for the previous line
                index[1] = lineno
                if firstmatch:
                    break
    msg = ''
    changed = False
    b_linesep = os.linesep.encode(errors='surrogate_or_strict')
    # Regexp matched a line in the file
    if index[0] != -1:
        if backrefs:
            b_new_line = m.expand(b_line)
        else:
            # Don't do backref expansion if not asked.
            b_new_line = b_line

        if not b_new_line.endswith(b_linesep):
            b_new_line += b_linesep

        # If no regexp was given and a line match is found anywhere in the file,
        # insert the line appropriately if using insertbefore or insertafter
        if regexp is None and m:

            # Insert lines
            if insertafter and insertafter != 'EOF':
                # Ensure there is a line separator after the found string
                # at the end of the file.
                if b_lines and not b_lines[-1][-1:] in ('\n', '\r'):
                    b_lines[-1] = b_lines[-1] + b_linesep

                # If the line to insert after is at the end of the file
                # use the appropriate index value.
                if len(b_lines) == index[1]:
                    if b_lines[index[1] - 1].rstrip('\r\n') != b_line:
                        b_lines.append(b_line + b_linesep)
                        msg = 'line added'
                        changed = True
                elif b_lines[index[1]].rstrip('\r\n') != b_line:
                    b_lines.insert(index[1], b_line + b_linesep)
                    msg = 'line added'
                    changed = True

            elif insertbefore and insertbefore != 'BOF':
                # If the line to insert before is at the beginning of the file
                # use the appropriate index value.
                if index[1] == 0:
                    if b_lines[index[1]].rstrip('\r\n') != b_line:
                        b_lines.insert(index[1], b_line + b_linesep)
                        msg = 'line replaced'
                        changed = True

                elif b_lines[index[1] - 1].rstrip('\r\n') != b_line:
                    b_lines.insert(index[1], b_line + b_linesep)
                    msg = 'line replaced'
                    changed = True

        elif b_lines[index[0]] != b_new_line:
            b_lines[index[0]] = b_new_line
            msg = 'line replaced'
            changed = True

    elif backrefs:
        # Do absolutely nothing, since it's not safe generating the line
        # without the regexp matching to populate the backrefs.
        pass
    # Add it to the beginning of the file
    elif insertbefore == 'BOF' or insertafter == 'BOF':
        b_lines.insert(0, b_line + b_linesep)
        msg = 'line added'
        changed = True
    # Add it to the end of the file if requested or
    # if insertafter/insertbefore didn't match anything
    # (so default behaviour is to add at the end)
    elif insertafter == 'EOF' or index[1] == -1:

        # If the file is not empty then ensure there's a newline before the added line
        if b_lines and not b_lines[-1][-1:] in ('\n', '\r'):
            b_lines.append(b_linesep)

        b_lines.append(b_line + b_linesep)
        msg = 'line added'
        changed = True
    # insert matched, but not the regexp
    else:
        b_lines.insert(index[1], b_line + b_linesep)
        msg = 'line added'
        changed = True

    #if module._diff:
    #    diff['after'] = to_native(b('').join(b_lines))

    backupdest = ""
    if changed: # and not module.check_mode:
        #if backup and os.path.exists(dest):
        #    backupdest = module.backup_local(dest)
        logging.info("Changed True")
        write_changes(b_lines, dest)

    #if module.check_mode and not os.path.exists(b_dest):
    #    module.exit_json(changed=changed, msg=msg, backup=backupdest, diff=diff)

    #attr_diff = {}
    #msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    #attr_diff['before_header'] = '%s (file attributes)' % dest
    #attr_diff['after_header'] = '%s (file attributes)' % dest

    #difflist = [diff, attr_diff]
    #module.exit_json(changed=changed, msg=msg, backup=backupdest, diff=difflist)


def absent(dest, regexp, line, backup):
    logger.debug("absent")
    b_dest = dest.encode(errors='surrogate_or_strict')
    if not os.path.exists(b_dest):
        logger.error(msg="file not present")
        exit(1)

    msg = ''
    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    f = open(b_dest, 'rb')
    b_lines = f.readlines()
    f.close()

    #if module._diff:
    #    diff['before'] = to_native(b('').join(b_lines))

    if regexp is not None:
        bre_c = re.compile(regexp.encode(errors='surrogate_or_strict'))
    found = []

    b_line = line.encode(errors='surrogate_or_strict')

    def matcher(b_cur_line):
        if regexp is not None:
            match_found = bre_c.search(b_cur_line)
        else:
            match_found = b_line == b_cur_line.rstrip('\r\n')
        if match_found:
            found.append(b_cur_line)
        return not match_found

    b_lines = [l for l in b_lines if matcher(l)]
    changed = len(found) > 0

    #if module._diff:
    #    diff['after'] = to_native(b('').join(b_lines))

    backupdest = ""
    if changed: # and not module.check_mode:
    #    if backup:
    #        backupdest = module.backup_local(dest)
        write_changes(b_lines, dest)

    if changed:
        msg = "%s line(s) removed" % len(found)

    #attr_diff = {}
    #msg, changed = check_file_attrs(changed, msg, attr_diff)

    #attr_diff['before_header'] = '%s (file attributes)' % dest
    #attr_diff['after_header'] = '%s (file attributes)' % dest

    #difflist = [diff, attr_diff]

    #module.exit_json(changed=changed, found=len(found), msg=msg, backup=backupdest, diff=difflist)

def lineinfile(create, backup, backrefs, path, firstmatch, regexp, line, insert_before=None, insert_after=None, state='present'):
    if regexp == '':
        logger.warn(
            "The regular expression is an empty string, which will match every line in the file. "
            "This may have unintended consequences, such as replacing the last line in the file rather than appending. "
            "If this is desired, use '^' to match every line in the file and avoid this warning.")

    b_path = path.encode(errors='surrogate_or_strict')
    if os.path.isdir(b_path):
        logger.error(rc=256, msg='Path %s is a directory !' % path)
        exit(1)

    if state == 'present':
        if backrefs and regexp is None:
            logger.error('regexp is required with backrefs=true')
            exit(1)
        if line is None:
            logger.error('line is required with state=present')
            exit(1)
        # Deal with the insertafter default value manually, to avoid errors
        # because of the mutually_exclusive mechanism.
        ins_bef, ins_aft = insert_before, insert_after
        if ins_bef is None and ins_aft is None:
            ins_aft = 'EOF'

        present(path, regexp, line,
                ins_aft, ins_bef, create, backup, backrefs, firstmatch)
    else:
        if regexp is None and line is None:
            logger.error('one of line or regexp is required with state=absent')

        absent(path, regexp, line, backup)