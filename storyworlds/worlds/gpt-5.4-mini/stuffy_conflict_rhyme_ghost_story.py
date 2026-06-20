#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stuffy_conflict_rhyme_ghost_story.py
====================================================================

A small standalone story world about a stuffy old room, a tiny conflict, and a
gentle rhyme that helps a child discover the "ghost" is just a friend in need.

The world is built as a classical simulation: typed entities with physical
meters and emotional memes, forward-chained causal rules, a reasonableness
gate, an inline ASP twin, and a renderer that turns state changes into a child-
facing ghost story with a beginning, turn, and ending image.

Seed idea
---------
A child is in a stuffy room at night. They hear a spooky rhyme and think a ghost
is causing trouble. The conflict turns on whether they should open the window or
stay scared. In the end, they discover the "ghost" is only a little white moth
stuck inside a paper lantern, and a safe rhyme becomes a signal for helping.

The world keeps the ghost-story feel, but the resolution is calm and concrete:
fresh air, a lantern, and a tiny helper released into the night.
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    stuffy: bool = False
    airy: bool = False
    gloomy: bool = False


@dataclass
class ObjectCfg:
    id: str
    label: str
    glow: str = ""
    rhyme_hook: str = ""
    gentle: bool = False
    haunted: bool = False
    moth_trap: bool = False


@dataclass
class ActionCfg:
    id: str
    verb: str
    risk: str
    fix: str
    better: str
    sense: int
    power: int


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_breathless(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.stuffy:
        return out
    sig = ("breathless", world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["unease"] += 1
    out.append("__breathless__")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["rhyme"] < THRESHOLD:
            continue
        sig = ("rhyme", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__rhyme__")
    return out


CAUSAL_RULES = [
    Rule("breathless", "physical", _r_breathless),
    Rule("rhyme", "social", _r_rhyme),
]


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


def reasonableness_gate(place: Place, obj: ObjectCfg, action: ActionCfg) -> bool:
    return True if (place.stuffy and obj.haunted and action.sense >= 2) else False


def sensible_actions() -> list[ActionCfg]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def outcome_of(params: "StoryParams") -> str:
    return "quieted" if params.action != "panic" else "scared"


def is_relieved(action: ActionCfg, place: Place) -> bool:
    return action.power >= (2 if place.stuffy else 1)


def predict(world: World, obj_id: str, action: ActionCfg) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(obj_id), action, narrate=False)
    return {
        "rhyme": sim.get(obj_id).meters["rhyme"] >= THRESHOLD,
        "unease": max((e.memes["unease"] for e in sim.characters()), default=0.0),
    }


def _do_action(world: World, actor: Entity, action: ActionCfg, narrate: bool = True) -> None:
    actor.meters[action.id] += 1
    actor.meters["rhyme"] += 1
    propagate(world, narrate=narrate)


def begin(world: World, child: Entity, place: Place, obj: ObjectCfg) -> None:
    world.say(
        f"That night, {child.id} crept into the {place.label}, where the air was "
        f"stuffy and still."
    )
    world.say(
        f"A little lantern glowed on the desk, and the room felt gloomy enough "
        f"to make even a brave heart listen close."
    )
    if obj.haunted:
        world.say(
            f"Near the curtain sat {obj.label}, and its soft face seemed to wait "
            f"for the dark."
        )


def conflict(world: World, child: Entity, obj: ObjectCfg) -> None:
    child.memes["fear"] += 1
    world.say(
        f"Then {child.id} heard a whispery rhyme: "
        f'"{obj.rhyme_hook} in the gloom, tap-tap-tap in the room."'
    )
    world.say(
        f'{child.id} hugged {child.pronoun("possessive")} {obj.label} and frowned. '
        f'"Is that a ghost?" {child.pronoun()} whispered.'
    )


def warn(world: World, child: Entity, parent: Entity, place: Place, obj: ObjectCfg) -> None:
    world.say(
        f'{parent.id} looked over {child.pronoun("possessive")} shoulder and said, '
        f'"This room is too stuffy. Sometimes a strange sound is only the wind, '
        f'or a tiny thing stuck inside."'
    )
    child.memes["doubt"] += 1


def defy_or_listen(world: World, child: Entity, parent: Entity, action: ActionCfg) -> None:
    if child.memes["doubt"] >= 1:
        world.say(
            f'{child.id} thought for a moment, then answered, '
            f'"Maybe I should listen first, before I run."'
        )
    else:
        world.say(
            f'"I do not like this!" {child.id} said, and the fear felt bigger '
            f"than the room."
        )


def opening(world: World, child: Entity, place: Place) -> None:
    place.stuffy = False
    place.airy = True
    child.memes["courage"] += 1
    world.say(
        f"At last, {child.id} opened the window. A cool breeze slipped in, and "
        f"the room breathed out like a sleepy cat."
    )


def reveal(world: World, child: Entity, obj: ObjectCfg) -> None:
    world.say(
        f"Inside {obj.label} they found the little ghostly trick: a white moth, "
        f"beating its tiny wings against the glass."
    )
    child.memes["surprise"] += 1
    child.memes["pity"] += 1


def free_moth(world: World, child: Entity, obj: ObjectCfg) -> None:
    world.say(
        f"{child.id} lifted {child.pronoun('possessive')} hands and let the moth "
        f"fly out into the night."
    )
    world.say(
        f"The moth drifted past the moon, and the rhyme turned from spooky to "
        f"sweet."
    )


def lesson(world: World, child: Entity, parent: Entity) -> None:
    child.memes["calm"] += 1
    world.say(
        f'{parent.id} smiled and said, "When a room feels stuffy, a little fresh '
        f'air can help. And when a sound feels spooky, a rhyme can become a clue."'
    )
    world.say(
        f"{child.id} nodded, less scared now, and listened to the quiet room with "
        f"a new kind of brave."
    )


def end_image(world: World, child: Entity, place: Place, obj: ObjectCfg) -> None:
    world.say(
        f"By the end, the {place.label} was airy, the lantern shone warm and soft, "
        f"and {obj.label} sat by the window like a friend instead of a fright."
    )


def tell(place: Place, obj: ObjectCfg, action: ActionCfg,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "girl") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    tool = world.add(Entity(id="lantern", type="thing", label="lantern"))
    toy = world.add(Entity(id=obj.id, type="thing", label=obj.label))
    world.facts["place"] = place
    world.facts["object"] = obj
    world.facts["action"] = action
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["tool"] = tool
    world.facts["toy"] = toy

    begin(world, child, place, obj)
    world.para()
    conflict(world, child, obj)
    warn(world, child, parent, place, obj)
    defy_or_listen(world, child, parent, action)
    world.para()
    opening(world, child, place)
    predict(world, toy.id, action)
    reveal(world, child, obj)
    free_moth(world, child, obj)
    lesson(world, child, parent)
    world.para()
    end_image(world, child, place, obj)
    world.facts["outcome"] = "quieted"
    return world


PLACES = {
    "attic": Place("attic", "attic", stuffy=True, gloomy=True),
    "closet": Place("closet", "closet", stuffy=True, gloomy=True),
    "bedroom": Place("bedroom", "bedroom", stuffy=True, gloomy=False),
}

OBJECTS = {
    "stuffy": ObjectCfg("stuffy", "a stuffed owl", glow="soft eyes", rhyme_hook="hooty"),
    "lantern": ObjectCfg("lantern", "a paper lantern", glow="gold glow", rhyme_hook="glowy", haunted=True, moth_trap=True),
    "curtain": ObjectCfg("curtain", "a white curtain", glow="moonlight", rhyme_hook="flutter", haunted=True),
}

ACTIONS = {
    "open_window": ActionCfg("open_window", "open the window", "stuffy air", "fresh air", "fresh air", 3, 3),
    "turn_on_lamp": ActionCfg("turn_on_lamp", "turn on the lamp", "darkness", "light", "light", 2, 2),
    "panic": ActionCfg("panic", "panic", "fear", "calm", "calm", 1, 0),
}

GIRL_NAMES = ["Mina", "Lina", "Sara", "Nora", "Ivy", "Rosa"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Ben", "Leo", "Owen"]


@dataclass
class StoryParams:
    place: str
    object: str
    action: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, o, a) for p in PLACES for o in OBJECTS for a in ACTIONS if reasonableness_gate(PLACES[p], OBJECTS[o], ACTIONS[a]) and o == "lantern"]


def explain_rejection(place: Place, obj: ObjectCfg, action: ActionCfg) -> str:
    return f"(No story: this scene needs a stuffy room, a haunting rhyme, and a sensible action. Try the lantern in the attic with open_window.)"


def explain_action(action_id: str) -> str:
    a = ACTIONS[action_id]
    return f"(Refusing action '{action_id}': it is too weak to make a useful change in the story.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    obj: ObjectCfg = f["object"]
    action: ActionCfg = f["action"]
    child: Entity = f["child"]
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the word "stuffy" and a spooky rhyme, but ends kindly.',
        f"Tell a gentle haunted-room story where {child.id} hears a rhyme near {obj.label}, thinks it is a ghost, and then solves the problem.",
        f"Write a story about a stuffy {place.label} where a child follows a rhyme clue, opens a window, and finds out the ghost is harmless.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    place: Place = f["place"]
    obj: ObjectCfg = f["object"]
    action: ActionCfg = f["action"]
    qa = [
        ("Where does the story happen?",
         f"It happens in the {place.label}, a place that felt stuffy and a little spooky at first."),
        ("What did {0} think the ghost was?".format(child.id),
         f"{child.id} thought the whispery rhyme might mean a ghost was hiding near {obj.label}. The sound seemed spooky because the room was stuffy and quiet."),
        ("What did the parent suggest?".format(parent.id),
         f"{parent.id} suggested that the sound might have a simple cause, and that fresh air could help. That turned the fear into a clue instead of a problem."),
        ("What solved the problem?",
         f"Opening the window helped the room feel airy, and then they found a tiny moth in {obj.label}. The rhyme was not a ghost after all; it was a little trapped creature making a sound."),
        ("How did the story end?",
         f"It ended with the room feeling fresh, {obj.label} by the window, and {child.id} feeling brave and calm. The scary thing became a small rescue instead of a fright."),
    ]
    return qa


KNOWLEDGE = {
    "stuffy": [("What does stuffy mean?",
                "Stuffy means the air feels old, close, or hard to breathe in. Opening a window can help.")],
    "window": [("Why do people open windows?",
                 "People open windows to let in fresh air and let out hot or stale air.")],
    "moth": [("What is a moth?",
               "A moth is a flying insect. Some moths are drawn to light at night.")],
    "rhyme": [("What is a rhyme?",
                "A rhyme is a sound pattern in words, like when two words end with the same sound.")],
    "ghost": [("Are all spooky sounds ghosts?",
                "No. Many spooky sounds have normal causes, like wind, a toy, or an animal.")],
    "lantern": [("What is a lantern?",
                  "A lantern is a light that helps people see in the dark.")],
}
KNOWLEDGE_ORDER = ["stuffy", "window", "moth", "rhyme", "ghost", "lantern"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"stuffy", "window", "moth", "rhyme", "ghost", "lantern"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "lantern", "open_window", "Mina", "girl", "Mom", "girl"),
    StoryParams("closet", "lantern", "turn_on_lamp", "Theo", "boy", "Dad", "boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.stuffy:
            lines.append(asp.fact("stuffy", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O,A) :- place(P), object(O), action(A), stuffy(P), O = "lantern", sense(A,S), S >= 2.
outcome(quieted) :- valid(_,_,_), power(_,P), P >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP gate diverged.")
        rc = 1
    try:
        generate(CURATED[0])
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world with stuffy air and a rhyme clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["girl", "boy"])
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
    if args.action and args.action not in ACTIONS:
        raise StoryError(explain_action(args.action))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, action = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["Mom", "Dad", "Aunt", "Uncle"])
    return StoryParams(place, obj, action, child, child_gender, parent, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OBJECTS[params.object], ACTIONS[params.action],
                 params.child, params.child_gender, params.parent, params.parent_gender)
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


GIRL_NAMES = ["Mina", "Lina", "Sara", "Nora", "Ivy", "Rosa"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Ben", "Leo", "Owen"]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
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
