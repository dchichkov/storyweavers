#!/usr/bin/env python3
"""
A small pirate-tale story world with a moral-value turn, rhyme, and dialogue.

Seed tale:
A desperate little deckhand on a tiny ship wanted to manipulate the ship's cow
into mooing on command so the captain would notice. The trick backfired, the crew
laughed in rhyme, and the deckhand learned that honest words and a kind ask
worked better than a sneaky plan.

This world models:
- physical meters: risk, chaos, treasure-safety, cow-comfort
- emotional memes: desperation, guilt, pride, trust, cheer
- a state-driven turn from sneaky manipulation to honest dialogue
- a moral-value ending that proves what changed
- a pirate-tale voice with a bit of rhyme in the resolution
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

MORAL_VALUES = ["honesty", "kindness", "patience", "fairness", "courage"]
LOCATIONS = ["the deck", "the galley", "the moonlit dock", "the crow's nest", "the bilge hatch"]
NAMES = ["Mira", "Jory", "Pip", "Nell", "Rafi", "Bree", "Tamsin", "Oren"]
CAPTAINS = ["Captain Salt", "Captain Brine", "Captain Peg", "Captain Wave"]
CREW_NAMES = ["Bosun Blue", "Matey Reed", "Old Sly", "Scarlet Finn"]



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    cow: object | None = None
    crew: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
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
    place: str
    night: bool = False
    tide: str = "calm"
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
class Charm:
    label: str
    phrase: str
    moral_value: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    captain: str
    crew: str
    charm: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(copy.deepcopy(self.setting))
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def asp_facts() -> str:
    import asp
    lines = []
    for loc in SETTINGS:
        lines.append(asp.fact("place", loc))
    for key, c in CHARMS.items():
        lines.append(asp.fact("charm", key))
        lines.append(asp.fact("value_of", key, c.moral_value))
    return "\n".join(lines)


ASP_RULES = r"""
good_story(P) :- place(P), charm(C), value_of(C, honesty).
#show good_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(charm: Charm) -> bool:
    return charm.moral_value in MORAL_VALUES


def _sneaky_attempt(world: World, hero: Entity, cow: Entity) -> None:
    hero.memes["desperation"] += 1
    hero.memes["pride"] += 1
    hero.memes["guilt"] += 1
    cow.memes["unease"] += 1
    world.facts["attempted_manipulation"] = True
    world.say(
        f"{hero.id} was desperate enough to try to manipulate the ship's cow. "
        f"{hero.pronoun().capitalize()} whispered a false promise and hoped for a loud moo."
    )
    world.say(
        f"But the cow only blinked, tugged a rope with {cow.pronoun('possessive')} nose, "
        f"and made the whole deck wobble like a sleepy boot."
    )
    world.say(
        f"The crew stared as if the sea itself had gone silent."
    )


def _crew_reacts(world: World, captain: Entity, crew: Entity, hero: Entity) -> None:
    hero.memes["shame"] += 1
    captain.memes["sternness"] += 1
    crew.memes["amused"] += 1
    world.say(
        f"Captain {captain.label} folded {captain.pronoun('possessive')} arms and said, "
        f'"A sneaky trick never sails straight, matey."'
    )
    world.say(
        f"{crew.label} snorted, then chuckled, and a little rhyme bobbed up on the wind: "
        f'"If you try to fool a cow, the truth will show you how."'
    )


def _honest_turn(world: World, hero: Entity, captain: Entity, cow: Entity, charm: Charm) -> None:
    hero.memes["desperation"] = max(0.0, hero.memes["desperation"] - 1)
    hero.memes["trust"] += 1
    hero.memes["guilt"] = max(0.0, hero.memes["guilt"] - 1)
    cow.memes["comfort"] += 1
    world.say(
        f"{hero.id} swallowed hard, looked at the deck, and chose honesty over a trick."
    )
    world.say(
        f'"Captain {captain.label}," {hero.pronoun()} said, "I wanted attention, but I tried to manipulate the cow."'
    )
    world.say(
        f'"I should have asked true and fair."'
    )
    world.say(
        f"Then {hero.id} knelt by the cow and asked kindly for a playful moo."
    )
    world.say(
        f"The cow answered with a bright, proud moo that rolled over the planks like a friendly drum."
    )
    world.say(
        f"That honest ask fit {charm.phrase}, and even the salt air seemed to smile."
    )


def _resolution(world: World, hero: Entity, captain: Entity, cow: Entity, charm: Charm) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    captain.memes["warmth"] += 1
    cow.memes["comfort"] += 1
    world.facts["resolved"] = True
    world.facts["moral_value"] = charm.moral_value
    world.say(
        f"In the end, the crew laughed kindly instead of scolding hard, and the ship felt lighter."
    )
    world.say(
        f"{hero.id} stood tall beside the cow, no longer desperate, because honesty had brought the better sound."
    )
    world.say(
        f"And so the little pirate tale ended with a clean deck, a calm heart, and a cow that could moo without a trick."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label=params.captain))
    crew = world.add(Entity(id="Crew", kind="character", type="crew", label=params.crew))
    cow = world.add(Entity(id="Cow", kind="character", type="cow", label="ship's cow"))

    charm = _safe_lookup(CHARMS, params.charm)
    world.facts.update(hero=hero, captain=captain, crew=crew, cow=cow, charm=charm, setting=setting)

    world.say(
        f"On {setting.place}, where the tide was {setting.tide} and the lanterns swayed, "
        f"{hero.id} was a small pirate with a desperate spark in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{hero.id} wanted the captain to notice {hero.pronoun('object')}, so {hero.pronoun()} thought to manipulate the ship's cow into mooing on command."
    )
    world.say(
        f"The charm of the day was {charm.phrase}, though {hero.id} had not yet learned how to live it."
    )

    world.para()
    _sneaky_attempt(world, hero, cow)
    _crew_reacts(world, captain, crew, hero)

    world.para()
    _honest_turn(world, hero, captain, cow, charm)
    _resolution(world, hero, captain, cow, charm)

    return world


SETTINGS = {
    "deck": Setting(place="the deck", night=True, tide="restless"),
    "galley": Setting(place="the galley", night=False, tide="calm"),
    "dock": Setting(place="the moonlit dock", night=True, tide="gentle"),
    "crow": Setting(place="the crow's nest", night=False, tide="blustery"),
    "bilge": Setting(place="the bilge hatch", night=True, tide="sloshy"),
}

CHARMS = {
    "honesty": Charm(label="honesty charm", phrase="a shine of honest words", moral_value="honesty"),
    "kindness": Charm(label="kindness charm", phrase="a soft and kind reply", moral_value="kindness"),
    "patience": Charm(label="patience charm", phrase="a slow and steady waiting spell", moral_value="patience"),
    "fairness": Charm(label="fairness charm", phrase="a fair turn for every matey", moral_value="fairness"),
    "courage": Charm(label="courage charm", phrase="a brave heart that did not hide", moral_value="courage"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with moral value, rhyme, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--crew", choices=CREW_NAMES)
    ap.add_argument("--charm", choices=CHARMS)
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
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAINS)
    crew = getattr(args, "crew", None) or rng.choice(CREW_NAMES)
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))
    if not reasonableness_gate(_safe_lookup(CHARMS, charm)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, hero_type=hero_type, captain=captain, crew=crew, charm=charm)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a pirate tale where a desperate child tries to manipulate a cow, but learns {_safe_lookup(CHARMS, params.charm).moral_value}.",
            f"Tell a short story with dialogue and rhyme about {params.hero} on {_safe_lookup(SETTINGS, params.place).place}.",
            f"Make a child-friendly pirate story where a sneaky plan turns into an honest talk and a happy moo.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    cow = f["cow"]
    charm: Charm = f["charm"]
    return [
        QAItem(
            question=f"Why was {hero.id} acting so sneaky at first?",
            answer=f"{hero.id} felt desperate and wanted attention, so {hero.pronoun()} tried to manipulate the ship's cow instead of asking honestly.",
        ),
        QAItem(
            question=f"What did Captain {captain.label} say about the trick?",
            answer=f"Captain {captain.label} warned that a sneaky trick never sails straight and told {hero.id} to choose a truer way.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} told the truth, asked kindly, and the cow gave a bright moo without needing a trick.",
        ),
        QAItem(
            question=f"What moral value did the story teach?",
            answer=f"The story taught {charm.moral_value}. Honest words worked better than manipulation, and that made the ending happy.",
        ),
        QAItem(
            question=f"What sound did the cow make at the end?",
            answer=f"The cow made a bright, proud moo that rolled over the planks like a friendly drum.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate captain?",
            answer="A pirate captain is the leader of the ship, the one who gives orders and keeps the crew together.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and not trying to trick others with lies or sneaky plans.",
        ),
        QAItem(
            question="Why can a cow moo?",
            answer="A cow moo is the sound a cow makes to speak, call, or answer in its own way.",
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show good_story/1.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "good_story")
    if ("deck",) in atoms or ("galley",) in atoms or ("dock",) in atoms or ("crow",) in atoms or ("bilge",) in atoms:
        print("OK: ASP program produces a good_story atom.")
        return 0
    print("ASP verification failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(sorted(set(asp.atoms(model, "good_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in [StoryParams(place=k, hero=_safe_lookup(NAMES, i % len(NAMES)), hero_type=["girl", "boy"][i % 2], captain=_safe_lookup(CAPTAINS, i % len(CAPTAINS)), crew=_safe_lookup(CREW_NAMES, i % len(CREW_NAMES)), charm=k) for i, k in enumerate(CHARMS)]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
