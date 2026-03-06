Admonition Test
==================

There are `nine explicit directive types <https://docutils.sourceforge.io/docs/ref/rst/directives.html>`_, 
and one generic type, for admonitions within docutils used by rST. There are 
`four types <https://vanillaframework.io/docs/patterns/notification>`_ within Vanilla, and as 
such there is no one to one mapping. Below shows each of the admonitions and how they are mapped to Vanilla.

.. attention::
    Attention admonitions map to caution notifications.

.. caution::
    Caution admonitions map to caution notifications. 

.. danger::
    Danger admonitions map to caution notifications.

.. error::
    Error admonitions map to negative notifications. 

.. hint::
    Hint admonitions map to positive notifications.

.. important::
    Important admonitions map to information notifications.

.. note::
    Note admonitions map to information notifications.

.. tip::
    Tip admonitions map to positive notifications.

.. warning::
    Warning admonitions map to caution notifications. 

.. admonition:: Generic Admonition

    Generic admonitions map to information notifications.
    NOTE: currently requires a blank line between title and text