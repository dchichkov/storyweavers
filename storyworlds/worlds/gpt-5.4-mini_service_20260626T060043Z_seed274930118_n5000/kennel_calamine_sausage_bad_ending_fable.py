#!/usr/bin/env python3
"""
storyworlds/worlds/kennel_calamine_sausage_bad_ending_fable.py
==============================================================

A small fable-style storyworld about a kennel, calamine, and sausage,
with a deliberately bad ending.

Premise:
- A little dog in a kennel gets itchy.
- A helper brings calamine lotion.
- A sausage tempts the dog at the wrong time.
- The dog makes a bad choice, and the ending turns out poorly.

The world is built as a stateful simulation with meters and memes:
physical state tracks itch, smear, hunger, and spoilage;
emotional state tracks trust, worry, greed, and relief.

The story is written as a fable: simple, concrete, and with a moral edge.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog", "hound", "puppy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    indoors: bool = False
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
    hero: str
    helper: str
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


SETTINGS = {
    "kennel": Setting(place="the kennel", indoors=True),
    "yard": Setting(place="the yard", indoors=False),
}

HEROES = {
    "dog": {"type": "dog", "label": "little dog", "phrase": "a little brown dog"},
    "puppy": {"type": "puppy", "label": "small puppy", "phrase": "a small white puppy"},
}

HELPERS = {
    "keeper": {"type": "woman", "label": "kennel keeper", "phrase": "the kennel keeper"},
    "child": {"type": "boy", "label": "kind child", "phrase": "a kind child"},
}

# Small registry of objects in the fable.
OBJECTS = {
    "calamine": {
        "type": "lotion",
        "label": "calamine",
        "phrase": "a bottle of calamine lotion",
    },
    "sausage": {
        "type": "food",
        "label": "sausage",
        "phrase": "a sizzling sausage",
    },
}

GREETINGS = ["calm", "gentle", "patient", "kind"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def n(name: str) -> str:
    return name


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero_info = _safe_lookup(HEROES, params.hero)
    helper_info = _safe_lookup(HELPERS, params.helper)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_info["type"],
            label=hero_info["label"],
            phrase=hero_info["phrase"],
            location=setting.place,
            meters={"itch": 0.0, "hunger": 0.0, "smear": 0.0, "sadness": 0.0},
            memes={"trust": 0.0, "worry": 0.0, "greed": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_info["type"],
            label=helper_info["label"],
            phrase=helper_info["phrase"],
            location=setting.place,
            meters={"kindness": 1.0, "worry": 0.0},
            memes={"care": 1.0},
        )
    )
    calamine = world.add(
        Entity(
            id="calamine",
            kind="thing",
            type="lotion",
            label="calamine",
            phrase="a bottle of calamine lotion",
            owner=helper.id,
            location=setting.place,
            meters={"coolness": 1.0},
        )
    )
    sausage = world.add(
        Entity(
            id="sausage",
            kind="thing",
            type="food",
            label="sausage",
            phrase="a sizzling sausage",
            location=setting.place,
            meters={"smell": 1.0, "temptation": 1.0},
        )
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        calamine=calamine,
        sausage=sausage,
        params=params,
    )
    return world


def itch_rule(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["itch"] < THRESHOLD:
        return []
    sig = ("itch",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return [f"{hero.label} scratched at {hero.pronoun('possessive')} side and looked miserable."]


def smear_rule(world: World) -> list[str]:
    hero = world.get("hero")
    calamine = world.get("calamine")
    if hero.meters["itch"] < THRESHOLD:
        return []
    if calamine.meters.get("applied", 0.0) < THRESHOLD:
        return []
    sig = ("smear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    calamine.meters["used"] = 1.0
    return [f"The white lotion left a pale smear on {hero.pronoun('possessive')} fur."]


def hunger_rule(world: World) -> list[str]:
    hero = world.get("hero")
    sausage = world.get("sausage")
    if sausage.location != world.setting.place:
        return []
    if hero.meters["hunger"] < THRESHOLD:
        return []
    sig = ("hunger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["greed"] += 1
    return [f"The smell of sausage made {hero.label} forget what was wise."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (itch_rule, smear_rule, hunger_rule):
            new = rule(world)
            if new:
                changed = True
                out.extend(new)
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def predict_choice(world: World) -> dict[str, bool]:
    sim = world.copy()
    hero = sim.get("hero")
    calamine = sim.get("calamine")
    sausage = sim.get("sausage")
    hero.meters["itch"] += 1
    hero.meters["hunger"] += 1
    calamine.meters["applied"] = 1.0
    propagate(sim, narrate=False)
    bad = sausage.location == sim.setting.place and hero.memes["greed"] >= THRESHOLD
    return {"bad": bad}


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    calamine = world.get("calamine")
    sausage = world.get("sausage")

    world.say(
        f"Once, in {world.setting.place}, there lived {hero.phrase} and {helper.phrase}."
    )
    world.say(
        f"The {hero.type} was small and sweet, and {helper.label} was {random.choice(GREETINGS)}."
    )
    world.say(
        f"One day, {hero.label} got itchy, and {helper.label} brought {calamine.phrase}."
    )
    hero.meters["itch"] += 1
    helper.memes["care"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Just then, {sausage.phrase} was left near the kennel, and its rich smell drifted in."
    )
    hero.meters["hunger"] += 1
    if predict_choice(world)["bad"]:
        hero.memes["greed"] += 1
    propagate(world)

    world.say(
        f"{hero.label} looked from the lotion to the sausage and chose the shiny smell."
    )
    hero.meters["itch"] += 1
    hero.meters["hunger"] += 1
    hero.meters["sadness"] += 1
    helper.memes["worry"] += 1

    # Bad ending: the dog ignores the care, spills the remedy, and loses the treat.
    calamine.meters["applied"] = 1.0
    calamine.meters["spilled"] = 1.0
    sausage.meters["lost"] = 1.0
    hero.memes["trust"] = max(0.0, hero.memes["trust"] - 1.0)
    world.para()
    world.say(
        f"{hero.label} knocked over the calamine, and the cool lotion ran into the straw."
    )
    world.say(
        f"The sausage was snatched away by the wind of the bad choice, and no one got comforted."
    )
    world.say(
        f"So the kennel grew quiet, {hero.label} stayed itchy, and {helper.label} sighed."
    )
    world.say(
        "The fable ends badly: greedy paws may follow the smell, but they do not keep a friend."
    )

    world.facts.update(
        ending="bad",
        choice="sausage",
        lesson="greed leads to loss",
        harmed="calamine",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")  # type: ignore[assignment]
    return [
        f"Write a short fable about a {hero.type} in a kennel, calamine lotion, and a sausage.",
        f"Tell a child-friendly story where {hero.label} is itchy, {helper.label} offers calamine, and the sausage causes trouble.",
        "Write a fable with a bad ending about choosing a tempting snack over good care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")  # type: ignore[assignment]
    calamine: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "calamine")  # type: ignore[assignment]
    sausage: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sausage")  # type: ignore[assignment]
    return [
        QAItem(
            question="Who lived in the kennel?",
            answer=f"{hero.label} lived in the kennel, and {helper.label} was there to help.",
        ),
        QAItem(
            question="What did the helper bring for the itch?",
            answer=f"{helper.label} brought {calamine.phrase} to help with the itch.",
        ),
        QAItem(
            question="What tempted the dog away from the lotion?",
            answer=f"The smell of {sausage.phrase} tempted {hero.label} away from the lotion.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended badly: the calamine spilled, the sausage was lost, and {hero.label} stayed itchy."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kennel?",
            answer="A kennel is a place where a dog can stay and rest safely.",
        ),
        QAItem(
            question="What is calamine lotion used for?",
            answer="Calamine lotion is used to soothe itchy skin.",
        ),
        QAItem(
            question="What is a sausage?",
            answer="A sausage is a kind of food made from seasoned meat.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_exists :- hero.
bad_ending :- hero_exists, sausage, calamine.

spilled(calamine) :- bad_ending.
lost(sausage) :- bad_ending.
itchy(hero) :- bad_ending.

#show bad_ending/0.
#show spilled/1.
#show lost/1.
#show itchy/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("hero"),
        asp.fact("sausage"),
        asp.fact("calamine"),
        asp.fact("kennel"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show bad_ending/0."))
    symbols = set((s.name, len(s.arguments)) for s in model)
    ok = ("bad_ending", 0) in symbols
    if ok:
        print("OK: ASP twin produces the bad ending.")
        return 0
    print("Mismatch: ASP twin did not produce the expected result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small kennel fable with calamine and sausage.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    if place != "kennel" and hero == "puppy" and helper == "child":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, helper=helper, seed=getattr(args, "seed", None))


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
    StoryParams(place="kennel", hero="dog", helper="keeper"),
    StoryParams(place="kennel", hero="puppy", helper="keeper"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_ending/0.\n#show spilled/1.\n#show lost/1.\n#show itchy/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show bad_ending/0.\n#show spilled/1.\n#show lost/1.\n#show itchy/1."))
        print(" ".join(str(s) for s in model))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
