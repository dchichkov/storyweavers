#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a tiny quest, a quiet nobody, and an
eleventh little throat-singing test.

Seed tale imagined from the prompt:
---
On the eleventh step of the day, nobody could sing the next line of the rhyme,
for a pebble had tickled the throat. A little rabbit and a lantern-bearer went
on a quest to fetch honey, warm water, and a feather to make the throat feel
better. They crossed a mossy bridge, asked a kind baker for help, and in the
end the nobody found their voice again and sang the last line of the rhyme.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "nobody":
            return {"subject": "nobody", "object": "nobody", "possessive": "nobody's"}[case]
        if self.type in {"rabbit"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the nursery lane"


@dataclass
class Quest:
    id: str
    goal: str
    steps: list[str]
    risk: str
    cure: str
    charm: str
    keyword: str = "quest"


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: str


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery_lane": Setting(place="the nursery lane"),
}

QUESTS = {
    "throat_quest": Quest(
        id="throat_quest",
        goal="find a gentle cure for a sore throat",
        steps=["hear the little cough", "walk to the baker", "carry warm honey", "sing the last line"],
        risk="the throat might stay scratchy",
        cure="warm honey water",
        charm="a soft feather",
        keyword="Quest",
    ),
}

AIDS = {
    "honey": Aid(id="honey", label="honey", phrase="a spoon of golden honey", helps="soothes"),
    "water": Aid(id="water", label="warm water", phrase="a cup of warm water", helps="warms"),
    "feather": Aid(id="feather", label="feather", phrase="a tiny soft feather", helps="tickles"),
}

NAMES = ["Mimi", "Pip", "Luna", "Toby", "Nell", "Rory"]
HELPERS = ["rabbit", "baker", "bird", "cat"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: a tiny quest to help a sore throat.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    quest = args.quest or rng.choice(list(QUESTS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, quest=quest, name=name, helper=helper)


def choose_entity_name(helper: str) -> str:
    return {"rabbit": "Ruby", "baker": "Bram", "bird": "Blue", "cat": "Penny"}[helper]


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    quest = QUESTS[params.quest]

    nobody = world.add(Entity(
        id="nobody",
        kind="character",
        type="nobody",
        label="nobody",
        traits=["quiet", "small", "lonely"],
        memes={"hope": 1.0, "worry": 1.0},
        meters={"throat": 1.0},
    ))
    helper_name = choose_entity_name(params.helper)
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=helper_name,
        traits=["kind"],
        memes={"care": 1.0},
    ))
    throat = world.add(Entity(
        id="throat",
        kind="thing",
        type="throat",
        label="throat",
        phrase="a scratchy little throat",
        owner=nobody.id,
        meters={"scratch": 1.0},
    ))
    honey = world.add(Entity(
        id="honey",
        kind="thing",
        type="honey",
        label="honey",
        phrase=AIDS["honey"].phrase,
        owner=helper.id,
        meters={"sweet": 1.0},
    ))
    water = world.add(Entity(
        id="water",
        kind="thing",
        type="water",
        label="warm water",
        phrase=AIDS["water"].phrase,
        owner=helper.id,
        meters={"warm": 1.0},
    ))

    world.say(
        f"On the eleventh little step by {world.setting.place}, nobody had a throat that felt quite wrong."
    )
    world.say(
        f"The throat was scratchy, and nobody could not sing the next rhyme."
    )
    world.say(
        f"So nobody began a quest for honey, warm water, and one soft feather."
    )

    world.para()
    world.say(
        f"{helper_name} the {params.helper} came along, and together they walked the nursery lane."
    )
    world.say(
        f"They passed a brass gate, a mossy stone, and a baker who smiled like morning."
    )
    world.say(
        f"The baker gave them honey, and the helper carried warm water in a tiny cup."
    )

    world.para()
    world.say(
        f"Nobody sipped the warm water, and the honey soothed the scratchy throat."
    )
    throat.meters["scratch"] = 0.0
    throat.memes["ease"] = 1.0
    nobody.memes["hope"] = 2.0
    nobody.memes["joy"] = 2.0
    world.say(
        f"Then nobody took the soft feather, laughed a little, and tried the last line of the rhyme."
    )
    world.say(
        f"This time the voice came clear, and nobody sang all the way home."
    )

    world.facts.update(
        nobody=nobody,
        helper=helper,
        throat=throat,
        honey=honey,
        water=water,
        quest=quest,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle nursery-rhyme story about nobody, an eleventh step, and a scratchy throat.',
        f"Tell a short story where nobody goes on a {world.facts['quest'].keyword} to help a throat.",
        "Write a child-facing rhyme where a small helper brings honey and warm water, and the ending feels better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who went on the quest in the story?",
            answer="Nobody went on the quest, and a kind helper went with them.",
        ),
        QAItem(
            question="What was wrong with nobody at the start?",
            answer="Nobody had a scratchy throat, so singing the next line of the rhyme was hard.",
        ),
        QAItem(
            question="What did the helper bring to help?",
            answer="The helper brought honey and warm water, and that made the throat feel better.",
        ),
        QAItem(
            question="Why is the eleventh step important?",
            answer="It is the little starting place in the rhyme, where nobody first noticed the throat problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer="Nobody sang the last line of the rhyme with a clear voice and went home happier.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find or do something important.",
        ),
        QAItem(
            question="What can honey do?",
            answer="Honey can taste sweet and feel soothing when someone has a sore throat.",
        ),
        QAItem(
            question="What is a throat?",
            answer="A throat is the part inside the neck that people use for swallowing and singing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(nursery_lane, throat_quest, nobody) :- setting(nursery_lane), quest(throat_quest), character(nobody).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "nursery_lane"), asp.fact("quest", "throat_quest"), asp.fact("character", "nobody")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("nursery_lane", "throat_quest", "nobody")}
    if atoms == py:
        print("OK: ASP matches Python.")
        return 0
    print("MISMATCH:")
    print("asp:", sorted(atoms))
    print("py:", sorted(py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(setting="nursery_lane", quest="throat_quest", name="Mimi", helper="rabbit")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
