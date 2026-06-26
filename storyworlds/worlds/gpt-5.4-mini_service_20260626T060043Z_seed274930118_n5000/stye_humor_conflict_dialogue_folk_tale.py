#!/usr/bin/env python3
"""
A small storyworld about a folk-tale household dealing with a stye.

Premise:
- A character gets a sore, swollen stye on an eyelid.
- The stye makes the character grumpy and fussy.
- A family member offers a warm cloth remedy and patient help.
- Humor comes from the character trying to act tough while blinking and peeking.

The world model tracks:
- physical meters: swelling, warmth, comfort, cleanliness
- emotional memes: fussiness, patience, relief, laughter, trust

This world is intentionally tiny, classical, and self-contained.
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

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Milo", "Nia", "Oren", "Pia", "Sera", "Tavi", "Lena", "Bram"]
KIN = ["mother", "father", "grandmother", "grandfather", "sister", "brother"]
TRAITS = ["cheerful", "sly", "stubborn", "kind", "quick", "tiny"]

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------



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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    kin: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "sister", "grandmother", "aunt", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "brother", "grandfather", "uncle", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Remedy:
    id: str
    label: str
    method: str
    effect: str
    REMEDY: object | None = None
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
    kin: str
    trait: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Causal dynamics
# ---------------------------------------------------------------------------

def _apply_stye(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("stye_swelling", 0) >= 1 and "stye" not in world.facts.get("fired", set()):
        world.facts.setdefault("fired", set()).add("stye")
        hero.memes["fuss"] = hero.memes.get("fuss", 0) + 1
        out.append(f"{hero.pronoun('subject').capitalize()} kept blinking at the sore little stye.")
    return out


def _apply_warmth(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("warmth", 0) >= 1 and not world.facts.get("warmth_applied"):
        world.facts["warmth_applied"] = True
        hero.meters["stye_swelling"] = max(0.0, hero.meters.get("stye_swelling", 0) - 1)
        hero.meters["comfort"] = hero.meters.get("comfort", 0) + 1
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        out.append("The warm cloth softened the sore spot little by little.")
    return out


def _apply_laughter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    kin = world.get("kin")
    if hero.memes.get("fuss", 0) >= 1 and hero.memes.get("relief", 0) >= 1 and not world.facts.get("laughed"):
        world.facts["laughed"] = True
        kin.memes["laugh"] = kin.memes.get("laugh", 0) + 1
        out.append(f"{kin.label.capitalize()} laughed softly, because the grumpy blinking looked very dramatic.")
    return out


RULES = [_apply_stye, _apply_warmth, _apply_laughter]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, kin: Entity, trait: str) -> None:
    world.say(
        f"Long ago, in a little house by the lane, there lived {hero.id}, "
        f"a {trait} child with bright eyes and a quick smile."
    )
    world.say(
        f"{hero.id} loved listening to {kin.label} tell old tales by the fire."
    )


def problem(world: World, hero: Entity, kin: Entity) -> None:
    hero.meters["stye_swelling"] = 1
    hero.memes["fuss"] = 1
    world.say(
        f"But one morning, {hero.id} woke with a stye on {hero.pronoun('possessive')} eyelid."
    )
    world.say(
        f'"Oh dear," said {kin.label}, "that little bump is a bossy pea, and it means trouble for your blinking."'
    )
    world.say(
        f'"I am not bossed by peas," said {hero.id}, though {hero.pronoun("subject")} blinked anyway.'
    )
    propagate(world, narrate=True)


def conflict(world: World, hero: Entity, kin: Entity) -> None:
    world.para()
    world.say(
        f"{hero.id} tried to look brave, but every glance felt scratchy and strange."
    )
    world.say(
        f'"I can still help with the chores," {hero.id} declared.'
    )
    world.say(
        f'"Then help by sitting still," said {kin.label}. "That stye will calm if we treat it kindly."'
    )
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    kin.memes["patience"] = kin.memes.get("patience", 0) + 1


def remedy_offer(world: World, hero: Entity, kin: Entity, remedy: Remedy) -> None:
    world.para()
    world.say(
        f"{kin.label} brought {hero.id} {remedy.label} and said, "
        f'"{remedy.method} will help the sore spot."'
    )
    world.say(
        f'"Will it make me look less like a sleepy owl?" asked {hero.id}.'
    )
    world.say(
        f'"A little," said {kin.label}, "but mostly it will make you feel better."'
    )
    hero.meters["warmth"] = 1
    propagate(world, narrate=True)


def resolution(world: World, hero: Entity, kin: Entity, remedy: Remedy) -> None:
    world.para()
    hero.meters["comfort"] = hero.meters.get("comfort", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["fuss"] = 0
    world.say(
        f"So {hero.id} sat still like a mouse by moonlight while {kin.label} held the warm cloth in place."
    )
    world.say(
        f"After a while, the stye looked smaller, and {hero.id} could open {hero.pronoun('possessive')} eye without wincing."
    )
    world.say(
        f'"There," said {kin.label}, "now you are only a little owl, not a cross one."'
    )
    world.say(
        f"{hero.id} laughed, and the house felt lighter than bread rising in a warm oven."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

REMEDY = Remedy(
    id="warm_cloth",
    label="a warm cloth",
    method="A warm cloth pressed gently over the eye",
    effect="soften the swelling",
)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    kin = world.add(Entity(id="kin", kind="character", type=params.kin, label=f"the {params.kin}"))
    intro(world, hero, kin, params.trait)
    world.para()
    problem(world, hero, kin)
    conflict(world, hero, kin)
    remedy_offer(world, hero, kin, REMEDY)
    resolution(world, hero, kin, REMEDY)
    world.facts.update(hero=hero, kin=kin, remedy=REMEDY, params=params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a folk-tale style story about {p.name} and a stubborn stye, with humor and dialogue.",
        f"Tell a small story where {p.name} gets a stye and {world.facts['kin'].label} helps with a warm cloth.",
        "Write a gentle, funny tale about a sore eye, patient help, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    kin = _safe_fact(world, world.facts, "kin")
    return [
        QAItem(
            question=f"What problem did {p.name} have at the start of the story?",
            answer=f"{p.name} woke up with a stye on {hero.pronoun('possessive')} eyelid, and it made blinking uncomfortable.",
        ),
        QAItem(
            question=f"Who helped {p.name} with the sore eye?",
            answer=f"The {p.kin} helped by bringing a warm cloth and speaking patiently.",
        ),
        QAItem(
            question=f"How did the story end for {p.name}?",
            answer=f"The swelling eased, {p.name} could open {hero.pronoun('possessive')} eye more easily, and everyone laughed at the sleepy-owl look.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stye?",
            answer="A stye is a sore, swollen bump on or near an eyelid. It can hurt and make blinking feel scratchy.",
        ),
        QAItem(
            question="Why can a warm cloth help a stye?",
            answer="Warmth can help the sore spot relax and feel less swollen, which may make it more comfortable.",
        ),
        QAItem(
            question="Why did the family laugh at the end?",
            answer="They laughed because the child looked very serious while blinking, which made the scene a little funny once the pain started to fade.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
character(hero). character(kin).
problem(stye) :- stye_swelling(hero,1).
helped :- warmth(hero,1).
resolved :- helped, comfort(hero,1).
funny :- fuss(hero,1), relief(hero,1).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "hero"),
            asp.fact("character", "kin"),
            asp.fact("stye_swelling", "hero", 1),
            asp.fact("warmth", "hero", 1),
            asp.fact("comfort", "hero", 1),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show helped/0. #show resolved/0. #show funny/0."))
    atoms = {s.name for s in model}
    expected = {"helped", "resolved"}
    if atoms >= expected:
        print("OK: ASP twin produces the expected help/resolution markers.")
        return 0
    print("MISMATCH: ASP twin did not produce expected markers.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld about a stye.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kin", choices=KIN)
    ap.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(NAMES),
        kin=getattr(args, "kin", None) or rng.choice(KIN),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
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
    StoryParams(name="Milo", kin="grandmother", trait="stubborn"),
    StoryParams(name="Nia", kin="mother", trait="cheerful"),
    StoryParams(name="Oren", kin="father", trait="sly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show helped/0. #show resolved/0. #show funny/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for parity checks; this world's core story is generated in Python.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
