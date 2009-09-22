#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Generates and decodes a unique ID, which can use characters to shorten its
    length.

     Author: Will Hardy
       Date: December 2008
      Usage: >>> encode(1)
             "KSR68"
Description: Invoice numbers like "0000004" are unprofessional in that they 
             expose how many sales a system has made, and can be used to monitor
             the rate of sales over a given time.  They are also harder for 
             customers to read back to you, especially if they are 10 digits 
             long.  
             These functions convert an integer (from eg an ID AutoField) to a
             short unique string. This is done simply using a perfect hash
             function and converting the result into a string of user friendly
             characters.

"""
import math

# If django is available for settings, import some defaults
# Alpha numeric characters, only uppercase, no confusing values (eg 1/I,0/O,Z/2)
# Remove some letters if you prefer more numbers in your strings
# You may wish to remove letters that sound similar, to avoid confusion when a
# customer calls on the phone (B/P, M/N, 3/C/D/E/G/T/V)
DEFAULT_VALID_CHARS = "3456789ACDEFGHJKLQRSTUVWXY"
# This just means we don't start with the first number, to mix things up
DEFAULT_OFFSET_PERCENT = 30
# Don't set this, it isn't necessary and you'll get ugly strings like 'AAAAAB3D'
# String length is automatically determined. Use only in an emergency
DEFAULT_STRING_LENGTH = None
# This minimum length is used to automatically determine the string length, if
# it is not set. For 26 characters, a length 5 string will represent about 11
# million, which is enough for most tasks. The size is increased to match the 
# order.
DEFAULT_MINIMUM_LENGTH = 5

try:
    from django.conf import settings
    DEFAULT_VALID_CHARS = getattr(settings, 'FRIENDLY_ID_VALID_CHARS', DEFAULT_VALID_CHARS)
    DEFAULT_OFFSET_PERCENT = getattr(settings, 'FRIENDLY_ID_OFFSET_PERCENT', DEFAULT_OFFSET_PERCENT)
    DEFAULT_STRING_LENGTH = getattr(settings, 'FRIENDLY_ID_STRING_LENGTH', DEFAULT_STRING_LENGTH)
    DEFAULT_MINIMUM_LENGTH = getattr(settings, 'FRIENDLY_ID_MINIMUM_LENGTH', DEFAULT_MINIMUM_LENGTH)
except ImportError:
    pass


class FriendlyID(object):
    def __init__(self, offset_percent=None, valid_chars=None, string_length=None, minimum_length=5):

        self.valid_chars = valid_chars or DEFAULT_VALID_CHARS
        # For convenience and speed
        self.number_valid_chars = len(self.valid_chars)

        minimum_length = minimum_length or DEFAULT_MINIMUM_LENGTH
        self.minimum_size = self.number_valid_chars ** minimum_length - 1

        # This just means we don't start with the first number, to mix things up
        self.offset_percent = offset_percent or DEFAULT_OFFSET_PERCENT

        # This is used to store already calculated periods, for speed and consistency
        self._period_cache = {}
        self._offset_cache = {}

        # Don't set this, it isn't necessary and you'll get ugly strings like 'AAAAAB3D'
        # String length is automatically determined. Use only in an emergency
        self.string_length = string_length or DEFAULT_STRING_LENGTH

    def get_size(self, num):
        " Returns the size of the field for the given number. "
        possible_size = self.minimum_size
        while num > possible_size:
            possible_size *= self.number_valid_chars
        return possible_size

    def get_period(self, size):
        """ Automatically find a suitable period to use.
            Factors are best, because they will have 1 left over when 
            dividing SIZE+1.
            This only needs to be run once, on import.
        """
        # Check in the cache first
        if size in self._period_cache:
            return self._period_cache[size]

        # The highest acceptable factor will be the square root of the size.
        highest_acceptable_factor = int(math.sqrt(size))
    
        # Too high a factor (eg SIZE/2) and the interval is too small, too 
        # low (eg 2) and the period is too small.
        # We would prefer it to be lower than the number of VALID_CHARS, but more
        # than say 4.
        # Each is done separately for efficiency
        starting_point = len(self.valid_chars) > 14 and len(self.valid_chars)/2 or 13
        for p in xrange(starting_point, 7, -1):
            # If p is a factor
            if size % p == 0:
                # Save to the cache and return
                self._period_cache[size] = p
                return p
        for p in xrange(highest_acceptable_factor, starting_point+1, -1):
            if size % p == 0:
                self._period_cache[size] = p
                return p
        for p in [6,5,4,3,2]:
            if size % p == 0:
                self._period_cache[size] = p
                return p
        raise Exception, "No valid period could be found for SIZE=%d.\n" \
                         "Try avoiding prime numbers :-)" % SIZE

    def get_offset(self, size):
        return size * self.offset_percent / 100 - 1 
    
    def perfect_hash(self, num, size):
        """ Translate a number to another unique number, using a perfect hash function.
        """
        period = self.get_period(size)
        offset = self.get_offset(size)
        return ((num+offset)*(size/period)) % (size+1) + 1
    
    def friendly_string(self, num, size):
        """ Convert a base 10 number to a base X string.
            Charcters from VALID_CHARS are chosen, to convert the number 
            to eg base 24, if there are 24 characters to choose from.
            Use valid chars to choose characters that are friendly, avoiding
            ones that could be confused in print or over the phone.
        """
        # Convert to a (shorter) string for human consumption
        string = ""
        # The length of the string can be determined by self.string_length or by how many
        # characters are necessary to present a base 30 representation of SIZE.
        while self.string_length and len(string) <= self.string_length \
                    or self.number_valid_chars**len(string) <= size:
            # PREpend string (to remove all obvious signs of order)
            string = self.valid_chars[num % self.number_valid_chars] + string
            num = num / self.number_valid_chars
        return string
    
    def encode(self, num):
        """ Encode a simple number, using a perfect hash and converting to a 
            more user friendly string of characters.
        """
        # Check the number is within our working range
        if num < 0: return None

        size = self.get_size(num)
        hash = self.perfect_hash(num, size)
        return self.friendly_string(hash, size)
    

def test(max_number):
    """ Test every single value for uniqueness and that they are properly decoded.
        This can take some time for large SIZE values, but need only be done once
        if the settings do not change.
    """
    fi = FriendlyID()

    # Check all numbers are unique
    from collections import defaultdict
    a = defaultdict()
    for i in range(max_number+1):
        if fi.encode(i) in a:
            print a
            return False
        a[fi.encode(i)] = i

    return True

def performance_test(num=None):
    """ Run test for the given data to test system performance. 
        (This is used for developing optimisations)
    """
    if not num:
        num = 5000
    from timeit import Timer
    t = Timer("test(%s)" % num, "from __main__ import test")
    print t.timeit(number=1)


if __name__ == '__main__':
    print "Here's a quick demonstration:"
    fi = FriendlyID()
    print 1, fi.encode(1)
    print 2, fi.encode(2)
    print 3, fi.encode(3)
    print 3, fi.encode(3)
    print 0, fi.encode(0)
    print -1, fi.encode(-1)
    print "26**5-1", fi.encode(26**5-1)
    print "26**5  ", fi.encode(26**5)
    print "big number     ", fi.encode(9999999999999999999999999999999999999999999999999999999999)
    print "same big number", fi.encode(9999999999999999999999999999999999999999999999999999999999)
    #assert test(50000)

