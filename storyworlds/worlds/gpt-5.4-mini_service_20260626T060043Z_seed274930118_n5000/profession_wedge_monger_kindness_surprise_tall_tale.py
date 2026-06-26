#!/usr/bin/env python3
"""
storyworlds/worlds/profession_wedge_monger_kindness_surprise_tall_tale.py
===========================================================================

A small standalone story world in the tall-tale style: a profession, a wedge,
a monger, and a kindness-driven surprise.

Premise:
- A traveling wedge-monger is a worker who sells and fits wooden wedges.
- A wedge can steady a wobbling thing: a gate, cart wheel, chair leg, or barn door.
- Kindness is the emotional force that changes the day.
- Surprise is the emotional turn: the crowd does not expect the wedge-monger's
  odd little job to save the day, and they are delighted when it does.

The world model tracks:
- physical meters: wobble, steadiness, load, travel, shine
- emotional memes: pride, worry, kindness, surprise, gratitude

The story is told as a tall tale with a beginning, a trouble, a surprising
kindness-based fix, and an ending image that proves what changed.
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str
    crowd: str


@dataclass
class Problem:
    id: str
    thing: str
    wobble: str
    fixed_by: str
    surprise_image: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    fits: str
    helps: str
    verb: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "riverbank": Setting(place="the riverbank", afford="cart", crowd="town folk"),
    "crossroads": Setting(place="the crossroads", afford="gate", crowd="travelers"),
    "barnyard": Setting(place="the barnyard", afford="barn door", crowd="neighbors"),
}

PROBLEMS = {
    "cart": Problem(
        id="cart",
        thing="a big wagon wheel",
        wobble="wobbling worse than a spoon in a storm",
        fixed_by="wheel wedge",
        surprise_image="the wagon stood steady as a church bell",
        keyword="wedge",
    ),
    "gate": Problem(
        id="gate",
        thing="a crooked gate",
        wobble="swinging loose like a latch with hiccups",
        fixed_by="gate wedge",
        surprise_image="the gate stayed shut and proud",
        keyword="monger",
    ),
    "barn door": Problem(
        id="barn door",
        thing="a heavy barn door",
        wobble="shuddering on its hinges like a giant trying not to sneeze",
        fixed_by="door wedge",
        surprise_image="the barn door held firm against the wind",
        keyword="profession",
    ),
}

TOOLS = {
    "wheel wedge": Tool(
        id="wheel wedge",
        label="a smooth wooden wheel wedge",
        fits="under the wheel",
        helps="steady the wagon",
        verb="slip a wedge under the wheel",
        tail="then gave the wheel a final snug tap",
    ),
    "gate wedge": Tool(
        id="gate wedge",
        label="a pointed gate wedge",
        fits="under the gate post",
        helps="hold the gate true",
        verb="set a wedge under the gate post",
        tail="then gave the wedge a kind little pat",
    ),
    "door wedge": Tool(
        id="door wedge",
        label="a stout door wedge",
        fits="under the barn door",
        helps="keep the door from drifting",
        verb="slide a wedge beneath the barn door",
        tail="then nodded as if it had always belonged there",
    ),
}

NAMES = ["Mabel", "Hank", "Rosie", "Jeb", "Lula", "Clem", "Ivy", "Bo", "June", "Otis"]
TRAITS = ["kindly", "breezy", "lively", "patient", "bright-eyed", "dusty-booted"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        lines.append(asp.fact("crowd", sid, s.crowd))
        lines.append(asp.fact("afford", sid, s.afford))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("thing", pid, p.thing))
        lines.append(asp.fact("keyword", pid, p.keyword))
        lines.append(asp.fact("fixed_by", pid, p.fixed_by))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("fits", tid, t.fits))
        lines.append(asp.fact("helps", tid, t.helps))
    return "\n".join(lines)


ASP_RULES = r"""
match(S,P,T) :- afford(S,P), fixed_by(P,T), tool(T).
shown(S,P,T) :- match(S,P,T).
#show shown/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_candidates() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown/3."))
    return sorted(set(asp.atoms(model, "shown")))


def asp_verify() -> int:
    python_set = {(sid, pid, tid) for sid in SETTINGS for pid, p in PROBLEMS.items() for tid, t in TOOLS.items()
                  if SETTINGS[sid].afford == pid and p.fixed_by == tid}
    clingo_set = set(asp_candidates())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a wedge-monger and a kindness surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or SETTINGS[setting].afford
    if problem != SETTINGS[setting].afford:
        raise StoryError("That setting and problem do not fit this tale.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, problem=problem, name=name, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[problem.fixed_by]
    world = World(setting)

    monger = world.add(Entity(id=params.name, kind="character", type="monger", label="the wedge-monger"))
    crowd = world.add(Entity(id="crowd", kind="character", type="folk", label=setting.crowd))

    wobble = world.add(Entity(id="wobble", type="thing", label=problem.thing, owner=monger.id))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, owner=monger.id, plural=False))

    monger.memes["kindness"] = 1.0
    crowd.memes["worry"] = 1.0
    wobble.meters["wobble"] = 2.0

    world.say(
        f"On a windy morning at {setting.place}, there lived a {params.trait} wedge-monger named {params.name}, "
        f"the sort of person who could hear a loose thing before it ever started to complain."
    )
    world.say(
        f"{params.name} carried {tool.label} in a little cart and sold wedges by the smile, by the tap, and by the old-tale mile."
    )

    world.say(
        f"That day, the {problem.thing} at {setting.place} was {problem.wobble}, and the {setting.crowd} gathered round with worried faces."
    )
    world.say(
        f"Nobody expected much from a wedge, but {params.name} tipped the hat, looked kind as moonlight, and said, "
        f'“A small wedge can do a giant job.”'
    )

    crowd.memes["surprise"] = 1.0
    crowd.memes["hope"] = 1.0
    world.say(
        f"So the wedge-monger did {tool.verb}, and the whole thing sat still at once."
    )
    wobble.meters["wobble"] = 0.0
    wobble.meters["steady"] = 2.0
    monger.memes["surprise"] = 1.0
    monger.memes["pride"] = 1.0
    world.say(
        f"With one snug push and one gentle grin, the trouble was gone, and {problem.surprise_image}."
    )
    world.say(
        f"The {setting.crowd} laughed in surprise, because the smallest kindness had done the tallest work of all."
    )
    world.say(
        f"And {params.name} packed up the cart, leaving the wedge where it belonged and the day standing straighter than a sapling."
    )

    world.facts.update(
        name=params.name,
        trait=params.trait,
        setting=setting,
        problem=problem,
        tool=tool,
        kind=True,
        surprise=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for young children about a {f["trait"]} wedge-monger who helps at {f["setting"].place}.',
        f"Tell a story where {f['name']} uses a wedge to fix a wobbling problem and the crowd feels surprise and kindness.",
        f'Write a simple tall tale that includes the words "profession", "wedge", and "monger".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    name = f["name"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {trait} wedge-monger {name}, who carried wedges and helped people steady wobbly things.",
        ),
        QAItem(
            question=f"What was wrong with {problem.thing} before the fix?",
            answer=f"It was {problem.wobble}, so the people at {setting.place} needed a steadying wedge.",
        ),
        QAItem(
            question=f"What did {name} use to solve the problem?",
            answer=f"{name} used {tool.label} and slid it {tool.fits}, which helped {tool.helps}.",
        ),
        QAItem(
            question="Why were the people surprised?",
            answer="They expected a tiny wedge to do only a tiny job, but it quietly fixed the whole trouble and made everyone smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a profession?",
            answer="A profession is a kind of work a person does to help other people and earn a living.",
        ),
        QAItem(
            question="What is a wedge?",
            answer="A wedge is a tool with a thin end and a thick end. People use it to split things or hold something steady.",
        ),
        QAItem(
            question="What does a monger do?",
            answer="A monger is a person who sells a certain thing or deals in it, like a fishmonger or a wedge-monger in this tale.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating others gently and helping when they need it.",
        ),
        QAItem(
            question="What is surprise?",
            answer="Surprise is the feeling you get when something happens that you did not expect.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show shown/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_candidates()
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            p = StoryParams(setting=setting, problem=SETTINGS[setting].afford, name=NAMES[0], trait=TRAITS[0])
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
