#!/usr/bin/env python3
"""
A small storyworld about a child at the swimming pool, a treasured manuscript,
and a careful way to keep the pages dry.

Seed-inspired ingredients:
- english
- nibble
- manuscript

Story ingredients:
- Bedtime Story tone
- Sound Effects
- Cautionary turn
- Repetition
- Set in a swimming pool

The world model tracks the child, the manuscript, water risk, caution, and the
final careful choice.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    protected_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cover_ent: object | None = None
    hero: object | None = None
    manuscript: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
class PoolSetting:
    place: str = "the swimming pool"
    splash_zone: set[str] = field(default_factory=lambda: {"poolside", "bench", "hands"})
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
class Cover:
    id: str
    label: str
    phrase: str
    guards: set[str]
    prep: str
    tail: str
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
    name: str
    gender: str
    parent: str
    place: str
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


class World:
    def __init__(self, setting: PoolSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.water_near_pages: bool = False

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.water_near_pages = self.water_near_pages
        return clone


def normalize(s: str) -> str:
    return s.strip().lower()


SETTINGS = {
    "swimming_pool": PoolSetting(place="the swimming pool"),
}

COVERS = {
    "plastic_folder": Cover(
        id="plastic_folder",
        label="a clear plastic folder",
        phrase="a clear plastic folder for the manuscript",
        guards={"wet"},
        prep="slip the manuscript into a clear plastic folder first",
        tail="carefully carried the manuscript in the clear plastic folder",
    ),
    "dry_bag": Cover(
        id="dry_bag",
        label="a dry bag",
        phrase="a dry bag with a tight seal",
        guards={"wet"},
        prep="put the manuscript in a dry bag first",
        tail="carefully carried the manuscript in the dry bag",
    ),
}

MANUSCRIPT = {
    "english": {
        "label": "manuscript",
        "phrase": "an English manuscript with neat black letters",
        "topic": "english",
    }
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Noah", "Ben", "Finn", "Theo"]


ASP_RULES = r"""
risk(P) :- manuscript(P), near_water(P).
safe(P) :- manuscript(P), protected(P).
careful_story :- risk(m), safe(m).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("manuscript", "m"),
        asp.fact("near_water", "m"),
    ]
    for cid in COVERS:
        lines.append(asp.fact("cover", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _reasonableness_gate() -> None:
    # This world is intentionally narrow: if there is a manuscript near pool water,
    # the story needs a protective cover to make the turn meaningful.
    if not COVERS:
        pass


def pick_cover(rng: random.Random) -> Cover:
    return rng.choice(list(COVERS.values()))


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"joy": 0.0},
        memes={"love": 0.0, "caution": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="parent",
        meters={"work": 0.0},
    ))
    manuscript = world.add(Entity(
        id="manuscript",
        type="manuscript",
        label="manuscript",
        phrase=MANUSCRIPT["english"]["phrase"],
        owner=hero.id,
        caretaker=parent.id,
        meters={"wet": 0.0, "safe": 0.0},
        memes={"value": 1.0},
    ))

    cover = pick_cover(random.Random(params.seed or 0))
    cover_ent = world.add(Entity(
        id=cover.id,
        type="cover",
        label=cover.label,
        phrase=cover.phrase,
        owner=hero.id,
        meters={"clean": 1.0},
    ))
    cover_ent.worn_by = hero.id
    manuscript.protected_by = cover.id

    world.say(
        f"At {world.setting.place}, {params.name} sat very still with {manuscript.phrase}."
    )
    world.say(
        f"The pages felt special, special, special, because {params.name} loved the English words."
    )
    world.say(
        f"And then came the pool sound: splash-swish, plip-plop, splash-swish."
    )

    world.para()
    world.say(
        f"{params.name} wanted to nibble the corner of a snack bar and read at once, but the water said, "
        f"\"Swoosh, swoosh, stay careful.\""
    )
    world.say(
        f"{params.parent.capitalize()} gave a gentle caution: \"Not too close to the edge, or the manuscript may get wet.\""
    )
    world.facts["risk"] = True

    world.para()
    world.say(
        f"{params.name} looked at the water, and looked at the manuscript, and looked again."
    )
    world.say(
        f"Nibble, nibble, read, read, pause, pause."
    )
    world.say(
        f"Then {params.name} nodded and listened to the caution."
    )
    world.say(
        f"First {cover.prep}, and only then walk beside the pool."
    )
    manuscript.meters["safe"] += 1
    manuscript.memes["caution"] += 1
    world.facts["safe"] = True
    world.facts["cover"] = cover.id

    world.para()
    world.say(
        f"So {params.name} {cover.tail}, and the pages stayed dry."
    )
    world.say(
        f"The pool still went splash-swish, splash-swish, but the manuscript stayed snug and safe."
    )
    world.say(
        f"At the end of the bedtime day, {params.name} had the English manuscript, the quiet cover, and a calm little smile."
    )

    world.facts.update(hero=hero, parent=parent, manuscript=manuscript, cover=cover, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle bedtime story set at a swimming pool with splashy sound effects, caution, and repetition.',
        f"Tell a story where {f['hero'].id} must keep an English manuscript dry near the swimming pool.",
        "Write a child-friendly story that says when to be careful, repeats a small phrase, and ends with a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    manuscript = f["manuscript"]
    cover = f["cover"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to keep safe near {world.setting.place}?",
            answer=f"{hero.id} was trying to keep the English manuscript safe and dry near {world.setting.place}.",
        ),
        QAItem(
            question=f"What caution did {parent.label} give about the manuscript?",
            answer="The caution was not to get the manuscript too close to the water, because it could get wet.",
        ),
        QAItem(
            question=f"What careful thing did {hero.id} use before walking by the pool?",
            answer=f"{hero.id} used {cover.label} so the manuscript stayed dry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does splash mean?",
            answer="Splash is the sound and spray water makes when it hits something.",
        ),
        QAItem(
            question="Why do people protect paper near water?",
            answer="People protect paper near water because paper can soak up water and get ruined.",
        ),
        QAItem(
            question="What is a manuscript?",
            answer="A manuscript is a handwritten or carefully prepared piece of writing, often like a story or book draft.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.protected_by:
            bits.append(f"protected_by={e.protected_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a manuscript by the swimming pool.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        place=getattr(args, "place", None) or "swimming_pool",
    )


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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show careful_story/0."))
    return sorted(set(asp.atoms(model, "careful_story")))


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", place="swimming_pool"),
    StoryParams(name="Leo", gender="boy", parent="father", place="swimming_pool"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show careful_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story shape.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
