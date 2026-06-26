#!/usr/bin/env python3
"""
Standalone story world: Puffin Quest Ghost Story.

A small, child-friendly simulation about a puffin who goes on a Quest,
meets a ghostly mystery, and learns how courage can make the dark feel kind.

The world is intentionally narrow:
- one puffin hero
- one moonlit place
- one lost object or hidden clue
- one ghost helper or ghostly obstacle
- one resolution that proves the change in state
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_at: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    friendly: bool = False
    spectral: bool = False

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "woman", "mother"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        if self.type in {"boy", "man", "father"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the foggy harbor"
    kind: str = "harbor"
    afford_quest: bool = True
    afford_ghosts: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    trial: str
    success_image: str
    keyword: str = "Quest"


@dataclass
class Ghost:
    id: str
    label: str
    hidden_item: str
    riddle: str
    help_line: str
    fear_drop: float = 1.0
    reveals: str = ""


@dataclass
class StoryParams:
    setting: str
    quest: str
    ghost: str
    name: str
    seed: Optional[int] = None


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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the foggy harbor", kind="harbor", afford_quest=True, afford_ghosts=True),
    "cliff": Setting(place="the moonlit cliff", kind="cliff", afford_quest=True, afford_ghosts=True),
    "island": Setting(place="the small island", kind="island", afford_quest=True, afford_ghosts=True),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="find the silver lantern",
        clue="a soft glow under the stones",
        trial="follow the tiny lights without getting scared",
        success_image="the lantern shining like a little star",
        keyword="Quest",
    ),
    "shell": Quest(
        id="shell",
        goal="find the lost pearl shell",
        clue="a white shell tucked near the tide line",
        trial="walk past the whispering water",
        success_image="the shell resting safely in the puffin's beak",
        keyword="Quest",
    ),
    "bell": Quest(
        id="bell",
        goal="find the little moon bell",
        clue="a bell sound hidden in the mist",
        trial="listen carefully when the wind starts to sing",
        success_image="the bell ringing gently in the night air",
        keyword="Quest",
    ),
}

GHOSTS = {
    "friendly": Ghost(
        id="friendly",
        label="a shy ghost",
        hidden_item="lantern",
        riddle="The thing you want is where brave feet can hear soft light.",
        help_line="I was only hiding it to keep it safe.",
        fear_drop=1.0,
        reveals="lantern",
    ),
    "mist": Ghost(
        id="mist",
        label="a mist ghost",
        hidden_item="shell",
        riddle="Look where the waves leave a white smile behind.",
        help_line="I keep it near the shore where no one would lose it again.",
        fear_drop=1.0,
        reveals="shell",
    ),
    "wind": Ghost(
        id="wind",
        label="a wind ghost",
        hidden_item="bell",
        riddle="Listen for the sound that hides inside the air.",
        help_line="I tucked it where the breeze could guard it.",
        fear_drop=1.0,
        reveals="bell",
    ),
}

NAMES = ["Pip", "Milo", "Nia", "Toby", "Luna", "Finn", "Mara", "Poppy", "Owen", "Ivy"]
TRAITS = ["brave", "curious", "gentle", "small", "tidy", "merry"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_valid(S, Q, G) :- setting(S), quest(Q), ghost(G),
                        setting_affords_quest(S), setting_affords_ghosts(S),
                        ghost_reveals(G, Q), quest_keyword(Q, "Quest").

story_ok(S, Q, G) :- quest_valid(S, Q, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_quest:
            lines.append(asp.fact("setting_affords_quest", sid))
        if s.afford_ghosts:
            lines.append(asp.fact("setting_affords_ghosts", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_keyword", qid, q.keyword))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("ghost_reveals", gid, g.reveals))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/3."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for g in GHOSTS:
                combos.append((s, q, g))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    ghost = GHOSTS[params.ghost]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="puffin",
        label="the puffin",
        traits=["small", "sea-bright"],
    ))
    spirit = world.add(Entity(
        id=ghost.id,
        kind="character",
        type="ghost",
        label=ghost.label,
        spectral=True,
        friendly=True,
    ))
    relic = world.add(Entity(
        id=quest.id,
        kind="thing",
        type=quest.id,
        label=quest.goal,
        phrase=quest.goal,
        hidden_at=setting.place,
    ))

    # Act 1
    world.say(f"{hero.id} was a small puffin who loved salty air and moonlit maps.")
    world.say(f"One night, {hero.id} heard about a {quest.keyword} to {quest.goal}.")
    world.say(f"The {quest.keyword} began at {setting.place}, where the fog curled like sleepy ribbons.")
    world.para()

    # Act 2
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1.0
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
    world.say(f"{hero.id} paddled forward on tiny feet and whispered, \"I can do a Quest.\"")
    world.say(f"Then {spirit.label} drifted out of the mist and said, \"{ghost.riddle}\"")
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(f"{hero.id}'s feathers prickled, but {hero.id} stayed near and listened.")
    world.para()

    # Act 3
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - ghost.fear_drop)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    relic.carried_by = hero.id
    relic.hidden_at = ""
    world.say(f"{spirit.label} sighed and said, \"{ghost.help_line}\"")
    world.say(f"With a careful flap and a brave blink, {hero.id} found the clue: {quest.clue}.")
    world.say(f"At last, {hero.id} carried away {relic.label}, and the night answered with {quest.success_image}.")
    world.say(f"The ghost waved goodbye, and the harbor felt kind instead of scary.")

    world.facts.update(hero=hero, ghost=spirit, quest=quest, relic=relic, setting=setting)
    return world


def valid_story_combo(setting: Setting, quest: Quest, ghost: Ghost) -> bool:
    return setting.afford_quest and setting.afford_ghosts and ghost.reveals == quest.id


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.quest and args.ghost:
        if not valid_story_combo(SETTINGS[args.setting], QUESTS[args.quest], GHOSTS[args.ghost]):
            raise StoryError("That combination does not make a reasonable ghost-quest story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, quest, ghost = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, quest=quest, ghost=ghost, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    ghost = f["ghost"]
    return [
        f'Write a short ghost story for young children about a puffin named {hero.id} on a {quest.keyword}.',
        f"Tell a moonlit story where {hero.id} meets {ghost.label} and learns how to finish the {quest.keyword}.",
        f'Write a gentle Puffin Quest story with mist, bravery, and a hidden treasure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    ghost = f["ghost"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who goes on the {quest.keyword} at {setting.place}?",
            answer=f"{hero.id}, a small puffin, goes on the {quest.keyword} at {setting.place}.",
        ),
        QAItem(
            question=f"What does {hero.id} want to do on the {quest.keyword}?",
            answer=f"{hero.id} wants to {quest.goal}.",
        ),
        QAItem(
            question=f"Who appears in the mist to help {hero.id}?",
            answer=f"{ghost.label} appears in the mist and gives {hero.id} a clue.",
        ),
        QAItem(
            question=f"What changes by the end of the story?",
            answer=f"By the end, {hero.id} is braver, the lost treasure is found, and the ghost is no longer scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puffin?",
            answer="A puffin is a seabird with a short body and a colorful beak. Puffins live near the ocean.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky-looking spirit. In a gentle story, a ghost can be lonely, shy, or helpful.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. A quest usually has a goal, a challenge, and a finish.",
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        if e.hidden_at:
            bits.append(f"hidden_at={e.hidden_at}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.spectral:
            bits.append("spectral=True")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for g in GHOSTS:
                if valid_story_combo(SETTINGS[s], QUESTS[q], GHOSTS[g]):
                    combos.append((s, q, g))
    return combos


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="harbor", quest="lantern", ghost="friendly", name="Pip"),
    StoryParams(setting="cliff", quest="bell", ghost="wind", name="Milo"),
    StoryParams(setting="island", quest="shell", ghost="mist", name="Nia"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Puffin Quest ghost story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_valid/3."))
        triples = sorted(set(asp.atoms(model, "quest_valid")))
        print(f"{len(triples)} valid story combos:\n")
        for s, q, g in triples:
            print(f"  {s:8} {q:8} {g:8}")
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
            header = f"### {p.name}: {p.quest} at {p.setting} (ghost: {p.ghost})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
