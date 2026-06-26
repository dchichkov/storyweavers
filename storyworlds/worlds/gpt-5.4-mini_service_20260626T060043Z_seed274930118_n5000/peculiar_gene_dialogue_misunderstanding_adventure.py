#!/usr/bin/env python3
"""
A small adventure storyworld with dialogue and a misunderstanding.

Seed premise:
- A child adventurer goes on a small quest.
- A peculiar guide named Gene speaks in a confusing way.
- The misunderstanding causes a detour.
- The child and Gene talk it through and reach the goal together.

This world keeps the tale grounded in physical meters and emotional memes,
and includes a small ASP twin for parity checking.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    route: str
    verb: str
    noise: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risky: bool = False


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with dialogue and misunderstanding.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


SETTINGS = {
    "cave": Setting("the cave", {"trail", "echo"}),
    "forest": Setting("the forest", {"trail", "bridge"}),
    "harbor": Setting("the harbor", {"dock", "rope"}),
}

QUESTS = {
    "map": Quest(
        id="map",
        goal="find the map",
        route="follow the lantern trail",
        verb="search for the map",
        noise="whispering",
        keyword="map",
        tags={"trail", "adventure"},
    ),
    "rope": Quest(
        id="rope",
        goal="reach the rope bridge",
        route="cross the bridge",
        verb="cross the rope bridge",
        noise="creaking",
        keyword="rope",
        tags={"bridge", "adventure"},
    ),
    "shell": Quest(
        id="shell",
        goal="recover the shell charm",
        route="walk to the dock",
        verb="look for the shell charm",
        noise="lapping",
        keyword="shell",
        tags={"dock", "adventure"},
    ),
}

ITEMS = {
    "lantern": Item("lantern", "lantern", "a small brass lantern", risky=False),
    "boots": Item("boots", "boots", "sturdy boots", risky=False),
    "key": Item("key", "key", "a tiny silver key", risky=True),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Pip", "Theo", "Arlo", "Finn", "Jace"]


@dataclass
class StoryParams:
    place: str
    quest: str
    item: str
    name: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id, quest in QUESTS.items():
            if not (quest.tags & setting.afford):
                continue
            for item_id, item in ITEMS.items():
                if quest_id == "rope" and item_id != "boots":
                    continue
                combos.append((place, quest_id, item_id))
    return combos


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    guide = world.get("gene")
    if hero.memes.get("confused", 0) < THRESHOLD or guide.memes.get("confused", 0) < THRESHOLD:
        return out
    sig = ("misunderstanding")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    guide.memes["worry"] = guide.memes.get("worry", 0) + 1
    out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            if s != "__misunderstanding__":
                world.say(s)
    return out


def tell(setting: Setting, quest: Quest, item: Item, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", "character", "boy" if hero_name in BOY_NAMES else "girl", traits=["curious", "brave"]))
    gene = world.add(Entity("gene", "character", "person", traits=["peculiar", "quiet"]))
    hero.id = hero_name
    gene.id = friend_name
    world.entities["hero"] = hero
    world.entities["gene"] = gene

    prize = world.add(Entity("prize", "thing", item.id, label=item.label, phrase=item.phrase, owner=hero.id))
    hero.meters["energy"] = 3
    hero.memes["hope"] = 1
    gene.memes["peculiar"] = 1

    world.say(f"{hero_name} was a small adventurer who loved a good trail and a bright clue.")
    world.say(f"One day, {hero_name} met a peculiar guide named Gene at {setting.place}.")
    world.say(f"Gene said, \"I can help you {quest.verb}, but only if you listen carefully.\"")
    world.say(f"{hero_name} clutched {prize.phrase} and nodded, though the words sounded strange.")

    world.para()
    world.say(f"They set off to {quest.route}.")
    world.say(f"Gene kept saying, \"Take the {quest.noise} path,\" and pointed ahead.")
    hero.memes["confused"] = 1
    gene.memes["confused"] = 1
    propagate(world, narrate=False)
    world.say(f"{hero_name} thought Gene meant a noisy shortcut and hurried the wrong way.")
    world.say(f"The path turned muddy and the little team had to stop.")

    world.para()
    if world.fired:
        world.say(f"{hero_name} frowned and asked, \"Do you mean the {quest.keyword} path or the noisy path?\"")
        world.say(f"Gene blinked. \"The {quest.keyword} path,\" Gene said. \"I was talking about the clue, not the sound.\"")
        hero.memes["worry"] = 0
        hero.memes["confused"] = 0
        gene.memes["worry"] = 0
        gene.memes["confused"] = 0
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        gene.memes["joy"] = gene.memes.get("joy", 0) + 1
        world.say(f"They laughed at the mix-up and took the real trail together.")
        world.say(f"At last, they reached the place and found {quest.goal}.")
        world.say(f"{hero_name} tucked {prize.phrase} away and walked home beside the peculiar Gene, both feeling proud.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the words "{f["hero_name"]}", "Gene", "peculiar", and "misunderstanding".',
        f"Tell a small quest story where {f['hero_name']} and Gene argue over a clue, then fix the misunderstanding.",
        f"Write a gentle adventure with dialogue, a wrong path, and a happy ending at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was the peculiar guide in the story?",
            answer="The peculiar guide was Gene, who spoke in a confusing way but was trying to help.",
        ),
        QAItem(
            question=f"What misunderstanding happened when they started the quest?",
            answer=f"{f['hero_name']} thought Gene meant a noisy shortcut, but Gene really meant the clue path.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"They cleared up the misunderstanding, took the real trail together, and found the goal safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people hear the same words but think they mean different things.",
        ),
        QAItem(
            question="What does an adventurer do?",
            answer="An adventurer explores new places, looks for clues, and keeps going when the path gets tricky.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "map", "lantern", "Mina", "Gene"),
    StoryParams("cave", "map", "key", "Pip", "Gene"),
    StoryParams("harbor", "shell", "boots", "Ivy", "Gene"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and args.item:
        if (args.place, args.quest, args.item) not in valid_combos():
            raise StoryError("That combination does not make a reasonable adventure.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("No valid adventure matches those options.")
    place, quest, item = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or "Gene"
    return StoryParams(place, quest, item, name, friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], ITEMS[params.item], params.name, params.friend)
    world.facts = {
        "hero_name": params.name,
        "friend_name": params.friend,
        "setting": SETTINGS[params.place],
        "quest": QUESTS[params.quest],
        "item": ITEMS[params.item],
    }
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
#show valid/3.
valid(Place,Quest,Item) :- setting(Place), quest(Quest), item(Item), allowed(Place,Quest,Item).

allowed(forest,map,lantern).
allowed(cave,map,lantern).
allowed(cave,map,key).
allowed(harbor,shell,boots).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for f in setting.afford:
            lines.append(asp.fact("afford", pid, f))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
