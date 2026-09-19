# Advent-of-Code-Excercises

## Next code in a custom alphabet

Codes are sequential numbers written with this 30-symbol alphabet. The rightmost symbol increments first, like an odometer:

`g r d x v c y 0 f j 7 5 p 4 q 3 s 6 2 8 z t m b h 9 n 1 k w`

Given starting code `3ppscy`, the next code is `3ppsc0` (`y` is followed by `0`).

```bash
python3 next_code.py 3ppscy
python3 next_code.py 3ppscy -a g-r-d-x-v-c-y-0-f-j-7-5-p-4-q-3-s-6-2-8-z-t-m-b-h-9-n-1-k-w
python3 next_code.py 3ppscy -n 1000 --suffixes tv,tstats,tci --groups 3
python3 -m unittest test_next_code.py
```

`-n 1000 --suffixes tv,tstats,tci --groups 3` prints the next 1000 codes after the given start, appending `tv`, `tstats`, and `tci` in that rotating order, split into three copy-paste blocks.
