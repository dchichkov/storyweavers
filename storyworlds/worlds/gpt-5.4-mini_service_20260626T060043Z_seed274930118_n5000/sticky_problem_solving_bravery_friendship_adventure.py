#!/usr/bin/env python3
"""
A tiny adventure storyworld about a sticky problem, brave teamwork, and a
friendship-powered solution.

Premise:
- A child and a friend want to reach a small treasure across a sticky place.
- The sticky place creates a concrete obstacle that must be solved, not just
  described.
- The story resolves when the friends use a tool or plan that actually works.

This world is intentionally small and constraint-checked.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


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

    def __post_init__(self) -> None:
        for k in ["stuck", "tired", "safe", "found", "carried", "hope"]:
            self.meters.setdefault(k, 0.0)
        for k in ["bravery", "friendship", "problem_solving", "worry", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    sticky_source: str
    obstacle: str
    verb: str
    risk: str
    problem: str
    fix_hint: str
    clue: str
    keyword: str = "sticky"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps_against: set[str] = field(default_factory=set)
    carries: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.sticky: bool = False
        self.challenge_id: str = ""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "forest_path": Setting(place="the forest path", afford={"cross"},
                           ),
    "riverbank": Setting(place="the riverbank trail", afford={"cross"}),
    "cave_entry": Setting(place="the cave entrance", afford={"cross"}),
    "hilltrail": Setting(place="the hill trail", afford={"cross"}),
}

CHALLENGES = {
    "sap": Challenge(
        id="sap",
        sticky_source="tree sap",
        obstacle="sticky sap",
        verb="walk across the sticky sap",
        risk="get stuck",
        problem="the path is hard to cross",
        fix_hint="use a long stick and leaves",
        clue="the sap glues shoes to the ground",
        tags={"sticky", "forest", "adventure"},
    ),
    "mud": Challenge(
        id="mud",
        sticky_source="deep mud",
        obstacle="sticky mud",
        verb="cross the sticky mud",
        risk="sink and slow down",
        problem="the trail is slippery and heavy",
        fix_hint="step on flat stones",
        clue="the mud clings to boots",
        tags={"sticky", "trail", "adventure"},
    ),
    "honey": Challenge(
        id="honey",
        sticky_source="spilled honey",
        obstacle="sticky honey",
        verb="get past the sticky honey",
        risk="lose their grip",
        problem="the ground is sweet but troublesome",
        fix_hint="sprinkle dry sand",
        clue="the honey shines like gold",
        tags={"sticky", "problem_solving", "adventure"},
    ),
}

TOOLS = {
    "stick": Tool(
        id="stick",
        label="a long stick",
        phrase="a long, smooth stick",
        use="probe the path and lift the goo away",
        helps_against={"sap", "mud"},
    ),
    "leaves": Tool(
        id="leaves",
        label="dry leaves",
        phrase="a handful of dry leaves",
        use="make a stepping path",
        helps_against={"sap"},
        carries=True,
    ),
    "stones": Tool(
        id="stones",
        label="flat stones",
        phrase="a few flat stones",
        use="build a safe trail",
        helps_against={"mud"},
    ),
    "sand": Tool(
        id="sand",
        label="dry sand",
        phrase="a little bag of dry sand",
        use="soak up the sticky spill",
        helps_against={"honey"},
    ),
}

CHILD_NAMES = ["Mina", "Toby", "Lina", "Ezra", "Nora", "Owen", "Sana", "Theo"]
FRIEND_NAMES = ["Pip", "Rae", "Finn", "Mira", "Jude", "Tia", "Noa", "Kai"]
TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    challenge: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Inline Python reasonableness gate
# ---------------------------------------------------------------------------

def compatible(challenge: Challenge, tool: Tool) -> bool:
    return challenge.id in tool.helps_against


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for cid, ch in CHALLENGES.items():
        for tid, tool in TOOLS.items():
            if compatible(ch, tool):
                out.append((cid, tid))
    return out


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

class ConflictResolved(Exception):
    pass


def setting_detail(setting: Setting, challenge: Challenge) -> str:
    if setting.place == "the forest path":
        return f"The trees leaned over {setting.place}, and the air smelled like sap and pine."
    if setting.place == "the riverbank trail":
        return f"{setting.place.capitalize()} glittered near the water, but {challenge.obstacle} blocked the way."
    if setting.place == "the cave entrance":
        return f"{setting.place.capitalize()} was dark at the edge, and {challenge.obstacle} made the ground tricky."
    return f"{setting.place.capitalize()} stretched ahead like a path for a brave little adventure."


def do_challenge(world: World, child: Entity, friend: Entity, challenge: Challenge, tool: Tool) -> None:
    child.meters["stuck"] += 1
    friend.memes["worry"] += 1
    world.sticky = True
    world.challenge_id = challenge.id
    world.say(
        f"{child.id} wanted to {challenge.verb}, but {challenge.obstacle} made the path hard."
    )
    world.say(
        f"It could make {child.pronoun('object')} {challenge.risk}, so {friend.id} stayed close."
    )


def brave_decision(world: World, child: Entity, friend: Entity, tool: Tool) -> None:
    child.memes["bravery"] += 1
    friend.memes["friendship"] += 1
    child.memes["friendship"] += 1
    world.say(
        f"Then {friend.id} smiled and said, \"We can solve this together.\""
    )
    world.say(
        f"{child.id} took a brave breath and agreed to try {tool.label}."
    )


def use_tool(world: World, child: Entity, friend: Entity, challenge: Challenge, tool: Tool) -> None:
    if challenge.id not in tool.helps_against:
        raise StoryError("The chosen tool does not actually solve this sticky problem.")
    world.facts["tool"] = tool
    world.facts["challenge"] = challenge
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.say(
        f"{friend.id} used {tool.phrase} to {tool.use}."
    )
    world.say(
        f"That worked: the sticky spot gave way, and {child.id} could move forward."
    )
    child.memes["problem_solving"] += 1
    friend.memes["problem_solving"] += 1
    child.meters["stuck"] = 0
    friend.meters["hope"] += 1
    child.memes["relief"] += 1
    friend.memes["relief"] += 1


def finish_adventure(world: World, child: Entity, friend: Entity, challenge: Challenge) -> None:
    world.say(
        f"Together they reached the other side, where a small treasure waited in the open air."
    )
    world.say(
        f"{child.id} grinned at {friend.id}, because bravery, friendship, and a good plan had won the day."
    )


def tell(setting: Setting, challenge: Challenge, tool: Tool,
         child_name: str, child_type: str, friend_name: str, friend_type: str,
         parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))

    world.say(
        f"{child.id} and {friend.id} were ready for a little adventure at {setting.place}."
    )
    world.say(
        f"They were looking for a small treasure, but first they had to face {challenge.obstacle}."
    )
    world.para()
    world.say(setting_detail(setting, challenge))
    do_challenge(world, child, friend, challenge, tool)
    world.say(
        f"{parent.label_word if hasattr(parent, 'label_word') else 'the parent'} had once said that sticky places need careful thinking."
    )
    world.para()
    brave_decision(world, child, friend, tool)
    use_tool(world, child, friend, challenge, tool)
    finish_adventure(world, child, friend, challenge)
    world.facts.update(
        setting=setting,
        challenge=challenge,
        tool=tool,
        parent=parent,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    challenge: Challenge = f["challenge"]
    tool: Tool = f["tool"]
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    return [
        f"Write a short adventure story for a young child about {child.id} and {friend.id} facing a sticky problem.",
        f"Tell a brave friendship story where two kids solve {challenge.obstacle} with {tool.label}.",
        f"Create a child-friendly adventure that includes the word \"sticky\" and ends with a clever solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    challenge: Challenge = f["challenge"]
    tool: Tool = f["tool"]
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    return [
        QAItem(
            question=f"What sticky problem did {child.id} and {friend.id} face?",
            answer=f"They faced {challenge.obstacle}, which made the path hard to cross.",
        ),
        QAItem(
            question=f"How did {friend.id} help solve the problem?",
            answer=f"{friend.id} used {tool.label} to {tool.use}, which made the way safe again.",
        ),
        QAItem(
            question=f"What did the story show about {child.id} and {friend.id}?",
            answer=f"It showed that bravery, problem solving, and friendship can help friends get through a sticky adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sticky mean?",
            answer="Sticky means something can cling to other things, like sap, honey, or mud that grabs onto shoes and fingers.",
        ),
        QAItem(
            question="Why do friends work together on hard problems?",
            answer="Friends work together because two people can think of more ideas, share the work, and feel braver side by side.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something hard or a little scary even when you still feel worried.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A sticky problem is compatible with a tool only if the tool helps against it.
compatible(C,T) :- challenge(C), tool(T), helps(T,C).

valid_story(P,C,T) :- place(P), challenge(C), tool(T), affords(P,C), compatible(C,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", pid, a))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for cid in sorted(tool.helps_against):
            lines.append(asp.fact("helps", tid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    clingo_set = set(asp.atoms(asp.one_model(program), "valid_story"))
    py_set = set((place, challenge, tool) for (place, challenge), tool in [])


def asp_valid_combos() -> list[tuple[str, str, str]]:
    return sorted(
        (pid, cid, tid)
        for pid in SETTINGS
        for cid, ch in CHALLENGES.items()
        for tid, tool in TOOLS.items()
        if pid in SETTINGS and compatible(ch, tool)
    )


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def valid_story_params() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for cid, ch in CHALLENGES.items():
            for tid, tool in TOOLS.items():
                if compatible(ch, tool):
                    out.append((place, cid, tid))
    return out


def explain_rejection(challenge: Challenge, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not really solve {challenge.obstacle}. "
        f"Pick a tool that can actually help with this sticky problem.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Sticky adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-type", choices=TYPES)
    ap.add_argument("--friend-type", choices=TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.challenge and args.tool:
        if not compatible(CHALLENGES[args.challenge], TOOLS[args.tool]):
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], TOOLS[args.tool]))
    combos = valid_story_params()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, challenge, tool = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(TYPES)
    friend_type = args.friend_type or rng.choice(TYPES)
    parent_type = args.parent or rng.choice(PARENT_TYPES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(
        place=place,
        challenge=challenge,
        child_name=child_name,
        child_type=child_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CHALLENGES[params.challenge],
        next(t for t in TOOLS.values() if t.id in {t.id for t in TOOLS.values()} and compatible(CHALLENGES[params.challenge], t)),
        params.child_name,
        params.child_type,
        params.friend_name,
        params.friend_type,
        params.parent_type,
    )
    # recover selected tool from params by matching compatibility and determinism
    chosen_tool = None
    for tool in TOOLS.values():
        if compatible(CHALLENGES[params.challenge], tool):
            chosen_tool = tool
            break
    if chosen_tool is None:
        raise StoryError("No compatible tool found.")
    world = tell(
        SETTINGS[params.place],
        CHALLENGES[params.challenge],
        chosen_tool,
        params.child_name,
        params.child_type,
        params.friend_name,
        params.friend_type,
        params.parent_type,
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, challenge, tool in valid_story_params():
            params = StoryParams(
                place=place,
                challenge=challenge,
                child_name=CHILD_NAMES[0],
                child_type=TYPES[0],
                friend_name=FRIEND_NAMES[0],
                friend_type=TYPES[1],
                parent_type=PARENT_TYPES[0],
                seed=base_seed,
            )
            # stable but varied enough for --all
            chosen_tool = TOOLS[tool]
            world = tell(
                SETTINGS[place],
                CHALLENGES[challenge],
                chosen_tool,
                params.child_name,
                params.child_type,
                params.friend_name,
                params.friend_type,
                params.parent_type,
            )
            samples.append(StorySample(
                params=params,
                story=world.render(),
                prompts=generation_prompts(world),
                story_qa=story_qa(world),
                world_qa=world_knowledge_qa(world),
                world=world,
            ))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.child_name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
