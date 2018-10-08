# Line in file

Это копия модуля для ansible адаптированная под Python 3 для использования в скриптах

###В настроящее время не работает:
  - Валидация
  - Backup

##Description:
  - This module ensures a particular line is in a file, or replace an
    existing line using a back-referenced regular expression.
  - This is primarily useful when you want to change a single line in
    a file only. See the M(replace) module if you want to change
    multiple, similar lines or check M(blockinfile) if you want to insert/update/remove a block of lines in a file.
    For other cases, see the M(copy) or M(template) modules.
version_added: "0.7"
options:
  path:
    description:
      - The file to modify.
      - Before 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    aliases: [ dest, destfile, name ]
    required: true
  regexp:
    description:
      - The regular expression to look for in every line of the file. For
        C(state=present), the pattern to replace if found. Only the last line
        found will be replaced. For C(state=absent), the pattern of the line(s)
        to remove. Uses Python regular expressions.
        See U(http://docs.python.org/2/library/re.html).
    version_added: '1.7'
  state:
    description:
      - Whether the line should be there or not.
    choices: [ absent, present ]
    default: present
  line:
    description:
      - Required for C(state=present). The line to insert/replace into the
        file. If C(backrefs) is set, may contain backreferences that will get
        expanded with the C(regexp) capture groups if the regexp matches.
  backrefs:
    description:
      - Used with C(state=present). If set, C(line) can contain backreferences
        (both positional and named) that will get populated if the C(regexp)
        matches. This flag changes the operation of the module slightly;
        C(insertbefore) and C(insertafter) will be ignored, and if the C(regexp)
        doesn't match anywhere in the file, the file will be left unchanged.
        If the C(regexp) does match, the last matching line will be replaced by
        the expanded line parameter.
    type: bool
    default: 'no'
    version_added: "1.1"
  insertafter:
    description:
      - Used with C(state=present). If specified, the line will be inserted
        after the last match of specified regular expression.
        If the first match is required, use(firstmatch=yes).
        A special value is available; C(EOF) for inserting the line at the
        end of the file.
        If specified regular expression has no matches, EOF will be used instead.
        May not be used with C(backrefs).
    choices: [ EOF, '*regex*' ]
    default: EOF
  insertbefore:
    description:
      - Used with C(state=present). If specified, the line will be inserted
        before the last match of specified regular expression.
        If the first match is required, use(firstmatch=yes).
        A value is available; C(BOF) for inserting the line at
        the beginning of the file.
        If specified regular expression has no matches, the line will be
        inserted at the end of the file.  May not be used with C(backrefs).
    choices: [ BOF, '*regex*' ]
    version_added: "1.1"
  create:
    description:
      - Used with C(state=present). If specified, the file will be created
        if it does not already exist. By default it will fail if the file
        is missing.
    type: bool
    default: 'no'
  backup:
     description:
       - Create a backup file including the timestamp information so you can
         get the original file back if you somehow clobbered it incorrectly.
     type: bool
     default: 'no'
  firstmatch:
    description:
      - Used with C(insertafter) or C(insertbefore). If set, C(insertafter) and C(inserbefore) find
        a first line has regular expression matches.
    type: bool
    default: 'no'
    version_added: "2.5"
  others:
     description:
       - All arguments accepted by the M(file) module also work here.