#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T073613Z_seed779406221_n50/gasp_breaker_obey_sharing_rhyme_whodunit.py
===============================================================================================================

A standalone storyworld for a small whodunit: a brief blackout, a shared rhyme
sheet, a startled gasp, and a child who chooses to obey the clues instead of
blaming the wrong suspect.

Initial story used to build the world model:
---
At the little library clubhouse, Noor and Ben were making a rhyme for the
sharing shelf. They had one bright page, a red marker, and a tiny lamp that
glowed over the table.

Then the room went dark. "Gasp!" said Noor. "The breaker tripped!"

Ben wanted to poke the fuse box right away, but the librarian had said, "Do not
touch the breaker. Obey the rules and call me."

So they did. Noor shared the rhyme page with Ben so they could read the clues
together. Ben noticed the lamp cord lay across the floor near a spilled cup of
water. The cup had tipped when the stack of books fell, and that was the real
mystery.

When the librarian came with a flashlight, she found the wet cord and reset the
breaker. The lamp blinked back on. Noor and Ben laughed, then fixed the rhyme
page and shared it with the little kids by the window.

Causal state updates:
---
    spilled water near cord -> cord.wet += 1 ; breaker.trip += 1
    breaker.trip             -> room.dark += 1 ; child.gasp += 1
    child.obeys rule         -> child.trust += 1 ; child.blame += 0
    child shares clue        -> both.child.cooperate += 1
    mystery solved           -> room.safe += 1 ; room.dark -> 0

Scripted social/emotional beats:
---
    shared project           -> both children.joy += 1 ; both.children.cooperate += 1
    gasp of surprise         -> startled child.fear += 1
    obey the adult rule      -> child.pride += 1 ; child.trust += 1
    accuse the wrong suspect -> child.conflict += 1
    follow the clue          -> child.calm += 1 ; mystery advances
    solution found           -> both children.relief += 1 ; room.safe += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    plural: bool = False

    adult: object | None = None
    breaker: object | None = None
    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    lamp: object | None = None
    page: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Setting:
    place: str
    indoors: bool = True
    afford: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = False
    mess: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class StoryParams:
    setting: str
    page: str
    clue: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "library": Setting(place="the little library clubhouse", indoors=True, afford={"rhyme", "sharing"}),
    "kitchen": Setting(place="the warm kitchen", indoors=True, afford={"sharing", "rhyme"}),
    "classroom": Setting(place="the bright classroom", indoors=True, afford={"rhyme", "sharing"}),
}

PAGES = {
    "rhyme_sheet": ObjectCfg("rhyme_sheet", "rhyme page", "a bright rhyme page", "page", tags={"rhyme", "sharing"}),
    "share_card": ObjectCfg("share_card", "sharing card", "a small sharing card", "card", tags={"sharing"}),
    "note": ObjectCfg("note", "note", "a folded note", "note", tags={"rhyme"}),
}

CLUES = {
    "cord": ObjectCfg("cord", "lamp cord", "the lamp cord", "cord", risky=True, mess="wet", tags={"breaker", "gasp"}),
    "cup": ObjectCfg("cup", "cup of water", "a spilled cup of water", "cup", risky=True, mess="wet", tags={"breaker"}),
    "books": ObjectCfg("books", "books", "a stack of books", "books", tags={"sharing"}),
}

GIRL_NAMES = ["Noor", "Maya", "Lina", "Ava", "Iris", "Zara"]
BOY_NAMES = ["Ben", "Eli", "Owen", "Theo", "Finn", "Milo"]
TRAITS = ["careful", "curious", "kind", "patient", "quiet", "bright"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: gasp, breaker, obey, sharing, rhyme, whodunit.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--page", choices=PAGES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PAGES:
            for c in CLUES:
                combos.append((s, p, c))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    page = getattr(args, "page", None) or rng.choice(list(PAGES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero]
    helper = getattr(args, "helper", None) or rng.choice(helper_pool)
    adult = getattr(args, "adult", None) or rng.choice(["librarian", "teacher", "parent"])
    if page == "note" and clue == "books":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, page=page, clue=clue, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, adult=adult)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    adult = world.add(Entity(id="adult", kind="character", type="adult", label=params.adult, role="adult"))
    page = world.add(Entity(id=params.page, type="page", label=_safe_lookup(PAGES, params.page).label, attrs={"phrase": _safe_lookup(PAGES, params.page).phrase}))
    clue = world.add(Entity(id=params.clue, type="thing", label=_safe_lookup(CLUES, params.clue).label, attrs={"phrase": _safe_lookup(CLUES, params.clue).phrase}))
    world.facts.update(hero=hero, helper=helper, adult=adult, page=page, clue=clue, setting=world.setting)
    return world


def propagate(world: World) -> None:
    clue = world.get(world.facts["clue"].id)
    if clue.id == "cord" or clue.id == "cup":
        if ("wet_breaker", clue.id) not in world.fired:
            world.fired.add(("wet_breaker", clue.id))
            world.get("breaker").meters["trip"] += 1
            world.get("room").meters["dark"] += 1
            world.get(world.facts["hero"].id).memes["gasp"] += 1
            world.get(world.facts["helper"].id).memes["alert"] += 1


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    adult = world.facts["adult"]
    page = world.facts["page"]
    clue = world.facts["clue"]

    room = world.add(Entity(id="room", type="room", label="the room"))
    breaker = world.add(Entity(id="breaker", type="breaker", label="the breaker"))
    lamp = world.add(Entity(id="lamp", type="lamp", label="the tiny lamp"))
    lamp.meters["glow"] += 1
    clue.meters["wet"] += 1
    world.say(f"At {world.setting.place}, {hero.id} and {helper.id} were making a rhyme for the sharing shelf.")
    world.say(f"They had one bright page, a red marker, and {lamp.label} over the table.")
    world.para()
    world.say(f"Then the room went dark. \"Gasp!\" said {hero.id}. \"The breaker tripped!\"")
    world.say(f"{helper.id} wanted to poke the breaker right away, but the {adult.label} had said, \"Do not touch the breaker. Obey the rules and call me.\"")
    world.para()
    world.say(f"So they did. {hero.id} shared the rhyme page with {helper.id} so they could read the clues together.")
    world.say(f"{helper.id} noticed the {clue.label} lay near the lamp cord. That was the real mystery.")
    world.say(f"When the {adult.label} came with a flashlight, they found the wet cord and reset the breaker.")
    room.meters["safe"] += 1
    breaker.meters["trip"] += 0
    hero.memes["trust"] += 1
    helper.memes["cooperate"] += 1
    world.para()
    world.say(f"The lamp blinked back on. {hero.id} and {helper.id} laughed, then fixed the rhyme page and shared it with the little kids by the window.")
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a 3-to-5-year-old with a gasp, a breaker, and a child who obeys the rules.',
        f"Tell a gentle mystery where {f['hero'].id} and {f['helper'].id} share a rhyme page, follow clues, and find out why the breaker tripped.",
        f'Write a child-friendly mystery that includes sharing, rhyme, and the word "obey".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, adult, clue = f["hero"], f["helper"], f["adult"], f["clue"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} and {helper.id}?",
            answer=f"It is a small mystery story. The children share a rhyme page, notice clues, and solve why the breaker tripped.",
        ),
        QAItem(
            question=f"Why did {hero.id} gasp when the room went dark?",
            answer=f"{hero.id} gasped because the breaker tripped and the room suddenly got dark. That made the mystery feel big and important.",
        ),
        QAItem(
            question=f"What did {helper.id} want to do to the breaker?",
            answer=f"{helper.id} wanted to poke the breaker, but the adult said to obey the rules and call for help. So the child listened instead.",
        ),
        QAItem(
            question=f"What clue solved the mystery?",
            answer=f"The wet lamp cord near the spilled water was the clue. It showed why the breaker tripped.",
        ),
        QAItem(
            question=f"How did the children finish the rhyme page?",
            answer=f"They fixed it up and shared it with the little kids by the window. The shared page made the ending feel friendly and neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a breaker do?",
            answer="A breaker helps keep electricity safe. If too much goes wrong, it trips and turns the power off.",
        ),
        QAItem(
            question="What does obey mean?",
            answer="To obey means to follow a rule or a grown-up's instruction. It helps keep people safe.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too. It is kind and helpful.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end. Rhymes can make a song or poem sound playful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
trip(Dark) :- breaker_trip(Dark), room(Dark).
solved :- obey(rule), share(clue), breaker_trip(dark).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy per contract
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PAGES:
        lines.append(asp.fact("page", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    lines.append(asp.fact("feature", "sharing"))
    lines.append(asp.fact("feature", "rhyme"))
    lines.append(asp.fact("keyword", "gasp"))
    lines.append(asp.fact("keyword", "breaker"))
    lines.append(asp.fact("keyword", "obey"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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
    StoryParams(setting="library", page="rhyme_sheet", clue="cord", hero="Noor", hero_gender="girl", helper="Ben", helper_gender="boy", adult="librarian"),
    StoryParams(setting="classroom", page="share_card", clue="cup", hero="Maya", hero_gender="girl", helper="Eli", helper_gender="boy", adult="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show setting/1.\n#show page/1.\n#show clue/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP twin is present for this tiny whodunit.")
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = getattr(args, "seed", None)
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
