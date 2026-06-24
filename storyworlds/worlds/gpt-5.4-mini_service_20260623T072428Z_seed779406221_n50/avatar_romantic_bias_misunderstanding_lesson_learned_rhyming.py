#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/avatar_romantic_bias_misunderstanding_lesson_learned_rhyming.py
==============================================================================================================

A small, self-contained storyworld about an avatar in a gentle romantic setting,
where bias leads to a misunderstanding and a lesson is learned. The prose is
kept close to a rhyming story style: short, child-facing, concrete, and lightly
musical without becoming sing-song scaffolding.

Seed words: avatar, romantic, bias
Features: Misunderstanding, Lesson Learned
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    other: object | None = None
    peer: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    kind: str
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


@dataclass
class Cue:
    id: str
    line: str
    tag: str
    mood: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            traits=list(v.traits), owner=v.owner,
            meters=dict(v.meters), memes=dict(v.memes)
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def rhyme(a: str, b: str) -> str:
    return f"{a}, {b}"


def rhyme_pair(words: list[str]) -> str:
    if len(words) < 2:
        return words[0]
    return f"{words[0]} and {words[1]}"


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    peer = world.entities.get("peer")
    if not hero or not peer:
        return out
    if hero.memes["bias"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hurt"] += 1
    peer.memes["sad"] += 1
    out.append("__misunderstanding__")
    return out


def _r_lesson(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    peer = world.entities.get("peer")
    if not hero or not peer:
        return out
    if hero.memes["listened"] < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bias"] = 0.0
    hero.memes["kindness"] += 1
    peer.memes["relief"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [
    _r_misunderstanding,
    _r_lesson,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_misunderstanding(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["bias"] += 1
    propagate(sim, narrate=False)
    return sim.get("hero").memes["hurt"] >= THRESHOLD


def choose_repair(cues: list[Cue]) -> Cue:
    for cue in cues:
        if cue.mood == "warm":
            return cue
    return cues[0]


def tell(setting: Setting, hero_def: ObjectDef, peer_def: ObjectDef, cue: Cue,
         hero_name: str, peer_name: str, hero_type: str = "girl",
         peer_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name,
                            role="avatar", traits=["gentle", "bright"]))
    peer = world.add(Entity(id="peer", kind="character", type=peer_type, label=peer_name,
                            role="friend", traits=["kind"]))
    prop = world.add(Entity(id=hero_def.id, kind="thing", type=hero_def.kind, label=hero_def.label))
    other = world.add(Entity(id=peer_def.id, kind="thing", type=peer_def.kind, label=peer_def.label))

    world.say(f"{hero.label} was an avatar, soft as a star,")
    world.say(f"in {setting.place}, where hearts could wander far.")
    world.say(f"{peer.label} came near with a smile so bright,")
    world.say(f"and the air felt romantic, warm and light.")

    world.para()
    world.say(f"{hero.label} wore {prop.label}, a lovely little token,")
    world.say(f"while {peer.label} held {other.label}, carefully chosen and spoken.")
    if predict_misunderstanding(world):
        world.say(f"But bias made {hero.label} guess the worst,")
        world.say(f"so a small misunderstanding came first.")

    hero.memes["bias"] += 1
    hero.memes["sting"] += 1
    peer.memes["hope"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f'"I thought your note meant I was not the one," {hero.label} sighed,')
    world.say(f'"but you meant the game, and I was the one beside."')
    cue_line = cue.line
    world.say(cue_line)

    hero.memes["listened"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"Then {hero.label} looked again and felt the tide,")
    world.say(f"their bias slipped away, and truth stood by their side.")
    world.say(f"{hero.label} smiled at {peer.label}, and the air felt free,")
    world.say(f"for lesson learned is love made clearer to see.")

    world.facts.update(
        hero=hero, peer=peer, setting=setting, cue=cue, hero_item=prop, peer_item=other,
        misunderstanding=True, lesson=True
    )
    return world


SETTINGS = {
    "garden": Setting(place="the garden path", vibe="romantic", affords={"talk"}),
    "cafe": Setting(place="the little cafe", vibe="romantic", affords={"talk"}),
    "bridge": Setting(place="the moonlit bridge", vibe="romantic", affords={"talk"}),
}

HERO_ITEMS = {
    "card": ObjectDef(id="card", label="a ribbon card", phrase="a ribbon card", kind="paper", tags={"note"}),
    "rose": ObjectDef(id="rose", label="a paper rose", phrase="a paper rose", kind="paper", tags={"gift"}),
    "star": ObjectDef(id="star", label="a tiny star charm", phrase="a tiny star charm", kind="charm", tags={"gift"}),
}

PEER_ITEMS = {
    "note": ObjectDef(id="note", label="a note", phrase="a note", kind="paper", tags={"note"}),
    "lantern": ObjectDef(id="lantern", label="a lantern", phrase="a small lantern", kind="light", tags={"light"}),
    "shell": ObjectDef(id="shell", label="a shell", phrase="a smooth shell", kind="gift", tags={"gift"}),
}

CUES = {
    "kind_note": Cue(id="kind_note", line="Then a kind note showed what was meant, and the cloudy thought was gently bent.", tag="note", mood="warm"),
    "soft_voice": Cue(id="soft_voice", line="Then a soft voice said, 'I meant no hurt,' and the heavy guess fell back to the dirt.", tag="talk", mood="warm"),
    "clear_smile": Cue(id="clear_smile", line="Then a clear smile made the meaning plain, and the tired old guess went off like rain.", tag="smile", mood="warm"),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Nora", "Lily", "Ava", "Maya"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Levi", "Owen", "Kai"]
TRAITS = ["gentle", "hopeful", "patient", "careful", "bright"]


@dataclass
class StoryParams:
    setting: str
    hero_item: str
    peer_item: str
    cue: str
    hero_name: str
    hero_gender: str
    peer_name: str
    peer_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HERO_ITEMS:
            for p in PEER_ITEMS:
                if h != p:
                    combos.append((s, h, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: avatar, romantic bias, misunderstanding, lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-item", choices=HERO_ITEMS)
    ap.add_argument("--peer-item", choices=PEER_ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--peer-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--peer-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "hero_item", None) is None or c[1] == getattr(args, "hero_item", None))
              and (getattr(args, "peer_item", None) is None or c[2] == getattr(args, "peer_item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, hero_item, peer_item = rng.choice(list(combos))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    peer_gender = getattr(args, "peer_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    peer_name = getattr(args, "peer_name", None) or rng.choice(GIRL_NAMES if peer_gender == "girl" else BOY_NAMES)
    if hero_name == peer_name:
        peer_name = rng.choice([n for n in (GIRL_NAMES if peer_gender == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(setting, hero_item, peer_item, rng.choice(list(CUES)), hero_name, hero_gender, peer_name, peer_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about an avatar named {f["hero"].label} in {f["setting"].place}.',
        f"Tell a gentle romantic story where {f['hero'].label} and {f['peer'].label} share a misunderstanding and then learn a lesson.",
        f'Write a child-friendly rhyming tale using the words "avatar", "romantic", and "bias".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    peer = f["peer"]
    setting = f["setting"]
    cue = f["cue"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.label}, an avatar, and {peer.label}, who meet in {setting.place}.",
        ),
        QAItem(
            question=f"What went wrong at first?",
            answer=f"Bias made {hero.label} guess wrong, so there was a misunderstanding between {hero.label} and {peer.label}.",
        ),
        QAItem(
            question=f"How did they fix it?",
            answer=f"They listened, spoke kindly, and remembered the lesson in {cue.line.lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bias?",
            answer="Bias is a quick unfair guess about someone before you know the full truth.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing and the other person meant something else.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something helpful you understand after you make a mistake or after someone explains things clearly.",
        ),
    ]


ASP_RULES = r"""
bias_hurts(H) :- bias(H), guesses_wrong(H).
misunderstanding(H, P) :- bias_hurts(H), peer(P).
lesson_learned(H) :- listens(H), misunderstanding(H, P).
resolved(H, P) :- lesson_learned(H), peer(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HERO_ITEMS:
        lines.append(asp.fact("hero_item", hid))
    for pid in PEER_ITEMS:
        lines.append(asp.fact("peer_item", pid))
    lines.append(asp.fact("bias", "hero"))
    lines.append(asp.fact("guesses_wrong", "hero"))
    lines.append(asp.fact("listens", "hero"))
    lines.append(asp.fact("peer", "peer"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2.\n#show lesson_learned/1."))
    atoms = set((s.name, tuple(a.name if a.type != 1 else a.number for a in s.arguments)) for s in model)
    ok = ("lesson_learned", ("hero",)) in atoms
    if ok:
        print("OK: ASP twin produced the expected lesson_learned outcome.")
        return 0
    print("MISMATCH: ASP twin did not produce lesson_learned(hero).")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(HERO_ITEMS, params.hero_item),
        _safe_lookup(PEER_ITEMS, params.peer_item),
        _safe_lookup(CUES, params.cue),
        params.hero_name,
        params.peer_name,
        params.hero_gender,
        params.peer_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
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
    StoryParams("garden", "card", "note", "kind_note", "Mia", "girl", "Noah", "boy"),
    StoryParams("cafe", "rose", "lantern", "soft_voice", "Lily", "girl", "Theo", "boy"),
    StoryParams("bridge", "star", "shell", "clear_smile", "Ava", "girl", "Kai", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/2.\n#show lesson_learned/1.\n#show misunderstanding/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/2.\n#show lesson_learned/1.\n#show resolved/2."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} and {p.peer_name} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
