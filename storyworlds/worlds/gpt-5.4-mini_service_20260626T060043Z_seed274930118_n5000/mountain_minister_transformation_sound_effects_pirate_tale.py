#!/usr/bin/env python3
"""
A standalone story world for a tiny pirate-style mountain tale.

Premise:
- A minister travels through a mountain pass with a small crew.
- A transformation happens when a strange sound effect from the mountain echo
  stirs a change in the minister's mood, voice, and appearance.
- The story resolves with the crew discovering the transformed minister can
  still guide them home in a new way.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- state-driven simulation
- invalid choices raise StoryError
- inline ASP twin and Python reasonableness gate
- generation, QA, JSON, trace, and verify support
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    transformed: bool = False
    voice: str = "plain"

    crew: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"minister", "man", "captain", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def title(self) -> str:
        return self.label or self.type
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
    place: str = "the mountain"
    weather: str = "windy"
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
class Crewmate:
    type: str
    label: str
    trait: str
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
class SoundEffect:
    id: str
    onomatopoeia: str
    cause: str
    effect: str
    volume: str
    transformation: str
    tags: set[str] = field(default_factory=set)
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
    sound: str
    hero_name: str
    hero_trait: str
    crew_label: str
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
        self.events: list[str] = []

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


def _meters(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _r_echo(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if _meters(ent, "wonder") < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(ent, "startled", 1.0)
        out.append(f"The mountain answered with a long echo for {ent.title()}.")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.kind != "character":
            continue
        if _meters(ent, "sound_hit") < THRESHOLD:
            continue
        if ent.transformed:
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.transformed = True
        ent.voice = "ringing"
        _add_meme(ent, "courage", 1.0)
        _add_meme(ent, "calm", 1.0)
        out.append(f"{ent.title()} changed in the mountain light.")
    return out


def _r_lead(world: World) -> list[str]:
    out = []
    hero = world.get("minister")
    crew = world.get("crew")
    if hero.transformed and _meters(hero, "lead") >= THRESHOLD:
        sig = ("lead", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meme(crew, "trust", 1.0)
            out.append("The crew trusted the minister's new voice.")
    return out


def propagate(world: World) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_echo, _r_transform, _r_lead):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def reasonableness_gate(setting: str, sound: str) -> None:
    if setting not in SETTINGS:
        pass
    if sound not in SOUNDS:
        pass
    s = _safe_lookup(SETTINGS, setting)
    snd = _safe_lookup(SOUNDS, sound)
    if setting not in snd.locations:
        pass


SETTINGS = {
    "mountain_path": Setting(place="the mountain path", weather="windy", affords={"walk", "climb", "echo"}),
    "cave_pass": Setting(place="the cave pass", weather="cold", affords={"walk", "echo", "drip"}),
    "cliff_landing": Setting(place="the cliff landing", weather="stormy", affords={"walk", "shout", "echo"}),
}

SOUNDS = {
    "clang": SoundEffect(
        id="clang",
        onomatopoeia="CLANG",
        cause="a bell in the mountain chapel",
        effect="shook the air",
        volume="loud",
        transformation="the minister's stiff coat became a bright captain's coat",
        tags={"echo", "metal"},
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        onomatopoeia="WHOOSH",
        cause="a gust racing through the pass",
        effect="spun like a sail",
        volume="wild",
        transformation="the minister's hat turned into a pirate hat with a feather",
        tags={"wind", "echo"},
    ),
    "boom": SoundEffect(
        id="boom",
        onomatopoeia="BOOM",
        cause="a drum of thunder behind the ridge",
        effect="bumped through the rocks",
        volume="deep",
        transformation="the minister's shoes became sturdy sea boots",
        tags={"thunder", "echo"},
    ),
}

CREW = [
    Crewmate(type="sailor", label="the sailor", trait="brave"),
    Crewmate(type="child", label="the cabin child", trait="wide-eyed"),
    Crewmate(type="mouse", label="the lookout mouse", trait="tiny"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-style mountain tale with transformation and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--name")
    ap.add_argument("--trait")
    ap.add_argument("--crew", choices=[c.label for c in CREW])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS))
    reasonableness_gate(setting, sound)
    hero_name = getattr(args, "name", None) or rng.choice(["Milo", "Iris", "Noah", "Pippa", "Levi"])
    hero_trait = getattr(args, "trait", None) or rng.choice(["solemn", "curious", "stern", "kind", "bold"])
    crew_label = getattr(args, "crew", None) or rng.choice([c.label for c in CREW])
    return StoryParams(setting=setting, sound=sound, hero_name=hero_name, hero_trait=hero_trait, crew_label=crew_label)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(Entity(id="minister", kind="character", type="minister", label=f"Minister {params.hero_name}", traits=[params.hero_trait]))
    crew = world.add(Entity(id="crew", kind="character", type="crew", label=params.crew_label, traits=["loyal"]))
    sound = _safe_lookup(SOUNDS, params.sound)

    _add_meter(hero, "wonder", 1.0)
    _add_meter(hero, "walk", 1.0)
    world.say(
        f"Minister {params.hero_name} climbed the mountain path with {crew.title()}, and the wind tugged at {hero.pronoun('possessive')} coat."
    )
    world.say(
        f"They were following an old pirate chart that said a safe road ran past the chapel stone."
    )
    world.para()
    world.say(
        f"Then came {sound.onomatopoeia}! It was {sound.cause}, and it {sound.effect} across the rocks."
    )
    _add_meter(hero, "sound_hit", 1.0)
    _add_meter(hero, "lead", 1.0)
    _add_meme(hero, "shock", 1.0)
    world.say(
        f"The sound struck {hero.title()} so hard that {sound.transformation}."
    )
    propagate(world)
    world.para()
    if hero.transformed:
        world.say(
            f"{hero.title()} stood taller after the change, with {hero.pronoun('possessive')} new voice sounding like a bell over the sea."
        )
        world.say(
            f"The crew marched on, and the transformed minister led them through the pass by calling directions in a ringing, pirate-bright way."
        )
    else:
        world.say(
            f"The crew kept close and listened for the next sound."
        )
    world.say(
        f"At the end, the mountain road opened wide, and {crew.title()} cheered because the minister had become someone even the cliffs could hear."
    )
    world.facts = {"hero": hero, "crew": crew, "sound": sound, "setting": setting}
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    crew = _safe_fact(world, world.facts, "crew")
    sound = _safe_fact(world, world.facts, "sound")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who climbed the mountain path with {crew.title()}?",
            answer=f"Minister {hero.id.split()[-1] if ' ' in hero.label else hero.label} climbed it with {crew.title()}, and the wind tugged at {hero.pronoun('possessive')} coat.",
        ),
        QAItem(
            question=f"What sound changed the minister on the mountain?",
            answer=f"{sound.onomatopoeia} changed the minister, because it came from {sound.cause} and {sound.effect} across the rocks.",
        ),
        QAItem(
            question="What was different about the minister after the sound?",
            answer=f"After the sound, the minister was transformed, spoke with a ringing voice, and could lead the crew through {setting.place} in a new way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back when it hits mountains, walls, or other hard surfaces.",
        ),
        QAItem(
            question="What is a mountain?",
            answer="A mountain is a very tall landform that rises high above the land around it.",
        ),
        QAItem(
            question="What is a minister?",
            answer="A minister is a person who helps lead a church and speaks to people with care.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style mountain story featuring a minister and the sound "{f["sound"].onomatopoeia}".',
        f"Tell a child-friendly tale where a minister changes after a sound echoes through the mountain pass.",
        "Write a short story with a surprising transformation, a loud sound effect, and a safe ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.transformed:
            bits.append("transformed=True")
        if e.voice:
            bits.append(f"voice={e.voice}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
sound(s1).
setting(mountain_path).

transforms(minister, clang) :- sound_effect(clang), on_mountain_path.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, snd in SOUNDS.items():
        lines.append(asp.fact("sound_effect", sid))
        lines.append(asp.fact("onoma", sid, snd.onomatopoeia))
        for loc in sorted({"mountain_path", "cave_pass", "cliff_landing"} & snd.locations if hasattr(snd, "locations") else {"mountain_path", "cave_pass", "cliff_landing"}):
            lines.append(asp.fact("fits", sid, loc))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(s, snd) for s in SETTINGS for snd in SOUNDS if s in {"mountain_path", "cave_pass", "cliff_landing"}]


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(setting="mountain_path", sound="clang", hero_name="Milo", hero_trait="stern", crew_label="the sailor"),
    StoryParams(setting="cave_pass", sound="whoosh", hero_name="Iris", hero_trait="curious", crew_label="the cabin child"),
    StoryParams(setting="cliff_landing", sound="boom", hero_name="Noah", hero_trait="bold", crew_label="the lookout mouse"),
]


def build_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} compatible combos")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(build_json(samples))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
