# Glass explore

## For dev (local dev)

**NOTE** Uses LFS for large IGDB file. If something not working, git-wise, check not hit storage limit on account.

1. right click on project root folder > select **open in terminal**
2. `python -m venv .venv` to setup python virtual environment for this project. TIP: copy from here and right click in terminal to paste-and-execute.
3. Dialog should come up asking you want this env as interpreter for project: answer yes.
4. If no to (3) on blue ribbon at bottom of VSCODE, on left click on interpreter, chose the **venv** one you just created.
5. Might get some bits and both e.g. 'install pylint' etc. click install for them.
6. `pip install -r requirements.txt` to install packages
7. `pip install -e .` to make editable
8. Run `./glass_explore/index.py` to run with **dev server**. (Running `./production.py` runs using `gunicorn` in production environment)

## Updating the IGDB

The IGDB is updated every couple of months with new and updated glass data from manufacturers.




From LBNL the IGDB database file in a Microsoft Access file (*.mdb).

Most up to date version is here

### Prepping IGDB database file for Heroku production env


#### MDB to SQLITE
Issues with getting linux-based heroku app environment reading Microsoft Access mdb file. Solution is to convert to sqlite file.
This requires drivers for Access to be available on dev machine - so Microsoft Access installed or the Microsoft Access Database Engine
Update IGDB to in LBNL WINDOW8, then  default path for uptodate non-password protected access db is in c:/Users/Public/LBNL/WINDOW7.8/w7.mdb

#### HDF file for igdb GLASS table

`./scripts/glass_table_to_hdf.py` creates an HDFStore file for modified data in IGDB's GLASS table. 

Run `script/update_igdb.py`

## Heroku deployment

**IMPORTANT: requirements.txt**

Use `pip-chill` to freeze requirements file, rather than `pip freeze` and delete `glass-explore` line that's created.

``` bash
pip-chill > requirements.txt
```

Auto deploys from `main`.

Uses this [Heroku buildpack](https://github.com/radian-software/heroku-buildpack-git-lfs) for LFS.