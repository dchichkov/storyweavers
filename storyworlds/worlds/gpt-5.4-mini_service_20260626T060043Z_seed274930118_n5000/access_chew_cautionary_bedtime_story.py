#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/access_chew_cautionary_bedtime_story.py
===============================================================================================================

A small bedtime story world about access, chewing, and a gentle caution.

Premise:
- A sleepy child wants access to a tempting chewable bedtime treat.
- A parent notices the treat could be messy, sticky, or too exciting near sleep.
- They choose a safer bedtime alternative and end the night calm and cozy.

The world is built from a few typed entities:
- characters with physical meters and emotional memes
- objects with ownership, access, and chew-related risk
- a room-setting that determines what is reachable at bedtime

The story always aims for:
- a clear bedtime setup
- a warning based on the world state
- a cautious turn toward a safer choice
- a peaceful ending image proving what changed
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    accessible: bool = True
    chewy: bool = False
    sticky: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    bedtime: bool = True
    lights: str = "soft lamp light"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risky_chew: bool
    sticky: bool = False
    crunchy: bool = False
    sweet: bool = False
    accessible_in: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    soothes: set[str] = field(default_factory=set)
    keeps_dry: bool = False
    helps_sleep: bool = True
    access_note: str = ""
    tail: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.chew_target: Optional[str] = None
        self.access_granted: bool = False

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.chew_target = self.chew_target
        clone.access_granted = self.access_granted
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_chew_mess(world: World) -> list[str]:
    out: list[str] = []
    if not world.access_granted or not world.chew_target:
        return out
    chew = world.get(world.chew_target)
    if not chew.chewy or chew.meters.get("chewed", 0.0) < THRESHOLD:
        return out
    sig = ("sticky", chew.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if chew.sticky:
        chew.meters["sticky"] = chew.meters.get("sticky", 0.0) + 1
        out.append(f"The sweet chew left sticky little traces.")
    else:
        out.append(f"The chew was handled gently and stayed tidy.")
    return out


def _r_bedtime_soften(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("sleepy", 0.0) < THRESHOLD:
            continue
        sig = ("soften", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] = ent.memes.get("calm", 0.0) + 1
        out.append(f"The room grew softer around {ent.id}.")
    return out


CAUSAL_RULES = [
    Rule("chew_mess", _r_chew_mess),
    Rule("bedtime_soften", _r_bedtime_soften),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_detail(setting: Setting) -> str:
    return f"The {setting.place} was quiet under {setting.lights}."


def assess_access(item: Item, room: str) -> bool:
    return room in item.accessible_in


def predict_chew(world: World, child: Entity, item: Item) -> dict:
    sim = world.copy()
    sim.chew_target = item.id
    if assess_access(item, sim.setting.place):
        sim.access_granted = True
        sim.get(child.id).memes["curiosity"] = sim.get(child.id).memes.get("curiosity", 0.0) + 1
        sim.get(item.id).meters["chewed"] = sim.get(item.id).meters.get("chewed", 0.0) + 1
        propagate(sim, narrate=False)
    return {
        "sticky": bool(sim.get(item.id).meters.get("sticky", 0.0) >= THRESHOLD),
        "sleepy": sim.get(child.id).memes.get("sleepy", 0.0),
    }


def tell(setting: Setting, child: Entity, parent: Entity, item: Item, comfort: Comfort) -> World:
    world = World(setting)
    world.add(child)
    world.add(parent)
    snack = world.add(Entity(
        id=item.id,
        type="thing",
        label=item.label,
        phrase=item.phrase,
        kind="thing",
        accessible=True,
        chewy=True,
        sticky=item.sticky,
    ))
    world.add(Entity(
        id=comfort.id,
        type="thing",
        label=comfort.label,
        phrase=comfort.phrase,
        kind="thing",
        accessible=True,
    ))

    world.say(f"{child.id} was sleepy and tucked in under the blankets.")
    world.say(f"{setup_detail(setting)} {child.id} noticed {item.phrase} nearby.")
    world.say(f"{parent.id} had set it out for later, but {child.id} wanted access to {item.label}.")

    world.para()
    world.say(
        f"{child.id} asked for the {item.label}, because {child.pronoun('subject')} wanted to chew something sweet before sleep."
    )

    predicted = predict_chew(world, child, item)
    world.facts["predicted_sticky"] = predicted["sticky"]

    if item.risky_chew:
        world.say(
            f"{parent.id} shook {parent.pronoun('possessive')} head gently. "
            f'"Not now," {parent.pronoun()} said. "A sticky chew can cling to your teeth and wake your mouth up."'
        )
        child.memes["disappointment"] = child.memes.get("disappointment", 0.0) + 1
        child.memes["desire"] = child.memes.get("desire", 0.0) + 1
        world.say(f"{child.id} looked at the {item.label}, then at the soft pillow, and listened.")
        world.para()
        world.say(
            f"{parent.id} offered {comfort.phrase} instead, {comfort.access_note}. "
            f"It was a kinder bedtime choice."
        )
        child.memes["calm"] = child.memes.get("calm", 0.0) + 1
        child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1
        world.access_granted = False
        world.chew_target = item.id
        snack.meters["chewed"] = 0.0
        world.say(
            f"{child.id} set the {item.label} aside and accepted the {comfort.label}. "
            f"Then {child.pronoun()} snuggled down while {comfort.tail}."
        )
        propagate(world, narrate=True)
        world.say(
            f"In the end, the {item.label} stayed untouched, the room stayed tidy, and {child.id} drifted off to sleep."
        )
    else:
        world.say(
            f"{parent.id} smiled and said the chew was fine for a little while, so long as it stayed slow and neat."
        )
        world.access_granted = True
        world.chew_target = item.id
        snack.meters["chewed"] = 1.0
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        propagate(world, narrate=True)
        world.say(f"{child.id} chewed carefully and soon curled back into the blankets, calm and drowsy.")

    world.facts.update(child=child, parent=parent, item=item, comfort=comfort, setting=setting)
    return world


SETTINGS = {
    "bedroom": Setting(place="bedroom", bedtime=True, lights="soft lamp light"),
    "nursery": Setting(place="nursery", bedtime=True, lights="a gold nightlight"),
    "cottage_room": Setting(place="cottage room", bedtime=True, lights="a moon-bright window"),
}

ITEMS = {
    "taffy": Item(
        id="taffy",
        label="taffy",
        phrase="a sticky ribbon of taffy",
        risky_chew=True,
        sticky=True,
        sweet=True,
        accessible_in={"bedroom", "cottage_room"},
    ),
    "hard_candy": Item(
        id="hard_candy",
        label="hard candy",
        phrase="a shiny hard candy",
        risky_chew=True,
        sticky=True,
        sweet=True,
        accessible_in={"bedroom", "nursery"},
    ),
    "apple_slice": Item(
        id="apple_slice",
        label="apple slice",
        phrase="a soft apple slice",
        risky_chew=False,
        sticky=False,
        sweet=True,
        accessible_in={"bedroom", "nursery", "cottage_room"},
    ),
    "bread_crust": Item(
        id="bread_crust",
        label="bread crust",
        phrase="a small bread crust",
        risky_chew=False,
        sticky=False,
        accessible_in={"cottage_room", "nursery"},
    ),
}

COMFORTS = {
    "water_cup": Comfort(
        id="water_cup",
        label="cup of water",
        phrase="a small cup of water",
        soothes={"sticky", "thirsty"},
        access_note="it was already within easy reach",
        tail="the water waited beside the lamp",
    ),
    "soft_pillow": Comfort(
        id="soft_pillow",
        label="soft pillow",
        phrase="a soft pillow to hug",
        soothes={"upset", "tired"},
        access_note="it was tucked right beside the bed",
        tail="the pillow stayed warm in the child’s arms",
    ),
    "teeth_brush": Comfort(
        id="teeth_brush",
        label="toothbrush",
        phrase="a little toothbrush and a rinse",
        soothes={"sticky", "worry"},
        access_note="it was ready by the sink",
        tail="the toothbrush made the mouth feel fresh and sleepy",
    ),
}

CHILD_NAMES = ["Mina", "Theo", "Luna", "Iris", "Noah", "Pip"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]
TRAITS = ["sleepy", "gentle", "curious", "cautious"]


@dataclass
class StoryParams:
    place: str
    item: str
    comfort: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            if not assess_access(item, place):
                continue
            for comfort_id in COMFORTS:
                combos.append((place, item_id, comfort_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Item = f["item"]
    return [
        f'Write a bedtime story for a child named {child.id} about access to {item.label} and a gentle warning.',
        f"Tell a cautionary bedtime tale where {child.id} wants to chew {item.phrase} but {parent.id} keeps the room calm.",
        f'Write a soft story that includes the words "access" and "chew" and ends with a sleepy, safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item: Item = f["item"]
    comfort: Comfort = f["comfort"]
    place = f["setting"].place
    trait = f"{child.type}" if child.type else "child"
    qa = [
        QAItem(
            question=f"Who wanted access to {item.label} at bedtime?",
            answer=f"{child.id} wanted access to {item.label} while the room was getting ready for sleep.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {child.id} about chewing {item.label}?",
            answer=(
                f"{parent.id} warned {child.id} because {item.phrase} could get sticky and keep {child.pronoun('possessive')} mouth busy when it was time to sleep."
            ),
        ),
        QAItem(
            question=f"What did they choose instead of chewing {item.label}?",
            answer=(
                f"They chose {comfort.phrase} instead, which was a calmer bedtime choice in the {place}."
            ),
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=(
                f"{child.id} settled down with {comfort.label}, and the {item.label} stayed put while the room turned quiet and sleepy."
            ),
        ),
    ]
    if f.get("predicted_sticky"):
        qa.append(
            QAItem(
                question=f"What was the warning about the chew at bedtime?",
                answer=(
                    f"The warning was that chewing {item.label} could make things sticky and wake {child.id} up instead of helping {child.id} rest."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "access": [
        QAItem(
            question="What does access mean?",
            answer="Access means being able to reach or use something.",
        )
    ],
    "chew": [
        QAItem(
            question="What does chew mean?",
            answer="Chew means to bite and work food with your teeth before swallowing it.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do people try to stay calm at bedtime?",
            answer="People try to stay calm at bedtime so their bodies can slow down and rest well.",
        )
    ],
    "sticky": [
        QAItem(
            question="Why can sticky food be tricky near bedtime?",
            answer="Sticky food can cling to teeth and make cleanup harder, which is why grown-ups often keep it for earlier in the day.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["access"])
    out.extend(WORLD_KNOWLEDGE["chew"])
    out.extend(WORLD_KNOWLEDGE["bedtime"])
    if world.facts["item"].sticky:
        out.extend(WORLD_KNOWLEDGE["sticky"])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  access_granted={world.access_granted}")
    lines.append(f"  chew_target={world.chew_target}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", item="taffy", comfort="water_cup", name="Mina", parent="Mom", trait="sleepy"),
    StoryParams(place="nursery", item="hard_candy", comfort="teeth_brush", name="Theo", parent="Dad", trait="curious"),
    StoryParams(place="cottage_room", item="taffy", comfort="soft_pillow", name="Luna", parent="Mama", trait="cautious"),
]


ASP_RULES = r"""
% Access is possible when the item can be reached in the current room.
reachable(I, P) :- item(I), place(P), available_in(I, P).

% A chew is risky when the item is sticky or the story marks it as risky.
risky_chew(I) :- item(I), sticky(I).
risky_chew(I) :- item(I), risky(I).

% A valid bedtime story has an accessible item, a cautious warning,
% and a safer comfort object offered instead.
valid_story(P, I, C) :- reachable(I, P), comfort(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.risky_chew:
            lines.append(asp.fact("risky", iid))
        if item.sticky:
            lines.append(asp.fact("sticky", iid))
        if item.sweet:
            lines.append(asp.fact("sweet", iid))
        for p in sorted(item.accessible_in):
            lines.append(asp.fact("available_in", iid, p))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary bedtime story world about access and chew.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["Mom", "Dad", "Mama", "Papa"])
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid bedtime combo matches the given options.)")
    place, item, comfort = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, comfort=comfort, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    child = Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Luna", "Iris"} else "boy")
    parent = Entity(id=params.parent, kind="character", type="mother" if params.parent in {"Mom", "Mama"} else "father")
    child.memes["sleepy"] = 1.0
    child.memes["curiosity"] = 1.0
    item = ITEMS[params.item]
    comfort = COMFORTS[params.comfort]
    world = tell(setting, child, parent, item, comfort)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid bedtime combos:")
        for place, item, comfort in combos:
            print(f"  {place:12} {item:12} {comfort}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
