#!/usr/bin/env python3
"""
Story world: a rhyming scuba quest with an iguana surprise.

A tiny, self-contained story simulation about a child or diver who goes on a
quest beneath the sea, repeats a call or action in a pattern, and astonishes an
iguana along the way. The world model keeps track of physical meters and
emotional memes so the story can turn from search to discovery to delight.
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

HERO_NAMES = ["Milo", "Nina", "Pia", "Theo", "Luna", "Omar", "Iris", "Zane"]
HERO_TYPES = ["child", "diver"]
COMPANION_NAMES = ["Nemo", "Pip", "Kiki", "Roo", "Bibi"]
LOCATIONS = {
    "reef": "the reef",
    "cove": "the moonlit cove",
    "lagoon": "the lagoon",
}
QUESTS = {
    "pearl": {
        "goal": "find the pearl",
        "lost": "lost pearl",
        "object": "a shining pearl",
        "reward": "pearlshell",
    },
    "starfish": {
        "goal": "find the starfish",
        "lost": "lost starfish charm",
        "object": "a little starfish charm",
        "reward": "star-glow",
    },
}
REPETITION_PATTERNS = {
    "chant": {
        "verb": "chant",
        "line": "splash and dash",
        "echo": "The chant went, splash and dash, splash and dash.",
    },
    "knock": {
        "verb": "tap",
        "line": "tap and clap",
        "echo": "The taps went, tap and clap, tap and clap.",
    },
    "wave": {
        "verb": "wave",
        "line": "wave and brave",
        "echo": "The wave went, wave and brave, wave and brave.",
    },
}
GEAR = {
    "scuba": {
        "label": "scuba gear",
        "phrase": "scuba gear",
        "effect": "breathe below the sea",
        "covers": {"water"},
    },
    "goggles": {
        "label": "goggles",
        "phrase": "clear goggles",
        "effect": "see through the blue",
        "covers": {"eyes"},
    },
}
IGUANA_STATES = {
    "sleepy": "sleepy",
    "shy": "shy",
    "astonished": "astonished",
}



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
class StoryParams:
    location: str
    quest: str
    repetition: str
    hero_name: str
    hero_type: str
    companion_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    traits: list[str] = field(default_factory=list)

    companion: object | None = None
    goggles: object | None = None
    hero: object | None = None
    iguana: object | None = None
    quest_item: object | None = None
    scuba: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
# Narrative helpers
# ---------------------------------------------------------------------------

def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def intro_line(hero: Entity, location: str) -> str:
    return (
        f"Little {hero.id} set out with a grin, "
        f"to {location} where the bright waves spin."
    )


def quest_line(quest: str, location: str) -> str:
    return f"They wished to {_safe_lookup(QUESTS, quest)['goal']} at {location}, where the blue tide hummed like a tune."


def repetition_line(pattern: str) -> str:
    info = _safe_lookup(REPETITION_PATTERNS, pattern)
    return f"{info['echo']} Again and again, they said the same sweet strain."


def astonish_line(iguana: Entity, pattern: str) -> str:
    info = _safe_lookup(REPETITION_PATTERNS, pattern)
    return (
        f"Down on a rock sat {iguana.label}, an iguana so green and bright. "
        f"It blinked in shock when the bubbles went {info['line']}, a funny, bouncy sight."
    )


def resolve_line(hero: Entity, quest: str, companion: Entity) -> str:
    return (
        f"At last they found the {_safe_lookup(QUESTS, quest)['lost']}, tucked by a shell so small. "
        f"{hero.id} laughed with {companion.id}, and the sea seemed to cheer for all."
    )


def final_image(hero: Entity, quest: str) -> str:
    return (
        f"Home they sailed with the prize in tow, "
        f"their hearts all warm and aglow. "
        f"The quest was done, the rhyme was spun, "
        f"and {hero.id} held the {_safe_lookup(QUESTS, quest)['object']} like a moonbeam's glow."
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["brave", "curious"],
        meters={"joy": 0.0, "wonder": 0.0},
        memes={"hope": 0.0, "astonish": 0.0},
    ))
    companion = world.add(Entity(
        id=params.companion_name,
        kind="character",
        type="dolphin",
        label=params.companion_name,
        meters={"help": 0.0},
        memes={"cheer": 0.0},
    ))
    iguana = world.add(Entity(
        id="iguana",
        kind="character",
        type="iguana",
        label="an iguana",
        meters={"surprise": 0.0},
        memes={"astonish": 0.0},
    ))
    quest_item = world.add(Entity(
        id="quest_item",
        kind="thing",
        type=params.quest,
        label=_safe_lookup(QUESTS, params.quest)["object"],
        phrase=_safe_lookup(QUESTS, params.quest)["object"],
        owner=None,
    ))
    scuba = world.add(Entity(
        id="scuba",
        kind="thing",
        type="gear",
        label=GEAR["scuba"]["label"],
        phrase=GEAR["scuba"]["phrase"],
        owner=hero.id,
        worn_by=hero.id,
    ))
    goggles = world.add(Entity(
        id="goggles",
        kind="thing",
        type="gear",
        label=GEAR["goggles"]["label"],
        phrase=GEAR["goggles"]["phrase"],
        owner=hero.id,
        worn_by=hero.id,
    ))

    world.facts.update(hero=hero, companion=companion, iguana=iguana, quest_item=quest_item)
    world.facts.update(scuba=scuba, goggles=goggles, quest=params.quest, repetition=params.repetition)

    # Act 1: setup
    world.say(intro_line(hero, _safe_lookup(LOCATIONS, params.location)))
    world.say(quest_line(params.quest, _safe_lookup(LOCATIONS, params.location)))
    world.say(
        f"With {scuba.label} and {goggles.label} on tight, "
        f"{hero.id} felt ready to go and to fight the fright."
    )

    # Act 2: repeated attempt and astonishment
    world.para()
    info = _safe_lookup(REPETITION_PATTERNS, params.repetition)
    hero.memes["hope"] += 1
    hero.meters["distance"] = 1.0
    world.say(
        f"Under the water, {hero.id} began to {info['verb']} "
        f"{info['line']}, {info['line']}."
    )
    companion.memes["cheer"] += 1
    world.say(f"{companion.id} swam near, a guide in the blue, and the path felt narrow but true.")
    iguana.memes["astonish"] += 1
    iguana.meters["surprise"] += 1
    world.say(astonish_line(iguana, params.repetition))
    world.say(
        f"The little beast did not flee, but bobbed and blinked in wonder and glee."
    )

    # Act 3: quest resolution
    world.para()
    hero.memes["wonder"] += 1
    quest_item.owner = hero.id
    world.say(resolve_line(hero, params.quest, companion))
    world.say(final_image(hero, params.quest))
    hero.meters["distance"] = 2.0
    hero.memes["joy"] += 2
    iguana.memes["astonish"] += 1
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.params
    q = _safe_lookup(QUESTS, p.quest)["goal"]
    rep = _safe_lookup(REPETITION_PATTERNS, p.repetition)["verb"]
    return [
        f"Write a short rhyming story about a {p.hero_type} on a scuba quest at {_safe_lookup(LOCATIONS, p.location)}.",
        f"Tell a gentle sea adventure where {p.hero_name} uses scuba gear, repeats a phrase, and astonishes an iguana.",
        f"Write a child-friendly rhyming tale that includes a repeated line and a happy quest ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    hero = _safe_fact(world, world.facts, "hero")
    iguana = _safe_fact(world, world.facts, "iguana")
    companion = _safe_fact(world, world.facts, "companion")
    quest = p.quest
    rep = _safe_lookup(REPETITION_PATTERNS, p.repetition)
    return [
        QAItem(
            question=f"What kind of quest did {hero.id} go on at {_safe_lookup(LOCATIONS, p.location)}?",
            answer=f"{hero.id} went on a {_safe_lookup(QUESTS, quest)['goal']} beneath {_safe_lookup(LOCATIONS, p.location)}.",
        ),
        QAItem(
            question=f"What repeated words did {hero.id} say while searching?",
            answer=f"{hero.id} kept saying, '{rep['line']}, {rep['line']}.'",
        ),
        QAItem(
            question=f"What happened to the iguana when the bubbles started?",
            answer=f"The iguana was astonished and blinked at the bubbly sight.",
        ),
        QAItem(
            question=f"Who helped {hero.id} on the quest?",
            answer=f"{companion.id} swam near and guided the way through the blue water.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is scuba gear for?",
            answer="Scuba gear helps a person breathe underwater and explore below the sea.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like a treasure or a lost prize.",
        ),
        QAItem(
            question="Why can repetition sound nice in a rhyming story?",
            answer="Repetition can make a story feel musical, easy to remember, and fun to say aloud.",
        ),
        QAItem(
            question="What is an iguana?",
            answer="An iguana is a lizard with a long body and a tail, and some iguanas live near warm places.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the chosen location supports a quest and the hero has
% scuba gear to explore the watery setting.
valid_story(L, Q, R) :- location(L), quest(Q), repetition(R), supports(L, Q), gear(scuba).

% Repetition is part of the intended style for every generated story.
styled(R) :- repetition(R).

% The iguana is astonished when the repeated line is performed near it.
astonished(iguana, R) :- repetition(R), valid_story(_, _, R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
        lines.append(asp.fact("supports", loc, "pearl"))
        lines.append(asp.fact("supports", loc, "starfish"))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in REPETITION_PATTERNS:
        lines.append(asp.fact("repetition", r))
    lines.append(asp.fact("gear", "scuba"))
    lines.append(asp.fact("character", "iguana"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(loc, q, r) for loc in LOCATIONS for q in QUESTS for r in REPETITION_PATTERNS}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python story space ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming scuba quest with an astonished iguana.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--repetition", choices=REPETITION_PATTERNS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(LOCATIONS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    repetition = getattr(args, "repetition", None) or rng.choice(list(REPETITION_PATTERNS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANION_NAMES)
    return StoryParams(
        location=place,
        quest=quest,
        repetition=repetition,
        hero_name=name,
        hero_type=hero_type,
        companion_name=companion,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    StoryParams(location="reef", quest="pearl", repetition="chant", hero_name="Milo", hero_type="child", companion_name="Nemo"),
    StoryParams(location="cove", quest="starfish", repetition="knock", hero_name="Luna", hero_type="diver", companion_name="Pip"),
    StoryParams(location="lagoon", quest="pearl", repetition="wave", hero_name="Iris", hero_type="child", companion_name="Kiki"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
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
            header = f"### {p.hero_name}: {p.quest} at {p.location} ({p.repetition})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
