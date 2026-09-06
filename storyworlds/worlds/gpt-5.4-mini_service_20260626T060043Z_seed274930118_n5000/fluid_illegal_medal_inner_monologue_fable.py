#!/usr/bin/env python3
"""
storyworlds/worlds/fluid_illegal_medal_inner_monologue_fable.py
===============================================================

A small, fable-like story world about a prized medal, a sneaky forbidden plan,
and the inner monologue that helps a character choose the honest path.

Seed tale, reimagined as a simulation:
---
In a small meadow village, a young crow found a medal left on a bench after the
summer games. The medal was shiny, heavy, and very important to the old judge
who owned it. A squirrel friend whispered that they could coat the medal with
glossy fluid and claim it as a new prize for themselves. That was illegal, and
the crow knew it. The crow listened to the loud wish inside its own head, then
spoke honestly, returned the medal, and earned trust instead of trouble.

World instruments:
---
- physical meters: shine, fluid, weight, distance, safety
- emotional memes: pride, greed, guilt, fear, trust, relief
- narrative feature: Inner Monologue
- style: Fable
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    kept_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fluid: object | None = None
    helper: object | None = None
    hero: object | None = None
    judge: object | None = None
    medal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "swan"}
        male = {"boy", "father", "dad", "man", "crow", "fox", "squirrel", "judge", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    w: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "crow"
    helper: str = "squirrel"
    judge: str = "judge"
    place: str = "the meadow court"
    medal_owner: str = "judge"
    hero_name: str = "Cora"
    helper_name: str = "Moss"
    judge_name: str = "Old Bram"
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


HERO_NAMES = ["Cora", "Pip", "Rowan", "Nico", "Tavi", "Luma"]
HELPER_NAMES = ["Moss", "Bramble", "Wren", "Tansy", "Juniper", "Reed"]
JUDGE_NAMES = ["Old Bram", "Lady Alder", "Master Thorne", "Judge Willow"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world about a medal, fluid, and an illegal choice.")
    ap.add_argument("--hero", choices=["crow", "fox", "squirrel"])
    ap.add_argument("--helper", choices=["crow", "fox", "squirrel"])
    ap.add_argument("--judge", choices=["judge", "elder"])
    ap.add_argument("--place")
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--judge-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(["crow", "fox", "squirrel"])
    helper = getattr(args, "helper", None) or rng.choice([x for x in ["crow", "fox", "squirrel"] if x != hero])
    if getattr(args, "helper", None) and getattr(args, "helper", None) == hero:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(["the meadow court", "the oak path", "the river bridge"])
    if "court" not in place and "bridge" not in place and "path" not in place:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero=hero,
        helper=helper,
        judge=getattr(args, "judge", None) or "judge",
        place=place,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        judge_name=getattr(args, "judge_name", None) or rng.choice(JUDGE_NAMES),
    )


def make_world(params: StoryParams) -> World:
    w = World(params.place)
    hero = w.add(Entity(
        id="hero", kind="character", type=params.hero, label=params.hero_name,
        meters={"distance": 0.0, "safety": 1.0},
        memes={"pride": 1.0, "greed": 0.0, "guilt": 0.0, "fear": 0.0, "trust": 0.2, "relief": 0.0},
    ))
    helper = w.add(Entity(
        id="helper", kind="character", type=params.helper, label=params.helper_name,
        meters={"distance": 0.0}, memes={"curiosity": 0.7, "greed": 0.4, "guilt": 0.0, "trust": 0.2},
    ))
    judge = w.add(Entity(
        id="judge", kind="character", type="judge", label=params.judge_name,
        meters={"distance": 2.0}, memes={"trust": 0.4, "calm": 1.0},
    ))
    medal = w.add(Entity(
        id="medal", kind="thing", type="medal", label="medal",
        phrase="the shining medal",
        owner=judge.id, caretaker=judge.id, kept_by=judge.id,
        meters={"shine": 1.0, "fluid": 0.0, "weight": 1.0, "safety": 1.0},
    ))
    fluid = w.add(Entity(
        id="fluid", kind="thing", type="fluid", label="glossy fluid",
        phrase="the glossy fluid",
        meters={"fluid": 1.0, "shine": 0.8},
    ))
    w.facts.update(hero=hero, helper=helper, judge=judge, medal=medal, fluid=fluid)
    return w


FABLE_ARCS = [
    {
        "title": "rain-barrel ribbons",
        "fluid": "blue rain-barrel dye",
        "premise": "the village was hanging ribbons for its rainy-day games",
        "find": "beneath the judges' awning, still tied to a winner's blue ribbon",
        "plan": "dip the ribbon in blue fluid, replace it with a plain cord, and claim the medal as a new prize",
        "harm": "the dye would stain the winner's ribbon and hide the mark that proved who earned it",
        "action": "set the bottle upright, wrapped the medal in a clean leaf, and asked the ribbon keeper to check the winners' list",
        "repair": "The keeper matched the blue ribbon to a young hare and returned the medal before the games began",
        "response": "praised the careful check, while the hare thanked them with a shy bow",
        "ending": "the true medal flashed above the finish line, and an unstained blue ribbon fluttered in the rain",
        "moral": "A borrowed shine never becomes an earned one.",
    },
    {
        "title": "sap over the engraving",
        "fluid": "clear pine sap",
        "premise": "the village was hosting a harvest contest",
        "find": "in a bed of fallen leaves, engraved with the name of last year's champion",
        "plan": "brush sticky fluid over the engraving and claim that the nameless medal had just been found",
        "harm": "the sap could seal dirt into the letters and erase part of the village's history",
        "action": "moved the sap away, compared the engraving with the honor board, and called for the contest steward",
        "repair": "The steward cleaned one corner with warm water, read the champion's name, and placed the medal in its display case",
        "response": "thanked them for protecting both the medal and the memory attached to it",
        "ending": "late sunlight filled every engraved letter while clean pinecones rested below the case",
        "moral": "Truth keeps old honors bright.",
    },
    {
        "title": "oil at the bridge",
        "fluid": "a jar of slippery seed oil",
        "premise": "boats were gathering for a lantern parade",
        "find": "beside a loose bridge plank, where a parade judge had dropped it",
        "plan": "grease the medal with fluid, slide it beneath the plank, and collect it later when nobody is watching",
        "harm": "oil near the river could make the bridge slick and send the medal into the current",
        "action": "capped the oil, marked the loose plank with a red scarf, and carried the medal to the lantern marshal",
        "repair": "The marshal fastened the plank and locked the medal in the parade chest until its owner arrived",
        "response": "said that guarding the bridge mattered even more than guarding a prize",
        "ending": "lanterns drifted under a dry bridge while the safe medal waited inside its locked parade chest",
        "moral": "A secret shortcut can endanger more than the secret.",
    },
    {
        "title": "berry-ink disguise",
        "fluid": "purple blackberry ink",
        "premise": "young artists were painting signs for the village fair",
        "find": "on the sign-painting table, beside a card naming its owner",
        "plan": "paint the medal purple with fluid and enter it in the fair as a brand-new sculpture",
        "harm": "the sour ink could darken the metal and turn another person's honor into a dishonest display",
        "action": "covered the ink cup, read the owner's card aloud, and carried both card and medal to the fair office",
        "repair": "The clerk wiped away one stray purple drop and sent a bell-ringer to find the owner",
        "response": "gave them blank tin circles to paint honestly instead of taking a finished medal",
        "ending": "their little painted moons hung beside the fair gate, while the medal shone in its owner's green sash",
        "moral": "Making something small is better than stealing something grand.",
    },
    {
        "title": "glue and the false sash",
        "fluid": "milky craft glue",
        "premise": "the schoolhouse animals were preparing a kindness ceremony",
        "find": "under a sewing stool, with a broken loop on its red ribbon",
        "plan": "use sticky fluid to fasten the medal to a spare sash and walk into the ceremony as winners",
        "harm": "the glue could ruin the ribbon, and the false claim would take applause from the child who had helped others",
        "action": "put the glue on a high shelf, showed the broken loop to the teacher, and offered thread for a proper repair",
        "repair": "The teacher stitched the loop, checked the ceremony book, and found the medal's worried recipient",
        "response": "invited both friends to help hand out programs because they had corrected their choice",
        "ending": "the repaired red ribbon rested over the right heart as paper programs rustled down every row",
        "moral": "Kindness cannot be glued onto a dishonest claim.",
    },
    {
        "title": "soap and the maker's mark",
        "fluid": "a bowl of strong washing soap",
        "premise": "market day had filled the lanes with carts and bells",
        "find": "near a silversmith's cart, stamped with the maker's tiny leaf",
        "plan": "scrub away the leaf with soapy fluid and trade the medal at another stall",
        "harm": "rough soap could scratch the medal, and selling found property would be illegal",
        "action": "left the bowl untouched, traced the tiny leaf on paper, and asked nearby sellers who used that mark",
        "repair": "A potter recognized the silversmith's leaf and led them to the owner before the market closed",
        "response": "showed them how a maker's mark helps lost treasures travel home",
        "ending": "the medal chimed softly against the silversmith's tools as the last market bell rang",
        "moral": "Honest questions uncover what scrubbing tries to hide.",
    },
    {
        "title": "wax over a crack",
        "fluid": "warm beeswax",
        "premise": "the village museum was airing its oldest keepsakes",
        "find": "near a display cloth, with a hairline crack across its back",
        "plan": "pour waxy fluid into the crack, hide the damage, and sell the medal as perfect",
        "harm": "hot wax might widen the crack, and hiding damage would cheat any buyer",
        "action": "blew out the warming candle, padded a small box with moss, and reported the crack to the curator",
        "repair": "The curator placed the medal in the padded box and wrote a truthful repair note for the conservator",
        "response": "said that admitting damage is the first careful step toward mending it",
        "ending": "the cracked medal rested safely on moss, its honest label glowing beneath a cool museum lamp",
        "moral": "A truthful flaw is safer than a hidden one.",
    },
    {
        "title": "paint-water switch",
        "fluid": "golden paint water",
        "premise": "a costume procession was forming nearby",
        "find": "inside an open costume trunk, next to a wooden pretend medal",
        "plan": "color the wooden token with golden fluid, swap it for the real medal, and keep the real one",
        "harm": "the switch would fool the performers and steal an object trusted to the costume keeper",
        "action": "separated the two medals, closed the paint jar, and called the keeper before anyone dressed for the parade",
        "repair": "The keeper counted both props, locked away the real medal, and let them safely paint the wooden one",
        "response": "explained that pretending onstage is fun, but tricking people offstage is wrong",
        "ending": "a wooden medal sparkled in the procession while the real one waited behind a brass lock",
        "moral": "Playful pretending must stop where deceit begins.",
    },
    {
        "title": "syrup and the borrowed sash",
        "fluid": "sticky maple syrup",
        "premise": "breakfast cooks were setting tables for a woodland thank-you feast",
        "find": "folded inside a borrowed sash that had slipped from a chair",
        "plan": "dab syrupy fluid under the medal so it would stick to a coat, then say it had always been there",
        "harm": "the syrup would stain the sash and turn a simple lost-and-found problem into stealing",
        "action": "washed away a sticky drop, hung the sash where everyone could see it, and rang the lost-property bell",
        "repair": "The feast captain followed the bell, named the sash's owner, and checked that the medal was dry",
        "response": "served them warm oatcakes for choosing to call attention rather than hide evidence",
        "ending": "steam curled above honest oatcakes while the clean medal lay on its blue sash",
        "moral": "What sticks to a lie is harder to wash away than syrup.",
    },
    {
        "title": "lamp-oil polish",
        "fluid": "smoky lamp oil",
        "premise": "the village night watch was beginning",
        "find": "near an empty watch post, dull from years of use",
        "plan": "polish it with lamp fluid, call it newly made, and demand a reward for bringing it",
        "harm": "lamp oil could stain the old medal, and inventing a reward would turn helpfulness into fraud",
        "action": "trimmed the lamp safely, noted where the medal lay, and fetched the watch captain without asking for payment",
        "repair": "The captain recognized the medal as the watch's service badge and returned it to its hook",
        "response": "offered sincere thanks, which felt better than a reward won by a lie",
        "ending": "the service medal hung above the watch log as one steady lamp lit the bridge",
        "moral": "Service shines best when it does not bargain for praise.",
    },
    {
        "title": "clay copy",
        "fluid": "silky clay slip",
        "premise": "potters were shaping keepsakes for the spring festival",
        "find": "on a drying board, beside a note asking that it be copied for the village archive",
        "plan": "press the medal into wet fluid clay, hand over the copy, and secretly keep the original",
        "harm": "a clay copy could be useful only if everyone knew it was a copy; switching it would be illegal theft",
        "action": "asked the archivist for permission, labeled the clay impression COPY, and kept the original in sight",
        "repair": "Together they fired the labeled copy and returned the real medal to its padded archive drawer",
        "response": "commended them for turning a dishonest idea into an honest craft lesson",
        "ending": "the clay copy stood beneath a clear label while the real medal gleamed safely behind glass",
        "moral": "A copy teaches only when it tells the truth about what it is.",
    },
    {
        "title": "muddy medal at the pond",
        "fluid": "clear pond water",
        "premise": "gardeners were cleaning paths after a windy sports day",
        "find": "half hidden in mud beside the pond, with one ribbon end pointing toward the playing field",
        "plan": "rinse it in the fluid, pocket the clean medal, and say the mud had held nothing",
        "harm": "cleaning the medal would not make it theirs, and silence would keep its owner searching",
        "action": "rinsed only enough mud to read the number, left a marker at the spot, and brought the medal to lost property",
        "repair": "The games judge matched the number to a runner who had been retracing every path in tears",
        "response": "thanked them for using the clue to return the medal instead of using the mud to hide it",
        "ending": "the runner's muddy shoes stopped at last, and a clean medal swung from the proper ribbon",
        "moral": "Finding what is hidden does not make it yours.",
    },
]


INNER_THOUGHTS = [
    "Wanting it does not change who owns it. What choice would I wish someone made with my treasure?",
    "The plan sounds clever only while I ignore who gets hurt. I can stop it before clever becomes cruel.",
    "My stomach feels knotted because I already know the rule. Courage means listening before the knot becomes guilt.",
    "Nobody may be watching, but I will remember. I would rather carry the truth than hide the medal.",
    "A bright object cannot brighten a lie. First I should protect it, then find the person who can prove its story.",
    "Being a friend does not mean agreeing with a wrong idea. A good friend can say no and help make things right.",
    "If I pause and check the clues, I can choose with facts instead of wishing. The owner's mark deserves an honest answer.",
    "The illegal part is not just a rule on paper. Someone trusted this medal to be returned, and that trust matters.",
]


REFUSALS = [
    '"Stop," {hero} said. "We are not changing or hiding a medal that belongs to someone else."',
    'Before the fluid moved another inch, {hero} stepped between the bottle and the medal. "No trick. We tell the truth."',
    '"I nearly followed your idea," {hero} admitted, "but it is illegal and it could cause real harm. Help me put it right."',
    '{hero} took one slow breath. "A friend can disagree," {hero} said. "I will protect the medal, and I hope you will help."',
    '"Let us test the honest path first," {hero} said. "We can follow the clues without damaging anything."',
    '{hero} shook their head. "Winning praise with somebody else\'s medal would not be winning at all."',
]


OPENINGS = [
    "On a morning when {premise}, {hero} and {helper} met at {place}.",
    "Every creature at {place} seemed busy because {premise}. Only {hero} and {helper} noticed something out of place.",
    "The bells at {place} had barely rung when {hero} joined {helper}; {premise}.",
    "Long ago, when {premise}, two friends named {hero} and {helper} crossed {place} together.",
    "At {place}, {premise}. That was where {hero} and {helper} faced a choice no contest could score.",
    "The day began cheerfully at {place}: {premise}. Then {hero} spotted a glint that changed the morning.",
]


TURN_LINKS = [
    "For one breath, the plan felt easy. Then {hero} listened inward instead of reaching outward.",
    "The bottle tipped, and the medal's reflection trembled. Inside, {hero}'s wish argued with a quieter, wiser voice.",
    "No grown-up stood nearby. That silence made {hero}'s inner monologue sound clearer, not weaker.",
    "The tempting idea raced ahead like a cart downhill. {hero} stopped and let one honest thought catch up.",
    "{hero} imagined owning the shine, then imagined the owner finding an empty place. The second picture changed everything.",
    "A rule alone felt small until {hero} pictured the damage the plan could cause. Then the choice became plain.",
]


def tell(params: StoryParams) -> World:
    w = make_world(params)
    hero = w.get("hero")
    helper = w.get("helper")
    judge = w.get("judge")
    medal = w.get("medal")
    fluid = w.get("fluid")

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(ch) for ch in (params.hero_name + params.helper_name + params.place))
    rng = random.Random(stable_seed ^ 0x51A7F1)
    arc = rng.choice(FABLE_ARCS)
    thought = rng.choice(INNER_THOUGHTS)
    refusal = rng.choice(REFUSALS).format(hero=hero.label)
    opening = rng.choice(OPENINGS).format(
        premise=arc["premise"], hero=hero.label, helper=helper.label, place=w.place
    )
    turn_link = rng.choice(TURN_LINKS).format(hero=hero.label)
    find_lines = [
        f"{hero.label} found a medal {arc['find']}. Its worn edge showed that it mattered to someone.",
        f"A medal caught {hero.label}'s eye {arc['find']}. It was no toy; its ribbon and marks carried an owner's history.",
        f"There lay a real medal {arc['find']}. {hero.label} lifted it only far enough to keep it from being stepped on.",
        f"Near their feet, {hero.label} noticed a medal {arc['find']}. The small object felt heavier than its size.",
    ]
    proposal_lines = [
        f"{helper.label} pointed to {arc['fluid']} and whispered, \"We could {arc['plan']}.\"",
        f"Then {helper.label} noticed {arc['fluid']}. \"What if we {arc['plan']}?\" came the whisper.",
        f"\"Here is a way to keep it,\" {helper.label} murmured, reaching toward {arc['fluid']}. \"We can {arc['plan']}.\"",
    ]

    fluid.label = arc["fluid"]
    fluid.phrase = arc["fluid"]
    helper.memes["greed"] += 0.8
    hero.memes["fear"] += 0.4
    medal.meters["fluid"] += 0.4
    medal.meters["safety"] -= 0.5
    w.facts.update(
        arc_title=arc["title"], fluid_name=arc["fluid"], illegal_plan=arc["plan"],
        possible_harm=arc["harm"], inner_thought=thought, honest_action=arc["action"],
        repair=arc["repair"], outcome=arc["response"], ending_image=arc["ending"],
        moral=arc["moral"], medal_at_risk=True,
    )

    w.say(opening)
    w.say(rng.choice(find_lines))
    w.para()
    w.say(rng.choice(proposal_lines))
    w.say(f"The idea was illegal: {arc['harm']}.")
    w.say(turn_link)
    w.say(f"{hero.label} thought, \"{thought}\"")
    w.para()
    w.say(refusal)
    w.say(f"Instead, {hero.label} {arc['action']}.")
    if rng.randrange(2):
        w.say(f"{helper.label} lowered their eyes. \"I was chasing the shine,\" they said. \"I will help with the truth.\"")
    else:
        w.say(f"After a quiet moment, {helper.label} drew back from the fluid. \"Your no stopped both of us from making it worse,\" they said.")
    w.para()
    w.say(f"{arc['repair']}.")
    w.say(f"When {judge.label} heard the whole account, {judge.label} {arc['response']}.")
    w.say(f"Before they left, {hero.label} said the lesson aloud: \"{arc['moral']}\"")
    w.say(f"By day's end, {arc['ending']}.")

    hero.memes["trust"] += 0.7
    hero.memes["relief"] += 0.8
    helper.memes["guilt"] += 0.4
    helper.memes["trust"] += 0.3
    judge.memes["trust"] += 0.6
    medal.meters["safety"] = 1.0
    medal.meters["fluid"] = 0.0
    medal.kept_by = judge.id
    medal.owner = judge.id
    w.facts["returned"] = True

    w.facts.update(
        place=w.place,
        hero_type=hero.type,
        helper_type=helper.type,
        judge_type=judge.type,
        hero_name=hero.label,
        helper_name=helper.label,
        judge_name=judge.label,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about a {f["hero_type"]} who finds a medal and uses an inner monologue to reject an illegal plan involving {f["fluid_name"]}.',
        f"Tell a gentle fable where {f['hero_name']} stops a plan to {f['illegal_plan']} and makes the medal safe.",
        f'Write a small moral story that includes the words "fluid", "illegal", and "medal".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    judge = _safe_fact(world, f, "judge")
    medal = _safe_fact(world, f, "medal")
    return [
        QAItem(
            question=f"What did {hero.label} find in the fable about {f['arc_title']}?",
            answer=f"{hero.label} found a medal that did not belong to them and kept it safe while looking for its owner.",
        ),
        QAItem(
            question=f"What illegal idea involved {f['fluid_name']}?",
            answer=f"{helper.label} proposed that they {f['illegal_plan']}.",
        ),
        QAItem(
            question=f"How did {hero.label}'s inner monologue change what happened next?",
            answer=f"{hero.label} thought, \"{f['inner_thought']}\" That thought helped them refuse the plan and choose an honest action.",
        ),
        QAItem(
            question=f"What honest action did {hero.label} take after realizing the plan could cause harm?",
            answer=f"{hero.label} {f['honest_action']}. As a result, {f['repair'].lower()}.",
        ),
        QAItem(
            question="What final image showed that the illegal plan had been stopped?",
            answer=f"At the end, {f['ending_image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a medal?",
            answer="A medal is a prize or honor, often a shiny object given for doing something well.",
        ),
        QAItem(
            question="What is fluid?",
            answer="A fluid is a liquid or a substance that can flow and spread from one place to another.",
        ),
        QAItem(
            question="What does illegal mean?",
            answer="Illegal means against the rules or against the law.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.kept_by:
            bits.append(f"kept_by={e.kept_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A medal is at risk when fluid is applied to it.
at_risk(M) :- medal(M), touched_by_fluid(M).

% Illegal plans are those that target a medal not owned by the actor.
illegal_take(H, M) :- hero(H), medal(M), owner(M, O), H != O.

% A sensible refusal happens when an illegal take would be wrong and the hero
% chooses honesty instead.
honest_choice(H) :- hero(H), not illegal_take(H, M), medal(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("judge", "judge"))
    lines.append(asp.fact("medal", "medal"))
    lines.append(asp.fact("owner", "medal", "judge"))
    lines.append(asp.fact("touched_by_fluid", "medal"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show at_risk/1. #show illegal_take/2."))
    atoms = set((sym.name, tuple(arg.name if arg.type != arg.type.Number else arg.number for arg in sym.arguments)) for sym in model)
    expected = {("at_risk", ("medal",)), ("illegal_take", ("hero", "medal"))}
    if atoms == expected:
        print("OK: ASP gate matches the Python world assumptions.")
        return 0
    print("MISMATCH between ASP and Python world assumptions.")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero=getattr(args, "hero", None) or rng.choice(["crow", "fox", "squirrel"]),
        helper=getattr(args, "helper", None) or rng.choice(["crow", "fox", "squirrel"]),
        judge=getattr(args, "judge", None) or "judge",
        place=getattr(args, "place", None) or rng.choice(["the meadow court", "the oak path", "the river bridge"]),
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        judge_name=getattr(args, "judge_name", None) or rng.choice(JUDGE_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero="crow", helper="squirrel", place="the meadow court", hero_name="Cora", helper_name="Moss", judge_name="Old Bram"),
    StoryParams(hero="fox", helper="crow", place="the oak path", hero_name="Fenn", helper_name="Wren", judge_name="Lady Alder"),
    StoryParams(hero="squirrel", helper="fox", place="the river bridge", hero_name="Pip", helper_name="Tansy", judge_name="Master Thorne"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show at_risk/1. #show illegal_take/2. #show honest_choice/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show at_risk/1. #show illegal_take/2. #show honest_choice/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_story_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
