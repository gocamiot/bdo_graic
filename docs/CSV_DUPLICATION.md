- Create a folder same as your model name, with the following files.
    - `MODELNAME_views.py`
    - `MODELNAME_urls.py`

- Register the urls in the main url
    - Go to `core/urls.py` file and add 
    - `path("tables/", include("apps.tables.FOLDERNAME.MODELNAME_urls")),`

- Create a form for your new model in the `forms.py` file.
    - There is already some existing forms for other models, copy one of them and rename as you want.

- Copy one of the `views.py` file.
    - Assume, copied `finance_views.py` from `apps/tables/finance`.
    - Rename all of the text, model name, form name that includes `finance` and replace with your new model name. (Keep the case as it is)

- create a new template `list_of_MODEL_NAME.html` and copy one of the template. Assume, copied `list_of_finances.html`.
    - Do the same in the template. Find the name `finance` and replace it with the the new name that used in the views.

- Copy one of the `urls.py` file.
    - Assume, copied `finance_urls.py` from `apps/tables/finance`.
    - Rename all of the text that includes `finance` and replace with your new model name.

- Finally add the urls in the `grc_sidebar.html` file.