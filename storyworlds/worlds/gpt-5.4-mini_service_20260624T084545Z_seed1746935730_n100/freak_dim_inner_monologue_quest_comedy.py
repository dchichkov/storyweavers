#!/usr/bin/env python3
"""
storyworlds/worlds/freak_dim_inner_monologue_quest_comedy.py
============================================================

A small comedic story world about a baffling little "freak-dim" quest, where a
child's inner monologue keeps getting in the way of the mission until the world
itself becomes the punchline.

Seed tale idea:
---
A kid notices that a strange, tiny, wobbling dimension has opened behind the
laundry basket. It keeps making goofy noises, as if it wants help. The kid wants
to be brave, but their inner monologue is dramatic and silly: "This could be a
monster, or a sandwich, or a monster sandwich!" They pack a flashlight, follow
the clue trail, and end up rescuing a lost button-king from a pile of socks.
The dimension closes with a pop, and the kid proudly declares the quest was
"not scary at all," even though their knees are still wobbly.

Causal state updates:
---
    clue collected            -> progress += 1, curiosity += 1
    inner monologue worries   -> worry += 1, courage -= 1
    quest progress + helper   -> progress += 2, worry -= 1
    solved quest              -> pride += 1, courage += 1, relief += 1
    freak-dim closes          -> weirdness -= 1, calm += 1

Scripted beats:
---
    invitation from the strange dimension
    dramatic inner monologue with comic overreaction
    questing through odd clues and a silly obstacle
    helpful discovery / rescue
    closing image that proves the world changed
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str = "the laundry room"
    weirdness: str = "slightly wobbling"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    safe: bool = False


@dataclass
class StoryParams:
    place: str
    quest: str
    help_item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.quest_log: list[str] = []

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.quest_log = list(self.quest_log)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if world.facts.get("monologue_active") and ("worry", hero.id) not in world.fired:
        world.fired.add(("worry", hero.id))
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        hero.memes["courage"] = hero.memes.get("courage", 0) - 1
        out.append(f"{hero.id}'s brain started making a very dramatic face.")
    return out


def _r_clue_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    clues = world.facts.get("clues_collected", 0)
    if clues > 0 and ("progress", clues) not in world.fired:
        world.fired.add(("progress", clues))
        hero.meters["progress"] = hero.meters.get("progress", 0) + clues
        hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + clues
        out.append(f"Each clue made the trail feel less spooky and more silly.")
    return out


def _r_helper_boost(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not hero or not helper:
        return out
    if world.facts.get("helper_joined") and ("help", hero.id) not in world.fired:
        world.fired.add(("help", hero.id))
        hero.meters["progress"] = hero.meters.get("progress", 0) + 2
        hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
        out.append(f"With help, the quest stopped wobbling so much.")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    if world.facts.get("quest_solved") and ("solved", hero.id) not in world.fired:
        world.fired.add(("solved", hero.id))
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
        hero.memes["courage"] = hero.memes.get("courage", 0) + 1
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        out.append(f"The strange little mission finally clicked into place.")
    return out


def _r_close_dim(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("dim_closed") and ("close", 1) not in world.fired:
        world.fired.add(("close", 1))
        world.facts["weirdness"] = max(0, world.facts.get("weirdness", 3) - 1)
        out.append(f"The freak-dim made one last fizzle, then behaved itself.")
    return out


CAUSAL_RULES = [
    Rule("inner_monologue", _r_inner_monologue),
    Rule("clue_progress", _r_clue_progress),
    Rule("helper_boost", _r_helper_boost),
    Rule("solved", _r_solved),
    Rule("close_dim", _r_close_dim),
]


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
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "laundry": Setting(place="the laundry room", weirdness="slightly wobbling", affords={"sock", "button", "lantern"}),
    "hall": Setting(place="the hallway", weirdness="humming", affords={"map", "lantern"}),
    "attic": Setting(place="the attic", weirdness="dusty and echoing", affords={"map", "button", "lantern"}),
}

QUESTS = {
    "button-king": {
        "name": "button-king",
        "goal": "find the lost button-king",
        "clues": ["a tiny crown", "a trail of silver thread", "a sock-shaped doorway"],
        "obstacle": "a mountain of socks",
        "rescue": "the button-king was stuck in the soft pile",
        "close": "the tiny doorway snapped shut",
    },
    "moon-map": {
        "name": "moon-map",
        "goal": "deliver the moon-map to the toy ship",
        "clues": ["a glowing corner", "a paper moon", "a polite note"],
        "obstacle": "a chair that squeaked like a mouse",
        "rescue": "the map had slid under the toy ship",
        "close": "the lamp blinked once and the room went calm",
    },
    "pickle-compass": {
        "name": "pickle-compass",
        "goal": "bring the pickle-compass back to the shelf",
        "clues": ["a green gleam", "a spoon bridge", "a crumb path"],
        "obstacle": "a jar with a stubborn lid",
        "rescue": "the compass was balancing on the rim",
        "close": "the jar stopped humming and sat still",
    },
}

TOOLS = {
    "flashlight": Tool("flashlight", "flashlight", "a brave little flashlight", {"button-king", "moon-map", "pickle-compass"}),
    "magnifier": Tool("magnifier", "magnifying glass", "a round magnifying glass", {"button-king", "pickle-compass"}),
    "map": Tool("map", "map", "a crumpled map", {"moon-map", "pickle-compass"}),
    "snack": Tool("snack", "snack", "a pocket snack", {"button-king", "moon-map", "pickle-compass"}, safe=True),
}

GIRL_NAMES = ["Mia", "Nora", "Ruby", "Ada", "Zoe", "Lina", "Piper", "June"]
BOY_NAMES = ["Max", "Theo", "Ben", "Finn", "Leo", "Eli", "Owen", "Sam"]
TRAITS = ["curious", "silly", "brave", "dramatic", "cheerful", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest in QUESTS:
            for help_item, tool in TOOLS.items():
                if quest in tool.helps and help_item in setting.affords:
                    combos.append((place, quest, help_item))
    return combos


def prize_at_risk(quest: dict, help_item: Tool) -> bool:
    return quest["name"] in help_item.helps


def select_tool(quest: dict, help_item: Tool) -> Optional[Tool]:
    return help_item if quest["name"] in help_item.helps else None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest(Quest) :- goal(Quest, _).
tool(Tool) :- helps(Tool, Quest).
valid(Place, Quest, Tool) :- affords(Place, Tool), goal(Quest, _), helps(Tool, Quest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("goal", qid, q["goal"]))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for q in sorted(t.helps):
            lines.append(asp.fact("helps", tid, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: freak-dim quest + inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--help-item", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def explain_rejection(place: str, quest: str, help_item: str) -> str:
    return f"(No story: {help_item} does not reasonably help with {quest} in {place}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and args.help_item:
        if (args.place, args.quest, args.help_item) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.quest, args.help_item))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.help_item is None or c[2] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, help_item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, quest, help_item, name, gender, parent, trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    quest = QUESTS[params.quest]
    tool = TOOLS[params.help_item]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"worry": 0, "courage": 1, "curiosity": 1}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    helper = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase))
    dim = world.add(Entity(id="freak-dim", kind="place", type="place", label="freak-dim", phrase="a tiny wobbling dimension"))

    world.facts.update(hero=hero, parent=parent, helper=helper, dim=dim, quest=quest, monologue_active=True, weirdness=3)

    world.say(f"{hero.id} found a tiny freak-dim behind {setting.place}. It hummed like it had a joke to tell.")
    world.say(f"{hero.id} was a {params.trait} {params.gender} who loved clues and tiny adventures.")
    world.say(f"The freak-dim winked and asked for help finding {quest['goal']}.")
    world.para()
    world.say(f"{hero.id} thought, \"This is either a quest or a very weird snack.\"")
    world.say(f"Inside {hero.id}'s head, the monologue got louder: \"What if it is a monster? What if it is a polite monster?\"")
    propagate(world)

    world.para()
    world.say(f"So {hero.id} grabbed {tool.phrase} and stepped into {setting.place}.")
    world.say(f"The first clue was {quest['clues'][0]}, which looked important enough to be silly.")
    world.facts["clues_collected"] = 1
    world.quest_log.append(quest["clues"][0])
    propagate(world)

    world.say(f"Then came {quest['clues'][1]} and {quest['obstacle']}.")
    world.facts["clues_collected"] = 2
    world.quest_log.append(quest["clues"][1])
    world.say(f"{hero.id} muttered, \"I am definitely winning this quest. I am also definitely standing very carefully.\"")
    propagate(world)

    world.para()
    world.say(f"{params.parent.capitalize()} peeked in and said, \"Need a hand?\"")
    world.say(f"{hero.id}'s brain whispered, \"Yes. No. Maybe a tiny heroic yes.\"")
    world.facts["helper_joined"] = True
    world.facts["clues_collected"] = 3
    world.quest_log.append(quest["clues"][2])
    propagate(world)

    world.say(f"At last, {quest['rescue']}. {hero.id} found the missing piece and laughed so hard {hero.pronoun('possessive')} knees almost forgot to be knees.")
    world.facts["quest_solved"] = True
    world.facts["dim_closed"] = True
    propagate(world)

    world.para()
    world.say(f"{quest['close']}, and the freak-dim gave a tiny satisfied pop.")
    world.say(f"{hero.id} went home proud, still a little wobbly, but grinning like a champion of weird little places.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a funny story for a young child about a "{quest["name"]}" quest in a freak-dim.',
        f"Tell a comic adventure where {hero.id} hears a dramatic inner monologue and then solves a tiny mystery.",
        f"Write a child-friendly story about a strange little dimension, a clue trail, and a happy rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    tool = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} find behind {world.setting.place}?",
            answer=f"{hero.id} found a tiny freak-dim, and it asked for help with {quest['goal']}.",
        ),
        QAItem(
            question=f"What did {hero.id}'s inner monologue worry about during the quest?",
            answer=f"{hero.id}'s inner monologue worried that the strange place might be a monster, or maybe a very polite monster.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help with the quest?",
            answer=f"{hero.id} used {tool.phrase} to keep going through the clues and the silly obstacle.",
        ),
        QAItem(
            question=f"How did the story end after the quest was solved?",
            answer=f"The freak-dim closed with a tiny pop, and {hero.id} went home proud and grinning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out a mystery or find the next step.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something, fix something, or help someone.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the voice in your head that tells you what you are thinking.",
        ),
        QAItem(
            question="Why can funny stories be helpful?",
            answer="Funny stories can help because laughing can make a scary or hard thing feel a little easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  quest log: {world.quest_log}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def asp_program_for_show(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_program() -> int:
    return asp_verify()


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="laundry", quest="button-king", help_item="flashlight", name="Mia", gender="girl", parent="mother", trait="dramatic"),
    StoryParams(place="hall", quest="moon-map", help_item="map", name="Ben", gender="boy", parent="father", trait="curious"),
    StoryParams(place="attic", quest="pickle-compass", help_item="magnifier", name="Ruby", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_for_show("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_program())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_for_show("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, quest, help-item) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
