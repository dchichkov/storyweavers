#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/arrival_paddy_rhyme_rhyming_story.py
======================================================================

A standalone story world for a tiny rhyming tale about an arrival day and a
muddy paddy path.

Premise
-------
A child is excited about the arrival of a friendly visitor named Paddy. The
child wants to rush outside to welcome Paddy, but the yard has a slick paddy of
mud and a loose gate. A calm grown-up makes a sensible fix: they wait by the
porch, bring a towel and boots, and greet the visitor safely. The ending proves
what changed by showing the muddy path cleaned and the welcome made warm.

The story is intentionally small, classical, and state-driven, with rhyming
pairs woven into the prose.
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Visitor:
    id: str
    label: str
    arrival_sound: str
    gift: str
    cheerful: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    messy: bool = True
    slippery: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Fix:
    id: str
    label: str
    do: str
    end: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    visitor: str
    trouble: str
    fix: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_mud(world: World) -> list[str]:
    out = []
    if world.get("path").meters["mud"] >= THRESHOLD and ("mud_alert",) not in world.fired:
        world.fired.add(("mud_alert",))
        world.get("path").meters["slip"] += 1
        world.get("child").memes["worry"] += 1
        out.append("__mud__")
    return out


def _r_wait(world: World) -> list[str]:
    out = []
    if world.get("child").memes["calm"] >= THRESHOLD and ("wait_calm",) not in world.fired:
        world.fired.add(("wait_calm",))
        world.get("porch").meters["safe"] += 1
        out.append("__wait__")
    return out


CAUSAL_RULES = [Rule("mud", "physical", _r_mud), Rule("wait", "social", _r_wait)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combo(visitor: Visitor, trouble: Trouble, fix: Fix) -> bool:
    return trouble.messy and trouble.slippery and fix.sense >= SENSE_MIN


def arrival_risk(trouble: Trouble) -> bool:
    return trouble.slippery or trouble.messy


def fix_enough(fix: Fix, trouble: Trouble) -> bool:
    return fix.power >= (2 if trouble.slippery else 1)


def outcome_of(params: StoryParams) -> str:
    fix = FIXES[params.fix]
    trouble = TROUBLES[params.trouble]
    if not valid_combo(VISITORS[params.visitor], trouble, fix):
        return "invalid"
    return "safe" if fix_enough(fix, trouble) else "messy"


def _do_visitor(world: World, visitor: Visitor, narrate: bool = True) -> None:
    world.get("guest").attrs["arrived"] = True
    world.get("child").memes["joy"] += 1
    world.get("guest").memes["joy"] += 1
    world.say(f"Then came the arrival of {visitor.label}, bright as a day in the sun.")
    world.say(f"{visitor.arrival_sound} -- the door gave a little sway.")


def _do_trouble(world: World, trouble: Trouble, narrate: bool = True) -> None:
    world.get("path").meters["mud"] += 1
    world.get("path").attrs["trouble"] = trouble.id
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, visitor: Visitor) -> None:
    world.say(
        f"{child.id} sat by the window with a grin so wide, "
        f"for today held the arrival of {visitor.label} from far outside."
    )
    world.say(
        f"The yard had a paddy of mud by the gate, dark and slick from the rain, "
        f"and that little mess made the welcome wait."
    )


def worry(world: World, child: Entity, parent: Entity, trouble: Trouble) -> None:
    child.memes["eager"] += 1
    child.memes["calm"] += 1
    world.say(
        f'"I want to run right out!" {child.id} cried. "I want to play and not delay."'
    )
    world.say(
        f'{parent.id} nodded slow and said, "Not that way. That paddy is slick; '
        f'one quick step could slide and sway."'
    )


def predict(world: World) -> dict:
    sim = world.copy()
    _do_trouble(sim, TROUBLES[sim.facts["trouble"]], narrate=False)
    return {"slip": sim.get("path").meters["slip"]}


def choose_wait(world: World, parent: Entity, fix: Fix) -> None:
    parent.memes["care"] += 1
    world.say(
        f'{parent.id} smiled and made a clever rhyme: "{fix.do}, and then we '
        f"welcome {world.facts['visitor'].label} in good time."
    )


def rescue(world: World, parent: Entity, fix: Fix, visitor: Visitor) -> None:
    world.get("path").meters["mud"] = 0.0
    world.get("path").meters["slip"] = 0.0
    world.say(
        f"{parent.id} brought out {fix.label}, and the plan went right on cue."
    )
    world.say(
        f"{fix.end}. The gate stood still, the porch stayed dry, and the welcome "
        f"felt warm and true."
    )


def ending(world: World, child: Entity, visitor: Visitor) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} waved and laughed, and {visitor.label} waved back with cheer."
    )
    world.say(
        f"The muddy paddy was cleared away, and the arrival became the best part "
        f"of the year."
    )


def tell(visitor: Visitor, trouble: Trouble, fix: Fix,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.add(Entity(id="guest", kind="character", type="visitor", label=visitor.label))
    world.add(Entity(id="path", type="place", label="the path"))
    world.add(Entity(id="porch", type="place", label="the porch"))
    world.facts["visitor"] = visitor
    world.facts["trouble"] = trouble.id
    world.facts["fix"] = fix.id

    introduce(world, child, visitor)
    world.para()
    worry(world, child, parent, trouble)
    world.say(f"The {trouble.label} was too slick for little feet to trust.")
    world.para()
    choose_wait(world, parent, fix)
    _do_trouble(world, trouble)
    if fix_enough(fix, trouble):
        rescue(world, parent, fix, visitor)
        ending(world, child, visitor)
        world.facts["outcome"] = "safe"
    else:
        world.say("The fix was too small, and the splash grew tall.")
        world.say("They had to step back and wait inside, while the mud kept its squall.")
        world.facts["outcome"] = "messy"
    return world


VISITORS = {
    "paddy": Visitor("paddy", "Paddy", "Pat-a-pat!", "a paper kite", "cheerful", tags={"arrival", "paddy"}),
    "grandpa": Visitor("grandpa", "Grandpa Paddy", "Tap-tap!", "a tin whistle", "cheerful", tags={"arrival", "paddy"}),
    "pony": Visitor("pony", "Paddy the pony", "Clip-clop!", "a carrot treat", "cheerful", tags={"arrival", "paddy"}),
}

TROUBLES = {
    "mud": Trouble("mud", "paddy of mud", "mud", messy=True, slippery=True, tags={"mud", "paddy"}),
    "slush": Trouble("slush", "slush by the gate", "slush", messy=True, slippery=True, tags={"mud"}),
    "puddle": Trouble("puddle", "wide puddle", "puddle", messy=True, slippery=True, tags={"mud"}),
}

FIXES = {
    "boots_and_porch": Fix("boots_and_porch", "rain boots and the porch", "put on our boots and wait on the porch", "Soon the boots were on, and the porch was the safe place to be", 2, 3, tags={"boots"}),
    "towel_and_step": Fix("towel_and_step", "a towel and one careful step", "lay down a towel and take one careful step at a time", "The towel kept the floor dry, and no one slipped", 1, 2, tags={"towel"}),
    "gate_and_wait": Fix("gate_and_wait", "the gate latch and a warm wait", "latch the gate and wait a minute", "The gate stayed shut, and waiting made the moment sweet", 2, 2, tags={"gate"}),
}

CHOICE_ORDER = ["paddy", "grandpa", "pony"]
TROUBLE_ORDER = ["mud", "slush", "puddle"]
FIX_ORDER = ["boots_and_porch", "towel_and_step", "gate_and_wait"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for vid in VISITORS:
        for tid in TROUBLES:
            for fid in FIXES:
                if valid_combo(VISITORS[vid], TROUBLES[tid], FIXES[fid]):
                    combos.append((vid, tid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about an arrival and a muddy paddy.")
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
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
              if (args.visitor is None or c[0] == args.visitor)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    v, t, f = rng.choice(sorted(combos))
    return StoryParams("Mia", "girl", "Mom", "mother", v, t, f)


def generate(params: StoryParams) -> StorySample:
    world = tell(VISITORS[params.visitor], TROUBLES[params.trouble], FIXES[params.fix],
                 params.child, params.child_gender, params.parent, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "arrival" and "paddy".',
        f"Tell a gentle rhyme where {f['visitor'].label} arrives, a muddy paddy by the gate causes worry, and a grown-up makes a safe plan.",
        f'Write a small rhyming story where a child waits for the arrival of {f["visitor"].label} and chooses a careful fix for the paddy path.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    v = world.facts["visitor"]
    t = TROUBLES[world.facts["trouble"]]
    f = FIXES[world.facts["fix"]]
    return [
        ("Who arrived in the story?",
         f"{v.label} arrived, and everyone was glad to see {v.label}."),
        ("What was the paddy like?",
         f"It was a muddy paddy by the gate, and it was slick enough to make little feet slip."),
        ("How did they keep things safe?",
         f"They chose {f.label} and waited on the porch. That kept the welcome dry and calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["visitor"].tags) | set(world.facts["trouble"].tags) | set(world.facts["fix"].tags)
    qa = []
    if "arrival" in tags:
        qa.append(("What does arrival mean?",
                   "Arrival means the moment when someone gets there. It is the time a visitor comes in.")) 
    if "paddy" in tags:
        qa.append(("What is a paddy of mud?",
                   "A paddy of mud is a patch of muddy ground. It can be slippery and messy to walk through."))
    if "boots" in tags:
        qa.append(("What are rain boots for?",
                   "Rain boots help keep feet dry when the ground is wet or muddy."))
    if "gate" in tags:
        qa.append(("What does a gate latch do?",
                   "A gate latch keeps the gate closed so it does not swing open by itself."))
    return qa


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,T,F) :- visitor(V), trouble(T), fix(F), messy(T), slippery(T), sense(F,S), sense_min(M), S >= M.
safe(T,F) :- trouble(T), fix(F), power(F,P), need(T,N), P >= N.
outcome(safe) :- valid(_,T,F), safe(T,F).
outcome(messy) :- valid(_,T,F), not safe(T,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("messy", tid))
        lines.append(asp.fact("slippery", tid))
        lines.append(asp.fact("need", tid, 2))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen", params.visitor), asp.fact("chosen_t", params.trouble), asp.fact("chosen_f", params.fix)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    sample = generate(resolve_params(argparse.Namespace(visitor=None, trouble=None, fix=None), random.Random(7)))
    if not sample.story:
        print("MISMATCH: generation failed")
        rc = 1
    if rc == 0:
        print("OK")
    return rc


CURATED = [
    StoryParams("Mia", "girl", "Mom", "mother", "paddy", "mud", "boots_and_porch"),
    StoryParams("Noah", "boy", "Dad", "father", "grandpa", "slush", "gate_and_wait"),
    StoryParams("Luna", "girl", "Mom", "mother", "pony", "puddle", "towel_and_step"),
]


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
        print("\n".join(str(x) for x in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "arrival" and "paddy".',
        f"Tell a gentle rhyme where {f['visitor'].label} arrives, a muddy paddy by the gate causes worry, and a grown-up makes a safe plan.",
        f'Write a small rhyming story where a child waits for the arrival of {f["visitor"].label} and chooses a careful fix for the paddy path.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    v = world.facts["visitor"]
    f = FIXES[world.facts["fix"]]
    return [
        ("Who arrived in the story?",
         f"{v.label} arrived, and everyone was glad to see {v.label}."),
        ("What was the paddy like?",
         "It was a muddy paddy by the gate, and it was slick enough to make little feet slip."),
        ("How did they keep things safe?",
         f"They chose {f.label} and waited on the porch. That kept the welcome dry and calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["visitor"].tags) | set(world.facts["trouble"].tags) | set(world.facts["fix"].tags)
    qa = []
    if "arrival" in tags:
        qa.append(("What does arrival mean?", "Arrival means the moment when someone gets there. It is the time a visitor comes in."))
    if "paddy" in tags:
        qa.append(("What is a paddy of mud?", "A paddy of mud is a patch of muddy ground. It can be slippery and messy to walk through."))
    if "boots" in tags:
        qa.append(("What are rain boots for?", "Rain boots help keep feet dry when the ground is wet or muddy."))
    if "gate" in tags:
        qa.append(("What does a gate latch do?", "A gate latch keeps the gate closed so it does not swing open by itself."))
    return qa
if __name__ == "__main__":
    main()
