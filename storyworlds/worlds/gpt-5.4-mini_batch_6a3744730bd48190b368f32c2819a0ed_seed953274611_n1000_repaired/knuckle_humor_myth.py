#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knuckle_humor_myth.py
=====================================================

A small myth-flavored storyworld about a boastful drummer-god, a stubborn
knuckle, and a very funny lesson about sharing credit.

Premise
-------
A child or apprentice wants to make an ancient ceremonial sound.
The sound depends on a knuckle-rattle instrument that is fussy, loud, and prone
to comic mistakes. A helper can warn, a trick can go wrong, and a clever fix can
turn embarrassment into a cheerful, legendary ending.

This world keeps the usual Storyweavers shape:
- typed entities with physical meters and emotional memes,
- a state-driven simulation rather than frozen prose,
- a reasonableness gate,
- inline ASP rules as a twin to the Python validity logic,
- prompts, story QA, and world-knowledge QA grounded in world state.

The default story is child-facing, humorous, and mythic in tone.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "goddess"}
        male = {"boy", "father", "dad", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Realm:
    id: str
    label: str
    style: str = "myth"
    humor: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Rattle:
    id: str
    label: str
    phrase: str
    sound: str
    comic: str
    sacred: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    risk: str
    severity: int = 1
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_laugh(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["comedy"] < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__laugh__")
    return out


def _r_pride_bump(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["pride"] < THRESHOLD:
            continue
        sig = ("pride_bump", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["embarrassment"] += 1
        out.append("__bump__")
    return out


CAUSAL_RULES = [Rule("laugh", "social", _r_laugh), Rule("pride_bump", "social", _r_pride_bump)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonableness_gate(realm: Realm, rattle: Rattle, trouble: Trouble, fix: Fix) -> bool:
    return realm.style == "myth" and rattle.sacred and trouble.severity <= fix.power and fix.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid, realm in REALMS.items():
        for tid, trouble in TROUBLES.items():
            for fid, fix in FIXES.items():
                for rid2, rattle in RATTLES.items():
                    if reasonableness_gate(realm, rattle, trouble, fix):
                        combos.append((rid, tid, fid))
    return combos


def _build_sound(world: World, child: Entity, rattle: Rattle) -> None:
    child.meters["comedy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"In the bright dawn of {world.facts['realm'].label}, {child.id} sought "
        f"{rattle.phrase} so the old stories might wake."
    )
    world.say(
        f'The elders whispered that only a true hero could draw forth {rattle.sound}, '
        f'but the instrument was as mischievous as a cat in a temple.'
    )


def _warn(world: World, helper: Entity, child: Entity, trouble: Trouble) -> None:
    helper.memes["wisdom"] += 1
    world.say(
        f'{helper.id} peered at the sacred thing and said, "Careful! If you strike '
        f'it the wrong way, {trouble.risk}."'
    )


def _boast(world: World, child: Entity, rattle: Rattle) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I can do it," said {child.id}, flexing a brave knuckle and grinning like '
        f'a sunrise. "Watch this ancient miracle!"'
    )


def _fumble(world: World, child: Entity, rattle: Rattle) -> None:
    child.meters["comedy"] += 1
    child.memes["embarrassment"] += 1
    world.say(
        f"Then {child.id} tapped the {rattle.label} with a knuckle, and it answered "
        f"with the wrong kind of thunder. The sound went BONK instead of {rattle.sound}."
    )
    propagate(world, narrate=False)


def _fix(world: World, helper: Entity, child: Entity, fix: Fix, trouble: Trouble) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} laughed kindly and showed a better way: {fix.method}."
    )
    world.say(
        f"Together they used {fix.phrase}, and the bad omen of {trouble.label} faded "
        f"like a shadow at noon."
    )


def _lesson(world: World, child: Entity, helper: Entity, rattle: Rattle) -> None:
    child.memes["humility"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} bowed to the music and said, 'I thought the knuckle was the hero, "
        f"but the joke was on me.'"
    )
    world.say(
        f'{helper.id} smiled. "A good story can be funny and still teach," {helper.pronoun()} said.'
    )
    world.say(
        f"And so the little myth ended with laughter, and the {rattle.label} sang "
        f"properly at last."
    )


def tell(realm: Realm, rattle: Rattle, trouble: Trouble, fix: Fix,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Aunt Iris", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.facts["realm"] = realm
    world.facts["rattle"] = rattle
    world.facts["trouble"] = trouble
    world.facts["fix"] = fix

    _build_sound(world, child, rattle)
    world.para()
    _warn(world, helper, child, trouble)
    _boast(world, child, rattle)
    _fumble(world, child, rattle)
    world.para()
    _fix(world, helper, child, fix, trouble)
    _lesson(world, child, helper, rattle)

    world.facts.update(child=child, helper=helper, outcome="resolved")
    return world


REALMS = {
    "mountain": Realm(id="mountain", label="the Mountain Court", tags={"mountain", "myth"}),
    "river": Realm(id="river", label="the River Hall", tags={"river", "myth"}),
    "cloud": Realm(id="cloud", label="the Cloud Gate", tags={"cloud", "myth"}),
}

RATTLES = {
    "bone": Rattle(id="bone", label="bone rattle", phrase="the bone rattle", sound="KRAK-krill", comic="bone"),
    "shell": Rattle(id="shell", label="shell rattle", phrase="the shell rattle", sound="SHIM-sham", comic="shell"),
    "stone": Rattle(id="stone", label="stone rattle", phrase="the stone rattle", sound="CLACK-laugh", comic="stone"),
}

TROUBLES = {
    "echo": Trouble(id="echo", label="echo trouble", phrase="echo trouble", risk="the mountain would answer back with silly echoes", severity=1),
    "snort": Trouble(id="snort", label="snort trouble", phrase="snort trouble", risk="the cave spirits would snort and giggle", severity=1),
    "stumble": Trouble(id="stumble", label="stumble trouble", phrase="stumble trouble", risk="everyone would wobble and look wobbly", severity=1),
}

FIXES = {
    "two_hand": Fix(id="two_hand", label="two-hand tap", phrase="a careful two-hand tap", method="tap it with both hands and a steady breath", power=2, sense=3),
    "song": Fix(id="song", label="song-count", phrase="a counting song and a gentle beat", method="sing a count before the strike", power=2, sense=3),
    "glove": Fix(id="glove", label="soft glove", phrase="a soft glove wrapped around the knuckles", method="wrap the knuckle in a soft glove and strike lightly", power=2, sense=2),
}

GIRL_NAMES = ["Nia", "Iris", "Luna", "Mara", "Sera"]
BOY_NAMES = ["Milo", "Tavi", "Joren", "Pax", "Orin"]


@dataclass
class StoryParams:
    realm: str
    rattle: str
    trouble: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic comedy for a child about {f["child"].id} and the {f["rattle"].label}.',
        f"Tell a humorous legend where a knuckle makes a sacred sound go wrong, and then a helper teaches a better way.",
        f'Write a myth-style story that includes the word "knuckle" and ends with laughter and a lesson.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, rattle, trouble, fix = f["child"], f["helper"], f["rattle"], f["trouble"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who wanted to awaken the old sound, and {helper.id}, who helped in the end."),
        ("What went wrong with the sacred instrument?",
         f"{child.id} hit the {rattle.label} with a knuckle, and it made a silly BONK instead of the right sound. The mistake turned the brave moment into a joke."),
        ("How did the story end?",
         f"{helper.id} showed {fix.method}, so the trouble faded and the story ended in laughter. The ending proves that the child learned a gentler way."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a knuckle?",
         "A knuckle is one of the bumpy joints in your fingers. You can bend your fingers because the knuckles help them move."),
        ("Why can humor help a myth?",
         "Humor makes a myth feel friendly and memorable. A funny mistake can also teach a lesson without making the story scary."),
        ("What is a myth?",
         "A myth is an old story that explains a world, a custom, or a special power. Myths often feel grand, magical, and larger than life."),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(realm="mountain", rattle="bone", trouble="echo", fix="two_hand", child_name="Milo", child_gender="boy", helper_name="Aunt Iris", helper_gender="woman"),
    StoryParams(realm="river", rattle="shell", trouble="snort", fix="song", child_name="Nia", child_gender="girl", helper_name="Uncle Sol", helper_gender="man"),
    StoryParams(realm="cloud", rattle="stone", trouble="stumble", fix="glove", child_name="Tavi", child_gender="boy", helper_name="Grandmother", helper_gender="woman"),
]


def explain_rejection() -> str:
    return "(No story: the chosen mix does not make a sensible mythic comedy.)"


def valid_combo(params: StoryParams) -> bool:
    try:
        realm = REALMS[params.realm]
        rattle = RATTLES[params.rattle]
        trouble = TROUBLES[params.trouble]
        fix = FIXES[params.fix]
    except KeyError:
        return False
    return reasonableness_gate(realm, rattle, trouble, fix)


ASP_RULES = r"""
valid(R, T, F) :- realm(R), trouble(T), fix(F), rattle(X), myth_realm(R), sacred(X), severity(T,S), power(F,P), P >= S.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in REALMS.items():
        lines.append(asp.fact("realm", rid))
        if "myth" in r.tags:
            lines.append(asp.fact("myth_realm", rid))
    for rid, r in RATTLES.items():
        lines.append(asp.fact("rattle", rid))
        if r.sacred:
            lines.append(asp.fact("sacred", rid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("severity", tid, t.severity))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    c = set(asp_valid_combos())
    p = set(valid_combos_for_all())
    if c != p:
        print("MISMATCH in ASP and Python validity.")
        if c - p:
            print(" only in clingo:", sorted(c - p))
        if p - c:
            print(" only in python:", sorted(p - c))
        return 1
    # smoke test
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    print(f"OK: ASP parity and story smoke test passed ({len(c)} combos).")
    return 0


def valid_combos_for_all() -> list[tuple[str, str, str]]:
    out = []
    for r in REALMS:
        for t in TROUBLES:
            for f in FIXES:
                if reasonableness_gate(REALMS[r], next(iter(RATTLES.values())), TROUBLES[t], FIXES[f]):
                    out.append((r, t, f))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic humor storyworld about a knuckle and a comic sacred sound.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--rattle", choices=RATTLES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["man", "woman"])
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
    realm = args.realm or rng.choice(sorted(REALMS))
    rattle = args.rattle or rng.choice(sorted(RATTLES))
    trouble = args.trouble or rng.choice(sorted(TROUBLES))
    fix = args.fix or rng.choice(sorted(FIXES))
    params = StoryParams(
        realm=realm,
        rattle=rattle,
        trouble=trouble,
        fix=fix,
        child_name=args.child_name or rng.choice(GIRL_NAMES + BOY_NAMES),
        child_gender=args.child_gender or rng.choice(["boy", "girl"]),
        helper_name=args.helper_name or rng.choice(["Aunt Iris", "Uncle Sol", "Grandmother"]),
        helper_gender=args.helper_gender or rng.choice(["woman", "man"]),
    )
    if not valid_combo(params):
        raise StoryError(explain_rejection())
    return params


def generate(params: StoryParams) -> StorySample:
    for key in ("realm", "rattle", "trouble", "fix"):
        if key not in params.__dict__:
            raise StoryError("invalid params")
    world = tell(
        REALMS[params.realm],
        RATTLES[params.rattle],
        TROUBLES[params.trouble],
        FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
