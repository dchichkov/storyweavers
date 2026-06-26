#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/goo_television_clamber_tool_shed_dialogue_mystery.py
===============================================================================================================================

A small mystery storyworld set in a tool shed.

Premise seed:
- goo
- television
- clamber
- dialogue
- mystery
- tool shed

The story model centers on a child who climbs into a tool shed, finds a strange
goo-covered television, and solves a gentle mystery through clues and dialogue.
The physical state tracks where the goo is, who is dusty, and what gets cleaned.
The emotional state tracks curiosity, worry, relief, and trust.

The script supports:
- default generation
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the tool shed"


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    action: str
    strange: str
    outcome: str


@dataclass
class StoryParams:
    mystery: str
    name: str
    gender: str
    helper: str
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

    def copy(self) -> "World":
        import copy
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle mystery in a tool shed, with goo, a television, and dialogue."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["parent", "friend", "neighbor"])
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
    choices = list(MYSTERIES)
    mystery = args.mystery or rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["parent", "friend", "neighbor"])
    return StoryParams(mystery=mystery, name=name, gender=gender, helper=helper)


def _m(name: str, gender: str) -> str:
    return "she" if gender == "girl" else "he"


def _poss(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def _obj(gender: str) -> str:
    return "her" if gender == "girl" else "him"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    mystery = MYSTERIES[params.mystery]

    child = world.add(Entity(
        id=params.name, kind="character", type=params.gender, label=params.name,
        meters={"dust": 0.0, "goo": 0.0}, memes={"curiosity": 1.0, "worry": 0.0, "relief": 0.0}
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=params.helper, label=params.helper,
        meters={"dust": 0.0}, memes={"worry": 0.0, "calm": 1.0}
    ))
    tv = world.add(Entity(
        id="Television", type="television", label="television",
        phrase="an old television with a cracked screen", owner="Helper",
        meters={"goo": 0.0, "dust": 0.0}
    ))
    goo = world.add(Entity(
        id="Goo", type="goo", label="goo",
        phrase="a slick green goo", owner="Television",
        meters={"goo": 1.0}
    ))
    tool = world.add(Entity(
        id="ToolShed", type="place", label="tool shed",
        phrase="the little tool shed behind the house"
    ))

    world.say(f"{params.name} was a curious little {params.gender} who liked solving mysteries.")
    world.say(
        f"One day, {params.name} peeked into {world.setting.place} and saw {mystery.strange}."
    )
    world.say(
        f'"Why is there {mystery.strange} in here?" {params.name} asked. '
        f'"And why does the television look so odd?"'
    )
    child.memes["curiosity"] += 1

    world.para()
    world.say(
        f"{params.name} had to clamber over a low stack of boxes to get closer."
    )
    child.meters["dust"] += 1
    child.memes["worry"] += 1
    tv.meters["dust"] += 1
    world.say(
        f'"Careful," said the {params.helper}. "That old television was here before the rain started."'
    )
    world.say(
        f'"Did it break?" {params.name} asked, brushing dust from {child.pronoun("possessive")} knees.'
    )

    world.para()
    world.say(
        f'{params.helper.capitalize()} pointed to the goo on the screen. '
        f'"Look at the edges. The goo dripped from the shelf above, not from the television itself."'
    )
    world.say(
        f'"So the television is not the culprit?" {params.name} said.'
    )
    world.say(
        f'"No," said the {params.helper}. "The mystery is what the goo was doing here."'
    )

    world.para()
    child.meters["goo"] += 1
    tv.meters["goo"] += 1
    world.say(
        f"{params.name} leaned in and found a little note stuck under the set."
    )
    world.say(
        f'The note said, "{mystery.clue}"'
    )
    world.say(
        f'"That sounds like {mystery.cause}," {params.name} said. "Someone must have left it for repairs."'
    )
    helper.memes["worry"] += 1
    helper.memes["calm"] += 1

    world.para()
    world.say(
        f'The {params.helper} smiled. "{mystery.reveal}"'
    )
    world.say(
        f'"Then the goo is just a mess, not a clue," {params.name} said.'
    )
    world.say(
        f'"Exactly," said the {params.helper}. "You solved it."'
    )
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0

    world.para()
    tv.meters["goo"] = 0.0
    child.meters["goo"] = 0.0
    child.meters["dust"] = 0.0
    world.say(
        f"Together they wiped the television clean and carried the goo jar back to the shelf."
    )
    world.say(
        f'At the end, {params.name} left the tool shed with a clean shirt, a clear answer, and a happy smile.'
    )

    world.facts.update(
        child=child,
        helper=helper,
        tv=tv,
        goo=goo,
        tool=tool,
        mystery=mystery,
        params=params,
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    m = f["mystery"]
    return [
        f'Write a gentle mystery story set in a tool shed that includes the words "goo", "television", and "clamber".',
        f"Tell a dialogue-heavy story about {p.name} finding out why there is goo on an old television in the tool shed.",
        f"Write a child-friendly mystery where someone has to clamber over boxes, ask questions, and solve a small shed puzzle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    m = f["mystery"]
    child = f["child"]
    helper = f["helper"]
    tv = f["tv"]
    return [
        QAItem(
            question=f"Where does {p.name} find the strange goo and the old television?",
            answer=f"{p.name} finds them in the tool shed behind the house.",
        ),
        QAItem(
            question=f"What does {p.name} have to do to get closer to the television?",
            answer=f"{p.name} has to clamber over a low stack of boxes to reach it.",
        ),
        QAItem(
            question=f"Why does the television turn out not to be the culprit?",
            answer=f"It is not the culprit because the goo dripped from a shelf above, so the television was only messy, not the cause.",
        ),
        QAItem(
            question=f"How does {p.name} feel after solving the mystery?",
            answer=f"{p.name} feels relieved and proud after solving the mystery with {helper.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is goo like?",
            answer="Goo is sticky and slippery, so it can make things feel messy.",
        ),
        QAItem(
            question="What is a television for?",
            answer="A television is a machine that shows pictures and stories on a screen.",
        ),
        QAItem(
            question="What does clamber mean?",
            answer="To clamber means to climb awkwardly over or onto something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Finn", "Leo", "Max"]

MYSTERIES = {
    "goo-on-tv": Mystery(
        id="goo-on-tv",
        clue="I put the goo jar here so I could fix the sticky hinge later.",
        cause="someone set down a repair jar on the shelf",
        reveal="I was fixing the shed hinge and left the goo jar near the television by mistake.",
        action="clean up the mess",
        strange="a television with goo on its screen",
        outcome="the television was safe and the mystery was solved",
    ),
    "late-night-static": Mystery(
        id="late-night-static",
        clue="The television is only old; the buzzing comes from the loose wire behind it.",
        cause="a loose wire behind the set",
        reveal="The buzzing was from a loose wire, and the goo came from a leaky glue pot on the shelf.",
        action="listen carefully",
        strange="a humming television and a drop of goo",
        outcome="the noise had a simple answer",
    ),
    "missing-battery": Mystery(
        id="missing-battery",
        clue="Check the red box before you blame the television.",
        cause="a battery box tucked behind tools",
        reveal="The missing battery was in the red box, and the goo was just spilled craft paste.",
        action="search the shelves",
        strange="a television, some goo, and a missing battery",
        outcome="the clues fit together at last",
    ),
}


SETTING = Setting(place="the tool shed")


ASP_RULES = r"""
mystery_scene(tool_shed).
has_goo(tv).
requires_clamber(child) :- stacked_boxes.
mystery(C) :- child(C), has_goo(tv), requires_clamber(C).
solved(C) :- mystery(C), clue_found(C), cause_known(C).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "tool_shed"),
        asp.fact("place", "tool_shed"),
    ]
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_id", mid))
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("has_goo", "tv"))
    lines.append(asp.fact("stacked_boxes"))
    lines.append(asp.fact("clue_found", "hero"))
    lines.append(asp.fact("cause_known", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1.\n#show mystery/1."))
    return sorted(set(asp.atoms(model, "solved"))), sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    solved, mystery = asp_valid()
    if solved and mystery:
        print("OK: ASP twin produces a solved mystery story shape.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story predicates.")
    return 1


def resolve_story_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show mystery/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        solved, mystery = asp_valid()
        print("ASP mystery predicates:")
        print("solved:", solved)
        print("mystery:", mystery)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for i, key in enumerate(sorted(MYSTERIES)):
            params = StoryParams(
                mystery=key,
                name=(GIRL_NAMES + BOY_NAMES)[i % (len(GIRL_NAMES) + len(BOY_NAMES))],
                gender="girl" if i % 2 == 0 else "boy",
                helper=["parent", "friend", "neighbor"][i % 3],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_story_choice(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
