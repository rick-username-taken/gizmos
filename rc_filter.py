#!/usr/bin/env python3
""" RC Filter Calculator

Handy dandy filter calculator.

Input two values, get the third.


Design goals:
Accepts capacitance, resistance, or frequency
    Possibly accept note in lieu of frequency
    Possibly output nearest note in addition to frequency
Accepts and returns standard value range metric prefixes
    M, k, m, u, n, p
    Possibly accept full written prefix (but probably not, lol)
    Possibly detect mu character at input and replace with u
        Useful if copying value from source using mu
    Possibly snap capacitance/resistance to nearest E series values
    Possibly allow for multiple E series values
Use 3 significant figures
Create class for filter objects?
    Would be beneficial down the line - 
    Supporting multiple filter types and configurations
    Possibly better solution than using dictionaries to track values...


Relevant Formulae:
f = 1/(2*pi*R*C)
R = (1/f)/(2*pi*C)
C = (1/f)/(2*pi*R)


Bug tracking:
    PRECISION WOES
    ./rc_filter.py 200ko 20kHz
    200000.0
    20000.0
    -12 1e-12
    39.800000000000004
    You will need a 39.800000000000004p farad capacitor.

    sig_fig 'value' after logic block: 3.978873577297384e-11
    sig_fig 'x' after format string and after float operation: 3.98e-11

    might be worth checking out the decimal module
    oh, fixed it, just needed to add a sig_fig on the exponent-stripped
    value in add_prefix


References:
    E series values and calculation thereof:
    https://en.wikipedia.org/wiki/E_series_of_preferred_numbers

    Cute significant figure formatting:
    https://stackoverflow.com/a/48812729/3597218
    Note that there is a sigfig module, but I want to minimize imports
    There is also a non-standard to-precision module
    Alternate solution: https://stackoverflow.com/a/49810920/3597218

    magnitude, si-prefix, pint, and QuantiPhy are modules for managing metric
    prefixes, in case you want to upgrade the dictionary approach

    Force standard notation output (rather than scientific):
    https://stackoverflow.com/a/37736333/3597218


Usage:
    rc_filter.py value_1 value_2
    Given two values, solve for remaining value in RC filter

    Values must conform to one of the following formats:
        [number][metric prefix][unit]
        [number][unit]
    Numbers may be integers or floats.
    Accepted prefixes are p, n, u, m, k, M. Case-sensitive.
    Accepted units are o, ohms, f, farads, hz, hertz. Not case-sensitive.
    Designed to ignore whitespace.
    Not designed for high precision!

"""

from math import pi
import sys


def get_frequency(resistance, capacitance):
    """ Provided resistance and capacitance, return frequency
    """
    f = 1/(2*pi*resistance*capacitance)  # pylint: disable=C0103
    return f


def get_component(frequency, component):
    """ Provided frequency and either component value, return remaining value
    """
    x = (1/frequency)/(2*pi*component)  # pylint: disable=C0103
    return x


def sig_fig(value):
    """ Returns int or float x formatted to 3 significant figures """
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            print('Input not recognized.')
    x = f'{float(f"{value:.3g}"):g}'  # pylint: disable=C0103
    x = float(x)  # pylint: disable=C0103
    # unnecessary typing, perhaps
    if int(x) == x:
        x = int(x)  # pylint: disable=C0103
    return x


def input_tidy(value):
    """ Ensures arguments fit expected formatting
    No whitespace, all lowercase except M
    Shortens written units
    """
    x = ''  # pylint: disable=C0103
    # originally had .lower before the split, but causes issues with M/mega
    # then found that without lower, Hz would give unexpected results
    # so I had to finger it out
    x = ''.join(value.split())  # pylint: disable=C0103
    if x.find('M') != x.lower().find('M'):
        mega = x.find('M')
        x = list(x.lower())  # pylint: disable=C0103
        x[mega] = 'M'
        x = ''.join(x)  # pylint: disable=C0103
    else:
        x = x.lower()  # pylint: disable=C0103
    if isinstance(value, str) and len(value) >= 2:
        if x.find('o') != -1:
            x = x[:x.find('o')+1]  # pylint: disable=C0103
        elif x.find('h') != -1:
            x = x[:x.find('h')+1]+'z'  # pylint: disable=C0103
        elif x.find('f') != -1:
            x = x[:x.find('f')+1]  # pylint: disable=C0103
        else:
            raise ValueError(f'Unit not recognized in argument {value}.')
    else:
        raise Exception(f'Invalid argument {value}: missing units.')
    return x


def get_unit(value):
    """ Determine unit
    """
    unit = {
        'h': 'frequency',
        'z': 'frequency',
        'o': 'resistance',
        'f': 'capacitance'
        }
    x = ''  # pylint: disable=C0103

    if value[-1].isalpha():
        try:
            x = unit[value[-1]]  # pylint: disable=C0103
        except KeyError:
            print('Unrecognized unit.')
    elif value[-1].isnumeric():
        print('Value passed lacks unit.')

    return x


def strip_unit(value):
    """ Remove unit
    """
    x = ''  # pylint: disable=C0103

    if value[-1].isalpha():
        if value[-2] == 'h' and value[-1] == 'z':
            x = value[:-2]  # pylint: disable=C0103
        elif value[-1] == 'f' or value[-1] == 'o':
            x = value[:-1]  # pylint: disable=C0103
        else:
            print('Value lacks unit.')
    elif value[-1].isnumeric():
        print('Value passed lacks unit and prefix.')

    return x


def strip_prefix(value):
    """ Remove metric prefix and return plain number
    """
    x = ''  # pylint: disable=C0103
    prefix = {
        'p': 1e-12,  # pico
        'n': 1e-9,   # nano
        'u': 1e-6,   # micro
        # '\u03bc': 1e-6,  # actual mu character
        'm': 1e-3,   # milli
        # '': 1,       # uhh what's the term for this
        'k': 1e3,    # kilo
        'M': 1e6,    # mega
        }
    try:
        x = float(value[:-1]) * prefix[value[-1]]  # pylint: disable=C0103
    except KeyError:
        # if value passed is a number
        try:
            if isinstance(int(value[-1]), int):
                x = value  # pylint: disable=C0103
        except ValueError:
            print('Error: unable to parse value.')
    x = float(x)  # pylint: disable=C0103
    return x


def add_prefix(value):
    """ YAY I DID IT

    input: plain number
    output: string of number followed by prefix
    """
    prefix = {
        -12: 'p',
        -9: 'n',
        -6: 'u',
        -3: 'm',
        3: 'k',
        6: 'M'
    }
    exponent = 1
    num = value
    try:
        num = float(num)
    except ValueError:
        print('Not a number!')
    if num > 1:
        for i in range(3, 7, 3):
            # print(i, 10**i)
            # print(num / 10**i)
            if 1000 > (num / 10**i) > 1:
                exponent = i
                break
    elif num < 1:
        for i in range(-12, -2, 3):
            # print(i, 10**i)
            # print(num / 10**i)
            if 1000 > (num / 10**i) > 1:
                exponent = i
                break

    if num == int(num):
        num = int(num)

    if exponent != 1:
        num = str(sig_fig(num / 10 ** exponent))
        try:
            exponent = prefix[exponent]
            return num + exponent
        except KeyError:
            print('Gadzooks!')
    else:
        return str(num)


def float_to_string(value):
    """ Convert a float or int to a string
    Required to force output to use standard notation rather than scientific
    Easier than adding prefixes *shrug*

    Now that I do have my add_prefix function, this isn't needed, but I am
    keeping it for future reference, maybe even use
    """
    return ('%.20f' % value).rstrip('0').rstrip('.')


def main():
    """ Main block

    Attributes:
    frc : list[bool, bool, bool]
        Frequency, resistance, capacitance. Tracks which values are known.

    """
    values = {
        'frequency': '',
        'resistance': '',
        'capacitance': '',
    }
    input_args = sys.argv[1:]

    if len(input_args) != 2:
        print('\nUsage:\t'
              f'{sys.argv[0]} <value>[prefix]<unit> <value>[prefix]<unit>\n\n'
              'See documentation for more information.\n')
        sys.exit()

    for i in input_args[0:]:
        tidy_arg = input_tidy(i)
        if len(sys.argv[0]) < 1:
            print(f'Raw Argument: {i}\n'
                  f'Formatted Argument: {tidy_arg}\n'
                  f'Argument specifies {get_unit(tidy_arg)}\n'
                  f'Base number: {strip_prefix(strip_unit(tidy_arg))}\n'
                  f'3 sigfigs: {sig_fig(strip_prefix(strip_unit(tidy_arg)))}'
                  '')
        values[get_unit(tidy_arg)] = sig_fig(
                                        strip_prefix(strip_unit(tidy_arg)))
        # print(values[get_unit(tidy_arg)])

    if values['frequency'] == '':
        frq = get_frequency(values['resistance'], values['capacitance'])
        print('The filter\'s -3dB frequency is '
              f'{add_prefix(sig_fig(frq))}Hz.')
    elif values['resistance'] == '':
        res = get_component(values['frequency'], values['capacitance'])
        print(f'You will need a {add_prefix(sig_fig(res))}ohm resistor.')
    elif values['capacitance'] == '':
        cap = get_component(values['frequency'], values['resistance'])
        print(f'You will need a '
              f'{add_prefix(sig_fig(cap))}F capacitor.')


if __name__ == '__main__':
    main()
