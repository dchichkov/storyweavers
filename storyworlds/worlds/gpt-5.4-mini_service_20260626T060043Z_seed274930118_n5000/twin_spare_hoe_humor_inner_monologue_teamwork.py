#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/twin_spare_hoe_humor_inner_monologue_teamwork.py
===============================================================================================================================

A small fable-style storyworld about twins, a spare hoe, humor, inner monologue,
and teamwork.

Seed tale premise:
---
A pair of twin siblings want to help their family in a garden, but the only
good hoe is bent. A spare hoe is small and clumsy, and both twins think they
can do the job alone. A little comedy, a few private worries, and a shared plan
turn the chore into teamwork.

World model:
---
- Two twin characters share a garden task.
- A primary hoe can be broken or missing.
- A spare hoe may be lighter, smaller, or less efficient.
- Soil patches and weeds track progress in meters.
- Memes track pride, worry, delight, and teamwork.

Narrative instruments:
---
- Humor: the spare hoe's awkwardness creates a gentle comic beat.
- Inner Monologue: each twin privately worries or boasts.
- Teamwork: the twins combine efforts and succeed together.

The story is narrated in a child-facing fable style, with a clear beginning,
middle turn, and ending image that proves what changed.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"use": 0.0, "damage": 0.0, "weeds": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "joy": 0.0, "humor": 0.0, "teamwork": 0.0}

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
    place: str = "the garden"
    season: str = "spring"
    weeds: str = "soft weeds"
    crop: str = "carrots"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    strength: float
    awkward: bool = False
    spare: bool = False


@dataclass
class StoryParams:
    name_left: str
    name_right: str
    role_left: str
    role_right: str
    parent: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "garden": Setting(place="the garden", season="spring", weeds="thin weeds", crop="carrots"),
    "orchard": Setting(place="the orchard", season="summer", weeds="stubborn weeds", crop="berries"),
    "yard": Setting(place="the yard", season="autumn", weeds="curling weeds", crop="beans"),
}

TWIN_NAMES = [
    ("Mina", "Milo"),
    ("Lina", "Leo"),
    ("Nia", "Niko"),
    ("Ada", "Ari"),
    ("Zoe", "Zane"),
]

ROLES = ["curious", "cheerful", "practical", "stubborn", "quick-thinking", "gentle"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]

TOOLS = {
    "hoe": Tool(
        id="hoe",
        label="the hoe",
        phrase="a sturdy garden hoe",
        strength=2.0,
        awkward=False,
        spare=False,
    ),
    "spare_hoe": Tool(
        id="spare_hoe",
        label="the spare hoe",
        phrase="a smaller spare hoe",
        strength=1.0,
        awkward=True,
        spare=True,
    ),
}

ASP_RULES = r"""
primary_tool(hoe).
primary_tool(spare_hoe).

awkward(spare_hoe).
spare(spare_hoe).

good_for(T) :- primary_tool(T), not awkward(T).
usable(T) :- primary_tool(T).
helpful(T) :- usable(T), not broken(T).
works_well(T) :- helpful(T), not awkward(T).

team_solution(T1, T2) :- primary_tool(T1), spare(T2), T1 != T2.
"""

# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------


def _narrate_inner_monologue(world: World, twin: Entity, tool: Entity, shared_task: str) -> None:
    if twin.memes["pride"] >= THRESHOLD:
        world.say(
            f'Inside, {twin.id} thought, "I can do this all by myself."'
        )
    else:
        world.say(
            f'Inside, {twin.id} thought, "I hope this tool does not make me look silly."'
        )


def _use_tool(world: World, actor: Entity, tool: Entity, narrate: bool = True) -> None:
    if tool.id == "hoe" and tool.meters["damage"] >= THRESHOLD:
        return
    actor.meters["use"] += 1
    if tool.id == "spare_hoe":
        tool.meters["use"] += 1
        actor.memes["humor"] += 1
    if narrate:
        if tool.id == "spare_hoe":
            world.say(f"{actor.id} tried the spare hoe, and it wobbled like a fish on a line.")
        else:
            world.say(f"{actor.id} worked with the hoe, taking neat bites out of the weeds.")


def _clear_weeds(world: World, actor: Entity, tool: Entity, narrate: bool = True) -> None:
    weeds = world.facts["weeds"]
    strength = tool.meters.get("strength", 1.0) if False else (TOOLS[tool.id].strength)
    if tool.id == "spare_hoe":
        cleared = 1.0
        actor.memes["humor"] += 1
    else:
        cleared = 2.0
    if weeds.meters["weeds"] <= 0:
        return
    weeds.meters["weeds"] = max(0.0, weeds.meters["weeds"] - cleared)
    weeds.meters["tidy"] += cleared
    actor.meters["tidy"] += cleared
    if narrate:
        if tool.id == "spare_hoe":
            world.say("The spare hoe made a funny little clink, but it still pulled up a clump of weeds.")
        else:
            world.say("The hoe lifted the weeds cleanly, and the soil looked better at once.")


def _team_up(world: World, left: Entity, right: Entity, tool1: Entity, tool2: Entity) -> None:
    left.memes["teamwork"] += 1
    right.memes["teamwork"] += 1
    world.say(f"{left.id} and {right.id} looked at each other and decided to work as one team.")
    world.say(
        f"{left.id} held the spare hoe steady while {right.id} guided the good hoe through the dirt."
    )
    _use_tool(world, left, tool2, narrate=False)
    _clear_weeds(world, left, tool2, narrate=True)
    _use_tool(world, right, tool1, narrate=False)
    _clear_weeds(world, right, tool1, narrate=True)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    left = world.add(Entity(
        id=params.name_left,
        kind="character",
        type=params.role_left,
        label=params.name_left,
        meters={"use": 0.0, "damage": 0.0, "weeds": 0.0, "tidy": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "joy": 0.0, "humor": 0.0, "teamwork": 0.0},
    ))
    right = world.add(Entity(
        id=params.name_right,
        kind="character",
        type=params.role_right,
        label=params.name_right,
        meters={"use": 0.0, "damage": 0.0, "weeds": 0.0, "tidy": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "joy": 0.0, "humor": 0.0, "teamwork": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    hoe = world.add(Entity(id="hoe", type="tool", label="the hoe", phrase="a sturdy garden hoe"))
    spare = world.add(Entity(id="spare_hoe", type="tool", label="the spare hoe", phrase="a smaller spare hoe", plural=False))
    weeds = world.add(Entity(id="weeds", type="patch", label=setting.weeds, phrase=setting.weeds, meters={"use": 0.0, "damage": 0.0, "weeds": 3.0, "tidy": 0.0}))

    world.facts.update(left=left, right=right, parent=parent, hoe=hoe, spare=spare, weeds=weeds, setting=setting)

    world.say(
        f"Once, in {setting.place}, twins named {left.id} and {right.id} found a patch of {setting.weeds} crowding the {setting.crop}."
    )
    world.say(
        f"{left.id} pointed at the garden hoe and said it was best for the work."
    )
    world.say(
        f"{right.id} saw the spare hoe and tried not to laugh, because it looked a little too small for such a serious job."
    )
    world.say(
        f"The twins each thought they could be the one who finished first."
    )

    world.para()
    _narrate_inner_monologue(world, left, hoe, "pulling weeds")
    _narrate_inner_monologue(world, right, spare, "pulling weeds")

    world.say(
        f"Then {left.id} lifted the hoe, but the handle snagged the tall weeds and made the pile lean sideways."
    )
    world.say(
        f"{right.id} picked up the spare hoe, and it gave a silly little wobble, as if it were bowing to the dirt."
    )
    world.say(
        f"That made both twins grin, and the garden seemed less heavy already."
    )

    world.para()
    _team_up(world, left, right, hoe, spare)
    left.memes["joy"] += 1
    right.memes["joy"] += 1
    parent.memes["joy"] += 1

    world.say(
        f"At last, the weeds were gone, the {setting.crop} had room to grow, and the twins stood shoulder to shoulder in the soft earth."
    )
    world.say(
        f"The spare hoe was still small, but it had helped, and the honest hoe had helped too; together they had done the work."
    )

    world.facts.update(resolved=True, weeds=weeds, left_name=left.id, right_name=right.id, parent_name=parent.label)
    return world


# ---------------------------------------------------------------------------
# Story/QA generation
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    left = f["left"]
    right = f["right"]
    setting = f["setting"]
    return [
        f"Write a short fable about twins in {setting.place} who use a spare hoe and learn to work together.",
        f"Tell a gentle story for children in which {left.id} and {right.id} begin by wanting to do the garden work alone, but a funny spare hoe helps them share the task.",
        f"Write a child-friendly fable with inner thoughts, humor, and teamwork, ending with twins clearing weeds in {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    left = f["left"]
    right = f["right"]
    setting = f["setting"]
    weeds = f["weeds"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who are the story's main helpers in {setting.place}?",
            answer=f"The main helpers are the twins {left.id} and {right.id}, who work in {setting.place}.",
        ),
        QAItem(
            question=f"What did the twins need to clear from the garden?",
            answer=f"They needed to clear {setting.weeds} so the {setting.crop} could grow with more room.",
        ),
        QAItem(
            question="What made the spare hoe funny?",
            answer="The spare hoe was small and wobbly, so it looked a little silly in the twins' hands, but it still helped.",
        ),
        QAItem(
            question=f"How did the twins change by the end?",
            answer=f"At the end, {left.id} and {right.id} stopped trying to prove who was best and worked together instead.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="Why did the work succeed in the end?",
                answer="The work succeeded because the twins shared the tools and used teamwork instead of pride.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "hoe": [
        QAItem(
            question="What is a hoe used for in a garden?",
            answer="A hoe is used to loosen soil and pull up weeds around plants.",
        )
    ],
    "spare": [
        QAItem(
            question="What is a spare thing?",
            answer="A spare thing is an extra one kept ready in case the first one is missing, broken, or busy.",
        )
    ],
    "twin": [
        QAItem(
            question="What are twins?",
            answer="Twins are two siblings who are born at about the same time.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        )
    ],
    "humor": [
        QAItem(
            question="Why can a funny moment help a story?",
            answer="A funny moment can make worried characters relax and notice they can solve a problem together.",
        )
    ],
    "inner_monologue": [
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thoughts, like the words they say inside their own head.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        item
        for key in ["twin", "hoe", "spare", "humor", "inner_monologue", "teamwork"]
        for item in WORLD_KNOWLEDGE[key]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
twin(left).
twin(right).
tool(hoe).
tool(spare_hoe).

spare(spare_hoe).
awkward(spare_hoe).

teamwork_possible :- twin(left), twin(right), tool(hoe), spare(spare_hoe).
funny_fix :- awkward(spare_hoe), spare(spare_hoe).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("twin", "left"),
        asp.fact("twin", "right"),
        asp.fact("tool", "hoe"),
        asp.fact("tool", "spare_hoe"),
        asp.fact("spare", "spare_hoe"),
        asp.fact("awkward", "spare_hoe"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork_possible/0. #show funny_fix/0."))
    atoms = {str(sym) for sym in model}
    expected = {"teamwork_possible", "funny_fix"}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python twin rules.")
    print("  ASP:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Params, parsing, generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name_left="Mina", name_right="Milo", role_left="curious", role_right="practical", parent="mother", setting="garden"),
    StoryParams(name_left="Lina", name_right="Leo", role_left="cheerful", role_right="stubborn", parent="father", setting="orchard"),
    StoryParams(name_left="Ada", name_right="Ari", role_left="gentle", role_right="quick-thinking", parent="grandmother", setting="yard"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: twins, a spare hoe, humor, inner monologue, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name-left")
    ap.add_argument("--name-right")
    ap.add_argument("--role-left", choices=ROLES)
    ap.add_argument("--role-right", choices=ROLES)
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.name_left and args.name_right and args.name_left == args.name_right:
        raise StoryError("The twins need two different names.")
    names = rng.choice(TWIN_NAMES)
    left_name = args.name_left or names[0]
    right_name = args.name_right or names[1]
    role_left = args.role_left or rng.choice(ROLES)
    role_right = args.role_right or rng.choice([r for r in ROLES if r != role_left])
    parent = args.parent or rng.choice(PARENTS)
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(
        name_left=left_name,
        name_right=right_name,
        role_left=role_left,
        role_right=role_right,
        parent=parent,
        setting=setting,
    )


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
        print(asp_program("#show teamwork_possible/0. #show funny_fix/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show teamwork_possible/0. #show funny_fix/0."))
        print("ASP atoms:", ", ".join(str(sym) for sym in model))
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
            header = f"### {p.name_left} and {p.name_right} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
