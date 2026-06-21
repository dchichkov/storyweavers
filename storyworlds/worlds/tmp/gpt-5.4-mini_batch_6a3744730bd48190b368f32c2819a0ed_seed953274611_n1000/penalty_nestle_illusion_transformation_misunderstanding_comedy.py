#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/penalty_nestle_illusion_transformation_misunderstanding_comedy.py
===================================================================================================

A small comedy storyworld about a child, a stage trick, a mistaken idea, and a
gentle transformation. The story includes the seed words *penalty*, *nestle*,
and *illusion*, and centers on misunderstanding and a playful change of form.

The world is built from a tiny simulation:
- typed entities with physical meters and emotional memes,
- forward causal rules,
- a reasonableness gate,
- an inline ASP twin for parity checking,
- story-grounded and world-knowledge QA.

The plot shape is:
premise -> misunderstanding -> tiny consequence / penalty -> reveal -> transformation -> warm comic ending.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    makes_illusion: bool = False
    can_transform: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Room:
    id: str
    label: str
    atmosphere: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    prop: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self._narrated_warning = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    prop = world.get("prop")
    if child.memes["confidence"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confused"] += 1
    out.append("__warn__")
    return out


def _r_penalty(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    child = world.get("child")
    if prop.meters["spill"] < THRESHOLD:
        return out
    sig = ("penalty",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.atmosphere = "bumpy"
    child.memes["embarrassed"] += 1
    out.append("__penalty__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    if prop.meters["spun"] < THRESHOLD:
        return out
    sig = ("transformation",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["sparkle"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding),
                Rule("penalty", _r_penalty),
                Rule("transformation", _r_transformation)]


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


def reasonableness_gate(prop: Prop, room: Room) -> bool:
    return prop.makes_illusion and prop.can_transform and "stage" in room.tags


def penalty_severity(prop: Prop) -> int:
    return 2 if "comic" in prop.tags else 1


def should_fix(response: Response) -> bool:
    return response.sense >= 2


def explain_rejection(prop: Prop, room: Room) -> str:
    return f"(No story: {prop.label} needs a stage-like room and a real trick, so this combination is too thin.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for this comic world; try a safer, kinder fix.)"


def predict(world: World, prop_id: str) -> dict:
    sim = world.copy()
    _cause_misunderstanding(sim, narrate=False)
    _cause_spill(sim, narrate=False)
    _cause_transformation(sim, narrate=False)
    prop = sim.get(prop_id)
    return {"spill": prop.meters["spill"], "sparkle": prop.meters["sparkle"], "embarrassed": sim.get("child").memes["embarrassed"]}


def _cause_misunderstanding(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    if child.memes["confidence"] >= THRESHOLD:
        child.memes["confused"] += 1
        world.say(f"{child.id} took the trick too literally and nodded with a serious face.")


def _cause_spill(world: World, narrate: bool = True) -> None:
    prop = world.get("prop")
    prop.meters["spill"] += 1
    prop.meters["stuck"] += 1
    propagate(world, narrate=narrate)


def _cause_transformation(world: World, narrate: bool = True) -> None:
    prop = world.get("prop")
    prop.meters["spun"] += 1
    propagate(world, narrate=narrate)


def setting_line(room: Room) -> str:
    return f"The {room.label} smelled like {room.atmosphere} and looked ready for a small show."


def setup(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    child.memes["confidence"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{child.id} and {helper.id} were in the {world.room.label}. "
        f"{setting_line(world.room)}"
    )
    world.say(
        f"{child.id} loved the {prop.label}, especially because it could make an {prop.label_word}."
    )


def desire(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f'"Let me do it," {child.id} said. "{prop.label_word.capitalize()} time!"'
    )
    helper.memes["alert"] += 1
    world.say(
        f"{helper.id} blinked and said, " \
        f'"Wait, did you mean a real {prop.label_word} or the {prop.label} kind?"'
    )


def warn(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    pred = predict(world, "prop")
    world.facts["predicted"] = pred
    world.say(
        f"{child.id} thought {helper.pronoun('subject')} meant one thing, but {helper.id} meant another. "
        f"The room was set for a joke, not a grand stunt."
    )


def do_penalty(world: World, child: Entity, prop: Entity) -> None:
    prop.meters["spill"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} knocked the cup, and the {prop.label} got a little spill as a comic penalty."
    )


def reveal(world: World, helper: Entity, prop: Entity) -> None:
    world.say(
        f"Then {helper.id} laughed and showed that the {prop.label_word} was only an illusion."
    )


def transform(world: World, prop: Entity) -> None:
    _cause_transformation(world, narrate=False)
    world.say(
        f"With a spin and a shimmy, the {prop.label} transformed from plain cardboard into a shiny crown."
    )


def lesson(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["embarrassed"] = 0.0
    world.say(
        f"{child.id} giggled, because the mistake had turned into a joke instead of a disaster."
    )
    world.say(
        f"{helper.id} tucked the {prop.label} close and said, 'Next time, let's ask before we guess.'"
    )


def story_end(world: World, child: Entity, helper: Entity, prop: Entity) -> None:
    world.say(
        f"At the end, {child.id} nestle-d against {helper.id} on the floor, smiling at the sparkling {prop.label}."
    )


RESPONSES = {
    "reveal": Response(
        id="reveal",
        sense=3,
        power=3,
        text="laughed and explained the trick, then wiped the spill away",
        fail="tried to explain, but the misunderstanding only got sillier",
        qa_text="laughed and explained the trick, then wiped the spill away",
        tags={"help", "comedy"},
    ),
    "tidy": Response(
        id="tidy",
        sense=2,
        power=2,
        text="tidied the spill and set the prop straight",
        fail="tidied, but the crowd was still confused",
        qa_text="tidied the spill and set the prop straight",
        tags={"help", "comedy"},
    ),
    "water_bucket": Response(
        id="water_bucket",
        sense=1,
        power=1,
        text="splashed water everywhere, which made the joke worse",
        fail="splashed water everywhere, which made the joke worse",
        qa_text="splashed water everywhere, which made the joke worse",
        tags={"bad"},
    ),
}


ROOMS = {
    "stage": Room(id="stage", label="little stage", atmosphere="dust and curtain fluff", tags={"stage", "comic"}),
    "playroom": Room(id="playroom", label="playroom", atmosphere="cookies and crayons", tags={"stage", "comic"}),
    "kitchen": Room(id="kitchen", label="kitchen", atmosphere="toast and warm milk", tags={"comic"}),
}

PROPS = {
    "illusion_box": Prop(id="illusion_box", label="illusion box", phrase="a cardboard illusion box", makes_illusion=True, can_transform=True, tags={"illusion", "comic"}),
    "nestle_hat": Prop(id="nestle_hat", label="nestle hat", phrase="a floppy hat that could nestle over one ear", makes_illusion=True, can_transform=True, tags={"nestle", "comic"}),
    "mirror_card": Prop(id="mirror_card", label="mirror card", phrase="a shiny mirror card", makes_illusion=True, can_transform=True, tags={"illusion", "comic"}),
}

CURATED = [
    StoryParams(room="stage", prop="illusion_box", response="reveal", child_name="Milo", child_gender="boy", helper_name="Aunt June", helper_gender="woman", helper_role="aunt"),
    StoryParams(room="playroom", prop="nestle_hat", response="tidy", child_name="Lina", child_gender="girl", helper_name="Dad", helper_gender="man", helper_role="dad"),
    StoryParams(room="stage", prop="mirror_card", response="reveal", child_name="Pip", child_gender="boy", helper_name="Ms. Bean", helper_gender="woman", helper_role="teacher"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid, room in ROOMS.items():
        for pid, prop in PROPS.items():
            if reasonableness_gate(prop, room):
                combos.append((rid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic storyworld about illusion, misunderstanding, and a tiny transformation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not should_fix(RESPONSES[args.response]):
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, prop = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(["Milo", "Lina", "Pip", "Nora", "Toby", "Zoe"])
    child_gender = "girl" if child_name in {"Lina", "Nora", "Zoe"} else "boy"
    helper_name = args.helper or rng.choice(["Aunt June", "Dad", "Ms. Bean", "Big Sis"])
    helper_gender = "woman" if helper_name in {"Aunt June", "Ms. Bean", "Big Sis"} else "man"
    helper_role = "aunt" if helper_name == "Aunt June" else "helper"
    response = args.response or rng.choice(["reveal", "tidy"])
    return StoryParams(
        room=room,
        prop=prop,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
    )


def tell(params: StoryParams) -> World:
    room = ROOMS[params.room]
    prop_cfg = PROPS[params.prop]
    world = World(room)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role=params.helper_role))
    prop = world.add(Entity(id="prop", kind="thing", type="prop", label=prop_cfg.label, traits=["illusion", "nestle"]))
    setup(world, child, helper, prop)
    world.para()
    desire(world, child, helper, prop)
    warn(world, child, helper, prop)
    do_penalty(world, child, prop)
    world.para()
    reveal(world, helper, prop)
    transform(world, prop)
    lesson(world, child, helper, prop)
    story_end(world, child, helper, prop)
    world.facts.update(child=child, helper=helper, prop=prop, room=room, response=RESPONSES[params.response])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a comic story for a small child in {f['room'].label} using the words penalty, nestle, and illusion.",
        f"Tell a funny misunderstanding story where {f['child'].id} mistakes an illusion for something real, then learns the trick.",
        f"Write a cheerful transformation story where a prop changes form after a misunderstanding and everyone laughs.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, prop = f["child"], f["helper"], f["prop"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who got tangled up in a silly illusion."),
        ("What was the misunderstanding?", f"{child.id} thought the prop was meant to be one thing, but {helper.id} meant it as a joke. That mix-up made the scene funny instead of serious."),
        ("What was the penalty?", f"The comic penalty was a little spill on the {prop.label}. It was small enough to laugh about, which kept the story light."),
        ("What changed at the end?", f"The prop transformed into a shiny crown, and the mistake turned into a cheerful ending."),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "illusion": [("What is an illusion?", "An illusion is something that looks real for a moment, but it is really a trick for the eyes.")],
    "penalty": [("What is a penalty?", "A penalty is a small consequence or setback when something goes wrong.")],
    "nestle": [("What does it mean to nestle?", "To nestle means to settle in a cozy, snug way.")],
    "transform": [("What does transform mean?", "To transform means to change into a different form or look.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when people think the same thing means different things.")],
    "comedy": [("What makes a story funny?", "A funny story often has a mix-up, a surprise, or a harmless mistake that turns out okay.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["prop"].tags) | {"penalty", "nestle", "illusion", "transform", "misunderstanding", "comedy"}
    out = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,P) :- room(R), prop(P), makes_illusion(P), can_transform(P), stage_room(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if "stage" in room.tags:
            lines.append(asp.fact("stage_room", rid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.makes_illusion:
            lines.append(asp.fact("makes_illusion", pid))
        if prop.can_transform:
            lines.append(asp.fact("can_transform", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(room=None, prop=None, response=None, name=None, helper=None), random.Random(0)))
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP/Python parity and generate/emit smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.prop not in PROPS or params.response not in RESPONSES:
        raise StoryError("(Invalid parameters for this world.)")
    world = tell(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for r, p in asp_valid_combos():
            print(f"  {r} {p}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
