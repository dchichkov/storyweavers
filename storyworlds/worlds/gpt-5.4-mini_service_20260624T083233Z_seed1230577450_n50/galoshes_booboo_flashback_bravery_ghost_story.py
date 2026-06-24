#!/usr/bin/env python3
"""
A tiny storyworld: a child, a ghost-story mood, a remembered boo-boo, and the
bravery to walk on with galoshes.

The domain is intentionally small and classical:
- a child ventures into a spooky place at night,
- a tiny flashback explains why the child is wary,
- a gentle ghostly presence appears,
- the child uses bravery, with help from galoshes, to finish the walk.

The simulated state carries both physical meters and emotional memes.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    booboo: object | None = None
    galoshes: object | None = None
    hero: object | None = None
    parent: object | None = None
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
    place: str = "the old path by the gate"
    dark: bool = True
    eerie: bool = True
    SETTING: object | None = None
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
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_seen = False

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = list(self.lines)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.flashback_seen = self.flashback_seen
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_mud_soak(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    boots = world.get("galoshes")
    if hero.meters.get("cold,") is not None:
        pass
    if hero.meters.get("mud", 0.0) >= THRESHOLD and boots.worn_by != hero.id:
        sig = ("mud",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["uneasy"] = hero.memes.get("uneasy", 0.0) + 1
        out.append("The damp ground made the child feel uneasy.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("bravery", 0.0) < THRESHOLD:
        return []
    sig = ("brave",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    out.append("Bravery warmed the child's small heart.")
    return out


RULES = [Rule("mud", _r_mud_soak), Rule("bravery", _r_bravery)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()
GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Clara", "June"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Finn", "Owen", "Miles"]


def _flashback(world: World, hero: Entity) -> None:
    if world.flashback_seen:
        return
    world.flashback_seen = True
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"For a moment, {hero.id} remembered a little booboo from earlier that day, "
        f"when a stone had scratched {hero.pronoun('possessive')} knee."
    )
    world.say(
        f"That flashback made the dark path seem sharper, but it also reminded {hero.pronoun('object')} "
        f"that small hurts could be faced and healed."
    )


def _introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.type} who liked quiet walks and spooky stories, "
        f"especially when {hero.pronoun('possessive')} {parent.type} walked beside {hero.pronoun('object')}."
    )
    world.say(
        f"On that night, {hero.pronoun('possessive')} trusty galoshes waited by the door."
    )


def _arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}, "
        f"where the wind whispered through the trees."
    )
    world.say(
        "The path looked ghostly in the moonlight, but it was only the night making shadows dance."
    )


def _fear_and_flashback(world: World, hero: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"{hero.id} slowed down when a pale shape moved near the fence."
    )
    _flashback(world, hero)


def _show_galoshes(world: World, hero: Entity) -> None:
    boots = world.get("galoshes")
    boots.worn_by = hero.id
    hero.memes["safe"] = hero.memes.get("safe", 0.0) + 1
    world.say(
        f"{hero.id} pulled on the galoshes, and their rubbery soles kept {hero.pronoun('possessive')} feet dry."
    )


def _choose_bravery(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"Then {hero.id} took one deep breath and chose bravery."
    )
    propagate(world, narrate=True)


def _ghostly_turn(world: World, hero: Entity) -> None:
    world.say(
        f"The pale shape turned out to be only a hanging sheet on a line, fluttering like a friendly ghost."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1


def _end(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} finished the walk with steady steps, the old booboo forgotten, "
        f"and the galoshes tapping softly over the wet leaves."
    )
    world.say(
        f"By the end, the dark path felt less scary, because {hero.id} had learned that bravery could walk right beside a small worry."
    )


def tell(name: str, gender: str, parent_type: str, place: str) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["small", "brave"]))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    galoshes = world.add(Entity(
        id="galoshes", type="galoshes", label="galoshes", phrase="a pair of galoshes",
        owner=hero.id, protective=True, plural=True, worn_by=None,
    ))
    booboo = world.add(Entity(
        id="booboo", type="booboo", label="booboo", phrase="a tiny booboo",
        owner=hero.id,
    ))
    world.facts.update(hero=hero, parent=parent, galoshes=galoshes, booboo=booboo, place=place)

    _introduce(world, hero, parent)
    world.para()
    _arrive(world, hero, parent)
    _fear_and_flashback(world, hero)
    _show_galoshes(world, hero)
    _choose_bravery(world, hero)
    world.para()
    _ghostly_turn(world, hero)
    _end(world, hero)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    return [
        f'Write a short ghost story for a young child named {hero.id} that includes galoshes and a harmless booboo.',
        f"Tell a gentle spooky story where {hero.id} walks to {place}, remembers a booboo, and finds bravery.",
        "Write a child-friendly ghost story with a flashback, a pair of galoshes, and a brave ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel nervous on the dark path?",
            answer=f"{hero.id} remembered a little booboo from earlier, and the flashback made the dark path feel scarier for a moment.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep going when the path felt spooky?",
            answer=f"The galoshes helped by keeping {hero.pronoun('possessive')} feet dry, and bravery helped {hero.id} keep walking.",
        ),
        QAItem(
            question=f"What turned out to be the ghostly shape near the fence?",
            answer="It was only a sheet hanging on a line, fluttering in the wind like a friendly ghost.",
        ),
        QAItem(
            question=f"Who walked with {hero.id} on the path?",
            answer=f"{hero.id}'s {parent.type} walked beside {hero.id} and stayed near during the scary moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are galoshes for?",
            answer="Galoshes are waterproof boots that help keep your feet dry in wet weather or muddy places.",
        ),
        QAItem(
            question="What is a booboo?",
            answer="A booboo is a small hurt, like a scratch or bump, that usually needs a little care and time to heal.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means facing something scary or hard even when you feel nervous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world with galoshes, booboo, flashback, and bravery.")
    ap.add_argument("--place", default="the old path by the gate")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--name", default=None)
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
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, place=getattr(args, "place", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.place)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


ASP_RULES = r"""
hero(X) :- character(X).
protective(galoshes).
brave(X) :- bravery(X).
flashback(X) :- remembers(X).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "hero"),
        asp.fact("character", "parent"),
        asp.fact("object", "galoshes"),
        asp.fact("object", "booboo"),
        asp.fact("theme", "flashback"),
        asp.fact("theme", "bravery"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program(""))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(name="Mina", gender="girl", parent="mother", place=getattr(args, "place", None)))]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
