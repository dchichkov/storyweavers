#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/puff_conflict_fairy_tale.py
===========================================================

A standalone story world for a tiny Fairy Tale domain built from the seed word
"puff" and the feature "Conflict".

Core premise:
- A young fairy tale hero wants to use a small puff charm to deal with a problem.
- A careful companion warns that the puff charm is not a safe or honest fix.
- A conflict follows: the hero may listen, or may try the charm and make a mess.
- A calm grown-up or old helper resolves the situation with a safer fairy-tale
  method, and the ending image proves what changed.

The world is constraint-checked, state-driven, and includes a Python reasonableness
gate plus an inline ASP twin.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/puff_conflict_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/puff_conflict_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/puff_conflict_fairy_tale.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/puff_conflict_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVE_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    gentle: bool = False
    magical: bool = False
    thorny: bool = False
    openable: bool = False
    locked: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch"}
        male = {"boy", "father", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    scene: str
    backdrop: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    where: str
    effect: str
    power: int
    sense: int
    magical: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Blocker:
    id: str
    label: str
    needs: set[str]
    covers: set[str]
    text: str
    fail: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_fallout(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["puff_scatter"] < THRESHOLD:
            continue
        sig = ("scatter", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["worry"] += 1
        out.append("__scatter__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("fallout", "physical", _r_fallout)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_use(charm: Trouble, blocker: Blocker) -> bool:
    return charm.magical and blocker.sense >= SENSE_MIN and blocker.power >= charm.power


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for tr in TROUBLES.values():
            for bl in BLOCKERS.values():
                if tr.magical and can_use(tr, bl):
                    combos.append((setting, tr.id, bl.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    trouble: str
    blocker: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    ruler: str
    delay: int = 0
    hero_age: int = 6
    companion_age: int = 7
    relation: str = "siblings"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def use_puff(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["defiance"] += 1
    hero.meters["puff_scatter"] += trouble.power
    world.say(
        f"{hero.id} took a tiny breath and tried a puff charm. "
        f'The air went "puff," and {trouble.label} swirled where {trouble.where}.'
    )
    propagate(world, narrate=False)


def setup(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"Once upon a time, in {setting.scene}, {hero.id} and {companion.id} "
        f"made a little game of royal errands. {setting.backdrop}"
    )


def premise(world: World, hero: Entity, companion: Entity, trouble: Trouble) -> None:
    world.say(
        f"They needed to open a small problem in the fairy-tale way. "
        f"{companion.id} peered at the trouble and said, "
        f'"Maybe we should not use a puff charm for that."'
    )
    world.say(
        f'{hero.id} looked at the {trouble.label} and whispered, '
        f'"But puff makes things move."'
    )


def warn(world: World, companion: Entity, hero: Entity, trouble: Trouble, blocker: Blocker) -> None:
    companion.memes["caution"] += 1
    world.say(
        f'{companion.id} bit {companion.pronoun("possessive")} lip. '
        f'"A puff can scatter {trouble.label}, and {blocker.label} needs a gentler '
        f"kind of help. Let's think first."
    )


def refuse_or_push(world: World, hero: Entity, companion: Entity, trouble: Trouble, blocker: Blocker) -> bool:
    if companion.age > hero.age and companion.memes["caution"] + 1 > BRAVE_INIT:
        world.say(
            f'{companion.id} stood in front of {hero.id}. '
            f'"No puff today," {companion.id} said, and {hero.id} sighed and stepped back.'
        )
        return True
    world.say(f'{hero.id} shook {hero.id.lower() and ""}')
    world.say(f'{hero.id} did not wait any longer.')
    return False


def trigger_conflict(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I can do it!" {hero.id} said. {companion.id} frowned, and the little game '
        f"turned into a real conflict."
    )


def response_scene(world: World, ruler: Entity, response: Response, trouble: Trouble, blocker: Blocker) -> None:
    body = response.text.replace("{target}", blocker.label)
    world.say(
        f"{ruler.label_word.capitalize()} came from the doorway and {body}."
    )
    world.say(
        f"The trouble settled, and the {blocker.label} was safe again."
    )


def lesson(world: World, ruler: Entity, hero: Entity, companion: Entity, trouble: Trouble) -> None:
    for e in (hero, companion):
        e.memes["relief"] += 1
        e.memes["love"] += 1
        e.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {ruler.label_word.capitalize()} knelt down and smiled. "
        f'"Puff is not the answer for everything," {ruler.pronoun()} said, '
        f'"but you did the right thing by calling me."'
    )
    world.say(f'"We promise," whispered {hero.id} and {companion.id}.')
    world.say(
        f"After that, they chose a softer way to fix the problem, and the room felt calm again."
    )


def safe_ending(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"The next morning, {hero.id} and {companion.id} were still in {setting.scene}, "
        f"but now they carried patience instead of a puff charm."
    )
    world.say(
        f"They walked under {setting.backdrop.lower()} with the problem solved the gentle way."
    )


def dangerous_fallout(world: World, ruler: Entity, trouble: Trouble, blocker: Blocker) -> None:
    world.get("room").meters["mess"] += 1
    world.get("room").meters["puff_scatter"] += 1
    world.say(
        f"The puff charm was too strong. It blew {trouble.label} all over the room "
        f"and made a bigger mess than anyone expected."
    )
    world.say(
        f"{ruler.label_word.capitalize()} had to sweep the glittering bits aside before {blocker.label} could be fixed."
    )


SETTINGS = {
    "castle": Setting("castle", "a castle hall with high windows", "The banners hung still, and the stone floor shone in the light."),
    "forest": Setting("forest", "a moonlit forest path", "The trees leaned close, as if listening."),
    "cottage": Setting("cottage", "a cozy cottage room", "A tiny fire crackled by the hearth."),
}

TROUBLES = {
    "briar": Trouble("briar", "briar gate", "at the gate", "open", 2, 3, True, {"briar", "magic"}),
    "dust": Trouble("dust", "sleeping dust", "around the old shelf", "wake", 2, 3, True, {"dust", "magic"}),
    "fog": Trouble("fog", "foggy curtain", "over the path", "clear", 3, 4, True, {"fog", "magic"}),
}

BLOCKERS = {
    "door": Blocker("door", "garden door", {"open"}, {"open"}, "open the garden door", "open the garden door with a key", 3, 3, {"door"}),
    "lantern": Blocker("lantern", "lantern room", {"wake"}, {"wake"}, "wake the lantern room", "wake the lantern room with a song", 2, 2, {"lantern"}),
    "path": Blocker("path", "forest path", {"clear"}, {"clear"}, "clear the forest path", "clear the forest path with a broom", 4, 4, {"path"}),
}

RESPONSES = {
    "key": Response("key", 3, 4, "turned a silver key and opened the {target} the proper way", "fumbled with a silver key, but it was too late", "turned a silver key and opened the {target} the proper way", {"key"}),
    "song": Response("song", 3, 3, "sang a steady song until the trouble settled into place", "sang, but the trouble only swirled harder", "sang a steady song until the trouble settled into place", {"song"}),
    "broom": Response("broom", 2, 4, "used a broom and swept the trouble gently aside", "swung a broom, but the trouble would not move", "used a broom and swept the trouble gently aside", {"broom"}),
}

GIRL_NAMES = ["Ella", "Mira", "Nora", "Tess", "Luna", "Ada"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Robin", "Hugo", "Jasper"]


def valid_pairing(trouble: Trouble, blocker: Blocker) -> bool:
    return trouble.magical and blocker.power >= trouble.power and blocker.sense >= SENSE_MIN


def explain_rejection(trouble: Trouble, blocker: Blocker) -> str:
    return f"(No story: a puff charm would not reasonably solve the {trouble.label} with {blocker.label}.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", age=params.hero_age, attrs={"relation": params.relation}))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion", age=params.companion_age, attrs={"relation": params.relation}))
    ruler = world.add(Entity(id="Queen", kind="character", type=params.ruler, role="ruler"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    trouble = world.add(Entity(id="trouble", type="trouble", label=TROUBLES[params.trouble].label, magical=True))
    blocker = world.add(Entity(id="blocker", type="blocker", label=BLOCKERS[params.blocker].label, openable=True, locked=True))

    setup(world, hero, companion, SETTINGS[params.setting])
    world.para()
    premise(world, hero, companion, TROUBLES[params.trouble])
    warn(world, companion, hero, TROUBLES[params.trouble], BLOCKERS[params.blocker])
    world.para()

    use_puff(world, hero, TROUBLES[params.trouble])
    trigger_conflict(world, hero, companion)

    if params.delay > 0:
        dangerous_fallout(world, ruler, TROUBLES[params.trouble], BLOCKERS[params.blocker])
    world.para()

    response_scene(world, ruler, RESPONSES[params.response], TROUBLES[params.trouble], BLOCKERS[params.blocker])
    lesson(world, ruler, hero, companion, TROUBLES[params.trouble])
    world.para()
    safe_ending(world, hero, companion, SETTINGS[params.setting])

    world.facts.update(
        hero=hero, companion=companion, ruler=ruler, setting=SETTINGS[params.setting],
        trouble=TROUBLES[params.trouble], blocker=BLOCKERS[params.blocker],
        response=RESPONSES[params.response], delay=params.delay,
        outcome="resolved", conflict=True, puffed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Fairy Tale story for a young child that includes the word "puff" and a small conflict about {f["trouble"].label}.',
        f"Tell a gentle fairy tale where {f['hero'].id} wants to use puff magic, but {f['companion'].id} argues against it and a queen helps resolve the problem.",
        f'Write a story with the word "puff" where a tiny magical mistake turns into a conflict, then ends safely and kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    ruler = f["ruler"]
    trouble = f["trouble"]
    blocker = f["blocker"]
    response = f["response"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id} and {companion.id}, who were caught up in a small fairy-tale conflict. {ruler.label_word.capitalize()} helped them finish the problem kindly."
        ),
        QAItem(
            question=f"What did {hero.id} try to do?",
            answer=f"{hero.id} tried to use a puff charm on the {trouble.label}. That choice made the conflict worse because the charm was not the safest way to fix it."
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{ruler.label_word.capitalize()} used {response.qa_text.replace('{target}', blocker.label)}. That calmer method settled the trouble without leaving the room in a bigger mess."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does puff sound like?",
            answer="Puff sounds like a soft little burst of air. In stories, it can mean a spell, a breath, or something small blowing away."
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is when characters want different things or disagree about what to do. It gives the story a problem that must be solved."
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a magical story with castles, helpers, and a problem to solve. It often ends with a kind lesson or a safe happy ending."
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.magical:
            lines.append(asp.fact("magical", tid))
        lines.append(asp.fact("power", tid, t.power))
        lines.append(asp.fact("sense", tid, t.sense))
    for bid, b in BLOCKERS.items():
        lines.append(asp.fact("blocker", bid))
        lines.append(asp.fact("power", bid, b.power))
        lines.append(asp.fact("sense", bid, b.sense))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, T, B) :- setting(S), trouble(T), blocker(B), magical(T), power(B, P), power(T, Q), P >= Q.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == {r for r in RESPONSES if RESPONSES[r].sense >= SENSE_MIN}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams("castle", "briar", "door", "key", "Ella", "girl", "Finn", "boy", "queen", 0, 7, 8, "siblings"),
    StoryParams("forest", "fog", "path", "broom", "Nora", "girl", "Owen", "boy", "king", 1, 6, 5, "friends"),
    StoryParams("cottage", "dust", "lantern", "song", "Mira", "girl", "Hugo", "boy", "witch", 0, 5, 7, "siblings"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world about puff, conflict, and a safe resolution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--blocker", choices=BLOCKERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--ruler", choices=["queen", "king", "witch", "wizard"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.blocker is None or c[2] == args.blocker)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, blocker = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero = args.hero or rng.choice(GIRL_NAMES := ["Ella", "Mira", "Nora", "Tess", "Luna", "Ada"])
    companion = args.companion or rng.choice(BOY_NAMES := ["Finn", "Owen", "Leo", "Robin", "Hugo", "Jasper"])
    ruler = args.ruler or rng.choice(["queen", "king", "witch", "wizard"])
    return StoryParams(setting, trouble, blocker, response, hero, "girl" if hero in GIRL_NAMES else "boy", companion, "boy", ruler, args.delay)


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
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, t, b in asp_valid_combos():
            print(f"{s:8} {t:8} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.companion}: {p.trouble} near {p.blocker} ({p.setting}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
