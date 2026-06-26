#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/keen_sound_effects_curiosity_dialogue_slice_of.py
===============================================================================================================

A small slice-of-life storyworld about a keen child, sound effects, curiosity,
and dialogue.

Premise:
- A child is very keen on the little sounds of ordinary life.
- They want to make sound effects for a pretend story.
- A caregiver worries about noise because someone nearby needs quiet.
- They find a gentle compromise using softer props and a listening game.

The world is intentionally compact: a few settings, a few sound activities, and
a few household props that can either be too loud or just right.
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
    quiet: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
    nearby_quiet: str = "someone is resting"


@dataclass
class Activity:
    id: str
    label: str
    sound: str
    curiosity: str
    loudness: float
    keyword: str


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    quiet: bool
    good_for: set[str]


@dataclass
class StoryParams:
    place: str
    activity: str
    prop: str
    name: str
    gender: str
    caretaker: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about keen curiosity, sound effects, and dialogue."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
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
    if args.activity and args.prop:
        act, prop = ACTIVITIES[args.activity], PROPS[args.prop]
        if act.id not in prop.good_for:
            raise StoryError(
                f"(No story: {prop.label} does not fit the sound kind '{act.label}'. "
                f"Choose a prop that makes that sound naturally.)"
            )
    combos = [
        (place, act_id, prop_id)
        for place, setting in SETTINGS.items()
        for act_id in setting.affords
        for prop_id, prop in PROPS.items()
        if act_id in prop.good_for
        and (args.place is None or place == args.place)
        and (args.activity is None or act_id == args.activity)
        and (args.prop is None or prop_id == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act_id, prop_id = rng.choice(sorted(combos))
    prop = PROPS[prop_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=act_id, prop=prop_id, name=name, gender=gender, caretaker=caretaker)


def _quiet_need(setting: Setting) -> str:
    return setting.nearby_quiet


def _do_activity(world: World, child: Entity, activity: Activity, prop: Entity, narrate: bool = True) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.meters["loudness"] = child.meters.get("loudness", 0.0) + activity.loudness
    prop.meters["used"] = prop.meters.get("used", 0.0) + 1
    if not prop.quiet:
        prop.meters["noise"] = prop.meters.get("noise", 0.0) + activity.loudness
    if narrate:
        world.say(f'{child.id} went, "{activity.sound}" and listened closely to the tiny echo.')


def predict_noise(world: World, child: Entity, activity: Activity, prop: Entity) -> bool:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_prop = sim.get(prop.id)
    _do_activity(sim, sim_child, activity, sim_prop, narrate=False)
    return bool(sim_prop.meters.get("noise", 0.0) >= THRESHOLD and not sim_prop.quiet)


def intro(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a keen little listener who noticed every creak, tap, and hush.")


def love_sounds(world: World, child: Entity, activity: Activity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.pronoun().capitalize()} loved sound effects, especially the {activity.sound} sound "
        f"that made pretend adventures feel real."
    )


def setup(world: World, child: Entity, caretaker: Entity, prop: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {child.id} found {prop.phrase} in {world.setting.place} and wanted to use it for a story."
    )
    world.say(
        f'"Can I make a {activity.label} sound?" {child.pronoun("subject")} asked. '
        f'"Maybe," {caretaker.pronoun("subject")} said, "but we need { _quiet_need(world.setting) }."'
    )


def turn(world: World, child: Entity, caretaker: Entity, prop: Entity, activity: Activity) -> None:
    if predict_noise(world, child, activity, prop):
        child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
        world.say(
            f'{child.id} tilted {child.pronoun("possessive")} head. "What if I try it softly?" '
            f"{caretaker.pronoun('subject').capitalize()} paused and listened."
        )
        world.say(
            f'"That could work," {caretaker.id} said. "Let\'s find the quietest way."'
        )
    else:
        world.say(
            f"{caretaker.id} smiled right away. \"That sound is already gentle,\" "
            f"{caretaker.pronoun('subject')} said."
        )


def resolve(world: World, child: Entity, caretaker: Entity, prop: Entity, activity: Activity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.id} tapped {prop.label} softly: {activity.sound}, {activity.sound}."
    )
    world.say(
        f"{caretaker.id} laughed and said, \"Perfect. That makes a nice sound without waking anyone.\""
    )
    world.say(
        f"By the end, {child.id} was still keen, but now {child.pronoun('subject')} was keen on quiet little sounds, too."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    prop = PROPS[params.prop]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=params.caretaker, label=params.caretaker))
    item = world.add(Entity(
        id="prop",
        kind="thing",
        type=prop.id,
        label=prop.label,
        phrase=prop.phrase,
        quiet=prop.quiet,
        caretaker=caretaker.id,
        owner=child.id,
    ))

    intro(world, child)
    love_sounds(world, child, act)
    world.para()
    setup(world, child, caretaker, item, act)
    turn(world, child, caretaker, item, act)
    world.para()
    _do_activity(world, child, act, item, narrate=True)
    resolve(world, child, caretaker, item, act)

    world.facts.update(child=child, caretaker=caretaker, prop=item, activity=act, setting=setting)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"kettle", "spoon", "jar"}, nearby_quiet="a nap on the couch"),
    "hallway": Setting(place="the hallway", indoors=True, affords={"shoes", "broom"}, nearby_quiet="a phone call nearby"),
    "backyard": Setting(place="the backyard", indoors=False, affords={"wind", "jar"}, nearby_quiet="a neighbor reading on the porch"),
}

ACTIVITIES = {
    "kettle": Activity(id="kettle", label="kettle whistle", sound="fweee", curiosity="steam and hiss", loudness=1.0, keyword="whistle"),
    "spoon": Activity(id="spoon", label="spoon tap", sound="ting-ting", curiosity="bright little clicks", loudness=0.4, keyword="tap"),
    "jar": Activity(id="jar", label="jar rattle", sound="clink-clink", curiosity="tiny shaking sounds", loudness=0.6, keyword="rattle"),
    "shoes": Activity(id="shoes", label="shoe squeak", sound="squeak", curiosity="sliding steps", loudness=0.5, keyword="squeak"),
    "broom": Activity(id="broom", label="broom swish", sound="swishhh", curiosity="brushing sounds", loudness=0.3, keyword="swish"),
    "wind": Activity(id="wind", label="wind sound", sound="whooo", curiosity="soft moving air", loudness=0.2, keyword="wind"),
}

PROPS = {
    "whistle": Prop(id="whistle", label="the kettle", phrase="the shiny kettle on the stove", sound="fweee", quiet=False, good_for={"kettle"}),
    "spoon": Prop(id="spoon", label="a wooden spoon", phrase="a wooden spoon in the drawer", sound="ting-ting", quiet=True, good_for={"spoon"}),
    "jar": Prop(id="jar", label="a little jar of buttons", phrase="a little jar full of buttons", sound="clink-clink", quiet=False, good_for={"jar"}),
    "shoes": Prop(id="shoes", label="the hallway shoes", phrase="the shoes by the door", sound="squeak", quiet=False, good_for={"shoes"}),
    "broom": Prop(id="broom", label="the broom", phrase="the broom leaning by the wall", sound="swishhh", quiet=True, good_for={"broom"}),
    "windchime": Prop(id="windchime", label="the wind chime", phrase="the wind chime hanging outside", sound="ding-ding", quiet=False, good_for={"wind"}),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Zoe", "Ava", "Mia"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Sam", "Max", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prop_id, prop in PROPS.items():
                if act in prop.good_for:
                    combos.append((place, act, prop_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    act: Activity = f["activity"]
    return [
        f"Write a short slice-of-life story about a keen child named {child.id} who wants to hear a {act.label} sound.",
        f"Tell a gentle story with curiosity and dialogue where {child.id} asks to make the sound '{act.sound}'.",
        f"Write a small domestic story about {child.id}, a household sound, and a quiet compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caretaker: Entity = f["caretaker"]
    act: Activity = f["activity"]
    prop: Entity = f["prop"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was {child.id} keen to do in {setting.place}?",
            answer=f"{child.id} was keen to make a {act.label} sound and listen to how it echoed in {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.id} ask about the {prop.label}?",
            answer=f"{child.id} asked if {child.pronoun('subject')} could use {prop.phrase} to make a {act.label} sound.",
        ),
        QAItem(
            question=f"Why did {caretaker.id} want the sound to stay gentle?",
            answer=f"{caretaker.id} wanted to keep things quiet because { _quiet_need(setting) } and the household needed a soft mood.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} making {act.sound}, {act.sound} softly and finding a quiet way to enjoy the sound.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "kettle": [
        QAItem(question="What does a kettle do when it boils?", answer="A kettle makes steam and a whistle sound when the water gets very hot."),
    ],
    "spoon": [
        QAItem(question="What sound can a spoon make?", answer="A spoon can make a small tapping sound when it hits a cup or bowl."),
    ],
    "jar": [
        QAItem(question="Why does a jar of buttons rattle?", answer="A jar rattles when the buttons inside bump against the glass and each other."),
    ],
    "shoes": [
        QAItem(question="Why can shoes squeak on a floor?", answer="Shoes can squeak when the soles rub against a smooth floor."),
    ],
    "broom": [
        QAItem(question="What sound does a broom make?", answer="A broom can make a soft swishing sound when it sweeps across the floor."),
    ],
    "wind": [
        QAItem(question="What does wind sound like?", answer="Wind can sound like a soft whooo or a whisper moving past your ears."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act: Activity = f["activity"]
    return list(WORLD_KNOWLEDGE.get(act.id, []))


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.quiet:
            bits.append("quiet=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="spoon", prop="spoon", name="Maya", gender="girl", caretaker="mother"),
    StoryParams(place="hallway", activity="broom", prop="broom", name="Leo", gender="boy", caretaker="father"),
    StoryParams(place="backyard", activity="wind", prop="windchime", name="Nora", gender="girl", caretaker="mother"),
]


ASP_RULES = r"""
% A story is valid when a place affords the activity and the prop naturally fits it.
valid(Place, Act, Prop) :- affords(Place, Act), fits(Prop, Act).

% Quiet props are preferred when the activity could otherwise be loud.
quiet_choice(Prop) :- prop(Prop), quiet(Prop).

% The declarative twin for the Python reasonableness gate.
compatible(Place, Act, Prop) :- valid(Place, Act, Prop).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("fits", aid, aid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.quiet:
            lines.append(asp.fact("quiet", pid))
        for a in sorted(prop.good_for):
            lines.append(asp.fact("fits", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} in {p.place} ({p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
