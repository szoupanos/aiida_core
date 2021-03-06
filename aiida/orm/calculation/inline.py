# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import functools
from aiida.orm.implementation.general.calculation.inline import InlineCalculation


__all__ = ['InlineCalculation', 'make_inline', 'optional_inline']


def make_inline(func):
    """
    This make_inline wrapper/decorator takes a function with specific
    requirements, runs it and stores the result as an InlineCalculation node.
    It will also store all other nodes, including any possibly unstored
    input node! The return value of the wrapped calculation will also be
    slightly changed, see below.

    The wrapper:

    * checks that the function name ends with the string ``'_inline'``
    * checks that each input parameter is a valid Data node
      (can be stored or unstored)
    * runs the actual function
    * gets the result values
    * checks that the result value is a dictionary, where the
      key are all strings and the values are all **unstored**
      data nodes
    * creates an InlineCalculation node, links all the kwargs
      as inputs and the returned nodes as outputs, using the
      keys as link labels
    * stores all the nodes (including, possibly, unstored input
      nodes given as kwargs)
    * returns a length-two tuple, where the first element is
      the InlineCalculation node, and the second is the dictionary
      returned by the wrapped function

    To use this function, you can use it as a decorator of a
    wrapped function::

        @make_inline
        def copy_inline(source):
            return {copy: source.copy()}

    In this way, every time you call copy_inline, the wrapped version
    is actually called, and the return value will be a tuple with
    the InlineCalculation instance, and the returned dictionary.
    For instance, if ``s`` is a valid ``Data`` node, with the following
    lines::

        c, s_copy_dict = copy_inline(source=s)
        s_copy = s_copy_dict['copy']

    ``c`` will contain the new ``InlineCalculation`` instance, ``s_copy`` the
    (stored) copy of ``s`` (with the side effect that, if ``s`` was not stored,
    after the function call it will be automatically stored).

    :note: If you use a wrapper, make sure to write explicitly in the docstrings
        that the function is going to store the nodes.

    The second possibility, if you want that by default the function does not
    store anything, but can be wrapped when it is necessary, is the following.
    You simply define the function you want to wrap (``copy_inline`` in the
    example above) without decorator::

        def copy_inline(source):
            return {copy: source.copy()}

    This is a normal function, so to call it you will normally do::

        s_copy_dict = copy_inline(s)

    while if you want to wrap it, so that an ``InlineCalculation`` is created, and
    everything is stored, you will run::

        c, s_copy_dict = make_inline(f)(s=s)

    Note that, with the wrapper, all the parameters to ``f()`` have to be
    passed as keyworded arguments. Moreover, the return value is different,
    i.e. ``(c, s_copy_dict)`` instead of simply ``s_copy_dict``.

    .. note:: EXTREMELY IMPORTANT! The wrapped function MUST have
        the following requirements in order to be reproducible.
        These requirements cannot be enforced, but must be
        followed when writing the wrapped function.

        * The function MUST NOT USE information that is not
          passed in the kwargs. In particular, it cannot read
          files from the hard-drive (that will not be present
          in another user's computer), it cannot connect
          to external databases and retrieve the current
          entries in that database (that could change over
          time), etc.
        * The only exception to the above rule is the access
          to the AiiDA database for the *parents* of the input
          nodes. That is, you can take the input nodes passed
          as kwargs, and use also the data given in their inputs,
          the inputs of their inputs, ... but you CANNOT use
          any output of any of the above-mentioned nodes (that
          could change over time).
        * The function MUST NOT have side effects (creating files on the disk,
          adding entries to an external database, ...).

    .. note:: The function will also store:

        * in the attributes: the function name, function namespace and the starting
          line number of the function in the source file
        * in the repository: the full source file if it is possible to retrieve it
          otherwise it will be set to None, e.g. if the function was defined
          in the interactive shell).

        For this reason, try to keep, if possible, all the code to be run
        within the same file, so that it is possible to keep the provenance
        of the functions that were run (if you instead call a function in a
        different file, you will never know in the future what that function
        did).
        If you call external modules and you matter about provenance, if would
        be good to also return in a suitable dictionary the version of these
        modules (e.g., after importing a module XXX, you can check if the
        module defines a variable XXX.__version__ or XXX.VERSION or something
        similar, and store it in an output node).

    :note: All nodes will be stored, including unstored input nodes!!

    :param kwargs: all kwargs are passed to the wrapped function
    :return: a length-two tuple, where the first element is
        the InlineCalculation node, and the second is the dictionary
        returned by the wrapped function. All nodes are stored.
    :raise TypeError: if the return value is not a dictionary, the
        keys are not strings, or the values
        are not data nodes. Raise also if the input values are not data nodes.
    :raise ModificationNotAllowed: if the returned Data nodes are already
        stored.
    :raise Exception: All other exceptions from the wrapped function
        are not catched.
    """
    from aiida.work import workfunction

    # Note: if you pass a lambda function, the name will be <lambda>; moreover
    # if you define a function f, and then do "h=f", h.__name__ will
    # still return 'f'!
    function_name = func.__name__
    if not function_name.endswith('_inline'):
        raise ValueError(
            "The function name that is wrapped must end "
            "with '_inline', while its name is '{}'".format(function_name))

    wf = workfunction(func, InlineCalculation)

    @functools.wraps(func)
    def swap_result(*args, **kwargs):
        result = wf.run_get_node(*args, **kwargs)
        return result[1], result[0]

    return swap_result


def optional_inline(func):
    """
    optional_inline wrapper/decorator takes a function, which can be called
    either as wrapped in InlineCalculation or a simple function, depending
    on 'store' keyworded argument (True stands for InlineCalculation, False
    for simple function). The wrapped function has to adhere to the
    requirements by make_inline wrapper/decorator.

    Usage example::

        @optional_inline
        def copy_inline(source=None):
            return {'copy': source.copy()}

    Function ``copy_inline`` will be wrapped in InlineCalculation when
    invoked in following way::

        copy_inline(source=node,store=True)

    while it will be called as a simple function when invoked::

        copy_inline(source=node)

    In any way the ``copy_inline`` will return the same results.
    """

    def wrapped_function(*args, **kwargs):
        """
        This wrapper function is the actual function that is called.
        """
        store = kwargs.pop('store', False)

        if store:
            return make_inline(func)(*args, **kwargs)[1]
        else:
            return func(*args, **kwargs)

    return wrapped_function
