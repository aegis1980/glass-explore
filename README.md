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

## IGDB

From LBNL the IGDB database file in a Microsoft Access file (*.mdb).

`igdb.csv` only includes glass data - good enough for basic visualisation.

### Converting database for Heroku env

Issues with getting linux-based heroku app environment reading Access mdb file. Solution is to convert with `mdb2sqlite.py` script:

``` bash
python mdb2sqlite.py data/igdb.mdb data/igdb.sqlite
```

## Heroku deployment

**IMPORTANT: requirements.txt**

Use `pip-chill` to freeze requirements file, rather than `pip freeze` and delete `glass-explore` line that's created.
 the 

``` bash
pip-chill > requirements.txt
```

Auto deploys from `main`.

Uses this [Heroku buildpack](https://github.com/radian-software/heroku-buildpack-git-lfs) for LFS.