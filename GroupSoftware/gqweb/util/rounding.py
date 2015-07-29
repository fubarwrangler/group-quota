# ===========================================================================
# Function to preform a fair-election among floating point values that keeps
# the sum constant.
#
# Algorithm inspired by: http://stackoverflow.com/questions/13483430/
#   1. Round down all numbers
#   2. Sum them up and subtract from the total to get remainder R
#   3. For the top R values sorted by decimal part add one.
#
# (C) 2015 William Strecker-Kellogg <willsk@bnl.gov>
# ===========================================================================
from math import floor


def largest_remainder(data, total):
    """ Preform fair-election on @data, adjusting so all end up as int() and
        the sum is maintained

        @data: list of floatint point numbers
        @total: what the final sum should be (== sum(data) mostly)
    """
    ifloor = lambda x: int(floor(x))

    new_data = map(ifloor, data)
    partial = sum(new_data)

    # How many extra integers to give out
    extra = total - partial

    # In largest decimal order
    decimal_order = map(ifloor, sorted(data, key=lambda x: floor(x) - x))

    n = 0
    while extra > 0.0:
        new_data[new_data.index(decimal_order[n])] += 1
        extra -= 1
        n += 1

    return new_data
