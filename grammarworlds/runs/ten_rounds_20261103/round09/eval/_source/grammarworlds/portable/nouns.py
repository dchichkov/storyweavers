"""Feature-carrying noun phrase rules adapted from GF NounEng.

Subset: simple determiners, prenominal adjectives, case, possession, coordination.
"""
from ..grammar import Node, seq, text, expand, choice
from .catalog import rule
from .features import Agreement, AP, Adv, CN, NP, require
from .morphology import plural


def genitive(node):
    alternatives, weights = [], []
    for tokens, probability, rules in expand(node):
        last = tokens[-1]
        tail = last + ("'" if last.endswith("s") else "'s")
        part = Node("text", "lexical", tokens[:-1] + (tail,))
        for label in rules:
            part = seq(label, part)
        alternatives.append(part); weights.append(probability)
    return choice("local.genitive", *alternatives, weights=tuple(weights))


@rule("gf.UseN", "NounEng.gf", "UseN", dependencies=("gf.regN",), tags=("noun", "lexicon"))
def use_n(word: str, entry: dict) -> CN:
    """Lift a lexical noun into a common noun, preserving number and mass status."""
    return CN(seq("gf.UseN", word), seq("gf.UseN", entry.get("plural", plural(word))), entry.get("mass", False))


@rule("gf.AdjCN", "NounEng.gf", "AdjCN", tags=("adjective", "noun", "description"))
def adj_cn(adjective: AP, noun: CN) -> CN:
    """Prenominal positive adjective; noun number and mass status are preserved."""
    require(adjective, AP); require(noun, CN)
    return CN(seq("gf.AdjCN", adjective.node, noun.singular),
              seq("gf.AdjCN", adjective.node, noun.plural), noun.mass)


@rule("gf.AdvCN", "NounEng.gf", "AdvCN", tags=("noun", "location", "modifier"))
def adv_cn(noun: CN, modifier: Adv) -> CN:
    """Attach a postnominal modifier: the drum on the shelf."""
    require(noun, CN); require(modifier, Adv)
    return CN(seq("gf.AdvCN", noun.singular, modifier.node), seq("gf.AdvCN", noun.plural, modifier.node), noun.mass)


@rule("gf.DetCN", "NounEng.gf", "DetCN, IndefArt, MassNP", tags=("determiner", "noun", "agreement", "article"))
def det_cn(noun: CN, determiner="the", number="singular") -> NP:
    """Determiner + noun binds NP agreement. a/an follows the first surface word.

    Supported determiners: the, a, bare; a mass noun cannot take singular a.
    """
    require(noun, CN)
    agreement = Agreement(number)
    if determiner not in {"the", "a", "bare"}:
        raise ValueError("unsupported determiner")
    if noun.mass and determiner == "a" and number == "singular":
        raise ValueError("mass noun cannot take singular indefinite article")
    n = noun.plural if number == "plural" else noun.singular
    det = "" if determiner == "bare" or (determiner == "a" and number == "plural") else determiner
    if det == "a":
        alternatives, weights = [], []
        for tokens, probability, rules in expand(n):
            first = tokens[0].lower()
            # Selected English orthographic article rule, with explicit sound exceptions.
            an = first.startswith(("honest", "hour", "honor", "heir")) or (
                first[0] in "aeiou" and not first.startswith(("uni", "use", "euro", "one")))
            node = seq("gf.DetCN", "an" if an else "a", seq("noun.surface", *tokens))
            for label in rules:
                node = seq(label, node)
            alternatives.append(node); weights.append(probability)
        surface = choice("gf.IndefArt", *alternatives, weights=tuple(weights))
    else:
        surface = seq("gf.DetCN", det, n)
    return NP(surface, surface, genitive(surface), agreement)


@rule("gf.UsePN", "NounEng.gf", "UsePN", tags=("proper", "name", "reference"))
def proper(name: str, number="singular") -> NP:
    """A proper name has third-person agreement and a genitive form."""
    node = seq("gf.UsePN", name)
    return NP(node, node, seq("gf.UsePN", name + "'s"), Agreement(number))


@rule("gf.UsePron", "NounEng.gf", "UsePron, PossPron", tags=("pronoun", "case", "reference", "possession"))
def pronoun(form: str) -> NP:
    """Pronoun features carry subject, object, possessive case, number, and person."""
    forms = {"she": ("her", "her", "singular", 3), "he": ("him", "his", "singular", 3),
             "it": ("it", "its", "singular", 3), "they": ("them", "their", "plural", 3),
             "I": ("me", "my", "singular", 1), "you": ("you", "your", "singular", 2),
             "we": ("us", "our", "plural", 1)}
    obj, poss, number, person = forms[form]
    return NP(*(seq("gf.UsePron", s) for s in (form, obj, poss)), Agreement(number, person))


@rule("gf.PossPron", "NounEng.gf", "PossPron, DetCN", dependencies=("gf.UsePron",), tags=("possession", "pronoun"))
def possess(owner: NP, noun: CN, number="singular") -> NP:
    """Possessive determiner: her drum; agreement follows drum, not the owner."""
    require(owner, NP); require(noun, CN)
    surface = seq("gf.PossPron", owner.possessive, noun.plural if number == "plural" else noun.singular)
    return NP(surface, surface, genitive(surface), Agreement(number))


@rule("local.ConjNP", "https://www.grammaticalframework.org/lib/doc/synopsis/index.html", "ConjNP (adapted)",
      tags=("coordination", "agreement", "plural"))
def both(left: NP, right: NP) -> NP:
    """Coordinate two noun phrases; the result takes plural agreement."""
    require(left, NP); require(right, NP)
    return NP(*(seq("local.ConjNP", getattr(left, c), "and", getattr(right, c))
                for c in ("subject", "object", "possessive")), Agreement("plural", min(left.agreement.person, right.agreement.person)))
