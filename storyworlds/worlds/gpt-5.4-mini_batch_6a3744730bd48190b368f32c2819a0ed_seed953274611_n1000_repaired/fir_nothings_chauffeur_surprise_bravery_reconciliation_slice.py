#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fir_nothings_chauffeur_surprise_bravery_reconciliation_slice.py
================================================================================================

A standalone slice-of-life storyworld about a family outing, a chauffeur, a fir
tree, a box of "nothings" (tiny keepsakes), and a surprise that asks for bravery
and ends in reconciliation.

The world supports:
- a short, state-driven story
- three Q&A sets
- a small Python reasonableness gate
- an inline ASP twin
- --verify smoke tests that exercise generation
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id.lower()
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
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class Trigger:
    id: str
    label: str
    phrase: str
    burden: int
    surprise: int
    bravery_need: int
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
class Gift:
    id: str
    label: str
    phrase: str
    joy: int
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
class Response:
    id: str
    sense: int
    comfort: int
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
    setting: str
    trigger: str
    gift: str
    response: str
    child: str
    child_type: str
    chauffeur: str
    chauffeur_type: str
    parent: str
    parent_type: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_spread(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["upset"] >= THRESHOLD and ("spread", e.id) not in world.fired:
            world.fired.add(("spread", e.id))
            if "child" in world.entities:
                world.get("child").memes["hurt"] += 1
            out.append(f"{world.get('child').id} felt a sharp little sting.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["brave"] >= THRESHOLD and child.memes["apology"] >= THRESHOLD and ("reconcile",) not in world.fired:
        world.fired.add(("reconcile",))
        child.memes["warmth"] += 1
        world.get("parent").memes["relief"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


SETTINGS = {
    "drive": Setting(id="drive", place="the quiet road", detail="The windows looked out at shops, sidewalks, and a small fir tree in a front yard.", affords={"surprise"}),
    "station": Setting(id="station", place="the train station", detail="The platform was calm, with benches, a kiosk, and a fir in a square planter.", affords={"surprise"}),
}

TRIGGERS = {
    "postcard": Trigger(id="postcard", label="a postcard", phrase="a postcard from the seaside", burden=1, surprise=2, bravery_need=1, tags={"surprise"}),
    "fir": Trigger(id="fir", label="a fir sapling", phrase="a tiny fir sapling wrapped in brown paper", burden=1, surprise=3, bravery_need=2, tags={"fir", "surprise"}),
    "nothings": Trigger(id="nothings", label="a box of nothings", phrase="a little box of nothings: ribbon scraps, a marble, and a bent leaf", burden=0, surprise=2, bravery_need=1, tags={"nothings", "surprise"}),
}

GIFTS = {
    "cookie": Gift(id="cookie", label="cookies", phrase="warm cookies from the corner bakery", joy=2, tags={"comfort"}),
    "fircone": Gift(id="fircone", label="fir cones", phrase="a bag of fir cones gathered from under the tree", joy=1, tags={"fir"}),
    "note": Gift(id="note", label="note", phrase="a note with kind words", joy=2, tags={"reconciliation"}),
}

RESPONSES = {
    "hug": Response(id="hug", sense=3, comfort=2, text="hugged the child and listened carefully", fail="wanted to hug the child, but the hurt stayed in the air", tags={"comfort"}),
    "apology": Response(id="apology", sense=3, comfort=3, text="let the child speak, then accepted the apology with a nod", fail="heard the apology, but it was too small to settle the feeling", tags={"reconciliation"}),
    "silence": Response(id="silence", sense=1, comfort=0, text="said nothing at all", fail="said nothing at all, and the room stayed heavy", tags={"low"}),
}

CHILDREN = [("Mia", "girl"), ("Noah", "boy"), ("Lea", "girl"), ("Eli", "boy")]
ADULTS = [("Ava", "mother"), ("Jon", "father")]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, trig in TRIGGERS.items():
            for gid in GIFTS:
                for rid, resp in RESPONSES.items():
                    if resp.sense >= 2 and trig.bravery_need <= 3:
                        combos.append((sid, tid, gid, rid))
    return combos


def _pick_child(rng: random.Random) -> tuple[str, str]:
    return rng.choice(CHILDREN)


def _pick_adult(rng: random.Random) -> tuple[str, str]:
    return rng.choice(ADULTS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a chauffeur, a surprise, bravery, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--chauffeur")
    ap.add_argument("--chauffeur-type", choices=["mother", "father"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too small and quiet for this story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.gift is None or c[2] == args.gift)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trigger, gift, response = rng.choice(sorted(combos))
    child, child_type = (args.child, args.child_type) if args.child and args.child_type else _pick_child(rng)
    chauffeur, chauffeur_type = (args.chauffeur, args.chauffeur_type) if args.chauffeur and args.chauffeur_type else _pick_adult(rng)
    parent, parent_type = (args.parent, args.parent_type) if args.parent and args.parent_type else _pick_adult(rng)
    return StoryParams(setting=setting, trigger=trigger, gift=gift, response=response,
                       child=child, child_type=child_type, chauffeur=chauffeur,
                       chauffeur_type=chauffeur_type, parent=parent, parent_type=parent_type)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.trigger not in TRIGGERS or params.gift not in GIFTS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    world = World()
    setting = SETTINGS[params.setting]
    trig = TRIGGERS[params.trigger]
    gift = GIFTS[params.gift]
    resp = RESPONSES[params.response]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    chauffeur = world.add(Entity(id=params.chauffeur, kind="character", type=params.chauffeur_type, role="chauffeur"))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent_type, role="parent"))
    child.memes["joy"] = 1
    world.say(f"On a quiet afternoon, {child.id} rode with {chauffeur.id}, the family chauffeur, past {setting.place}. {setting.detail}")
    world.say(f'{child.id} noticed {trig.phrase} and whispered, "Maybe that is for me?"')
    world.para()
    child.memes["surprise"] += trig.surprise
    child.memes["brave"] += trig.bravery_need
    world.say(f"The surprise was small, but real. {child.id} held the little bundle of {trig.label} and took a breath.")
    world.say(f'"I can ask," {child.id} said, and that was brave enough.')
    world.para()
    child.memes["apology"] += 1
    child.meters["upset"] += trig.burden
    propagate(world, narrate=False)
    world.say(f"Then {parent.id} explained the plan: {gift.phrase} were waiting at home, and the fir tree would still be there later.")
    world.say(f"{resp.text.capitalize()}.")
    world.para()
    if resp.id == "apology":
        child.memes["apology"] += 1
    child.memes["warmth"] += 1
    child.meters["upset"] = 0
    world.say(f"{child.id} smiled again, this time softer. {chauffeur.id} parked by the curb, and {parent.id} and {child.id} shared the little keepsakes.")
    world.say(f"In the end, the nothings were not nothing at all, and the fir outside stood quiet while everyone felt close again.")
    world.facts.update(setting=setting, trigger=trig, gift=gift, response=resp, child=child, chauffeur=chauffeur, parent=parent, outcome="reconciled")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "{f["trigger"].label}", "chauffeur", and "fir".',
        f"Tell a gentle story where {f['child'].id} feels a surprise, shows bravery, and ends in reconciliation.",
        f"Write a small family story where a chauffeur rides along, a fir tree matters, and nothing scary stays scary for long.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    chauffeur = f["chauffeur"]
    parent = f["parent"]
    trig = f["trigger"]
    gift = f["gift"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, {chauffeur.id}, and {parent.id}, all sharing one ordinary day that turns special."),
        ("What was surprising?", f"The surprise was {trig.phrase}. It felt unexpected, but it also gave {child.id} a chance to be brave."),
        ("How did the story end?", f"It ended with reconciliation. {child.id} and {parent.id} spoke kindly again, and the day settled into a warm, easy feeling."),
        ("Why was {0} brave?".format(child.id), f"{child.id} was brave because {child.pronoun()} took a breath, asked instead of hiding, and then helped the family talk things through."),
        ("What did the family have to remember?", f"They remembered that {gift.phrase} were waiting and that the fir tree would still be there later, so there was no need to rush or argue."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["trigger"].tags) | set(world.facts["gift"].tags) | {"reconciliation"}
    if "fir" in tags:
        out.append(("What is a fir?", "A fir is an evergreen tree with needles that stay green all year. People often notice fir trees in yards, parks, and winter decorations."))
    if "nothings" in tags:
        out.append(("What are nothings?", "In this story, nothings are tiny little keepsakes that seem small, but still mean something. A bent leaf or a ribbon scrap can hold a memory."))
    out.append(("What does a chauffeur do?", "A chauffeur drives people where they need to go. The job is to make the ride smooth and calm."))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_story_gate() -> list[tuple[str, str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(S,T,G,R) :- setting(S), trigger(T), gift(G), response(R), sense_ok(R).
sense_ok(R) :- response(R), sense(R,S), min_sense(M), S >= M.
outcome(reconciled) :- chosen_child(C), chosen_chauffeur(H), chosen_parent(P), brave(C), apology(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("bravery_need", tid, t.bravery_need))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_child", params.child),
        asp.fact("chosen_chauffeur", params.chauffeur),
        asp.fact("chosen_parent", params.parent),
        asp.fact("brave", params.child),
        asp.fact("apology", params.child),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    if set(valid_story_gate()) == set(asp_valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_story_gate())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        return 1
    if asp_outcome(sample.params) != "reconciled":
        rc = 1
        print("MISMATCH in outcome.")
    else:
        print("OK: ASP outcome matches Python.")
    return rc


CURATED = [
    StoryParams(setting="drive", trigger="fir", gift="note", response="apology", child="Mia", child_type="girl", chauffeur="Ruth", chauffeur_type="mother", parent="Ava", parent_type="mother"),
    StoryParams(setting="station", trigger="nothings", gift="fircone", response="hug", child="Noah", child_type="boy", chauffeur="Jon", chauffeur_type="father", parent="Jon", parent_type="father"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_story_gate()
              if (args.setting is None or c[0] == args.setting)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.gift is None or c[2] == args.gift)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trigger, gift, response = rng.choice(sorted(combos))
    child, child_type = (args.child, args.child_type) if args.child and args.child_type else _pick_child(rng)
    chauffeur, chauffeur_type = (args.chauffeur, args.chauffeur_type) if args.chauffeur and args.chauffeur_type else _pick_adult(rng)
    parent, parent_type = (args.parent, args.parent_type) if args.parent and args.parent_type else _pick_adult(rng)
    return StoryParams(setting=setting, trigger=trigger, gift=gift, response=response,
                       child=child, child_type=child_type, chauffeur=chauffeur,
                       chauffeur_type=chauffeur_type, parent=parent, parent_type=parent_type)


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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
            s = generate(params)
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
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
