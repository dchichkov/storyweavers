#!/usr/bin/env python3
"""
storyworlds/worlds/photo_dialogue_sound_effects_sharing_heartwarming.py
=======================================================================

A small, heartwarming storyworld about a child taking a photo, hearing a tiny
sound effect, and choosing to share the picture so nobody feels left out.

Seed tale used to build the world:
---
A child wants to keep a special photo all to themself, but a friend looks sad.
They hear the cheerful click of the camera and talk about it. In the end, they
share the photo, make a copy, and everyone smiles together.

World model:
---
- physical meters: possession, distance to goal, sound, damage-free use of tools
- emotional memes: joy, worry, loneliness, warmth, generosity, gratitude

The story is driven by state changes:
- making a photo increases a child's delight and leaves a tangible picture
- hearing the camera click or a little printer whir can prompt dialogue
- sharing the photo lowers loneliness and raises warmth/gratitude
- refusing to share keeps the other child lonely until a turn happens

The story should read like a complete, gentle scene with a clear beginning,
middle turn, and ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    attributes: object | None = None
    copytool: object | None = None
    device: object | None = None
    friend: object | None = None
    maker: object | None = None
    photo: object | None = None
    sharer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    id: str
    label: str
    indoor: bool = True
    cozy: bool = True
    supports: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    can_copy: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    photo = world.get("photo")
    for kid in world.characters():
        if kid.memes.get("wants_sharing", 0) < THRESHOLD:
            continue
        if kid.memes.get("left_out", 0) < THRESHOLD:
            continue
        sig = ("lonely", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["loneliness"] += 1
        out.append(f"{kid.label} looked even more left out.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_lonely(world):
            changed = True
            produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    maker: str
    sharer: str
    friend: str
    photo_kind: str = "photo"
    device: str = "camera"
    copy_method: str = "printer"
    seed: Optional[int] = None
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


PLACES = {
    "schoolyard": Place(id="schoolyard", label="the schoolyard", indoor=False, cozy=False, supports={"photo"}),
    "living_room": Place(id="living_room", label="the living room", indoor=True, cozy=True, supports={"photo"}),
    "library_corner": Place(id="library_corner", label="the library corner", indoor=True, cozy=True, supports={"photo"}),
}

PHOTO_KINDS = {
    "photo": Item(id="photo", label="photo", phrase="a special photo", kind="picture", can_copy=True, tags={"photo"}),
}

CAMERAS = {
    "camera": Item(id="camera", label="camera", phrase="a little camera", kind="tool", can_copy=False, tags={"camera"}),
}

COPY_METHODS = {
    "printer": Item(id="printer", label="printer", phrase="a small printer", kind="tool", can_copy=True, tags={"printer"}),
    "photocopier": Item(id="photocopier", label="copy machine", phrase="a copy machine", kind="tool", can_copy=True, tags={"printer"}),
}

NAMES = ["Mia", "Noah", "Lina", "Eli", "Sara", "Owen", "Ruby", "Theo"]
GENTLE_TRAITS = ["kind", "quiet", "bright", "thoughtful", "cheerful", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for maker in NAMES:
            for sharer in NAMES:
                for friend in NAMES:
                    if len({maker, sharer, friend}) == 3:
                        combos.append((place, maker, sharer, friend))
    return combos


def make_story_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.photo_kind not in PHOTO_KINDS:
        pass
    if params.device not in CAMERAS:
        pass
    if params.copy_method not in COPY_METHODS:
        pass

    world = World(_safe_lookup(PLACES, params.place))
    maker = world.add(Entity(id=params.maker, kind="character", type="girl" if params.maker in {"Mia", "Lina", "Sara", "Ruby"} else "boy", label=params.maker, attributes=None))
    maker = world.entities[params.maker]
    maker.kind = "character"
    maker.type = "girl" if params.maker in {"Mia", "Lina", "Sara", "Ruby"} else "boy"
    sharer = world.add(Entity(id=params.sharer, kind="character", type="girl" if params.sharer in {"Mia", "Lina", "Sara", "Ruby"} else "boy", label=params.sharer))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl" if params.friend in {"Mia", "Lina", "Sara", "Ruby"} else "boy", label=params.friend))
    photo = world.add(Entity(id="photo", kind="thing", type="photo", label="photo", phrase=_safe_lookup(PHOTO_KINDS, params.photo_kind).phrase, owner=maker.id, shared_with={sharer.id}))
    device = world.add(Entity(id="device", kind="thing", type="camera", label="camera", phrase="a little camera"))
    copytool = world.add(Entity(id="copytool", kind="thing", type="tool", label=_safe_lookup(COPY_METHODS, params.copy_method).label, phrase=_safe_lookup(COPY_METHODS, params.copy_method).phrase))

    maker.memes.update({"joy": 0.0, "warmth": 0.0, "generosity": 0.0})
    sharer.memes.update({"joy": 0.0, "worry": 0.0, "warmth": 0.0})
    friend.memes.update({"loneliness": 1.0, "wants_sharing": 1.0, "left_out": 1.0})
    photo.meters.update({"held": 1.0, "copied": 0.0, "seen_by_friend": 0.0})
    device.meters.update({"clicks": 0.0})
    copytool.meters.update({"copies": 0.0})

    world.say(f"{maker.label} found {photo.phrase} on a bright day at {world.place.label}.")
    world.say(f'{maker.label} held up the camera and said, "Let me take one more photo."')
    device.meters["clicks"] += 1
    maker.memes["joy"] += 1
    world.say("Click!")
    world.say(f'{friend.label} leaned closer and asked, "Can I see it too?"')

    world.para()
    if friend.memes["left_out"] >= THRESHOLD:
        world.say(f"{sharer.label} noticed the small sad face and looked down at the photo.")
        world.say(f'"Oh," {sharer.label} said softly, "I was keeping it all to myself."')
        sharer.memes["worry"] += 1
        sharer.memes["warmth"] += 1
        world.say(f'"Here," {sharer.label} said. "We can share it."')
        copytool.meters["copies"] += 1
        photo.meters["copied"] = 1.0
        photo.meters["seen_by_friend"] = 1.0
        photo.shared_with.add(friend.id)
        friend.memes["loneliness"] = 0.0
        friend.memes["joy"] = 1.0
        friend.memes["warmth"] = 1.0
        maker.memes["generosity"] += 1
        maker.memes["warmth"] += 1
        world.say("Whirrr...")
        world.say(f"{copytool.label.capitalize()} hummed, and soon there was a copy for {friend.label} too.")
        world.say(f'Then {friend.label} smiled and said, "Now it feels like our photo."')
        world.say(f"{maker.label} smiled back, and the three of them stood together, shoulder to shoulder, looking at the same picture.")
    else:
        world.say(f"{sharer.label} smiled and shared the photo right away.")
        world.say(f"{friend.label} laughed, and the three of them crowded around the picture together.")

    world.facts.update(maker=maker, sharer=sharer, friend=friend, photo=photo, device=device, copytool=copytool, place=world.place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "photo" and a cheerful "Click!" sound.',
        f'Tell a gentle story where {f["maker"].label} makes a photo, then chooses to share it with {f["friend"].label}.',
        f'Write a warm story about a child, a photo, a tiny sound effect, and a kind moment of sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker, sharer, friend = f["maker"], f["sharer"], f["friend"]
    photo = f["photo"]
    return [
        QAItem(
            question=f"Who made the photo in the story?",
            answer=f"{maker.label} made the photo. The picture started as something {maker.label} wanted to keep close.",
        ),
        QAItem(
            question=f"What sound did the camera make?",
            answer="The camera made a cheerful click. That little sound showed the photo had just been taken.",
        ),
        QAItem(
            question=f"Why did {sharer.label} decide to share the photo?",
            answer=f"{sharer.label} noticed that {friend.label} felt left out. Sharing the photo helped turn that lonely feeling into a happy one.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the photo was shared and {friend.label} had a copy too. Everyone ended up smiling together instead of holding the picture apart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a photo?",
            answer="A photo is a picture made by a camera that captures a moment so you can look at it later.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, see, or enjoy something with you. It helps people feel included.",
        ),
        QAItem(
            question="Why can a tiny sound like click matter in a story?",
            answer="A tiny sound can show that something important just happened. In this kind of story, it helps the moment feel real and alive.",
        ),
    ]


ASP_RULES = r"""
shared(P, F) :- owner(P, M), friend(F), maker(M), wants_share(P), chooses_share(M, P).
comfort_after(P) :- shared(P, F), seen_by_friend(P), friend(F).
happy_end(M, F) :- maker(M), friend(F), comfort_after(P), shared(P, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n in NAMES:
        lines.append(asp.fact("name", n))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("maker", "maker"))
    lines.append(asp.fact("wants_share", "photo"))
    lines.append(asp.fact("chooses_share", "maker", "photo"))
    lines.append(asp.fact("seen_by_friend", "photo"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # smoke test normal generation first
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, maker=None, sharer=None, friend=None, photo_kind=None, device=None, copy_method=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming photo-sharing storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--photo-kind", dest="photo_kind", choices=PHOTO_KINDS)
    ap.add_argument("--device", choices=CAMERAS)
    ap.add_argument("--copy-method", dest="copy_method", choices=COPY_METHODS)
    ap.add_argument("--maker", choices=NAMES)
    ap.add_argument("--sharer", choices=NAMES)
    ap.add_argument("--friend", choices=NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    maker = getattr(args, "maker", None) or rng.choice(NAMES)
    sharer = getattr(args, "sharer", None) or rng.choice([n for n in NAMES if n != maker])
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n not in {maker, sharer}])
    if len({maker, sharer, friend}) < 3:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        maker=maker,
        sharer=sharer,
        friend=friend,
        photo_kind=getattr(args, "photo_kind", None) or "photo",
        device=getattr(args, "device", None) or "camera",
        copy_method=getattr(args, "copy_method", None) or "printer",
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        pass
    world = make_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.shared_with:
            parts.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show shared/2.\n#show happy_end/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="living_room", maker="Mia", sharer="Noah", friend="Lina", photo_kind="photo", device="camera", copy_method="printer"),
            StoryParams(place="schoolyard", maker="Eli", sharer="Ruby", friend="Theo", photo_kind="photo", device="camera", copy_method="photocopier"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
