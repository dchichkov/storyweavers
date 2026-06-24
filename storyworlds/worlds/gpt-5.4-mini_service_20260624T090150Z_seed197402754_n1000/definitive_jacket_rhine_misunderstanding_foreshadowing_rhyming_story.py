#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/definitive_jacket_rhine_misunderstanding_foreshadowing_rhyming_story.py
===============================================================================================================

A small standalone storyworld about a child by the Rhine, a jacket, and a
gentle misunderstanding that is foreshadowed before it is fixed.

The story engine models:
- a child with feelings and physical state,
- a riverbank setting by the Rhine,
- a jacket that can keep the child warm,
- a harmless misunderstanding,
- a parent who notices the signs and helps set things right.

The prose is authored to sound like a rhyming story: short, child-facing,
concrete, and lightly musical, while still being driven by simulated world
state rather than a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    hint: str
    mess: str
    chill_gain: float
    risk_region: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Jacket:
    id: str
    label: str
    phrase: str
    warm: bool = True
    color: str = "yellow"
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = "breezy"
        self.river_name: str = "the Rhine"

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        clone.river_name = self.river_name
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def possessive_name(name: str) -> str:
    return name + "'" if name.endswith("s") else name + "'s"


def prefix_name(entity: Entity) -> str:
    return entity.id


def forecast(world: World, child: Entity, action: Action) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(child.id), action, narrate=False)
    jacket = sim.entities.get("jacket")
    return {
        "cold": child.meters.get("chill", 0.0) >= THRESHOLD,
        "jacket_needed": jacket is not None and child.meters.get("chill", 0.0) >= THRESHOLD,
        "misunderstanding": child.memes.get("confused", 0.0) >= THRESHOLD,
    }


def _rule_chill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("chill", 0.0) < THRESHOLD:
            continue
        sig = ("shiver", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["unease"] = ent.memes.get("unease", 0.0) + 1
        out.append(f"{ent.id} gave a tiny shiver in the breezy air.")
    return out


def _rule_jacket_help(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("chill", 0.0) < THRESHOLD:
            continue
        jacket = next((j for j in world.worn_items(ent) if j.id == "jacket"), None)
        if not jacket:
            continue
        sig = ("warm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["chill"] = max(0.0, ent.meters["chill"] - 1.0)
        ent.memes["comfort"] = ent.memes.get("comfort", 0.0) + 1
        out.append(f"The jacket kept {ent.id} warm and snug.")
    return out


def _rule_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    if not child or not parent:
        return out
    if child.memes.get("confused", 0.0) < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    out.append("The child looked puzzled, because the words had tangled like thread.")
    return out


CAUSAL_RULES = [_rule_chill, _rule_jacket_help, _rule_misunderstanding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def _do_action(world: World, child: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.afford:
        return
    child.meters[action.mess] = child.meters.get(action.mess, 0.0) + action.chill_gain
    child.meters["chill"] = child.meters.get("chill", 0.0) + action.chill_gain
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved a walk by {world.river_name}, "
        f"where ripples rolled and the willow trees swayed."
    )


def setup(world: World, child: Entity, parent: Entity, jacket: Entity, action: Action) -> None:
    world.say(
        f"{child.id} wore {article(jacket.label)} {jacket.phrase}, a definitive jacket "
        f"for a blustery day, and {child.pronoun('possessive')} {parent.type} smiled."
    )
    world.say(
        f"{child.id} liked to {action.verb}, and every splash and skip felt fine in the light."
    )


def foreshadow(world: World, child: Entity, action: Action) -> None:
    world.para()
    world.say(
        f"By {world.river_name}, the clouds were thin and gray, and the wind began to sway."
    )
    world.say(
        f"{child.id} wanted to {action.verb}, though the breeze said, 'Stay warm today.'"
    )


def misunderstanding(world: World, child: Entity, parent: Entity, jacket: Entity, action: Action) -> None:
    child.memes["confused"] = child.memes.get("confused", 0.0) + 1
    world.say(
        f"{child.id} frowned and thought the jacket was just for show, not for the chill that winds can blow."
    )
    world.say(
        f'"Do I need it for the rhine?" {child.id} asked, "or only for the rhyme?"'
    )
    propagate(world, narrate=True)


def gentle_fix(world: World, child: Entity, parent: Entity, jacket: Entity, action: Action) -> None:
    world.say(
        f"{parent.id} laughed a soft, kind laugh and said, "
        f'"It is for the breeze, the spray, and the time between; that is the definitive reason it is seen."'
    )
    jacket.worn_by = child.id
    child.memes["confused"] = 0.0
    child.memes["safe"] = child.memes.get("safe", 0.0) + 1
    child.meters["chill"] = max(0.0, child.meters.get("chill", 0.0) - 1.0)
    world.say(
        f"{child.id} pulled the jacket on and grinned, and the shiver in {child.id} slid away with the wind."
    )
    world.say(
        f"Then {child.id} could {action.verb} by {world.river_name}, warm as toast, with cheeks aglow and rosy most."
    )


def tell(setting: Setting, action: Action, jacket: Jacket, child_name: str = "Lina") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl"))
    parent = world.add(Entity(id="parent", kind="character", type="mother"))
    coat = world.add(Entity(
        id="jacket",
        type="jacket",
        label="jacket",
        phrase=jacket.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    coat.worn_by = None

    intro(world, child)
    setup(world, child, parent, coat, action)
    world.para()
    foreshadow(world, child, action)
    misunderstanding(world, child, parent, coat, action)
    world.para()
    gentle_fix(world, child, parent, coat, action)

    world.facts.update(
        child=child,
        parent=parent,
        jacket=coat,
        action=action,
        setting=setting,
        warmed=True,
        confused=child.memes.get("confused", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "rhinebank": Setting(place="the Rhine bank", afford={"walk", "skip", "dance"}),
    "path": Setting(place="the river path", afford={"walk", "skip"}),
    "meadow": Setting(place="the meadow near the Rhine", afford={"walk", "dance"}),
}

ACTIONS = {
    "walk": Action(
        id="walk",
        verb="walk along the stones",
        gerund="walking along the stones",
        hint="the wind nipped at little ears",
        mess="chill",
        chill_gain=1.0,
        risk_region="torso",
        keyword="wind",
        tags={"wind", "rhine", "chill"},
    ),
    "skip": Action(
        id="skip",
        verb="skip beside the water",
        gerund="skipping beside the water",
        hint="spray could kiss a sleeve",
        mess="chill",
        chill_gain=1.0,
        risk_region="torso",
        keyword="spray",
        tags={"spray", "rhine", "chill"},
    ),
    "dance": Action(
        id="dance",
        verb="dance on the bank",
        gerund="dancing on the bank",
        hint="a twirl could stir the breeze",
        mess="chill",
        chill_gain=1.0,
        risk_region="torso",
        keyword="breeze",
        tags={"breeze", "rhine", "chill"},
    ),
}

JACKETS = {
    "yellow": Jacket(id="yellow", label="yellow jacket", phrase="a bright yellow jacket", tags={"jacket", "warm"}),
    "red": Jacket(id="red", label="red jacket", phrase="a snug red jacket", tags={"jacket", "warm"}),
}

CURATED = [
    dataclass(type("StoryParams", (), {}))
]


@dataclass
class StoryParams:
    place: str
    action: str
    jacket: str
    name: str = "Lina"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    return [
        f'Write a gentle rhyming story about a child named {child.id} by the Rhine.',
        f"Tell a story where {child.id} wants to {action.verb} but needs a jacket for the breeze.",
        f'Write a short child-friendly story that uses the words "definitive", "jacket", and "Rhine".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    action = f["action"]
    jacket = f["jacket"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Where did {child.id} want to go and play?",
            answer=f"{child.id} wanted to play at {place}, by the Rhine, where the water and wind could make a little song.",
        ),
        QAItem(
            question=f"What was the jacket for?",
            answer=f"The jacket was for the breeze and the cool air, so {child.id} could stay warm while {child.id} {action.verb}.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding?",
            answer=f"{child.id} thought the jacket was only for show, but {parent.id} meant it was the sensible, definitive thing to wear for the chilly river air.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} put on the {jacket.label} and felt warm, so the day by the Rhine turned happy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jacket for?",
            answer="A jacket is a piece of clothing you wear over your clothes to help keep warm when the air feels cool or windy.",
        ),
        QAItem(
            question="What is the Rhine?",
            answer="The Rhine is a long river in Europe, and people can walk near its banks and look at the water.",
        ),
        QAItem(
            question="What does foreshadowing mean?",
            answer="Foreshadowing means giving little hints early in a story about what might happen later.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding is when someone thinks a thing means one idea, but another person means something different.",
        ),
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.worn_by:
            bits.append(f"worn_by={ent.worn_by}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world set by the Rhine.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--jacket", choices=JACKETS)
    ap.add_argument("--name")
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
    combos = [(p, a, j) for p in SETTINGS for a in ACTIONS for j in JACKETS]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.jacket:
        combos = [c for c in combos if c[2] == args.jacket]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action, jacket = rng.choice(sorted(combos))
    return StoryParams(place=place, action=action, jacket=jacket, name=args.name or "Lina")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], JACKETS[params.jacket], params.name)
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


ASP_RULES = r"""
place(rhinebank).
place(path).
place(meadow).

action(walk).
action(skip).
action(dance).

jacket(yellow).
jacket(red).

affords(rhinebank,walk).
affords(rhinebank,skip).
affords(rhinebank,dance).
affords(path,walk).
affords(path,skip).
affords(meadow,walk).
affords(meadow,dance).

valid_story(P,A,J) :- place(P), action(A), jacket(J), affords(P,A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in SETTINGS[p].afford:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for j in JACKETS:
        lines.append(asp.fact("jacket", j))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(p, a, j) for p in SETTINGS for a in SETTINGS[p].afford for j in JACKETS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in SETTINGS:
            for a in SETTINGS[p].afford:
                for j in JACKETS:
                    params = StoryParams(place=p, action=a, jacket=j, name="Lina")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
