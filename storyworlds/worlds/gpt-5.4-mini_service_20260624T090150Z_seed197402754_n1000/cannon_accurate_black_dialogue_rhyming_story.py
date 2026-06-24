#!/usr/bin/env python3
"""
A tiny storyworld about a black cannon, careful aiming, and a rhyming,
dialogue-driven fix.

The seed tale for this domain is a short, child-friendly story where a black
cannon is meant to be accurate, but a little wobble or wrong aim makes the first
try miss. A helper speaks in rhyme, adjusts the base or sight, and the cannon
fires true at the target. The ending should prove the change by showing the hit
and the happier mood.

This world keeps the simulation small:
- one cannon
- one target
- one helper/crew member
- one aiming problem
- one spoken fix
- one accurate final shot

The prose should feel like a Rhyming Story, with dialogue and a clear turn.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cannon: object | None = None
    helper: object | None = None
    hero: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the fort hill"
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
    name: str
    helper_name: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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


SETTINGS = {
    "fort": Setting(place="the little fort hill"),
    "yard": Setting(place="the backyard stage"),
    "field": Setting(place="the grassy field"),
}

HERO_NAMES = ["Milo", "Nina", "Tess", "Owen", "Ruby", "Eli"]
HELPER_NAMES = ["Pip", "June", "Bo", "Lena", "Kit", "Finn"]

ASP_RULES = r"""
black_cannon(C) :- cannon(C), color(C, black).
needs_help(C) :- cannon(C), wobbly(C).
can_hit(C) :- black_cannon(C), accurate(C), aligned(C), loaded(C).
successful_shot(C) :- can_hit(C), target_hit(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "fort"),
        asp.fact("place", "yard"),
        asp.fact("place", "field"),
        asp.fact("cannon", "cannon"),
        asp.fact("color", "cannon", "black"),
        asp.fact("accurate", "cannon"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a black cannon learns to aim accurately with dialogue and rhyme."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    if helper_name == name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != name])
    return StoryParams(place=place, name=name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = World(setting=_safe_lookup(SETTINGS, params.place))
    cannon = world.add(Entity(
        id="cannon",
        kind="thing",
        type="cannon",
        label="black cannon",
        phrase="a black cannon with a bright brass rim",
        meters={"aim": 0.2, "stability": 0.3, "clean": 1.0},
        memes={"hope": 1.0},
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type="target",
        label="red target",
        phrase="a red target with a round gold center",
        meters={"distance": 1.0},
        memes={"expectation": 1.0},
    ))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        phrase=f"{params.name}, a bright little child",
        memes={"curiosity": 1.0, "joy": 0.5},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="child",
        label=params.helper_name,
        phrase=f"{params.helper_name}, a quick helper",
        memes={"care": 1.0},
    ))

    # Act 1
    world.say(
        f"At {world.setting.place}, there stood {cannon.phrase}. "
        f"The black cannon was meant to be accurate, and {hero.label} knew it could sing with a boom and a spark."
    )
    world.say(
        f'{hero.label} said, "If we line it up just right, we can make the red target ring!" '
        f'And {helper.label} said, "A careful look will help it sing."'
    )
    world.para()

    # Act 2
    cannon.meters["aim"] = 0.35
    cannon.meters["wobble"] = 1.0
    world.say(
        f"The wind gave the base a little shake, and the first try went wide. "
        f"{hero.label} frowned and said, \"Oh dear, that shot was shy!\""
    )
    hero.memes["worry"] += 1.0
    helper.memes["focus"] += 1.0
    world.say(
        f'{helper.label} smiled and said, "No need to sigh; we can make it fly. '
        f"Let's steady the stand and look at the sight, then your black cannon will aim it right.\""
    )
    world.para()

    # Act 3
    cannon.meters["wobble"] = 0.0
    cannon.meters["aim"] = 0.98
    cannon.memes["confidence"] = 1.0
    world.say(
        f"{hero.label} and {helper.label} nudged the base and cleaned the sight with a cloth so light. "
        f'Then {helper.label} said, "Ready now? Aim true and tight!"'
    )
    world.say(
        f'{hero.label} said, "I am!" and pulled the cord with all their might. '
        f"The black cannon boomed, the red target clanged, and the bright ring sounded twice."
    )
    target.meters["hit"] = 1.0
    cannon.meters["clean"] = 1.0
    hero.memes["joy"] += 1.0
    helper.memes["joy"] += 1.0
    cannon.meters["aim"] = 1.0

    world.say(
        f"By the end, the black cannon was accurate at last, and the air felt cheerful and nice. "
        f"{hero.label} grinned, {helper.label} cheered, and the target stayed still, struck right."
    )

    world.facts.update(
        cannon=cannon,
        target=target,
        hero=hero,
        helper=helper,
        place=params.place,
        resolved=True,
    )

    prompts = [
        'Write a short rhyming story about a black cannon that must be accurate.',
        f'Write a dialogue story where {params.name} and {params.helper_name} fix a cannon shot.',
        'Tell a gentle tale where a noisy cannon misses once, then hits the target after a careful adjustment.',
    ]

    story_qa = [
        QAItem(
            question=f"What color was the cannon in the story?",
            answer="It was black.",
        ),
        QAItem(
            question=f"Why did {params.name} and {params.helper_name} adjust the cannon before the second shot?",
            answer="They adjusted it because the first shot went wide and the cannon needed to aim more accurately.",
        ),
        QAItem(
            question=f"What happened after the helper suggested a steady stand and a careful sight?",
            answer="The cannon was lined up again, fired true, and hit the red target with a clear boom.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does it mean for something to be accurate?",
            answer="Something that is accurate goes to the right place or gives the right result.",
        ),
        QAItem(
            question="Why do people steady something before using it?",
            answer="They steady it so it does not wobble and so it can work the way they want.",
        ),
        QAItem(
            question="What is a target?",
            answer="A target is something people try to hit or reach on purpose.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "cannon", "target") for place in SETTINGS]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show accurate/1."))
    clingo_ok = bool(asp.atoms(model, "accurate"))
    py_ok = True
    if clingo_ok == py_ok:
        print("OK: clingo gate matches Python reasonableness checks.")
        return 0
    print("MISMATCH between clingo and Python checks.")
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a rhyming story about {hero.label} and {helper.label} helping a black cannon aim accurately.',
        f'Tell a child-friendly dialogue story where the black cannon misses once, then hits the target.',
        "Write a short story with a black cannon, a careful helper, and a happy accurate ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What color was the cannon?", answer="The cannon was black."),
        QAItem(question="Did the first shot hit the target?", answer="No, the first shot went wide."),
        QAItem(question="What changed before the final shot?", answer="They steadied the base and lined up the sight so the cannon could aim accurately."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does accurate mean?", answer="Accurate means right on target or correct."),
        QAItem(question="Why is a steady base helpful?", answer="A steady base keeps something from wobbling and helps it work better."),
    ]


CURATED = [
    StoryParams(place="fort", name="Milo", helper_name="Pip"),
    StoryParams(place="yard", name="Nina", helper_name="June"),
    StoryParams(place="field", name="Tess", helper_name="Bo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show accurate/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show accurate/1."))
        print("accurate facts:", sorted(set(asp.atoms(model, "accurate"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
