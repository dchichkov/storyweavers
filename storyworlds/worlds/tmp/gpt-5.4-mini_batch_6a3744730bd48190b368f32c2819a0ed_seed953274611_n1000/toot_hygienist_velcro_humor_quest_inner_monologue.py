#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/toot_hygienist_velcro_humor_quest_inner_monologue.py
====================================================================================

A tiny fairy-tale storyworld about a toot, a hygienist, and a Velcro quest.

Premise:
- A small castle has a squeaky problem.
- A young quester needs a magical fix for a loose satchel strap.
- A kind hygienist and a funny inner-monologue beat guide the turn.
- The ending proves the quest changed the world: clean teeth, a steady strap,
  and a relieved little laugh.

This world is deliberately small and classical: typed entities with physical
meters and emotional memes, state-driven prose, a Python reasonableness gate,
and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "lady"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class CharacterSpec:
    id: str
    type: str
    title: str
    pronoun_hint: str = ""


@dataclass
class QuestSpec:
    id: str
    start: str
    goal: str
    tool: str
    humor_line: str
    monologue_line: str
    success_line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolSpec:
    id: str
    label: str
    phrase: str
    works: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    hero: str
    hero_type: str
    hygienist: str
    hygienist_type: str
    tool: str
    toot_style: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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


QUESTS = {
    "tooth_lantern": QuestSpec(
        id="tooth_lantern",
        start="the little castle had gone dim and pearly",
        goal="find a bright tooth-lantern smile",
        tool="toot",
        humor_line="A toot popped out of nowhere like a mischievous trumpeter under a bridge.",
        monologue_line="The child thought, Perhaps a clean smile is a brave kind of magic.",
        success_line="the hygienist polished away the sugar and the grin shone like a lantern",
        fail_line="the sugar stayed stuck like sticky barn moss",
        tags={"toot", "hygienist", "quest", "inner_monologue", "humor"},
    )
}

TOOLS = {
    "velcro": ToolSpec(
        id="velcro",
        label="Velcro",
        phrase="a strip of Velcro",
        works=True,
        tags={"velcro", "quest"},
    ),
    "ribbon": ToolSpec(
        id="ribbon",
        label="ribbon",
        phrase="a ribbon",
        works=False,
        tags={"quest"},
    ),
}

CHARACTERS = {
    "child": CharacterSpec(id="Pip", type="boy", title="young quester"),
    "hygienist": CharacterSpec(id="Hush", type="queen", title="hygienist"),
    "child2": CharacterSpec(id="Mina", type="girl", title="young quester"),
}

CURATED = [
    StoryParams(quest="tooth_lantern", hero="Pip", hero_type="boy", hygienist="Hush",
                hygienist_type="queen", tool="velcro", toot_style="tiny", seed=7),
    StoryParams(quest="tooth_lantern", hero="Mina", hero_type="girl", hygienist="Hush",
                hygienist_type="queen", tool="velcro", toot_style="giggle", seed=11),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for qid, q in QUESTS.items():
        for tool_id, tool in TOOLS.items():
            for c in CHARACTERS.values():
                if q.tool == "toot" and tool.works and tool_id == "velcro":
                    combos.append((qid, c.id, tool_id))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.hero_type not in {"boy", "girl"}:
        raise StoryError("Hero must be a child of a fairytale kind.")
    if params.hygienist_type not in {"queen", "lady", "boy", "girl"}:
        raise StoryError("Unreasonable hygienist type.")
    if params.tool != "velcro":
        raise StoryError("This quest needs Velcro, because the strap only holds with a clean, clever fastening.")
    if not TOOLS[params.tool].works:
        raise StoryError("That tool will not solve the quest.")


def tell(world: World, params: StoryParams) -> None:
    q = QUESTS[params.quest]
    tool = TOOLS[params.tool]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="quester"))
    hyg = world.add(Entity(id=params.hygienist, kind="character", type=params.hygienist_type, role="helper"))
    hero.memes["curiosity"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"Once in a small fairy castle, {hero.id} set out on a quest because {q.start}."
    )
    world.say(
        f"{hero.id} carried a loose satchel strap, and the only clue was {tool.phrase}."
    )
    world.para()
    hero.meters["toot"] += 1
    hero.memes["humor"] += 1
    world.say(f"{q.humor_line} The tiny toot made the pageboys blink and the sparrows hop.")
    world.say(f"In the quiet after it, {hero.id} thought, \"{q.monologue_line}\"")
    world.say(f"{hero.id} marched to {hyg.id}, the castle hygienist, and asked for help.")
    world.say(
        f"{hyg.id} smiled, washed the little brush, and used {tool.phrase} to make the strap hold."
    )
    hero.meters["fastened"] += 1
    hyg.meters["polished"] += 1
    hero.memes["relief"] += 1
    hyg.memes["kindness"] += 1
    world.para()
    world.say(
        f"At last, {q.success_line}, and {hero.id}'s satchel stopped flapping like a nervous flag."
    )
    world.say(
        f"{hero.id} gave a happy toot of laughter, and {hyg.id} bowed like a polite queen of clean teeth."
    )
    world.facts.update(hero=hero, hygienist=hyg, tool=tool, quest=q, outcome="success")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy-tale story with humor, a quest, and an inner monologue that includes the words toot, hygienist, and velcro.",
        f"Tell a child-facing story where {f['hero'].id} needs help from {f['hygienist'].id}, and Velcro solves a small quest in a funny way.",
        f"Write a gentle castle tale in which a toot becomes part of a quest and a hygienist helps make the ending bright and neat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    hyg = f["hygienist"].id
    return [
        QAItem(
            question="Who went on the quest?",
            answer=f"{hero} went on the quest, and {hyg} helped make it possible. The child wanted a small brave solution, and the hygienist knew exactly how to make it work.",
        ),
        QAItem(
            question="What problem did the hero have?",
            answer=f"The satchel strap was loose, so the hero needed something to hold it steady. The quest stayed small and funny, but it still needed a real fix.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a neat, steady strap and a clean, happy smile. The hero learned that asking for help can be the cleverest part of a quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Velcro?",
            answer="Velcro is a fastening that sticks together so things can stay closed without knots or buckles.",
        ),
        QAItem(
            question="What is a hygienist?",
            answer="A hygienist is a dental helper who cleans teeth and helps keep smiles healthy.",
        ),
        QAItem(
            question="Why can a toot be funny in a story?",
            answer="A toot can be funny because it makes a sudden, silly sound that surprises everyone and lightens the mood.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale quest about toot, hygienist, and velcro.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--hygienist")
    ap.add_argument("--hygienist-type", choices=["queen", "lady", "boy", "girl"])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--toot-style", choices=["tiny", "giggle"])
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
    quest = args.quest or "tooth_lantern"
    hero = args.hero or rng.choice(["Pip", "Mina"])
    hero_type = args.hero_type or ("boy" if hero == "Pip" else "girl")
    hygienist = args.hygienist or "Hush"
    hygienist_type = args.hygienist_type or "queen"
    tool = args.tool or "velcro"
    toot_style = args.toot_style or rng.choice(["tiny", "giggle"])
    params = StoryParams(
        quest=quest, hero=hero, hero_type=hero_type,
        hygienist=hygienist, hygienist_type=hygienist_type,
        tool=tool, toot_style=toot_style,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters for this story world.")
    reasonableness_gate(params)
    world = World()
    tell(world, params)
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("quest", "tooth_lantern"), asp.fact("tool", "velcro"), asp.fact("works", "velcro")]
    return "\n".join(lines)


ASP_RULES = r"""
valid(Quest, Hero, Tool) :- quest(Quest), tool(Tool), works(Tool).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python combo gates match.")
    else:
        rc = 1
        print("MISMATCH in combo gates.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
