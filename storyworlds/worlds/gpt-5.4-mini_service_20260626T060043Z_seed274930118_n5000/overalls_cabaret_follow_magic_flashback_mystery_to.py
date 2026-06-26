#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/overalls_cabaret_follow_magic_flashback_mystery_to.py
===============================================================================================================================

A small nursery-rhyme storyworld about a child in overalls, a cabaret stage,
a wish to follow the music, a little magic, and a flashback mystery to solve.

Premise:
- A child in favorite overalls loves to follow a line of sparkling music.
- At the cabaret, a stage trick makes a clue vanish.
- A flashback helps the child remember where the missing clue went.
- The mystery is solved with a gentle magical choice, not with force.

World model:
- Physical meters track things like sparkle, hush, dust, and foundness.
- Emotional memes track wonder, worry, courage, and relief.
- The story is generated from simulated state, not from a frozen template.

The tone aims for nursery-rhyme softness: small, concrete images, repeated
rhythms, and a warm ending that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sparkle": 0.0, "dust": 0.0, "foundness": 0.0}
        if not self.memes:
            self.memes = {"wonder": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0}

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
    place: str = "the cabaret"
    indoor: bool = True
    allows: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    protect: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    reveals: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_seen: bool = False
        self.clue_hidden: bool = False
        self.clue_revealed: bool = False

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
        clone.paragraphs = [[]]
        clone.flashback_seen = self.flashback_seen
        clone.clue_hidden = self.clue_hidden
        clone.clue_revealed = self.clue_revealed
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_magic_glow(world: World) -> list[str]:
    out = []
    if not world.clue_hidden or world.clue_revealed:
        return out
    if ("magic", "glow") in world.fired:
        return out
    world.fired.add(("magic", "glow"))
    for e in world.characters():
        e.meters["sparkle"] += 1
        e.memes["wonder"] += 1
    out.append("The stage gave a tiny twinkle-tap, and the air felt full of wonder.")
    return out


def _r_flashback_remember(world: World) -> list[str]:
    out = []
    if not world.flashback_seen or world.clue_revealed:
        return out
    if ("flashback", "remember") in world.fired:
        return out
    world.fired.add(("flashback", "remember"))
    clue = world.get("clue")
    clue.meters["foundness"] += 1
    out.append("In the flashback, the child remembered the clue hid behind a velvet curtain.")
    return out


def _r_mystery_solve(world: World) -> list[str]:
    out = []
    if world.clue_revealed:
        return out
    clue = world.get("clue")
    if clue.meters["foundness"] < THRESHOLD:
        return out
    if ("mystery", "solve") in world.fired:
        return out
    world.fired.add(("mystery", "solve"))
    world.clue_revealed = True
    for e in world.characters():
        e.meters["sparkle"] += 1
        e.memes["relief"] += 1
        e.memes["worry"] = 0.0
    out.append("The missing note was found, and the little mystery was solved at last.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("magic_glow", _r_magic_glow),
    Rule("flashback_remember", _r_flashback_remember),
    Rule("mystery_solve", _r_mystery_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_follow(world: World, actor: Entity) -> None:
    actor.meters["sparkle"] += 1
    actor.memes["courage"] += 1
    world.say(f"{actor.id} followed the shining tune on tiptoe, soft as a feather.")
    propagate(world, narrate=True)


def _make_flashback(world: World, actor: Entity) -> None:
    world.flashback_seen = True
    actor.memes["wonder"] += 1
    world.say(f"Then came a flashback, small and clear, like moonlight in a spoon.")
    propagate(world, narrate=True)


def _hide_clue(world: World) -> None:
    world.clue_hidden = True
    clue = world.get("clue")
    clue.meters["foundness"] = 0.0
    world.say("A mystery trick made the clue slip away behind the curtain.")
    propagate(world, narrate=True)


def tell(world: World, hero: Entity, parent: Entity, clue: Entity, tool: Entity) -> World:
    world.say(f"{hero.id} was a little {hero.type} in snug overalls, bright and neat.")
    world.say(f"{hero.id} loved to follow music, one step, two steps, under the cabaret lights.")
    world.say(f"{parent.id} had brought {hero.pronoun('object')} to the cabaret to hear the cheerful show.")

    world.para()
    world.say("But oh, the stage went hush, and a tiny clue went missing from sight.")
    world.say(f"{hero.id} worried a bit, for the missing clue was tied to the night's surprise.")
    _hide_clue(world)

    world.para()
    world.say(f"Then {tool.label} began to shimmer, as if it knew a friendly way to help.")
    world.say(f"{hero.id} chose to follow the glimmer, not rush, not fuss, just follow.")
    _do_follow(world, hero)

    world.para()
    _make_flashback(world, hero)
    world.say(f"In that flashback, {hero.id} remembered the clue hid where velvet shadows met.")
    clue.meters["foundness"] += 1
    tool.meters["foundness"] += 1
    propagate(world, narrate=True)

    world.para()
    if world.clue_revealed:
        world.say(f"{hero.id} lifted the curtain, and there was the clue, snug and safe.")
        world.say(f"{parent.id} clapped softly, and the cabaret sparkled like a row of little stars.")
    else:
        world.say(f"{hero.id} looked and looked, but the clue was still shy and hidden.")

    world.facts.update(hero=hero, parent=parent, clue=clue, tool=tool)
    return world


SETTING = Setting(place="the cabaret", indoor=True, allows={"follow", "magic", "flashback", "mystery"})
ITEMS = {
    "overalls": Item(
        id="overalls",
        label="overalls",
        phrase="striped little overalls",
        region="legs",
        plural=True,
        protect={"dust"},
    ),
    "clue": Item(
        id="clue",
        label="clue",
        phrase="a silver clue-note",
        region="torso",
        protect=set(),
    ),
}
MAGIC_TOOLS = {
    "lantern": MagicTool(
        id="lantern",
        label="a moon lantern",
        phrase="a moon lantern with a soft glow",
        helps={"magic", "follow"},
        reveals={"clue"},
    ),
}
HERO_NAMES = ["Mina", "Pip", "Toby", "Nell", "Juno", "Lulu"]
PARENT_NAMES = ["Mama", "Papa", "Auntie", "Uncle"]
TRAITS = ["spry", "cheerful", "curious", "bright", "gentle"]


@dataclass
class StoryParams:
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld of overalls, cabaret, follow, magic, flashback, and a mystery to solve.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    return StoryParams(
        name=args.name or rng.choice(HERO_NAMES),
        parent=args.parent or rng.choice(PARENT_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a nursery-rhyme story about {hero.id} in overalls at the cabaret, following a glowing clue.",
        "Tell a gentle tale with magic, a flashback, and a mystery to solve.",
        "Write a short child-friendly story where someone follows a tune and finds what was hidden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    clue: Entity = f["clue"]
    return [
        QAItem(
            question=f"Who followed the shining tune at the cabaret?",
            answer=f"{hero.id} followed the shining tune at the cabaret in {hero.pronoun('possessive')} little overalls.",
        ),
        QAItem(
            question="What kind of problem needed to be solved?",
            answer="A small mystery needed to be solved because a clue went missing behind the curtain.",
        ),
        QAItem(
            question=f"What helped {hero.id} remember where the clue was hidden?",
            answer=f"A flashback helped {hero.id} remember that the clue hid behind the velvet curtain.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The missing clue was found, and the cabaret felt bright and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cabaret?",
            answer="A cabaret is a place where people perform music, dance, and cheerful little shows.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier, so someone can remember an old clue or feeling.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find out what happened or where something went by using clues and careful thinking.",
        ),
        QAItem(
            question="What are overalls?",
            answer="Overalls are clothes with straps and a front piece, often worn for play or work.",
        ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  flashback_seen={world.flashback_seen} clue_hidden={world.clue_hidden} clue_revealed={world.clue_revealed}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "cabaret"))
    lines.append(asp.fact("allows", "cabaret", "follow"))
    lines.append(asp.fact("allows", "cabaret", "magic"))
    lines.append(asp.fact("allows", "cabaret", "flashback"))
    lines.append(asp.fact("allows", "cabaret", "mystery"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worn_on", iid, item.region))
    for mid, tool in MAGIC_TOOLS.items():
        lines.append(asp.fact("magic", mid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", mid, h))
        for r in sorted(tool.reveals):
            lines.append(asp.fact("reveals", mid, r))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P) :- setting(P), allows(P,follow), allows(P,magic), allows(P,flashback), allows(P,mystery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"clingo unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("cabaret",)}
    if asp_set == py_set:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py_set))
    return 1


def valid_story_combo() -> bool:
    return True


CURATED = [
    StoryParams(name="Mina", parent="Mama", trait="curious"),
    StoryParams(name="Pip", parent="Papa", trait="cheerful"),
    StoryParams(name="Nell", parent="Auntie", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Nell", "Lulu"} else "boy"))
    hero.traits = ["little", params.trait]
    parent = world.add(Entity(id=params.parent, kind="character", type="mother" if params.parent in {"Mama", "Auntie"} else "father"))
    overalls = world.add(Entity(id="overalls", type="overalls", label="overalls", phrase="striped little overalls", owner=hero.id, worn_by=hero.id))
    clue = world.add(Entity(id="clue", type="clue", label="clue", phrase="a silver clue-note", owner="cabaret"))
    tool = world.add(Entity(id="lantern", type="magic", label="moon lantern", phrase="a moon lantern", owner=hero.id))
    tool.meters["foundness"] = 0.0

    tell(world, hero, parent, clue, tool)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story shape: cabaret with follow, magic, flashback, mystery.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
