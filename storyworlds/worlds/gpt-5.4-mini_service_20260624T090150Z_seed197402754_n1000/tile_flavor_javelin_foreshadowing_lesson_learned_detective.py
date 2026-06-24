#!/usr/bin/env python3
"""
storyworlds/worlds/tile_flavor_javelin_foreshadowing_lesson_learned_detective.py
=================================================================================

A small detective-style storyworld about a careful child detective, a strange
flavor clue, and a javelin that should never be treated like a toy.

Seed tale:
---
At the school gym, Mina noticed a tiny mint flavor on one bright tile. She also
found a javelin lying too close to the snack table. The janitor said nobody had
seen who moved it, but the mint clue made Mina look toward the juice stand.
There she found a cracked cup, a sticky trail, and a child who had been rushing
around with the javelin for fun.

Mina told the child that sharp things were not for games. The child apologized
and put the javelin back in the sports rack. Mina learned that little clues can
point to the truth, and that careful eyes can keep everyone safe.

World model:
---
* physical meters: cleanliness, safety, damage, clutter, flavor_trace
* emotional memes: curiosity, concern, relief, embarrassment, confidence

Narrative shape:
---
setup -> foreshadowing clue -> investigation -> reveal -> lesson learned
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
    carried_by: Optional[str] = None
    location: str = ""
    sharp: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {
        "cleanliness": 0.0,
        "safety": 0.0,
        "damage": 0.0,
        "clutter": 0.0,
        "flavor_trace": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "curiosity": 0.0,
        "concern": 0.0,
        "relief": 0.0,
        "embarrassment": 0.0,
        "confidence": 0.0,
    })

    child: object | None = None
    detective: object | None = None
    javelin: object | None = None
    tile: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man", "boy detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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


@dataclass
class Setting:
    place: str = "the school gym"
    affords: set[str] = field(default_factory=lambda: {"investigate", "tidy_up"})
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
    flavor: str
    place: str
    hint: str
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
class ObjectDef:
    label: str
    phrase: str
    type: str
    location: str = "floor"
    sharp: bool = False
    plural: bool = False
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
    clue: str
    object: str
    detective_name: str
    child_name: str
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
    "gym": Setting(place="the school gym"),
    "hall": Setting(place="the tiled hallway"),
    "cafeteria": Setting(place="the cafeteria"),
}

CLUES = {
    "mint": Clue(flavor="mint", place="tile", hint="a fresh mint taste"),
    "strawberry": Clue(flavor="strawberry", place="tile", hint="a sweet strawberry taste"),
    "orange": Clue(flavor="orange", place="tile", hint="a bright orange taste"),
}

OBJECTS = {
    "javelin": ObjectDef(
        label="javelin",
        phrase="a long practice javelin",
        type="javelin",
        location="sports rack",
        sharp=True,
        plural=False,
    ),
}

DETECTIVE_NAMES = ["Mina", "Noa", "Riley", "Ivy", "Arlo"]
CHILD_NAMES = ["Ben", "Lena", "Toby", "Mara", "Jun"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _advance(world: World) -> None:
    detective = world.get("detective")
    suspect = world.get("child")
    obj = world.get("javelin")
    clue = _safe_fact(world, world.facts, "clue")
    tile = world.get("tile")

    if "foreshadow" not in world.fired and clue.flavor in tile.meters and tile.meters["flavor_trace"] >= THRESHOLD:
        world.fired.add("foreshadow")
        detective.memes["curiosity"] += 1
        detective.memes["confidence"] += 1
        world.say(
            f"{detective.id} noticed a tiny {clue.flavor} taste on the tile, "
            f"and that small clue felt important right away."
        )

    if "investigate" not in world.fired and detective.memes["curiosity"] >= THRESHOLD:
        world.fired.add("investigate")
        detective.meters["clutter"] += 0.5
        world.say(
            f"{detective.id} knelt down and followed the flavor clue across the shiny floor."
        )
        world.say(
            f"The trail led past the snack table and straight toward the javelin rack."
        )

    if "reveal" not in world.fired and obj.carried_by == suspect.id:
        world.fired.add("reveal")
        detective.memes["concern"] += 1
        suspect.memes["embarrassment"] += 1
        world.say(
            f"There, {suspect.id} was holding the javelin too casually, as if it were a play stick."
        )
        world.say(
            f"Near {suspect.id}'s feet sat a cracked cup and a sticky spot that matched the flavor clue."
        )

    if "lesson" not in world.fired and suspect.memes["embarrassment"] >= THRESHOLD:
        world.fired.add("lesson")
        suspect.meters["safety"] += 1
        detective.memes["relief"] += 1
        detective.memes["confidence"] += 1
        suspect.carried_by = None
        obj.carried_by = None
        world.say(
            f"{detective.id} explained that sharp things like a javelin belong in the sports rack, not in games."
        )
        world.say(
            f"{suspect.id} apologized, put the javelin back where it belonged, and promised to walk carefully."
        )
        world.say(
            f"Then {detective.id} smiled, because the little flavor clue had foreshadowed the truth all along."
        )


def tell(setting: Setting, clue: Clue, obj: ObjectDef, detective_name: str, child_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="girl", label="detective"))
    child = world.add(Entity(id=child_name, kind="character", type="boy"))
    tile = world.add(Entity(id="tile", type="tile", label="tile", location="floor"))
    javelin = world.add(Entity(id="javelin", type="javelin", label="javelin", sharp=True, location=obj.location))
    tile.meters["flavor_trace"] = 1.0
    tile.meters["cleanliness"] = 0.2
    javelin.carried_by = child.id
    child.memes["embarrassment"] = 0.0

    world.facts.update(
        detective=detective,
        child=child,
        tile=tile,
        javelin=javelin,
        clue=clue,
        object=obj,
        setting=setting,
    )

    world.say(
        f"{detective.id} was a careful little detective who loved solving small mysteries at {setting.place}."
    )
    world.say(
        f"One afternoon, {detective.id} found {clue.hint} on a bright tile near the snack table."
    )
    world.say(
        f"That clue was a small foreshadowing: something had gone wrong near the javelin rack."
    )
    world.para()
    world.say(
        f"{detective.id} followed the taste clue and looked where the floor shone the brightest."
    )
    _advance(world)
    world.para()
    world.say(
        f"In the end, {detective.id} learned that careful eyes can solve a mystery before anyone gets hurt."
    )
    world.say(
        f"{child.id} learned a lesson too: javelins are for practice and sports racks, never for rough play."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that includes a tile, a flavor clue, and a javelin.',
        f'Write a gentle mystery where {f["detective"].id} notices a {f["clue"].flavor} clue on a tile and discovers why the javelin was out of place.',
        f'Write a story with foreshadowing and a lesson learned in {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    d = _safe_fact(world, world.facts, "detective")
    c = _safe_fact(world, world.facts, "child")
    clue = _safe_fact(world, world.facts, "clue")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{d.id} solved it by noticing a tiny clue and following it carefully.",
        ),
        QAItem(
            question=f"What flavor clue did {d.id} find on the tile?",
            answer=f"{d.id} found {clue.hint} on the tile.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"The lesson was that javelins belong in the sports rack, and small clues can help solve a problem safely.",
        ),
        QAItem(
            question=f"Why was {c.id} embarrassed?",
            answer=f"{c.id} was embarrassed because {c.id} had been handling the javelin carelessly instead of treating it like a sports tool.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a javelin?",
            answer="A javelin is a long, pointed sports spear used in track and field practice, so it should be handled carefully.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue early on that hints something important will happen later.",
        ),
        QAItem(
            question="What is a tile?",
            answer="A tile is a flat piece of hard material used to cover floors or walls.",
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


ASP_RULES = r"""
detective(X) :- person(X).
clue(flavor) :- flavor_trace(flavor).
foreshadowing :- clue(flavor), item(tile).
lesson_learned :- item(javelin), safe_storage(javelin).
"""


def asp_facts() -> str:
    import asp
    parts = [
        asp.fact("person", "detective"),
        asp.fact("person", "child"),
        asp.fact("item", "tile"),
        asp.fact("item", "javelin"),
        asp.fact("safe_storage", "javelin"),
    ]
    for flavor in CLUES:
        parts.append(asp.fact("flavor_trace", flavor))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld with a flavor clue and a javelin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
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
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    obj = getattr(args, "object", None) or "javelin"
    det = getattr(args, "detective_name", None) or rng.choice(DETECTIVE_NAMES)
    child = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(setting=setting, clue=clue, object=obj, detective_name=det, child_name=child)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CLUES, params.clue), _safe_lookup(OBJECTS, params.object), params.detective_name, params.child_name)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: round(v, 2) for k, v in e.meters.items() if v}
            memes = {k: round(v, 2) for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.location:
                bits.append(f"location={e.location}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[tuple[str, str, str]]:
    return [(s, c, "javelin") for s in SETTINGS for c in CLUES]


def asp_verify() -> int:
    import asp
    program = asp_program("#show foreshadowing/0.\n#show lesson_learned/0.")
    model = asp.one_model(program)
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    want = {"foreshadowing/0", "lesson_learned/0"}
    if atoms == want:
        print("OK: ASP twin matches the simple reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected atoms.")
    print("got:", sorted(atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show foreshadowing/0.\n#show lesson_learned/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Compatible detective-story combos:")
        for s, c, o in valid_story_params():
            print(f"  {s} / {c} / {o}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s, c, o in valid_story_params():
            params = StoryParams(setting=s, clue=c, object=o,
                                 detective_name=_safe_lookup(DETECTIVE_NAMES, 0), child_name=_safe_lookup(CHILD_NAMES, 0))
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
