"""English paradigm subset adapted from GF RGL 20260403 ParadigmsEng/ResEng.

See sources/GF-RGL-LICENSE. Explicit irregular entries override paradigms.
No guessing a missing word's valency and no fallback verbing of nouns.
"""
from .catalog import rule
from .features import Verb
import re


@rule("gf.regN", "ParadigmsEng.gf", "regN, mk2N", tags=("noun", "plural", "morphology"))
def plural(word: str) -> str:
    """Regular plural; irregular forms must be supplied by the lexicon."""
    if word.endswith(("io", "oo")):
        return word + "s"
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeou":
        return word[:-1] + "ies"
    if word.endswith(("s", "sh", "ch", "x", "z", "o")):
        return word + "es"
    return word + "s"


@rule("gf.mkV", "ParadigmsEng.gf", "regV, duplV, irregV, irreg4V, mk5V",
      dependencies=("gf.regN",), tags=("verb", "inflection", "past", "irregular"))
def verb(word: str, entry: dict) -> Verb:
    """One to five GF-style principal parts plus explicit allowed valencies."""
    forms = entry.get("forms", [word])
    if not 1 <= len(forms) <= 5 or forms[0] != word:
        raise ValueError(f"invalid verb paradigm for {word}")
    third = plural(word)
    def double_final(s):
        if re.search(r"[aeo][aeiou].$", s):
            return s
        return s + s[-1] if re.search(r"[aeiou][bdgmnprt]$", s) else s
    # GF's regular paradigm is deliberately a heuristic. Lexical exceptions
    # such as open/opened are supplied explicitly, just as in an RGL lexicon.
    past = third[:-1] + "d" if third.endswith("es") else (
        third[:-1] + "ed" if third.endswith("ers") else double_final(word) + "ed")
    if word.endswith("ee"):
        ing = word + "ing"
    elif word.endswith("ie"):
        ing = word[:-2] + "ying"
    elif word.endswith("e"):
        ing = word[:-1] + "ing"
    elif word.endswith("er"):
        ing = word + "ing"
    else:
        ing = double_final(word) + "ing"
    if len(forms) == 2:
        stem = forms[1][:-2]
        if stem and word[-1] == stem[-1]:
            past, ing = stem + "ed", stem + "ing"
    part = past
    if len(forms) >= 3:
        past, part = forms[1:3]
    if len(forms) == 4:
        ing = forms[3]
    if len(forms) == 5:
        third, past, part, ing = forms[1:]
    return Verb(word, third, past, part, ing, tuple(entry["valencies"]))


@rule("gf.finite", "ResEng.gf", "nonAuxVerbForms, auxBe, mkVerbForms",
      tags=("agreement", "tense", "negation", "auxiliary"))
def finite(v: Verb, agreement, tense="past", negative=False, auxiliary="") -> str:
    """Simple past/present, copula/modal agreement, and uncontracted do-negation."""
    if tense not in {"past", "present"}:
        raise ValueError("supported tenses: past, present")
    if auxiliary == "be":
        if tense == "past":
            form = "were" if agreement.number == "plural" or agreement.person == 2 else "was"
        else:
            form = "are" if agreement.number == "plural" or agreement.person == 2 else ("am" if agreement.person == 1 else "is")
        return form + (" not" if negative else "")
    if auxiliary == "can":
        return ("could" if tense == "past" else "can") + (" not" if negative else "")
    if negative:
        auxiliary = "did" if tense == "past" else ("does" if agreement.third_singular else "do")
        return auxiliary + " not " + v.base
    return v.past if tense == "past" else (v.third if agreement.third_singular else v.base)
