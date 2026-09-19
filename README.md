# Advent-of-Code-Excercises

## Next code in a custom alphabet

Codes are sequential numbers written with this 30-symbol alphabet. The rightmost symbol increments first, like an odometer:

`g r d x v c y 0 f j 7 5 p 4 q 3 s 6 2 8 z t m b h 9 n 1 k w`

Given starting code `3ppscy`, the next code is `3ppsc0` (`y` is followed by `0`).

```bash
python3 next_code.py 3ppscy
python3 next_code.py 3ppscy -a g-r-d-x-v-c-y-0-f-j-7-5-p-4-q-3-s-6-2-8-z-t-m-b-h-9-n-1-k-w
python3 next_code.py 3ppscy -n 1000 --prefixes tv,tstats,tci
python3 -m unittest test_next_code.py
```

`-n 1000 --prefixes tv,tstats,tci` prints the next codes after the given start with `tv`, `tstats`, and `tci` prepended in that order. Every paste group is one set of those three prefixes. A requested count that is not a multiple of 3 is rounded up so the last group is complete (1000 becomes 1002 codes / 334 groups).
