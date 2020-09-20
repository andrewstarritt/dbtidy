""" This module provides an abstraction around a statndard file type that
    allws the reading of lexical items (as opposed to lines etc.)
"""

from collections import namedtuple
from . import ordered_enum
from . import common

OrderedEnum = ordered_enum.OrderedEnum

lex_values = ("Lk_Void",         # use as an initialiser, a quazi None
              "Lk_End_Of_File",  # end of file, indicates no more data.
              "Lk_Comment",      # starting with # to end of line
              #
              "Lk_Identifier",   # record type names e.g. ai, calc, mbbo
                                 # and field names VAL, SCAN etc., also Q:group and the like
              "Lk_String",       # "includes the quotes"
              "Lk_Number",       # 0-9[.0-9[E[+/-]0-9]] - excludes preceeding +/-
              "Lk_Open_Round",   # (
              "Lk_Close_Round",  # )
              "Lk_Open_Square",  # [
              "Lk_Close_Square", # ]
              "Lk_Open_Brace",   # {
              "Lk_Close_Brace",  # }
              "Lk_Comma",        # ,
              "Lk_Plus",         # +/- - rebadge to Lk_Sign
              "Lk_Macro",        # includes the $( and )
              "Lk_Other",        # any other arbitary character
              #
              # Reserved words
              #
              "Rw_Alias",
              "Rw_Field",
              "Rw_Info",
              "Rw_Function",
              "Rw_Record",
              "Rw_Grecord",
              "Rw_Device",
              "Rw_Driver",
              "Rw_Registrar",
              "Rw_Variable",
              #
              "Rw_Asl",
              "Rw_Choice",
              "Rw_Extra",
              "Rw_Include",
              "Rw_Initial",
              "Rw_Interest",
              "Rw_Menu",
              "Rw_Pp",
              "Rw_Prompt",
              "Rw_Prompt_Group",
              "Rw_Record_Type",
              "Rw_Size",
              "Rw_Special")

lex_kinds = OrderedEnum("lex_kinds", lex_values)

# Defines a lexical item
#
lex_items = namedtuple("lex_items", ("kind", "value", "line_number", "col_number"))

def lex_item_image(self):
    vtext ="'%s'" % self.value
    return "%-16s %-32s %s:%d:%d" % (self.kind.name, vtext, 
           common.source_file_name, self.line_number, self.col_number)

# monkey patch the __str__ function
#
lex_items.__str__ = lex_item_image


# -----------------------------------------------------------------------------
#
class lex_file (object):

    def __init__(self, filename):
        self.filename = filename
        self.buffer = ""
        self.line_number = 0
        self.col_number = 0
        self.source = open(self.filename, 'r')


    def __enter__(self):
        return self


    def __exit__(self, ex_type, ex_value, traceback):
        self.close()


    def close(self):
        self.source.close()


    def get_next_line(self):
        while True:
            # Read the next line from the file.
            #
            line = self.source.readline()
            self.line_number += 1
            self.col_number = 1

            if line == '':
                # Empty string indicates end of file
                #
                return (True, "")

            # Trim leading white space inc. tracking ol number.
            #
            while len(line) >= 1 and line[0] in (' ', '\t'):
                line = line [1:]
                self.col_number += 1
                
            # Remove trailing white space, including any '\n' character
            #
            line = line.rstrip()
            
            if len (line) > 0:
                return (False, line)


    def get_next_lexical_item(self):
        """ Gets the next lexical item from the file or returns an end of file
            indicator. Reads one or more lines form the file if needs be.
        """
        kind = lex_kinds.Lk_Void
        value = ""
        next = 0
                
        # Any input left in the buffer?
        #
        if self.buffer == "":
            # Buffer is empty.
            #
            eof, self.buffer = self.get_next_line()
            if eof:
                kind = lex_kinds.Lk_End_Of_File
                return lex_items(kind, value, self.line_number, self.col_number)


        # c is first character of item, next points to following character.
        # lex item is at least one character
        #
        c = self.buffer[0]
        next = 1

#       print (c, next, self.buffer)

        # Oh how I would kill for a case statement
        #
        if c == '(':
            kind = lex_kinds.Lk_Open_Round

        elif c == ')':
            kind = lex_kinds.Lk_Close_Round

        elif c == '[':
            kind = lex_kinds.Lk_Open_Square

        elif c == ']':
            kind = lex_kinds.Lk_Close_Square

        elif c == '{':
            kind = lex_kinds.Lk_Open_Brace

        elif c == '}':
            kind = lex_kinds.Lk_Close_Brace

        elif c == ',':
            kind = lex_kinds.Lk_Comma

        elif c in ('+','-'):
            # +/-.
            #
            kind = lex_kinds.Lk_Plus    


        elif c.isnumeric():
            # Number
            #
            kind = lex_kinds.Lk_Number
            
            # Integer part
            #
            while next < len(self.buffer) and self.buffer[next].isnumeric():
                next += 1
                
            if next < len(self.buffer) and self.buffer[next] == ".":
                next += 1
                
            # Fractional part
            while next < len(self.buffer) and self.buffer[next].isnumeric():
                next += 1
                    
            if  next < len(self.buffer) and self.buffer[next] in ('e','E'):
                next += 1

            if  next < len(self.buffer) and self.buffer[next] in ('+','-'):
                next += 1

            # Exponent part
            while next < len(self.buffer) and self.buffer[next].isnumeric():
                next += 1
                

        elif c.isalpha():
            # identifier or reserved word.
            #
            while next < len(self.buffer) and \
                    self.is_identifier_char(self.buffer[next]):
                next += 1

            value = self.buffer[0:next]
            kind = self.is_resererved_word(value)
            if kind is None:
                kind = lex_kinds.Lk_Identifier

        elif c == '"':
            # quote
            kind = lex_kinds.Lk_String

            # A string is of the form "", "XXXX", or "XXX\"XXX"
            # Two quotes "" in a string are NOT interpreted as a single
            # quote by dbLoadRecord.
            #
            back_slash_count = 0
            while True:
                if next >= len(self.buffer):
                    break

                d = self.buffer[next]
                if d == '\\':
                    back_slash_count = (back_slash_count + 1) % 2
                elif d != '"':
                    back_slash_count = 0

                # Advance
                #
                next += 1

                # Was previous charactcer a quote?
                #
                if d == '"':
                    # Yes - posible end of line.
                    #
                    if back_slash_count == 0:
                        # All done if not masked, i.e. even number of \\.
                        #
                        break

        elif c == '$':
            # Macro  $(XXX)
            # TODO: Macro with default, $(XXX=YYY)
            #
            if next < len(self.buffer) and self.buffer[next] == '(':
                kind = lex_kinds.Lk_Macro

                next += 1   # skip the (

                while next < len(self.buffer) and self.buffer[next] != ')':
                    next += 1

                next += 1   # skip the )

            else:
                kind = lex_kinds.Lk_Other

        elif c == '#':
            kind = lex_kinds.Lk_Comment
            next = len(self.buffer)

        else:
            # some unexpected arbitary character.
            #
            kind = lex_kinds.Lk_Other


        value = self.buffer[0:next]
        result = lex_items(kind, value, self.line_number, self.col_number)

        # Remove the value from the buffer.
        #
        self.buffer = self.buffer[next:]
        self.col_number += next

        # Trim any white space
        #
        while len(self.buffer) >= 1 and self.buffer[0] in (' ', '\t'):
            self.buffer = self.buffer [1:]
            self.col_number += 1
        
        return result


    def is_resererved_word(self, word):
        """ if is a resered form, returns the associated lext kind,
            otherwise retuens None
        """
        word = word.lower()
        return reserved_words.get(word, None)

    def is_identifier_char(self, char):
        # We allow colon, for stuff like Q:group
        #
        return char.isalpha() or char.isnumeric() or char == ':'


reserved_words = {
    "alias":       lex_kinds.Rw_Alias,
    "field":       lex_kinds.Rw_Field,
    "info":        lex_kinds.Rw_Info,
    "function":    lex_kinds.Rw_Function,
    "record":      lex_kinds.Rw_Record,
    "grecord":     lex_kinds.Rw_Grecord,
    "device":      lex_kinds.Rw_Device,
    "driver":      lex_kinds.Rw_Driver,
    "registrar":   lex_kinds.Rw_Registrar,
    "variable":    lex_kinds.Rw_Variable,
    #
    "asl":         lex_kinds.Rw_Asl,
    "choice":      lex_kinds.Rw_Choice,
    "extra":       lex_kinds.Rw_Extra,
    "include":     lex_kinds.Rw_Include,
    "initial":     lex_kinds.Rw_Initial,
    "interest":    lex_kinds.Rw_Interest,
    "menu":        lex_kinds.Rw_Menu,
    "pp":          lex_kinds.Rw_Pp,
    "prompt":      lex_kinds.Rw_Prompt,
    "promptgroup": lex_kinds.Rw_Prompt_Group,
    "recordtype":  lex_kinds.Rw_Record_Type,
    "size":        lex_kinds.Rw_Size,
    "special":     lex_kinds.Rw_Special
}


# end
