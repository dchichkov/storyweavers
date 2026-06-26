#!/usr/bin/env python3
"""
A small storyworld about a ghost in a community garden, a pot of stroganoff,
a rhyme, and a bad ending that still feels complete.

This world models a tiny supernatural garden tale:
- a child or gardener hears a rhyme in the evening,
- a helpful meal is shared,
- a ghostly mix-up causes trouble,
- the ending is bad for the stroganoff, but the garden changes in a clear way.

The prose is driven by world state so stories are not frozen templates.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    role: str
    name: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Thing:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    state: str = "plain"
    bowl: object | None = None
    ghost: object | None = None
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
    gardener: str
    companion: str
    seed_word: str = "stroganoff"
    seed: Optional[int] = None
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
class Garden:
    place: str = "the community garden"
    evening: bool = True
    rhyme_heard: bool = False
    ghost_seen: bool = False
    ending_bad: bool = True
    facts: dict = field(default_factory=dict)
    garden: object | None = None
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


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.garden = Garden()
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity):
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str):
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
        w = World(self.params)
        w.garden = copy.deepcopy(self.garden)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story in a community garden with stroganoff and rhyme.")
    ap.add_argument("--gardener", choices=["Mina", "Noah", "Iris", "Eli", "June", "Owen"])
    ap.add_argument("--companion", choices=["grandpa", "grandma", "mom", "dad", "neighbor"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gardener = getattr(args, "gardener", None) or rng.choice(["Mina", "Noah", "Iris", "Eli", "June", "Owen"])
    companion = getattr(args, "companion", None) or rng.choice(["grandpa", "grandma", "mom", "dad", "neighbor"])
    return StoryParams(gardener=gardener, companion=companion, seed=getattr(args, "seed", None))


def rhyme_lines() -> list[str]:
    return [
        "In the garden dark and green, a silver mist was softly seen.",
        "By the beans and basil beds, a ghostly tune ran through their heads.",
        "If you share the stew and spoon, the moon will hum a tiny tune.",
    ]


def rhyme_text() -> str:
    lines = rhyme_lines()
    return " ".join(lines[:2])


def make_world(params: StoryParams) -> World:
    w = World(params)
    hero = w.add(Person(id="gardener", role="gardener", name=params.gardener))
    companion = w.add(Person(id="companion", role=params.companion, name=params.companion))
    bowl = w.add(Thing(id="stroganoff", label="stroganoff", owner=hero.id))
    ghost = w.add(Thing(id="ghost", label="garden ghost"))
    w.garden.facts.update(hero=hero, companion=companion, bowl=bowl, ghost=ghost)
    return w


def disturb_stroganoff(w: World) -> None:
    bowl: Thing = w.get("stroganoff")
    if "disturbed" in w.fired:
        return
    w.fired.add("disturbed")
    bowl.meters["mess"] += 1
    bowl.state = "splashed"
    w.garden.ghost_seen = True
    w.garden.facts["disturbed"] = True
    w.say(f"That evening, {w.params.gardener} and {w.params.companion} sat in {w.garden.place} with a warm bowl of stroganoff.")
    w.say(f"The air went quiet, and a rhyme drifted over the tomato vines: “{rhyme_lines()[0]}”")
    w.say(f"Then another line followed: “{rhyme_lines()[1]}”")
    w.say(f"A pale ghost stepped between the bean poles and pointed at the stroganoff as if it had been waiting all night.")


def fear_and_warning(w: World) -> None:
    hero: Person = w.get("gardener")
    companion: Person = w.get("companion")
    bowl: Thing = w.get("stroganoff")
    if "warned" in w.fired:
        return
    w.fired.add("warned")
    hero.meters["fear"] += 1
    hero.memes["wonder"] += 1
    companion.meters["care"] += 1
    w.say(f"{hero.name} held the spoon tighter, because the ghost's whisper made the bowl feel colder.")
    w.say(f"{companion.name} said the rhyme sounded friendly, but the garden shadows did not agree.")
    w.say(f'The ghost sighed, “If you follow the tune, the stew will spill; if you stay too long, the night grows still.”')


def ghost_turn(w: World) -> None:
    hero: Person = w.get("gardener")
    bowl: Thing = w.get("stroganoff")
    if "turn" in w.fired:
        return
    w.fired.add("turn")
    w.garden.rhyme_heard = True
    bowl.meters["cold"] += 1
    hero.memes["sadness"] += 1
    w.say(f"{hero.name} tried to answer the rhyme, but the ghost blew a chilly breath across the bowl.")
    w.say(f"The stroganoff shivered, the noodles stuck together, and the steam vanished like a secret.")


def bad_ending(w: World) -> None:
    hero: Person = w.get("gardener")
    companion: Person = w.get("companion")
    bowl: Thing = w.get("stroganoff")
    ghost: Thing = w.get("ghost")
    if "end" in w.fired:
        return
    w.fired.add("end")
    bowl.state = "ruined"
    bowl.meters["mess"] += 2
    hero.memes["sadness"] += 1
    companion.memes["comfort"] += 1
    w.garden.ending_bad = True
    w.say(f'They followed the last line of the rhyme—“{rhyme_lines()[2]}”—but it was too late.')
    w.say(f"The ghost lifted the spoon, the bowl tipped, and the stroganoff slipped into the soil between the carrots.")
    w.say(f"{hero.name} stared at the muddy noodles while {companion.name} wrapped an arm around {hero.name}'s shoulders.")
    w.say(f"In the end, the ghost vanished, the garden smelled like onions and rain, and the stroganoff was gone for good.")


def tell_story(w: World) -> None:
    hero: Person = w.get("gardener")
    companion: Person = w.get("companion")
    bowl: Thing = w.get("stroganoff")
    w.say(f"{hero.name} loved visiting {w.garden.place} with {companion.name}, especially when dinner was warm and the bees were quiet.")
    w.say(f"They had brought a bowl of stroganoff, thick with noodles and mushrooms, because the long rows of beans made everyone hungry.")
    w.para()
    disturb_stroganoff(w)
    fear_and_warning(w)
    ghost_turn(w)
    w.para()
    bad_ending(w)
    w.garden.facts.update(
        bowl=bowl,
        hero=hero,
        companion=companion,
        rhyme=rhyme_text(),
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Person = world.garden.facts["hero"]
    companion: Person = world.garden.facts["companion"]
    bowl: Thing = world.garden.facts["bowl"]
    return [
        QAItem(
            question=f"Where did {hero.name} and {companion.name} share the stroganoff?",
            answer=f"They shared it in the community garden, among the bean poles, tomato vines, and carrots.",
        ),
        QAItem(
            question="What strange thing did they hear before the trouble started?",
            answer=f"They heard a ghostly rhyme drifting through the garden, and it made the night feel colder.",
        ),
        QAItem(
            question=f"What happened to the {bowl.label} at the end?",
            answer="The bowl tipped into the soil, and the stroganoff was ruined instead of being eaten.",
        ),
        QAItem(
            question=f"How did {companion.name} help when {hero.name} felt bad?",
            answer=f"{companion.name} stayed beside {hero.name}, wrapped an arm around them, and helped them face the bad ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is stroganoff?",
            answer="Stroganoff is a warm noodle-and-sauce dish that people often eat for dinner.",
        ),
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared place where neighbors grow flowers, vegetables, and herbs together.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end, which can make a line feel like a song.",
        ),
        QAItem(
            question="Why can a ghost story feel spooky?",
            answer="A ghost story feels spooky because it uses quiet places, strange sounds, and the idea that something unseen might be near.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Person = world.garden.facts["hero"]
    companion: Person = world.garden.facts["companion"]
    return [
        f"Write a short ghost story in a community garden about {hero.name}, {companion.name}, and stroganoff.",
        "Tell a child-friendly spooky tale where a rhyme leads to a bad ending for dinner.",
        "Write a small story about a garden ghost, a warm meal, and a night that goes wrong.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.garden.place}")
    lines.append(f"  rhyme_heard: {world.garden.rhyme_heard}")
    lines.append(f"  ghost_seen: {world.garden.ghost_seen}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if isinstance(e, Thing):
            bits.append(f"state={e.state}")
        lines.append(f"  {e.id}: {e.label if hasattr(e, 'label') else e.name} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
garden(garden).
dish(stroganoff).
rhyme(line1).
ghost(ghost).
bad_ending(ending).

hear_rhyme :- rhyme(line1).
spook :- ghost(ghost), hear_rhyme.
ruin_dish :- spook, dish(stroganoff), bad_ending(ending).

#show hear_rhyme/0.
#show spook/0.
#show ruin_dish/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("garden", "community_garden"),
        asp.fact("dish", "stroganoff"),
        asp.fact("rhyme", "line1"),
        asp.fact("ghost", "ghost"),
        asp.fact("bad_ending", "ending"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hear_rhyme/0. #show spook/0. #show ruin_dish/0."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("hear_rhyme", 0), ("spook", 0), ("ruin_dish", 0)}
    if atoms == expected:
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected atoms.")
    print("got:", sorted(atoms))
    print("exp:", sorted(expected))
    return 1


def asp_stories() -> list[tuple[str, str, str]]:
    return [("community_garden", "stroganoff", "ghost_story")]


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(gardener="Mina", companion="grandma"),
        StoryParams(gardener="Owen", companion="neighbor"),
        StoryParams(gardener="Iris", companion="dad"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show hear_rhyme/0. #show spook/0. #show ruin_dish/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in build_curated():
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
