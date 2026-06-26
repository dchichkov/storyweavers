#!/usr/bin/env python3
"""
storyworlds/worlds/ottoman_badminton_tidbit_magic_dialogue_mystery.py
======================================================================

A small mystery storyworld about an ottoman, a badminton game, and a curious
tidbit that helps solve the puzzle with a touch of magic and dialogue.

The seed tale behind this world:
---
Nia found her badmiton shuttle missing after practice in the living room.
Her brother said it must have rolled away, but Nia noticed a tiny glittering
tidbit on the ottoman. When she asked about it, the tidbit glowed and a whisper
pointed under the cushion. There, with a little magic and a lot of talking,
they found the shuttlecock and laughed about the mystery.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    ottoman: object | None = None
    shuttle: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
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
class Setting:
    place: str = "the living room"
    affords: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    hint: str
    revealed_by_magic: bool = False
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
    place: str
    hero_name: str
    hero_type: str
    sibling_name: str
    sibling_type: str
    clue: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.magic_awake: bool = False
        self.whisper: str = ""

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.magic_awake = self.magic_awake
        clone.whisper = self.whisper
        return clone


def _r_magic_whisper(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if not clue:
        return out
    if world.magic_awake and clue.meters.get("glow", 0.0) >= THRESHOLD:
        sig = ("whisper", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.whisper = clue.hint
        out.append("A soft whisper pointed the way.")
    return out


def _r_find_item(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    shuttle = world.entities.get("shuttle")
    if not clue or not shuttle:
        return out
    if clue.meters.get("glow", 0.0) < THRESHOLD:
        return out
    if shuttle.meters.get("hidden", 0.0) < THRESHOLD:
        return out
    sig = ("found", shuttle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shuttle.meters["hidden"] = 0.0
    shuttle.meters["found"] = 1.0
    out.append("Under the ottoman cushion, the missing shuttlecock was finally found.")
    return out


CAUSAL_RULES = [
    _r_magic_whisper,
    _r_find_item,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story_world(setting: Setting, clue_cfg: Clue, hero_name: str, hero_type: str,
                      sibling_name: str, sibling_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name,
                            traits=["curious", "careful"]))
    sibling = world.add(Entity(id="sibling", kind="character", type=sibling_type, label=sibling_name,
                              traits=["busy", "sure"]))
    ottoman = world.add(Entity(id="ottoman", type="furniture", label="ottoman",
                              phrase="a soft ottoman with a stitched cover"))
    shuttle = world.add(Entity(id="shuttle", type="object", label="shuttlecock",
                              phrase="the missing badminton shuttlecock"))
    clue = world.add(Entity(id="clue", type="clue", label=clue_cfg.label,
                           phrase=clue_cfg.phrase))
    shuttle.meters["hidden"] = 1.0
    clue.meters["glow"] = 0.0

    world.say(f"{hero.label} loved badminton, but that afternoon the shuttlecock had vanished.")
    world.say(f"{hero.label} looked under the table, behind the chair, and even near the door.")
    world.say(f'"Did you see it?" {hero.label} asked.')
    world.say(f'"No," {sibling.label} said. "It must have rolled away."')
    world.para()

    world.say(f"{hero.label} turned to the ottoman and noticed a tiny tidbit resting on top of it.")
    world.say(f'"That is strange," {hero.label} whispered. "Why would a tidbit sparkle there?"')
    world.say(f"The room felt quiet, as if it wanted to keep a secret.")
    world.facts["hero"] = hero
    world.facts["sibling"] = sibling
    world.facts["ottoman"] = ottoman
    world.facts["shuttle"] = shuttle
    world.facts["clue"] = clue
    world.facts["clue_cfg"] = clue_cfg
    world.facts["setting"] = setting
    world.facts["magic_awake"] = False

    world.para()
    world.say(f'When {hero.label} touched the tidbit, it gave a warm little glow.')
    world.magic_awake = True
    clue.meters["glow"] += 1.0
    propagate(world, narrate=True)

    if world.whisper:
        world.say(f'"Listen," {hero.label} said. "{world.whisper}"')
    if shuttle.meters.get("found", 0.0) >= THRESHOLD:
        world.say(f"{hero.label} lifted the cushion and gasped. There was the shuttlecock after all.")
        world.say(f'"You were right to look closer," {sibling.label} said with a grin.')
        world.say(f"{hero.label} laughed and tucked the tidbit back on the ottoman, like a clue in a treasure hunt.")

    world.facts["magic_awake"] = world.magic_awake
    return world


SETTINGS = {
    "living_room": Setting(place="the living room", affords={"mystery"}),
    "den": Setting(place="the den", affords={"mystery"}),
    "family_room": Setting(place="the family room", affords={"mystery"}),
}

CLUES = {
    "tidbit": Clue(
        id="tidbit",
        label="tidbit",
        phrase="a tiny glittering tidbit",
        hint="Look under the ottoman cushion.",
        revealed_by_magic=True,
    ),
    "trinket": Clue(
        id="trinket",
        label="trinket",
        phrase="a bright little trinket",
        hint="The clue is hiding beneath something soft.",
        revealed_by_magic=True,
    ),
}

HERO_NAMES = ["Nia", "Maya", "Lena", "Rosa", "Ivy", "Ari", "Tess", "Milo", "Noah", "Finn"]
SIBLING_NAMES = ["Owen", "Pia", "Jules", "Eli", "June", "Ada", "Theo", "Bea"]
TRAITS = ["curious", "careful", "brave", "thoughtful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with magic and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    sibling_gender = getattr(args, "sibling_gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES if gender == "girl" else HERO_NAMES)
    sibling_name = getattr(args, "sibling_name", None) or rng.choice(SIBLING_NAMES)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=gender,
        sibling_name=sibling_name,
        sibling_type=sibling_gender,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CLUES, params.clue),
        params.hero_name,
        params.hero_type,
        params.sibling_name,
        params.sibling_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    clue = _safe_fact(world, f, "clue_cfg")
    return [
        f'Write a short mystery story for a young child about a {hero.type} named {hero.label}, an ottoman, and a {clue.label}.',
        f'Create a gentle story with dialogue where {hero.label} and {sibling.label} use magic to solve a missing badminton mystery.',
        f'Write a small story in a family room where a sparkling {clue.label} helps find a missing badminton shuttlecock.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    clue = _safe_fact(world, f, "clue_cfg")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What was missing in {place}?",
            answer="The badminton shuttlecock was missing.",
        ),
        QAItem(
            question=f"What did {hero.label} notice on the ottoman?",
            answer=f"{hero.label} noticed {clue.phrase} on the ottoman.",
        ),
        QAItem(
            question=f"How did the tidbit help solve the mystery?",
            answer="It glowed, gave a whisper, and pointed to the shuttlecock under the cushion.",
        ),
        QAItem(
            question=f"What did {sibling.label} say about the missing shuttlecock?",
            answer=f'{sibling.label} said, "It must have rolled away."',
        ),
        QAItem(
            question=f"What did {hero.label} do after the clue glowed?",
            answer=f"{hero.label} lifted the cushion and found the shuttlecock.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ottoman?",
            answer="An ottoman is a low soft seat or footrest, and people can also look beside or under it.",
        ),
        QAItem(
            question="What is badminton?",
            answer="Badminton is a game where players hit a shuttlecock back and forth with rackets.",
        ),
        QAItem(
            question="What is a tidbit?",
            answer="A tidbit is a very small piece or bit of something.",
        ),
        QAItem(
            question="What does magic do in a mystery story?",
            answer="Magic can reveal hidden clues, surprise the characters, and help solve the puzzle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  magic_awake={world.magic_awake}")
    lines.append(f"  whisper={world.whisper!r}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_glows(C) :- clue(C).
mystery_solved :- clue_glows(clue), shuttle_hidden(shuttle).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("shuttle_hidden", "shuttle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/0."))
    atoms = asp.atoms(model, "mystery_solved")
    if atoms:
        print("OK: ASP twin can derive a solved mystery.")
        return 0
    print("MISMATCH: ASP twin did not derive the solved mystery.")
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue_glows/1."))
    return sorted(set(asp.atoms(model, "clue_glows")))


CURATED = [
    StoryParams(place="living_room", hero_name="Nia", hero_type="girl", sibling_name="Owen", sibling_type="boy", clue="tidbit"),
    StoryParams(place="den", hero_name="Maya", hero_type="girl", sibling_name="Pia", sibling_type="girl", clue="trinket"),
    StoryParams(place="family_room", hero_name="Milo", hero_type="boy", sibling_name="Ada", sibling_type="girl", clue="tidbit"),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show clue_glows/1.\n#show mystery_solved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid())} ASP clue facts:")
        for atom in asp_valid():
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} in {p.place} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
