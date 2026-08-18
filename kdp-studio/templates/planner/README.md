# Planner template notes

Typical trim: `letter` (8.5×11) or `trade` (6×9).  
Bleed: usually no. Paper: white or cream. Ink: black.

Page ideas: yearly overview, monthly calendars, weekly spreads, habit trackers, notes.

Scaffold:

```bash
cd kdp-studio/tools
python3 -m kdp_studio new --slug my-planner --type planner --title "..." --trim letter --designs 52
```

Replace generated geometry pages with planner page PNGs/PDFs before building the interior.
