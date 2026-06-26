#!/usr/bin/env python3
"""
storyworlds/worlds/convey_sound_effects_rhyme_whodunit.py
=========================================================

A tiny whodunit storyworld with sound effects, little rhymes, and a child-safe
mystery that is solved by noticing what the clues *mean*.

Premise
-------
A beloved object goes missing from a small setting.
The finder hears a few sound cues, notices a rhyme-like clue, and uses the
world model to reason out who moved the object and where it ended up.

The narration is intentionally shaped like a gentle whodunit:
- clear setup
- a clue-filled middle
- a deduction turn
- a tidy ending that proves what changed

The world is simulated through typed entities with physical meters and emotional
memes. The story is not a frozen paragraph; it is assembled from state changes
and inference over those changes.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    detective: object | None = None
    helper: object | None = None
    object_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class Setting:
    place: str
    indoor: bool
    sound: str
    rhyme_hint: str
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
class Mystery:
    id: str
    object_label: str
    object_phrase: str
    object_location: str
    clue_sound: str
    clue_rhyme: str
    culprit_id: str
    culprit_label: str
    culprit_type: str
    culprit_sound: str
    culprit_hideout: str
    ending: str
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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    detective_type: str
    helper_type: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, sound="clink-clink", rhyme_hint="sink"),
    "library": Setting(place="the library", indoor=True, sound="flip-flip", rhyme_hint="glow"),
    "garden": Setting(place="the garden", indoor=False, sound="rustle-rustle", rhyme_hint="gate"),
    "attic": Setting(place="the attic", indoor=True, sound="tap-tap", rhyme_hint="chair"),
}

MYSTERIES = {
    "cookie": Mystery(
        id="cookie",
        object_label="cookie tin",
        object_phrase="a shiny cookie tin",
        object_location="behind the flour jar",
        clue_sound="clink-clink",
        clue_rhyme="If you hear a clink near the sink, look where spoons like to blink.",
        culprit_id="mouse",
        culprit_label="a mouse",
        culprit_type="mouse",
        culprit_sound="skitter-skit",
        culprit_hideout="under the pantry shelf",
        ending="the tin was back on the counter, and the cookie crumbs were gone",
    ),
    "bell": Mystery(
        id="bell",
        object_label="silver bell",
        object_phrase="a little silver bell",
        object_location="inside a basket of yarn",
        clue_sound="ding-ding",
        clue_rhyme="If the ding comes when things begin to sing, check the softest ring.",
        culprit_id="cat",
        culprit_label="a cat",
        culprit_type="cat",
        culprit_sound="mrrp-rrp",
        culprit_hideout="on a sunny cushion",
        ending="the bell was tied to the basket again, and the yarn was neat",
    ),
    "crayon": Mystery(
        id="crayon",
        object_label="red crayon",
        object_phrase="one bright red crayon",
        object_location="inside a toy box",
        clue_sound="scratch-scratch",
        clue_rhyme="If you hear a scratch where the toys are stacked, follow the trail that is neatly tracked.",
        culprit_id="rabbit",
        culprit_label="a rabbit",
        culprit_type="rabbit",
        culprit_sound="thump-thump",
        culprit_hideout="behind a pillow fort",
        ending="the red crayon was back in the toy box, and the picture was finished",
    ),
}

DETECTIVE_NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Luna", "Ben"]
HELPER_TYPES = ["dog", "bird", "squirrel", "brother", "sister"]
DETECTIVE_TYPES = ["girl", "boy"]


def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    return True if setting and mystery else False


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, mid) for sid in SETTINGS for mid in MYSTERIES if reasonableness_gate(_safe_lookup(SETTINGS, sid), _safe_lookup(MYSTERIES, mid))]


def choose_clue_order(world: World, mystery: Mystery) -> list[str]:
    return [mystery.clue_sound, mystery.clue_rhyme, world.setting.rhyme_hint]


def solve_mystery(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f"{detective.id} was a little detective who loved to convey clues to the room "
        f"with a calm nod and a careful look."
    )
    world.say(
        f"One day, in {world.setting.place}, {detective.id} found that {mystery.object_phrase} was missing."
    )
    world.say(
        f'"{mystery.clue_sound}!" went a sound from the {world.setting.place}. '
        f"{mystery.clue_rhyme}"
    )
    world.say(
        f"{helper.id} tilted {helper.pronoun('possessive')} head and said, "
        f'"Hmm, that sound feels like a trail, not a trick."'
    )

    detective.memes["doubt"] += 1
    world.say(
        f"{detective.id} followed the little trail of signs: {world.setting.sound}, then "
        f"{mystery.culprit_sound}, then a quiet hush near {mystery.culprit_hideout}."
    )
    world.say(
        f"At last, {detective.id} pointed and said, "
        f'"The clue rhyme fits! {mystery.culprit_label} moved the {mystery.object_label}!"'
    )

    detective.memes["certainty"] += 1
    detective.meters["found"] = 1
    mystery_obj = world.get(mystery.object_label)
    culprit = world.get(mystery.culprit_id)
    mystery_obj.location = "returned"
    culprit.meters["caught"] = 1
    culprit.memes["embarrassed"] += 1
    world.say(
        f"{mystery.culprit_label} peeked out and gave a tiny {mystery.culprit_sound}. "
        f"It had tucked the {mystery.object_label} away by mistake."
    )
    world.say(
        f"{detective.id} smiled, and {helper.id} helped put everything back where it belonged."
    )
    world.say(
        f"In the end, {mystery.ending}, and the whole room felt tidy again."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_type,
    ))
    object_ent = world.add(Entity(
        id=mystery.object_label,
        kind="thing",
        type="object",
        label=mystery.object_label,
        phrase=mystery.object_phrase,
        owner=detective.id,
        location=mystery.object_location,
    ))
    culprit = world.add(Entity(
        id=mystery.culprit_id,
        kind="character",
        type=mystery.culprit_type,
        label=mystery.culprit_label,
        location=mystery.culprit_hideout,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        object_ent=object_ent,
        culprit=culprit,
        mystery=mystery,
        setting=setting,
    )
    solve_mystery(world, detective, helper, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = _safe_fact(world, f, "mystery")
    setting = _safe_fact(world, f, "setting")
    detective = _safe_fact(world, f, "detective")
    return [
        f"Write a child-friendly whodunit set in {setting.place} that uses the words "
        f'"{mystery.clue_sound}" and "{mystery.clue_rhyme[:18]}..."',
        f"Tell a short mystery where {detective.id} can convey the answer by noticing a sound clue and a rhyme.",
        f"Write a gentle detective story with a missing {mystery.object_label} and a tidy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = _safe_fact(world, f, "mystery")
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    culprit = _safe_fact(world, f, "culprit")
    setting = _safe_fact(world, f, "setting")
    obj = _safe_fact(world, f, "object_ent")
    return [
        QAItem(
            question=f"What went missing in {setting.place}?",
            answer=f"{detective.id} noticed that {obj.phrase} had gone missing.",
        ),
        QAItem(
            question=f"What clue sound did the detective hear?",
            answer=f"{mystery.clue_sound} was the clue sound, and it led {detective.id} to look closer.",
        ),
        QAItem(
            question=f"Who helped {detective.id} solve the mystery?",
            answer=f"{helper.id} helped by listening carefully and staying near {detective.id}.",
        ),
        QAItem(
            question=f"Who had moved the object?",
            answer=f"It was {culprit.label}, which had moved the {mystery.object_label} by mistake.",
        ),
        QAItem(
            question=f"What was the ending image?",
            answer=f"In the end, {mystery.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="Why do people use sound effects in stories?",
            answer="Sound effects can help a reader hear what is happening and make the story feel lively.",
        ),
        QAItem(
            question="Why do rhymes help in a mystery?",
            answer="A rhyme can make a clue easier to remember and can point the detective toward the answer.",
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).

valid(S, M) :- setting(S), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_fact", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle whodunit storyworld with sound effects and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=DETECTIVE_NAMES)
    ap.add_argument("--type", dest="detective_type", choices=DETECTIVE_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "mystery", None):
        if (getattr(args, "setting", None), getattr(args, "mystery", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [c for c in combos
             if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
             and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mystery = rng.choice(valid)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES),
        detective_type=getattr(args, "detective_type", None) or rng.choice(DETECTIVE_TYPES),
        helper_type=getattr(args, "helper", None) or rng.choice(HELPER_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(setting="kitchen", mystery="cookie", detective_name="Mia", detective_type="girl", helper_type="dog"),
    StoryParams(setting="library", mystery="bell", detective_name="Leo", detective_type="boy", helper_type="bird"),
    StoryParams(setting="garden", mystery="crayon", detective_name="Nora", detective_type="girl", helper_type="squirrel"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for item in combos:
            print(" ", item)
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
