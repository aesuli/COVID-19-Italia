REM This is a temporal data repo.
REM Every commit contains all the past history.
REM I don't need to keep diffs. 
REM Every update deletes old commits.

REM Conda env.
call C:\Users\andre\anaconda3\Scripts\activate.bat py3

REM Create plots.
python make_plots_and_pages.py

REM This commit creates diffs.
git commit -am "aaa"

REM Check out to a temporary branch.
git checkout --orphan TEMP_BRANCH

REM Add all the files.
git add -A

REM Commit the changes without a previous commit to diff on.
git commit -am "Data update"

REM Delete the old branch.
git branch -D master

REM Rename the temporary branch to master.
git branch -m master

REM Force push on remote, deleting previous commits.
git push -f origin master