#!/usr/bin/env python3
"""
storyworlds/worlds/grammar_bone_repetition_transformation_ghost_story.py
=======================================================================

A small ghost-story storyworld about grammar, a bone, repetition, and a gentle
transformation.

Seed tale:
---
A child in a quiet old house hears a spooky tapping in the dark. The tapping
comes from a bone hidden in a dusty box. The child is nervous, but they keep
saying a grammar sentence out loud: "The bone is not a monster." After each
repeat, the tapping softens. At last, the bone transforms into a shiny little
bone-shaped key that unlocks a music box. A friendly ghost puppy appears, and
the child learns that some scary things are only waiting to change.

World model:
---
    child bravery -> fear down, curiosity up
    repeated grammar line -> bone glow up, haunting down
    bone glow + courage -> transformation into key
    key opening -> ghost puppy comfort up, room calm
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bone: object | None = None
    hero: object | None = None
    parent: object | None = None
    puppy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the old house"
    detail: str = "The hall was quiet, and the moonlight made the shadows long."
    affords: set[str] = field(default_factory=lambda: {"listen", "repeat", "open"})
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
class BoneThing:
    id: str
    label: str
    phrase: str
    transformed_label: str
    transformed_phrase: str
    tag: str = "bone"
    BONE: object | None = None
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
    place: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
    "attic": Setting(
        place="the attic",
        detail="The attic was full of dusty boxes, and the moonlight fell in pale squares.",
    ),
    "hallway": Setting(
        place="the hallway",
        detail="The hallway was narrow and sleepy, with creaky boards and a little cold air.",
    ),
    "study": Setting(
        place="the study",
        detail="The study was still and neat, with a desk, a lamp, and one dark corner.",
    ),
}

NAMES_GIRL = ["Mina", "Lina", "Tess", "Nora", "Maya"]
NAMES_BOY = ["Eli", "Finn", "Noah", "Theo", "Ari"]
PARENTS = {"mother": "mom", "father": "dad"}

BONE = BoneThing(
    id="bone",
    label="bone",
    phrase="an old bone tucked inside a dusty box",
    transformed_label="bone-shaped key",
    transformed_phrase="a shiny little bone-shaped key",
)

ASP_RULES = r"""
% A bone becomes eerie when it has been listened to and repeated enough.
haunted(B) :- bone(B), heard(B), repeated(B).

% The brave line changes the bone when fear has gone low enough.
transforms(B, K) :- haunted(B), courage(hero), not fear_high(hero), key(K).

% Opening the music box calms the room and brings the ghost puppy out.
comforts(P) :- key(K), opens(K), puppy(P).
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("bone", "bone"),
        asp.fact("key", "bone_key"),
        asp.fact("opens", "bone_key"),
        asp.fact("puppy", "ghost_puppy"),
        asp.fact("heard", "bone"),
        asp.fact("repeated", "bone"),
        asp.fact("courage", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost story world: grammar, a bone, repetition, and transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(list(PARENTS))
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def _build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=_safe_lookup(PARENTS, params.parent)))
    bone = world.add(Entity(
        id=BONE.id,
        type="bone",
        label=BONE.label,
        phrase=BONE.phrase,
        owner=hero.id,
        meters={"glow": 0.0, "transformed": 0.0},
        memes={"fear": 2.0, "curiosity": 0.0, "bravery": 0.0, "comfort": 0.0},
    ))
    puppy = world.add(Entity(
        id="ghost_puppy",
        kind="character",
        type="puppy",
        label="ghost puppy",
        phrase="a friendly ghost puppy",
        meters={"presence": 0.0},
        memes={"lonely": 1.0, "comfort": 0.0},
    ))

    world.say(f"{hero.id} was a little {hero.type} who liked grammar games, especially quiet sentence games.")
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.label} went into {world.setting.place}.")
    world.say(world.setting.detail)
    world.say(f"On a shelf sat {bone.phrase}.")
    world.para()

    world.say(
        f"At first, the bone gave a soft tap, tap, tap. {hero.id} froze, because the tapping sounded spooky."
    )
    hero.memes["fear"] += 1.0
    bone.meters["glow"] += 0.25
    world.say(
        f"But {hero.id} remembered a grammar sentence and said, \"The bone is not a monster.\""
    )
    hero.memes["bravery"] += 0.5
    hero.memes["curiosity"] += 0.5
    bone.meters["glow"] += 0.5
    bone.meters["heard"] = bone.meters.get("heard", 0.0) + 1.0

    world.say(
        f"{hero.id} said it again. \"The bone is not a monster.\""
    )
    bone.meters["glow"] += 0.75
    bone.meters["heard"] += 1.0

    world.say(
        f"And then again. \"The bone is not a monster.\""
    )
    bone.meters["glow"] += 1.0
    bone.meters["heard"] += 1.0

    world.para()

    if bone.meters["glow"] >= THRESHOLD:
        hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.5)
        hero.memes["bravery"] += 1.0
        bone.meters["transformed"] = 1.0
        world.say(
            f"With one bright shiver, the bone changed into {BONE.transformed_phrase}."
        )
        world.say(
            f"{hero.id} picked it up, and it clicked open a tiny music box hidden underneath."
        )
        puppet = puppy
        puppet.meters["presence"] = 1.0
        puppet.memes["comfort"] += 2.0
        hero.memes["comfort"] += 2.0
        world.say(
            f"A gentle ghost puppy wiggled out, wagged a thin tail, and leaned against {hero.id}."
        )
        world.say(
            f"The room felt warm now, and the tapping was only the music box saying hello."
        )
    else:
        world.say(
            f"The bone stayed quiet, and {hero.id} kept holding {hero.pronoun('possessive')} breath."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        bone=bone,
        puppy=puppy,
        transformed=bool(bone.meters.get("transformed")),
        place=params.place,
    )
    return world


def _story(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    return [
        'Write a gentle ghost story for a child that includes the words "grammar" and "bone".',
        f"Tell a spooky but kind story where {hero.id} repeats a grammar sentence until a bone changes.",
        f"Write a short story about {hero.id}, {parent.label}, a bone, and a friendly ghost puppy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    bone = _safe_fact(world, f, "bone")
    parent = _safe_fact(world, f, "parent")
    qa = [
        QAItem(
            question=f"What made {hero.id} feel scared at first in {world.setting.place}?",
            answer=f"{hero.id} felt scared because the bone in the dusty box kept making a soft tap, tap, tap in the dark.",
        ),
        QAItem(
            question=f"What sentence did {hero.id} repeat to help with the grammar and the scary bone?",
            answer='They repeated, "The bone is not a monster." That grammar sentence helped them stay brave.',
        ),
        QAItem(
            question=f"What changed after {hero.id} said the sentence again and again?",
            answer=f"The bone changed into {BONE.transformed_phrase}, and that opened the hidden music box.",
        ),
        QAItem(
            question=f"Who came out after the transformation?",
            answer="A friendly ghost puppy came out and leaned against the child, so the room felt warm instead of scary.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave and comforted, because the spooky noise turned into a gentle hello.",
        ),
    ]
    if parent.id:
        qa.append(
            QAItem(
                question=f"Who went with {hero.id} into {world.setting.place}?",
                answer=f"{hero.id} went with {parent.label} into {world.setting.place} on the spooky little trip.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grammar?",
            answer="Grammar is the set of rules that helps words fit together so sentences make sense.",
        ),
        QAItem(
            question="What is a bone?",
            answer="A bone is a hard part inside a body, and people also use the word for a real or pretend bone in stories and toys.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means saying or doing something again and again.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into something new.",
        ),
    ]


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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="hallway", name="Eli", gender="boy", parent="father"),
    StoryParams(place="study", name="Tess", gender="girl", parent="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=_story(world),
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


def asp_verify() -> int:
    import asp

    program = asp_program("#show haunted/1.\n#show transforms/2.\n#show comforts/1.")
    model = asp.one_model(program)
    haunted = asp.atoms(model, "haunted")
    transforms = asp.atoms(model, "transforms")
    comforts = asp.atoms(model, "comforts")
    ok = ("bone",) in haunted and ("bone", "bone_key") in transforms and ("ghost_puppy",) in comforts
    if ok:
        print("OK: ASP twin produces the expected haunted/transforms/comforts model.")
        return 0
    print("MISMATCH: ASP twin did not yield the expected model.")
    print("haunted:", haunted)
    print("transforms:", transforms)
    print("comforts:", comforts)
    return 1


def build_asp_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show haunted/1.\n#show transforms/2.\n#show comforts/1."))
    print("haunted:", asp.atoms(model, "haunted"))
    print("transforms:", asp.atoms(model, "transforms"))
    print("comforts:", asp.atoms(model, "comforts"))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show haunted/1.\n#show transforms/2.\n#show comforts/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        build_asp_list()
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
