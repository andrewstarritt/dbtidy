""" Provides an order enum type, essentially as suggested in:
    https://docs.python.org/3.6/library/enum.html#orderedenum
"""

import enum       # back port of enum34

class OrderedEnum (enum.Enum):

    """Allows enum < enum etc.., useful for sorts."""

    # -------------------------------------------------------------------------
    #
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    # -------------------------------------------------------------------------
    #
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    # -------------------------------------------------------------------------
    #
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    # -------------------------------------------------------------------------
    #
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

# end
