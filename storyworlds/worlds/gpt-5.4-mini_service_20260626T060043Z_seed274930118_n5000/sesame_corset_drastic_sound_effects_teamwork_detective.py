#!/usr/bin/env python3
"""
Storyworld: sesame corset drastic sound effects teamwork detective
===============================================================

A small detective-story world about a child sleuth, a strange sound, a
stubborn clue, and a teamwork fix. The seed words are woven into the world
model so they shape the premise, tension, turn, and ending.

Premise:
- A young detective hears a curious sound effect in a place full of props.
- The clue leads to a sesame stain on a corset.
- The case becomes drastic when the wrong costume is needed for a show.

Turn:
- The detective and a helper work together to trace the sound, find the
  missing piece, and restore the costume before the show starts.

Resolution:
- The clue is solved by teamwork, the corset is cleaned and repaired, and the
  final sound is a cheerful applause-like effect instead of a mystery noise.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
@dataclass
class Setting:
    place: str
    indoors: bool
    detail: str


@dataclass
class Sound:
    id: str
    onomatopoeia: str
    source: str
    clue: str
    risk: str
    mood: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: str
    covers: set[str] = field(default_factory=set)
    protective: bool = False


SETTINGS = {
    "the costume attic": Setting(
        place="the costume attic",
        indoors=True,
        detail="Tall racks, old masks, and hanging curtains made the room feel like a tiny theater.",
    ),
    "the backstage room": Setting(
        place="the backstage room",
        indoors=True,
        detail="Boxes of props sat beside a long mirror with yellow tape on the floor.",
    ),
    "the museum storeroom": Setting(
        place="the museum storeroom",
        indoors=True,
        detail="Dusty shelves held labeled boxes, lamps, and cloth covers over careful displays.",
    ),
}

SOUNDS = {
    "clatter": Sound(
        id="clatter",
        onomatopoeia="clatter-clink",
        source="a dropped prop tray",
        clue="a sesame seed trail on the floor",
        risk="the noise could mean the wrong costume piece got moved",
        mood="busy",
    ),
    "whisper": Sound(
        id="whisper",
        onomatopoeia="shhh-shhh",
        source="a hidden curtain cord",
        clue="a tiny thread snagged on a hook",
        risk="the quiet sound could hide a missing item",
        mood="secret",
    ),
    "boom": Sound(
        id="boom",
        onomatopoeia="boom-pop",
        source="a stage effect box",
        clue="a torn label on a costume crate",
        risk="the sudden noise made everyone think something drastic happened",
        mood="drastic",
    ),
}

PRIZES = {
    "corset": Prize(
        id="corset",
        label="corset",
        phrase="a satin corset with silver laces",
        region="torso",
    ),
    "hat": Prize(
        id="hat",
        label="hat",
        phrase="a round detective hat",
        region="head",
    ),
    "gloves": Prize(
        id="gloves",
        label="gloves",
        phrase="soft white gloves",
        region="hands",
        plural=True,
    ),
    "vest": Prize(
        id="vest",
        label="vest",
        phrase="a neat black vest",
        region="torso",
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a bright magnifying glass",
        helps_with="finding tiny clues",
    ),
    "brush": Tool(
        id="brush",
        label="soft brush",
        phrase="a soft brush for dust",
        helps_with="cleaning delicate fabric",
    ),
    "cloth": Tool(
        id="cloth",
        label="clean cloth",
        phrase="a clean cloth",
        helps_with="wiping away stains",
    ),
    "tape": Tool(
        id="tape",
        label="repair tape",
        phrase="repair tape",
        helps_with="mending a torn seam",
        protective=True,
    ),
    "apron": Tool(
        id="apron",
        label="protective apron",
        phrase="a protective apron",
        helps_with="keeping clothes clean during work",
        covers={"torso"},
        protective=True,
    ),
}

CHARACTER_NAMES = ["Maya", "Noah", "Tessa", "Leo", "Ivy", "Owen"]
HELPER_NAMES = ["Nina", "Eli", "Rosa", "Jude", "Ana", "Finn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    sound: str
    prize: str
    detective_name: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin / facts
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk if the sound source clues point to a place where it can be
% disturbed or stained by the clue trail.
at_risk(S, P) :- sound(S), prize(P), risk_tag(S, P).

% A tool is a reasonable fix if it helps with the specific problem and protects
% the region involved.
good_tool(T, P) :- tool(T), prize(P), tool_help(T, P).

% A story is valid when the setup includes at-risk prize + a matching tool.
valid_story(Set, S, P, T) :- setting(Set), sound(S), prize(P), tool(T),
                            at_risk(S, P), good_tool(T, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("source", sid, s.source))
        lines.append(asp.fact("clue", sid, s.clue))
        lines.append(asp.fact("risk_tag", sid, "corset"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.protective:
            lines.append(asp.fact("protective", tid))
        if t.label == "soft brush":
            lines.append(asp.fact("tool_help", tid, "corset"))
        elif t.label == "clean cloth":
            lines.append(asp.fact("tool_help", tid, "corset"))
        elif t.label == "repair tape":
            lines.append(asp.fact("tool_help", tid, "corset"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python reasonableness ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python combos.")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for sound in SOUNDS.values():
            for prize in PRIZES.values():
                if prize.id != "corset":
                    continue
                combos.append((setting, sound.id, prize.id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def choose_tool() -> Tool:
    return TOOLS["cloth"]


def setting_text(world: World) -> str:
    return SETTINGS[world.setting].detail


def story_intro(world: World, detective: Entity, helper: Entity, prize: Entity, sound: Sound) -> None:
    world.say(
        f"{detective.id} was a young detective who loved quiet clues, careful notes, and big questions."
    )
    world.say(
        f"{helper.id} liked teamwork and never missed a chance to carry a flashlight or hold the notebook."
    )
    world.say(
        f"Together they were looking for {prize.phrase} when they heard {sound.onomatopoeia} near {world.setting}."
    )


def sound_turn(world: World, detective: Entity, prize: Entity, sound: Sound) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    world.say(setting_text(world))
    world.say(
        f"The sound said {sound.onomatopoeia}, and it made the case feel {sound.mood}."
    )
    world.say(
        f"{sound.risk.capitalize()}, so {detective.id} bent down and followed {sound.clue}."
    )


def drastic_moment(world: World, detective: Entity, prize: Entity, sound: Sound) -> None:
    detective.memes["alarm"] = detective.memes.get("alarm", 0) + 1
    prize.meters["dirty"] = prize.meters.get("dirty", 0) + 1
    world.say(
        f"Then the detective found the problem: sesame crumbs had stuck to the {prize.label}, making the clue feel drastic."
    )
    world.say(
        f"The {prize.label} was not ruined forever, but the stain had to be handled carefully."
    )


def teamwork_fix(world: World, detective: Entity, helper: Entity, prize: Entity, tool: Tool) -> None:
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0) + 1
    world.say(
        f"{detective.id} held the magnifying glass while {helper.id} used {tool.phrase} to clean the stain."
    )
    world.say(
        f"Then they used repair tape on the loose seam, because teamwork could do what one pair of hands could not."
    )
    world.say(
        f"At last, the {prize.label} looked neat again, and the clue trail led straight to the missing costume box."
    )


def ending_image(world: World, detective: Entity, helper: Entity, prize: Entity) -> None:
    detective.memes["pride"] = detective.memes.get("pride", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.say(
        f"When the show began, the loudest sound was applause, not mystery."
    )
    world.say(
        f"{detective.id} and {helper.id} smiled beside the clean {prize.label}, knowing the case was solved together."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(setting=params.setting)
    detective = world.add(Entity(id=params.detective_name, kind="character", type="girl"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="boy"))
    prize = world.add(Entity(
        id=params.prize,
        type=params.prize,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        region=PRIZES[params.prize].region,
    ))
    sound = SOUNDS[params.sound]

    world.facts.update(
        detective=detective,
        helper=helper,
        prize=prize,
        sound=sound,
        tool=choose_tool(),
        setting=params.setting,
    )

    story_intro(world, detective, helper, prize, sound)
    world.para()
    sound_turn(world, detective, prize, sound)
    drastic_moment(world, detective, prize, sound)
    world.para()
    teamwork_fix(world, detective, helper, prize, choose_tool())
    ending_image(world, detective, helper, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prize = f["prize"]
    sound = f["sound"]
    setting = f["setting"]
    return [
        f"Write a short detective story for a child where a strange {sound.onomatopoeia} leads to a clue about a {prize.label}.",
        f"Tell a teamwork story set in {setting} that includes sesame crumbs, a corset, and a drastic problem.",
        f"Write a gentle mystery where two helpers solve a costume problem by following a sound effect and working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    prize = f["prize"]
    sound = f["sound"]
    return [
        QAItem(
            question=f"Who solved the case in the story?",
            answer=f"{detective.id} and {helper.id} solved it together by using teamwork.",
        ),
        QAItem(
            question=f"What sound effect started the mystery?",
            answer=f"The mystery started with the sound {sound.onomatopoeia}.",
        ),
        QAItem(
            question=f"What costume item had the sesame clue on it?",
            answer=f"The sesame clue was stuck on the {prize.label}.",
        ),
        QAItem(
            question=f"How did they fix the drastic problem?",
            answer=f"They cleaned the stain, repaired the seam, and worked together until the {prize.label} looked neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sesame?",
            answer="Sesame is a tiny seed that can be sprinkled on food or fall into little crumbs.",
        ),
        QAItem(
            question="What is a corset?",
            answer="A corset is a fitted piece of clothing that supports the torso and can be part of a costume.",
        ),
        QAItem(
            question="What does drastic mean?",
            answer="Drastic means very sudden, strong, or extreme.",
        ),
        QAItem(
            question="Why do detectives use magnifying glasses?",
            answer="Detectives use magnifying glasses to look closely at tiny clues they might miss with their eyes alone.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because people can do more when they share jobs and help each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with sesame, corset, drastic sounds, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--sound", choices=SOUNDS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.prize and args.prize != "corset":
        raise StoryError("This world only tells stories where the corset is the clue-bearing costume piece.")
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    sound = args.sound or rng.choice(list(SOUNDS.keys()))
    prize = "corset"
    detective_name = args.name or rng.choice(CHARACTER_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, sound=sound, prize=prize, detective_name=detective_name, helper_name=helper_name)


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


CURATED = [
    StoryParams(setting="the costume attic", sound="clatter", prize="corset", detective_name="Maya", helper_name="Nina"),
    StoryParams(setting="the backstage room", sound="whisper", prize="corset", detective_name="Leo", helper_name="Rosa"),
    StoryParams(setting="the museum storeroom", sound="boom", prize="corset", detective_name="Ivy", helper_name="Jude"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} ASP-compatible stories:")
        for row in triples:
            print("  ", row)
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
            header = f"### {p.detective_name}: {p.sound} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
