#!/usr/bin/env python3
"""
A small storyworld in the style of a gentle ghost story.

Premise:
A young gymnast practices in an old gym at night. A shy ghost appears during a
flashback to a past mistake, and the coach helps the child clarify what really
happened so fear can turn into confidence.

The story is intentionally compact: one setting, one activity, one haunting
memory, one friendly turn, one resolution.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old gym"
    detail: str = "The old gym smelled like chalk and rain."
    nighttime: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


ACTIVITIES = {
    "beam": Activity(
        id="beam",
        verb="walk the balance beam",
        gerund="walking the balance beam",
        rush="hurry across the beam",
        risk="slipping",
        keyword="balance",
        tags={"gymnast", "beam", "ghost", "flashback", "clarify"},
    ),
    "vault": Activity(
        id="vault",
        verb="try the vault",
        gerund="trying the vault",
        rush="run toward the vault",
        risk="landing crooked",
        keyword="vault",
        tags={"gymnast", "ghost", "flashback", "clarify"},
    ),
    "bars": Activity(
        id="bars",
        verb="swing on the bars",
        gerund="swinging on the bars",
        rush="grab the bars quickly",
        risk="slipping",
        keyword="swing",
        tags={"gymnast", "ghost", "flashback", "clarify"},
    ),
}

OBJECTS = {
    "chalk": ObjectItem(
        id="chalk",
        label="chalky grips",
        phrase="soft chalky grips",
        type="grips",
        region="hands",
        plural=True,
    ),
    "ribbon": ObjectItem(
        id="ribbon",
        label="a blue ribbon",
        phrase="a blue ribbon from the last meet",
        type="ribbon",
        region="chest",
    ),
    "shoes": ObjectItem(
        id="shoes",
        label="gym shoes",
        phrase="a pair of gym shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
}

SETTINGS = {
    "gym": Setting(),
}

GIRL_NAMES = ["Maya", "Lena", "Ivy", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Theo", "Max", "Eli"]
TRAITS = ["careful", "brave", "nervous", "determined", "gentle", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, act_id, obj_id) for place in SETTINGS for act_id in ACTIVITIES for obj_id in OBJECTS]


def prize_at_risk(activity: Activity, obj: ObjectItem) -> bool:
    return True


def select_gear(activity: Activity, obj: ObjectItem):
    return "clarification"


def explain_rejection(activity: Activity, obj: ObjectItem) -> str:
    return f"(No story: {obj.label} does not fit this quiet gym flashback.)"


def explain_gender(obj_id: str, gender: str) -> str:
    return f"(No story: try a different name for the {gender} gymnast.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story gym world with flashback and clarification."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.gender and args.name is None:
        pass
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, obj_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    if gender == "girl" and name in BOY_NAMES:
        raise StoryError(explain_gender(obj_id, gender))
    if gender == "boy" and name in GIRL_NAMES:
        raise StoryError(explain_gender(obj_id, gender))
    return StoryParams(place=place, activity=activity, object=obj_id, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters[activity.id] = actor.meters.get(activity.id, 0.0) + 1.0
    actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1.0


def tell(setting: Setting, activity: Activity, obj_cfg: ObjectItem,
         hero_name: str, hero_type: str, parent_type: str, hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    obj = world.add(Entity(id="object", type=obj_cfg.type, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id, caretaker=parent.id, plural=obj_cfg.plural))

    hero.memes["nervous"] = 1.0
    world.say(f"{hero.id} was a {hero_trait} young {hero.type} who loved {activity.gerund} in {setting.place}.")
    world.say(setting.detail)
    world.say(f"{hero.id} treasured {obj.phrase}, because it made {hero.pronoun('possessive')} practice feel bright.")

    world.para()
    world.say(f"That night, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place} after the lights had gone soft.")
    world.say(f"{hero.id} wanted to {activity.verb}, but something in the room made {hero.pronoun('object')} slow down.")
    world.say(f"A cold draft slid under the door, and a pale shadow drifted past the chalk line like an old memory.")

    world.para()
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(f"Then came a flashback: last time, {hero.id} had tried to {activity.verb} and almost {activity.risk}.")
    world.say(f"{hero.id} gasped, because the memory felt like a ghost standing right beside {hero.pronoun('object')}.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, but {hero.pronoun('possessive')} knees felt wobbly.")

    world.para()
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} did not laugh.")
    world.say(f'"Let me clarify," {parent.pronoun().capitalize()} said softly. "The old slip was only one moment. It does not mean you cannot try again."')
    world.say(f"The ghost in the corner looked less scary after that, like a thin curtain instead of a monster.")
    world.say(f"{hero.id} breathed slowly, nodded, and stepped back into the bright square of the mat.")

    world.para()
    _do_activity(world, hero, activity)
    hero.memes["fear"] = 0.0
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    world.say(f"This time, {hero.id} moved carefully, with {hero.pronoun('possessive')} eyes clear and {hero.pronoun('possessive')} hands steady.")
    world.say(f"{hero.pronoun().capitalize()} {activity.gerund} all the way through, and the room felt warm instead of haunted.")
    world.say(f"When {hero.id} landed safely, even the ghost seemed to fade into a gentle little hush.")
    world.say(f"{obj.phrase.capitalize()} stayed with {hero.id}, and the old gym held only quiet pride and chalk dust.")

    world.facts.update(hero=hero, parent=parent, obj=obj, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    obj = f["obj"]
    return [
        f'Write a short ghost story for a child about a gymnast named {hero.id} who wants to {act.verb} and needs to clarify a scary flashback.',
        f'Tell a gentle nighttime story in an old gym where {hero.id} learns that a flashback is only a memory, not a ghost.',
        f'Write a small story using the word "clarify" where a gymnast keeps practicing after a spooky moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    obj = f["obj"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a young {hero.type} gymnast, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What scared {hero.id} in the old gym?",
            answer=f"A flashback of a past mistake scared {hero.id}, and it felt like a ghost was standing nearby.",
        ),
        QAItem(
            question=f"What did {hero.pronoun('possessive')} {parent.label} do to help?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label} helped by clarifying that the old slip was only one moment, not a sign that {hero.id} would fail again.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} finished {act.gerund} safely, and {obj.phrase} stayed with {hero.pronoun('object')} while the gym grew quiet and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory that a person feels very strongly again, as if it is happening in the present.",
        ),
        QAItem(
            question="What does it mean to clarify something?",
            answer="To clarify means to explain something clearly so it is easier to understand.",
        ),
        QAItem(
            question="What is a gymnast?",
            answer="A gymnast is a person who practices exercises, jumps, and balance moves on gym equipment or mats.",
        ),
        QAItem(
            question="Why can an old gym feel spooky at night?",
            answer="An old gym can feel spooky at night because it is quiet, dim, and full of shadows that make small sounds seem bigger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="gym", activity="beam", object="ribbon", name="Maya", gender="girl", parent="mother", trait="nervous"),
    StoryParams(place="gym", activity="vault", object="shoes", name="Leo", gender="boy", parent="father", trait="determined"),
    StoryParams(place="gym", activity="bars", object="chalk", name="Ivy", gender="girl", parent="mother", trait="careful"),
]


ASP_RULES = r"""
% A story is valid when the gymnast, the activity, and the object all belong
% to the same small world, and the story always includes a clarifying turn.
valid_story(Place, Activity, Object) :- place(Place), activity(Activity), object(Object).
valid_story(Place, Activity, Object) :- place(Place), activity(Activity), object(Object), clarify_turn.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    lines.append(asp.fact("clarify_turn"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_asp_combos() -> list[tuple]:
    return valid_combos()


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_asp_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        OBJECTS[params.object],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
