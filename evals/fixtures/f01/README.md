# TrayCount

**FICTIONAL evaluation dossier. All people, events, logs, quotes, and tools are invented.**

TrayCount adds a Restock command to the spreadsheet Mara already uses for theatre consumables. The weekly job is to list quantities below their agreed minimum and write a restock CSV. The input remains the existing stock-count CSV; no account or new database is required.

## First use

1. Open the stock spreadsheet and choose TrayCount > Restock.
2. Before the first run, create `traycount.cfg` and supply `stock_profile`. The program requires one of the installation's internal profile codes. This README does not list those codes or explain where a new user can find them.
3. Select the same stock-count CSV used for the weekly manual report.
4. Preview the calculation and export the restock CSV beside the input.

The installation will not calculate until a profile is present. It displays `Missing stock_profile; contact maintainer`; this is a visible setup error. Once configured, the same profile is reused. A preview shows input counts and minimums alongside each subtraction. A bad quantity is highlighted with its source row; editing or excluding that row lets the user retry. The input file is never changed. Discarding the preview or deleting the new CSV undoes the operation.
