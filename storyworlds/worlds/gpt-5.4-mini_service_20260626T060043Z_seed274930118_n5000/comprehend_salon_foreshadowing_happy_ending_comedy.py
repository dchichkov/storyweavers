#!/usr/bin/env python3
"""
Standalone storyworld: a comedy about a child who does not quite comprehend the
salon at first, with light foreshadowing and a happy ending.

This world is intentionally small and constraint-driven:
- One child, one parent, one salon visit, one harmless mishap, one fix.
- The parent foreshadows the surprise with clues in the room.
- The child eventually comprehends the plan, and the ending is cheerful.

The story engine models physical meters and emotional memes, then narrates from
state changes instead of swapping nouns in a frozen paragraph.
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "confusion": 0.0, "comprehension": 0.0, "amusement": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the salon"
    sounds: str = "the buzz of a dryer and the snip-snip of scissors"
    smells: str = "shampoo and warm towels"


@dataclass
class StoryParams:
    name: str
    child_type: str
    parent_type: str
    item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.events: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CHILD_NAMES = ["Milo", "Nina", "Toby", "Luna", "Pippa", "Ezra"]
CHILD_TRAITS = ["curious", "silly", "bright-eyed", "chatty", "bouncy", "playful"]

ITEMS = {
    "haircut": {
        "label": "haircut",
        "phrase": "a tidy haircut",
        "mess": "snip",
        "fix": "comb",
    },
    "braids": {
        "label": "braids",
        "phrase": "neat braids",
        "mess": "tangle",
        "fix": "spray bottle",
    },
    "bangs": {
        "label": "bangs",
        "phrase": "soft bangs",
        "mess": "frizz",
        "fix": "clip",
    },
}

SETTING = Setting()


# ---------------------------------------------------------------------------
# Reasonable story gate
# ---------------------------------------------------------------------------

def reasonableness_check(params: StoryParams) -> None:
    if params.item not in ITEMS:
        raise StoryError("Unknown salon item.")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("Child type must be girl or boy.")
    if params.parent_type not in {"mother", "father"}:
        raise StoryError("Parent type must be mother or father.")


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.meters.keys() if False) if False else ''}".strip()
    )


def start_scene(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"{child.id} and {parent.pronoun('possessive')} {parent.type} went to {world.setting.place}, "
        f"where there was {world.setting.sounds} and the smell of {world.setting.smells}."
    )


def foreshadow(world: World, child: Entity, item: Entity) -> None:
    world.say(
        f"At the front desk, a shiny sign showed a brush, a comb, and a small spray bottle."
    )
    world.say(
        f"{child.id} stared at the tools and did not quite comprehend why the grown-ups were smiling."
    )
    world.facts["foreshadowed_fix"] = item.label


def wants_change(world: World, child: Entity, item: Entity) -> None:
    child.memes["confusion"] += 1
    world.say(
        f"{child.id} wanted {item.phrase}, but {child.pronoun('possessive')} hair felt like a funny nest."
    )


def mistaken_mess(world: World, child: Entity, item: Entity) -> None:
    child.meters["mess"] += 1
    child.memes["amusement"] += 1
    world.say(
        f"When the cape went on, {child.id} giggled so hard that the stylist said the bangs were trying to do comedy."
    )
    world.say(
        f"A lock slipped, then another, and the room looked as if a cloud of tiny hairs had sneezed."
    )


def warning(world: World, parent: Entity, child: Entity, item: Entity) -> None:
    world.say(
        f"{parent.id} pointed at the comb and said, \"First the trim, then the tidy-up. You'll understand in a minute.\""
    )


def comprehend_turn(world: World, child: Entity, item: Entity) -> None:
    child.memes["comprehension"] += 1
    child.memes["confusion"] = 0.0
    world.say(
        f"Then {child.id} comprehended the joke: the salon was not a place for looking serious the whole time."
    )
    world.say(
        f"{child.id} laughed so hard that even the dryer sounded like it was joining in."
    )


def fix_and_finish(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.meters["mess"] = 0.0
    child.meters["tidy"] += 1
    child.memes["joy"] += 1
    parent.memes["joy"] = parent.memes.get("joy", 0.0) + 1
    world.say(
        f"The stylist used the {ITEMS[item.id]['fix']} and a careful brush, and soon {child.id}'s hair looked neat again."
    )
    world.say(
        f"{child.id} grinned in the mirror, {parent.pronoun('subject')} laughed, and the little salon visit ended as a happy ending with tidy hair and bigger smiles."
    )


def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    world = World(SETTING)

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.child_type,
            meters={"mess": 0.0, "tidy": 0.0},
            memes={"joy": 0.0, "confusion": 0.0, "comprehension": 0.0, "amusement": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=params.parent_type,
            label="parent",
            meters={"mess": 0.0, "tidy": 0.0},
            memes={"joy": 0.0, "confusion": 0.0, "comprehension": 0.0, "amusement": 0.0},
        )
    )
    item_cfg = ITEMS[params.item]
    item = world.add(
        Entity(
            id=params.item,
            kind="thing",
            type="salon-item",
            label=item_cfg["label"],
            phrase=item_cfg["phrase"],
            owner=child.id,
        )
    )

    world.facts.update(child=child, parent=parent, item=item, item_cfg=item_cfg)

    world.say(
        f"{child.id} was a little {params.child_type} named {params.name}, and {child.pronoun('subject')} loved asking questions."
    )
    world.say(
        f"{child.id} and the {parent.type} went to the salon for {item.phrase}."
    )
    world.para()

    start_scene(world, child, parent)
    foreshadow(world, child, item)
    wants_change(world, child, item)
    warning(world, parent, child, item)
    mistaken_mess(world, child, item)
    world.para()
    comprehend_turn(world, child, item)
    fix_and_finish(world, child, parent, item)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item_cfg = f["item_cfg"]
    return [
        f"Write a funny story for young children about {child.id} going to a salon and finally comprehending what the tools are for.",
        f"Tell a comedy with foreshadowing, a salon, and a happy ending where {child.id} learns why {item_cfg['label']} matters.",
        f"Write a short child-friendly salon story that includes a clue, a joke, and a neat ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    item_cfg = f["item_cfg"]
    return [
        QAItem(
            question=f"Where did {child.id} go with the {parent.type}?",
            answer=f"{child.id} went to the salon with {parent.id}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the fix in the salon?",
            answer="A shiny sign with a brush, a comb, and a spray bottle foreshadowed the tidy-up.",
        ),
        QAItem(
            question=f"When did {child.id} comprehend what was happening?",
            answer=f"{child.id} comprehended it after the silly haircut moment and before the tidy finish.",
        ),
        QAItem(
            question=f"What helped finish the {item_cfg['label']} story well?",
            answer=f"The {item_cfg['fix']} and careful brushing helped end the salon visit with a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salon?",
            answer="A salon is a place where people go to have hair cut, brushed, braided, or styled.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives small clues early on about what will happen later.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling glad.",
        ),
        QAItem(
            question="Why do people use a comb?",
            answer="People use a comb to smooth hair and help it lie neatly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A salon story is reasonable when a child visits the salon and a fix tool exists.
salon_story(C, I) :- child(C), item(I), fix(I, _).

% Foreshadowing is represented by a clue near the tools.
foreshadowing(clue) :- tool(brush), tool(comb), tool(spray).

% The happy ending happens when the mess is cleared and joy rises.
happy_ending(C) :- child(C), cleared(C), joy(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [
        asp.fact("child", "child"),
        asp.fact("parent", "parent"),
    ]
    for item_id, cfg in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("fix", item_id, cfg["fix"]))
    lines.extend(
        [
            asp.fact("tool", "brush"),
            asp.fact("tool", "comb"),
            asp.fact("tool", "spray"),
            asp.fact("cleared", "child"),
            asp.fact("joy", "child"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show salon_story/2.\n#show foreshadowing/1.\n#show happy_ending/1."))
    shown = set(asp.atoms(model, "salon_story")) | set(asp.atoms(model, "foreshadowing")) | set(asp.atoms(model, "happy_ending"))
    expected = {("child", "haircut"), ("clue",), ("child",)}
    if shown == expected:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH:", sorted(shown), "expected", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy salon storyworld with foreshadowing and a happy ending.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--item", choices=sorted(ITEMS))
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    name = args.name or rng.choice(CHILD_NAMES)
    item = args.item or rng.choice(sorted(ITEMS))
    return StoryParams(name=name, child_type=child_type, parent_type=parent_type, item=item)


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
        print("\n--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(eid, ent.meters, ent.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show salon_story/2.\n#show foreshadowing/1.\n#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show salon_story/2."))
        print(sorted(set(asp.atoms(model, "salon_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Milo", child_type="boy", parent_type="mother", item="haircut"),
            StoryParams(name="Nina", child_type="girl", parent_type="father", item="braids"),
            StoryParams(name="Toby", child_type="boy", parent_type="father", item="bangs"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
