#!/usr/bin/env python3
"""
A small whodunit-style story world: a flower vanishes, a laser misfires, and a
careful clue trail reveals that disability is not a punchline but part of the
moral value of the tale.
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
# Model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    reveals: str


@dataclass
class Puzzle:
    id: str
    missing: str
    culprit: str
    method: str
    moral: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "museum": Setting(place="the old museum", afford={"laser", "flower", "whodunit"}),
    "garden": Setting(place="the moonlit garden", afford={"flower", "whodunit"}),
    "lab": Setting(place="the quiet science lab", afford={"laser", "whodunit"}),
}

CHARACTER_TYPES = ["girl", "boy", "woman", "man"]
NAMES = {
    "girl": ["Mina", "Ada", "June", "Ivy"],
    "boy": ["Noah", "Eli", "Theo", "Finn"],
    "woman": ["Dr. Reyes", "Nora", "Marta", "Iris"],
    "man": ["Mr. Lane", "Owen", "Arlo", "Basil"],
}

PREFERRED_NAMES = ["Mina", "Ada", "Noah", "Eli", "Dr. Reyes", "Mr. Lane"]

PLANTS = {
    "flower": "a tiny blue flower in a glass vase",
    "orchid": "a white orchid in a clay pot",
}

DEVICES = {
    "laser": "a small red laser pointer",
}

CLUES = {
    "flower": [
        Clue("soil", "There was a pinch of wet soil on the table.", "garden"),
        Clue("glass", "A little shard of glass glittered near the base.", "vase"),
    ],
    "laser": [
        Clue("dot", "A red dot winked on the wall and then vanished.", "laser"),
        Clue("battery", "The laser pointer had a loose battery cap.", "device"),
    ],
    "disability": [
        Clue("ramp", "A small ramp made the side entrance easy to use.", "respect"),
        Clue("spoken", "Everyone used clear words and waited for replies.", "care"),
    ],
}

KNOWLEDGE = {
    "flower": (
        "What is a flower?",
        "A flower is the part of a plant that often has bright petals and can grow into seeds later.",
    ),
    "laser": (
        "What is a laser pointer?",
        "A laser pointer makes a tiny bright dot of light that people can move around for a moment.",
    ),
    "disability": (
        "What does disability mean?",
        "Disability means a person may use different ways or tools to do things, and those ways deserve respect.",
    ),
    "moral value": (
        "What is moral value?",
        "Moral value means choosing what is fair, kind, and honest, even when the answer is surprising.",
    ),
}

GENDERED_NAMES = {
    "girl": NAMES["girl"],
    "boy": NAMES["boy"],
    "woman": NAMES["woman"],
    "man": NAMES["man"],
}

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = "museum"
    seed: Optional[int] = None
    suspect: Optional[str] = None
    victim: Optional[str] = None


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    if "whodunit" not in setting.afford:
        raise StoryError("This setting cannot host a mystery.")
    world = World(setting)

    detective = world.add(Entity(id="detective", kind="character", type="woman", label="Detective Nora"))
    helper = world.add(Entity(id="helper", kind="character", type="boy", label="Eli"))
    caretaker = world.add(Entity(id="caretaker", kind="character", type="man", label="Mr. Lane"))

    victim_key = params.victim or "flower"
    if victim_key not in PLANTS:
        raise StoryError("Unknown victim.")
    victim = world.add(Entity(
        id="victim",
        type="flower",
        label="flower",
        phrase=PLANTS[victim_key],
        owner="museum",
        caretaker="caretaker",
        location="display table",
    ))

    culprit_key = params.suspect or "laser"
    if culprit_key not in DEVICES:
        raise StoryError("Unknown suspect.")
    culprit = world.add(Entity(
        id="culprit",
        type="device",
        label="laser pointer",
        phrase=DEVICES[culprit_key],
        location="desk drawer",
        suspicious=True,
    ))

    visitor = world.add(Entity(
        id="visitor",
        kind="character",
        type="girl",
        label="Mina",
    ))

    # Give the world a disability-related presence and normal, respectful treatment.
    ramp = world.add(Entity(id="ramp", type="thing", label="ramp", phrase="a small ramp", location="side door"))
    wheelchair_user = world.add(Entity(
        id="guest",
        kind="character",
        type="woman",
        label="Dr. Reyes",
    ))

    # Setup: a calm room with a flower, a laser, and a surprise.
    world.say(f"At {world.setting.place}, Detective Nora noticed something strange on the display table.")
    world.say(f"A tiny blue flower had been moved, and the room felt full of surprise.")
    world.say("The museum had quiet rules, clear signs, and a side entrance with a ramp, so everyone could come in comfortably.")
    world.say("Dr. Reyes arrived through the ramped entrance, and Mina kept close so she would not miss a clue.")

    # Middle: clues and suspicion.
    world.say("Eli pointed at the wall. 'Look,' he said, 'a little red dot was there a moment ago.'")
    world.say("Nora checked the desk drawer and found a small laser pointer with a loose battery cap.")
    world.say("Near the vase she found wet soil, which meant the flower had been disturbed by a careful hand or an accidental bump.")
    world.say("No one laughed at Dr. Reyes for using a ramp. Instead, Nora listened when she said the flower had been kept low on purpose, so visitors using different bodies could still enjoy it.")

    # Turn: the detective understands the method.
    culprit.meters["used"] = 1
    victim.meters["moved"] = 1
    visitor.memes["surprise"] = 1
    detective.memes["focus"] = 1

    world.say("Nora matched the clues: the laser dot had distracted Mina, the loose cap had flicked open, and the flower had been knocked sideways.")
    world.say("It was not a cruel mystery after all, just a messy surprise with a simple cause.")
    world.say("Mina looked worried, but Nora reminded her that a mistake is not the same as being bad.")

    # Resolution and moral value.
    world.say("Nora returned the flower to its vase and tightened the laser cap.")
    world.say("Then she said, 'The honest answer matters, and so does kindness. We solve the puzzle without shaming anyone.'")
    world.say("Dr. Reyes smiled because the ramp stayed in place, the flower stood bright again, and the room felt fair.")
    world.say("Mina took a slow breath and felt proud that the truth could be both surprising and gentle.")

    world.facts.update(
        detective=detective,
        helper=helper,
        caretaker=caretaker,
        victim=victim,
        culprit=culprit,
        visitor=visitor,
        guest=wheelchair_user,
        ramp=ramp,
        setting=setting,
        culprit_method="laser distraction",
        moral="Kindness and honesty matter more than blame.",
        surprise=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    victim = f["victim"]
    culprit = f["culprit"]
    guest = f["guest"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer="It was about a missing flower, a strange laser dot, and the question of what really happened in the museum.",
        ),
        QAItem(
            question="How did the detective solve the surprise?",
            answer="Detective Nora followed the clues, noticed the loose laser cap and the wet soil, and realized the laser had caused the flower to be moved.",
        ),
        QAItem(
            question="Why was the ramp important in the story?",
            answer="The ramp made the side entrance easy to use, so Dr. Reyes could enter comfortably and everyone could focus on the mystery instead of barriers.",
        ),
        QAItem(
            question="What moral value did the detective teach?",
            answer="She taught that honesty and kindness matter more than blame, especially when a mistake turns into a surprising puzzle.",
        ),
        QAItem(
            question="What happened to the flower at the end?",
            answer="The flower was put back in its vase, and the room looked calm and bright again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE.values()]


def prompts(world: World) -> list[str]:
    return [
        "Write a short whodunit story for young children about a flower, a laser, and a surprising clue trail.",
        "Tell a gentle mystery where the answer is fair, the surprise is real, and the moral value is kindness.",
        "Write a child-friendly detective story that includes disability respectfully and ends with the truth.",
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(museum).
setting(garden).
setting(lab).

affords(museum,whodunit).
affords(museum,flower).
affords(museum,laser).
affords(garden,whodunit).
affords(garden,flower).
affords(lab,whodunit).
affords(lab,laser).

topic(flower).
topic(laser).
topic(disability).
topic(moral_value).

clue(flower,soil).
clue(flower,glass).
clue(laser,dot).
clue(laser,battery).
clue(disability,ramp).
clue(disability,spoken).

mystery(S,T) :- affords(S,whodunit), topic(T).
surprise_story(S) :- mystery(S,flower), mystery(S,laser), mystery(S,disability), topic(moral_value).
#show mystery/2.
#show surprise_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for t in ("flower", "laser", "disability", "moral_value"):
        lines.append(asp.fact("topic", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise_story/1."))
    asp_atoms = set(asp.atoms(model, "surprise_story"))
    py_atoms = {("museum",)} if "whodunit" in SETTINGS["museum"].afford else set()
    if asp_atoms == py_atoms:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_atoms))
    print("Python:", sorted(py_atoms))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit story world.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    if "whodunit" not in SETTINGS[setting].afford:
        raise StoryError("That setting cannot hold the mystery.")
    return StoryParams(setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.suspicious:
            bits.append("suspicious=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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
        print(asp_program("#show surprise_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/2.\n#show surprise_story/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(setting=s)) for s in sorted(SETTINGS)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
