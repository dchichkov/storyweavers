"""Opt-in typed phrase alternatives; no post-generation text replacement.

All alternatives retain the clause's participants, polarity, tense and event.
The original portable grammar remains frozen. Explicit paradigms avoid guessing
new verb forms or allowing synonyms with incompatible complement structures.
"""
from dataclasses import replace

from ..grammar import choice, seq
from ..portable.features import Sentence
from ..portable.morphology import verb
from .surface import SpeechLanguage

# Deliberately small lexical equivalence classes in these controlled worlds.
# Each row lists allowed construction labels, followed by explicit paradigms.
LEXICAL = {
    "give": (("gf.ComplV3",), (("hand", "hands", "handed", "handed", "handing"),)),
    "put": (("gf.ComplV2",), (("place", "places", "placed", "placed", "placing"),)),
    "set": (("gf.ComplV2",), (("place", "places", "placed", "placed", "placing"),)),
    "repair": (("gf.ComplV2",), (("fix", "fixes", "fixed", "fixed", "fixing"),)),
    "find": (("gf.ComplV2",), (("locate", "locates", "located", "located", "locating"),
                                ("discover", "discovers", "discovered", "discovered", "discovering"))),
    "spot": (("gf.ComplV2",), (("notice", "notices", "noticed", "noticed", "noticing"),)),
    "sketch": (("gf.ComplV2",), (("draw", "draws", "drew", "drawn", "drawing"),)),
    "perform": (("gf.ComplV2",), (("play", "plays", "played", "played", "playing"),)),
    "practice": (("gf.ComplV2",), (("rehearse", "rehearses", "rehearsed", "rehearsed", "rehearsing"),)),
    "choose": (("gf.ComplVV",), (("decide", "decides", "decided", "decided", "deciding"),)),
    "shape": (("gf.ComplV2",), (("form", "forms", "formed", "formed", "forming"),)),
    "reshape": (("gf.ComplV2",), (("remold", "remolds", "remolded", "remolded", "remolding"),)),
    "smooth": (("gf.ComplV2",), (("smooth out", "smooths out", "smoothed out", "smoothed out", "smoothing out"),)),
}


class ExpandedLanguage(SpeechLanguage):
    """Expand before sampling, while phrases still have grammatical types."""

    def s(self, subject, predicate, *, negative=False, tense=None):
        if isinstance(subject, str):
            subject = self.ref(subject, subject=True)
        tense = tense or self.tense
        original = super().s(subject, predicate, negative=negative, tense=tense)
        alternatives = [original.node]
        labels, paradigms = LEXICAL.get(predicate.verb.base, ((), ()))
        # AdvVP retains the saturated construction label, so modifiers and their
        # participants survive substitution without rebuilding object strings.
        if not predicate.auxiliary and predicate.label in labels:
            for forms in paradigms:
                if (predicate.verb.base == "choose" and tense == "present") or (negative and forms[0] == "discover"):
                    continue  # Avoid stilted 'I decide' and negative discovery claims.
                lexical = verb(forms[0], {"forms": list(forms), "valencies": list(predicate.verb.valencies)})
                variant = replace(predicate, verb=lexical)
                alternatives.append(super().s(subject, variant, negative=negative, tense=tense).node)
        if predicate.verb.base == "want" and predicate.label in {"gf.ComplVV", "gf.ComplV2"} and tense == "present" and not negative:
            # The complement is already saturated: 'a cup' or 'to make a sail'.
            alternatives.append(seq("expanded.polite_desire", subject.subject, "would like", predicate.tail))
        if predicate.auxiliary == "can" and tense == "present" and not negative:
            # A tentative offer of the same legal action, not an assertion of
            # a new ability. Past/negative modal meanings are left unchanged.
            alternatives.append(seq("expanded.tentative_offer", subject.subject, "could", predicate.tail))
        return Sentence(choice("expanded.clause", *alternatives)) if len(alternatives) > 1 else original

    def v(self, word, *complements):
        original = super().v(word, *complements)
        if word == "give" and original.label == "gf.ComplV3":
            recipient, obj = complements
            return replace(original, tail=choice("expanded.dative",
                original.tail, seq("expanded.to_recipient", obj.object, "to", recipient.object)))
        return original

    def using(self, actor, action, instrument):
        # Resolve once, so alternative enumeration cannot alter discourse state.
        subject = self.ref(actor, subject=True) if isinstance(actor, str) else actor
        plain = self.s(subject, action)
        return self.either(
            self.s(subject, self.v("use", instrument, action)),
            self.s(subject, self.adv(action, self.pp("with", instrument))),
            Sentence(seq("expanded.instrument_front", "With", instrument.object, ",", plain.node)),
            Sentence(seq("expanded.using_front", "Using", instrument.object, ",", plain.node)),
        )

    def join(self, left, right, conjunction="and"):
        original = super().join(left, right, conjunction)
        if conjunction == "and":
            alternate = seq("expanded.split_sequence", left.node, ".", right.node)
        elif conjunction == "but":
            alternate = seq("expanded.split_contrast", left.node, ".", "But", right.node)
        else:
            return original  # Keep explicit causal linkage and clause order.
        return Sentence(choice("expanded.clause_link", original.node, alternate, weights=(2, 1)))
