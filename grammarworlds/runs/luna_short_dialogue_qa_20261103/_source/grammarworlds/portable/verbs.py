"""GF verb-complement constructions, lowered to our weighted phrase Nodes.

Slash/gap machinery is deliberately reduced to saturated, declarative phrases.
"""
from dataclasses import replace
from ..grammar import seq, text
from .catalog import rule
from .features import AP, Adv, NP, Sentence, VP, Verb, require
from .morphology import finite


def accepts(verb, valency):
    require(verb, Verb)
    if valency not in verb.valencies:
        raise TypeError(f"{verb.base!r} does not license {valency}; allowed: {verb.valencies}")


def infinitive(vp):
    require(vp, VP)
    if vp.auxiliary == "can":
        raise ValueError("modal can has no to-infinitive in this subset")
    return seq("gf.infVP", vp.verb.base, vp.tail)


@rule("gf.UseV", "VerbEng.gf", "UseV, predV", tags=("intransitive", "verb", "action"))
def use_v(verb: Verb) -> VP:
    """Intransitive verb: the kitten rested. Rejects verbs requiring a complement."""
    accepts(verb, "V")
    return VP(verb, text(""), "gf.UseV")


@rule("gf.ComplV2", "VerbEng.gf", "SlashV2a + ComplSlash", tags=("transitive", "object", "case", "action"))
def transitive(verb: Verb, obj: NP) -> VP:
    """Saturate a transitive verb with an object-case NP: Nia thanked him."""
    accepts(verb, "V2"); require(obj, NP)
    return VP(verb, obj.object, "gf.ComplV2")


@rule("gf.ComplVV", "VerbEng.gf", "ComplVV, infVP", tags=("complement", "intention", "infinitive", "hope"))
def intention(verb: Verb, action: VP) -> VP:
    """Verb + to-infinitive: hoped to play. A noun is not a valid complement."""
    accepts(verb, "VV"); require(action, VP)
    return VP(verb, seq("gf.ComplVV", "to", infinitive(action)), "gf.ComplVV")


@rule("gf.ComplVS", "VerbEng.gf", "ComplVS", tags=("complement", "report", "clause", "thought"))
def report(verb: Verb, sentence: Sentence) -> VP:
    """Verb + that-clause: realized that the ladder could reach the ledge."""
    accepts(verb, "VS"); require(sentence, Sentence)
    return VP(verb, seq("gf.ComplVS", "that", sentence.node), "gf.ComplVS")


@rule("gf.ComplV3", "VerbEng.gf", "Slash2V3 + ComplSlash (double-object subset)", tags=("recipient", "give", "complement"))
def give(verb: Verb, recipient: NP, obj: NP) -> VP:
    """Double object construction: Dad brought her the ladder."""
    accepts(verb, "V3"); require(recipient, NP); require(obj, NP)
    return VP(verb, seq("gf.ComplV3", recipient.object, obj.object), "gf.ComplV3")


@rule("gf.ComplV2V", "VerbEng.gf", "SlashV2V + ComplSlash (to-infinitive subset)", tags=("invitation", "ask", "complement", "infinitive"))
def request(verb: Verb, obj: NP, action: VP) -> VP:
    """Object + to-infinitive: Nia asked Mateo to play; used tape to mend it."""
    accepts(verb, "V2V"); require(obj, NP); require(action, VP)
    return VP(verb, seq("gf.ComplV2V", obj.object, "to", infinitive(action)), "gf.ComplV2V")


@rule("gf.UseComp", "VerbEng.gf", "UseComp, CompAP, CompAdv", tags=("copula", "state", "location", "agreement"))
def copula(complement: AP | Adv) -> VP:
    """Copula with adjective or location: the drums were quiet/on the shelf."""
    if not isinstance(complement, (AP, Adv)):
        raise TypeError("copula expects an adjective or adverbial in this subset")
    return VP(Verb("be", "is", "was", "been", "being", ()), complement.node, "gf.UseComp", "be")


@rule("gf.ModalVV", "ResEng.gf", "infVP VVAux, predVV", tags=("modal", "ability", "infinitive"))
def can(action: VP) -> VP:
    """Modal can/could takes a bare infinitive, unlike want/hope + to."""
    require(action, VP)
    return VP(Verb("can", "can", "could", "", "", ()), infinitive(action), "gf.ModalVV", "can")


@rule("gf.AdvVP", "VerbEng.gf", "AdvVP", tags=("modifier", "instrument", "location", "manner"))
def modify(action: VP, modifier: Adv) -> VP:
    """Attach a VP modifier while preserving its verb features and complements."""
    require(action, VP); require(modifier, Adv)
    return replace(action, tail=seq("gf.AdvVP", action.tail, modifier.node))


@rule("local.PrepNP", "https://www.grammaticalframework.org/lib/doc/synopsis/index.html", "PrepNP (adapted)",
      tags=("preposition", "location", "instrument", "case"))
def prep_np(preposition: str, obj: NP) -> Adv:
    """Preposition takes object case: with him, beside the drum."""
    require(obj, NP)
    return Adv(seq("local.PrepNP", preposition, obj.object))


def realize(action, agreement, tense, negative):
    require(action, VP)
    return seq(action.label, seq("gf.finite", finite(action.verb, agreement, tense, negative, action.auxiliary)), action.tail)
