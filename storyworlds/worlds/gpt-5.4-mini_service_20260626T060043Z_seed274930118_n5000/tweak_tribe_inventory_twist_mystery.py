#!/usr/bin/env python3
"""
storyworlds/worlds/tweak_tribe_inventory_twist_mystery.py
==========================================================

A small mystery-style storyworld about a tribe's shared inventory, one tiny
tweak, and a twist that turns a worry into a harmless explanation.
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
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
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
class Setting:
    place: str
    mood: str = "quiet"
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
    kind: str
    twist_hint: str
    color: str
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
    place: str
    clue: str
    twist: str
    name: str
    role: str
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


SETTINGS = {
    "clearing": Setting(place="the forest clearing", mood="quiet"),
    "hall": Setting(place="the tribe hall", mood="busy"),
    "riverside": Setting(place="the riverside camp", mood="misty"),
}

CLUES = {
    "feather": Clue(id="feather", label="a bright feather", kind="feather", twist_hint="tucked into a basket", color="gold"),
    "shell": Clue(id="shell", label="a smooth shell", kind="shell", twist_hint="used as a drum marker", color="white"),
    "cord": Clue(id="cord", label="a red cord", kind="cord", twist_hint="tied around a bundle", color="red"),
}

TWISTS = {
    "borrowed": "borrowed",
    "moved": "moved",
    "tweaked": "tweaked",
}

NAMES = ["Ari", "Mina", "Toma", "Lena", "Rin", "Sora", "Jai", "Nia"]
ROLES = ["girl", "boy"]

ASP_RULES = r"""
clue(C) :- clue_id(C).
twist(T) :- twist_id(T).
place(P) :- place_id(P).
valid(P,C,T) :- place(P), clue(C), twist(T).
#show valid/3.
"""


@dataclass
class World:
    setting: Setting
    hero: Entity
    elder: Entity
    clue: Entity
    inventory: dict[str, Entity] = field(default_factory=dict)
    story: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.story.append(text)

    def render(self) -> str:
        return " ".join(self.story)
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


def build_inventory(clue: Clue) -> dict[str, Entity]:
    return {
        "lantern": Entity(id="lantern", label="lantern", type="thing", owner="tribe"),
        "basket": Entity(id="basket", label="basket", type="thing", owner="tribe"),
        "drum": Entity(id="drum", label="drum", type="thing", owner="tribe"),
        "clue": Entity(id=clue.id, label=clue.label, type=clue.kind, owner="tribe"),
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for c in CLUES:
            for t in TWISTS:
                combos.append((p, c, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about a tribe inventory and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "twist", None) is None or c[2] == getattr(args, "twist", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, twist = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, clue=clue, twist=twist, name=name, role=role)


def introduce(world: World) -> None:
    world.say(f"{world.hero.label} was a curious little {world.hero.type} who listened closely when the tribe was worried.")
    world.say(f"In {world.setting.place}, the tribe kept a shared inventory of useful things for the day.")


def setup_mystery(world: World) -> None:
    world.hero.memes["curiosity"] = 1
    world.elder.memes["worry"] = 1
    world.say(f"One evening, the tribe checked the inventory and found that the lantern count looked strange.")
    world.say(f"{world.elder.label} frowned at the list. Someone had made a tiny tweak, and now a clue seemed out of place.")


def clue_search(world: World) -> None:
    world.hero.memes["focus"] = 1
    world.say(f"{world.hero.label} looked again at the inventory, then at {world.clue.label}.")
    world.say(f"The {world.clue.label} had a small mark that matched the {world.clue.color} dye on a basket tie.")
    world.facts["clue_hint"] = world.clue.color
    world.facts["twist"] = world.params.twist if hasattr(world, "params") else ""


def twist_reveal(world: World, params: StoryParams) -> None:
    if params.twist == "borrowed":
        world.say("The twist was simple: the lantern was not lost at all. It had been borrowed for a night path and set back carefully inside a basket.")
    elif params.twist == "moved":
        world.say("The twist was gentle: the lantern had been moved to the riverside camp so the youngest children could follow the glow home.")
    else:
        world.say("The twist was small but important: the inventory had been tweaked by an older child who fixed the list after a spill hid the lantern line.")
    world.say(f"{world.hero.label} smiled when the truth appeared. The tribe did not have a thief; it had a tidy reason.")


def resolution(world: World) -> None:
    world.hero.memes["joy"] = 1
    world.elder.memes["worry"] = 0
    world.say(f"By the end, the tribe's inventory was straight again, and the lantern shone where everyone could see it.")
    world.say(f"{world.hero.label} liked the mystery even more because the answer made the camp feel safe.")


def generate_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    clue_cfg = _safe_lookup(CLUES, params.clue)
    hero = Entity(id=params.name, kind="character", label=params.name, type=params.role)
    elder = Entity(id="elder", kind="character", label="the elder", type="woman")
    clue = Entity(id=clue_cfg.id, kind="thing", label=clue_cfg.label, type=clue_cfg.kind)
    world = World(setting=setting, hero=hero, elder=elder, clue=clue, inventory=build_inventory(clue_cfg))
    world.params = params  # non-serialized helper for narration
    return world


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    introduce(world)
    world.say("")
    setup_mystery(world)
    world.say("")
    clue_search(world)
    world.say("")
    twist_reveal(world, params)
    resolution(world)

    prompts = [
        f"Write a gentle mystery story about a tribe, an inventory, and a tiny {params.twist}.",
        f"Tell a child-friendly story where {params.name} notices a clue in the tribe's inventory and learns the truth.",
        f"Write a short mystery with the words tweak, tribe, inventory, and twist.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {params.name} look at the tribe's inventory?",
            answer=f"{params.name} wanted to understand why the lantern count looked wrong and what tiny tweak had changed the list.",
        ),
        QAItem(
            question=f"What clue helped {params.name} solve the mystery?",
            answer=f"The {_safe_lookup(CLUES, params.clue).label} helped because its small mark matched the basket tie and pointed to the answer.",
        ),
        QAItem(
            question="Was there really a thief?",
            answer="No, there was no thief. The story's twist showed that the missing thing had been borrowed, moved, or fixed on the list, depending on the version of the story.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is an inventory?",
            answer="An inventory is a list of the things a group has, so people can tell what is there and what is missing.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
    ]

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )
    return sample


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
    for ent in [world.hero, world.elder, world.clue] + list(world.inventory.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place_id", p))
    for c in CLUES:
        lines.append(asp.fact("clue_id", c))
    for t in TWISTS:
        lines.append(asp.fact("twist_id", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python for {len(py)} combos.")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(place="hall", clue="feather", twist="borrowed", name="Mina", role="girl"),
    StoryParams(place="clearing", clue="shell", twist="moved", name="Ari", role="boy"),
    StoryParams(place="riverside", clue="cord", twist="tweaked", name="Lena", role="girl"),
]


def asp_all() -> None:
    for combo in asp_valid_combos():
        print(combo)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        asp_all()
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.place}, clue={p.clue}, twist={p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
