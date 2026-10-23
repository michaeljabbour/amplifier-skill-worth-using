# ShelfNote

**FICTIONAL evaluation dossier. All people, events, logs, quotes, and tools are invented.**

ShelfNote adds a Restock command to the spreadsheet Nina already uses for workshop consumables. It lists quantities below their agreed minimum and writes a restock CSV. It uses the existing stock-count CSV, which already contains item, quantity, and minimum columns. No account, configuration code, or new data collection is needed.

## First use

1. In the stock spreadsheet, choose ShelfNote > Restock.
2. Select the existing stock-count CSV.
3. Review the preview, which shows the source quantities, minimums, and proposed restock amounts.
4. Export the restock CSV beside the input.

The preview never changes the input. A bad quantity is highlighted with its source row, and export remains disabled until the row is corrected or excluded. Editing the source copy and trying again requires no maintainer access. Discard the preview or delete the newly generated CSV to undo a run.
