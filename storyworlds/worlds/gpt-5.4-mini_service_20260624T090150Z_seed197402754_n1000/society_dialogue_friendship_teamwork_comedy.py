#!/usr/bin/env python3
"""
storyworlds/worlds/society_dialogue_friendship_teamwork_comedy.py
===============================================================

A small comedy storyworld about a tiny society where friends use dialogue and
teamwork to solve a public problem without getting too fussy about it.

Seed tale:
---
In a little town square, a snack cart keeps getting stuck because everyone is
trying to move it at once and nobody is speaking clearly. A cheerful child and
a friend notice the confusion, ask questions, make a plan, and work together.
They use a rope, take turns, and soon the cart rolls free. Everyone laughs,
thanks them, and shares the snacks.

World model:
---
- A public place has a small crowd, a stuck object, and a simple goal.
- Characters have meters like effort, stuckness, and tidiness; and memes like
  cheer, worry, patience, and friendship.
- Dialogue changes state: asking questions reduces confusion; a clear plan
  increases teamwork.
- Friendship and teamwork resolve the problem and end with a funny, happy image.

The story engine chooses a plausible pair of friends and a suitable public
object, then simulates the talk-and-work chain into a punchline ending.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the town square"
    public: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    verb: str
    stuck_word: str
    fix_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_verb: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.problem_id: str = ""

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
        clone.problem_id = self.problem_id
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


PROBLEMS = {
    "cart": Problem(
        id="cart",
        label="snack cart",
        phrase="a little snack cart",
        verb="roll the snack cart",
        stuck_word="stuck",
        fix_word="unstuck",
        tags={"public", "snack", "wheel"},
    ),
    "bench": Problem(
        id="bench",
        label="park bench",
        phrase="a wobbly park bench",
        verb="move the bench",
        stuck_word="stuck",
        fix_word="steady",
        tags={"public", "bench"},
    ),
    "float": Problem(
        id="float",
        label="festival float",
        phrase="a tiny parade float",
        verb="pull the float",
        stuck_word="stuck",
        fix_word="moving",
        tags={"public", "festival"},
    ),
}

TOOLS = [
    Tool(id="rope", label="a rope", phrase="a rope", use_verb="pull", helps={"cart", "float"}),
    Tool(id="wedge", label="a wooden wedge", phrase="a wooden wedge", use_verb="prop", helps={"bench"}),
    Tool(id="rollers", label="rollers", phrase="some small rollers", use_verb="place", helps={"cart", "float"}, plural=True),
]

SETTINGS = {
    "square": Setting(place="the town square", public=True, affords={"cart", "bench", "float"}),
    "fair": Setting(place="the spring fair", public=True, affords={"cart", "float"}),
    "park": Setting(place="the park path", public=True, affords={"bench", "cart"}),
}

NAMES = ["Mila", "Noah", "Ada", "Theo", "Lena", "Owen", "Maya", "Finn"]
FRIEND_NAMES = ["Pip", "June", "Zed", "Ivy", "Bea", "Rio"]
TRAITS = ["cheerful", "curious", "kind", "silly", "quick-thinking"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(problem: Problem, setting: Setting) -> bool:
    return problem.id in setting.affords


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.id in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            if select_tool(PROBLEMS[pid]) is not None:
                out.append((place, pid))
    return out


def _meeting(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} and {friend.id} came to {world.setting.place} and saw {problem.phrase} {problem.stuck_word}."
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    friend.memes["curiosity"] = friend.memes.get("curiosity", 0) + 1
    world.facts["stuck"] = problem.id


def _dialogue(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["patience"] = friend.memes.get("patience", 0) + 1
    world.say(
        f'"Why is it {problem.stuck_word}?" {hero.id} asked.'
    )
    world.say(
        f'"Because everyone is pulling the same way," {friend.id} said. "Let\'s make a plan."'
    )
    world.facts["planned"] = True


def _plan(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    hero.memes["cheer"] = hero.memes.get("cheer", 0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0) + 1
    world.say(
        f"They found {tool.phrase}, and {hero.id} said, \"I can {tool.use_verb} while you guide.\""
    )
    world.say(
        f'"Perfect," said {friend.id}. "That sounds less heroic and much less wobbly."'
    )
    world.facts["tool"] = tool.id


def _work(world: World, hero: Entity, friend: Entity, problem: Problem, tool: Tool) -> None:
    if tool.id == "rope":
        world.say(
            f"{hero.id} held one end, {friend.id} held the other, and they counted, \"One, two, pull!\""
        )
        world.say(
            f"The cart gave a tiny squeak, then rolled free like it had remembered how to behave."
        )
    elif tool.id == "rollers":
        world.say(
            f"They placed the rollers under the float, and it scooted forward with a very important little rattle."
        )
    else:
        world.say(
            f"{friend.id} slipped the wedge under the bench, and the bench stopped wobbling like a nervous spoon."
        )
    world.facts["fixed"] = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1


def _ending(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    world.para()
    if problem.id == "cart":
        world.say(
            f"Everyone laughed because the cart rolled straight to the snack table as if it had been waiting for directions all morning."
        )
        world.say(
            f"{hero.id} and {friend.id} got the first cookies, and the snack cart looked proud of itself."
        )
    elif problem.id == "bench":
        world.say(
            f"The bench sat steady at last, and even the birds seemed to nod at the excellent teamwork."
        )
        world.say(
            f"{hero.id} and {friend.id} shared a very serious high-five that was immediately ruined by giggles."
        )
    else:
        world.say(
            f"The float moved on, and its paper flowers bounced so much that everyone clapped for the flowers too."
        )
        world.say(
            f"{hero.id} and {friend.id} bowed to the crowd, which made the crowd laugh even harder."
        )


def tell(setting: Setting, problem: Problem, hero_name: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in {"Mila", "Ada", "Lena", "Maya"} else "boy"))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl" if friend_name in {"Pip", "June", "Ivy", "Bea"} else "boy"))
    tool = select_tool(problem)
    if tool is None:
        raise StoryError("No reasonable teamwork tool exists for this problem.")
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["problem"] = problem
    world.facts["setting"] = setting
    world.facts["tool_obj"] = tool

    _meeting(world, hero, friend, problem)
    world.para()
    _dialogue(world, hero, friend, problem)
    _plan(world, hero, friend, tool)
    world.para()
    _work(world, hero, friend, problem, tool)
    _ending(world, hero, friend, problem)

    world.facts.update(tool=tool, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, problem = f["hero"], f["friend"], f["problem"]
    return [
        'Write a short, funny story for a young child about a public place, a problem, and a team fix.',
        f"Tell a comedy story where {hero.id} and {friend.id} use dialogue and teamwork to solve {problem.phrase}.",
        f'Write a gentle story about "{world.setting.place}" and make sure the friends talk before they act.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, problem, tool = f["hero"], f["friend"], f["problem"], f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} and {friend.id} see at {world.setting.place}?",
            answer=f"They saw {problem.phrase} {problem.stuck_word}, so they needed a plan.",
        ),
        QAItem(
            question=f"What did {friend.id} say after {hero.id} asked why it was {problem.stuck_word}?",
            answer=f"{friend.id} said that everyone was pulling the same way and that they should make a plan.",
        ),
        QAItem(
            question=f"How did {tool.label} help the friends?",
            answer=f"It gave them a careful way to work together, so they could {problem.verb} and make the problem {problem.fix_word}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem solved, everyone laughing, and {hero.id} and {friend.id} feeling proud of their teamwork.",
        ),
    ]


KNOWLEDGE = {
    "society": [
        QAItem(
            question="What is a society?",
            answer="A society is a group of people who live, work, and play around one another and share places like streets, parks, and shops.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is talking between people in a story, like asking questions, answering, and making plans.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and enjoy spending time together.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and each person does a part of the job.",
        )
    ],
    "comedy": [
        QAItem(
            question="What makes a story funny?",
            answer="A story can be funny when characters say silly things, make a small mistake, or laugh after solving a problem.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *KNOWLEDGE["society"],
        *KNOWLEDGE["dialogue"],
        *KNOWLEDGE["friendship"],
        *KNOWLEDGE["teamwork"],
        *KNOWLEDGE["comedy"],
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", problem="cart", name="Mila", friend="Pip", trait="cheerful"),
    StoryParams(place="fair", problem="float", name="Noah", friend="June", trait="curious"),
    StoryParams(place="park", problem="bench", name="Ada", friend="Zed", trait="kind"),
]


ASP_RULES = r"""
problem(P) :- prob(P).
tool(T) :- t(T).
place(X) :- plc(X).

compatible(Place, Problem, Tool) :- place(Place), problem(Problem), tool(Tool),
    affords(Place, Problem), helps(Tool, Problem).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("plc", pid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("prob", pid))
    for t in TOOLS:
        lines.append(asp.fact("t", t.id))
        for p in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only python:", sorted(py - cl))
    print(" only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy society storyworld with dialogue, friendship, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if friend == name:
        raise StoryError("The hero and friend should be different characters.")
    return StoryParams(place=place, problem=problem, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], params.name, params.friend, params.trait)
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible combos:\n")
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
