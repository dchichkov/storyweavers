#!/usr/bin/env python3
"""
storyworlds/worlds/lop_honcho_mystery_to_solve_friendship_tall.py
==================================================================

A small tall-tale storyworld about a lop-eared little hero, a friendly honcho,
and a mystery that can be solved with noticing, teamwork, and kindness.

The seed story that inspired this world:
---
A lop-eared bunny named Loppy lived at the edge of a wide, windy plain.
One afternoon, the barn bell went missing, and everyone looked at one another
as if the sky itself had hidden it. The ranch honcho, a big cheerful cow named
Mabel, asked Loppy to help solve the mystery. Loppy followed tracks, asked
careful questions, and found the bell tangled in a rope swing. Mabel laughed,
Loppy beamed, and the two became fast friends.
---

This script turns that premise into a simulation with:
- physical meters: distance, hiding, noise, wind, clues, discovered
- emotional memes: curiosity, worry, trust, friendship, pride, relief

The story is intended to read like a complete little tall tale:
setup -> mystery -> clue chase -> reveal -> friendship-ending image.
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
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    sky: str
    surfaces: tuple[str, ...]
    affordances: tuple[str, ...]


@dataclass(frozen=True)
class Mystery:
    id: str
    missing: str
    clue_kind: str
    culprit: str
    reveal_method: str
    ending_image: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Friend:
    id: str
    type: str
    name: str
    title: str
    phrase: str
    traits: tuple[str, ...]
    gender: str = "neutral"


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: tuple[str, ...]
    tags: tuple[str, ...]


SETTINGS = {
    "barn": Setting(
        id="barn",
        place="the red barn",
        sky="wide and windy",
        surfaces=("dusty floor", "hay pile", "loft ladder"),
        affordances=("search", "hide", "listen"),
    ),
    "fair": Setting(
        id="fair",
        place="the county fair",
        sky="bright and busy",
        surfaces=("ticket booth", "cookie table", "prize fence"),
        affordances=("search", "listen", "ask"),
    ),
    "plain": Setting(
        id="plain",
        place="the open plain",
        sky="big and blustery",
        surfaces=("long grass", "wagon track", "stone fence"),
        affordances=("search", "track", "listen"),
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing="the barn bell",
        clue_kind="shiny mark",
        culprit="a rope swing",
        reveal_method="followed the shiny clue",
        ending_image="the bell hung right where the breeze had danced it into place",
        tags=("shiny", "rope", "wind"),
    ),
    "pie": Mystery(
        id="pie",
        missing="the prize pie",
        clue_kind="crumb trail",
        culprit="a picnic basket lid",
        reveal_method="followed the crumb trail",
        ending_image="the pie sat safe beside a smiling table",
        tags=("crumbs", "basket", "sweet"),
    ),
    "hat": Mystery(
        id="hat",
        missing="the honcho's tall hat",
        clue_kind="bent feather",
        culprit="a low branch",
        reveal_method="followed the bent feather",
        ending_image="the hat rested snug on a peg by the door",
        tags=("feather", "branch", "tall"),
    ),
    "lantern": Mystery(
        id="lantern",
        missing="the porch lantern",
        clue_kind="warm glow",
        culprit="a squirrel nest",
        reveal_method="followed the warm glow",
        ending_image="the lantern glowed again like a small moon on the porch",
        tags=("glow", "nest", "light"),
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a little lantern that shone like a yellow firefly",
        helps_with=("dark", "glow", "night"),
        tags=("light",),
    ),
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        phrase="a round magnifying glass with a wooden handle",
        helps_with=("shiny", "crumbs", "feather"),
        tags=("look",),
    ),
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a sturdy rope for lifting and tying",
        helps_with=("branch", "basket", "loft"),
        tags=("tie",),
    ),
    "notebook": Tool(
        id="notebook",
        label="a notebook",
        phrase="a square notebook with a red cover",
        helps_with=("ask", "listen", "track"),
        tags=("note",),
    ),
}

LOPES = [
    Friend(
        id="Lop",
        type="rabbit",
        name="Lop",
        title="little lop-eared rabbit",
        phrase="a little lop-eared rabbit with ears that folded like soft ribbons",
        traits=("curious", "gentle", "quick"),
        gender="neutral",
    ),
    Friend(
        id="Mina",
        type="rabbit",
        name="Mina",
        title="lop-eared rabbit",
        phrase="a lop-eared rabbit with a nose that twitched at every clue",
        traits=("brave", "curious", "kind"),
        gender="neutral",
    ),
]

HONCHOS = [
    Friend(
        id="Mabel",
        type="cow",
        name="Mabel",
        title="honcho cow",
        phrase="a honcho cow who ran the farm with a warm smile and a booming laugh",
        traits=("steady", "cheerful", "wise"),
        gender="neutral",
    ),
    Friend(
        id="Otis",
        type="horse",
        name="Otis",
        title="honcho horse",
        phrase="a honcho horse with a long tail and a bossy-but-kind voice",
        traits=("strong", "patient", "friendly"),
        gender="neutral",
    ),
    Friend(
        id="Pearl",
        type="hen",
        name="Pearl",
        title="honcho hen",
        phrase="a honcho hen who kept every nest in order",
        traits=("alert", "snappy", "helpful"),
        gender="neutral",
    ),
]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story_bits: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.story_bits.append(text)

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
    setting: str
    mystery: str
    hero: str
    honcho: str
    tool: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: a lop, a honcho, and a mystery to solve.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--hero", choices=sorted({f.id for f in LOPES}))
    ap.add_argument("--honcho", choices=sorted({f.id for f in HONCHOS}))
    ap.add_argument("--tool", choices=sorted(TOOLS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero = args.hero or rng.choice([f.id for f in LOPES])
    honcho = args.honcho or rng.choice([f.id for f in HONCHOS])
    tool = args.tool or rng.choice(list(TOOLS))

    if hero == honcho:
        raise StoryError("The lop and the honcho must be different characters.")

    return StoryParams(setting=setting, mystery=mystery, hero=hero, honcho=honcho, tool=tool)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/4.

compatible_story(S, M, H, C) :- setting(S), mystery(M), hero(H), honcho(C),
    helps(H, M), helps(C, M), different(H, C), at_risk(S, M).

valid_story(S, M, H, C) :- compatible_story(S, M, H, C).

different(H, C) :- H != C.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for aff in s.affordances:
            lines.append(asp.fact("affords", sid, aff))
        if s.sky:
            lines.append(asp.fact("sky", sid, s.sky))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        lines.append(asp.fact("culprit", mid, m.culprit))
        for tag in m.tags:
            lines.append(asp.fact("tags", mid, tag))
    for f in LOPES:
        lines.append(asp.fact("hero", f.id))
        for t in f.traits:
            lines.append(asp.fact("helps", f.id, t))
    for f in HONCHOS:
        lines.append(asp.fact("honcho", f.id))
        for t in f.traits:
            lines.append(asp.fact("helps", f.id, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in t.helps_with:
            lines.append(asp.fact("helps", tid, h))
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            # simple compatibility: mystery is reasonable in any setting that affords search/listen/ask/track
            if "search" in s.affordances or "listen" in s.affordances:
                lines.append(asp.fact("at_risk", sid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} story combinations.")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for h in LOPES:
                for c in HONCHOS:
                    if h.id == c.id:
                        continue
                    combos.append((s, m, h.id, c.id))
    return combos


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    hero_cfg = next(f for f in LOPES if f.id == params.hero)
    honcho_cfg = next(f for f in HONCHOS if f.id == params.honcho)
    tool_cfg = TOOLS[params.tool]

    world = World(setting)
    hero = world.add(Entity(id=hero_cfg.id, kind="character", type=hero_cfg.type, label=hero_cfg.name, phrase=hero_cfg.phrase))
    honcho = world.add(Entity(id=honcho_cfg.id, kind="character", type=honcho_cfg.type, label=honcho_cfg.name, phrase=honcho_cfg.phrase))
    tool = world.add(Entity(id=tool_cfg.id, kind="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase))
    lost = world.add(Entity(id=mystery.id, kind="object", type="object", label=mystery.missing, phrase=mystery.missing, owner=honcho.id))

    # meters
    hero.meters.update(curiosity=1.0, distance=0.0, clue=0.0, joy=0.0)
    honcho.meters.update(worry=1.0, patience=1.0, relief=0.0)
    lost.meters.update(hidden=1.0, found=0.0)

    # memes
    hero.memes.update(friendship=0.0, pride=0.0, wonder=1.0)
    honcho.memes.update(trust=0.0, worry=1.0, friendship=0.0)

    world.facts.update(
        hero=hero_cfg,
        honcho=honcho_cfg,
        mystery=mystery,
        setting=setting,
        tool=tool_cfg,
        lost=lost,
    )

    # story beats
    world.say(f"At {setting.place}, under a sky that looked {setting.sky}, there lived {hero_cfg.phrase}.")
    world.say(f"Near by stood {honcho_cfg.phrase}, the kind of honcho who could calm a stampede with one hoof or one cluck.")
    world.say(f"One morning, {mystery.missing} went missing, and the whole place hummed with mystery.")

    world.para()
    hero.memes["wonder"] += 1.0
    honcho.memes["worry"] += 0.5
    world.say(f"{hero_cfg.name} said the case had a tall-tale smell to it, the kind that made a rabbit's whiskers stand straight up.")
    world.say(f"{honcho_cfg.name} handed over {tool_cfg.phrase} and asked {hero_cfg.name} to look carefully, not hurriedly.")

    world.para()
    hero.meters["distance"] += 1.0
    hero.meters["clue"] += 1.0
    world.say(f"{hero_cfg.name} followed the {mystery.clue_kind} across {setting.surfaces[0]}, then across {setting.surfaces[1]}, as if the clue had legs of its own.")
    world.say(f"{hero_cfg.name} noticed the mark led toward {mystery.culprit}, which was swinging and swaying like it had a secret to tell.")
    world.say(f"That was when {hero_cfg.name} understood the mystery was not mean at all; it was only hiding in plain sight.")

    world.para()
    hero.memes["friendship"] += 1.0
    honcho.memes["trust"] += 1.0
    honcho.meters["worry"] = 0.0
    honcho.meters["relief"] += 1.0
    lost.meters["hidden"] = 0.0
    lost.meters["found"] = 1.0

    world.say(f"With a gentle tug and a clever little twist, {hero_cfg.name} and {honcho_cfg.name} freed {mystery.missing}.")
    world.say(f"{mystery.reveal_method.capitalize()}, and there it was all along: {mystery.ending_image}.")
    world.say(f"{honcho_cfg.name} laughed a big honcho laugh, and {hero_cfg.name} laughed too, because a mystery solved together feels brighter than a new penny.")

    world.facts["resolved"] = True
    world.facts["ending"] = mystery.ending_image
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h: Friend = f["hero"]
    c: Friend = f["honcho"]
    m: Mystery = f["mystery"]
    s: Setting = f["setting"]
    return [
        f"Write a tall-tale style story for young children about {h.phrase} and {c.phrase} at {s.place}, where they solve a mystery about {m.missing}.",
        f"Tell a warm friendship story in which {h.name} and {c.name} use a clue to solve the mystery of the missing {m.missing}.",
        f"Write a simple, funny mystery story with a lop-eared rabbit, a honcho, and a clue that leads to a surprising reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Friend = f["hero"]
    c: Friend = f["honcho"]
    m: Mystery = f["mystery"]
    s: Setting = f["setting"]
    t: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who solved the mystery of the missing {m.missing} at {s.place}?",
            answer=f"{h.name} and {c.name} solved it together. {h.name} was the lop-eared rabbit, and {c.name} was the honcho who helped keep the search calm.",
        ),
        QAItem(
            question=f"What clue did {h.name} follow to find {m.missing}?",
            answer=f"{h.name} followed the {m.clue_kind} and used {t.label} to look closely. That careful looking led right to the answer.",
        ),
        QAItem(
            question=f"What was the mystery really about?",
            answer=f"The mystery was that {m.missing} had not vanished forever; it had simply been caught or tucked near {m.culprit} until {h.name} and {c.name} found it.",
        ),
        QAItem(
            question=f"How did {h.name} and {c.name} feel at the end?",
            answer=f"They felt relieved and happy. Solving the mystery made their friendship stronger, and they ended the story laughing together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out a mystery.",
        ),
        QAItem(
            question="What does a honcho mean?",
            answer="A honcho is the boss or leader who helps make sure things get done.",
        ),
        QAItem(
            question="What does friendship do in a hard moment?",
            answer="Friendship helps people work together, stay calm, and solve problems more kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(setting=s, mystery=m, hero=h.id, honcho=c.id, tool="magnifier")
            for s in SETTINGS
            for m in MYSTERIES
            for h in LOPES
            for c in HONCHOS
            if h.id != c.id
        ]
        samples = [generate(p) for p in cur[: min(len(cur), max(args.n, 1))]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
