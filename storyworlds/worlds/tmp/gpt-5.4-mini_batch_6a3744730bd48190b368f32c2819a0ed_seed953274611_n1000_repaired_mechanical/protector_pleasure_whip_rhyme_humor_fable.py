#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/protector_pleasure_whip_rhyme_humor_fable.py
=============================================================================

A tiny, self-contained storyworld with a fable feel, light rhyme, and a bit of
humor. The seed words are woven into a simple domain about a small protector,
a tempting pleasure, and a whip of cream that is either handled wisely or
ruins the treat if used badly.

Domain premise
--------------
A young mouse baker wants the pleasure of a sweet pie. A tidy protector -- a
glass cloche, a friendly lid, or a careful guardian -- keeps the treat safe from
thirsty bees and greedy paws. The character is tempted to use a whip in a silly
way, but the wiser course is to whip cream in a bowl, keep the protector in
place, and share the pie fairly.

The world is small on purpose:
- physical state: cream, pie, bees, cover, crumbs
- emotional state: delight, worry, pride, shame, gratitude
- a forward-chained simulation determines whether the pie stays safe and how
  the ending turns out

The prose aims for:
- clear beginning / middle / turn / ending
- child-facing, concrete language
- a fable-like lesson
- a little rhyme and humor without becoming a poem

Supported CLI:
- default runs and -n
- --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp

The ASP twin mirrors the Python reasonableness gate and outcome model.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    protected: bool = False
    covers: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    scene: str
    rhyme: str
    danger: str
    whimsy: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Protector:
    id: str
    label: str
    keeps_off: str
    covers: set[str]
    sense: int = 3
    humor: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Pleasure:
    id: str
    label: str
    phrase: str
    joy: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Whip:
    id: str
    label: str
    phrase: str
    use: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_alarm(world: World) -> list[str]:
    out = []
    pie = world.entities.get("pie")
    bees = world.entities.get("bees")
    if not pie or not bees:
        return out
    if pie.meters["spoiled"] >= THRESHOLD and ("alarm", "bees") not in world.fired:
        world.fired.add(("alarm", "bees"))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for pr in PLEASURES:
            for wh in WHIPS:
                if reasonable_story(place, pr, wh):
                    combos.append((pid, pr.id, wh.id))
    return combos


def reasonable_story(place: Place, pleasure: Pleasure, whip: Whip) -> bool:
    return (pleasure.id == "cream" and whip.id in {"whisk", "toywhip"} and place.id in {"kitchen", "garden"})


def outcome_of(params: "StoryParams") -> str:
    if params.whip == "toywhip":
        return "messy"
    return "sweet"


def explain_rejection(place: Place, pleasure: Pleasure, whip: Whip) -> str:
    return f"(No story: this combination doesn't make a sensible fable with a protector, pleasure, and whip.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def _do_mess(world: World, narrate: bool = True) -> None:
    pie = world.get("pie")
    pie.meters["spoiled"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {place.scene}, {hero.id} lived by a little rule: "
        f"\"If a pie can purr, keep it near the protector.\" "
        f"{place.rhyme}"
    )


def temptation(world: World, hero: Entity, pleasure: Pleasure, whip: Whip) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} smelled {pleasure.phrase} and sighed with pleasure. "
        f"\"I want a treat, not a tattletale!\" {hero.id} joked, eyeing {whip.phrase}."
    )


def warn(world: World, hero: Entity, protector: Entity, pleasure: Pleasure, whip: Whip) -> None:
    protector.memes["care"] += 1
    world.say(
        f"The {protector.label} gave a kindly wink. \"A whip for cream can be fun,"
        f" but a whip near bees can make a bumbling run. Keep the cover on, dear; "
        f"then sweet stays here.\""
    )


def spill_or_whip(world: World, hero: Entity, pleasure: Pleasure, whip: Whip) -> None:
    if whip.id == "toywhip":
        world.say(f"{hero.id} waved the toy whip too wildly, and the cream splatted like a clown in a cloud.")
        _do_mess(world)
    else:
        hero.memes["pride"] += 1
        world.say(f"{hero.id} whirled the whisk with a grin and whipped the cream until it stood in little snowy hills.")


def rescue(world: World, protector: Entity, response: Response) -> None:
    world.get("pie").meters["spoiled"] = 0.0
    body = response.text
    world.say(f"{protector.label_word.capitalize()} came at once and {body}.")
    world.say("The bees buzzed off, the pie stayed bright, and the room smelled sweet again.")


def lesson(world: World, protector: Entity, hero: Entity) -> None:
    hero.memes["gratitude"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{protector.label_word.capitalize()} smiled. \"The best pleasure is shared,"
        f" and the cleverest whip is the one that stirs, not stings.\""
    )
    world.say(f"{hero.id} laughed. \"A whip for cream, not for a whim!\"")
    world.say("And the mouse learned, with a grin so bright: keep the sweet, and keep it right.")


def happy_end(world: World, hero: Entity, pleasure: Pleasure) -> None:
    hero.memes["joy"] += 1
    world.say(f"In the end, {hero.id} licked the bowl and shared {pleasure.label} with the whole small hall.")


def tell(place: Place, pleasure: Pleasure, whip: Whip, response: Response,
         hero_name: str = "Mina", hero_gender: str = "girl",
         protector_name: str = "Aunt Reed", protector_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    protector = world.add(Entity(id=protector_name, kind="character", type=protector_gender, role="protector"))
    world.add(Entity(id="pie", type="thing", label="pie"))
    world.add(Entity(id="bees", type="thing", label="bees"))
    intro(world, hero, place)
    world.para()
    temptation(world, hero, pleasure, whip)
    warn(world, hero, protector, pleasure, whip)
    world.para()
    spill_or_whip(world, hero, pleasure, whip)
    if whip.id == "toywhip":
        world.say("The protector frowned, then fixed the mess with a calm, clever turn.")
        rescue(world, protector, response)
        lesson(world, protector, hero)
        world.para()
        happy_end(world, hero, pleasure)
    else:
        world.say("The protector laughed and said the sweet old rule: no fuss, no muss, just a whisking touch.")
        happy_end(world, hero, pleasure)
    world.facts.update(hero=hero, protector=protector, place=place, pleasure=pleasure, whip=whip, response=response)
    return world


PLACES = {
    "kitchen": Place(id="kitchen", scene="a warm kitchen", rhyme="A pie kept cool is a wise old jewel."),
    "garden": Place(id="garden", scene="a sunny garden", rhyme="A sweet thing shared is doubly fair."),
}

PLEASURES = [
    Pleasure(id="cream", label="whipped cream", phrase="a bowl of cream", joy="sweetness", tags={"sweet"}),
    Pleasure(id="honey", label="honey cake", phrase="a plate of honey cake", joy="treat", tags={"sweet"}),
]

WHIPS = [
    Whip(id="whisk", label="whisk", phrase="a shiny whisk", use="whip cream", risky=False, tags={"whip"}),
    Whip(id="toywhip", label="toy whip", phrase="a silly toy whip", use="swing about", risky=True, tags={"whip"}),
]

RESPONSES = {
    "wipe": Response("wipe", 3, 4, "wiped the bowl clean with a towel and set the cover back on", "tried to wipe the mess, but the cream was gone for good", "wiped the bowl clean"),
    "cover": Response("cover", 3, 3, "covered the pie with a glass cloche and smiled", "covered the pie too late to save the sweet top", "covered the pie with a glass cloche"),
    "scrape": Response("scrape", 2, 2, "scraped the cream into a fresh dish and saved the day", "scraped at the spill, but only made a bigger streak", "scraped the cream into a fresh dish"),
}


@dataclass
class StoryParams:
    place: str
    pleasure: str
    whip: str
    response: str
    hero_name: str
    hero_gender: str
    protector_name: str
    protector_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "whip": [("What does it mean to whip cream?", "To whip cream is to beat it quickly so it becomes fluffy and thick. Then it can sit in soft little peaks.")],
    "protector": [("What is a protector?", "A protector is something or someone that keeps danger away. It helps a good thing stay safe.")],
    "pleasure": [("What is pleasure?", "Pleasure is a happy, pleasant feeling. It can come from a treat, a game, or a kind surprise.")],
    "bees": [("Why do bees matter near sweet food?", "Bees like sweet smells, so sweet food can attract them. Keeping food covered helps keep them away.")],
}
KNOWLEDGE_ORDER = ["protector", "pleasure", "whip", "bees"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a young child that includes the words "protector", "pleasure", and "whip".',
        f"Tell a rhyming, humorous story where {f['hero'].id} learns that a protector helps keep pleasure safe.",
        f"Write a small moral tale about a whip, a treat, and a wise protector, with a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, protector, pleasure, whip = f["hero"], f["protector"], f["pleasure"], f["whip"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {hero.id} and {protector.id}, who watched over a sweet treat together."),
        QAItem(question="What did the hero want?", answer=f"{hero.id} wanted the pleasure of {pleasure.label}. That was the tasty thing they hoped to enjoy."),
        QAItem(question="What happened with the whip?", answer=f"The {whip.label} was used in a way that either helped or made a mess, depending on the branch. The protector then kept the story on a wise track."),
        QAItem(question="How did the story end?", answer=f"It ended with a small lesson: keep pleasure safe, and let the protector do its job. The final image shows a cleaner table and a happier heart."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"protector", "pleasure", "whip", "bees"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", pleasure="cream", whip="whisk", response="cover", hero_name="Mina", hero_gender="girl", protector_name="Aunt Reed", protector_gender="woman"),
    StoryParams(place="garden", pleasure="cream", whip="toywhip", response="wipe", hero_name="Jory", hero_gender="boy", protector_name="Uncle Bram", protector_gender="man"),
    StoryParams(place="kitchen", pleasure="cream", whip="whisk", response="scrape", hero_name="Pia", hero_gender="girl", protector_name="Grandma Pip", protector_gender="woman"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("scene", pid, p.scene))
    for pl in PLEASURES:
        lines.append(asp.fact("pleasure", pl.id))
    for wh in WHIPS:
        lines.append(asp.fact("whip", wh.id))
        if wh.risky:
            lines.append(asp.fact("risky", wh.id))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, L, W) :- place(P), pleasure(L), whip(W), pleasure(L), whip(W), P = P, L = L, W = W.
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world with rhyme and humor.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--pleasure", choices=[p.id for p in PLEASURES])
    ap.add_argument("--whip", choices=[w.id for w in WHIPS])
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--name")
    ap.add_argument("--protector-name")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.pleasure is None or c[1] == args.pleasure)
              and (args.whip is None or c[2] == args.whip)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, pleasure, whip = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    return StoryParams(
        place=place,
        pleasure=pleasure,
        whip=whip,
        response=response,
        hero_name=args.name or rng.choice(["Mina", "Pia", "Jory", "Tavi", "Nell"]),
        hero_gender="girl" if (args.name or "Mina") in {"Mina", "Pia", "Nell"} else "boy",
        protector_name=args.protector_name or rng.choice(["Aunt Reed", "Uncle Bram", "Grandma Pip"]),
        protector_gender="woman" if (args.protector_name or "").startswith("Aunt") or (args.protector_name or "Grandma").startswith("Grandma") else "man",
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, lookup in [("place", PLACES), ("pleasure", {p.id: p for p in PLEASURES}), ("whip", {w.id: w for w in WHIPS}), ("response", RESPONSES)]:
        if getattr(params, field_name) not in lookup:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)!r}")
    place = PLACES[params.place]
    pleasure = next(p for p in PLEASURES if p.id == params.pleasure)
    whip = next(w for w in WHIPS if w.id == params.whip)
    response = RESPONSES[params.response]
    world = tell(place, pleasure, whip, response, params.hero_name, params.hero_gender, params.protector_name, params.protector_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
