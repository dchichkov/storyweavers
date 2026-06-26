#!/usr/bin/env python3
"""
storyworlds/worlds/bassinet_gyp_nursery_cautionary_heartwarming.py
===================================================================

A small, standalone story world about a nursery, a bassinet, and a gentle,
cautionary heartwarming choice.

Premise:
- A caregiver brings a baby named Gyp to the nursery.
- The older child wants to make the bassinet feel extra cozy or fun.
- The caregiver notices a safety issue: some objects belong near the baby and
  some do not.
- The family makes a kind, safe change together.

The world simulates:
- physical state: what's placed where, what is safe, what is near the baby
- emotional state: curiosity, worry, reassurance, relief, pride, love

The prose is generated from the world model, not from a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    in_container: Optional[str] = None
    placed_near: Optional[str] = None
    safe: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    cue: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    safe_near_baby: bool
    role: str
    plural: bool = False


@dataclass
class StoryParams:
    activity: str
    item: str
    name: str
    sibling_name: str
    parent_name: str
    seed: Optional[int] = None


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def nearby_items(self, container_id: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.placed_near == container_id]


def safe_choice(rng: random.Random, seq):
    if not seq:
        raise StoryError("No valid choices available.")
    return rng.choice(list(seq))


SETTING = Setting(place="the nursery")

ACTIVITIES = {
    "decorate": Activity(
        id="decorate",
        verb="decorate the bassinet",
        gerund="decorating the bassinet",
        risk="loose things could fall in",
        cue="a soft blanket and a rattle",
        fix="keep only the safe blanket nearby",
        tags={"bassinet", "nursery", "baby", "safety"},
    ),
    "rock": Activity(
        id="rock",
        verb="rock the bassinet",
        gerund="rocking the bassinet",
        risk="too much motion could wake the baby",
        cue="gentle hands and a quiet voice",
        fix="rock it slowly and quietly",
        tags={"bassinet", "nursery", "baby", "quiet"},
    ),
    "nearby_light": Activity(
        id="light",
        verb="put a lamp near the bassinet",
        gerund="setting a lamp near the bassinet",
        risk="bright light could bother sleepy eyes",
        cue="a small lamp with a warm glow",
        fix="move the lamp farther away",
        tags={"bassinet", "nursery", "light", "baby"},
    ),
}

ITEMS = {
    "blanket": Item(
        id="blanket",
        label="soft blanket",
        phrase="a soft knitted blanket",
        kind="blanket",
        safe_near_baby=True,
        role="comfort",
    ),
    "rattle": Item(
        id="rattle",
        label="small rattle",
        phrase="a small wooden rattle",
        kind="toy",
        safe_near_baby=False,
        role="noise",
    ),
    "lamp": Item(
        id="lamp",
        label="lamp",
        phrase="a little lamp with a bright bulb",
        kind="lamp",
        safe_near_baby=False,
        role="light",
    ),
    "book": Item(
        id="book",
        label="board book",
        phrase="a sturdy board book",
        kind="book",
        safe_near_baby=True,
        role="calm",
    ),
}

NAMES = ["Ava", "Mila", "Nora", "Leo", "Owen", "Iris", "June", "Emil"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for act_id, act in ACTIVITIES.items():
        for item_id, item in ITEMS.items():
            if act_id == "decorate" and item.safe_near_baby:
                out.append((act_id, item_id))
            elif act_id == "rock" and item_id in {"blanket", "book"}:
                out.append((act_id, item_id))
            elif act_id == "nearby_light" and item_id == "lamp":
                out.append((act_id, item_id))
    return out


def explain_rejection(activity: Activity, item: Item) -> str:
    return (
        f"(No story: {item.label} does not make a safe or sensible choice for "
        f"{activity.gerund} in the nursery.)"
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    baby = world.add(Entity(id="Baby", kind="character", type="baby", label=params.name))
    sibling = world.add(Entity(id="Sibling", kind="character", type="child", label=params.sibling_name))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label=params.parent_name))
    bassinet = world.add(Entity(id="Bassinet", type="bassinet", label="bassinet", safe=True))
    item = world.add(Entity(id="Item", type=ITEMS[params.item].kind, label=ITEMS[params.item].label))
    world.facts.update(
        baby=baby,
        sibling=sibling,
        parent=parent,
        bassinet=bassinet,
        item=item,
        activity=ACTIVITIES[params.activity],
        item_cfg=ITEMS[params.item],
    )
    return world


def predict_risk(world: World, activity: Activity, item_cfg: Item) -> bool:
    if activity.id == "decorate":
        return not item_cfg.safe_near_baby
    if activity.id == "rock":
        return item_cfg.kind == "lamp"
    if activity.id == "nearby_light":
        return item_cfg.kind != "lamp"
    return True


def tell(world: World, params: StoryParams) -> World:
    f = world.facts
    baby: Entity = f["baby"]
    sibling: Entity = f["sibling"]
    parent: Entity = f["parent"]
    bassinet: Entity = f["bassinet"]
    item: Entity = f["item"]
    act: Activity = f["activity"]
    item_cfg: Item = f["item_cfg"]

    baby.meters["sleep"] = 1
    sibling.memes["curiosity"] = 1
    parent.memes["care"] = 1

    world.say(
        f"In the nursery, {baby.label} slept in the bassinet while "
        f"{sibling.label} looked around for a sweet way to help."
    )
    world.say(
        f"{sibling.label} wanted to {act.verb}, because {act.cue} felt "
        f"like a lovely idea."
    )

    world.para()
    risky = predict_risk(world, act, item_cfg)
    if risky:
        sibling.memes["worry"] = 1
        parent.memes["worry"] = 1
        world.say(
            f"{parent.label} noticed that {item.label} could cause trouble: "
            f"{act.risk}."
        )
        world.say(
            f'"Let’s be careful," {parent.pronoun("subject")} said softly. '
            f'"We want the bassinet to stay safe for {baby.label}."'
        )
        sibling.memes["pause"] = 1
        world.say(
            f"{sibling.label} stopped right away, because {sibling.pronoun("subject")} "
            f"could see why the warning mattered."
        )
        if act.id == "decorate":
            if item_cfg.kind in {"blanket", "book"}:
                item.placed_near = bassinet.id
                world.say(
                    f"They chose {item.label} instead, and it made the bassinet "
                    f"look cozy without crowding the baby."
                )
            else:
                world.say(
                    f"They moved {item.label} to the shelf, then found a "
                    f"{ITEMS["blanket"].label} to tuck nearby."
                )
        elif act.id == "rock":
            world.say(
                f"Together they rocked the bassinet slowly and quiet as a whisper, "
                f"so {baby.label} kept sleeping."
            )
        else:
            world.say(
                f"They moved the lamp farther away, and the nursery glowed with a "
                f"gentler, warmer light."
            )
        parent.memes["relief"] = 1
        sibling.memes["pride"] = 1
        world.para()
        world.say(
            f"In the end, {baby.label} stayed snug in the bassinet, and "
            f"{sibling.label} felt proud of helping the safe way."
        )
    else:
        item.placed_near = bassinet.id
        sibling.memes["joy"] = 1
        parent.memes["joy"] = 1
        world.say(
            f"That plan was safe, so {sibling.label} did it with care and "
            f"everything stayed peaceful."
        )
        world.say(
            f"The nursery felt warm and calm, and {baby.label} kept dreaming in the bassinet."
        )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act: Activity = f["activity"]
    item_cfg: Item = f["item_cfg"]
    baby: Entity = f["baby"]
    sibling: Entity = f["sibling"]
    return [
        f'Write a short heartwarming cautionary story set in the nursery using the words "bassinet", "gyp", and "nursery".',
        f"Tell a gentle story where {sibling.label} wants to {act.verb} but learns "
        f"why {item_cfg.label} needs careful handling near {baby.label}'s bassinet.",
        f"Write a simple story about a family in the nursery who makes a safe choice around a bassinet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    baby: Entity = f["baby"]
    sibling: Entity = f["sibling"]
    parent: Entity = f["parent"]
    act: Activity = f["activity"]
    item_cfg: Item = f["item_cfg"]

    qa = [
        QAItem(
            question=f"Where does the story take place?",
            answer="It takes place in the nursery, where the bassinet sits near the family.",
        ),
        QAItem(
            question=f"What did {sibling.label} want to do with the bassinet?",
            answer=f"{sibling.label} wanted to {act.verb}, because it seemed sweet or fun at first.",
        ),
        QAItem(
            question=f"Why did {parent.label} speak up?",
            answer=(
                f"{parent.label} spoke up because {item_cfg.label} could be risky near the baby, "
                f"and the family wanted the bassinet to stay safe for {baby.label}."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, the family chose a safer plan, and {baby.label} stayed snug and calm "
                f"in the bassinet while everyone felt better."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bassinet?",
            answer="A bassinet is a small bed made for a baby, so the baby can sleep close by.",
        ),
        QAItem(
            question="What is a nursery?",
            answer="A nursery is a room where a baby sleeps, rests, and is cared for.",
        ),
        QAItem(
            question="Why should grown-ups be careful around a sleeping baby?",
            answer="Grown-ups should be careful so the baby stays safe, comfortable, and able to rest.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.placed_near:
            bits.append(f"near={e.placed_near}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% An activity is risky for an item if the item is not appropriate near the baby
% in that kind of nursery action.
risky(A, I) :- activity(A), item(I), bad_pair(A, I).

valid(A, I) :- activity(A), item(I), not risky(A, I).

% This world keeps a small set of acceptable stories.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for i, item in ITEMS.items():
        lines.append(asp.fact("item", i))
        if item.safe_near_baby:
            lines.append(asp.fact("safe", i))
    lines.append(asp.fact("bad_pair", "decorate", "rattle"))
    lines.append(asp.fact("bad_pair", "decorate", "lamp"))
    lines.append(asp.fact("bad_pair", "rock", "lamp"))
    lines.append(asp.fact("bad_pair", "nearby_light", "blanket"))
    lines.append(asp.fact("bad_pair", "nearby_light", "book"))
    lines.append(asp.fact("bad_pair", "nearby_light", "rattle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming cautionary nursery story world.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--parent-name")
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
    if args.activity and args.item:
        if (args.activity, args.item) not in combos:
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], ITEMS[args.item]))
    combos = [
        c for c in combos
        if (args.activity is None or c[0] == args.activity)
        and (args.item is None or c[1] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    act, item = rng.choice(sorted(combos))
    name = args.name or "Gyp"
    sibling_name = args.sibling_name or safe_choice(rng, NAMES)
    parent_name = args.parent_name or safe_choice(rng, ["Mom", "Dad", "Aunt", "Papa"])
    return StoryParams(activity=act, item=item, name=name, sibling_name=sibling_name, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible activity/item combos:\n")
        for act, item in combos:
            print(f"  {act:12} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(activity="decorate", item="blanket", name="Gyp", sibling_name="Mila", parent_name="Mom"),
            StoryParams(activity="rock", item="book", name="Gyp", sibling_name="Leo", parent_name="Dad"),
            StoryParams(activity="nearby_light", item="lamp", name="Gyp", sibling_name="Nora", parent_name="Aunt"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
