#!/usr/bin/env python3
"""
Storyworld: a coed race, a magical thingamajig, suspense, and kindness.

A small fable-shaped world:
- Children of different genders enter a race.
- A magical thingamajig can help, but it is finicky.
- Suspense grows when a racer must choose between winning and helping.
- Kindness changes the ending image and the emotional state of the world.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    rival: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Track:
    place: str = "the meadow track"
    surface: str = "grass"
    lap_count: int = 3
    affords: set[str] = field(default_factory=lambda: {"race"})
    track: object | None = None
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
class Trinket:
    id: str
    label: str
    phrase: str
    help_kind: str
    risk_kind: str
    charge_need: float = 1.0
    magic: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    name: str
    rival: str
    gender: str
    rival_gender: str
    track: str = "meadow"
    seed: Optional[int] = None
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
    def __init__(self, track: Track) -> None:
        self.track = track
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
        import copy
        clone = World(self.track)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _race_pressure(world: World) -> list[str]:
    out: list[str] = []
    racers = world.characters()
    if len(racers) < 2:
        return out
    leader = max(racers, key=lambda e: e.meters.get("speed", 0.0))
    for racer in racers:
        if racer.id == leader.id:
            continue
        if racer.memes.get("pressure", 0.0) >= THRESHOLD:
            continue
        sig = ("pressure", racer.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        racer.memes["pressure"] = racer.memes.get("pressure", 0.0) + 1
        out.append(f"{racer.id} felt the race tightening around {racer.pronoun('object')}.")
    return out


def _kindness_turn(world: World) -> list[str]:
    out: list[str] = []
    for racer in world.characters():
        if racer.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness_turn", racer.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        racer.memes["calm"] = racer.memes.get("calm", 0.0) + 1
        racer.memes["suspense"] = max(0.0, racer.memes.get("suspense", 0.0) - 1)
        out.append(f"Kindness steadied {racer.id}'s breathing.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_race_pressure, _kindness_turn):
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def race_help_needed(world: World, hero: Entity, trinket: Trinket) -> bool:
    return hero.meters.get("tired", 0.0) >= THRESHOLD and trinket.help_kind == "boost"


def use_thingamajig(world: World, hero: Entity, trinket: Trinket) -> bool:
    if trinket.risk_kind != "tumble":
        return False
    hero.meters["speed"] = hero.meters.get("speed", 0.0) + 1
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    return True


def tell_story(params: StoryParams) -> World:
    track = Track()
    world = World(track)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    rival = world.add(Entity(id=params.rival, kind="character", type=params.rival_gender))
    thing = world.add(Entity(
        id="thingamajig",
        kind="thing",
        type="thingamajig",
        label="thingamajig",
        phrase="a tiny brass thingamajig with a moon-blue button",
        owner=hero.id,
    ))
    magic = Trinket(
        id="thingamajig",
        label="thingamajig",
        phrase="a tiny brass thingamajig with a moon-blue button",
        help_kind="boost",
        risk_kind="tumble",
    )

    hero.meters["speed"] = 1
    rival.meters["speed"] = 1
    hero.meters["tired"] = 0
    rival.meters["tired"] = 0

    world.say(
        f"Long ago, in a little meadow, {hero.id} and {rival.id} came to race under the same sun."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {thing.label}, a {thing.phrase}, and both racers smiled at it."
    )
    world.say(
        "The old fox in the hedgerow called it a fair day, for the race was coed and the path was open to all."
    )

    world.para()
    world.say(
        f"At the first turn, {rival.id} leapt ahead, and the breeze made the little thingamajig glow."
    )
    hero.memes["suspense"] += 1
    hero.meters["tired"] += 1
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} knew {hero.pronoun('possessive')} chance to win was slipping fast."
    )

    world.para()
    world.say(
        f"Then {hero.id} saw {rival.id} stumble on a root."
    )
    world.say(
        f"The glowing thingamajig hummed softly, as if it were asking whether speed mattered more than kindness."
    )
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["suspense"] += 1

    if use_thingamajig(world, hero, magic):
        world.say(
            f"{hero.id} tapped the moon-blue button, but instead of racing ahead alone, {hero.pronoun()} slowed down."
        )
        world.say(
            f"{hero.id} offered {rival.pronoun('object')} a hand, and the thingamajig gave off a warm, gold spark."
        )
        rival.memes["kindness"] = rival.memes.get("kindness", 0.0) + 1
        rival.meters["tired"] += 1
        world.say(
            f"Together they ran the last stretch, and the race felt lighter for both of them."
        )

    hero.meters["speed"] += 1
    rival.meters["speed"] += 1
    hero.memes["suspense"] = max(0.0, hero.memes.get("suspense", 0.0) - 1)
    world.para()
    world.say(
        f"In the end, {hero.id} crossed the finish line with {rival.id} beside {hero.pronoun('object')}, and neither child was left alone."
    )
    world.say(
        f"The fox said that a race can teach many things, but the brightest lesson is that kindness makes the win last longer than a shout."
    )

    world.facts.update(
        hero=hero,
        rival=rival,
        thing=thing,
        magic=magic,
        place=track.place,
        race_type="coed",
        suspense=hero.memes.get("suspense", 0.0) > 0,
        kindness=hero.memes.get("kindness", 0.0) > 0,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fable about a coed race, a magical thingamajig, suspense, and kindness.',
        f"Tell a child-friendly story where {f['hero'].id} and {f['rival'].id} race at {f['place']} and a thingamajig changes the ending.",
        "Write a short fable in which a racer must choose between winning and helping another child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rival = _safe_fact(world, f, "rival")
    qa = [
        QAItem(
            question=f"Who took part in the coed race?",
            answer=f"{hero.id} and {rival.id} took part in the race together."
        ),
        QAItem(
            question=f"What magical object did {hero.id} carry?",
            answer=f"{hero.id} carried a thingamajig, a tiny brass object with a moon-blue button."
        ),
        QAItem(
            question=f"Why did the story feel suspenseful near the end?",
            answer=(
                f"It felt suspenseful because {hero.id} was close to winning, but then saw {rival.id} stumble "
                f"and had to decide whether to race on or help."
            ),
        ),
        QAItem(
            question=f"How did kindness change the ending?",
            answer=(
                f"Kindness made {hero.id} slow down and help {rival.id}, so they finished together instead of leaving one child behind."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thingamajig?",
            answer="A thingamajig is a made-up name for a small object when you know what it does more than what it is called."
        ),
        QAItem(
            question="What is a race?",
            answer="A race is a contest where people or animals try to finish a course before others do."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating someone with care, helping them, and not being mean when you could be."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show compatible/2.

compatible(Child, Thing) :- child(Child), thingamajig(Thing), carries(Child, Thing).
story_ok(Child, Rival) :- child(Child), child(Rival), child_gender(Child, G1), child_gender(Rival, G2), G1 != G2.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "hero"),
        asp.fact("child", "rival"),
        asp.fact("thingamajig", "thingamajig"),
        asp.fact("carries", "hero", "thingamajig"),
        asp.fact("child_gender", "hero", "girl"),
        asp.fact("child_gender", "rival", "boy"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    atoms = set(asp.atoms(model, "story_ok"))
    expected = {("hero", "rival")}
    if atoms == expected:
        print("OK: ASP story gate matches Python expectations.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a coed race and a thingamajig.")
    ap.add_argument("--name")
    ap.add_argument("--rival")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--rival-gender", choices=["girl", "boy"])
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    rival_gender = getattr(args, "rival_gender", None) or ("boy" if gender == "girl" else "girl")
    name_pool = ["Mina", "Ada", "Lena", "Tara"] if gender == "girl" else ["Owen", "Theo", "Milo", "Finn"]
    rival_pool = ["Eli", "Noah", "Arin", "Sage"] if rival_gender == "boy" else ["June", "Ivy", "Nora", "Wren"]
    name = getattr(args, "name", None) or rng.choice(name_pool)
    rival = getattr(args, "rival", None) or rng.choice([n for n in rival_pool if n != name])
    if name == rival:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, rival=rival, gender=gender, rival_gender=rival_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(name="Mina", rival="Owen", gender="girl", rival_gender="boy"),
    StoryParams(name="Theo", rival="Lena", gender="boy", rival_gender="girl"),
    StoryParams(name="Ada", rival="Finn", gender="girl", rival_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ok/2."))
        print(sorted(set(asp.atoms(model, "story_ok"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 30, 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
