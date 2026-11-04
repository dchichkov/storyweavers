"""Bounded English morphology; the realizer never infers tense from prose."""


def third_person(lemma):
    head, *tail = lemma.split(" ")
    if head in {"be", "have", "do", "go"}:
        head = {"be": "is", "have": "has", "do": "does", "go": "goes"}[head]
    elif head.endswith("y") and head[-2:-1] not in "aeiou":
        head = head[:-1] + "ies"
    elif head.endswith(("s", "sh", "ch", "x", "z", "o")):
        head += "es"
    else:
        head += "s"
    return " ".join([head] + tail)


def verb_phrase(verb, tense="past", negative=False, *, person=3, plural=False):
    if tense == "infinitive":
        return ("not " if negative else "") + verb.lemma
    if tense == "future":
        return "will " + ("not " if negative else "") + verb.lemma
    if tense == "past_perfect":
        return "had " + ("not " if negative else "") + (verb.participle or verb.past)
    if verb.lemma == "be":
        form = ("were" if plural or person == 2 else "was") if tense == "past" else (
            "am" if person == 1 and not plural else "are" if plural or person == 2 else "is")
        return form + (" not" if negative else "")
    if negative:
        auxiliary = "did" if tense == "past" else "does" if person == 3 and not plural else "do"
        return auxiliary + " not " + verb.lemma
    if tense == "past":
        return verb.past
    return third_person(verb.lemma) if person == 3 and not plural else verb.lemma
