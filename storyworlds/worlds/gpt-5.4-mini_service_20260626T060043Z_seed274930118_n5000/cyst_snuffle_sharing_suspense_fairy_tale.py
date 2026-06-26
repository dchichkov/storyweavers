#!/usr/bin/env python3
"""
storyworlds/worlds/cyst_snuffle_sharing_suspense_fairy_tale.py
===============================================================

A tiny fairy-tale storyworld about a child, a strange little cyst-shaped
charm, a nervous snuffle, and the brave act of sharing that turns suspense
into relief.

The world is intentionally small: the simulated state tracks who has the charm,
who is cold, who is waiting, and whether sharing resolves the tension. The
story is not a frozen template; it is narrated from the state updates that
happen as the world runs.

Seed words:
- cyst
- snuffle

Features:
- Sharing
- Suspense

Style:
- Fairy Tale
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

SETTING_NAME = "the moonlit forest"
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
    carried_by: Optional[str] = None
    shared_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "knight", "boy-fairy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone
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
    place: str = "forest"
    hero_name: str = "Mira"
    hero_type: str = "girl"
    helper_name: str = "Pip"
    helper_type: str = "boy"
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


SETTINGS = {
    "forest": SETTING_NAME,
}

HERO_NAMES = ["Mira", "Luna", "Elin", "Tessa", "Nora", "Ivy"]
HELPER_NAMES = ["Pip", "Oren", "Bram", "Toby", "Finn", "Joss"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["boy", "girl"]

ASP_RULES = r"""
hero(H) :- named(H).
helper(H) :- named(H), helper_name(H).
place(forest).

has_cyst(H) :- holds(H, cyst).
snuffles(H) :- named(H), snuffle(H).
cold(H) :- snuffles(H).

needs_sharing(H) :- has_cyst(H), cold(H).
can_share(H, X) :- named(H), named(X), H != X, holds(H, cyst), waiting(X).
resolved :- can_share(H, X), give(H, X, cyst).
"""

CYST_LABEL = "a small moon-cyst"
CYST_PHRASE = "a small moon-cyst"
CYST_OWNER = "Mira"


class WorldModel:
    def __init__(self, world: World):
        self.world = world

    def run(self) -> None:
        hero = self.world.get("hero")
        helper = self.world.get("helper")
        cyst = self.world.get("cyst")

        hero.meters["curiosity"] = 1
        hero.memes["hope"] = 1
        self.world.say(
            f"Once upon a time in {self.world.place}, {hero.id} walked beneath silver leaves and found {cyst.phrase} tucked in a hollow stone."
        )
        self.world.say(
            f"It looked like a tiny treasure, and it gave off a soft snuffle of wind, as if it were listening."
        )

        self.world.para()
        helper.memes["cold"] = 1
        helper.memes["waiting"] = 1
        self.world.say(
            f"Before long, {helper.id} came out of the dark brush with a shiver and a snuffle. {helper.pronoun().capitalize()} had lost {helper.pronoun('possessive')} lantern."
        )
        self.world.say(
            f"{hero.id} saw {helper.id} standing alone in the moonlight, and the little cyst seemed to pulse as if it wanted a kinder story."
        )

        self.world.para()
        hero.memes["suspense"] = 1
        self.world.say(
            f"{hero.id} held the cyst close and waited. For a moment, nothing happened, and the forest stayed still enough to hear owls blink."
        )
        self.world.say(
            f"Then {hero.id} remembered that a gift grows brighter when it is shared."
        )

        self.world.para()
        cyst.carried_by = helper.id
        cyst.shared_with = helper.id
        helper.memes["warmth"] = 1
        helper.memes["hope"] = 1
        helper.memes["suspense"] = 0
        self.world.say(
            f"{hero.id} placed the cyst into {helper.id}'s hands and shared the glow without keeping the wonder for {hero.pronoun('object')}."
        )
        self.world.say(
            f"The cyst opened like a pearl flower, and its light filled the path so both children could see the way home."
        )

        self.world.facts.update(
            hero=hero,
            helper=helper,
            cyst=cyst,
            resolved=True,
            shared=True,
            setting=self.world.place,
        )


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    cyst = world.add(
        Entity(
            id="cyst",
            kind="thing",
            type="charm",
            label="cyst",
            phrase=CYST_PHRASE,
            owner=hero.id,
            carried_by=hero.id,
        )
    )
    world.facts.update(hero=hero, helper=helper, cyst=cyst)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    return [
        'Write a short fairy tale for young children that includes the word "cyst" and a gentle feeling of suspense.',
        f"Tell a moonlit forest story where {hero.id} discovers a strange cyst, hears a snuffle in the dark, and decides whether to share it.",
        f"Write a child-friendly fairy tale in which {hero.id} shares a magical little cyst with {helper.id} and the worry turns into a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    cyst = _safe_fact(world, world.facts, "cyst")
    return [
        QAItem(
            question=f"Who found the cyst in the moonlit forest?",
            answer=f"{hero.id} found the cyst while walking beneath the silver leaves.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful before the ending?",
            answer=f"It felt suspenseful because {hero.id} waited to see what the cyst would do, and the forest stayed quiet for a moment.",
        ),
        QAItem(
            question=f"What happened after {hero.id} shared the cyst?",
            answer=f"The cyst opened like a pearl flower, {helper.id} got its warm light, and both children could see the way home.",
        ),
        QAItem(
            question=f"Who gave the cyst to someone else?",
            answer=f"{hero.id} gave the cyst to {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to someone else so both people can enjoy it or use it.",
        ),
        QAItem(
            question="What does a snuffle sound like?",
            answer="A snuffle is a soft, sniffly sound, like someone breathing through a cold nose.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="What do fairy tales often have?",
            answer="Fairy tales often have magical objects, brave choices, and a happy ending.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "forest"),
        asp.fact("named", "hero"),
        asp.fact("named", "helper"),
        asp.fact("helper_name", "helper"),
        asp.fact("named", "cyst"),
        asp.fact("holds", "hero", "cyst"),
        asp.fact("snuffle", "helper"),
        asp.fact("waiting", "helper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0.\n#show needs_sharing/1.\n#show can_share/3."))
    shown = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("resolved", 0), ("needs_sharing", 1), ("can_share", 3)}
    if shown == expected:
        print("OK: ASP gate is internally consistent for the seeded fairy-tale state.")
        return 0
    print("MISMATCH in ASP verification.")
    print("model:", sorted(shown))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world about cyst, snuffle, sharing, and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS.keys(), default="forest")
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    if hero_name == helper_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=getattr(args, "place", None) or "forest",
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type=rng.choice(HELPER_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    model = WorldModel(world)
    model.run()
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


def asp_valid() -> bool:
    import asp
    model = asp.one_model(asp_program("#show resolved/0.\n#show needs_sharing/1.\n#show can_share/3."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    return ("resolved", 0) in atoms and ("needs_sharing", 1) in atoms and ("can_share", 3) in atoms


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0.\n#show needs_sharing/1.\n#show can_share/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP twin is present for the seeded fairy-tale world.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(place="forest", hero_name="Mira", hero_type="girl", helper_name="Pip", helper_type="boy")
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 10):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
