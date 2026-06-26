#!/usr/bin/env python3
"""
Storyworld: emphasize_expensive_transformation_detective_story
==============================================================

A small, constraint-checked detective story world where a careful investigator
chases a clue about an expensive transformation.

Premise
-------
A clever detective in a rainy city is asked to find out why an expensive silver
locket keeps changing shape. The case moves from a tidy office to a shadowy
workshop, where the detective must choose the right method, follow the clues,
and expose the trick behind the transformation.

World shape
-----------
- Typed entities with physical meters and emotional memes.
- A simple causal simulation: clues raise suspicion, tools reveal hidden signs,
  and the final reveal can transform the object's appearance.
- The story is always driven by state changes, not a frozen paragraph.

This world includes the seed words "emphasize" and "expensive", and the core
feature is "Transformation".
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    cost: str
    tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reveals: set[str]
    costs: set[str]
    action: str


@dataclass
class MysteryItem:
    label: str
    phrase: str
    initial_form: str
    transformed_form: str
    mystery: str
    expensive: bool = True


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    name: str
    gender: str
    assistant: str
    seed: Optional[int] = None


SETTINGS = {
    "office": Setting(place="the detective office", mood="quiet", affords={"interview", "search"}),
    "alley": Setting(place="the rain-slick alley", mood="shadowy", affords={"search", "chase"}),
    "workshop": Setting(place="the clockmaker's workshop", mood="dusty", affords={"search", "reveal"}),
}

CLUES = {
    "ticket": Clue(
        id="ticket",
        label="a train ticket stub",
        phrase="a torn ticket stub",
        reveals="the workshop",
        cost="could only mean someone had traveled with care",
        tag="travel",
    ),
    "gloves": Clue(
        id="gloves",
        label="a pair of white gloves",
        phrase="a thin pair of white gloves",
        reveals="a hidden drawer",
        cost="pointed to a careful hand",
        tag="careful",
    ),
    "receipt": Clue(
        id="receipt",
        label="an expensive receipt",
        phrase="an expensive receipt with a gold stamp",
        reveals="the silver locket",
        cost="showed the item was too valuable to lose",
        tag="expensive",
    ),
    "mirror": Clue(
        id="mirror",
        label="a cracked mirror shard",
        phrase="a cracked mirror shard",
        reveals="the transformation trick",
        cost="caught a strange glint",
        tag="reflection",
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        phrase="a magnifying glass",
        reveals={"reflection", "careful"},
        costs={"hidden"},
        action="inspect",
    ),
    "lamp": Tool(
        id="lamp",
        label="a bright lamp",
        phrase="a bright lamp",
        reveals={"hidden", "travel"},
        costs={"shadow"},
        action="shine",
    ),
    "ledger": Tool(
        id="ledger",
        label="a case ledger",
        phrase="a case ledger",
        reveals={"expensive"},
        costs={"falsehood"},
        action="compare",
    ),
}

MYSTERY = MysteryItem(
    label="silver locket",
    phrase="an expensive silver locket",
    initial_form="round and plain",
    transformed_form="square, engraved, and open",
    mystery="transformation",
    expensive=True,
)

NAMES = ["Iris", "Mina", "Noel", "Ada", "Clara", "Jules", "Ruth", "Eli"]
ASSISTANTS = ["partner", "driver", "clerk", "neighbor"]
GENDERS = ["girl", "boy"]


class Detective(Entity):
    pass


def clue_by_id(cid: str) -> Clue:
    if cid not in CLUES:
        raise StoryError(f"Unknown clue: {cid}")
    return CLUES[cid]


def tool_by_id(tid: str) -> Tool:
    if tid not in TOOLS:
        raise StoryError(f"Unknown tool: {tid}")
    return TOOLS[tid]


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    detective = world.add(Detective(
        id=params.name,
        kind="character",
        type=params.gender,
        label="detective",
        meters={"focus": 0.0, "progress": 0.0, "suspicion": 0.0, "reveal": 0.0},
        memes={"confidence": 0.0, "curiosity": 1.0, "resolve": 0.0},
    ))
    assistant = world.add(Entity(
        id="assistant",
        kind="character",
        type="person",
        label=params.assistant,
        meters={"help": 0.0},
        memes={"worry": 0.0, "trust": 1.0},
    ))
    item = world.add(Entity(
        id="item",
        type="object",
        label=MYSTERY.label,
        phrase=MYSTERY.phrase,
        owner=detective.id,
        meters={"mystery": 1.0, "transform": 0.0, "value": 1.0},
        memes={"importance": 1.0},
    ))
    world.facts.update(
        detective=detective,
        assistant=assistant,
        item=item,
        clue=clue_by_id(params.clue),
        tool=tool_by_id(params.tool),
        params=params,
    )
    return world


def introduce(world: World) -> None:
    d: Entity = world.facts["detective"]
    item: Entity = world.facts["item"]
    world.say(
        f"{d.id} was the kind of detective who noticed tiny details and knew how to "
        f"emphasize the one clue that mattered."
    )
    world.say(
        f"One rainy night, {d.id} took a case involving {item.phrase}, and everyone said "
        f"it was too expensive to lose."
    )


def search(world: World) -> None:
    d: Entity = world.facts["detective"]
    clue: Clue = world.facts["clue"]
    tool: Tool = world.facts["tool"]
    item: Entity = world.facts["item"]

    d.meters["focus"] += 1
    d.meters["progress"] += 1
    d.memes["curiosity"] += 1

    world.say(
        f"{d.id} went to {world.setting.place} with {tool.phrase} and looked for {clue.phrase}."
    )
    world.say(
        f"The place felt {world.setting.mood}, and the detective knew the case would only "
        f"move forward if {tool.action} was used carefully."
    )

    if clue.tag in tool.reveals:
        d.meters["suspicion"] += 1
        d.meters["reveal"] += 1
        item.meters["transform"] += 1
        world.say(
            f"The tool caught what the eyes almost missed: {clue.cost}, and that pointed "
            f"straight toward {clue.reveals}."
        )


def reveal(world: World) -> None:
    d: Entity = world.facts["detective"]
    assistant: Entity = world.facts["assistant"]
    clue: Clue = world.facts["clue"]
    item: Entity = world.facts["item"]

    if item.meters["transform"] < THRESHOLD:
        return

    d.memes["confidence"] += 1
    d.memes["resolve"] += 1
    assistant.memes["trust"] += 1

    world.say(
        f"At last, {d.id} found the trick: the locket had a hidden hinge, so it could "
        f"change from {MYSTERY.initial_form} to {MYSTERY.transformed_form}."
    )
    world.say(
        f"It was not magic at all, just a clever transformation hidden behind a polished "
        f"surface."
    )
    world.say(
        f"{assistant.label.capitalize()} let out a breath of relief, because the expensive "
        f"piece was safe once the secret was known."
    )
    world.say(
        f"{d.id} closed the case by placing the locket back in its box, where it stayed "
        f"still and shining."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    search(world)
    world.para()
    reveal(world)
    return world


def world_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    clue: Clue = world.facts["clue"]
    tool: Tool = world.facts["tool"]
    return [
        f'Write a short detective story that emphasizes a clue about an expensive transformation.',
        f"Tell a child-friendly mystery where {p.name} uses {tool.label} to follow {clue.label} and solve a case.",
        f"Write a noir-flavored story in simple language about a detective, a shiny object, and a secret change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    d: Entity = world.facts["detective"]
    clue: Clue = world.facts["clue"]
    tool: Tool = world.facts["tool"]
    item: Entity = world.facts["item"]
    return [
        QAItem(
            question=f"What kind of story is this about {d.id}?",
            answer=f"It is a detective story about {d.id} solving a case with a clue and a careful search.",
        ),
        QAItem(
            question=f"Why did the detective care so much about the locket?",
            answer=f"Because it was an expensive silver locket and the case depended on figuring out what changed it.",
        ),
        QAItem(
            question=f"What tool helped {d.id} notice the clue at {world.setting.place}?",
            answer=f"{tool.label.capitalize()} helped {d.id} notice the clue and follow the hidden detail.",
        ),
        QAItem(
            question=f"What was the locket's transformation?",
            answer=f"It changed from {MYSTERY.initial_form} to {MYSTERY.transformed_form} once the hinge trick was understood.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and solves mysteries.",
        ),
        QAItem(
            question="What is a magnifying glass for?",
            answer="A magnifying glass helps you look closely at small details.",
        ),
        QAItem(
            question="What does expensive mean?",
            answer="Expensive means something costs a lot of money.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with an expensive transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--assistant", choices=ASSISTANTS)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    clue = args.clue or rng.choice(list(CLUES.keys()))
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    assistant = args.assistant or rng.choice(ASSISTANTS)

    if clue == "receipt" and tool == "ledger":
        pass
    elif clue == "mirror" and tool == "magnifier":
        pass
    elif clue == "ticket" and tool == "lamp":
        pass
    elif clue == "gloves" and tool in {"magnifier", "lamp"}:
        pass
    else:
        if args.clue and args.tool:
            raise StoryError("That clue/tool pair does not lead to a clean detective reveal.")
    return StoryParams(place=place, clue=clue, tool=tool, name=name, gender=gender, assistant=assistant)


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
        print(world_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
clue(tag).
tool(tag).

matches(C,T) :- clue(C), tool(T), usable(T,C).
case_ready(P,C,T) :- place(P), clue(C), tool(T), affords(P,search), matches(C,T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("usable", "magnifier", c.tag) if c.tag in {"reflection", "careful"} else "")
        lines.append(asp.fact("usable", "lamp", c.tag) if c.tag in {"travel", "hidden"} else "")
        lines.append(asp.fact("usable", "ledger", c.tag) if c.tag in {"expensive"} else "")
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                if (c == "receipt" and t == "ledger") or (c == "mirror" and t == "magnifier") or (c == "ticket" and t == "lamp") or (c == "gloves" and t in {"magnifier", "lamp"}):
                    combos.append((p, c, t))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show case_ready/3."))
    return sorted(set(asp.atoms(model, "case_ready")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="office", clue="receipt", tool="ledger", name="Iris", gender="girl", assistant="partner"),
    StoryParams(place="alley", clue="mirror", tool="magnifier", name="Noel", gender="boy", assistant="driver"),
    StoryParams(place="workshop", clue="ticket", tool="lamp", name="Ada", gender="girl", assistant="clerk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show case_ready/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show case_ready/3."))
        print(sorted(set(asp.atoms(model, "case_ready"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i - 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
