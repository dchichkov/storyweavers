#!/usr/bin/env python3
"""
A small whodunit storyworld about a puzzling leak, a plumb line, and a careful
fix that ends happily.

Seed premise:
- A child notices a mysterious drip.
- The family looks for clues in a few simple rooms.
- A plumb tool helps reveal the real cause.
- The ending is cautionary but warm: small leaks matter, and checking early
  keeps a bigger mess away.

The world is intentionally small and classical:
- one child, one grown-up helper, one problem object, one clue tool, one fix.
- state changes are physical (meters) and emotional (memes).
- dialogue and deduction drive the narrative.
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

ROOMS = {
    "kitchen": {
        "place": "the kitchen",
        "clue_places": {"sink", "floor"},
        "sound": "plink",
        "light": "bright",
    },
    "bathroom": {
        "place": "the bathroom",
        "clue_places": {"sink", "tub", "tile"},
        "sound": "drip",
        "light": "small and shiny",
    },
    "basement": {
        "place": "the basement",
        "clue_places": {"pipe", "floor"},
        "sound": "plip",
        "light": "dim",
    },
}

MYSTERIES = {
    "drip": {
        "id": "drip",
        "problem": "a little drip",
        "symptom": "water kept making a tiny spot on the floor",
        "risk": "it could turn into a bigger puddle",
        "mess": "wet",
    },
    "leak": {
        "id": "leak",
        "problem": "a sneaky leak",
        "symptom": "water kept sneaking out from a pipe",
        "risk": "it could spread and stain the floor",
        "mess": "wet",
    },
    "rattle": {
        "id": "rattle",
        "problem": "a rattling pipe",
        "symptom": "the pipe shook and tapped whenever water ran",
        "risk": "it might shake a joint loose",
        "mess": "noisy",
    },
}

TOOLS = {
    "plumb_line": {
        "id": "plumb_line",
        "label": "a plumb line",
        "phrase": "a thin plumb line with a little weight on the end",
        "use": "show what was straight",
        "helps": {"drip", "leak"},
        "clue": "it hung straight down and pointed to the loose joint",
    },
    "wrench": {
        "id": "wrench",
        "label": "a wrench",
        "phrase": "a small silver wrench",
        "use": "tighten the pipe joint",
        "helps": {"leak", "rattle"},
        "clue": "it fit the nut near the leak",
    },
    "towel": {
        "id": "towel",
        "label": "a towel",
        "phrase": "a thick dry towel",
        "use": "soak up the wet spot",
        "helps": {"drip", "leak"},
        "clue": "it kept the puddle from growing while they worked",
    },
}

CULPRITS = {
    "loose_nut": {
        "id": "loose_nut",
        "label": "a loose nut",
        "reveal": "the nut had worked itself loose and let water slip out",
        "fix": "tighten it",
    },
    "cracked_washer": {
        "id": "cracked_washer",
        "label": "a cracked washer",
        "reveal": "the washer had cracked, so the joint could not hold the water",
        "fix": "replace it",
    },
    "bent_pipe": {
        "id": "bent_pipe",
        "label": "a bent pipe",
        "reveal": "the pipe had bent just enough to make the joint wobble",
        "fix": "steady it",
    },
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Sam"]
ADULTS = ["Mom", "Dad", "Aunt Jo", "Uncle Ray", "Grandma", "Grandpa"]
TRAITS = ["curious", "careful", "brave", "quiet", "bright", "patient"]


# ---------------------------------------------------------------------------
# Dataclasses
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def _word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    room: str
    place: str
    clues: set[str] = field(default_factory=set)
    light: str = ""


@dataclass
class StoryParams:
    room: str
    mystery: str
    tool: str
    culprit: str
    name: str
    adult: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(room: str, mystery: str, tool: str, culprit: str) -> bool:
    setting = ROOMS[room]
    m = MYSTERIES[mystery]
    t = TOOLS[tool]
    c = CULPRITS[culprit]
    if mystery == "rattle" and tool == "plumb_line":
        return False
    if culprit == "bent_pipe" and tool == "towel":
        return False
    if mystery not in t["helps"]:
        return False
    if room == "kitchen" and culprit == "bent_pipe":
        return True
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for room in ROOMS:
        for mystery in MYSTERIES:
            for tool in TOOLS:
                for culprit in CULPRITS:
                    if valid_combo(room, mystery, tool, culprit):
                        out.append((room, mystery, tool, culprit))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room(kitchen).
room(bathroom).
room(basement).

mystery(drip).
mystery(leak).
mystery(rattle).

tool(plumb_line).
tool(wrench).
tool(towel).

culprit(loose_nut).
culprit(cracked_washer).
culprit(bent_pipe).

helps(plumb_line, drip).
helps(plumb_line, leak).
helps(wrench, leak).
helps(wrench, rattle).
helps(towel, drip).
helps(towel, leak).

invalid(rattle, plumb_line).
invalid(rattle, towel).
invalid(bent_pipe, towel).

valid(R, M, T, C) :- room(R), mystery(M), tool(T), culprit(C),
                     helps(T, M), not invalid(M, T).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room, data in ROOMS.items():
        lines.append(asp.fact("room", room))
        for clue in sorted(data["clue_places"]):
            lines.append(asp.fact("clue_place", room, clue))
    for mid, data in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("risk", mid, data["risk"]))
    for tid, data in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(data["helps"]):
            lines.append(asp.fact("helps", tid, m))
    for cid, data in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python gate.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, adult: Entity, mystery: dict) -> None:
    world.say(
        f"{child.id} was a {world.facts['trait']} little {child.type} who liked solving puzzles."
    )
    world.say(
        f"One evening, {child.id} heard a tiny {mystery['problem']} in {world.setting.place}."
    )


def clue_scene(world: World, child: Entity, adult: Entity, mystery: dict, tool: dict, culprit: dict) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f'"Did you hear that?" {child.id} asked. "{adult.id}, something is dripping."'
    )
    world.say(
        f'"Let us look carefully," {adult.id} said, and they followed the sound to the {world.setting.room}.'
    )
    world.say(
        f"The room was {world.setting.light}, and the sound went {world.setting.sound}, {world.setting.sound}, {world.setting.sound}."
    )
    world.say(
        f"{adult.id} held up {tool['phrase']}. \"This is a good clue,\" {adult.id} said. \"It can show what hangs straight.\""
    )
    world.say(
        f"{child.id} watched closely. \"So the mystery is not random,\" {child.id} said. \"Something is making the water slip.\""
    )
    world.say(
        f"They found that {culprit['label']} had caused trouble near the pipe."
    )


def tension_scene(world: World, child: Entity, adult: Entity, mystery: dict, tool: dict, culprit: dict) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    adult.memes["focus"] = adult.memes.get("focus", 0) + 1
    world.say(
        f'"Should we wait?" {child.id} asked. "{mystery["problem"]} looks small."'
    )
    world.say(
        f'"Small leaks can turn big," {adult.id} said. "{mystery["risk"]}."'
    )
    world.say(
        f"{child.id} nodded and brought a towel so the wet spot would not spread."
    )
    world.say(
        f"Then {adult.id} used {tool['label']} to {tool['use']}, and the clue pointed right at the problem."
    )
    world.say(
        f'"There!" {child.id} said. "{culprit["reveal"]}."'
    )


def resolution_scene(world: World, child: Entity, adult: Entity, mystery: dict, tool: dict, culprit: dict) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    adult.memes["joy"] = adult.memes.get("joy", 0) + 1
    world.say(
        f'"Now we know what did it," {adult.id} said. "We can {culprit["fix"]} it before the floor gets worse."'
    )
    world.say(
        f"They worked together, and the little drip stopped at last."
    )
    world.say(
        f"{child.id} smiled. \"The mystery is solved,\" {child.id} said. \"And next time, we will check tiny drips right away.\""
    )
    world.say(
        f"By bedtime, the floor was dry, the pipe was calm, and the room felt safe again."
    )


def tell(setting: Setting, mystery: dict, tool: dict, culprit: dict, child_name: str, adult_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type="adult"))
    world.facts.update(
        child=child,
        adult=adult,
        mystery=mystery,
        tool=tool,
        culprit=culprit,
        trait=trait,
    )
    introduce(world, child, adult, mystery)
    world.para()
    clue_scene(world, child, adult, mystery, tool, culprit)
    world.para()
    tension_scene(world, child, adult, mystery, tool, culprit)
    world.para()
    resolution_scene(world, child, adult, mystery, tool, culprit)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story about "{f["mystery"]["problem"]}" and a {f["tool"]["label"]}.',
        f'Tell a dialogue-driven mystery where {f["child"].id} and {f["adult"].id} investigate a leak in {world.setting.place}.',
        f'Write a cautionary, happy-ending story about a tiny plumbing problem being solved before it gets worse.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    mystery = f["mystery"]
    tool = f["tool"]
    culprit = f["culprit"]
    return [
        QAItem(
            question=f"What was the mystery in {world.setting.place}?",
            answer=f"It was {mystery['problem']}. {mystery['symptom'].capitalize()}.",
        ),
        QAItem(
            question=f"What clue tool did {adult.id} use to help solve the case?",
            answer=f"{adult.id} used {tool['phrase']} to help show what was wrong.",
        ),
        QAItem(
            question=f"Who seemed to be the real cause of the trouble?",
            answer=f"The real cause was {culprit['label']}, because {culprit['reveal']}.",
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=f"It ended happily: the drip stopped, the floor dried, and {child.id} learned to check small leaks right away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a plumb line do?",
            answer="A plumb line hangs straight down, so it helps people see whether something is truly vertical.",
        ),
        QAItem(
            question="Why should a small leak be fixed quickly?",
            answer="A small leak should be fixed quickly because it can grow into a bigger mess and damage the room.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a helpful detail that points toward the answer to the puzzle.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params, parsing, generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    mystery: str
    tool: str
    culprit: str
    name: str
    adult: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with dialogue, caution, and a happy ending.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)
              and (args.culprit is None or c[3] == args.culprit)]
    if not combos:
        raise StoryError("No valid mystery/tool/culprit combination matches the given options.")
    room, mystery, tool, culprit = rng.choice(sorted(combos))
    return StoryParams(
        room=room,
        mystery=mystery,
        tool=tool,
        culprit=culprit,
        name=args.name or rng.choice(NAMES),
        adult=args.adult or rng.choice(ADULTS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    setting = Setting(
        room=params.room,
        place=ROOMS[params.room]["place"],
        clues=set(ROOMS[params.room]["clue_places"]),
        light=ROOMS[params.room]["light"],
    )
    world = tell(setting, MYSTERIES[params.mystery], TOOLS[params.tool], CULPRITS[params.culprit],
                 params.name, params.adult, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
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


CURATED = [
    StoryParams(room="kitchen", mystery="drip", tool="plumb_line", culprit="loose_nut", name="Mia", adult="Mom", trait="curious"),
    StoryParams(room="bathroom", mystery="leak", tool="wrench", culprit="cracked_washer", name="Leo", adult="Dad", trait="careful"),
    StoryParams(room="basement", mystery="rattle", tool="wrench", culprit="bent_pipe", name="Nora", adult="Aunt Jo", trait="brave"),
]


def asp_verify_story() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify_story())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
