# Django CVS BULK Processing

This helper will parse all CVSs discovered in `media` DIRECTORY and generate the related Models in `apps/tables/models.py`. 
The translation can be customized via an external `mapper` file defined in the INPUT directory. 

> Syntax (basic usage)

```bash
$ python manage.py csv-to-model
``` 

<br />

> Syntax - Simulation Mode

```bash
$ python manage.py csv-to-model -s
// OR
$ python manage.py csv-to-model --simulation
```

### Quick Start

```bash
$ rm db.sqlite3                        # Remove DB
$ python manage.py csv-to-model        # Convert CVS -> Model
$ python manage.py makemigrations      # Generate SQL
$ python manage.py migrate             # Mutate DB  
$ python manage.py csv-to-model -ld    # Load CSV into the generated Model
```

Once the load is finished, we can query the data

```py
$ python.exe manage.py shell
>>> 
>>> from apps.tables.models import *
>>> Devices.objects.all()
<QuerySet [<Devices: Devices object (1)>, <Devices: Devices object (2)>, <Devices: Devices object (3)>, <Devices: Devices object (4)>, <Devices: Devices object (5)>, <Devices: Devices object (6)>, <Devices: Devices object (7)>, <Devices: Devices object (8)>, <Devices: Devices object (9)>, <Devices: Devices object (10)>, <Devices: Devices object (11)>, <Devices: Devices object (12)>, <Devices: Devices object (13)>, <Devices: Devices object (14)>, <Devices: Devices object (15)>, <Devices: Devices object (16)>, <Devices: Devices object (17)>, <Devices: Devices object (18)>, <Devices: Devices object (19)>, <Devices: Devices object (20)>, '...(remaining elements truncated)...']>
```

### Complete tests

- Delete sqlite file (to ensure a fresh start)
- Migrate DB
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- Convert CVS to Models (tables app)
  - Check the Input 
    - `python manage.py csv-to-model -c`
  - Simulate the conversion
    - `python manage.py csv-to-model -s`
  - Generate Modles 
    - `python manage.py csv-to-model`
    - All model(s) are generated in `apps.tables.models.py` 
- Migrate DB (two ways)
  - `python manage.py makemigrations` 
  - `python manage.py migrate`
- Load data
  - The operation applies to all CVS Files from `media/tables-data`
  - Append the data  
    - `python manage.py csv-to-model -l`
  - DELETE the existing rows (extra `d` argument)
    - `python manage.py csv-to-model -ld`
- DELETE Only
    - `python manage.py csv-to-model -d`
