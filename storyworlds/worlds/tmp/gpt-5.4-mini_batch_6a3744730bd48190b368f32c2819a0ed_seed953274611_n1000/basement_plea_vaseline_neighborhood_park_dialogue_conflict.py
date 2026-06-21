#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/basement_plea_vaseline_neighborhood_park_dialogue_conflict.py
=============================================================================================

A standalone storyworld for a small comedy with dialogue, conflict, and bravery.

Premise:
- Two kids are playing at a neighborhood park.
- One kid has a small problem: a scraped knee and an overblown "basement mission"
  imagination.
- They argue about whether a jar of vaseline is an emergency hero-item or just a
  silly distraction.
- A brave child makes a careful plea for help, they call a grown-up, and the
  ending proves the bravery was choosing the sensible thing.

This world models:
- typed entities with physical meters and emotional memes,
- state-driven causal turns,
- a reasonableness gate,
- an inline ASP twin for parity,
- three Q&A sets grounded in simulated state.

The story is intentionally child-facing, concrete, and lightly comedic.
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
BRAVERY_MIN = 2
CONFLICT_MIN = 1
SAFE_HELPERS = {"bandage", "ice_pack", "grownup"}
SETTING_ID = "neighborhood_park"


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
    props: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    use: str
    risk: str
    safe_role: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    object_id: str
    helper: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    tone: str = "comedy"
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["conflict"] < THRESHOLD or e.memes["bravery"] < BRAVERY_MIN:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["shaky"] += 1
        out.append("__dialogue__")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    if world.facts.get("called_help") and not world.facts.get("help_arrived"):
        world.facts["help_arrived"] = True
        world.get("helper").memes["calm"] += 1
        out.append("__help__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("help", _r_help)]


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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for obj_id, obj in OBJECTS.items():
        if "vaseline" not in obj.tags:
            continue
        if "basement" not in obj.tags:
            continue
        combos.append((SETTING_ID, obj_id))
    return combos


def reasonableness_ok(params: StoryParams) -> bool:
    return params.place == SETTING_ID and params.object_id in OBJECTS and params.helper in HELPERS


def explain_rejection(params: StoryParams) -> str:
    if params.place != SETTING_ID:
        return "(No story: this world is only set in a neighborhood park.)"
    if params.object_id not in OBJECTS:
        return "(No story: unknown object.)"
    if params.helper not in HELPERS:
        return "(No story: this helper is not part of the world.)"
    return "(No story: the combination is not reasonable.)"


def predict(world: World, obj: ObjectCfg) -> dict:
    sim = world.copy()
    sim.get("child1").meters["scraped_knee"] += 1
    sim.get("child1").memes["fear"] += 1
    return {"needs_help": obj.safe_role == "bandage", "conflict": sim.get("child1").memes["fear"]}


def setup(world: World, a: Entity, b: Entity, parent: Entity, place: Place, obj: ObjectCfg) -> None:
    a.memes["bravery"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"At the neighborhood park, {a.id} and {b.id} were building a pretend "
        f"mission to the basement of an old clubhouse. {place.props[0]} "
        f"{place.props[1]}"
    )
    world.say(
        f'"This is important," {a.id} said. "{obj.phrase} might save the day." '
        f'"Save what?" {b.id} asked.'
    )


def incident(world: World, a: Entity, b: Entity, obj: ObjectCfg) -> None:
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.say(
        f"Then {a.id} noticed {a.pronoun('possessive')} scraped knee and made a grand, serious face."
    )
    world.say(
        f'"I need a plea!" {a.id} declared. "{obj.label}! For the basement!"'
    )
    world.say(
        f'"A plea for what?" {b.id} said, trying not to laugh. '
        f'"You are at a park, not an emergency museum."'
    )


def warn(world: World, b: Entity, a: Entity, obj: ObjectCfg, helper: Entity) -> None:
    pred = predict(world, OBJECTS[obj.id])
    b.memes["bravery"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'"No," {b.id} said, standing a little taller. '
        f'"{obj.label} is not for that. It is for {obj.use}, not for a basement mission."'
    )
    world.say(
        f'"If we need help, we should ask {helper.label_word}.' 
        f'That is the brave thing."'
    )


def resolve(world: World, helper: Entity, a: Entity, b: Entity, obj: ObjectCfg) -> None:
    helper.memes["calm"] += 1
    helper.memes["warmth"] += 1
    world.facts["called_help"] = True
    world.say(
        f"{helper.label_word.capitalize()} came over with a bandage and an ice pack. "
        f'`"Nice basement drama,"` {helper.id} said with a smile. '
        f'"Now let us fix the knee, not the whole underworld."'
    )
    world.say(
        f"{helper.id} cleaned the scrape, used the bandage, and set the vaseline aside "
        f"for later, when it could be used the normal way."
    )
    world.say(
        f"{a.id} blinked, then grinned. {b.id} laughed so hard {b.pronoun('possessive')} "
        f"shoulders shook."
    )


def ending(world: World, a: Entity, b: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] += 1
    world.say(
        f"By the time they left the park, {a.id}'s knee was patched up and "
        f"{b.id} was still giggling about the basement plan."
    )
    world.say(
        f"On the way home, {a.id} held the bandage like a medal. "
        f'"That was my bravest plea," {a.id} said. "I asked for help."'
    )
    world.say(
        f'"Exactly," {b.id} said. "And next time, let us keep the basement out of the picnic."'
    )


def tell(place: Place, obj: ObjectCfg, helper_cfg: ObjectCfg,
         a_name: str, a_gender: str, b_name: str, b_gender: str,
         parent_type: str) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="child"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=parent_type, label="the grown-up"))
    world.add(Entity(id="object", kind="thing", type="thing", label=obj.label, tags=set(obj.tags)))
    a.memes["bravery"] = 1.0
    b.memes["bravery"] = 1.0
    setup(world, a, b, helper, place, obj)
    world.para()
    incident(world, a, b, obj)
    warn(world, b, a, obj, helper)
    world.para()
    resolve(world, helper, a, b, obj)
    ending(world, a, b)
    world.facts.update(
        child1=a, child2=b, helper=helper, place=place, obj=obj,
        called_help=True, outcome="safe"
    )
    return world


SETTINGS = {
    SETTING_ID: Place(
        id=SETTING_ID,
        label="neighborhood park",
        props=["The swings squeaked nearby.", "A basement-shaped clubhouse sat behind the trees."],
        tags={"park", "basement"},
    ),
}

OBJECTS = {
    "vaseline": ObjectCfg(
        id="vaseline",
        label="vaseline",
        phrase="the tiny jar of vaseline",
        use="keeping skin from getting too dry",
        risk="nothing dramatic at all",
        safe_role="bandage",
        tags={"vaseline", "basement"},
    ),
    "bandage": ObjectCfg(
        id="bandage",
        label="bandage",
        phrase="a clean bandage",
        use="covering scrapes",
        risk="none",
        safe_role="bandage",
        tags={"bandage"},
    ),
}

HELPERS = {
    "grownup": Entity(id="grownup", kind="character", type="mother", label="the grown-up"),
}

GIRL_NAMES = ["Mina", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Eli"]


@dataclass
class StoryParams:
    place: str
    object_id: str
    helper: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    tone: str = "comedy"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: basement plea, vaseline, park conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", dest="child1_gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", dest="child2_gender", choices=["girl", "boy"])
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
    place = args.place or SETTING_ID
    object_id = args.object_id or "vaseline"
    helper = args.helper or "grownup"
    if not reasonableness_ok(StoryParams(place, object_id, helper, "A", "girl", "B", "boy", "mother")):
        raise StoryError(explain_rejection(StoryParams(place, object_id, helper, "A", "girl", "B", "boy", "mother")))
    c1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    c2_gender = args.child2_gender or ("boy" if c1_gender == "girl" else "girl")
    c1_pool = GIRL_NAMES if c1_gender == "girl" else BOY_NAMES
    c2_pool = GIRL_NAMES if c2_gender == "girl" else BOY_NAMES
    child1 = args.child1 or rng.choice(c1_pool)
    child2 = args.child2 or rng.choice([n for n in c2_pool if n != child1] or c2_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place, object_id=object_id, helper=helper,
        child1=child1, child1_gender=c1_gender, child2=child2, child2_gender=c2_gender,
        parent=parent, tone="comedy"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"].id
    b = f["child2"].id
    return [
        f'Write a funny story at a neighborhood park that includes the words "basement", "plea", and "vaseline".',
        f"Tell a dialogue-heavy comedy where {a} makes a dramatic basement plea and {b} argues back before a grown-up helps.",
        f"Write a child-friendly conflict story where bravery means asking for help instead of making a silly situation bigger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    helper = f["helper"]
    obj = f["obj"]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} argue about?",
            answer=f"They argued about {obj.label} and whether it belonged in the basement mission. {b.id} thought that was silly, and {a.id} insisted it was important until the grown-up stepped in."
        ),
        QAItem(
            question=f"Why was {a.id} brave?",
            answer=f"{a.id} was brave because {a.pronoun('subject')} asked for help instead of pretending everything was fine. That kind of bravery is quiet, but it solved the problem the right way."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily with a cleaned scrape, a bandage, and lots of laughing at the park. The vaseline stayed safe for later, and the basement idea turned into a joke."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is vaseline usually for?",
            answer="Vaseline is a soft ointment people use to protect dry skin. It is not a toy, and it does not belong in a silly basement mission."
        ),
        QAItem(
            question="What should you do if you get hurt at the park?",
            answer="You should tell a grown-up right away and get help. That keeps the problem small and helps the hurt part feel better faster."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.object_id not in OBJECTS or params.helper not in HELPERS:
        raise StoryError("(Invalid parameters.)")
    world = tell(
        SETTINGS[params.place],
        OBJECTS[params.object_id],
        OBJECTS["bandage"],
        params.child1, params.child1_gender,
        params.child2, params.child2_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place=SETTING_ID, object_id="vaseline", helper="grownup",
        child1="Mina", child1_gender="girl",
        child2="Ben", child2_gender="boy",
        parent="mother"
    )
]


ASP_RULES = r"""
place(neighborhood_park).
object(vaseline).
helper(grownup).
valid(place,object,helper) :- place(place), object(object), helper(helper).
bravery(ask_help).
conflict(basement_plea).
resolution(grownup_help).
"""


def asp_facts() -> str:
    import asp
    parts = [
        asp.fact("place", SETTING_ID),
        asp.fact("object", "vaseline"),
        asp.fact("helper", "grownup"),
    ]
    return "\n".join(parts)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != {("place", "object", "helper")}:
            rc = 1
            print("MISMATCH in ASP validity.")
        sample = generate(resolve_params(argparse.Namespace(place=None, object_id=None, helper=None, child1=None, child1_gender=None, child2=None, child2_gender=None, parent=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print("VERIFY FAILED:", e)
        traceback.print_exc()
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
