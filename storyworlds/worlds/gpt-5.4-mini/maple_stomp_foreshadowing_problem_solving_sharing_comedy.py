#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/maple_stomp_foreshadowing_problem_solving_sharing_comedy.py
==========================================================================================

A small standalone story world about a silly maple-day mix-up: a child wants to
make a grand snack, a warning foreshadows a mess, a problem gets solved with a
calm plan, and everyone ends by sharing the funny result.

This world is built to satisfy the Storyweavers contract:
- stdlib only
- eager results import
- typed entities with meters and memes
- world-driven prose
- story, prompts, story QA, and world QA
- Python and ASP reasonableness / parity checks
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    sticky: bool = False
    breakable: bool = False
    edible: bool = False
    sharable: bool = False
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    stage: str
    ambience: str
    affords: set[str] = field(default_factory=set)

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
class Prop:
    id: str
    label: str
    phrase: str
    use: str
    sparkle: str
    edible: bool = False
    sticky: bool = False
    breakable: bool = False
    sharable: bool = False
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
class Problem:
    id: str
    label: str
    cause: str
    sign: str
    severity: int
    fix_text: str
    fail_text: str
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
class Share:
    id: str
    label: str
    action: str
    ending: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["sticky"] < THRESHOLD:
            continue
        sig = ("sticky", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["alarm"] += 1
        out.append("__sticky__")
    return out


def _r_smirk(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("foreshadowed") and not world.facts.get("sticky_happened"):
        for c in world.characters():
            c.memes["anticipation"] += 1
        sig = ("smirk", "all")
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The room had a sneaky, syrupy feeling.")
    return out


CAUSAL_RULES = [Rule("sticky", "physical", _r_sticky), Rule("smirk", "social", _r_smirk)]


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


def hazard(problem: Problem, prop: Prop) -> bool:
    return problem.id in {"spilled_maple", "sticky_jar"} and prop.sticky


def sensible_fix(problem: Problem) -> bool:
    return FIXES[problem.id].sense >= SENSE_MIN


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str
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


def _do_problem(world: World, prop_ent: Entity, problem: Problem, narrate: bool = True) -> None:
    prop_ent.meters["sticky"] += 1
    world.facts["sticky_happened"] = True
    propagate(world, narrate=narrate)


def setup(world: World, kid: Entity, friend: Entity, setting: Setting, prop: Prop) -> None:
    kid.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {kid.id} and {friend.id} turned {setting.place} into a tiny stage. "
        f"{setting.stage} {setting.ambience}"
    )
    world.say(
        f'{kid.id} grinned. "{prop.label.capitalize()} day!" {kid.id} said, because the whole room smelled like a treat.'
    )


def foreshadow(world: World, kid: Entity, friend: Entity, prop: Prop, problem: Problem) -> None:
    world.facts["foreshadowed"] = True
    kid.memes["curiosity"] += 1
    world.say(
        f"{friend.id} noticed a little warning first: {problem.sign}. "
        f'"If that hits the {prop.label}, it will be a sticky parade," {friend.id} said.'
    )
    world.say(
        f"{kid.id} laughed, but the shiny jar sat there looking innocent, like it was waiting to misbehave."
    )


def tempt(world: World, kid: Entity, prop: Prop) -> None:
    kid.memes["impulse"] += 1
    world.say(
        f'{kid.id} tried to make the treat extra fancy and reached for the {prop.label}. '
        f'"Just one stomp and it will be perfect!" {kid.id} declared.'
    )


def problem_happens(world: World, prop_ent: Entity, problem: Problem) -> None:
    _do_problem(world, prop_ent, problem)
    world.say(
        f"Then came the {problem.cause}. The {prop_ent.label} went splat and made {problem.sign}."
    )


def explain(world: World, friend: Entity, kid: Entity, prop: Prop, problem: Problem) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} pointed at the mess and said, "See? I told you the {problem.label} would happen." '
        f'"We need a plan, not a panic stomp."'
    )


def solve(world: World, parent: Entity, kid: Entity, friend: Entity, prop: Prop, problem: Problem, fix: Fix) -> None:
    for c in (kid, friend):
        c.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in smiling and did not make a big speech. "
        f"{parent.pronoun().capitalize()} simply {fix.text}."
    )
    world.say(
        f"The sticky puddle settled down. The joke of the day was that the floor looked like a maple lake."
    )


def share(world: World, kid: Entity, friend: Entity, parent: Entity, prop: Prop, sh: Share) -> None:
    kid.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    world.say(
        f"{kid.id} took a breath, then shared the last {prop.label} with {friend.id}. "
        f'"Fair is fair," {kid.id} said, handing over a piece.'
    )
    world.say(
        f"{friend.id} nodded and {sh.ending}."
    )


def tell(setting: Setting, prop: Prop, problem: Problem, fix: Fix, sh: Share,
         kid_name: str = "Mina", kid_gender: str = "girl",
         friend_name: str = "Pip", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="instigator"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="cautioner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    prop_ent = world.add(Entity(id=prop.id, label=prop.label, sticky=prop.sticky, edible=prop.edible, sharable=prop.sharable))
    world.facts["fix"] = fix
    world.facts["share"] = sh

    setup(world, kid, friend, setting, prop)
    world.para()
    foreshadow(world, kid, friend, prop, problem)
    tempt(world, kid, prop)
    problem_happens(world, prop_ent, problem)
    explain(world, friend, kid, prop, problem)

    contained = fix.power >= problem.severity
    world.para()
    if contained:
        solve(world, parent, kid, friend, prop, problem, fix)
        world.para()
        share(world, kid, friend, parent, prop, sh)
        outcome = "solved"
    else:
        world.say(
            f"{parent.label_word.capitalize()} tried the plan, but the joke had already stomped too far."
        )
        world.say("Everyone still shared a towel and a laugh, because the day was ridiculous.")
        outcome = "failed"

    world.facts.update(
        kid=kid, friend=friend, parent=parent, prop=prop_ent, prop_cfg=prop,
        problem=problem, outcome=outcome, contained=contained, setting=setting
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the counter was set with a bowl and a spoon.", "The air smelled warm and sweet.", {"spill"}),
    "porch": Setting("porch", "the porch", "the porch had a tiny table and two wobbly chairs.", "The wind made everything feel extra dramatic.", {"spill"}),
    "picnic": Setting("picnic", "the picnic blanket", "the blanket was spread out under a maple tree.", "Leaves ticked like little jokes from above.", {"spill"}),
}

PROPS = {
    "maple_jar": Prop("maple_jar", "maple jar", "a maple jar", "sweetening snack", "shiny", edible=True, sticky=True, sharable=True, tags={"maple"}),
    "syrup_bottle": Prop("syrup_bottle", "maple syrup bottle", "a maple syrup bottle", "pouring snack", "gleaming", edible=True, sticky=True, sharable=True, tags={"maple"}),
    "pancake_stack": Prop("pancake_stack", "pancake stack", "a pancake stack", "breakfast snack", "golden", edible=True, sharable=True, tags={"maple"}),
}

PROBLEMS = {
    "spilled_maple": Problem("spilled_maple", "maple spill", "a clumsy bump", "a sticky maple puddle", 2, "wiped the spill with a towel and slid a plate under the jar", "wiped at the mess, but it was already too slippery", {"maple", "spill"}),
    "sticky_jar": Problem("sticky_jar", "sticky jar", "a joyful stomp", "sticky fingers on the floor", 3, "used a spoon, a napkin, and a small tray to keep the jar steady", "tried to clean it with a paper scrap, but the syrup kept spreading", {"maple", "spill"}),
}

FIXES = {
    "towel_tray": Fix("towel_tray", 3, 3, "wiped the spill with a towel and slid a plate under the jar", "wiped at the mess, but it was already too slippery", "wiped the spill with a towel and slid a plate under the jar", {"problem_solving"}),
    "spoon_napkin": Fix("spoon_napkin", 3, 3, "used a spoon, a napkin, and a small tray to keep the jar steady", "tried to clean it with a paper scrap, but the syrup kept spreading", "used a spoon, a napkin, and a small tray to keep the jar steady", {"problem_solving"}),
    "big_towel": Fix("big_towel", 2, 2, "threw a big towel over the slick spot and asked everyone to step like penguins", "threw a towel, but the syrup was already in charge", "threw a big towel over the slick spot", {"problem_solving"}),
}

SHARES = {
    "pieces": Share("pieces", "piece-sharing", "shared the treat in little pieces", "everyone ended up laughing with sticky happy mouths", {"sharing", "comedy"}),
    "half": Share("half", "half-sharing", "split the snack right down the middle", "both kids got the same silly syrupy smile", {"sharing", "comedy"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ava", "Tess", "Ruby"]
BOY_NAMES = ["Pip", "Owen", "Leo", "Sam", "Finn", "Toby"]
TRAITS = ["curious", "careful", "silly", "bright", "chatty"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPS.items():
            for prob in PROBLEMS.values():
                if hazard(prob, prop):
                    out.append((sid, pid, prob.id))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    prop: str
    problem: str
    fix: str
    share: str
    kid: str
    kid_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "maple" and "stomp".',
        f"Tell a comedy story where {f['kid'].id} and {f['friend'].id} almost make a maple mess, but solve the problem calmly and share the snack at the end.",
        f"Write a foreshadowing-and-fix story about a maple treat, a warning sign, a clever cleanup, and sharing the last bite.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, friend, parent = f["kid"], f["friend"], f["parent"]
    prop, problem, fix, sh = f["prop"], f["problem"], f["fix"], f["share"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {friend.id}, plus {parent.label_word}, who help with the maple snack."),
        ("What warning came before the mess?",
         f"{friend.id} noticed {problem.sign} before it got worse. That was the foreshadowing clue that made the joke land."),
        ("How did they solve the problem?",
         f"They used a calm plan: {fix.qa}. That stopped the sticky mess from taking over the whole scene."),
        ("What did they do at the end?",
         f"They shared the last {prop.label} and laughed together. The ending is funny because the mess turned into a snack story instead of a disaster."),
    ]
    if f["outcome"] == "solved":
        qa.append(("Why did the plan work?",
                   f"The fix was strong enough for the problem, so the syrup stayed where they could handle it. That let them clean up and still share the treat."))

    return qa


KNOWLEDGE = {
    "maple": [("What is maple syrup?",
               "Maple syrup is a sweet, sticky syrup made from maple tree sap. People pour it on pancakes and other treats.")],
    "stomp": [("What does stomp mean?",
               "To stomp means to step down hard with your foot. It makes a big thump, which can be funny in a story but messy near food.")],
    "spill": [("Why do sticky spills need help?",
              "Sticky spills spread and make the floor slippery. A towel, tray, or spoon can help keep the mess under control.")],
    "sharing": [("Why do people share snacks?",
                 "People share snacks so everyone gets some and nobody feels left out. Sharing can make a small treat feel happier.")],
    "problem_solving": [("What is problem solving?",
                           "Problem solving means noticing what went wrong and choosing a smart way to fix it. It is like using your brain before using your elbows.")],
}

KNOWLEDGE_ORDER = ["maple", "stomp", "spill", "problem_solving", "sharing"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["prop_cfg"].tags) | set(world.facts["problem"].tags) | set(world.facts["fix"].tags) | set(world.facts["share"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.sticky or e.breakable or e.edible or e.sharable:
            flags = [n for n, on in (("sticky", e.sticky), ("breakable", e.breakable), ("edible", e.edible), ("sharable", e.sharable)) if on]
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, prop: Prop) -> str:
    return f"(No story: {problem.label} needs a sticky prop like {prop.label} to make the foreshadowing and cleanup honest.)"


ASP_RULES = r"""
hazard(P, Pr) :- problem(P), prop(Pr), sticky(Pr).
valid(S, Pr, P) :- setting(S), prop(Pr), problem(P), hazard(P, Pr).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.sticky:
            lines.append(asp.fact("sticky", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy maple story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.problem and args.prop:
        if not hazard(PROBLEMS[args.problem], PROPS[args.prop]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], PROPS[args.prop]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, problem = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    share = args.share or rng.choice(sorted(SHARES))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if kid_gender == "girl" else "girl")
    kid = args.kid or rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != kid])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, prop, problem, fix, share, kid, kid_gender, friend, friend_gender, parent, trait)


CURATED = [
    StoryParams("kitchen", "maple_jar", "spilled_maple", "towel_tray", "pieces", "Mina", "girl", "Pip", "boy", "mother", "silly"),
    StoryParams("picnic", "syrup_bottle", "sticky_jar", "spoon_napkin", "half", "Lina", "girl", "Owen", "boy", "father", "curious"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], PROBLEMS[params.problem], FIXES[params.fix], SHARES[params.share],
                 params.kid, params.kid_gender, params.friend, params.friend_gender, params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for sid, prop, prob in asp_valid_combos():
            print(sid, prop, prob)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
