#!/usr/bin/env python3
"""
A small mythic story world about a sheriff manatee, a wretched misunderstanding,
and a suspenseful conflict that ends in a truthful peace.

The seed tale behind this world:
---
In a moonlit bay, Sheriff Manatee guarded the pearl bridge and the singing reeds.
One night, the silver tide went still, and a wretched rumor spread that the sheriff
had hidden the village bell. The old otter clerk thought the manatee was sly; the
sheriff thought the clerk had accused them on purpose. Suspense grew under the stars
while both sides held their breath.

Then a lantern drifted up from the deep garden, where the bell had snagged on a root.
The clerk apologized. The sheriff rolled the bell back to the square, and the bay
breathed easy again.
---
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clerk: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "dame"}
        male = {"boy", "man", "father", "king", "sheriff"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
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


def _clean_join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _titleize(name: str) -> str:
    return name[:1].upper() + name[1:]


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    clerk_name: str
    relic: str
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
    "moon_bay": "the moon bay",
    "reed_square": "the reed square",
    "deep_garden": "the deep garden",
    "tide_bridge": "the pearl bridge",
}

RELICS = {
    "bell": {
        "label": "village bell",
        "phrase": "an old village bell",
        "place": "deep_garden",
    },
    "key": {
        "label": "latch key",
        "phrase": "a bright latch key",
        "place": "tide_bridge",
    },
    "lantern": {
        "label": "golden lantern",
        "phrase": "a little golden lantern",
        "place": "reed_square",
    },
}

NAMES = ["Mira", "Talon", "Nia", "Orin", "Luma", "Kest", "Rowan", "Ari", "Sable", "Cleo"]
CLERKS = ["Otis", "Brin", "Pip", "Moss", "Lark", "Wren", "Tavi", "Edda"]

TRAITS = ["watchful", "gentle", "brave", "curious", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic sheriff-manatee story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--clerk")
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


def _story_theme() -> str:
    return "Conflict, Misunderstanding, Suspense"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for relic in RELICS:
            if RECLIC_OK := True:
                out.append((place, relic))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "relic", None) is None or c[1] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, relic = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    clerk_name = getattr(args, "clerk", None) or rng.choice(CLERKS)
    return StoryParams(place=place, hero_name=hero_name, clerk_name=clerk_name, relic=relic)


def _introduce(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.setting}, Sheriff {hero.id} was a {hero.traits[0]} manatee, "
        f"trusted by fish, reeds, and moonlit tide."
    )


def _setup(world: World, hero: Entity, clerk: Entity, relic: Entity) -> None:
    world.say(
        f"{hero.id} kept watch over the bay, where the {relic.label} was said to bless the water."
    )
    world.say(
        f"Each dusk, {clerk.id} the clerk counted the bells and lanterns, "
        f"and the little town slept a bit more safely."
    )


def _misunderstanding(world: World, hero: Entity, clerk: Entity, relic: Entity) -> None:
    hero.memes["duty"] += 1
    clerk.memes["worry"] += 1
    world.say(
        f"One night, the {relic.label} was gone from its hook, and a wretched hush fell over the square."
    )
    world.say(
        f"{clerk.id} thought Sheriff {hero.id} had hidden it, and {hero.id} thought {clerk.id} had blamed them on purpose."
    )
    hero.memes["hurt"] += 1
    clerk.memes["suspicion"] += 1
    world.say(
        f"Neither wanted a quarrel, yet the words between them grew sharp, like shells in a net."
    )


def _suspense(world: World, hero: Entity, clerk: Entity, relic: Entity) -> None:
    hero.memes["suspense"] += 1
    clerk.memes["suspense"] += 1
    world.say(
        f"The tide held still. Lanterns trembled. Even the gulls flew quiet, as if the bay itself were listening."
    )
    world.say(
        f"Sheriff {hero.id} dove through the dark water, while {clerk.id} waited on the shore, heart thudding like a drum."
    )


def _resolution(world: World, hero: Entity, clerk: Entity, relic: Entity) -> None:
    world.say(
        f"At last, a lantern glimmered in the deep garden, where the {relic.label} had snagged on a root."
    )
    world.say(
        f"{clerk.id} saw the truth and bowed their head. \"I was wrong,\" they said, and the wretched rumor broke like foam."
    )
    hero.memes["joy"] += 1
    hero.memes["hurt"] = 0
    clerk.memes["suspicion"] = 0
    world.say(
        f"Sheriff {hero.id} carried the {relic.label} back to the square, and the moonlit bay breathed easy again."
    )
    world.say(
        f"By dawn, the reeds sang softly, and the town remembered that even a deep misunderstanding can be mended by a true look."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="sheriff",
        label="sheriff manatee",
        traits=["watchful", "gentle"],
        meters={"duty": 1.0},
        memes={"duty": 1.0},
    ))
    clerk = world.add(Entity(
        id=params.clerk_name,
        kind="character",
        type="manatee",
        label="clerk manatee",
        traits=["careful"],
        meters={},
        memes={},
    ))
    relic_data = _safe_lookup(RELICS, params.relic)
    relic = world.add(Entity(
        id="relic",
        type="thing",
        label=relic_data["label"],
        phrase=relic_data["phrase"],
        owner=hero.id,
        meters={"missing": 1.0},
        memes={},
    ))

    _introduce(world, hero)
    _setup(world, hero, clerk, relic)
    world.para()
    _misunderstanding(world, hero, clerk, relic)
    world.para()
    _suspense(world, hero, clerk, relic)
    world.para()
    _resolution(world, hero, clerk, relic)

    world.facts.update(
        hero=hero,
        clerk=clerk,
        relic=relic,
        params=params,
        theme=_story_theme(),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clerk: Entity = _safe_fact(world, f, "clerk")
    relic: Entity = _safe_fact(world, f, "relic")
    return [
        f'Write a short myth for a child about Sheriff {hero.id}, a manatee, and a wretched misunderstanding in {world.setting}.',
        f"Tell a suspenseful story where {clerk.id} suspects Sheriff {hero.id} about the {relic.label}, but the truth is gentler.",
        f'Write a myth-like tale with conflict, misunderstanding, and suspense that ends with the {relic.label} returned to the square.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clerk: Entity = _safe_fact(world, f, "clerk")
    relic: Entity = _safe_fact(world, f, "relic")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about Sheriff {hero.id}, a watchful manatee who kept watch over {world.setting}.",
        ),
        QAItem(
            question=f"What did the clerk think happened to the {relic.label}?",
            answer=f"{clerk.id} thought Sheriff {hero.id} had hidden the {relic.label}, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"What caused the suspense in the story?",
            answer=f"The suspense came from the missing {relic.label}, the quiet tide, and the fear that the truth might stay hidden.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended when the {relic.label} was found in the deep garden and Sheriff {hero.id} brought it back to the square.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sheriff?",
            answer="A sheriff is a person who helps keep a place safe and makes sure rules are followed.",
        ),
        QAItem(
            question="What is a manatee?",
            answer="A manatee is a large, gentle sea mammal that swims slowly through warm water.",
        ),
        QAItem(
            question="What does wretched mean?",
            answer="Wretched means very bad, miserable, or full of unhappy feeling.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when people think the wrong thing about each other or about what happened.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the nervous feeling that comes when you are waiting to find out what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==",]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Relic) :- setting(Place), relic(Relic).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="moon_bay", hero_name="Mira", clerk_name="Otis", relic="bell"),
    StoryParams(place="reed_square", hero_name="Luma", clerk_name="Brin", relic="lantern"),
    StoryParams(place="deep_garden", hero_name="Ari", clerk_name="Pip", relic="key"),
]


def explain_rejection() -> str:
    return "(No story: this world accepts any of the listed mythic places and relics.)"


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, relic in combos:
            print(f"  {place:12} {relic}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
