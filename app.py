"""
Usage:  python patch_nav.py app.py
Updates app.py in place (writes app.py.bak first) with:
  - previous_nav = 119.11
  - total_units  = 34628.09
  - holdings from the 31-Oct-2026 statement (MEESHO added)
"""
import re
import shutil
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "app.py"
src = open(path, encoding="utf-8").read()
shutil.copy(path, path + ".bak")

NEW_STOCKS = '''# Updated to Motilal Oswal Midcap Fund's Monthly Portfolio Statement
# AS ON OCTOBER 31, 2026 (equity only; TREPS 4.39% and net
# receivables 0.40% excluded). NEW vs September: MEESHO.

stocks = [

    ("PAYTM", 8.54),
    ("ETERNAL", 7.32),
    ("KALYANKJIL", 7.29),
    ("COFORGE", 6.44),
    ("PERSISTENT", 5.15),
    ("ABCAPITAL", 4.57),
    ("STLTECH", 4.04),
    ("GROWW", 3.90),
    ("MCX", 3.67),
    ("KEI", 3.66),
    ("SHRIRAMFIN", 3.07),
    ("LENSKART", 3.06),
    ("DIXON", 2.92),
    ("BHARTIHEXA", 2.60),
    ("MOTHERSON", 2.34),
    ("PRESTIGE", 2.29),
    ("BSE", 2.28),
    ("ICICIAMC", 2.28),
    ("TIINDIA", 2.20),
    ("IDFCFIRSTB", 2.15),
    ("PREMIERENE", 2.10),
    ("BEL", 1.92),
    ("INDIGO", 1.74),
    ("SUZLON", 1.71),
    ("POLICYBZR", 1.64),
    ("LTF", 1.56),
    ("WAAREEENER", 1.50),
    ("MAXHEALTH", 1.24),
    ("ADANIENT", 0.79),
    ("MEESHO", 0.69),
    ("PWL", 0.55),

]
'''

# 1) Holdings: replace from the "Updated to ..." comment through the closing ]
pattern = re.compile(
    r"# Updated to Motilal Oswal Midcap Fund's Monthly Portfolio Statement.*?^stocks = \[.*?^\]\n",
    re.S | re.M,
)
src, n1 = pattern.subn(lambda m: NEW_STOCKS, src, count=1)

# 2) Previous NAV and units
src, n2 = re.subn(r"^previous_nav = [\d.]+", "previous_nav = 119.11", src, count=1, flags=re.M)
src, n3 = re.subn(r"^total_units = [\d.]+", "total_units = 34628.09", src, count=1, flags=re.M)

open(path, "w", encoding="utf-8").write(src)
print(f"holdings block: {n1}, previous_nav: {n2}, total_units: {n3}  (expected 1/1/1)")
print(f"Backup saved to {path}.bak")
