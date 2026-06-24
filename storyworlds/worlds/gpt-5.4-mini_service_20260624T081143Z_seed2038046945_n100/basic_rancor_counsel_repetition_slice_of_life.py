#!/usr/bin/env python3
"""
storyworlds/worlds/basic_rancor_counsel_repetition_slice_of_life.py
===================================================================

A small slice-of-life storyworld about a basic daily task, a little rancor,
and counsel that helps everyone settle into a better rhythm.

Premise:
- A child wants to do a basic everyday activity at home.
- A sibling or parent is annoyed by repetition or small mess.
- Careful counsel turns the rancor into a calmer routine.

The world is intentionally modest:
- one household setting
- one repeated action that can become irritating
- one advisory turn that suggests a better method
- one gentle resolution image proving the change

The prose should feel like a tiny authored story, not an event log.
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

BASIC_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    time_of_day: str = "morning"
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    repeated_line: str
    strain: str
    mess: str
    tag: str = ""


@dataclass
class Counsel:
    id: str
    label: str
    method: str
    result_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def repeat_line(activity: Activity, count: int) -> str:
    return " ".join([activity.repeated_line] * count)


def build_basic_world() -> tuple[Setting, dict[str, Activity], dict[str, Counsel]]:
    setting = Setting(place="the kitchen", time_of_day="morning", afford={"wash", "stack"})
    activities = {
        "wash_dishes": Activity(
            id="wash_dishes",
            verb="wash the dishes",
            gerund="washing the dishes",
            repeated_line="splash, swish, rinse",
            strain="annoying",
            mess="splash",
            tag="dishes",
        ),
        "fold_laundry": Activity(
            id="fold_laundry",
            verb="fold the laundry",
            gerund="folding the laundry",
            repeated_line="fold, fold, fold",
            strain="boring",
            mess="crease",
            tag="laundry",
        ),
    }
    counsel = {
        "slow_down": Counsel(
            id="slow_down",
            label="slow, clear counsel",
            method="count the steps and use a small towel",
            result_line="Once they slowed down, the work felt easier.",
        ),
        "share_job": Counsel(
            id="share_job",
            label="simple counsel",
            method="take turns and switch after each small part",
            result_line="Taking turns kept the room calm.",
        ),
    }
    return setting, activities, counsel


def tell_story(setting: Setting, activity: Activity, counsel: Counsel,
               child_name: str, sibling_name: str, child_type: str,
               sibling_type: str) -> World:
    world = World(setting)

    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_type))
    sink = world.add(Entity(id="sink", type="sink", label="the sink", caretaker=child.id))
    table = world.add(Entity(id="table", type="table", label="the table", caretaker=sibling.id))

    world.say(f"It was a basic morning in {setting.place}.")
    world.say(
        f"{child.id} wanted to {activity.verb}, and {child.pronoun()} liked the steady rhythm of {activity.gerund}."
    )
    world.say(
        f"Nearby, {sibling.id} kept hearing {repeat_line(activity, 2)} again and again."
    )
    sibling.memes["rancor"] += 1
    world.say(
        f"That repetition made {sibling.pronoun('object')} feel a little rancor."
    )

    world.para()
    world.say(
        f"{sibling.id} crossed {sibling.pronoun('possessive')} arms and said, "
        f'"Too much noise. Too much {activity.tag}."'
    )
    child.memes["desire"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} paused, then looked at {sibling.id} and listened."
    )
    world.say(
        f"After a moment, {child.id} asked for counsel instead of arguing."
    )

    world.para()
    child.memes["counsel"] += 1
    sibling.memes["counsel"] += 1
    world.say(
        f"{counsel.label} came in the form of a small idea: {counsel.method}."
    )
    world.say(
        f"{child.id} tried it once, then again, and the work got quieter."
    )
    sibling.memes["rancor"] = 0
    child.memes["calm"] += 1
    world.say(counsel.result_line)

    world.para()
    world.say(
        f"In the end, {child.id} finished {activity.gerund}, and {sibling.id} set the last clean dish by {sink.label}."
    )
    world.say(
        f"The kitchen stayed simple and neat, and the basic morning became a better one."
    )

    world.facts.update(
        child=child,
        sibling=sibling,
        sink=sink,
        table=table,
        activity=activity,
        counsel=counsel,
        setting=setting,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", time_of_day="morning", afford={"wash", "stack"}),
    "laundry_room": Setting(place="the laundry room", time_of_day="afternoon", afford={"fold"}),
}

ACTIVITIES = build_basic_world()[1]
COUNSELS = build_basic_world()[2]

NAMES = ["Mia", "Noah", "Lena", "Eli", "Ruby", "Finn", "Sara", "Theo"]
TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    counsel: str
    child_name: str
    child_type: str
    sibling_name: str
    sibling_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for activity_id in setting.afford:
            for counsel_id in COUNSELS:
                out.append((place, activity_id, counsel_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life storyworld about a basic task, rancor, and counsel."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--counsel", choices=COUNSELS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=TYPES)
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-type", choices=TYPES)
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
              and (args.activity is None or c[1] == args.activity)
              and (args.counsel is None or c[2] == args.counsel)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, counsel = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(TYPES)
    sibling_type = args.sibling_type or ("boy" if child_type == "girl" else "girl")
    child_name = args.child_name or rng.choice(NAMES)
    sibling_name = args.sibling_name or rng.choice([n for n in NAMES if n != child_name])
    return StoryParams(
        place=place,
        activity=activity,
        counsel=counsel,
        child_name=child_name,
        child_type=child_type,
        sibling_name=sibling_name,
        sibling_type=sibling_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a small slice-of-life story about {f['child'].id} doing a basic chore in {f['setting'].place}.",
        f"Tell a gentle story where repetition causes a little rancor, then counsel helps the family settle down.",
        f"Write a child-facing story that uses the words basic, rancor, and counsel naturally.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    activity = f["activity"]
    counsel = f["counsel"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What basic thing did {child.id} want to do in {place}?",
            answer=f"{child.id} wanted to {activity.verb}. It was a basic morning task in {place}.",
        ),
        QAItem(
            question=f"Why did {sibling.id} feel rancor during the morning?",
            answer=f"{sibling.id} felt rancor because the repeated {activity.repeated_line} sounds kept coming back again and again.",
        ),
        QAItem(
            question=f"What kind of counsel helped the two children?",
            answer=f"{counsel.label} helped when they used this idea: {counsel.method}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} finishing {activity.gerund} and the kitchen staying calm and neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does basic mean?", answer="Basic means simple, ordinary, and easy to understand."),
        QAItem(question="What is rancor?", answer="Rancor is a strong feeling of bitterness or anger that can linger after people get upset."),
        QAItem(question="What is counsel?", answer="Counsel is advice or guidance that helps someone choose a better way."),
        QAItem(question="Why can repetition be annoying?", answer="Repetition can be annoying because hearing or seeing the same thing again and again can wear on people's patience."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        COUNSELS[params.counsel],
        params.child_name,
        params.sibling_name,
        params.child_type,
        params.sibling_type,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(place, activity, counsel) :- setting(place), affords(place, activity), counsel_kind(counsel).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(s.afford):
            lines.append(asp.fact("affords", place, act))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for cid in COUNSELS:
        lines.append(asp.fact("counsel_kind", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("kitchen", "wash_dishes", "slow_down", "Mia", "girl", "Noah", "boy"),
    StoryParams("kitchen", "stack", "share_job", "Eli", "boy", "Ruby", "girl"),
    StoryParams("laundry_room", "fold_laundry", "slow_down", "Lena", "girl", "Theo", "boy"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not fit the small slice-of-life home routine.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
