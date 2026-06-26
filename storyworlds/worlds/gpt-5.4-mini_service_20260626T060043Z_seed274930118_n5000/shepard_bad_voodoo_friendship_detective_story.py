#!/usr/bin/env python3
"""
A small storyworld: a detective-style friendship mystery involving Shepard,
a bad feeling about voodoo, and a careful turn toward trust.

The story model is intentionally simple:
- A child detective notices a strange misunderstanding.
- A friend seems "bad" only because of a rumor about a voodoo charm.
- The detective follows clues, learns the truth, and repairs the friendship.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    d: object | None = None
    f: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def display(self) -> str:
        return self.label or self.id
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
class Place:
    id: str
    label: str
    clues: list[str] = field(default_factory=list)
    affords: set[str] = field(default_factory=set)
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
    detective_name: str
    friend_name: str
    rumor: str
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        clone = World(place=self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
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


SETTINGS = {
    "alley": Place(id="alley", label="the old alley", clues=["muddy shoeprints", "a bent paper tag", "a broken candle"], affords={"search"}),
    "library": Place(id="library", label="the quiet library", clues=["a note tucked in a book", "a whisper by the shelf", "a smudged page"], affords={"search"}),
    "garden": Place(id="garden", label="the garden path", clues=["a ribbon on a gate", "soft footprints", "a hidden key"], affords={"search"}),
}

DETECTIVE_NAMES = ["Shepard", "Mina", "Noah", "Lena", "Tari", "Pip"]
FRIEND_NAMES = ["Ivy", "Rory", "Jun", "Maya", "Benn", "Suri"]
RUMORS = ["bad voodoo", "a bad voodoo charm", "a voodoo trick", "a bad spell"]
TRUTHS = [
    "a friendship token",
    "a lucky charm",
    "a tiny keepsake from home",
    "a practice charm for a school play",
]


ASP_RULES = r"""
% A story is valid when the detective, friend, and setting are all present.
valid_story(P, D, F, R) :- place(P), detective(D), friend(F), rumor(R).

% A rumor is suspicious if it includes voodoo and the friend is accused of being bad.
suspicious(R) :- rumor(R), contains_bad(R), contains_voodoo(R).

% The case resolves when clues are found and the friendship is repaired.
resolved(P, D, F) :- place(P), detective(D), friend(F), clue_found(P), friendship_repaired(D, F).

#show valid_story/4.
#show suspicious/1.
#show resolved/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for clue in place.clues:
            lines.append(asp.fact("clue", pid, clue))
    for name in DETECTIVE_NAMES:
        lines.append(asp.fact("detective", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend", name))
    for rumor in RUMORS:
        lines.append(asp.fact("rumor", rumor))
        if "bad" in rumor:
            lines.append(asp.fact("contains_bad", rumor))
        if "voodoo" in rumor:
            lines.append(asp.fact("contains_voodoo", rumor))
    for truth in TRUTHS:
        lines.append(asp.fact("truth", truth))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspicious/1.\n#show resolved/3."))
    suspicious = set(asp.atoms(model, "suspicious"))
    resolved = set(asp.atoms(model, "resolved"))
    expected_suspicious = {(r,) for r in RUMORS if "bad" in r and "voodoo" in r}
    if suspicious != expected_suspicious:
        print("MISMATCH in suspicious rumor parity")
        print("clingo:", sorted(suspicious))
        print("python:", sorted(expected_suspicious))
        return 1
    if not resolved:
        print("MISMATCH: no resolved stories found")
        return 1
    print(f"OK: ASP parity verified; {len(resolved)} resolved story pattern(s) found.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style friendship mystery with a bad voodoo rumor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--rumor", choices=RUMORS)
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
    rumor = getattr(args, "rumor", None) or rng.choice(RUMORS)
    detective_name = getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    if detective_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if "voodoo" not in rumor or "bad" not in rumor:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, detective_name=detective_name, friend_name=friend_name, rumor=rumor)


def build_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(SETTINGS, params.place))
    d = world.add(Entity(id=params.detective_name, kind="character", type="child", label=params.detective_name, traits=["curious", "careful"], meters={"focus": 1.0}, memes={"friendship": 1.0}))
    f = world.add(Entity(id=params.friend_name, kind="character", type="child", label=params.friend_name, traits=["quiet", "hurt"], meters={"worry": 1.0}, memes={"friendship": 1.0, "sadness": 1.0}))
    world.facts.update(detective=d, friend=f, rumor=params.rumor, place=world.place)
    return world


def clue_chain(place: Place) -> list[str]:
    return place.clues[:3]


def generate_story(world: World) -> None:
    d: Entity = _safe_fact(world, world.facts, "detective")
    f: Entity = _safe_fact(world, world.facts, "friend")
    rumor: str = _safe_fact(world, world.facts, "rumor")
    place: Place = _safe_fact(world, world.facts, "place")

    world.say(f"{d.display} liked solving little puzzles, especially when a friend needed help.")
    world.say(f"At {place.label}, people kept whispering about {f.display} and a {rumor}.")
    world.para()
    world.say(f"{d.display} did not like rumors, so {d.pronoun()} listened carefully and looked for clues.")
    for clue in clue_chain(place):
        world.say(f"{d.display} found {clue}.")
    world.say(f"The clues did not point to anything bad at all. They pointed to a tiny truth instead.")
    world.para()
    truth = random.choice(TRUTHS)
    world.say(f"It turned out the strange item was only {truth}, not a bad voodoo trick.")
    world.say(f"{f.display} had felt lonely and misunderstood, but {d.display} smiled and told the truth out loud.")
    world.say(f"{f.display} smiled back, and the two friends left together with the rumor gone and their friendship feeling strong.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story for a young child about {f['detective'].display} and {f['friend'].display}, where a bad voodoo rumor turns out to be false.",
        f"Tell a friendship mystery set at {world.place.label} that begins with a scary whisper and ends with a kind truth.",
        f"Write a gentle detective story that includes the words \"shepard\", \"bad\", and \"voodoo\" in a child-friendly way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d: Entity = _safe_fact(world, world.facts, "detective")
    f: Entity = _safe_fact(world, world.facts, "friend")
    rumor: str = _safe_fact(world, world.facts, "rumor")
    place: Place = _safe_fact(world, world.facts, "place")
    q = [
        QAItem(
            question=f"Who solved the mystery at {place.label}?",
            answer=f"{d.display} solved it by looking carefully and following the clues.",
        ),
        QAItem(
            question=f"Why did {d.display} think the rumor about {f.display} was wrong?",
            answer=f"{d.display} found clues that did not match the scary rumor about {rumor}. The clues led to a harmless truth instead.",
        ),
        QAItem(
            question=f"What happened to the friendship in the end?",
            answer=f"The friends understood each other better, and their friendship felt strong again.",
        ),
    ]
    return q


def world_qa(world: World) -> list[QAItem]:
    place: Place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question=f"Why should a detective check the facts before believing a rumor?",
            answer="A detective checks the facts because rumors can be wrong, and the truth matters more than a scary guess.",
        ),
        QAItem(
            question=f"What helps friends stay close when something feels confusing?",
            answer="Kind listening and honest words help friends understand each other and keep their friendship safe.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"place={world.place.label}")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in SETTINGS:
        for d in DETECTIVE_NAMES:
            for f in FRIEND_NAMES:
                if d != f:
                    out.append((pid, d, f))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story patterns")
        for s in stories[:20]:
            print(s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, place in enumerate(SETTINGS):
            params = StoryParams(
                place=place,
                detective_name=_safe_lookup(DETECTIVE_NAMES, i % len(DETECTIVE_NAMES)),
                friend_name=_safe_lookup(FRIEND_NAMES, (i + 2) % len(FRIEND_NAMES)),
                rumor=_safe_lookup(RUMORS, i % len(RUMORS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
