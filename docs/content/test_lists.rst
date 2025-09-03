Lists
-----

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          - Item 1
          - Item 2
          - Item 3
     - - Item 1
       - Item 2
       - Item 3
   * - .. code::

          1. Step 1
          #. Step 2
          #. Step 3
     - 1. Step 1
       #. Step 2
       #. Step 3
   * - .. code::

          a. Step 1
          #. Step 2
          #. Step 3
     - a. Step 1
       #. Step 2
       #. Step 3

You can also nest lists:

.. tabs::

   .. tab:: Input

      .. code::

         1. Step 1

            - Item 1

              * Sub-item
            - Item 2

              i. Sub-step 1
              #. Sub-step 2
         #. Step 2

            a. Sub-step 1

               - Item
            #. Sub-step 2
   .. tab:: Output



       1. Step 1

          - Item 1

            * Sub-item
          - Item 2

            i. Sub-step 1
            #. Sub-step 2
       #. Step 2

          a. Sub-step 1

             - Item
          #. Sub-step 2



Adhere to the following conventions:

- In numbered lists, number the first item and use ``#.`` for all subsequent items to generate the step numbers automatically.
- Use ``-`` for unordered lists. When using nested lists, you can use ``*`` for the nested level.

Definition lists
~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Input
     - Output
   * - .. code::

          Term 1:
            Definition
          Term 2:
            Definition
     - Term 1:
         Definition
       Term 2:
         Definition