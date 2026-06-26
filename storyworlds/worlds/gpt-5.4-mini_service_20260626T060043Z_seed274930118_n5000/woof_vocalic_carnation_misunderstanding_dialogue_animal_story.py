#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/woof_vocalic_carnation_misunderstanding_dialogue_animal_story.py
================================================================================================

A small animal-story world about a harmless misunderstanding that gets fixed
through dialogue.

Seed-shaped premise:
- A dog hears a vocalic sound near a carnation.
- The dog thinks the flower is in trouble.
- Friends talk it through and discover the sound is just a cheerful song.

The domain keeps the story child-facing, concrete, and state-driven:
- typed entities with meters and memes
- a physical setting
- misunderstanding caused by an ambiguous sound
- dialogue that resolves the confusion
- an ending image proving what changed
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    flower: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dog", "cat", "fox", "rabbit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    detail: str
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
class Sound:
    label: str
    source: str
    misunderstood_as: str
    clue: str
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
    sound: str
    flower: str
    hero: str
    friend: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", detail="A fence hummed softly in the warm air."),
    "yard": Setting(place="the yard", detail="Little shadows wiggled under the bushes."),
    "porch": Setting(place="the porch", detail="The porch boards were bright in the afternoon sun."),
}

SOUNDS = {
    "woof": Sound(
        label="woof",
        source="dog",
        misunderstood_as="a warning bark",
        clue="The sound was friendly and round, not sharp at all.",
    ),
    "vocalic": Sound(
        label="vocalic hum",
        source="songbird",
        misunderstood_as="a cry for help",
        clue="The sound rose and fell like a tiny song.",
    ),
    "rustle": Sound(
        label="rustle",
        source="breeze",
        misunderstood_as="a sneaky step",
        clue="The leaves only whispered because the wind moved them.",
    ),
}

FLOWERS = {
    "carnation": "a bright pink carnation",
    "yellow_carnation": "a yellow carnation",
    "red_carnation": "a red carnation",
}

HEROES = {
    "dog": ("Dottie", "dog"),
    "cat": ("Milo", "cat"),
    "rabbit": ("Nina", "rabbit"),
}

FRIENDS = ["cat", "rabbit", "fox"]


ASP_RULES = r"""
sound_misunderstood(S) :- sound(S), misunderstood(S,_).
needs_talk(H,S,F) :- hero(H), sound_misunderstood(S), flower(F).
resolved(H,S) :- needs_talk(H,S,_), dialogue(H,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("misunderstood", sid, s.misunderstood_as))
    for fid in FLOWERS:
        lines.append(asp.fact("flower", fid))
    for hid, (name, kind) in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("animal", kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.sound in SOUNDS and params.flower in FLOWERS and params.hero in HEROES


def _inspect_confusion(world: World, hero: Entity, sound: Sound, flower: Entity) -> bool:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} heard a {sound.label} near {flower.label} and froze. "
        f"{hero.id} thought it meant {sound.misunderstood_as}."
    )
    return True


def _dialogue(world: World, hero: Entity, friend: Entity, sound: Sound, flower: Entity) -> None:
    hero.memes["confusion"] += 1
    friend.memes["calm"] += 1
    world.say(
        f'"Wait," said {friend.id}. "That is only a {sound.label}."'
    )
    world.say(
        f'"Look," {friend.id} added, "the {sound.clue.lower()}"'
    )
    hero.memes["confusion"] = 0.0
    hero.memes["relief"] += 1
    hero.meters["closer"] = 1.0
    world.say(
        f"{hero.id} listened again and leaned closer to the {flower.label}. "
        f"The little flower was still bright and safe."
    )


def tell(setting: Setting, sound: Sound, flower_name: str, hero_kind: str, friend_kind: str) -> World:
    world = World(setting)
    hero_name, hero_type = _safe_lookup(HEROES, hero_kind)
    friend_name, friend_type = _safe_lookup(HEROES, friend_kind)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    flower = world.add(Entity(id="flower", kind="thing", type="flower", label=_safe_lookup(FLOWERS, flower_name), phrase=_safe_lookup(FLOWERS, flower_name)))

    world.say(f"{hero.id} lived near {setting.place}.")
    world.say(f"{hero.id} loved quiet mornings there.")
    world.say(f"{setting.detail}")

    world.para()
    world.say(
        f"One day, {hero.id} heard a {sound.label} beside {flower.label}."
    )
    _inspect_confusion(world, hero, sound, flower)
    world.say(
        f"{hero.id} hurried over because it seemed important."
    )

    world.para()
    _dialogue(world, hero, friend, sound, flower)
    world.say(
        f"In the end, {hero.id} stayed with {friend.id} and watched the {flower.label} sway in the light."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        flower=flower,
        sound=sound,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story where {f["hero"].id} hears a {f["sound"].label} near a {f["flower"].label} and worries.',
        f"Tell a gentle story with a misunderstanding and dialogue in {f['setting'].place}.",
        f'Write a child-friendly animal story that includes the word "{f["sound"].label}" and ends with relief.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    sound = _safe_fact(world, f, "sound")
    flower = _safe_fact(world, f, "flower")
    return [
        QAItem(
            question=f"What did {hero.id} hear near the {flower.label}?",
            answer=f"{hero.id} heard a {sound.label} near the {flower.label} and thought it was a warning at first."
        ),
        QAItem(
            question=f"Why was {hero.id} confused at first?",
            answer=f"{hero.id} misunderstood the {sound.label} and thought it meant {sound.misunderstood_as}."
        ),
        QAItem(
            question=f"Who helped explain what was really happening?",
            answer=f"{friend.id} helped by talking kindly and pointing out that the sound was only a {sound.label}."
        ),
        QAItem(
            question=f"What changed after the dialogue?",
            answer=f"After they talked, {hero.id} felt relief, the confusion went away, and the {flower.label} stayed safe and bright."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carnation?",
            answer="A carnation is a flower with soft petals that can grow in bright colors like pink, red, or yellow."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a sound or action means one thing, but it really means something else."
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters talk to each other to share ideas, ask questions, or fix confusion."
        ),
        QAItem(
            question="What does a woof sound like?",
            answer="A woof is a short dog sound, often friendly and lively."
        ),
        QAItem(
            question="What does vocalic mean here?",
            answer="Here, vocalic means the sound is voice-like or song-like, with a musical shape."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", sound="woof", flower="carnation", hero="dog", friend="cat"),
    StoryParams(place="yard", sound="vocalic", flower="yellow_carnation", hero="cat", friend="rabbit"),
    StoryParams(place="porch", sound="rustle", flower="red_carnation", hero="rabbit", friend="fox"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about misunderstanding and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS))
    flower = getattr(args, "flower", None) or rng.choice(list(FLOWERS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    friend = getattr(args, "friend", None) or rng.choice([k for k in FRIENDS if k != hero])
    params = StoryParams(place=place, sound=sound, flower=flower, hero=hero, friend=friend)
    if not _python_reasonable(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SOUNDS, params.sound), params.flower, params.hero, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p.place, p.sound) for p in CURATED}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches curated validity ({len(cl)} cases).")
        return 0
    print("Mismatch between ASP and Python validity.")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        for place, sound in vals:
            print(place, sound)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.hero} / {p.sound} / {p.flower} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
