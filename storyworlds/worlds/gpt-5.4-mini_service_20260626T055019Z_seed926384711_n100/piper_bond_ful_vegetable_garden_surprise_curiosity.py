#!/usr/bin/env python3
"""
storyworlds/worlds/piper_bond_ful_vegetable_garden_surprise_curiosity.py
========================================================================

A small animal-story world set in a vegetable garden.

Premise:
- Piper is a curious rabbit.
- Bond is a steady badger friend.
- Ful is a tiny field mouse friend.
- A vegetable garden holds a hidden surprise.
- Curiosity opens the path, Surprise reveals the finding, and Twist changes
  what everyone thinks the find means.

The story is built from a simulated world model with physical meters and
emotional memes. The garden can be searched, a hidden patch can be uncovered,
and an ending bond can form when the characters choose to share the discovery.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    carries: list[str] = field(default_factory=list)

    bond: object | None = None
    ful: object | None = None
    hidden: object | None = None
    piper: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "mouse", "badger", "cat", "fox", "hedgehog", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the vegetable garden"
    afford_search: bool = True
    afford_hide: bool = True
    SETTING: object | None = None
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
class Find:
    id: str
    label: str
    phrase: str
    kind: str
    reveal: str
    twist: str
    value: str
    tags: set[str] = field(default_factory=set)
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
    seed_word_1: str = "piper"
    seed_word_2: str = "bond"
    seed_word_3: str = "ful"
    find: str = "carrot_cache"
    name_piper: str = "Piper"
    name_bond: str = "Bond"
    name_ful: str = "Ful"
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
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


def _fmt_join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


FINDINGS = {
    "carrot_cache": Find(
        id="carrot_cache",
        label="carrot cache",
        phrase="a tucked-away pile of bright carrots",
        kind="food",
        reveal="a careful nest of carrots under a clump of leaves",
        twist="it belonged to the garden keeper for the winter birds",
        value="sharing",
        tags={"surprise", "curiosity", "twist", "carrot"},
    ),
    "bean_basket": Find(
        id="bean_basket",
        label="bean basket",
        phrase="a little basket of green beans",
        kind="food",
        reveal="a little basket hiding under a bean vine",
        twist="it was a gift meant for a sleepy hedgehog family",
        value="sharing",
        tags={"surprise", "curiosity", "twist", "bean"},
    ),
    "pumpkin_note": Find(
        id="pumpkin_note",
        label="pumpkin note",
        phrase="a round pumpkin with a folded note taped to it",
        kind="message",
        reveal="a pumpkin that had a note hiding under one leaf",
        twist="the note asked for help moving the pumpkin before sunset",
        value="helping",
        tags={"surprise", "curiosity", "twist", "pumpkin"},
    ),
}

SETTING = Setting()

PIPER_KINDS = ["rabbit", "hare"]
BOND_KINDS = ["badger", "otter"]
FUL_KINDS = ["mouse", "field mouse", "vole"]
MOODS = ["curious", "careful", "bright", "gentle", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world in a vegetable garden.")
    ap.add_argument("--find", choices=sorted(FINDINGS))
    ap.add_argument("--name-piper")
    ap.add_argument("--name-bond")
    ap.add_argument("--name-ful")
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
    find = getattr(args, "find", None) or rng.choice(sorted(FINDINGS))
    return StoryParams(
        seed_word_1="piper",
        seed_word_2="bond",
        seed_word_3="ful",
        find=find,
        name_piper=getattr(args, "name_piper", None) or "Piper",
        name_bond=getattr(args, "name_bond", None) or "Bond",
        name_ful=getattr(args, "name_ful", None) or "Ful",
    )


def _build_world(params: StoryParams) -> World:
    if params.find not in FINDINGS:
        pass
    world = World(SETTING)

    piper = world.add(Entity(
        id="piper", kind="character", type="rabbit", label=params.name_piper,
        traits=["little", "curious", "quick"], memes={"curiosity": 1.0, "joy": 0.2},
    ))
    bond = world.add(Entity(
        id="bond", kind="character", type="badger", label=params.name_bond,
        traits=["steady", "kind"], memes={"trust": 0.8, "calm": 0.8},
    ))
    ful = world.add(Entity(
        id="ful", kind="character", type="mouse", label=params.name_ful,
        traits=["small", "bright"], memes={"curiosity": 0.6, "worry": 0.1},
    ))
    find = _safe_lookup(FINDINGS, params.find)
    hidden = world.add(Entity(
        id="hidden_find", kind="thing", type=find.kind, label=find.label,
        phrase=find.phrase, meters={"hidden": 1.0}, memes={"mystery": 1.0},
    ))

    world.facts.update(piper=piper, bond=bond, ful=ful, hidden=hidden, find=find)
    return world


def _narrate_setup(world: World) -> None:
    piper = world.get("piper")
    bond = world.get("bond")
    ful = world.get("ful")
    world.say(
        f"{piper.label}, a little rabbit, lived beside {world.setting.place}. "
        f"{piper.pronoun('subject').capitalize()} loved poking through the green rows and sniffing every leaf."
    )
    world.say(
        f"{bond.label}, a steady badger, stayed close by, and {ful.label}, a tiny mouse, followed with bright eyes. "
        f"The three friends had a soft bond because they always listened to one another."
    )
    world.say(
        f"On a warm day, {piper.label} noticed a hummock of soil that looked a little too smooth."
    )


def _search(world: World, find: Find) -> None:
    piper = world.get("piper")
    bond = world.get("bond")
    ful = world.get("ful")
    piper.memes["curiosity"] += 1.0
    piper.meters["search"] = piper.meters.get("search", 0.0) + 1.0
    world.say(
        f"{piper.label} leaned closer, because curiosity pulled {piper.pronoun('object')} toward the patch."
    )
    world.say(
        f"{ful.label} waddled over and whispered, \"What is under there?\" while {bond.label} lowered {bond.pronoun('possessive')} nose."
    )
    world.say(
        f"Together they nudged aside the leaves."
    )
    hidden = world.get("hidden_find")
    hidden.meters["hidden"] = 0.0
    hidden.meters["revealed"] = 1.0
    hidden.memes["mystery"] = 0.0
    world.facts["revealed"] = True
    world.say(f"Surprise! They found {find.reveal}.")


def _twist(world: World, find: Find) -> None:
    piper = world.get("piper")
    bond = world.get("bond")
    ful = world.get("ful")
    find_obj = world.get("hidden_find")
    world.say(
        f"At first, {piper.label} thought the find was a prize just for nibbling."
    )
    world.say(
        f"Then the twist came: {find.twist}."
    )
    if find.value == "sharing":
        bond.memes["trust"] += 1.0
        ful.memes["joy"] += 1.0
        piper.memes["surprise"] = piper.memes.get("surprise", 0.0) + 1.0
        world.say(
            f"{bond.label} said the best surprise was not keeping it, but sharing it with hungry friends."
        )
        world.say(
            f"{piper.label} nodded, and the little rabbit's curiosity turned into a warm, careful plan."
        )
        world.facts["resolution"] = "shared"
    else:
        bond.memes["trust"] += 0.5
        piper.memes["surprise"] = piper.memes.get("surprise", 0.0) + 1.0
        world.say(
            f"{ful.label} noticed that helping would make the garden kinder for everyone."
        )
        world.facts["resolution"] = "helped"
    find_obj.meters["special"] = 1.0
    world.say(
        f"In the end, the friends carried the find together, and the garden felt less secret and more friendly."
    )
    world.say(
        f"{piper.label} had started with curiosity, met surprise, and learned that a good twist can grow a stronger bond."
    )


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    find = _safe_lookup(FINDINGS, params.find)
    _narrate_setup(world)
    world.para()
    _search(world, find)
    world.para()
    _twist(world, find)
    return world


ASP_RULES = r"""
% A hidden find becomes revealed when curiosity is high enough.
revealed(C) :- curious(C), hidden(find), search(C).

% The twist resolves when the find is revealed and the friends share/help.
resolved(shared) :- revealed(find), sharing(find).

% A bond is strengthened when a surprised friend responds kindly.
bond_stronger(piper, bond) :- surprised(piper), kind(bond).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("character", "piper"))
    lines.append(asp.fact("character", "bond"))
    lines.append(asp.fact("character", "ful"))
    lines.append(asp.fact("curious", "piper"))
    lines.append(asp.fact("kind", "bond"))
    lines.append(asp.fact("helpful", "bond"))
    lines.append(asp.fact("search", "piper"))
    lines.append(asp.fact("hidden", "find"))
    for fid, find in FINDINGS.items():
        lines.append(asp.fact("find", fid))
        for tag in sorted(find.tags):
            lines.append(asp.fact(tag, fid))
        if find.value == "sharing":
            lines.append(asp.fact("sharing", fid))
        if find.value == "helping":
            lines.append(asp.fact("helping", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1. #show bond_stronger/2."))
    atoms = set()
    for sym in model:
        if sym.name in {"resolved", "bond_stronger"}:
            atoms.add((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)))
    if ("resolved", ("shared",)) in atoms or ("bond_stronger", ("piper", "bond")) in atoms:
        print("OK: ASP facts/rules produce the expected story signals.")
        return 0
    print("ASP verification failed.")
    return 1


def generation_prompts(world: World) -> list[str]:
    return [
        'Write an Animal Story set in a vegetable garden about piper, bond, and ful, where curiosity leads to a surprise and then a twist.',
        f"Tell a short story about {world.get('piper').label}, {world.get('bond').label}, and {world.get('ful').label} finding something hidden in the vegetable garden.",
        "Write a child-facing story where a curious animal discovers a garden secret, and the ending changes what the friends think it means.",
    ]


def story_qa(world: World) -> list[QAItem]:
    piper = world.get("piper")
    bond = world.get("bond")
    ful = world.get("ful")
    find = _safe_fact(world, world.facts, "find")
    return [
        QAItem(
            question="Who was the curious rabbit in the vegetable garden?",
            answer=f"{piper.label} was the curious rabbit, and {piper.label} was the one who noticed the smooth patch first.",
        ),
        QAItem(
            question="What did the friends discover under the leaves?",
            answer=f"They discovered {find.reveal}, which was a surprise hidden in the vegetable garden.",
        ),
        QAItem(
            question="How did Bond and Ful help with the find?",
            answer=f"{bond.label} stayed steady while {ful.label} asked questions, and that helped the friends uncover the hidden thing together.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The twist changed the meaning of the find, and the friends ended by sharing or helping instead of keeping the secret alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow vegetables, like carrots, beans, and pumpkins, in soil and rows.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when you do not know it is coming.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that makes the story go in a new direction or changes what the characters thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that could produce this story =="]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


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


def valid_findings() -> list[str]:
    return sorted(FINDINGS)


CURATED = [
    StoryParams(find="carrot_cache", name_piper="Piper", name_bond="Bond", name_ful="Ful"),
    StoryParams(find="bean_basket", name_piper="Piper", name_bond="Bond", name_ful="Ful"),
    StoryParams(find="pumpkin_note", name_piper="Piper", name_bond="Bond", name_ful="Ful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1. #show bond_stronger/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name_piper} / {p.name_bond} / {p.name_ful} ({p.find})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
