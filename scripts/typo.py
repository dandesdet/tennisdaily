"""Неразрывный пробел после предлогов, союзов и частиц. Список совпадает с scripts/typo.js."""
import re

WORDS = (
    "а без в во да для до за и из изо или к ко на над не ни но о об обо от ото по под при про с со у "
    "через перед между как что "
    "va u bu har bir eng "
    "a an the and or but of in on at to by for with from vs no not"
).split()

RE = re.compile(r"(?<![\w'’‘`-])(" + "|".join(WORDS) + r") +(?=[\w«„\"(])", re.IGNORECASE)


def nb(text):
    return RE.sub("\\1\u00a0", text)
