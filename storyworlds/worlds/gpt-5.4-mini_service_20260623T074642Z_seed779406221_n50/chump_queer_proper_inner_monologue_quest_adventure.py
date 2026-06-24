#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/chump_queer_proper_inner_monologue_quest_adventure.py
==============================================================================================================================

A small Adventure-style storyworld built from the seed words:
- chump
- queer
- proper

Premise:
A young runner wants to begin a quest the "proper" way, but an inner monologue
keeps calling him a chump until he notices the quest is actually to help a queer
little market lantern find its missing cap. The turn is learning that proper can
mean careful and kind, not stiff. The resolution is choosing a sensible tool and
finishing the quest with a bright ending image.

This file is standalone and uses only the stdlib plus the shared storyworld
result containers. ASP support is inline via ASP_RULES and lazily imported.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cap: object | None = None
    guide: object | None = None
    hero: object | None = None
    lantern: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
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
    outdoors: bool = True
    landmarks: list[str] = field(default_factory=list)
    affordances: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    goal: str
    key_word: str
    trouble: str
    turn: str
    ending: str
    requires: set[str] = field(default_factory=set)
    helper: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
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


SETTINGS = {
    "market": Setting(
        place="the market",
        outdoors=True,
        landmarks=["stall", "fountain", "alley"],
        affordances={"search", "cross", "ask"},
    ),
    "harbor": Setting(
        place="the harbor",
        outdoors=True,
        landmarks=["dock", "rope ladder", "lantern post"],
        affordances={"search", "cross", "ask"},
    ),
    "cove": Setting(
        place="the cove",
        outdoors=True,
        landmarks=["rock", "boat", "cave mouth"],
        affordances={"search", "cross", "ask"},
    ),
}

QUESTS = {
    "lantern_cap": Quest(
        id="lantern_cap",
        goal="find the lost cap for the queer little lantern",
        key_word="lantern",
        trouble="the lantern could not shine properly without its cap",
        turn="he found the cap where the wind had tucked it under a crate",
        ending="the lantern shone straight and warm all the way home",
        requires={"search", "ask"},
        helper="lantern keeper",
    ),
    "river_key": Quest(
        id="river_key",
        goal="carry a small key across the bridge without dropping it",
        key_word="key",
        trouble="the bridge wind kept rattling the key in his pocket",
        turn="he tied the key to a string so it stayed put",
        ending="the key reached the other side safe and bright",
        requires={"cross", "search"},
        helper="bridge guide",
    ),
    "pouch_map": Quest(
        id="pouch_map",
        goal="deliver a folded map to the hill hut",
        key_word="map",
        trouble="the map kept trying to open in the breeze",
        turn="he slipped it into a pouch and walked carefully",
        ending="the map arrived flat and neat at the hut door",
        requires={"cross", "ask"},
        helper="hill courier",
    ),
}

HERO_NAMES = ["Nico", "Jules", "Milo", "Ravi", "Theo", "Pip"]
HERO_TYPES = ["boy", "girl"]
QUEST_ORDER = ["lantern_cap", "river_key", "pouch_map"]


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_kind(Q).
hero(H) :- hero_kind(H).
valid(P, Q) :- setting(P), quest_kind(Q), can_do(P, Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for l in s.landmarks:
            lines.append(asp.fact("landmark", pid, l))
        for a in sorted(s.affordances):
            lines.append(asp.fact("can_do", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_kind", qid))
        for r in sorted(q.requires):
            lines.append(asp.fact("requires", qid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


class NARR:
    @staticmethod
    def intro(hero: Entity, setting: Setting, quest: Quest) -> str:
        return (
            f"{hero.id} was a proper little runner who loved maps, honest paths, "
            f"and the feeling of beginning a quest the right way."
        )

    @staticmethod
    def monologue(hero: Entity, quest: Quest) -> str:
        return (
            f'“Come on, chump,” his own inner monologue muttered, though {hero.id} '
            f'kept looking at the goal anyway: {quest.goal}.'
        )

    @staticmethod
    def arrive(hero: Entity, setting: Setting, quest: Quest) -> str:
        return (
            f"He went to {setting.place}, where a wind-colored path bent between "
            f"{setting.landmarks[0]} and {setting.landmarks[-1]}."
        )

    @staticmethod
    def trouble(hero: Entity, quest: Quest) -> str:
        return (
            f"At first, {quest.trouble}, and that made {hero.id} feel small and "
            f"a little foolish."
        )

    @staticmethod
    def turn(hero: Entity, quest: Quest) -> str:
        return (
            f"Then he remembered that proper did not mean stiff; proper meant "
            f"careful, and careful meant asking for help."
        )

    @staticmethod
    def resolve(hero: Entity, quest: Quest) -> str:
        return (
            f"So he chose a sensible way, and {quest.turn}. Soon {quest.ending}."
        )


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in SETTINGS:
        for qid, q in QUESTS.items():
            if q.requires <= _safe_lookup(SETTINGS, p).affordances:
                combos.append((p, qid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with inner monologue and quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    return StoryParams(place=place, quest=quest, hero_name=name, hero_type=gender)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    lantern = world.add(Entity(id="lantern", label="queer little lantern", type="thing", owner=hero.id))
    cap = world.add(Entity(id="cap", label="brass cap", type="thing", owner=lantern.id))
    guide = world.add(Entity(id="guide", kind="character", type="person", label=quest.helper))

    hero.memes["doubt"] += 1
    world.say(NARR.intro(hero, setting, quest))
    world.say(NARR.monologue(hero, quest))
    world.para()
    world.say(NARR.arrive(hero, setting, quest))
    world.say(NARR.trouble(hero, quest))
    world.say(f"The {quest.helper} pointed toward the clue and stayed patient.")
    world.para()
    hero.memes["resolve"] += 1
    world.say(NARR.turn(hero, quest))
    world.say(NARR.resolve(hero, quest))
    hero.memes["joy"] += 1
    lantern.meters["lit"] += 1
    cap.carried_by = hero.id
    world.facts.update(hero=hero, lantern=lantern, cap=cap, guide=guide, quest=quest, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Adventure story for a child who hears an inner monologue and sets out on a quest in {f["setting"].place}.',
        f"Tell a gentle quest story where {f['hero'].id} is called a chump in his own head but chooses to act properly anyway.",
        f'Write a simple story that includes the words "proper", "queer", and "chump" and ends with a clear quest resolved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest, setting = f["hero"], f["quest"], f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {setting.place}?",
            answer=f"{hero.id} was trying to {quest.goal}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel unsure at first?",
            answer=f"He heard his own inner monologue call him a chump, and the quest looked hard before he understood it.",
        ),
        QAItem(
            question=f"How did he choose to be proper?",
            answer="He chose to be careful, ask for help, and follow the clue instead of rushing.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The quest was finished, and {quest.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of your own thoughts in your head.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, often to find something, deliver something, or solve a problem.",
        ),
        QAItem(
            question="What does proper mean here?",
            answer="Proper means careful, correct, and respectful rather than careless.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="market", quest="lantern_cap", hero_name="Nico", hero_type="boy"),
    StoryParams(place="harbor", quest="river_key", hero_name="Jules", hero_type="girl"),
    StoryParams(place="cove", quest="pouch_map", hero_name="Milo", hero_type="boy"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
