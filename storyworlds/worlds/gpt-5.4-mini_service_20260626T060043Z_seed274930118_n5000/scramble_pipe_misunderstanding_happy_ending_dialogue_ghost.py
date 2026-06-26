#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-shaped misunderstanding about a pipe.

Seed premise:
A child hears strange scraping in an old house and thinks it is a ghost.
The sound comes from a loose pipe, and everyone scrambles to fix it.
The child and a helper talk it through, discover the misunderstanding,
and end with a happy, cozy feeling.

The world is built around:
- a spooky setting
- a noisy pipe
- misunderstanding
- scrambling to solve the problem
- dialogue
- a happy ending
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    eerie: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    cause: str
    fix: str
    keyword: str


@dataclass
class StoryParams:
    place: str
    activity: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "old house": Setting(place="the old house", eerie=True, affords={"scramble"}),
    "attic": Setting(place="the attic", eerie=True, affords={"scramble"}),
    "cellar": Setting(place="the cellar", eerie=True, affords={"scramble"}),
}

ACTIVITIES = {
    "scramble": Activity(
        id="scramble",
        verb="scramble toward the pipe",
        gerund="scrambling around the pipe",
        rush="scramble toward the wall",
        sound="scritch-scritch",
        cause="a loose pipe making a strange sound",
        fix="tighten the pipe",
        keyword="pipe",
    ),
}

TRAITS = ["curious", "brave", "quiet", "thoughtful", "tiny", "gentle"]
CHILD_NAMES = ["Mia", "Noah", "Lena", "Owen", "Ruby", "Theo"]
HELPER_NAMES = ["Aunt June", "Grandpa", "Nora", "Uncle Ben", "Mom", "Dad"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a pipe misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "scramble"
    if activity not in SETTINGS[place].affords:
        raise StoryError("This setting cannot support that story.")
    child_name = rng.choice(CHILD_NAMES) if not hasattr(args, "name") or not getattr(args, "name", None) else args.name
    helper_name = rng.choice(HELPER_NAMES)
    child_type = rng.choice(["girl", "boy"])
    helper_type = "woman" if "Mom" in helper_name or "Aunt" in helper_name or helper_name == "Nora" else "man"
    return StoryParams(place=place, activity=activity, child_name=child_name, child_type=child_type,
                       helper_name=helper_name, helper_type=helper_type)


def _pronoun_for_type(type_name: str, case: str = "subject") -> str:
    if type_name in {"girl", "mother", "mom", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if type_name in {"boy", "father", "dad", "man"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(setting: Setting, activity: Activity, child_name: str, child_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    pipe = world.add(Entity(id="pipe", type="pipe", label="pipe", phrase="an old pipe in the wall"))
    leak = world.add(Entity(id="leak", type="thing", label="drip", phrase="a tiny drip of water", caretaker=helper.id))

    child.memes["uneasy"] = 1
    child.memes["curious"] = 1
    pipe.meters["noise"] = 1
    leak.meters["drip"] = 1

    world.say(
        f"{child.id} lived in {setting.place}, where the halls could feel dark at night."
    )
    world.say(
        f"One evening, {child.id} heard {activity.sound} from the wall and looked up fast."
    )
    world.say(
        f"{child.id} thought it might be a ghost hiding near the {activity.keyword}."
    )
    world.para()
    world.say(
        f"{child.id} {activity.rush}, and {child.pronoun().capitalize()} called for {helper.id}."
    )
    world.say(
        f'"Did you hear that?" {child.id} asked. "{activity.sound}!"'
    )
    world.say(
        f"{helper.id} listened, then smiled. \"That is not a ghost,\" {helper.pronoun()} said."
    )
    world.say(
        f"\"It sounds like {activity.cause}.\""
    )
    world.para()
    world.say(
        f"{child.id} and {helper.id} scrambled together to find the noise."
    )
    world.say(
        f"They followed the soft drip and the tap-tap sound until they found the loose pipe."
    )
    world.say(
        f"\"Oh!\" {child.id} said. \"The house was just making a funny sound.\""
    )
    world.say(
        f"{helper.id} nodded. \"Let's {activity.fix} and make it quiet again.\""
    )
    pipe.meters["fixed"] = 1
    child.memes["fear"] = 0
    child.memes["joy"] = 1
    child.memes["relief"] = 1
    helper.memes["joy"] = 1
    helper.memes["care"] = 1

    world.para()
    world.say(
        f"They tightened the pipe, and the scritch-scritch stopped."
    )
    world.say(
        f"{child.id} laughed, because the spooky thing had been only a misunderstanding."
    )
    world.say(
        f"After that, the old house felt cozy instead of scary."
    )
    world.say(
        f"{child.id} and {helper.id} went to bed smiling, with the wall quiet and still."
    )

    world.facts.update(
        child=child,
        helper=helper,
        pipe=pipe,
        leak=leak,
        activity=activity,
        setting=setting,
        misunderstanding=True,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    activity = f["activity"]
    return [
        f'Write a short ghost story for a child that includes the word "{activity.keyword}".',
        f"Tell a story where {child.id} hears a spooky sound, thinks it is a ghost, and talks it through with {helper.id}.",
        f"Write a gentle mystery with dialogue, a misunderstanding, and a happy ending in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"Why did {child.id} think there was a ghost?",
            answer=f"{child.id} heard {activity.sound} from the wall and did not know it was only the pipe making noise.",
        ),
        QAItem(
            question=f"What did {helper.id} say the sound really was?",
            answer=f"{helper.id} said it sounded like {activity.cause}.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} solve the problem?",
            answer=f"They scrambled together, found the loose pipe, and used a simple fix to tighten it so the noise stopped.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended happily, with {child.id} feeling relieved and the old house quiet and cozy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pipe?",
            answer="A pipe is a long tube that can carry water or air through a building.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but it turns out to be wrong.",
        ),
        QAItem(
            question="What does it mean to scramble?",
            answer="To scramble means to move quickly and a little messily because something needs attention right away.",
        ),
        QAItem(
            question="Why do people feel better after a problem is solved?",
            answer="People often feel better after a problem is solved because the worry goes away and things become safe or calm again.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old house", activity="scramble", child_name="Mia", child_type="girl", helper_name="Mom", helper_type="woman"),
    StoryParams(place="attic", activity="scramble", child_name="Noah", child_type="boy", helper_name="Dad", helper_type="man"),
    StoryParams(place="cellar", activity="scramble", child_name="Lena", child_type="girl", helper_name="Grandpa", helper_type="man"),
]


ASP_RULES = r"""
% A story is valid when the child hears a spooky sound from the pipe, thinks it
% might be a ghost, and there is a clear fix that resolves the problem.
spooky_place(P) :- place(P).
pipe_story(P) :- spooky_place(P), hears_pipe(P), misunderstanding(P), happy_ending(P).

valid_story(P, A) :- place(P), activity(A), possible(P, A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.eerie:
            lines.append(asp.fact("spooky_place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lightweight parity gate: compare a small declarative validity predicate
    # with Python's curated valid stories.
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p.place, p.activity) for p in CURATED}
    if asp_set == py_set:
        print(f"OK: clingo gate matches curated stories ({len(py_set)}).")
        return 0
    print("MISMATCH between clingo and curated stories:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 params.child_name, params.child_type,
                 params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "scramble"
    if activity not in SETTINGS[place].affords:
        raise StoryError("That story cannot happen in this setting.")
    child_name = rng.choice(CHILD_NAMES)
    child_type = rng.choice(["girl", "boy"])
    helper_name = rng.choice(HELPER_NAMES)
    helper_type = "woman" if helper_name in {"Mom", "Aunt June", "Nora"} else "man"
    return StoryParams(
        place=place,
        activity=activity,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
                params = resolve_story_params(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
