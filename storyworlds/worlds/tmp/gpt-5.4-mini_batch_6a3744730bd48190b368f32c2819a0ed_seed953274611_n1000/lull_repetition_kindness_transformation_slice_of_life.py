#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lull_repetition_kindness_transformation_slice_of_life.py
========================================================================================

A small slice-of-life storyworld about a child, a calming lull, repeated little
chores, kindness, and a quiet transformation in how a home feels.

The domain is built from a tiny seed: a tired child, a soft lull in the
afternoon, a repeated pattern of kindness, and the change that follows.
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
class ObjectCfg:
    id: str
    label: str
    place: str
    kind: str = "thing"
    type: str = "thing"
    requires_kindness: bool = False
    transformable: bool = False
    cozy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ActionCfg:
    id: str
    noun: str
    verb: str
    repeat_verb: str
    result_meme: str
    effect_meter: str
    can_transform: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    action: str
    object: str
    helper: str
    helper_gender: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_lull(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["lull"] < THRESHOLD:
        return out
    sig = ("lull",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["sleepy"] += 1
    child.memes["calm"] += 1
    helper.memes["calm"] += 1
    out.append("The room settled into a soft lull, and even the busy little sounds grew quiet.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    for k in range(1, 4):
        sig = ("kindness", k)
        if sig in world.fired:
            continue
        if helper.memes["kindness"] < k:
            continue
        world.fired.add(sig)
        child.memes["glad"] += 1
        child.meters["tidy"] += 1
        room = world.get("room")
        room.meters["warmth"] += 1
        if k == 1:
            out.append(f"{helper.id} noticed {child.id} looking tired and brought a cup of water.")
        elif k == 2:
            out.append(f"{helper.id} gently folded the blanket and set it back where it belonged.")
        else:
            out.append(f"{helper.id} smiled and kept the light low so the whole room could rest.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    obj = world.get("object")
    sig = ("transform",)
    if sig in world.fired:
        return out
    if room.meters["warmth"] < 2 or obj.meters["care"] < 2:
        return out
    world.fired.add(sig)
    obj.meters["changed"] += 1
    room.meters["quiet"] += 1
    out.append(f"By the end of it, the {obj.label} felt different: not new, just cared for.")
    return out


RULES = [
    Rule("lull", _r_lull),
    Rule("kindness", _r_kindness),
    Rule("transform", _r_transform),
]


ROOMS = {
    "kitchen": "the kitchen",
    "living_room": "the living room",
    "bedroom": "the bedroom",
}

ACTIONS = {
    "cleaning": ActionCfg(
        id="cleaning",
        noun="the little mess",
        verb="clean up",
        repeat_verb="cleaned up another corner",
        result_meme="proud",
        effect_meter="care",
        can_transform=True,
        tags={"clean", "care"},
    ),
    "teatime": ActionCfg(
        id="teatime",
        noun="the tea things",
        verb="set the table",
        repeat_verb="set out one more cup",
        result_meme="settled",
        effect_meter="care",
        can_transform=True,
        tags={"tea", "care"},
    ),
    "tidying": ActionCfg(
        id="tidying",
        noun="the scattered toys",
        verb="tidy up",
        repeat_verb="put away one more toy",
        result_meme="glad",
        effect_meter="care",
        can_transform=True,
        tags={"tidy", "care"},
    ),
}

OBJECTS = {
    "blanket": ObjectCfg("blanket", "blanket", "sofa", requires_kindness=True, transformable=True, cozy=True, tags={"soft"}),
    "table": ObjectCfg("table", "table", "center of the room", requires_kindness=False, transformable=True, tags={"wood"}),
    "plants": ObjectCfg("plants", "plant pots", "window", requires_kindness=True, transformable=False, cozy=False, tags={"green"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Maya", "June"]
BOY_NAMES = ["Eli", "Theo", "Finn", "Owen", "Leo", "Asa"]
HELPERS = ["mother", "father"]
TRAITS = ["gentle", "patient", "thoughtful", "quiet", "kind"]

KNOWLEDGE = {
    "lull": [("What is a lull?", "A lull is a calm, quiet pause when the noise and action slow down. It can make a room feel sleepy and peaceful.")],
    "kindness": [("What is kindness?", "Kindness means doing helpful, caring things for someone else. Small kind acts can make a day feel safer and warmer.")],
    "transform": [("What does transform mean?", "Transform means to change into something different. Sometimes a place changes because people care for it.")],
    "blanket": [("What is a blanket for?", "A blanket is soft and warm. People use it to feel cozy or to rest.")],
    "table": [("What is a table for?", "A table is a flat surface people use for meals, games, and work.")],
    "plants": [("Why do plants need care?", "Plants need water, light, and attention to stay healthy and green.")],
}
KNOWLEDGE_ORDER = ["lull", "kindness", "transform", "blanket", "table", "plants"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for act_id, act in ACTIONS.items():
            for obj_id, obj in OBJECTS.items():
                if obj.transformable and act.can_transform:
                    combos.append((room, act_id, obj_id))
    return combos


def explain_rejection(action: ActionCfg, obj: ObjectCfg) -> str:
    return f"(No story: {action.verb} does not lead to a believable transformation for the {obj.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with lull, kindness, and quiet transformation.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["mother", "father"])
    ap.add_argument("--parent", choices=HELPERS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for o, ob in OBJECTS.items():
        lines.append(asp.fact("object", o))
        if ob.transformable:
            lines.append(asp.fact("transformable", o))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,A,O) :- room(R), action(A), object(O), transformable(O).
"""


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
        sample = generate(resolve_params(argparse.Namespace(room=None, action=None, object=None, child=None, child_gender=None, helper=None, helper_gender=None, parent=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: smoke test failed: {exc}")
        rc = 1
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.action is None or c[1] == args.action)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, action, obj = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(HELPERS)
    return StoryParams(
        room=room,
        action=action,
        object=obj,
        child=args.child or _pick_name(rng, child_gender),
        child_gender=child_gender,
        helper=args.helper or rng.choice(GIRL_NAMES + BOY_NAMES),
        helper_gender=helper_gender,
        parent=args.parent or rng.choice(HELPERS),
    )


def _story_intro(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    room = world.get("room")
    world.say(f"{child.id} and {helper.id} were having a quiet afternoon in {room.label}.")
    world.say(f"The little routine of the day moved slowly, like a soft lull after lunch.")


def _repeat_kindness(world: World, action: ActionCfg, obj: ObjectCfg) -> None:
    child = world.get("child")
    helper = world.get("helper")
    room = world.get("room")
    for i in range(3):
        helper.memes["kindness"] += 1
        child.memes["tired"] += 1 if i == 0 else 0
        obj.meters["care"] += 1
        room.meters["lull"] += 1 if i == 0 else 0
        if i == 0:
            world.say(f"When {child.id} looked worn out, {helper.id} started with one small kind thing.")
        elif i == 1:
            world.say(f"Then {helper.id} did it again, in the same gentle way, with no hurry at all.")
        else:
            world.say(f"One more time, {helper.id} did the little task, and the room grew even calmer.")
    child.memes[action.result_meme] += 1
    child.meters[action.effect_meter] += 1
    obj.meters["care"] += 1


def _transform(world: World, obj: ObjectCfg) -> None:
    obj_ent = world.get("object")
    obj_ent.meters["changed"] += 1
    obj_ent.memes["love"] += 1
    world.say(f"After that, {obj_ent.label} did not feel the same anymore.")
    world.say(f"It felt cared for, and the whole room seemed softer because of it.")


def tell(params: StoryParams) -> World:
    world = World()
    room_label = ROOMS[params.room]
    action = ACTIONS[params.action]
    obj_cfg = OBJECTS[params.object]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="room", label=room_label))
    obj = world.add(Entity(id="object", type="thing", label=obj_cfg.label, attrs={"place": obj_cfg.place}))
    _story_intro(world)
    world.para()
    world.say(f"{child.id} wanted to {action.verb}, and {helper.id} wanted to help.")
    world.say(f"That was when the lull settled in, and the same kind motion happened again and again.")
    _repeat_kindness(world, action, obj_cfg)
    world.para()
    if obj_cfg.transformable:
        _transform(world, obj_cfg)
    world.say(f"By evening, {room.label} felt tidier, and {child.id} looked brighter than before.")
    world.say(f"It was only a small day, but the small day had changed something real.")
    world.facts.update(child=child, helper=helper, room=room, object=obj, action=action, cfg=obj_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, action, obj = f["child"], f["helper"], f["action"], f["cfg"]
    return [
        f'Write a slice-of-life story that uses the word "lull" and shows {helper.id} being kind more than once.',
        f"Tell a gentle story where {child.id} and {helper.id} repeat a small helpful act until the {obj.label} feels transformed.",
        f'Write a quiet home story with repetition, kindness, and a soft transformation in {world.get("room").label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, action, obj = f["child"], f["helper"], f["action"], f["cfg"]
    return [
        QAItem(
            question="What was the quiet feeling in the room called?",
            answer="It was a lull, a calm pause where everything slowed down. That quiet made the small kind acts easier to notice."
        ),
        QAItem(
            question=f"What did {helper.id} do again and again?",
            answer=f"{helper.id} repeated small kind things: bringing water, folding the blanket, and keeping the light low. The repetition is what turned one nice moment into a whole gentle routine."
        ),
        QAItem(
            question=f"How did the {obj.label} change by the end?",
            answer=f"It felt cared for and different by the end, almost transformed by the attention it received. The change came from kindness repeated over and over."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"lull", "kindness", "transform", "blanket"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.action not in ACTIONS or params.object not in OBJECTS:
        raise StoryError("invalid StoryParams")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(room="living_room", action="cleaning", object="blanket", helper="Mara", helper_gender="mother", child="Nina", child_gender="girl", parent="mother"),
    StoryParams(room="kitchen", action="teatime", object="table", helper="Ben", helper_gender="father", child="Owen", child_gender="boy", parent="father"),
    StoryParams(room="bedroom", action="tidying", object="plants", helper="Lia", helper_gender="mother", child="Eli", child_gender="boy", parent="mother"),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
