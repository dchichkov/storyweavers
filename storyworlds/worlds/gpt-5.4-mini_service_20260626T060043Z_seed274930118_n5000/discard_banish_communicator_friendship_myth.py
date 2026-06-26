#!/usr/bin/env python3
"""
storyworlds/worlds/discard_banish_communicator_friendship_myth.py
=================================================================

A small myth-style story world about friendship, a troublesome communicator,
and the choice to discard or banish it.

Premise:
- Two friends share a sacred place.
- A communicator spreads a misleading message.
- Friendship is strained, then repaired when the harmful tool is discarded
  and banished.

The world is built to read like a short myth: concrete, gentle, and causal.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    communicator: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "king", "father", "brother", "warrior"}
        female = {"girl", "woman", "queen", "mother", "sister", "priestess"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    title: str
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
class Communicator:
    id: str
    label: str
    phrase: str
    kind: str
    rumor: str
    harmful: bool
    setting_tags: set[str] = field(default_factory=set)
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
    setting: str
    communicator: str
    hero: str
    friend: str
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
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "grove": Setting(place="the grove", title="the green grove", affords={"listen", "gather"}),
    "shore": Setting(place="the shore", title="the bright shore", affords={"listen", "gather"}),
    "temple": Setting(place="the temple steps", title="the temple steps", affords={"listen", "gather"}),
}

COMMUNICATORS = {
    "shell": Communicator(
        id="shell",
        label="whisper shell",
        phrase="a whisper shell that carried voices across the water",
        kind="shell",
        rumor="that one friend would leave and never return",
        harmful=True,
        setting_tags={"shore"},
    ),
    "drum": Communicator(
        id="drum",
        label="bronze drum",
        phrase="a bronze drum that could send a message through the whole hill",
        kind="drum",
        rumor="that the harvest would fail unless the friends stopped meeting",
        harmful=True,
        setting_tags={"grove", "temple"},
    ),
    "bell": Communicator(
        id="bell",
        label="small bell",
        phrase="a small bell that rang from one doorway to the next",
        kind="bell",
        rumor="that the moon itself was calling for silence",
        harmful=True,
        setting_tags={"temple", "grove"},
    ),
}

HEROES = {
    "Asha": "girl",
    "Korin": "boy",
    "Mira": "girl",
    "Taro": "boy",
}

FRIENDS = {
    "Lina": "girl",
    "Nilo": "boy",
    "Sera": "girl",
    "Pavo": "boy",
}


def _make_entity(name: str, typ: str, kind: str = "character") -> Entity:
    return Entity(id=name, kind=kind, type=typ, label=name)


def validate_combo(setting: Setting, comm: Communicator) -> bool:
    return bool(setting.affords) and setting.title.split() and bool(comm.setting_tags & set(setting.affords) or comm.setting_tags == {"shore", "grove", "temple"})


def explain_rejection(setting: Setting, comm: Communicator) -> str:
    return (
        f"(No story: the {comm.label} does not fit this setting well enough for a "
        f"mythic warning. Choose a setting where the communicator can actually be heard.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic friendship storyworld with discard and banish.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--communicator", choices=sorted(COMMUNICATORS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    communicator = getattr(args, "communicator", None) or rng.choice(list(COMMUNICATORS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIENDS if n != hero])
    if hero == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    st = _safe_lookup(SETTINGS, setting)
    cm = _safe_lookup(COMMUNICATORS, communicator)
    if not validate_combo(st, cm):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, communicator=communicator, hero=hero, friend=friend)


def story_setup(world: World, hero: Entity, friend: Entity, comm: Communicator) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"In {world.setting.title}, {hero.id} and {friend.id} were bound by a gentle friendship."
    )
    world.say(
        f"Together they kept {comm.phrase} near their hands, because the old place loved every voice."
    )


def communicator_turn(world: World, hero: Entity, friend: Entity, comm: Communicator) -> None:
    hero.memes["doubt"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"One dusk, the {comm.label} carried a cruel rumor: {comm.rumor}."
    )
    world.say(
        f"{hero.id} went quiet, and {friend.id} looked away, as if the words had turned to ash between them."
    )


def discard_communicator(world: World, hero: Entity, comm: Communicator) -> None:
    if not comm.harmful:
        pass
    world.say(
        f"{hero.id} understood that the {comm.label} was feeding the hurt, so {hero.pronoun('subject')} chose to discard it."
    )
    world.facts["discarded"] = True


def banish_communicator(world: World, friend: Entity, comm: Communicator) -> None:
    friend.memes["resolve"] += 1
    world.say(
        f"Then {friend.id} carried the broken {comm.label} beyond the mossy stones and banish it from the friendship's path."
    )
    world.say(
        f"They laid it far from the hearth, where no gentle ear would mistake it for truth."
    )
    world.facts["banished"] = True


def repair_friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["doubt"] = 0.0
    friend.memes["fear"] = 0.0
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"With the false voice gone, {hero.id} spoke plainly, and {friend.id} answered with an open smile."
    )
    world.say(
        f"Their friendship returned stronger than before, like river water clearing after a storm."
    )


def tell(setting: Setting, comm: Communicator, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero_type = _safe_lookup(HEROES, hero_name)
    friend_type = _safe_lookup(FRIENDS, friend_name)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    communicator = world.add(Entity(
        id=comm.id,
        kind="thing",
        type=comm.kind,
        label=comm.label,
        phrase=comm.phrase,
        owner=hero.id,
        place=setting.place,
    ))

    story_setup(world, hero, friend, comm)
    world.para()
    communicator_turn(world, hero, friend, comm)
    world.para()
    discard_communicator(world, hero, comm)
    banish_communicator(world, friend, comm)
    repair_friendship(world, hero, friend)
    world.facts.update(
        hero=hero,
        friend=friend,
        communicator=communicator,
        setting=setting,
        comm_def=comm,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    comm = _safe_fact(world, f, "comm_def")
    return [
        f'Write a short myth about {hero.id} and {friend.id}, a broken {comm.label}, and a friendship that is tested then healed.',
        f"Tell a gentle legendary story where {comm.phrase} causes trouble and the friends choose to discard and banish it.",
        f'Write a child-friendly myth that includes the words "discard" and "banish" and ends with friendship restored.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    comm = _safe_fact(world, f, "comm_def")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {hero.id} and {friend.id}, who share a friendship in {setting.title}.",
        ),
        QAItem(
            question=f"What trouble did the {comm.label} bring?",
            answer=f"It carried a harmful rumor that made the friends worry and feel distant from each other.",
        ),
        QAItem(
            question=f"What did they do with the communicator at the end?",
            answer=f"They chose to discard it and then banish it far from the path of their friendship.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the friends speaking honestly again and their friendship becoming strong and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to discard something?",
            answer="To discard something means to throw it away or choose not to keep using it.",
        ),
        QAItem(
            question="What does it mean to banish something?",
            answer="To banish something means to send it away and not let it stay near the people or place it would trouble.",
        ),
        QAItem(
            question="What is a communicator?",
            answer="A communicator is something that carries a message or voice from one place or person to another.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind and trusting bond between people who care about each other.",
        ),
    ]


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
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="grove", communicator="drum", hero="Asha", friend="Lina"),
    StoryParams(setting="shore", communicator="shell", hero="Korin", friend="Sera"),
    StoryParams(setting="temple", communicator="bell", hero="Mira", friend="Pavo"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
communicator(C) :- communicator_fact(C).

compatible(S, C) :- setting_fact(S), communicator_fact(C), allowed(S, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in COMMUNICATORS.items():
        lines.append(asp.fact("communicator_fact", cid))
        if c.harmful:
            lines.append(asp.fact("harmful", cid))
        for tag in sorted(c.setting_tags):
            lines.append(asp.fact("allowed", tag, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in COMMUNICATORS.items():
            if c.setting_tags & {sid}:
                combos.append((sid, cid))
    return sorted(combos)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(COMMUNICATORS, params.communicator), params.hero, params.friend)
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


def explain_all_invalid(setting: Setting, comm: Communicator) -> str:
    return (
        f"(No story: the {comm.label} is not a reasonable fit for {setting.title} in this myth.)"
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/communicator pairs:\n")
        for s, c in combos:
            print(f"  {s:7} {c}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.friend} at {p.setting} with {p.communicator}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
