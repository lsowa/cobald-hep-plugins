#############
Timer Plugin
#############

.. py:module:: cobald_hep_plugins.timer
    :synopsis: Time-of-day demand controller

The :class:`~cobald_hep_plugins.timer.Timer` plugin enforces a recurring,
time-of-day schedule for the demand of a target pool.

At its core the Timer plugin stores an ordered mapping of ``HH:MM`` to demand values. Whenever the demand is updated,
``Timer`` looks for the latest schedule entry that is not later than the current
time and applies the demand from that entplugin pool. If the current
time is earlier than the first entry, the scheduled value from the previous day
becomes active. User supplied values to :attr:`demand` are ignored so that the
scheduled demand is always in effect.

Configuration
=============

The class accepts three arguments:

``target``
    The pool whose demand should follow the schedule. This is the same target
    you would normally use in a COBalD pipeline.

``schedule``
    A mapping where the key is either ``HH:MM`` and the
    value is a floating point demand. The schedule must at least contain one
    entry and demand values must be non-negative.

``interval`` (optional)
    Number of seconds between two schedule checks. Defaults to ``300`` seconds.

Schedule semantics
==================

Demands remain active until the next configured timestamp is reached. For
example with the fragment below.

.. code:: yaml

    schedule:
      '08:00': 50   # from 08:00 until 12:30
      '12:30': 120  # from 12:30 until 20:15
      '20:15': 10   # from 20:15 until 08:00 next day


Example configuration
=====================

An example snippet for the YAML interface in a COBalD configuration file:

.. code:: yaml

    - !Timer
      target: SomePool
      schedule:
        '06:00': 20
        '09:00': 80
        '17:30': 10
      interval: 120

With the configuration above the decorator wakes up every two minutes, updates
``target`` with the most recent demand of the schedule and thus enforces a
repeatable daily pattern.
