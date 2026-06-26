#!/usr/bin/env python3
"""
storyworlds/worlds/artistic_gymnasium_bogey_transformation_heartwarming.py
===========================================================================

A heartwarming storyworld about an artistic gymnasium class where a small
messy bogey-shaped mistake can be transformed into something lovely.

Source-tale inspiration:
---
A child comes to an art gymnasium feeling shy because they made a lopsided,
bogey-looking clay lump. A kind teacher helps them add color, texture, and
funny eyes so the lump becomes a cheerful little sculpture. The child learns
that mistakes can change into art, and the whole room feels warmer because of
it.
---

World model:
- A child, a teacher, a studio-like gymnasium setting, and a clay/art project.
- The child's embarrassment rises when the bogey-like shape looks "wrong".
- A supportive helper suggests a simple transformation: add details, rename it,
  and give it a place of honor.
- The emotional turn is that the child stops feeling ashamed and starts feeling
  proud, and the physical turn is that the messy shape becomes a finished piece.

The prose is driven by simulated state: blush, mess, cleanup, transformed object,
and the resulting pride all matter to the ending.
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
    transformed_from: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
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
    place: str = "the gymnasium art room"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    gendered_use: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    finish: str
    transforms_into: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "gymnasium": Setting(place="the gymnasium art room", indoor=True, affords={"clay", "paint", "collage"}),
}

ACTIVITIES = {
    "clay": Activity(
        id="clay",
        verb="shape a clay creature",
        gerund="shaping clay creatures",
        mess="clay-smeared",
        turn="turn the lopsided lump into something charming",
        keyword="bogey",
        tags={"artistic", "bogey", "transformation"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting bright pictures",
        mess="paint-speckled",
        turn="turn a smudge into a smiling face",
        keyword="artistic",
        tags={"artistic", "transformation"},
    ),
    "collage": Activity(
        id="collage",
        verb="build a collage",
        gerund="cutting and gluing shapes",
        mess="paper-flecked",
        turn="turn scraps into a lovely scene",
        keyword="artistic",
        tags={"artistic", "transformation"},
    ),
}

PRIZES = {
    "apron": Prize(label="apron", phrase="a soft art apron", type="apron"),
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt"),
    "sketchbook": Prize(label="sketchbook", phrase="a new sketchbook with thick pages", type="sketchbook"),
}

TOOLS = [
    Tool(
        id="googly_eyes",
        label="googly eyes",
        prep="add a pair of googly eyes",
        finish="glued on two tiny eyes",
        transforms_into="a cheerful little face",
        tags={"transformation", "bogey"},
    ),
    Tool(
        id="sprinkles",
        label="bright sprinkles of paint",
        prep="brush on bright sprinkles of paint",
        finish="covered the lump in happy colors",
        transforms_into="a bright, smiling sculpture",
        tags={"artistic", "transformation"},
    ),
    Tool(
        id="ribbon",
        label="a curly ribbon",
        prep="tie on a curly ribbon",
        finish="gave the piece a proud little flourish",
        transforms_into="something that looked ready for a shelf",
        tags={"artistic", "transformation"},
    ),
]

NAMES = {
    "girl": ["Mia", "Lila", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Milo", "Eli", "Theo"],
}

TRAITS = ["gentle", "curious", "shy", "cheerful", "brave"]


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _tool_for(activity: Activity) -> Tool:
    if activity.id == "clay":
        return TOOLS[0]
    if activity.id == "paint":
        return TOOLS[1]
    return TOOLS[2]


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return activity.id in {"clay", "paint", "collage"} and prize.label in {"apron", "shirt", "sketchbook"}


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not give a believable heartwarming "
        f"turn with {prize.phrase}. Try a more art-friendly prize.)"
    )


def introduce(world: StoryWorld, child: Entity, helper: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.memes.get('trait', 'sweet')} {child.type} who loved making art in "
        f"{world.setting.place}."
    )
    world.say(
        f"{helper.pronoun().capitalize()} was the kind of helper who noticed a quiet face and made it feel safe."
    )


def setup(world: StoryWorld, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    child.memes["love_art"] = child.memes.get("love_art", 0) + 1
    prize.owner = child.id
    prize.caretaker = helper.id
    world.say(
        f"{child.id} wore {child.pronoun('possessive')} {prize.label} and wanted to {activity.verb} right away."
    )


def make_mess(world: StoryWorld, child: Entity, activity: Activity, prize: Entity) -> None:
    child.meters[activity.mess] = child.meters.get(activity.mess, 0) + 1
    child.memes["confidence"] = child.memes.get("confidence", 0) - 0.5
    world.say(
        f"But the first shape came out a little crooked, like a tiny bogey that had rolled out of a dream."
    )
    if prize.label == "shirt":
        prize.meters["messy"] = prize.meters.get("messy", 0) + 1
        world.say(f"{child.pronoun('possessive').capitalize()} {prize.label} caught a few specks, and {child.id} frowned.")
    else:
        world.say(f"{child.id} stared at the lumpy art and worried it looked wrong.")


def worry(world: StoryWorld, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    child.memes["sad"] = child.memes.get("sad", 0) + 1
    world.say(
        f"{helper.pronoun().capitalize()} knelt beside {child.id} and said, \"We do not throw away good try. "
        f"We change it.\""
    )
    world.say(
        f"{child.id} sniffled, because the bogey-shaped lump felt embarrassing."
    )


def transform(world: StoryWorld, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    tool = _tool_for(activity)
    world.say(
        f"Then {helper.pronoun('subject')} helped {child.id} {tool.prep}."
    )
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    child.memes["confidence"] = max(child.memes.get("confidence", 0), 0) + 1
    world.say(
        f"With each careful touch, the crooked lump started to become {tool.transforms_into}."
    )
    world.say(
        f"At last, {helper.pronoun('subject')} {tool.finish}, and {child.id} could see a sweet new face inside the mess."
    )
    child.memes["proud"] = child.memes.get("proud", 0) + 1
    prize.meters["clean"] = max(prize.meters.get("clean", 0), 1)
    world.facts["tool"] = tool
    world.facts["transformed"] = True
    world.facts["tool_label"] = tool.label
    world.facts["tool_id"] = tool.id


def ending(world: StoryWorld, child: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{child.id} smiled so wide that the room seemed warmer."
    )
    world.say(
        f"{child.id} gave the finished piece a place of honor beside {child.pronoun('possessive')} {prize.label}, "
        f"and {helper.id} smiled back like the whole room had grown kinder."
    )
    world.say(
        f"Now the bogey was not a mistake anymore. It was {world.facts['tool'].transforms_into}, made by loving hands."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str, trait: str) -> StoryWorld:
    world = StoryWorld(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id))

    introduce(world, child, helper)
    world.para()
    setup(world, child, helper, prize, activity)
    make_mess(world, child, activity, prize)
    worry(world, child, helper, prize, activity)
    world.para()
    transform(world, child, helper, prize, activity)
    ending(world, child, helper, prize, activity)

    world.facts.update(child=child, helper=helper, prize=prize, activity=activity, setting=setting)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a heartwarming story for a young child about {child.id} in {f["setting"].place} and the word "{activity.keyword}".',
        f"Tell a gentle tale where a {child.type} makes a {activity.gerund} mistake and then transforms it into something lovely.",
        f"Write a short story about art, a bogey-shaped mix-up, and a happy transformation at {f['setting'].place}.",
        f"Make a warm story in which a {child.id} and a helper protect {prize.phrase} while making art.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    prize = f["prize"]
    activity = f["activity"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Where did {child.id} make the art?",
            answer=f"{child.id} made the art in {f['setting'].place}, a cozy place for creative work.",
        ),
        QAItem(
            question=f"What did {child.id} first make that felt embarrassing?",
            answer=f"{child.id} first made a lumpy clay piece that looked like a bogey-shaped mistake.",
        ),
        QAItem(
            question=f"How did {helper.id} help {child.id} feel better?",
            answer=f"{helper.id} encouraged {child.id} to keep going and helped turn the mess into {tool.transforms_into}.",
        ),
        QAItem(
            question=f"What happened to {child.id}'s {prize.label} by the end?",
            answer=f"{child.id}'s {prize.label} stayed part of the art time, and the finished piece became the star of the room.",
        ),
        QAItem(
            question=f"What change shows the story's transformation?",
            answer=f"The story changes from a crooked bogey-like lump into a cheerful finished artwork that {child.id} feels proud of.",
        ),
        QAItem(
            question=f"Why is this a heartwarming story?",
            answer=f"It is heartwarming because kindness helps {child.id} turn an awkward mistake into something beautiful and feel proud instead of ashamed.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gymnasium?",
            answer="A gymnasium is a large room or building for exercise, games, or activities, and in this story it is also used for making art.",
        ),
        QAItem(
            question="What does artistic mean?",
            answer="Artistic means making or enjoying art, like drawing, painting, or building a creative project.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing from one form or feeling into another, like a messy lump becoming a lovely sculpture.",
        ),
        QAItem(
            question="What is a bogey?",
            answer="A bogey is a small messy blob in this storyworld, and the word is used for the awkward little shape before it becomes art.",
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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for t in sorted(act.tags):
            lines.append(asp.fact("tagged", aid, t))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if prize.label in {"apron", "shirt", "sketchbook"}:
            lines.append(asp.fact("reasonable_prize", pid))
    for tid, tool in [(t.id, t) for t in TOOLS]:
        lines.append(asp.fact("tool", tid))
        for tag in sorted(tool.tags):
            lines.append(asp.fact("tagged_tool", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Act, Prize) :- setting(Place), affords(Place, Act), activity(Act), prize(Prize), reasonable_prize(Prize).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(ACTIVITIES[act], prize):
                    out.append((place, act, prize_id))
    return sorted(out)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming artistic gymnasium storyworld with a bogey-shaped transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["teacher", "mother", "father"])
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
    if args.activity and args.prize:
        if not reasonableness_gate(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(["teacher", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.helper,
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
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible combos:")
        for place, act, prize in vals:
            print(f"  {place:10} {act:10} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="gymnasium", activity="clay", prize="apron", name="Mia", gender="girl", helper="teacher", trait="shy"),
            StoryParams(place="gymnasium", activity="paint", prize="shirt", name="Leo", gender="boy", helper="mother", trait="curious"),
            StoryParams(place="gymnasium", activity="collage", prize="sketchbook", name="Nora", gender="girl", helper="father", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.activity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
