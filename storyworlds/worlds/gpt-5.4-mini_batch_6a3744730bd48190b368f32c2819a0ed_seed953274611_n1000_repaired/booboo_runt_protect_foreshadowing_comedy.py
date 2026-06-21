#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/booboo_runt_protect_foreshadowing_comedy.py
============================================================================

A small comedy storyworld about a tiny mishap, a runt-sized hero, and a parent
who protects everyone just in time. The story uses foreshadowing: an early clue
about a wobbly ladder, a squeaky helmet, or a too-bright kite hints at the later
booboo before the rescue.

The domain is intentionally tiny and state-driven:
- a child wants to do a silly task
- a smaller runt companion notices an early warning
- a harmless comedy setup hints at the mishap
- a small booboo happens
- a grown-up protects the child and turns the moment into a laugh

The required seed words are woven in naturally:
- booboo
- runt
- protect

The style is child-facing comedy, with a gentle ending image proving what changed.
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
BRAVE_INIT = 5.0


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    action: str
    laugh_line: str
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


@dataclass
class Prop:
    id: str
    label: str
    hint: str
    foreshadow: str
    risky: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mishap:
    id: str
    label: str
    cause: str
    effect: str
    severity: int
    comedic: str
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


@dataclass
class Protection:
    id: str
    label: str
    method: str
    power: int
    punchline: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_boooboo(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mishap_done"):
        key = ("booboo",)
        if key not in world.fired:
            world.fired.add(key)
            child = world.get("child")
            child.meters["booboo"] += 1
            child.memes["surprise"] += 1
            out.append("__booboo__")
    return out


def _r_protect(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("need_protect") and not world.facts.get("protected"):
        key = ("protect",)
        if key not in world.fired:
            world.fired.add(key)
            parent = world.get("parent")
            child = world.get("child")
            parent.memes["care"] += 1
            child.memes["safe"] += 1
            world.facts["protected"] = True
            out.append("__protect__")
    return out


CAUSAL_RULES = [Rule("booboo", _r_boooboo), Rule("protect", _r_protect)]


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


def reasonableness_gate(setting: Setting, prop: Prop, mishap: Mishap, protection: Protection) -> bool:
    return setting.id in SETTINGS and prop.id in PROPS and mishap.id in MISHAPS and protection.id in PROTECTIONS


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPS.items():
            for mid, mishap in MISHAPS.items():
                for rid, protection in PROTECTIONS.items():
                    if prop.risky and mishap.severity <= protection.power:
                        combos.append((sid, pid, mid, rid))
    return combos


def predict(world: World, mishap: Mishap) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["booboo"] += 1
    return {"booboo": child.meters["booboo"] >= THRESHOLD}


def setup(world: World, child: Entity, runt: Entity, parent: Entity, setting: Setting, prop: Prop) -> None:
    child.memes["joy"] += 1
    runt.memes["curious"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {runt.id} went to {setting.place}. "
        f"{setting.detail} {setting.laugh_line}"
    )
    world.say(
        f"{child.id} wanted to play with {prop.label}, and {runt.id} -- the little runt -- "
        f"watched with wide eyes."
    )


def foreshadow(world: World, runt: Entity, prop: Prop, mishap: Mishap) -> None:
    runt.memes["worry"] += 1
    world.say(
        f'{runt.id} pointed at the {prop.label} and said, "That wobbly thing looks like '
        f'it could cause a {mishap.label}."'
    )
    world.say(
        f"Nobody laughed right away, which is how everyone knew the joke was hiding a clue."
    )


def silly_attempt(world: World, child: Entity, prop: Prop) -> None:
    child.memes["brave"] += 1
    world.say(
        f'{child.id} grinned. "I can handle it," {child.pronoun()} said, '
        f"and reached for the {prop.label}."
    )


def mishap_beats(world: World, child: Entity, prop: Prop, mishap: Mishap) -> None:
    world.facts["mishap_done"] = True
    child.meters["booboo"] += 1
    child.memes["oops"] += 1
    world.say(
        f"Then the {prop.label} went sideways with a silly little flop. "
        f"{mishap.comedic} {mishap.effect}."
    )


def alarm(world: World, runt: Entity, child: Entity) -> None:
    world.say(f'"{child.id}! {child.id}!" {runt.id} squeaked. "That looked like a booboo waiting to happen!"')


def protect_scene(world: World, parent: Entity, child: Entity, protection: Protection, mishap: Mishap) -> None:
    parent.memes["care"] += 1
    world.facts["need_protect"] = True
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} came over at once and {protection.method}. "
        f"It was so fast that the whole thing turned into a joke instead of a disaster."
    )
    world.say(
        f"{mishap.label.capitalize()} faded into a tiny booboo, and {parent.label_word} gave "
        f"{child.id} a hug, a clean cloth, and one very dramatic eyebrow raise."
    )


def end_image(world: World, child: Entity, runt: Entity, prop: Prop, protection: Protection) -> None:
    world.say(
        f"After that, {child.id} kept the {prop.label} steady, {runt.id} kept watch, "
        f"and {protection.label} stayed nearby in case the comedy tried a sequel."
    )
    world.say(
        f"This time, there was no crash -- just {child.id}, {runt.id}, and one safe laugh."
    )


def tell(setting: Setting, prop: Prop, mishap: Mishap, protection: Protection,
         child_name: str = "Nina", child_gender: str = "girl",
         runt_name: str = "Pip", runt_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    runt = world.add(Entity(id=runt_name, kind="character", type=runt_gender, role="runt"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="setting", type="place", label=setting.place))
    world.add(Entity(id="prop", type="thing", label=prop.label))
    world.add(Entity(id="mishap", type="thing", label=mishap.label))
    world.add(Entity(id="protection", type="thing", label=protection.label))

    setup(world, child, runt, parent, setting, prop)
    world.para()
    foreshadow(world, runt, prop, mishap)
    silly_attempt(world, child, prop)
    world.para()
    alarm(world, runt, child)
    mishap_beats(world, child, prop, mishap)
    protect_scene(world, parent, child, protection, mishap)
    world.para()
    end_image(world, child, runt, prop, protection)

    world.facts.update(
        child=child, runt=runt, parent=parent, setting=setting, prop=prop,
        mishap=mishap, protection=protection, protected=True, mishap_done=True
    )
    return world


SETTINGS = {
    "yard": Setting(
        id="yard",
        place="the backyard",
        detail="The grass was shiny from an earlier sprinkle, and a toy bucket sat upside down like a tiny hat.",
        action="balance",
        laugh_line="A garden gnome looked like it was trying very hard not to giggle.",
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        detail="The floor was clean enough to slide a spoon on, which is a ridiculous but true fact.",
        action="stack",
        laugh_line="Even the fridge seemed to be holding its breath.",
    ),
    "garage": Setting(
        id="garage",
        place="the garage",
        detail="The shelves leaned just a little, as if they were also telling a joke.",
        action="reach",
        laugh_line="A bicycle bell gave a cheerful ding at exactly the wrong moment.",
    ),
}

PROPS = {
    "chair": Prop(
        id="chair",
        label="wobbly chair",
        hint="chair",
        foreshadow="one leg was shorter than the others",
        risky=True,
    ),
    "ladder": Prop(
        id="ladder",
        label="tippy ladder",
        hint="ladder",
        foreshadow="it swayed every time someone looked at it",
        risky=True,
    ),
    "box": Prop(
        id="box",
        label="squeaky box",
        hint="box",
        foreshadow="it made a tiny squeal before anyone touched it",
        risky=False,
    ),
}

MISHAPS = {
    "stumble": Mishap(
        id="stumble",
        label="stumble",
        cause="a silly toe catch",
        effect="down went the child with a bonk and a puff of dust",
        severity=1,
        comedic="The chair made a gasp that sounded exactly like an old goose.",
    ),
    "bonk": Mishap(
        id="bonk",
        label="bonk",
        cause="a clumsy reach",
        effect="there was a soft bonk, then a very offended silence",
        severity=2,
        comedic="The ladder wobbled so hard it seemed to apologize in advance.",
    ),
}

PROTECTIONS = {
    "helmet": Protection(
        id="helmet",
        label="helmet",
        method="slipped a helmet on the child's head and steadied the ladder",
        power=2,
        punchline="The helmet looked proud of itself.",
    ),
    "cushion": Protection(
        id="cushion",
        label="cushion",
        method="stuffed a cushion under the wobbly side and held the child back",
        power=1,
        punchline="The cushion fluffed up like a heroic cloud.",
    ),
    "blanket": Protection(
        id="blanket",
        label="blanket",
        method="threw a blanket over the awkward corner and caught the wobble before it could be funny",
        power=2,
        punchline="Even the blanket looked smug.",
    ),
}

@dataclass
class StoryParams:
    setting: str
    prop: str
    mishap: str
    protection: str
    child_name: str = "Nina"
    child_gender: str = "girl"
    runt_name: str = "Pip"
    runt_gender: str = "boy"
    parent_type: str = "mother"
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


CURATED = [
    StoryParams(
        setting="yard", prop="chair", mishap="stumble", protection="helmet",
        child_name="Nina", child_gender="girl", runt_name="Pip", runt_gender="boy",
        parent_type="mother"
    ),
    StoryParams(
        setting="garage", prop="ladder", mishap="bonk", protection="blanket",
        child_name="Milo", child_gender="boy", runt_name="Dot", runt_gender="girl",
        parent_type="father"
    ),
]


def explain_rejection(params: StoryParams) -> str:
    prop = PROPS[params.prop]
    mishap = MISHAPS[params.mishap]
    protection = PROTECTIONS[params.protection]
    if not prop.risky:
        return f"(No story: {prop.label} does not give the kind of foreshadowing that leads to a funny booboo.)"
    if protection.power < mishap.severity:
        return f"(No story: {protection.label} is too small to protect against this mishap.)"
    return "(No story: this combination is not reasonable for the tiny comedy domain.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that includes the words "booboo", '
        f'"runt", and "protect".',
        f"Tell a comedy story where {f['runt'].id} notices an early clue before {f['child'].id} "
        f"gets a tiny booboo, and a grown-up protects them in time.",
        f"Write a foreshadowing story in a playful style about a wobbly object, a runt-sized warning, and a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, runt, parent = f["child"], f["runt"], f["parent"]
    prop, mishap, protection = f["prop"], f["mishap"], f["protection"]
    return [
        ("Who was the story about?",
         f"It was about {child.id}, {runt.id}, and {parent.label_word}. The tiny runt noticed trouble early, which gave the comedy its clue."),
        ("What clue foreshadowed the booboo?",
         f"The {prop.label} kept wobbling and looked like it could cause a {mishap.label}. That warning came before anything went wrong, so it was foreshadowing."),
        ("What did the parent do?",
         f"{parent.label_word.capitalize()} came over and {protection.method}. That protected {child.id} and turned the mishap into a harmless laugh."),
        ("How did the story end?",
         f"It ended with everyone safe and smiling. {child.id} kept steady, {runt.id} kept watch, and the joke stayed small instead of becoming a bigger accident."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is foreshadowing?",
         "Foreshadowing is when a story gives a small clue early so readers can guess that something will happen later."),
        ("What does protect mean?",
         "Protect means to keep someone or something safe from harm or trouble."),
        ("What is a runt?",
         "A runt is the smallest one in a group, and in stories that can make the runt funny, brave, or especially observant."),
        ("What is a booboo?",
         "A booboo is a small hurt, like a tiny bump or scrape. It is not a big injury, just the kind that makes a child say, 'Ow!'"),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
risky_prop(P) :- prop(P), risky(P).
protects(R) :- protection(R), power(R, P), mishap_severity(M), P >= M.
valid(S,P,M,R) :- setting(S), prop(P), mishap(M), protection(R), risky(P), protects(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.risky:
            lines.append(asp.fact("risky", pid))
    for mid, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        lines.append(asp.fact("mishap_severity", mishap.severity))
    for rid, protection in PROTECTIONS.items():
        lines.append(asp.fact("protection", rid))
        lines.append(asp.fact("power", rid, protection.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python gates differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with foreshadowing, a runt, and a protect beat.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--protection", choices=PROTECTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--runt-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.mishap is None or c[2] == args.mishap)
              and (args.protection is None or c[3] == args.protection)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, mid, rid = rng.choice(sorted(combos))
    return StoryParams(
        setting=sid,
        prop=pid,
        mishap=mid,
        protection=rid,
        child_name=args.child_name or rng.choice(["Nina", "Milo", "Tia", "Owen", "Bea"]),
        child_gender="girl" if (args.child_name in {"Nina", "Tia", "Bea"}) else rng.choice(["girl", "boy"]),
        runt_name=args.runt_name or rng.choice(["Pip", "Dot", "Bean", "Midge"]),
        runt_gender=rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.prop not in PROPS or params.mishap not in MISHAPS or params.protection not in PROTECTIONS:
        raise StoryError("Invalid StoryParams.")
    setting = SETTINGS[params.setting]
    prop = PROPS[params.prop]
    mishap = MISHAPS[params.mishap]
    protection = PROTECTIONS[params.protection]
    if not reasonableness_gate(setting, prop, mishap, protection):
        raise StoryError(explain_rejection(params))
    world = tell(
        setting=setting,
        prop=prop,
        mishap=mishap,
        protection=protection,
        child_name=params.child_name,
        child_gender=params.child_gender,
        runt_name=params.runt_name,
        runt_gender=params.runt_gender,
        parent_type=params.parent_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
