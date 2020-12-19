###################
Building Local Docs
###################


Building local docs is done via compiling docs locally. In order to do this, in the terminal type::

    python setup.py build_docs
    
This should create a new folder, _build, inside tardis/docs. Go through this folder and find the local docs that you are changing/creating to view how they will be compiled once a PR is approved. This method is good to check the formatting of docstrings in the API and the formatting of display files such as this one, as well as any other aspects that will be loaded in the tardis docs. 

For information on how docstrings should be formatted, refer 'here <https://tardis-sn.github.io/tarids/coding_guidelines.html>`_ for more information and examples. To create new documentation that will have a link inside the `TARDIS pages <https://tardis-sn.github.io/tardis>`_, you will need to edit the corresponding index.rst file to include your file inside of the toctree. For example, when the documentation was made for `research papers <https://tardis-sn.github.io/tardis/research/research_done_using_TARDIS/research_papers.html>`_ that used TARDIS, this location's `index.rst <https://github.com/tardis-sn/tardis/blob/master/docs/research/index.rst>`_ toctree was editted to include the path to the .rst file that would be generated when the docs are compiled and create a notebook.

When making or adding to the functionality of an aspect of TARDIS, an example notebook file should be made to show the changes/function that is created using that file. If a file is being converted from one language to another, a notebook should be included to show that the same values are outputted. 
