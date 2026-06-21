#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/manual_pesky_cypress_bad_ending_rhyming_story.py
=================================================================================

A small standalone storyworld about a child, a pesky problem, a cypress tree,
and a bad ending told in a rhyming-story style.

The world is intentionally tiny:
- a child finds a manual
- the manual suggests a risky fix
- a pesky little problem worsens the situation
- the cypress tree is harmed
- the ending is sad, concrete, and proves what changed

The script follows the shared storyworld contract:
- generates complete stories from simulated state
- exposes QA prompts grounded in world facts
- includes a Python reasonableness gate and an inline ASP twin
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Manual:
    id: str
    label: str
    risky_tool: bool = True
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
class Pest:
    id: str
    label: str
    way: str
    pesky: bool = True
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
class Cypress:
    id: str
    label: str
    bark: str
    branch: str
    can_bend: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
class StoryParams:
    manual: str
    pest: str
    cypress: str
    response: str
    child: str
    child_gender: str
    parent: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tree = world.get("cypress")
    pest = world.get("pest")
    if child.meters["risky_fix"] >= THRESHOLD and pest.meters["pesky"] >= THRESHOLD:
        sig = ("damage",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        tree.meters["scarred"] += 1
        tree.meters["lean"] += 1
        child.memes["panic"] += 1
        out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("damage", _r_damage)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for m in MANUALS:
        for p in PESTS:
            for c in CYPRESSES:
                if m.risky_tool and p.pesky and c.can_bend:
                    combos.append((m.id, p.id, c.id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_ok(manual: Manual, pest: Pest, cypress: Cypress) -> bool:
    return manual.risky_tool and pest.pesky and cypress.can_bend


def should_fail(response: Response, cypress: Cypress, delay: int) -> bool:
    severity = 1 + delay
    return response.power < severity


def predict_damage(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.get("child").meters["risky_fix"] += 1
    sim.get("pest").meters["pesky"] += 1
    propagate(sim, narrate=False)
    return {
        "damaged": sim.get("cypress").meters["scarred"] >= THRESHOLD,
        "panic": sim.get("child").memes["panic"],
    }


def intro(world: World, child: Entity, manual: Manual, pest: Pest, cypress: Cypress) -> None:
    world.say(
        f"{child.id} found a manual by the cypress in the morning light; "
        f"its little steps were neat and bright."
    )
    world.say(
        f"The manual said to fix the pesky thing fast, "
        f"so the day would be tidy, sturdy, and last."
    )
    world.say(
        f"But the pesky {pest.label} kept darting about, "
        f"and {cypress.label} stood close with a whispery pout."
    )


def choose(world: World, child: Entity, manual: Manual, pest: Pest) -> None:
    child.memes["curious"] += 1
    child.memes["bold"] += 1
    world.say(
        f'{child.id} nodded at the manual and said, "I know the way; '
        f"I'll fix this pesky problem today.""
    )


def act(world: World, child: Entity, manual: Manual, pest: Pest, cypress: Cypress) -> None:
    child.meters["risky_fix"] += 1
    pest.meters["pesky"] += 1
    world.say(
        f"{child.id} followed the manual, quick as a spark, "
        f"but the pesky little pest made the path hard and dark."
    )
    propagate(world, narrate=False)
    world.say(
        f"The cypress branch creaked with a thin little sigh, "
        f"and the bark got a scrape as the pest zipped by."
    )


def accident(world: World, child: Entity, pest: Pest, cypress: Cypress) -> None:
    cypress.meters["scarred"] += 1
    cypress.meters["lean"] += 1
    child.memes["fear"] += 1
    world.say(
        f"The branch bent low with a crack and a groan; "
        f"the cypress looked tired, like it had been thrown."
    )
    world.say(
        f"The pesky {pest.label} vanished away, "
        f"and {child.id} stood still in a pale, shaky gray."
    )


def ending_bad(world: World, child: Entity, parent: Entity, cypress: Cypress, manual: Manual) -> None:
    child.memes["sad"] += 1
    parent.memes["sad"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came slowly and saw the poor scene; "
        f"the cypress was bent, and its bark showed a sheen."
    )
    world.say(
        f'"The manual was meant to help," {parent.id} said low, '
        f'"but not every fast fix makes a safe place to grow."'
    )
    world.say(
        f"{child.id} hugged the manual, small and tight in hand, "
        f"while the cypress stayed crooked in the sleepy sand."
    )
    world.say(
        "So the day ended badly, with a hush and a frown; "
        "the tree was still scarred when the sun went down."
    )


def tell(manual: Manual, pest: Pest, cypress: Cypress, response: Response,
         child: str = "Mila", child_gender: str = "girl", parent: str = "mother",
         delay: int = 0) -> World:
    world = World()
    kid = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    grown = world.add(Entity(id="Parent", kind="character", type=parent, role="parent", label="the parent"))
    m = world.add(Entity(id="manual", type="thing", label=manual.label, tags=set(manual.tags)))
    p = world.add(Entity(id="pest", type="thing", label=pest.label, tags=set(pest.tags)))
    c = world.add(Entity(id="cypress", type="thing", label=cypress.label, tags=set(cypress.tags)))

    intro(world, kid, manual, pest, cypress)
    world.para()
    choose(world, kid, manual, pest)
    act(world, kid, manual, pest, cypress)

    if should_fail(response, cypress, delay):
        world.para()
        accident(world, kid, pest, cypress)
        world.para()
        ending_bad(world, kid, grown, cypress, manual)
        outcome = "bad"
    else:
        world.para()
        world.say(
            f"The fix held for a tiny, trembling bit, "
            f"but the cypress still drooped, not steady or fit."
        )
        ending_bad(world, kid, grown, cypress, manual)
        outcome = "bad"

    world.facts.update(
        child=kid,
        parent=grown,
        manual_cfg=manual,
        pest_cfg=pest,
        cypress_cfg=cypress,
        response=response,
        outcome=outcome,
        damaged=True,
        delay=delay,
    )
    return world


MANUALS = {
    "garden_manual": Manual(id="garden_manual", label="a garden manual", risky_tool=True, tags={"manual"}),
    "old_manual": Manual(id="old_manual", label="an old manual", risky_tool=True, tags={"manual"}),
}

PESTS = {
    "bird": Pest(id="bird", label="pesky bird", way="fluttering and pecking", pesky=True, tags={"pesky"}),
    "squirrel": Pest(id="squirrel", label="pesky squirrel", way="scrambling and nibbling", pesky=True, tags={"pesky"}),
    "bee": Pest(id="bee", label="pesky bee", way="buzzing and darting", pesky=True, tags={"pesky"}),
}

CYPRESSES = {
    "young": Cypress(id="young", label="young cypress", bark="smooth bark", branch="thin branch", can_bend=True, tags={"cypress"}),
    "tall": Cypress(id="tall", label="tall cypress", bark="striped bark", branch="low branch", can_bend=True, tags={"cypress"}),
}

RESPONSES = {
    "fumble": Response(id="fumble", sense=2, power=1, text="tried a careful fix", fail="tried a careful fix, but it slipped", tags={"fix"}),
    "patch": Response(id="patch", sense=3, power=2, text="patched the trouble for a moment", fail="patched the trouble for a moment, but not enough", tags={"fix"}),
}

SENSE_MIN = 2

CURATED = [
    StoryParams(manual="garden_manual", pest="squirrel", cypress="young", response="fumble", child="Mila", child_gender="girl", parent="mother"),
    StoryParams(manual="old_manual", pest="bee", cypress="tall", response="patch", child="Noah", child_gender="boy", parent="father"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a rhyming story for a young child that includes the words "manual", "pesky", and "cypress".',
        f"Tell a sad little rhyming story where {f['child'].id} follows a manual near a pesky problem and the cypress ends up harmed.",
        "Write a rhyming bad-ending story with a child, a manual, and a cypress tree, ending with a clear sad image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent = f["child"], f["parent"]
    cypress = f["cypress_cfg"]
    pest = f["pest_cfg"]
    manual = f["manual_cfg"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who found a {manual.label} near a {cypress.label}. The pesky {pest.label} made the day harder."),
        ("What did {child.id} try to do?",
         f"{child.id} tried to follow the manual and fix the pesky trouble fast. The plan seemed quick, but it was risky around the cypress."),
        ("What happened to the cypress?",
         f"The {cypress.label} got scarred and leaned over. The bad ending shows the tree was not the same after the fix."),
        ("How did the story end?",
         f"It ended badly, with the cypress bent and the child sad. The manual stayed in {child.id}'s hands, but the easy answer did not make a safe result."),
    ]
    if f.get("damaged"):
        qa.append((
            "Why was the ending bad?",
            f"The manual led {child.id} into a risky fix, and the pesky {pest.label} made it worse. The cypress was left scarred, so the day ended in a sad way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a manual?",
         "A manual is a book or guide that tells you how to do something step by step."),
        ("What does pesky mean?",
         "Pesky means annoying or hard to deal with, like a little trouble that keeps getting in the way."),
        ("What is a cypress?",
         "A cypress is a kind of tree with tall, elegant branches and bark that can look smooth or striped."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
manual_risky(M) :- manual(M).
pesky_problem(P) :- pest(P).
cypress_tree(C) :- cypress(C).

hazard(M, P, C) :- manual_risky(M), pesky_problem(P), cypress_tree(C).
bad_ending(M, P, C) :- hazard(M, P, C), response(R), sense(R,S), sense_min(Min), S >= Min.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for m in MANUALS:
        lines.append(asp.fact("manual", m))
    for p in PESTS:
        lines.append(asp.fact("pest", p))
    for c in CYPRESSES:
        lines.append(asp.fact("cypress", c))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
        lines.append(asp.fact("power", r, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/3."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming bad-ending storyworld with a manual, a pesky problem, and a cypress tree.")
    ap.add_argument("--manual", choices=MANUALS)
    ap.add_argument("--pest", choices=PESTS)
    ap.add_argument("--cypress", choices=CYPRESSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.manual is None or c[0] == args.manual)
              and (args.pest is None or c[1] == args.pest)
              and (args.cypress is None or c[2] == args.cypress)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    manual, pest, cypress = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Mila", "Noah", "Lena", "Owen"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(manual=manual, pest=pest, cypress=cypress, response=response,
                       child=child, child_gender=child_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.manual not in MANUALS or params.pest not in PESTS or params.cypress not in CYPRESSES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(MANUALS[params.manual], PESTS[params.pest], CYPRESSES[params.cypress],
                 RESPONSES[params.response], child=params.child, child_gender=params.child_gender, parent=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show hazard/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (manual, pest, cypress) triples:\n")
        for m, p, c in combos:
            print(f"  {m:12} {p:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
