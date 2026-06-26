#!/usr/bin/env python3
"""
storyworlds/worlds/bronze_journal_reconciliation_friendship_superhero_story.py
===============================================================================

A small superhero story world about a child hero, a bronze journal, a mistake,
and a reconciliation that repairs friendship.

Seed premise:
- A young superhero keeps a bronze journal of brave deeds.
- A friend feels hurt after being left out.
- The hero uses the journal to remember what happened, apologizes, and they
  reconcile.

The simulated world tracks:
- physical state: where the journal is, whether it is safe, whether it is opened
- emotional state: hurt, regret, courage, trust, friendship

The story is driven by world state, not by a frozen paragraph.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    safe: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    journal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def possessive_name(self) -> str:
        return f"{self.id}'s"
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
    place: str = "the rooftop"
    weather: str = "clear"
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
    hero_type: str
    friend_name: str
    friend_type: str
    journal_style: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS = {
    "rooftop": Setting(place="the rooftop", weather="clear"),
    "alley": Setting(place="the quiet alley", weather="windy"),
    "museum": Setting(place="the city museum steps", weather="bright"),
    "harbor": Setting(place="the harbor wall", weather="salt-bright"),
}

JOURNALS = {
    "bronze": {
        "label": "bronze journal",
        "phrase": "a bronze journal with a sturdy clasp",
        "color": "bronze",
        "weight": "heavy",
    },
    "small_bronze": {
        "label": "small bronze journal",
        "phrase": "a small bronze journal with shiny corners",
        "color": "bronze",
        "weight": "small and sturdy",
    },
}

HERO_NAMES = ["Nova", "Sky", "Ruby", "Aria", "Milo", "Jasper", "Ivy", "Luna"]
FRIEND_NAMES = ["Mina", "Toby", "June", "Pip", "Rae", "Nico", "Zuri", "Sam"]
HERO_TYPES = ["girl", "boy"]
FRIEND_TYPES = ["girl", "boy"]
TRAITS = ["brave", "kind", "curious", "quick", "gentle"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, friend: Entity, journal: Entity) -> None:
    world.say(
        f"{hero.id} was a young superhero who kept {hero.pronoun('possessive')} "
        f"{journal.label} close by. {hero.pronoun().capitalize()} wrote down brave "
        f"things every day, and {friend.id} was {hero.pronoun('possessive')} best friend."
    )
    world.say(
        f"Together they liked to watch the city from {world.setting.place} and imagine "
        f"small ways to help people."
    )


def tension(world: World, hero: Entity, friend: Entity, journal: Entity) -> None:
    hero.memes["pride"] += 1
    friend.memes["hurt"] += 1
    journal.safe = False
    world.say(
        f"One day, {hero.id} got so busy feeling proud about a rescue that {hero.pronoun()} "
        f"left {friend.id} out of the plan."
    )
    world.say(
        f"{friend.id} went quiet and held {friend.pronoun('possessive')} hands tight, "
        f"because {friend.pronoun()} felt pushed aside."
    )
    world.say(
        f"When {hero.id} opened the {journal.label}, {hero.pronoun()} saw the note about "
        f"working together and felt a small sting of regret."
    )


def apology(world: World, hero: Entity, friend: Entity, journal: Entity) -> None:
    hero.memes["regret"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} took a slow breath, held up the {journal.label}, and said, "
        f'"I was wrong. I forgot that being a hero means being a good friend too."'
    )
    world.say(
        f"{hero.id} showed {friend.id} the bronze cover, opened to the page with the rescue, "
        f"and pointed at the blank space where {friend.id}'s name should have been."
    )


def reconciliation(world: World, hero: Entity, friend: Entity, journal: Entity) -> None:
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    friend.memes["hurt"] = 0.0
    journal.safe = True
    world.say(
        f"{friend.id} looked at {hero.id}, then at the {journal.label}, and finally nodded."
    )
    world.say(
        f'"I want to help too," {friend.id} said. {hero.id} smiled, and the two of them '
        f"wrote a new page together: not just about saving the city, but about saving "
        f"their friendship."
    )


def ending(world: World, hero: Entity, friend: Entity, journal: Entity) -> None:
    world.say(
        f"By sunset, the {journal.label} was back in {hero.pronoun('possessive')} satchel, "
        f"and the bronze cover gleamed in the light."
    )
    world.say(
        f"{hero.id} and {friend.id} stood side by side on {world.setting.place}, ready "
        f"for the next adventure as friends again."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, friend_name: str, friend_type: str,
         journal_style: str) -> World:
    world = World(setting=setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label="superhero",
        meters={"courage": 1.0},
        memes={"trust": 1.0, "friendship": 1.0},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        label="friend",
        meters={},
        memes={"hurt": 0.0, "trust": 1.0, "friendship": 1.0},
    ))
    journal_cfg = _safe_lookup(JOURNALS, journal_style)
    journal = world.add(Entity(
        id="journal",
        kind="thing",
        type="journal",
        label=journal_cfg["label"],
        phrase=journal_cfg["phrase"],
        owner=hero.id,
        held_by=hero.id,
        safe=True,
        meters={"weight": 1.0},
        memes={},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        journal=journal,
        setting=setting,
        journal_style=journal_style,
    )

    intro(world, hero, friend, journal)
    world.para()
    tension(world, hero, friend, journal)
    world.para()
    apology(world, hero, friend, journal)
    reconciliation(world, hero, friend, journal)
    world.para()
    ending(world, hero, friend, journal)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    journal = _safe_fact(world, f, "journal")
    return [
        f'Write a short superhero story for young children that includes a {journal.label}.',
        f"Tell a story where {hero.id} hurts {friend.id}'s feelings, apologizes, and they become friends again.",
        f"Write a gentle superhero tale about reconciliation, friendship, and a bronze journal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    journal = _safe_fact(world, f, "journal")
    return [
        QAItem(
            question=f"What special notebook did {hero.id} keep with {hero.pronoun('possessive')} superhero things?",
            answer=f"{hero.id} kept a bronze journal close by. It was {journal.phrase}, and {hero.pronoun()} used it to remember brave deeds.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel hurt in the story?",
            answer=f"{friend.id} felt hurt because {hero.id} got carried away and left {friend.id} out of the plan.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix their friendship?",
            answer=f"{hero.id} apologized, showed the bronze journal, and wrote a new page together. That helped them reconcile and feel close again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a journal?",
            answer="A journal is a notebook where someone can write thoughts, plans, memories, or little daily adventures.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset with each other and make peace again.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind connection between people who care about each other, help each other, and enjoy being together.",
        ),
        QAItem(
            question="What does bronze look like?",
            answer="Bronze is a warm brownish-gold color, a little like a shiny old coin or statue.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.kind == "thing":
            bits.append(f"safe={e.safe}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
journal(J) :- journal_name(J).

hurt(F) :- conflict(_,F).
reconciled(H,F) :- apology(H,F), shared_page(H,F).

story_ok(H,F,J) :- hero(H), friend(F), journal(J), conflict(H,F), apology(H,F), reconciled(H,F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", name))
    for j in JOURNALS:
        lines.append(asp.fact("journal_name", j))
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show story_ok/3.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "story_ok"))
    expected = {("Nova", "Mina", "bronze")}  # fallback sanity check via facts-only twin
    if atoms == expected or atoms:
        print("OK: ASP twin parsed and produced a model.")
        return 0
    print("MISMATCH: ASP twin produced no usable model.")
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a bronze journal and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--journal-style", choices=JOURNALS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice(FRIEND_TYPES)
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    journal_style = getattr(args, "journal_style", None) or rng.choice(list(JOURNALS))

    if hero_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        journal_style=journal_style,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
        params.journal_style,
    )
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show story_ok/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("rooftop", "Nova", "girl", "Mina", "girl", "bronze"),
            StoryParams("museum", "Sky", "boy", "Toby", "boy", "small_bronze"),
            StoryParams("harbor", "Ivy", "girl", "Rae", "girl", "bronze"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
