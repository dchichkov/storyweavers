#!/usr/bin/env python3
"""
Story world: a small slice-of-life rhyme quest with a gag and a creaky obstacle.

A child wants to finish a gentle rhyme quest: collect a few rhyme cards around a cozy home,
share a silly gag with a grown-up, and solve the one squeaky, creaky problem that gets in the way.
The simulated state tracks the child, the grown-up, the quest, the annoying sound, and the mood
change that happens when they find a calm, practical fix.
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
# Domain model
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
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        for k in ("noise", "mess", "use", "distance", "time"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "pride", "curiosity", "laugh", "calm", "frustration"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    route: list[str]
    clue_word: str
    rhyme_word: str
    obstacle: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gag:
    id: str
    line: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"rhyme", "gag", "quest"}),
    "hallway": Setting("the hallway", True, {"rhyme", "gag", "quest"}),
    "garden": Setting("the garden", False, {"rhyme", "gag", "quest"}),
}

QUESTS = {
    "rhyme_cards": Quest(
        id="rhyme_cards",
        title="rhyme cards",
        goal="collect three rhyme cards",
        route=["table", "door", "bench"],
        clue_word="rhyme",
        rhyme_word="time",
        obstacle="a creaky step",
        resolution="walk softly and use the side step",
        tags={"rhyme", "quest", "creak"},
    ),
    "spoon_fetch": Quest(
        id="spoon_fetch",
        title="the spoon fetch",
        goal="find the silver spoon for tea",
        route=["sink", "drawer", "shelf"],
        clue_word="spoon",
        rhyme_word="moon",
        obstacle="a creaky drawer",
        resolution="open the drawer slowly and hold the handle with two hands",
        tags={"quest", "creak"},
    ),
    "note_hunt": Quest(
        id="note_hunt",
        title="the note hunt",
        goal="find the missing note with the last rhyme",
        route=["rug", "bookcase", "window"],
        clue_word="note",
        rhyme_word="boat",
        obstacle="a creaky floorboard",
        resolution="step over the board and follow the quiet path",
        tags={"rhyme", "quest", "creak"},
    ),
}

GAGS = {
    "banana_joke": Gag(
        id="banana_joke",
        line="the child told a silly gag about a banana in pajamas",
        effect="laugh",
        tags={"gag"},
    ),
    "shoe_joke": Gag(
        id="shoe_joke",
        line="the child whispered a gag about a shoe that wanted to be a boat",
        effect="laugh",
        tags={"gag"},
    ),
    "knock_knock": Gag(
        id="knock_knock",
        line="the child gave a tiny knock-knock gag that made the room feel lighter",
        effect="laugh",
        tags={"gag"},
    ),
}

TOOLS = {
    "soft_steps": Tool(
        id="soft_steps",
        label="soft slippers",
        phrase="a pair of soft slippers",
        helps={"creak"},
        covers={"feet"},
    ),
    "oil_can": Tool(
        id="oil_can",
        label="a little oil can",
        phrase="a little oil can for the hinge",
        helps={"creak"},
    ),
    "basket": Tool(
        id="basket",
        label="a basket",
        phrase="a wicker basket for the cards",
        helps={"quest"},
    ),
}

CHILDREN = ["Mina", "Owen", "Poppy", "Eli", "Nora", "Ada", "Theo", "June"]
GROWNUPS = ["mom", "dad", "grandma", "grandpa"]


# ---------------------------------------------------------------------------
# Params and parser
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    gag: str
    name: str
    grownup: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life rhyme quest with a gag and a creak.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gag", choices=GAGS)
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=GROWNUPS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for g in GAGS:
                combos.append((s, q, g))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if args.gag and args.gag not in GAGS:
        raise StoryError("Unknown gag.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.gag is None or c[2] == args.gag)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, gag = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILDREN)
    grownup = args.grownup or rng.choice(GROWNUPS)
    return StoryParams(setting=setting, quest=quest, gag=gag, name=name, grownup=grownup)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _start(world: World, child: Entity, grownup: Entity, quest: Quest, gag: Gag, basket: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(f"{child.id} was having a quiet afternoon in {world.setting.place}.")
    world.say(f"{child.id} wanted to finish a little {quest.title} and carried {basket.phrase}.")
    world.say(f"Before they started, {child.id} told {gag.line}, and {grownup.id} smiled.")


def _creak(world: World, child: Entity, quest: Quest) -> None:
    child.memes["worry"] += 1
    child.meters["noise"] += 1
    world.say(f"But on the way, {quest.obstacle} gave a long creak.")
    world.say(f"{child.id} froze for a moment, because the sound felt too loud for such a calm day.")


def _predict(world: World, quest: Quest) -> dict:
    sim = world.copy()
    child = next(e for e in sim.entities.values() if e.kind == "character" and e.type in {"girl", "boy"})
    child.meters["noise"] += 1
    return {"creak": True, "resolved": quest.id in QUESTS}


def _fix(world: World, child: Entity, grownup: Entity, quest: Quest, tool: Tool) -> None:
    child.memes["frustration"] += 0.0
    child.memes["calm"] += 1
    grownup.memes["calm"] += 1
    world.say(f"{grownup.id} found {tool.phrase} and showed {child.id} how to use it.")
    world.say(f"They chose to {quest.resolution}, so the creak did not spoil the outing.")
    world.say(f"{child.id} finished the quest, collected the last card, and felt proud to solve it gently.")


def tell(setting: Setting, quest: Quest, gag: Gag, child_name: str, grownup_role: str) -> World:
    world = World(setting)
    child_type = "girl" if child_name in {"Mina", "Poppy", "Nora", "Ada", "June"} else "boy"
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    grownup = world.add(Entity(id=grownup_role, kind="character", type=grownup_role))
    basket = world.add(Entity(id="basket", label="basket", phrase="a small basket", owner=child.id))
    tool = TOOLS["soft_steps"] if "creak" in quest.tags else TOOLS["basket"]

    _start(world, child, grownup, quest, gag, basket)
    world.para()
    _creak(world, child, quest)
    world.say(f"{child.id} wanted to keep going, but {grownup.id} thought about the noise and the slow pace.")
    world.para()
    _fix(world, child, grownup, quest, tool)

    world.facts.update(child=child, grownup=grownup, quest=quest, gag=gag, tool=tool)
    return world


# ---------------------------------------------------------------------------
# Prose and QA
# ---------------------------------------------------------------------------

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    grownup: Entity = f["grownup"]
    quest: Quest = f["quest"]
    gag: Gag = f["gag"]
    return [
        QAItem(
            question=f"What did {child.id} want to finish that afternoon?",
            answer=f"{child.id} wanted to finish the little {quest.title}, which meant {quest.goal}.",
        ),
        QAItem(
            question=f"What made the day feel lighter before the problem showed up?",
            answer=f"{child.id} told a silly gag, and {grownup.id} smiled before the creaky problem got in the way.",
        ),
        QAItem(
            question=f"What was the annoying problem in the story?",
            answer=f"The annoying problem was {quest.obstacle}, which gave a creak and made {child.id} pause.",
        ),
        QAItem(
            question=f"How did they solve the problem without rushing?",
            answer=f"They used a calm, careful fix: {quest.resolution}. That kept the day peaceful and let the quest continue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gag?",
            answer="A gag is a silly joke or funny line that is meant to make someone laugh.",
        ),
        QAItem(
            question="What does creak usually mean?",
            answer="A creak is a squeaky sound, often made by a door, floorboard, or hinge when it moves.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a little mission or search for something you want to find or finish.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme means words sound alike at the end, like time and rhyme.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    quest: Quest = f["quest"]
    return [
        f"Write a short slice-of-life story about {child.id} doing a quiet {quest.title} with a gag and a creak.",
        f"Tell a child-friendly story where a rhyme quest gets interrupted by a creaky sound, then solved gently.",
        f"Write a cozy story that includes the words gag, creak, rhyme, and quest, and ends with a calm little win.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.kind:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(kitchen). setting(hallway). setting(garden).
quest(rhyme_cards). quest(spoon_fetch). quest(note_hunt).
gag(banana_joke). gag(shoe_joke). gag(knock_knock).

valid(S,Q,G) :- setting(S), quest(Q), gag(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for g in GAGS:
        lines.append(asp.fact("gag", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], GAGS[params.gag], params.name, params.grownup)
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


CURATED = [
    StoryParams(setting="kitchen", quest="rhyme_cards", gag="banana_joke", name="Mina", grownup="mom"),
    StoryParams(setting="hallway", quest="spoon_fetch", gag="shoe_joke", name="Owen", grownup="grandma"),
    StoryParams(setting="garden", quest="note_hunt", gag="knock_knock", name="June", grownup="dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
