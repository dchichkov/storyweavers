#!/usr/bin/env python3
"""
storyworlds/worlds/freak_dim_rhyme_sharing_surprise_superhero_story.py
=====================================================================

A standalone story world for a tiny superhero tale with:
- freak-dim
- rhyme
- sharing
- surprise

Premise:
A young superhero finds that a strange "freak-dim" door has opened in the city.
A rescue depends on noticing a rhyme clue, sharing a special gadget, and
handling a surprise twist in the dim tunnel below.

The world is intentionally small and constraint-driven: only a few compatible
story variants are allowed, and every story is built from live state changes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Small domain registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HeroSpec:
    hero_type: str
    noun: str
    pronoun: str
    poss: str
    role: str


@dataclass(frozen=True)
class RescueTool:
    id: str
    name: str
    phrase: str
    helps: str
    shared: bool = True


@dataclass(frozen=True)
class RhymeClue:
    id: str
    line: str
    hint: str
    action: str


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dimness": 0.0, "trouble": 0.0, "joy": 0.0}
        if not self.memes:
            self.memes = {"surprise": 0.0, "teamwork": 0.0, "care": 0.0}


@dataclass
class World:
    city: str
    hero: Entity
    sidekick: Entity
    tool: Entity
    clue: Entity
    villain: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    city: str
    hero: str
    sidekick: str
    tool: str
    clue: str
    villain: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HEROES = {
    "spark": HeroSpec("girl", "girl", "she", "her", "a bright little hero"),
    "bolt": HeroSpec("boy", "boy", "he", "his", "a quick little hero"),
    "nova": HeroSpec("girl", "girl", "she", "her", "a brave little hero"),
    "flare": HeroSpec("boy", "boy", "he", "his", "a steady little hero"),
}

TOOLS = {
    "ropebeam": RescueTool(
        id="ropebeam",
        name="rope beam",
        phrase="a shiny rope beam",
        helps="pull things close or bridge a gap",
    ),
    "glowshield": RescueTool(
        id="glowshield",
        name="glow shield",
        phrase="a round glow shield",
        helps="light the way and calm a dim place",
    ),
    "sharepack": RescueTool(
        id="sharepack",
        name="share pack",
        phrase="a handy share pack",
        helps="carry pieces that must be shared with friends",
    ),
}

CLUES = {
    "rhyme1": RhymeClue(
        id="rhyme1",
        line="When the tunnel goes low, the lights must glow.",
        hint="glow",
        action="follow the rhyme",
    ),
    "rhyme2": RhymeClue(
        id="rhyme2",
        line="If you see a crack, send the beam back.",
        hint="beam",
        action="send the beam back",
    ),
    "rhyme3": RhymeClue(
        id="rhyme3",
        line="When friends must share, the path is fair.",
        hint="share",
        action="share the gear",
    ),
}

VILLAINS = {
    "murmur-moth": "murmur-moth",
    "dim-blob": "dim-blob",
    "whisper-void": "whisper-void",
}

CITIES = {
    "Metroglow": {"dimness": 2.0},
    "Brightbay": {"dimness": 1.5},
    "Starcross": {"dimness": 2.5},
}

CURATED = [
    StoryParams(city="Metroglow", hero="spark", sidekick="bolt", tool="glowshield", clue="rhyme1", villain="dim-blob"),
    StoryParams(city="Brightbay", hero="nova", sidekick="flare", tool="ropebeam", clue="rhyme2", villain="murmur-moth"),
    StoryParams(city="Starcross", hero="bolt", sidekick="spark", tool="sharepack", clue="rhyme3", villain="whisper-void"),
]

CITYS = list(CITIES.keys())


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def valid_combo(city: str, hero: str, sidekick: str, tool: str, clue: str, villain: str) -> bool:
    if hero == sidekick:
        return False
    if tool == "glowshield" and clue != "rhyme1":
        return False
    if tool == "ropebeam" and clue != "rhyme2":
        return False
    if tool == "sharepack" and clue != "rhyme3":
        return False
    if villain == "dim-blob" and tool not in {"glowshield", "sharepack"}:
        return False
    if villain == "murmur-moth" and tool not in {"ropebeam", "glowshield"}:
        return False
    if villain == "whisper-void" and tool not in {"sharepack", "ropebeam"}:
        return False
    return True


def all_valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for city in CITIES:
        for hero in HEROES:
            for sidekick in HEROES:
                for tool in TOOLS:
                    for clue in CLUES:
                        for villain in VILLAINS:
                            if valid_combo(city, hero, sidekick, tool, clue, villain):
                                combos.append((city, hero, sidekick, tool, clue, villain))
    return combos


def explain_rejection(city: str, hero: str, sidekick: str, tool: str, clue: str, villain: str) -> str:
    return (
        f"(No story: the chosen mix does not make sense. The tool {tool} does not "
        f"fit the rhyme clue {clue}, or the villain {villain} cannot be solved that way.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    hero_spec = HEROES[params.hero]
    sidekick_spec = HEROES[params.sidekick]
    tool_spec = TOOLS[params.tool]
    clue_spec = CLUES[params.clue]
    city_state = CITIES[params.city]

    hero = Entity(id=params.hero, kind="character", label=hero_spec.role, type=hero_spec.hero_type)
    sidekick = Entity(id=params.sidekick, kind="character", label=sidekick_spec.role, type=sidekick_spec.hero_type)
    tool = Entity(id=params.tool, kind="thing", label=tool_spec.name, type="tool", owner=hero.id)
    clue = Entity(id=params.clue, kind="thing", label="rhyme clue", type="clue")
    villain = Entity(id=params.villain, kind="character", label=params.villain, type="villain")
    world = World(city=params.city, hero=hero, sidekick=sidekick, tool=tool, clue=clue, villain=villain)

    world.facts.update(
        hero_spec=hero_spec,
        sidekick_spec=sidekick_spec,
        tool_spec=tool_spec,
        clue_spec=clue_spec,
        city_state=city_state,
    )
    return world


def run_story(world: World) -> None:
    fs = world.facts
    hero_spec: HeroSpec = fs["hero_spec"]
    sidekick_spec: HeroSpec = fs["sidekick_spec"]
    tool_spec: RescueTool = fs["tool_spec"]
    clue_spec: RhymeClue = fs["clue_spec"]
    city_state = fs["city_state"]

    hero = world.hero
    sidekick = world.sidekick
    tool = world.tool
    clue = world.clue
    villain = world.villain

    # Setup
    world.say(
        f"In {world.city}, {hero.label} {hero.id} was {hero_spec.role} who loved helping people."
    )
    world.say(
        f"{hero.id} had a friend named {sidekick.id}, and together they watched the sky for trouble."
    )
    world.say(
        f"They carried {tool_spec.phrase}, because it could {tool_spec.helps}."
    )
    world.para()

    # Conflict
    world.say(
        f"One evening, a strange freak-dim opened under the street lights, and the whole block went hush-quiet."
    )
    world.say(
        f"The darkness felt heavier there, and even {villain.id} was hiding behind the fog."
    )
    world.say(
        f"{hero.id} found a little rhyme clue on the wall: \"{clue_spec.line}\""
    )
    world.facts["rhyme_heard"] = True
    world.facts["surprise_seen"] = True
    world.facts["dimness"] = city_state["dimness"] + 2.0
    hero.meters["trouble"] += 1.0
    hero.memes["surprise"] += 1.0
    sidekick.memes["surprise"] += 1.0
    world.para()

    # Turn
    world.say(
        f"{hero.id} stopped, smiled, and said the line again. \"{clue_spec.line}\""
    )
    world.say(
        f"{sidekick.id} nodded. That meant they had to {clue_spec.action}, not rush ahead."
    )
    if tool.id == "sharepack":
        world.say(
            f"They opened the {tool_spec.name} and shared the pieces, one for each hand."
        )
        tool.shared_with = [hero.id, sidekick.id]
    else:
        world.say(
            f"{hero.id} handed {tool_spec.name} to {sidekick.id} so they could use it together."
        )
        tool.shared_with = [hero.id, sidekick.id]
    world.facts["shared"] = True
    hero.memes["teamwork"] += 1.0
    sidekick.memes["teamwork"] += 1.0
    hero.memes["care"] += 1.0
    sidekick.memes["care"] += 1.0

    if clue.id == "rhyme3":
        world.say(
            f"The rhyme about sharing was just right, and it made the path feel fair instead of scary."
        )
    elif clue.id == "rhyme2":
        world.say(
            f"The rhyme about the beam pointed straight to the crack in the floor."
        )
    else:
        world.say(
            f"The rhyme about the glow pointed them toward the dim spot below the stairs."
        )

    # Surprise resolution
    world.para()
    world.say(
        f"Then came the surprise: {villain.id} was not stealing anything at all."
    )
    world.say(
        f"{villain.id} was stuck in the freak-dim, shivering and too dim to find the way out."
    )
    world.say(
        f"{hero.id} and {sidekick.id} used the {tool_spec.name} together, and the light and courage worked like a team."
    )
    if tool.id == "glowshield":
        world.say(
            f"The glow shield made a warm circle, and {villain.id} finally saw the door."
        )
    elif tool.id == "ropebeam":
        world.say(
            f"The rope beam reached across the gap, and {villain.id} could climb back to the street."
        )
    else:
        world.say(
            f"The share pack let them split the rescue gear, and that was enough to pull {villain.id} free."
        )
    world.say(
        f"{villain.id} blinked, apologized, and slipped away into the night."
    )
    world.say(
        f"At the end, the freak-dim was smaller, the street lights were bright again, and {hero.id} and {sidekick.id} smiled in the clean night air."
    )

    hero.meters["joy"] += 1.0
    sidekick.meters["joy"] += 1.0
    villain.meters["trouble"] = max(0.0, villain.meters["trouble"] - 1.0)
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    fs = world.facts
    hero = world.hero
    sidekick = world.sidekick
    tool_spec: RescueTool = fs["tool_spec"]
    clue_spec: RhymeClue = fs["clue_spec"]
    return [
        f'Write a short superhero story for young children that includes the word "freak-dim".',
        f"Tell a story where {hero.id} and {sidekick.id} solve trouble by using a rhyme clue and sharing {tool_spec.name}.",
        f'Write a gentle rescue story where the surprise ending shows why " {clue_spec.hint} " mattered.',
    ]


def story_qa(world: World) -> list[QAItem]:
    fs = world.facts
    hero: Entity = world.hero
    sidekick: Entity = world.sidekick
    tool_spec: RescueTool = fs["tool_spec"]
    clue_spec: RhymeClue = fs["clue_spec"]
    villain: Entity = world.villain

    return [
        QAItem(
            question=f"Who were the two heroes in {world.city}?",
            answer=f"The heroes were {hero.id} and {sidekick.id}. They worked together in {world.city}.",
        ),
        QAItem(
            question=f"What clue helped them in the freak-dim?",
            answer=f"They heard a rhyme: \"{clue_spec.line}\" That clue told them what to do next.",
        ),
        QAItem(
            question=f"What did they share to help the rescue?",
            answer=f"They shared {tool_spec.phrase}. Sharing it let both heroes use it together.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {villain.id} was stuck in the freak-dim and needed help, instead of causing the trouble.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the freak-dim getting smaller, the street lights shining again, and {hero.id} and {sidekick.id} feeling proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    fs = world.facts
    tool_spec: RescueTool = fs["tool_spec"]
    clue_spec: RhymeClue = fs["clue_spec"]
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike, like glow and show, or beam and dream.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something with you, so everyone can help or enjoy it together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect, so it makes you stop and notice what changed.",
        ),
        QAItem(
            question=f"What does {tool_spec.name} do?",
            answer=f"{tool_spec.phrase.capitalize()} can {tool_spec.helps}.",
        ),
        QAItem(
            question="Why do heroes work together?",
            answer="Heroes work together because teamwork lets them solve bigger problems than one hero could solve alone.",
        ),
        QAItem(
            question=f"What kind of thing is the phrase \"{clue_spec.line}\" in the story?",
            answer="It is a rhyme clue, which means the words sound catchy and help point the heroes toward the right action.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/6.

hero(H) :- hero_spec(H).
sidekick(S) :- hero_spec(S).

compatible(H, S) :- hero_spec(H), hero_spec(S), H != S.

tool_for_clue(glowshield, rhyme1).
tool_for_clue(ropebeam, rhyme2).
tool_for_clue(sharepack, rhyme3).

tool_for_villain(glowshield, dim-blob).
tool_for_villain(sharepack, dim-blob).
tool_for_villain(ropebeam, murmur-moth).
tool_for_villain(glowshield, murmur-moth).
tool_for_villain(sharepack, whisper-void).
tool_for_villain(ropebeam, whisper-void).

valid(City, Hero, Sidekick, Tool, Clue, Villain) :-
    city(City),
    hero_spec(Hero),
    hero_spec(Sidekick),
    Hero != Sidekick,
    tool(Tool),
    clue(Clue),
    villain(Villain),
    tool_for_clue(Tool, Clue),
    tool_for_villain(Tool, Villain).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for city in CITIES:
        lines.append(asp.fact("city", city))
    for hid in HEROES:
        lines.append(asp.fact("hero_spec", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for vid in VILLAINS:
        lines.append(asp.fact("villain", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(all_valid_combos())
    cl = set(asp_valid_combos())
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
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world with freak-dim, rhyme, sharing, and surprise.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=HEROES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--villain", choices=VILLAINS)
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
    if args.city and args.hero and args.sidekick and args.tool and args.clue and args.villain:
        if not valid_combo(args.city, args.hero, args.sidekick, args.tool, args.clue, args.villain):
            raise StoryError(explain_rejection(args.city, args.hero, args.sidekick, args.tool, args.clue, args.villain))

    combos = [
        c for c in all_valid_combos()
        if (args.city is None or c[0] == args.city)
        and (args.hero is None or c[1] == args.hero)
        and (args.sidekick is None or c[2] == args.sidekick)
        and (args.tool is None or c[3] == args.tool)
        and (args.clue is None or c[4] == args.clue)
        and (args.villain is None or c[5] == args.villain)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    city, hero, sidekick, tool, clue, villain = rng.choice(sorted(combos))
    return StoryParams(city=city, hero=hero, sidekick=sidekick, tool=tool, clue=clue, villain=villain)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    run_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.sidekick, world.tool, world.clue, world.villain]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.shared_with:
            bits.append(f"shared_with={ent.shared_with}")
        lines.append(f"  {ent.id:10} ({ent.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combinations.")
        for combo in combos[:200]:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and i < limit:
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero} + {p.sidekick} in {p.city} (tool: {p.tool}, clue: {p.clue}, villain: {p.villain})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
