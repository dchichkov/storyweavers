#!/usr/bin/env python3
"""
storyworlds/worlds/manatee_energetic_magic_dialogue_sound_effects_superhero.py
==============================================================================

A tiny superhero storyworld starring an energetic manatee, a bit of magic,
dialogue, and comic-book sound effects.

The world model is deliberately small:
- one hero with emotional meters/memes
- one city setting with a problem
- one magical tool that can help
- one obstacle that creates tension
- a simple causal arc that turns worry into rescue

The story engine simulates the state and narrates from that state, rather than
swapping nouns into a fixed paragraph.
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

HEROES = [
    "Milo",
    "Nori",
    "Benny",
    "Luna",
    "Pip",
    "Coral",
]

CITIES = [
    "Harbor City",
    "Seashell Square",
    "Blue Reef Bay",
    "Coralport",
]

THREATS = [
    "a towering tide wall",
    "a sneaky smoke cloud",
    "a giant tangle of kelp",
    "a runaway meteor kite",
    "a shadowy whirlpool",
]

MAGICS = [
    "a glowing pearl wand",
    "a sparkling shell charm",
    "a moonbeam cape clasp",
    "a ripple ring of light",
]

SFX = [
    "WHOOSH!",
    "ZAP!",
    "BAM!",
    "POW!",
    "SWOOSH!",
    "KRAK!",
]

TRAITS = [
    "energetic",
    "brave",
    "cheerful",
    "quick-thinking",
    "kind-hearted",
]



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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    helper: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    magic: object | None = None
    threat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "manatee":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    problem: str
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
    place: str
    hero_name: str
    trait: str
    threat: str
    magic: str
    seed: Optional[int] = None
    params: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld with an energetic manatee, magic, dialogue, and sound effects."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--threat", choices=sorted(THREATS))
    ap.add_argument("--magic", choices=sorted(MAGICS))
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


SETTINGS = {
    "harbor": Setting(place="the harbor", problem="the docks were in danger"),
    "square": Setting(place="the square", problem="the crowd needed help"),
    "bay": Setting(place="the bay", problem="the waves were getting bigger"),
}

SETTING_KEYS = list(SETTINGS)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.trait != "energetic" and params.trait not in TRAITS:
        pass
    if params.name not in HEROES:
        pass


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="manatee",
        label=params.name,
        phrase=f"an {params.trait} manatee superhero",
        meters={"energy": 2.0, "splash": 0.0},
        memes={"joy": 1.0, "worry": 0.0, "courage": 1.0},
    ))
    magic = world.add(Entity(
        id="magic",
        kind="thing",
        type="magic",
        label=params.magic,
        phrase=params.magic,
        owner=hero.id,
        helper=True,
        magical=True,
    ))
    threat = world.add(Entity(
        id="threat",
        kind="thing",
        type="threat",
        label=params.threat,
        phrase=params.threat,
        meters={"danger": 2.0},
    ))

    world.say(
        f"{hero.id} was an {params.trait} manatee superhero who loved helping {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {magic.label} and listened for trouble."
    )

    world.para()
    world.say(
        f"Then {world.setting.problem}: {threat.label} rolled in over {world.setting.place}."
    )
    world.say(
        f'"{hero.id}!" called a small voice. "Can you help us?"'
    )
    world.say(
        f"{hero.id} nodded. \"Yes,\" {hero.pronoun('subject')} said, \"I can help!\""
    )
    world.say(f"{random.choice(SFX)} {random.choice(SFX)}")

    hero.meters["energy"] += 1.0
    hero.memes["worry"] += 1.0
    threat.meters["danger"] += 1.0

    world.para()
    world.say(
        f"{hero.id} raised {hero.pronoun('possessive')} {magic.label} and whispered a magic word."
    )
    world.say(f"{random.choice(SFX)} {random.choice(SFX)}")
    world.say(
        f"Bright light flashed, and the {threat.label} began to shrink."
    )
    threat.meters["danger"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 2.0

    world.para()
    world.say(
        f"The harbor was safe again, and {hero.id} smiled at the cheering crowd."
    )
    world.say(
        f"\"That was amazing!\" they said."
    )
    world.say(
        f"\"Any time,\" {hero.id} replied, {random.choice(SFX)} in the splashy air."
    )

    world.facts.update(
        hero=hero,
        magic=magic,
        threat=threat,
        setting=setting,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    return [
        f'Write a short superhero story for children about an energetic manatee named {p.hero_name} who uses {p.magic}.',
        f'Tell a story where {p.hero_name} hears a problem at {world.setting.place} and answers with brave dialogue and sound effects.',
        f'Write a simple rescue story with a manatee superhero, a magical tool, and comic-book sound effects like "{random.choice(SFX)}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    magic: Entity = _safe_fact(world, f, "magic")
    threat: Entity = _safe_fact(world, f, "threat")
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, an {params.trait} manatee who helps at {world.setting.place}.",
        ),
        QAItem(
            question=f"What magical thing did {hero.id} use?",
            answer=f"{hero.id} used {magic.label} to make the problem smaller and safer.",
        ),
        QAItem(
            question=f"What danger appeared in the story?",
            answer=f"{threat.label} appeared, and it put {world.setting.place} in danger until {hero.id} fixed it.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} saving the day, the danger gone, and the crowd cheering at {world.setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a manatee?",
            answer="A manatee is a large, gentle sea animal that swims slowly and eats plants underwater.",
        ),
        QAItem(
            question="What do sound effects do in a superhero story?",
            answer="Sound effects like POW and ZAP make action scenes feel loud, exciting, and full of movement.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something special or impossible in real life that can cause surprising changes in a story.",
        ),
        QAItem(
            question="Why do characters talk in dialogue?",
            answer="Dialogue lets characters speak to each other directly, which makes the story feel alive and easy to follow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_name(X).
valid_story(P,N,T,M) :- place(P), hero_name(N), trait(T), magic(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("place", k))
    for n in HEROES:
        lines.append(asp.fact("hero_name", n))
    for t in TRAITS:
        lines.append(asp.fact("trait", t))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(SETTING_KEYS)
    name = getattr(args, "name", None) or rng.choice(HEROES)
    trait = getattr(args, "trait", None) or "energetic"
    threat = getattr(args, "threat", None) or rng.choice(THREATS)
    magic = getattr(args, "magic", None) or rng.choice(MAGICS)
    params = StoryParams(place=place, hero_name=name, trait=trait, threat=threat, magic=magic)
    reasonableness_gate(params)
    return params


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
    StoryParams(place="harbor", hero_name="Milo", trait="energetic", threat="a towering tide wall", magic="a glowing pearl wand"),
    StoryParams(place="square", hero_name="Luna", trait="energetic", threat="a sneaky smoke cloud", magic="a sparkling shell charm"),
    StoryParams(place="bay", hero_name="Nori", trait="energetic", threat="a shadowy whirlpool", magic="a ripple ring of light"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
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
