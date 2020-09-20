""" This module provided the main dbtidy logic.
"""

import sys

from . import ordered_enum
from . import lexer
from . import common

OrderedEnum = ordered_enum.OrderedEnum
lex_kinds = lexer.lex_kinds
lex_items = lexer.lex_items
lex_file  = lexer.lex_file


def warning(lex_item, text):
    sys.stderr.write("warning >>> %s:%d:%d:%s\n" %
                     (common.source_file_name, lex_item.line_number, lex_item.col_number, text))


class AnyClass (object):
    """ Singleton class, sort of like None, but represents any value.
    """
    def __init__(self):
        pass

    def __str__(self):
        return 'Any'


Any = AnyClass()
del AnyClass


# -----------------------------------------------------------------------------
# Index by (prev kind, current kind)
#
gaps = {
    (Any,                     lex_kinds.Lk_Comment):     2,
    (lex_kinds.Lk_Open_Round, Any):                      0,
    (Any,                     lex_kinds.Lk_Close_Round): 0,
    (Any,                     lex_kinds.Lk_Comma):       0,
    (lex_kinds.Lk_Comma,      Any):                      1,
    (lex_kinds.Lk_Plus,       lex_kinds.Lk_Identifier):  0,
    (Any,                     Any):                      1
}


# -----------------------------------------------------------------------------
#
def lex_gap(a, b):
    """ Returns the required gap between two lexical kinds. 
    """
    if (a, b) in gaps:
        gap = gaps[(a, b)]

    elif (Any, b) in gaps:
        gap = gaps[(Any, b)]

    elif (a, Any) in gaps:
        gap = gaps[(a, Any)]

    else:
        gap = 1

    return " " * gap


# -----------------------------------------------------------------------------
#
def process(source, target):
    """ Main tidy functionality here. 
    """

    rw_field_indent = 4
    field_value_indent = 17
    same_line_comment = 41

    # Comments starting with this sequences of charcters are meta
    # directives used for archiving, autosaving etc.
    #
    meta = "#!!"

    modes = OrderedEnum("modes",
                        ("Void", "Record_Type_Spec", "Record_Spec"))

    states = OrderedEnum("states",
                         ("Void", "Record_Name", "Field_Name", "Field_Value"))

    is_new_line = True
    line_length = 0

    def new_line():
        nonlocal is_new_line
        nonlocal line_length

        target.write('\n')
        line_length = 0
        is_new_line = True

    do_new_line = False
    do_blank_line = False
    offset = 0

    indent = 0
    mode = modes.Void
    state = states.Void

    comment_block = True
    is_new_line = True
    line_length = 0

    prev_item = lex_items(lex_kinds.Lk_Void, "", 1, 1)

    lex_item = source.get_next_lexical_item()
#   print(lex_item)
    
    while lex_item.kind != lex_kinds.Lk_End_Of_File:

        # Allow peek at next item - currently not used
        #
        next_item = source.get_next_lexical_item()

        # Pre-processing of lexical item - phase 1
        #
        if lex_item.kind == lex_kinds.Lk_Identifier:
            if state == states.Field_Name:
                if lex_item.value != lex_item.value.upper():
                    warning(lex_item, "field name not upper case: %s" % lex_item.value)

                if len(lex_item.value) < 1 or len(lex_item.value) > 4:
                    warning(lex_item, "field name too long or empty: %s" % lex_item.value)

        elif lex_item.kind >= lex_kinds.Rw_Alias and lex_item.kind <= lex_kinds.Rw_Special:
            lex_item = lex_items(lex_item.kind, lex_item.value.lower(),
                                 lex_item.line_number, lex_item.col_number)

        # Pre-processing of lexical item - phase 2
        #
        do_new_line = False
        do_blank_line = False
        offset = 0

        # If input file has at least one blank line
        # then preserve line.
        #
        if lex_item.line_number > prev_item.line_number + 1:
            do_blank_line = True

        # Pre-processing of lexical item - phase 3
        #
        if lex_item.kind == lex_kinds.Lk_Comment:
            if not comment_block:
                # check for end of line comment.
                #
                if lex_item.line_number == prev_item.line_number:
                    offset = same_line_comment - indent
                else:
                    do_blank_line = True

            # Do a special for the meta comments
            #
            if lex_item.value.startswith(meta):
                offset = -indent

        elif lex_item.kind == lex_kinds.Lk_Open_Brace:
            indent += rw_field_indent

        elif lex_item.kind == lex_kinds.Lk_Close_Brace:
            do_new_line = True
            indent = max(0, indent - rw_field_indent)

        elif lex_item.kind == lex_kinds.Lk_Identifier:
            # state machine change.
            #
            if state == states.Field_Name:
                state = states.Field_Value
            elif state == states.Field_Value:
                offset = field_value_indent - indent
                state = states.Void

        elif lex_item.kind == lex_kinds.Lk_String:
            # state machine change.
            #
            if state == states.Field_Value:
                offset = field_value_indent - indent
                state = states.Void

        elif lex_item.kind == lex_kinds.Lk_Macro:
            # honour new line.
            #
            if lex_item.line_number > prev_item.line_number:
                do_new_line = True
                offset = -indent

        elif lex_item.kind in (lex_kinds.Rw_Record, lex_kinds.Rw_Grecord):
            if not comment_block:
                do_blank_line = True

            do_new_line = True
            state = states.Record_Name
            mode = modes.Record_Spec

        elif lex_item.kind in (lex_kinds.Rw_Alias, lex_kinds.Rw_Device,
                               lex_kinds.Rw_Driver, lex_kinds.Rw_Function,
                               lex_kinds.Rw_Registrar, lex_kinds.Rw_Variable):
            do_new_line = True

        elif lex_item.kind == lex_kinds.Rw_Record_Type:
            if not comment_block:
                do_blank_line = True

            do_new_line = True
            state = states.Record_Name
            mode = modes.Record_Type_Spec

        elif lex_item.kind in (lex_kinds.Rw_Field, lex_kinds.Rw_Info):
            if mode == modes.Record_Type_Spec and not comment_block:
                do_blank_line = True
            else:
                # Honor same line for preceeding macro
                #
                if prev_item.kind != lex_kinds.Lk_Macro or \
                   lex_item.line_number > prev_item.line_number:
                    do_new_line = True

            # Next name (identifier) is field name.
            #
            state = states.Field_Name

        elif lex_item.kind in (lex_kinds.Rw_Asl, lex_kinds.Rw_Choice,
                               lex_kinds.Rw_Extra, lex_kinds.Rw_Include,
                               lex_kinds.Rw_Initial, lex_kinds.Rw_Interest,
                               lex_kinds.Rw_Menu, lex_kinds.Rw_Pp,
                               lex_kinds.Rw_Prompt, lex_kinds.Rw_Prompt_Group,
                               lex_kinds.Rw_Size, lex_kinds.Rw_Special):
            do_new_line = True

        # end phase 3

        # Output the pre-lexical white space.
        #
        if do_blank_line:
            if not is_new_line:
                new_line()
            new_line()

        elif do_new_line:
            if not is_new_line:
                new_line()

        if is_new_line:
            temp = max(0, indent + offset)
            target.write(' ' * temp)
            line_length = temp

        else:
            gap = lex_gap(prev_item.kind, lex_item.kind)
            target.write(gap)
            line_length += len(gap)

            if indent + offset > line_length:
                temp = indent + offset - line_length
                target.write(' ' * temp)
                line_length += temp

        # Output the lexical item.
        #
        target.write(lex_item.value)
        line_length += len(lex_item.value)
        is_new_line = False

        # post-processing of lexical item.
        #
        comment_block = False

        if lex_item.kind == lex_kinds.Lk_Comment:
            new_line()
            comment_block = True

        elif lex_item.kind in (lex_kinds.Lk_Open_Brace, lex_kinds.Lk_Close_Brace):
            new_line()

        # update for next iteration
        #
        prev_item = lex_item
        lex_item = next_item
#       print(lex_item)

    if not is_new_line:
        new_line()


# -----------------------------------------------------------------------------
#
def process_file(source_filename, target_filename):
    """ Handles file opening/closeing
    """
    with lex_file(source_filename) as source:
        with open(target_filename, 'w') as target:
            process(source, target)

# end
