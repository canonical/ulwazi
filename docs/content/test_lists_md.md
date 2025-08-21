# Lists (Markdown)

````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ```
    - Item 1
    - Item 2
    - Item 3
    ```
  - - Item 1
    - Item 2
    - Item 3
* - ```
    1. Step 1
    2. Step 2
    3. Step 3
    ```
  - 1. Step 1
    1. Step 2
    2. Step 3
* - ```
    1. Step 1
       - Item 1
         * Sub-item
       - Item 2
    2. Step 2
       1. Sub-step 1
       2. Sub-step 2
    ```
  - 1. Step 1
       - Item 1
         * Sub-item
       - Item 2
    1. Step 2
       1. Sub-step 1
       2. Sub-step 2
````

Adhere to the following conventions:

- In numbered lists, use `1.` for all items to generate the step numbers automatically.
  You can also use a higher number for the first item to start with that number.
- Use `-` for unordered lists. When using nested lists, you can use `*` for the nested level.

## Definition lists

````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ```
    Term 1
    : Definition

    Term 2
    : Definition
    ```
  - Term 1
    : Definition

    Term 2
    : Definition
````

--------

Term 1
   : Definition

Term 2
   : Definition

Term 1
: Definition

Term 2
: Longer definition

  With multiple paragraphs

- And bullet points
