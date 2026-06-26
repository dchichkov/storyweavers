#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bubble_fine_dialogue_comedy.py
===============================================================================================================

A small, standalone story world built from the seed words "bubble" and "fine".
The world is a comedy of dialogue: a child wants to make bubbles, a grown-up
worries about a fine, and the two find a funny, safe compromise.

The simulation tracks both physical meters and emotional memes. The story is not
a frozen paragraph: it is assembled from a world model that changes as the
dialogue plays out.

Premise:
- A child loves bubbles.
- The chosen setting has a rule or risk that makes bubble play potentially
  troublesome.
- A parent or guardian notices the danger of a fine.
- The child pushes back in a comic way.
- A compromise avoids the fine and still gives the child bubbles.

This script supports:
- default runs
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    holds: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["bubble", "spill", "fine_risk"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "embarrassment", "humor", "relief", "stubbornness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister"}
        male = {"boy", "father", "dad", "man", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    indoors: bool
    forbids_bubbles: bool = False
    fine_amount: int = 0
    allows: set[str] = field(default_factory=set)


@dataclass
class BubbleActivity:
    id: str
    verb: str
    gerund: str
    rash: str
    keyword: str = "bubble"
    bubble_kind: str = "soap bubble"
    mess: str = "slippery"
    risk: str = "a fine"
    noise: str = "puffing"
    tags: set[str] = field(default_factory=lambda: {"bubble"})


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    prevents: set[str]
    prep: str
    tail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library_steps": Setting(
        id="library_steps",
        place="the library steps",
        indoors=False,
        forbids_bubbles=True,
        fine_amount=12,
        allows={"bubble"},
    ),
    "bakery_patio": Setting(
        id="bakery_patio",
        place="the bakery patio",
        indoors=False,
        forbids_bubbles=True,
        fine_amount=8,
        allows={"bubble"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        indoors=False,
        forbids_bubbles=False,
        fine_amount=0,
        allows={"bubble"},
    ),
    "bathroom": Setting(
        id="bathroom",
        place="the bathroom",
        indoors=True,
        forbids_bubbles=False,
        fine_amount=0,
        allows={"bubble"},
    ),
}

ACTIVITIES = {
    "bubble_wand": BubbleActivity(
        id="bubble_wand",
        verb="blow bubbles",
        gerund="blowing bubbles",
        rash="run after every shiny bubble",
        bubble_kind="soap bubble",
        mess="slippery",
        risk="a fine",
        noise="puffing",
        tags={"bubble", "soap"},
    ),
    "bubble_machine": BubbleActivity(
        id="bubble_machine",
        verb="start the bubble machine",
        gerund="watching bubbles drift up",
        rash="chase the spinning stream",
        bubble_kind="bubble stream",
        mess="slippery",
        risk="a fine",
        noise="whirring",
        tags={"bubble", "machine"},
    ),
}

GADGETS = [
    Gear(
        id="sign",
        label="a little sign",
        phrase="a little sign that said 'Bubbles Here'",
        covers={"setting"},
        prevents={"fine"},
        prep="move to the marked spot",
        tail="stood under the sign and kept the bubbles in the right place",
        tags={"bubble"},
    ),
    Gear(
        id="mat",
        label="a rubber mat",
        phrase="a rubber mat that kept feet from sliding",
        covers={"ground"},
        prevents={"slip"},
        prep="put down the rubber mat first",
        tail="played on the mat and kept the floor safe",
        tags={"bubble"},
    ),
    Gear(
        id="tray",
        label="a tray",
        phrase="a tray to catch drips",
        covers={"hands"},
        prevents={"spill"},
        prep="hold the wand over the tray",
        tail="caught the drips before they could make trouble",
        tags={"bubble"},
    ),
]

GIRL_NAMES = ["Mia", "Lila", "Nora", "Zoe", "Ava", "Ivy", "Poppy", "Ruby"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Ben", "Sam", "Owen", "Jude"]
TRAITS = ["curious", "silly", "cheerful", "spirited", "bouncy", "impish"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting forbids bubble play when the activity would trigger a fine there.
forbidden(S,A) :- setting(S), activity(A), forbids_bubbles(S), bubble_act(A).

% A compatible fix exists when there is a gear item that addresses the same
% problem the setting creates (e.g. a sign for a place that needs a marked zone).
has_fix(S,A) :- forbidden(S,A), setting_fix(S,A).

valid_story(S,A) :- setting(S), activity(A), allows(S,A), has_fix(S,A).

% A story is reasonable only if it is forbidden before the fix.
reasonably_tense(S,A) :- forbidden(S,A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.forbids_bubbles:
            lines.append(asp.fact("forbids_bubbles", sid))
        if s.fine_amount:
            lines.append(asp.fact("fine_amount", sid, s.fine_amount))
        for a in sorted(s.allows):
            lines.append(asp.fact("allows", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("bubble_act", aid))
        lines.append(asp.fact("risk", aid, a.risk))
    for g in GADGETS:
        for t in sorted(g.tags):
            lines.append(asp.fact("setting_fix", "library_steps", "bubble_wand") if t == "bubble" else "")
    # We intentionally emit a compact fact set; the rules only need categories.
    lines = [x for x in lines if x]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    out = []
    for sid, s in SETTINGS.items():
        for aid in ACTIVITIES:
            if s.allows and "bubble" in s.allows:
                if s.forbids_bubbles:
                    out.append((sid, aid))
    return sorted(set(out))


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(setting: Setting, activity: BubbleActivity, hero_name: str, gender: str,
                parent_type: str, trait: str) -> World:
    w = World(setting)
    child = w.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    parent = w.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    bubble = w.add(Entity(
        id="bubbles",
        kind="thing",
        type="toy",
        label=activity.bubble_kind,
        phrase=activity.bubble_kind,
        owner=child.id,
    ))
    w.facts.update(child=child, parent=parent, bubble=bubble, activity=activity, trait=trait)
    return w


def predict_fine(world: World, activity: BubbleActivity) -> bool:
    return world.setting.forbids_bubbles and activity.id in {"bubble_wand", "bubble_machine"}


def perform_activity(world: World, child: Entity, activity: BubbleActivity) -> None:
    child.meters["bubble"] += 1
    child.memes["joy"] += 1
    if world.setting.indoors:
        child.meters["spill"] += 0.25
    world.say(
        f"{child.name} started {activity.gerund}, and the room filled with {activity.noise} little bursts."
    )


def warn(world: World, parent: Entity, child: Entity, activity: BubbleActivity) -> bool:
    if not predict_fine(world, activity):
        return False
    amount = world.setting.fine_amount
    child.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.facts["predicted_fine"] = amount
    world.say(
        f'"If you do that here, we could get a fine," {parent.name} said. '
        f'"A real one, not a tiny one."'
    )
    return True


def joke(world: World, child: Entity, parent: Entity) -> None:
    child.memes["humor"] += 1
    child.memes["stubbornness"] += 1
    world.say(
        f'"But bubbles are already fine," {child.name} said. '
        f'"They are round, shiny, and very polite."'
    )
    world.say(
        f"{parent.name} blinked, then laughed despite trying not to."
    )


def offer_fix(world: World, parent: Entity, child: Entity, activity: BubbleActivity) -> Gear:
    if world.setting.id == "library_steps":
        gear = GADGETS[0]
    elif world.setting.id == "bakery_patio":
        gear = GADGETS[1]
    else:
        gear = GADGETS[2]
    world.facts["gear"] = gear
    world.say(
        f'"Fine," {parent.name} said, with a grin. "Let us {gear.prep}."'
    )
    return gear


def accept_fix(world: World, child: Entity, parent: Entity, gear: Gear, activity: BubbleActivity) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f'{child.name} hopped in place and said, "That is a fine idea!"'
    )
    if gear.id == "sign":
        world.say(
            f"They moved to the marked spot, and {child.name} kept the bubbles where they belonged."
        )
    elif gear.id == "mat":
        world.say(
            f"They spread out the mat, and nobody slipped while the bubbles floated up like tiny moons."
        )
    else:
        world.say(
            f"They used the tray, and every drippy bubble stayed neat enough to make the grown-ups smile."
        )


def resolve_story(world: World, child: Entity, parent: Entity, activity: BubbleActivity) -> None:
    perform_activity(world, child, activity)
    world.para()
    if warn(world, parent, child, activity):
        joke(world, child, parent)
        world.para()
        gear = offer_fix(world, parent, child, activity)
        accept_fix(world, child, parent, gear, activity)
    else:
        world.say(
            f"{parent.name} watched for a moment and decided the bubbles were fine right where they were."
        )
        child.memes["relief"] += 1
    world.para()
    world.say(
        f"At the end, the bubbles were still drifting, the grown-up was not paying any fine, and {child.name} was laughing at the shiny mess of it all."
    )


def tell(setting: Setting, activity: BubbleActivity, hero_name: str, gender: str,
         parent_type: str, trait: str) -> World:
    world = build_world(setting, activity, hero_name, gender, parent_type, trait)
    child = world.get(hero_name)
    parent = world.get("parent")
    world.say(
        f"{hero_name} was a {trait} little {gender} who loved bubbles almost more than snacks."
    )
    world.say(
        f"{hero_name} liked the way a bubble could wobble, flash rainbow colors, and pop with a tiny blink."
    )
    world.para()
    world.say(
        f"One day, {hero_name} wanted to {activity.verb} at {setting.place}."
    )
    resolve_story(world, child, parent, activity)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    activity: BubbleActivity = f["activity"]
    trait = f["trait"]
    gear: Optional[Gear] = f.get("gear")
    questions = [
        QAItem(
            question=f"What did {child.name} want to do?",
            answer=f"{child.name} wanted to {activity.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.name} worry about a fine?",
            answer=(
                f"{parent.name} worried because {world.setting.place} was a place where bubbles could cause trouble, "
                f"and the rule could lead to {world.setting.fine_amount} dollars of fine if they stayed there without a fix."
            ),
        ),
        QAItem(
            question=f"How did {child.name} react when the grown-up mentioned the fine?",
            answer=(
                f"{trait.capitalize()} {child.name} joked that bubbles were already fine, which made {parent.name} laugh."
            ),
        ),
    ]
    if gear:
        questions.append(
            QAItem(
                question="What plan helped the bubbles stay okay?",
                answer=(
                    f"They used {gear.phrase}, so {child.name} could keep playing without causing a fine."
                ),
            )
        )
    return questions


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bubble?",
            answer="A bubble is a thin шар of air wrapped in soap or liquid, and it floats for a moment before popping.",
        ),
        QAItem(
            question="What is a fine?",
            answer="A fine is money you have to pay when you break a rule or do something you are not supposed to do.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    activity: BubbleActivity = f["activity"]
    return [
        f"Write a funny short story where {child.name} wants to {activity.verb} and an adult worries about a fine.",
        f"Tell a dialogue-driven comedy about bubbles, a rule, and a clever fix.",
        f"Make a child-friendly story that uses the words 'bubble' and 'fine' and ends with everyone laughing.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    out.append(f"setting={world.setting.id}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bubble/fine comedy storyworld with dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        if s.forbids_bubbles:
            for aid in ACTIVITIES:
                combos.append((sid, aid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.activity and (args.setting, args.activity) not in combos:
        raise StoryError("That setting/activity pair does not make a good bubble story.")
    matching = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.activity is None or c[1] == args.activity)
    ]
    if not matching:
        raise StoryError("No valid story matches the chosen filters.")
    setting, activity = rng.choice(sorted(matching))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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


# ---------------------------------------------------------------------------
# ASP / verify
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import storyworlds.asp as asp

    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: ASP and Python agree on {len(a)} valid story shapes.")
        return 0
    print("MISMATCH:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="library_steps", activity="bubble_wand", name="Mia", gender="girl", parent="mother", trait="silly"),
            StoryParams(setting="bakery_patio", activity="bubble_wand", name="Leo", gender="boy", parent="father", trait="curious"),
            StoryParams(setting="backyard", activity="bubble_machine", name="Nora", gender="girl", parent="mother", trait="impish"),
            StoryParams(setting="bathroom", activity="bubble_wand", name="Finn", gender="boy", parent="father", trait="cheerful"),
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
