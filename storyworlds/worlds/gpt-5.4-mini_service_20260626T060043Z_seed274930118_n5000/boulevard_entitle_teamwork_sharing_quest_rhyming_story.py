#!/usr/bin/env python3
"""
A small story world for a rhyming teamwork-and-sharing quest on a boulevard.

This world models a child-sized quest where friends travel down a boulevard,
discover a small problem, and solve it by sharing tools and working together.
The prose is intentionally rhythmic and child-facing, with a clear turn and a
visible ending change in the world state.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the boulevard"
    surface: str = "wide stone path"
    affordance: str = "walking"


@dataclass
class Quest:
    goal: str
    object_name: str
    object_phrase: str
    missing: str
    rhyme_key: str
    risk: str
    success_image: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    shared: bool = True


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


@dataclass
class StoryParams:
    name: str
    friend: str
    parent: str
    quest: str
    tool: str
    seed: Optional[int] = None


NAMES = ["Mia", "Leo", "Nora", "Ben", "Zoe", "Finn", "Ava", "Eli"]
FRIENDS = ["friend", "pal", "buddy", "mate"]
PARENTS = ["mother", "father"]
SETTING = Setting(
    place="the boulevard",
    surface="bright brick boulevard",
    affordance="strolling"
)

QUESTS = {
    "kite": Quest(
        goal="fly a kite",
        object_name="kite",
        object_phrase="a bright blue kite",
        missing="string",
        rhyme_key="kite",
        risk="the kite might drift away",
        success_image="the kite dancing high above the boulevard"
    ),
    "map": Quest(
        goal="find the map",
        object_name="map",
        object_phrase="a folded treasure map",
        missing="corner",
        rhyme_key="map",
        risk="the map might tear or tumble",
        success_image="the map unfolding safe and smooth"
    ),
    "snack": Quest(
        goal="share a snack",
        object_name="snack",
        object_phrase="a small fruit snack",
        missing="spoon",
        rhyme_key="snack",
        risk="the snack might spill on the way",
        success_image="the snack shared neatly in the middle"
    ),
}

TOOLS = {
    "spool": Tool(
        id="spool",
        label="spool of string",
        phrase="a spool of string",
        helps={"kite"},
    ),
    "clip": Tool(
        id="clip",
        label="paper clip",
        phrase="a tiny paper clip",
        helps={"map"},
    ),
    "napkin": Tool(
        id="napkin",
        label="napkin",
        phrase="a clean napkin",
        helps={"snack"},
    ),
}


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def introduce(world: World, child: Entity, friend: Entity, parent: Entity, quest: Quest) -> None:
    world.say(
        f"On the boulevard, with a shine and a glow, {child.id} and {friend.id} were ready to go."
    )
    world.say(
        f"They loved a small quest with a merry-sweet beat: to {quest.goal} with quick little feet."
    )
    world.say(
        f"{child.id}'s {parent.label} smiled and said, \"Go on, be bright; share what you find, and do it just right.\""
    )


def start_quest(world: World, child: Entity, friend: Entity, quest: Quest) -> None:
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    friend.memes["curious"] = friend.memes.get("curious", 0) + 1
    world.say(
        f"They skipped to the boulevard stones, side by side, with teamwork in step and no need to hide."
    )
    world.say(
        f"But soon they saw trouble, a tiny one there: {quest.risk}, waiting in air."
    )


def notice_missing(world: World, quest: Quest) -> None:
    world.say(
        f"Their plan needed {quest.missing}, yet the bag had none; that made the quest harder than fun."
    )


def choose_tool(world: World, tool: Tool, quest: Quest) -> None:
    world.say(
        f"Then {tool.label} appeared with a shimmer and gleam, just right for the quest and just right for the team."
    )
    world.say(
        f"They agreed to share it, not grab it alone; that sharing made courage begin to be shown."
    )


def work_together(world: World, child: Entity, friend: Entity, tool: Tool, quest: Quest) -> None:
    child.memes["teamwork"] = child.memes.get("teamwork", 0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0) + 1
    child.memes["sharing"] = child.memes.get("sharing", 0) + 1
    friend.memes["sharing"] = friend.memes.get("sharing", 0) + 1

    world.say(
        f"{child.id} held one side, and {friend.id} held the other; they passed the {tool.label} like sister and brother."
    )
    world.say(
        f"They used it together with careful delight, and the quest felt lighter, more cheerful, more right."
    )


def resolve(world: World, child: Entity, friend: Entity, quest: Quest) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"At last, {quest.success_image} shone in the sky, and both little helpers let out a cry."
    )
    world.say(
        f"{child.id} laughed, \"We did it!\" {friend.id} cheered, \"So neat!\" Their sharing had turned the hard part sweet."
    )
    world.say(
        f"They walked home down the boulevard glow, with teamwork in their hearts and a happy soft snow."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type="girl"))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy"))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother", label=params.parent))
    quest = QUESTS[params.quest]
    tool = TOOLS[params.tool]

    if quest.object_name not in tool.helps:
        raise StoryError(f"{tool.label} does not reasonably help with the {quest.object_name} quest.")

    child.meters["distance"] = 0
    friend.meters["distance"] = 0

    introduce(world, child, friend, parent, quest)
    world.para()
    start_quest(world, child, friend, quest)
    notice_missing(world, quest)
    world.say(f"They looked around the boulevard, thinking, then found a way to share instead of stalling.")

    world.para()
    choose_tool(world, tool, quest)
    work_together(world, child, friend, tool, quest)
    resolve(world, child, friend, quest)

    world.facts.update(child=child, friend=friend, parent=parent, quest=quest, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    tool = f["tool"]
    return [
        f'Write a rhyming little story about a child named {child.id} on the boulevard.',
        f"Tell a teamwork story where friends share {tool.phrase} to {quest.goal}.",
        f"Make a gentle quest tale with sharing, a small problem, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    quest = f["quest"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was {child.id} trying to do on the boulevard?",
            answer=f"{child.id} and {friend.id} were trying to {quest.goal}.",
        ),
        QAItem(
            question=f"What helped the two friends finish the quest?",
            answer=f"They shared {tool.phrase} and used it together with teamwork.",
        ),
        QAItem(
            question=f"Why did the quest feel hard at first?",
            answer=f"It felt hard because {quest.risk}, and they were missing the right part at first.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help one another reach the same goal.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something with you.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or journey where someone tries to find, fix, or finish something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork-and-sharing quest on a boulevard.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    quest = args.quest or rng.choice(list(QUESTS))
    tool = args.tool or rng.choice([k for k, v in TOOLS.items() if quest in v.helps])
    if quest not in TOOLS[tool].helps:
        raise StoryError(f"{TOOLS[tool].label} doesn't fit the {quest} quest.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        parent=args.parent or rng.choice(PARENTS),
        quest=quest,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
quest_help(T, Q) :- tool(T), quest(Q), helps(T, Q).
valid_story(N, F, P, Q, T) :- name(N), friend(F), parent(P), quest(Q), tool(T), quest_help(T, Q).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    for p in PARENTS:
        lines.append(asp.fact("parent", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        for q in sorted(tool.helps):
            lines.append(asp.fact("helps", t, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = set()
    for q in QUESTS:
        for t, tool in TOOLS.items():
            if q in tool.helps:
                for n in NAMES:
                    for f in FRIENDS:
                        for p in PARENTS:
                            py.add((n, f, p, q, t))
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(atoms - py))
    print("Only in Python:", sorted(py - atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} compatible stories")
        for item in items[:20]:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for q in QUESTS:
            for t, tool in TOOLS.items():
                if q in tool.helps:
                    params = StoryParams(
                        name=NAMES[0],
                        friend=FRIENDS[0],
                        parent=PARENTS[0],
                        quest=q,
                        tool=t,
                    )
                    samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
