# Glass explore

(c)2026 Jon Robinson. All Rights Reserved.


## For developement (local dev of webapp)

**NOTE** Uses LFS for large IGDB file. If something not working, git-wise, check not hit storage limit on account.

### VS code IDE start cheat sheet

1. right click on project root folder > select **open in terminal**
2. `python3.12 -m venv venv` to setup python virtual environment for this project. TIP: copy from here and right click in terminal to paste-and-execute. (March 2026)
3. Dialog should come up asking you want this env as interpreter for project: answer yes.
4. If no to (3) on blue ribbon at bottom of VSCODE, on left click on interpreter, chose the **venv** one you just created.
5. Might get some bits and both e.g. 'install pylint' etc. click install for them.
6. `pip install -r requirements.txt` to install packages
7. `pip install -e .` to make editable
8. Run `./glass_explore/app.py` to run with **dev server**. (Running `./production.py` runs using `gunicorn` in production environment)

## Updating the IGDB

The International Glazing Database (IGDB) is [updated every couple of months](https://windows.lbl.gov/igdb-downloads) with new and updated glass data from manufacturers.

From LBNL the IGDB database file in a Microsoft Access file (*.mdb).

When you download and install from [here](https://windows.lbl.gov/igdb-downloads) there is a password-protected Microsoft Access file `Glazing.mdb` saved in `c:\Users\Public\LBNL\LBNL Shared`. Becuase password protected we cannot use this.

To access data in the IGDB Access file, update **Libraries > Glass > Update IGDB (button)** in LBNL WINDOW program. This puts a non-protected file `C:\Users\Public\LBNL\WINDOW7.8\w7.mdb` (or `C:\Users\Public\LBNL\WINDOW7.7\w7.mdb`) depending on which version of LBNL WINDOW you are using.

### Prepping IGDB database file for Heroku production env

#### MDB to SQLITE
There are issues with getting linux-based server environment reading Microsoft Access mdb file. Solution is to convert to sqlite file.
This requires drivers for Access to be available on dev machine - so Microsoft Access installed or the Microsoft Access Database Engine
Update IGDB to in LBNL WINDOW8, then  default path for up-to-date non-password protected access db is in `c:/Users/Public/LBNL/WINDOW7.8/w7.mdb`

#### Parquet file for igdb GLASS table

(March 2026: Previously HD5 stroe, updated to Parquet)

`./scripts/glass_table_to_parquet.py` creates an Parquet file for modified data in IGDB's GLASS table. 

Run `script/update_igdb.py`

When updated correctly, the updated IGDB version should show in app `About` modal popup.


## Heroku deployment [March 2026 not longer supported - deployment moved to Railway]

**IMPORTANT: requirements.txt**

Use `pip-chill` to freeze requirements file, rather than `pip freeze` and delete `glass-explore` line that's created.

``` bash
pip-chill > requirements.txt
```

Auto deploys from `main`.

Uses this [Heroku buildpack](https://github.com/radian-software/heroku-buildpack-git-lfs) for LFS.

## Railway deployment

(as of March 2026)

- update to python 3.11. (Issues with installing pywincalc with 3.12)
- Using poetry for package management rather than pip. (`pyproject.toml`)
- Using parquet rather than HD5 storage for processed dataframes.


### Sqlite data file
Not longer using git-lfs for sqlite file since does not seem to be well supported in Railway.
Using a Railway 'volume' mounted at '/igdb'



