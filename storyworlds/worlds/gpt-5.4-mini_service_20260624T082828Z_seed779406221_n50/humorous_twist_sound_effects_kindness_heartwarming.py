#!/usr/bin/env python3
"""
storyworlds/worlds/humorous_twist_sound_effects_kindness_heartwarming.py
========================================================================

A small story world about a child, a friendly plan, noisy sound effects, and a
kind twist that turns a hiccup into a warm ending.

Seed premise:
---
A child wants to put on a funny sound-effects show, but something goes wrong
with the props. Instead of getting mad, the child and a helper use kindness,
share the job, and make the performance even better.

World model:
---
- Physical meters track volume, wobble, brokenness, and sparkle.
- Emotional memes track excitement, worry, embarrassment, kindness, and joy.
- A humorous twist can change the plan, but it must be caused by the world state.
- Sound effects are concrete acts that raise volume and can spill into a scene.
- Kindness is the resolving force that repairs a social problem and completes
  the little performance.

The story should feel child-facing, concrete, warm, and gently funny.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the living room"
    indoor: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    sound: str
    mess: str
    twist: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    fixed_by: str = ""
    makes: str = ""
    owner_role: str = "child"
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    offer: str
    tail: str
    makes: str
    kind: str = "character"
    type: str = "adult"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.active_act: str = ""
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.active_act = self.active_act
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    act: str
    prop: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "living_room": Setting(place="the living room", indoor=True, affordances={"boing", "whoosh", "plink"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affordances={"plink", "sizzle", "boing"}),
    "backyard": Setting(place="the backyard", indoor=False, affordances={"whoosh", "crash", "boing"}),
}

ACTS = {
    "boing": Act(
        id="boing",
        verb="bounce on the big cushion",
        gerund="bouncing on the big cushion",
        sound="boing",
        mess="wobble",
        twist="the cushion gives a silly squeak and tips sideways",
        keyword="boing",
        tags={"humorous", "sound", "twist"},
    ),
    "whoosh": Act(
        id="whoosh",
        verb="swoosh the paper fan",
        gerund="swooshing the paper fan",
        sound="whoosh",
        mess="flutter",
        twist="the fan slips and makes a tiny wind storm",
        keyword="whoosh",
        tags={"humorous", "sound"},
    ),
    "plink": Act(
        id="plink",
        verb="tap the cups in a rhythm",
        gerund="tapping the cups in a rhythm",
        sound="plink",
        mess="jingle",
        twist="one cup rolls away like it has very busy feet",
        keyword="plink",
        tags={"sound", "twist"},
    ),
}

PROPS = {
    "drum": Prop(
        id="drum",
        label="little drum",
        phrase="a bright little drum",
        fragile=False,
        fixed_by="tape",
        makes="boom",
        owner_role="child",
    ),
    "bell": Prop(
        id="bell",
        label="jingle bell",
        phrase="a shiny jingle bell",
        fragile=True,
        fixed_by="string",
        makes="ding",
        owner_role="child",
        plural=False,
    ),
    "cups": Prop(
        id="cups",
        label="cups",
        phrase="three plastic cups",
        fragile=False,
        fixed_by="tray",
        makes="plink",
        owner_role="child",
        plural=True,
    ),
}

HELPERS = {
    "sister": Helper(
        id="helper_sister",
        label="older sister",
        phrase="his older sister",
        offer="help hold the prop steady",
        tail="held the prop steady with a careful grin",
        makes="tada",
        type="girl",
    ),
    "mom": Helper(
        id="helper_mom",
        label="mom",
        phrase="his mom",
        offer="find the missing piece",
        tail="came back with the missing piece and a gentle smile",
        makes="pop",
        type="mother",
    ),
    "neighbor": Helper(
        id="helper_neighbor",
        label="neighbor",
        phrase="the kind neighbor",
        offer="lend a backup prop",
        tail="lent a backup prop and clapped along",
        makes="clang",
        type="adult",
    ),
}

BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Noah", "Finn", "Theo"]
GIRL_NAMES = ["Mia", "Ava", "Lily", "Zoe", "Nora", "Rose", "Maya", "Ella"]
TRAITS = ["curious", "cheerful", "silly", "gentle", "brave", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affordances:
            for prop_id, prop in PROPS.items():
                if act_id == "boing" and prop_id in {"drum", "cups"}:
                    out.append((place, act_id, prop_id))
                elif act_id == "whoosh" and prop_id in {"bell", "cups"}:
                    out.append((place, act_id, prop_id))
                elif act_id == "plink" and prop_id in {"cups", "bell"}:
                    out.append((place, act_id, prop_id))
    return out


def choose_helper(act: Act, prop: Prop) -> Optional[Helper]:
    if act.id == "boing":
        return HELPERS["sister"]
    if act.id == "whoosh":
        return HELPERS["mom"]
    if act.id == "plink":
        return HELPERS["neighbor"]
    return None


ASP_RULES = r"""
valid(Place, Act, Prop) :- afford(Place, Act), compatible(Act, Prop).
compatible(boing, drum).
compatible(boing, cups).
compatible(whoosh, bell).
compatible(whoosh, cups).
compatible(plink, cups).
compatible(plink, bell).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("afford", pid, a))
    for aid in ACTS:
        lines.append(asp.fact("act", aid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming humorous sound-effects twist story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.act is None or c[1] == args.act)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, act=act, prop=prop, name=name, gender=gender, helper=helper, trait=trait)


def _new_entity_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Helper]:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    helper_def = HELPERS[params.helper]
    helper = world.add(Entity(id=helper_def.id, kind="character", type=helper_def.type, label=helper_def.label))
    prop_def = PROPS[params.prop]
    prop = world.add(Entity(id=prop_def.id, type=prop_def.id, label=prop_def.label, phrase=prop_def.phrase))
    return world, child, helper, prop, helper_def


def predict_twist(world: World, act: Act, prop: Entity) -> dict:
    sim = world.copy()
    hero = next(e for e in sim.characters() if e.kind == "character")
    hero.meters[act.mess] = hero.meters.get(act.mess, 0) + 1
    prop.meters = copy.deepcopy(prop.meters)
    if act.id == "boing":
        prop.meters["wobble"] = prop.meters.get("wobble", 0) + 1
    elif act.id == "whoosh":
        prop.meters["flutter"] = prop.meters.get("flutter", 0) + 1
    else:
        prop.meters["jingle"] = prop.meters.get("jingle", 0) + 1
    return {"twisty": True, "messy": True}


def tell(params: StoryParams) -> World:
    world, child, helper, prop, helper_def = _new_entity_world(params)
    act = ACTS[params.act]

    child.memes["excitement"] = 1
    world.say(f"{child.id} was a {params.trait} little {params.gender} who loved sound effects.")
    world.say(f"{child.pronoun().capitalize()} wanted to {act.verb} because {act.sound} made everyone laugh.")
    world.say(f"{child.id} had {prop.phrase}, and {child.pronoun('possessive')} {helper.label_word} promised to help with the show.")

    world.para()
    child.memes["worry"] = 1
    world.say(f"At {world.setting.place}, {child.id} started {act.gerund}.")
    world.say(f"Then came the twist: {act.twist}.")
    if act.id == "boing":
        child.meters["wobble"] = 1
    elif act.id == "whoosh":
        child.meters["flutter"] = 1
    else:
        child.meters["jingle"] = 1

    world.say(f"{child.id} blinked, then let out a tiny laugh at the very silly mistake.")
    world.say(f"It was funny, but {child.pronoun('possessive')} cheeks felt a little hot.")

    world.para()
    child.memes["embarrassment"] = 1
    helper.memes["kindness"] = 1
    world.say(f"That was when {helper_def.phrase} came over and said, \"I can {helper_def.offer}.\"")
    world.say(f"{helper_def.tail}.")
    child.memes["kindness"] = 1
    child.memes["joy"] = 1
    child.memes["embarrassment"] = 0
    child.memes["worry"] = 0
    world.say(f"{child.id} took a breath, smiled, and said thank you.")
    world.say(f"Together they turned the big oops into a better show, and {act.sound} sounded even brighter than before.")

    world.facts.update(
        child=child,
        helper=helper,
        prop=prop,
        helper_def=helper_def,
        act=act,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, prop, act = f["child"], f["helper"], f["prop"], f["act"]
    return [
        f'Write a short heartwarming story for a young child about "{act.keyword}" sound effects and a funny twist.',
        f"Tell a gentle story where {child.id} wants to {act.verb}, but a silly twist happens and {helper.label_word} helps kindly.",
        f"Write a warm, funny story that ends with {child.id} and {helper.label_word} laughing after a sound-effects mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, prop, act = f["child"], f["helper"], f["prop"], f["act"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at {world.setting.place}?",
            answer=f"{child.id} wanted to {act.verb}. {child.pronoun().capitalize()} loved making {act.sound} sounds for the show.",
        ),
        QAItem(
            question=f"What funny twist happened while {child.id} was {act.gerund}?",
            answer=f"The twist was that {act.twist}. That made the moment silly instead of perfect.",
        ),
        QAItem(
            question=f"How did {helper.label_word} help when the twist made things tricky?",
            answer=f"{helper.label_word.capitalize()} answered kindly and helped by saying, \"I can {f['helper_def'].offer}.\" Then they worked together so the show could go on.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and relieved. {child.pronoun().capitalize()} said thank you, and the two of them finished the show together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = f["act"]
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound made on purpose to help tell a story, make a game funnier, or make a show feel lively.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle and helpful to someone else, especially when they feel upset or embarrassed.",
        ),
        QAItem(
            question="Why can a twist make a story more interesting?",
            answer="A twist is a surprising change. It can make a story more interesting because the characters have to think in a new way.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="living_room", act="boing", prop="drum", name="Milo", gender="boy", helper="sister", trait="silly"),
    StoryParams(place="kitchen", act="plink", prop="cups", name="Maya", gender="girl", helper="mom", trait="curious"),
    StoryParams(place="backyard", act="whoosh", prop="bell", name="Leo", gender="boy", helper="neighbor", trait="cheerful"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, act, prop) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.act} at {p.place} (prop: {p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
