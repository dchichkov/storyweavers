#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stead_cautionary_rhyming_story.py
=================================================================

A small, cautionary, rhyming storyworld about a child at the steady old stead:
a curious child wants to sneak one last ride, ignores a careful warning, and
learns why a stead's gate, gear, and ledge all need respect. The world is tiny
and state-driven: physical meters track the stable, the gate, the path, the
bridge, and the pony; emotional memes track worry, pride, relief, and trust.

The story style aims to feel like a short rhyming tale for children. It keeps a
simple beat: premise, warning, turn, consequence, and a safe ending image that
proves what changed.
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    rhyme: str
    steady: bool = True
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
class Ride:
    id: str
    label: str
    phrase: str
    safe_speed: int
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
class Warning:
    id: str
    label: str
    rhyme: str
    caution_line: str
    lesson_line: str
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
class Result:
    id: str
    label: str
    fix: str
    lyric: str
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
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            traits=list(v.traits), attrs=dict(v.attrs),
            meters=defaultdict(float, v.meters), memes=defaultdict(float, v.memes),
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} / {b}"


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    rider = world.entities.get("rider")
    if not rider:
        return out
    if rider.meters["slipping"] < THRESHOLD:
        return out
    sig = ("slip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("path").meters["danger"] += 1
    rider.memes["fear"] += 1
    out.append("__slip__")
    return out


def _r_gate(world: World) -> list[str]:
    out: list[str] = []
    gate = world.entities.get("gate")
    if not gate or gate.meters["open"] < THRESHOLD:
        return out
    sig = ("gate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("stead").meters["risk"] += 1
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_slip, _r_gate):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_choose(choice: Ride, place: Place) -> bool:
    return place.steady and choice.safe_speed <= 2


def predict_trouble(world: World, choice: Ride) -> dict:
    sim = world.copy()
    _make_choice(sim, choice, narrate=False)
    return {
        "danger": sim.get("path").meters["danger"],
        "risk": sim.get("stead").meters["risk"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At the old {place.label}, {child.id} and {helper.id} were glad and bright; "
        f"the morning sun was soft and the breeze was light."
    )
    world.say(
        f"{child.id} loved the {place.label}, that steady old stead, "
        f"with warm brown boards and a little lane ahead."
    )


def want_ride(world: World, child: Entity, choice: Ride, place: Place) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I want one more ride," {child.id} said with a grin, '
        f'"along the path by the {place.rhyme} and back again."'
    )
    world.say(f"The {choice.label} waited by the door, small and neat.")


def warn(world: World, helper: Entity, child: Entity, warning: Warning, choice: Ride) -> None:
    pred = predict_trouble(world, choice)
    helper.memes["worry"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'"{warning.caution_line}," {helper.id} said, soft but clear; '
        f'"A fast little turn can bring a tear."'
    )
    world.say(
        f'"If you rush on the lane, the {choice.label} may slide, '
        f"and that is no game for a sunny ride."
    )


def defy(world: World, child: Entity, choice: Ride) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} felt bold, with a skip and a sway, '
        f'and hurried along to the path that day.'
    )
    world.say(
        f"{child.id} took the {choice.label} and tried to go fast, "
        f"but the wheel made a wobble that did not last."
    )


def _make_choice(world: World, choice: Ride, narrate: bool = True) -> None:
    rider = world.get("rider")
    rider.meters["slipping"] += 1
    world.get("gate").meters["open"] += 1
    world.get("path").meters["slick"] += 1
    propagate(world, narrate=narrate)


def accident(world: World, child: Entity, choice: Ride) -> None:
    _make_choice(world, choice)
    world.say(
        f"The {choice.label} skidded once, then gave a little spin; "
        f"the lane was too narrow for the speed within."
    )
    world.say(
        f"Down went the ride with a small, hard clack, "
        f"and {child.id} sat still, then looked back."
    )


def help_and_fix(world: World, helper: Entity, child: Entity, result: Result, place: Place) -> None:
    world.get("gate").meters["open"] = 0.0
    world.get("stead").meters["risk"] = 0.0
    world.get("path").meters["danger"] = 0.0
    child.memes["fear"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} came right over, calm as a tree, "
        f"and led {child.id} back carefully."
    )
    world.say(
        f"{helper.id} checked the {result.label} and mended the latch with care, "
        f"then shut the gate so it could stay there."
    )
    world.say(
        f'"{result.fix}," {helper.id} said, with a smile and a nod, '
        f'"so the {place.label} stays safe on the sod."'
    )
    world.say(
        f"Now the lane was quiet, the gate held tight, "
        f"and the steady old stead felt safe and right."
    )


def lesson(world: World, helper: Entity, child: Entity, warning: Warning) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{helper.id} hugged {child.id} and spoke so true: "
        f'"{warning.lesson_line}, and that is why we slow right through."'
    )
    world.say(
        f'"A careful start keeps a cheerful heart, '
        f"and smart small steps are the best part."'
    )


def tell(place: Place, choice: Ride, warning: Warning, result: Result,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Papa", helper_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="rider", label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", label="the helper"))
    world.add(Entity(id="stead", type="place", label="stead"))
    world.add(Entity(id="gate", type="thing", label="gate"))
    world.add(Entity(id="path", type="thing", label="path"))
    world.add(Entity(id="rider", type="thing", label=choice.label))
    world.facts["place"] = place
    world.facts["choice"] = choice
    world.facts["warning"] = warning
    world.facts["result"] = result
    world.facts["child"] = child
    world.facts["helper"] = helper

    introduce(world, child, helper, place)
    want_ride(world, child, choice, place)
    world.para()
    warn(world, helper, child, warning, choice)
    defy(world, child, choice)
    world.para()
    accident(world, child, choice)
    help_and_fix(world, helper, child, result, place)
    world.para()
    lesson(world, helper, child, warning)
    return world


PLACES = {
    "stead": Place(id="stead", label="stead", rhyme="stead", steady=True, tags={"stead"}),
    "barnyard": Place(id="barnyard", label="barnyard", rhyme="yard", steady=True, tags={"barnyard"}),
    "laneway": Place(id="laneway", label="lane", rhyme="lane", steady=True, tags={"lane"}),
}

RIDES = {
    "pony": Ride(id="pony", label="pony", phrase="a small pony", safe_speed=1, tags={"pony"}),
    "cart": Ride(id="cart", label="cart", phrase="a little cart", safe_speed=2, tags={"cart"}),
    "scoot": Ride(id="scoot", label="scooter", phrase="a bright scooter", safe_speed=2, tags={"scooter"}),
}

WARNINGS = {
    "gate": Warning(
        id="gate", label="gate", rhyme="late",
        caution_line="Keep the gate shut and don't run straight",
        lesson_line="A closed gate keeps a steady pace",
        tags={"gate", "caution"},
    ),
    "bend": Warning(
        id="bend", label="bend", rhyme="bend",
        caution_line="Take the bend slow, and mind the road",
        lesson_line="Slow turns keep the wheels in line",
        tags={"bend", "caution"},
    ),
}

RESULTS = {
    "latch": Result(
        id="latch", label="latch", fix="the latch is mended and the gate can stay shut",
        lyric="the latch held firm and the gate stayed tight",
        tags={"latch"},
    ),
    "rope": Result(
        id="rope", label="rope", fix="a rope tie keeps the gate snug and neat",
        lyric="the rope held steady and the gate sat neat",
        tags={"rope"},
    ),
}

@dataclass
class StoryParams:
    place: str
    choice: str
    warning: str
    result: str
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


CURATED = [
    StoryParams(place="stead", choice="pony", warning="gate", result="latch",
                child_name="Mina", child_gender="girl", helper_name="Papa", helper_gender="boy"),
    StoryParams(place="barnyard", choice="cart", warning="bend", result="rope",
                child_name="Nia", child_gender="girl", helper_name="Mum", helper_gender="woman"),
]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for c in RIDES.values():
            for w in WARNINGS.values():
                for r in RESULTS.values():
                    if can_choose(c, p):
                        combos.append((p.id, c.id, w.id))
    return combos


KNOWLEDGE = {
    "stead": [("What is a stead?",
               "A stead is a place where a horse or pony lives and stands safe and calm.")],
    "gate": [("Why should a gate stay shut?",
              "A shut gate helps keep animals and children where they belong, so nobody wanders into trouble.")],
    "pony": [("What is a pony?",
              "A pony is a small horse. Ponies are gentle, but they still need careful riding.")],
    "cart": [("What is a cart?",
             "A cart is a small wheeled thing that can be pulled or pushed. It should not go too fast.")],
    "scooter": [("Why must a scooter be ridden carefully?",
                 "A scooter can tip or skid if you go too fast, so slow feet are safer.")],
    "caution": [("What does caution mean?",
                 "Caution means being careful and thinking ahead so you do not get hurt.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming cautionary story for a child at a stead, and include the word "stead".',
        f"Tell a gentle rhyming tale where {f['child'].id} wants one more ride, but {f['helper'].id} warns about the gate and the child learns to slow down.",
        f"Write a simple warning story with a safe ending about a {f['choice'].label} and a shut gate at the stead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, place, choice, warning = f["child"], f["helper"], f["place"], f["choice"], f["warning"]
    return [
        ("Where did the story happen?",
         f"It happened at the {place.label}, a steady old place where the {choice.label} and the gate were part of the day."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted one more ride on the {choice.label}. That choice mattered because the lane by the stead could be tricky if someone rushed."),
        (f"What did {helper.id} warn about?",
         f"{helper.id} warned about the {warning.label} and told {child.id} to be careful. The warning mattered because a fast start can lead to a slip."),
        ("What changed by the end?",
         "The gate was shut again, the risky hurry was gone, and the child learned to slow down. That makes the ending feel safe and steady."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["choice"].tags) | set(world.facts["warning"].tags)
    out: list[tuple[str, str]] = []
    for key, pairs in KNOWLEDGE.items():
        if key in tags:
            out.extend(pairs)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this choice is not cautious enough for the tiny stead world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary rhyming storyworld at a stead.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--choice", choices=RIDES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--result", choices=RESULTS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.choice:
        combos = [c for c in combos if c[1] == args.choice]
    if args.warning:
        combos = [c for c in combos if c[2] == args.warning]
    if not combos:
        raise StoryError(explain_rejection())
    place, choice, warning = rng.choice(sorted(combos))
    result = args.result or rng.choice(sorted(RESULTS))
    return StoryParams(
        place=place,
        choice=choice,
        warning=warning,
        result=result,
        child_name=args.child_name or rng.choice(["Mina", "Nia", "Lia", "Jo"]),
        child_gender="girl",
        helper_name=args.helper_name or rng.choice(["Papa", "Mama", "Aunt Rae"]),
        helper_gender="boy",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.choice not in RIDES or params.warning not in WARNINGS or params.result not in RESULTS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        place=PLACES[params.place],
        choice=RIDES[params.choice],
        warning=WARNINGS[params.warning],
        result=RESULTS[params.result],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
    )
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


ASP_RULES = r"""
risk(P) :- place(P), steady(P), gate_open(G), G > 0.
unsafe_choice(C) :- ride(C), fast(C, S), S > 2.
valid(P, C, W) :- place(P), ride(C), warning(W), not unsafe_choice(C), steady(P).
outcome(cautionary) :- risk(stead), warning(gate).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.steady:
            lines.append(asp.fact("steady", pid))
    for cid, c in RIDES.items():
        lines.append(asp.fact("ride", cid))
        lines.append(asp.fact("fast", cid, c.safe_speed))
    for wid, w in WARNINGS.items():
        lines.append(asp.fact("warning", wid))
    for rid in RESULTS:
        lines.append(asp.fact("result", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as err:
        print(f"MISMATCH: normal generation/emit failed: {err}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def valid_combos_simple() -> list[tuple[str, str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at the stead ({p.choice})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
