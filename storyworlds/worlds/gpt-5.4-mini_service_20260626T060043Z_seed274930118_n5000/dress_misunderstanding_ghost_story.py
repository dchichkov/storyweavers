#!/usr/bin/env python3
"""
storyworlds/worlds/dress_misunderstanding_ghost_story.py
=========================================================

A small ghost-story world about a child, a dress, and a misunderstanding.

Premise:
- A child finds a special dress near an old house or attic.
- A shy ghost seems to be haunting the dress.
- The child first misreads the ghost's behavior as spooky or possessive.

Turn:
- The ghost is not scary; it is trying to point out that the dress belongs to
  someone else, or that it needs one small repair before it can be worn.

Resolution:
- The child understands the ghost's message, helps fix or return the dress, and
  the haunting turns gentle.

This storyworld uses physical meters and emotional memes, and it includes an
inline ASP twin for the story validity gate.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    indoor: bool = True
    echoey: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Dress:
    id: str
    label: str
    phrase: str
    color: str
    age: str
    can_be_returned: bool = True
    can_be_repaired: bool = True


@dataclass
class Ghost:
    id: str
    label: str
    whisper: str
    haunting_reason: str
    gentle: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.spook_level: float = 0.0

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
        clone.spook_level = self.spook_level
        return clone


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.spook_level < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0
    out.append("A cold little shiver ran through the room.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    dress = world.get("dress")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    if ghost.memes.get("want_help", 0.0) < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confused"] = child.memes.get("confused", 0.0) + 1.0
    out.append(f"{child.id} thought {ghost.id} wanted to take the {dress.label} away.")
    return out


def _r_understanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes.get("confused", 0.0) < THRESHOLD:
        return out
    if world.facts.get("repair_done") or world.facts.get("return_done"):
        sig = ("understanding",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
            child.memes["fear"] = 0.0
            ghost.memes["relief"] = ghost.memes.get("relief", 0.0) + 1.0
            out.append(f"Then {child.id} saw that {ghost.id} was asking for help, not haunting.")
    return out


CAUSAL_RULES = [_r_spook, _r_misunderstanding, _r_understanding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "old_house": Setting(place="the old house", indoor=True, echoey=True, affords={"visit_attic", "find_dress"}),
    "attic": Setting(place="the attic", indoor=True, echoey=True, affords={"find_dress", "repair_dress"}),
    "garden_gate": Setting(place="the garden gate", indoor=False, echoey=False, affords={"return_dress"}),
}

DRESSES = {
    "blue_dress": Dress(
        id="blue_dress",
        label="blue dress",
        phrase="a soft blue dress with a silver ribbon",
        color="blue",
        age="old",
    ),
    "white_dress": Dress(
        id="white_dress",
        label="white dress",
        phrase="a white dress with lace sleeves",
        color="white",
        age="old",
    ),
    "red_dress": Dress(
        id="red_dress",
        label="red dress",
        phrase="a bright red dress with tiny buttons",
        color="red",
        age="new",
    ),
}

GHOSTS = {
    "lantern_ghost": Ghost(
        id="lantern_ghost",
        label="lantern ghost",
        whisper="follow the light",
        haunting_reason="the dress must be fixed before it can be worn",
    ),
    "attic_ghost": Ghost(
        id="attic_ghost",
        label="attic ghost",
        whisper="that dress belongs to someone else",
        haunting_reason="the dress should be returned to its owner",
    ),
}

NAMES = ["Mia", "Nora", "Leah", "Ivy", "Ruby", "Ava", "Finn", "Theo", "Ben", "Leo"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "brave", "quiet", "gentle", "shy", "careful"]


@dataclass
class StoryParams:
    place: str
    dress: str
    ghost: str
    name: str
    gender: str
    parent: str
    trait: str
    action: str
    seed: Optional[int] = None


ACTIONS = {
    "repair_dress": "repair the torn seam",
    "return_dress": "return the dress",
    "find_dress": "find the dress",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story about a dress and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--dress", choices=DRESSES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--action", choices=ACTIONS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.dress not in DRESSES:
        raise StoryError("Unknown dress.")
    if params.ghost not in GHOSTS:
        raise StoryError("Unknown ghost.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.action == "return_dress" and params.place == "attic":
        raise StoryError("Returning the dress makes more sense at the garden gate than in the attic.")
    if params.action == "repair_dress" and params.place == "garden_gate":
        raise StoryError("Repairing the dress makes more sense in the attic or old house.")
    if params.action == "find_dress" and params.place == "garden_gate":
        raise StoryError("Finding the dress makes more sense in the old house or attic.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    dress = args.dress or rng.choice(list(DRESSES))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice([n for n in NAMES if (gender == "girl") == (n in {"Mia", "Nora", "Leah", "Ivy", "Ruby", "Ava"})] or NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    action = args.action or rng.choice(list(ACTIONS))
    params = StoryParams(place=place, dress=dress, ghost=ghost, name=name, gender=gender, parent=parent, trait=trait, action=action)
    reasonableness_gate(params)
    return params


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    dress_cfg = DRESSES[params.dress]
    dress = world.add(Entity(
        id="dress", kind="thing", type="dress", label=dress_cfg.label,
        phrase=dress_cfg.phrase, owner="unknown", caretaker="parent", worn_by=None
    ))
    ghost_cfg = GHOSTS[params.ghost]
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost_cfg.label))
    world.facts.update(
        child=child, parent=parent, dress=dress, ghost=ghost,
        params=params, dress_cfg=dress_cfg, ghost_cfg=ghost_cfg
    )
    return world


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    child = world.get("child")
    parent = world.get("parent")
    dress = world.get("dress")
    ghost = world.get("ghost")
    dress_cfg = world.facts["dress_cfg"]
    ghost_cfg = world.facts["ghost_cfg"]

    child.memes["wonder"] = 1.0
    ghost.memes["want_help"] = 1.0

    world.say(f"{child.label} and {parent.pronoun('possessive')} {parent.type} came to {world.setting.place}.")
    world.say(f"Inside, they found {dress_cfg.phrase}; it looked like it had been waiting in the dark for years.")
    world.say(f"Then {ghost.label} floated out, pale and quiet, and whispered, “{ghost_cfg.whisper}.”")

    world.para()
    child.memes["fear"] = 1.0
    world.spook_level = 1.0
    propagate(world, narrate=True)
    world.say(f"{child.label} backed up and clutched {parent.pronoun('possessive')} sleeve.")
    world.say(f"It looked like the ghost was trying to claim the {dress.label}.")

    world.para()
    if params.action == "repair_dress":
        world.say(f"But the ghost pointed at a torn seam and gently tugged the thread loose.")
        world.facts["repair_done"] = True
        world.say(f"{child.label} found a needle and helped {parent.label} {ACTIONS[params.action]}.")
        world.say(f"When the last stitch tied off, the {dress.label} stopped fluttering like a worried flag.")
    elif params.action == "return_dress":
        world.say(f"But the ghost pointed past the house, toward a small gate and a little lantern on the path.")
        world.facts["return_done"] = True
        world.say(f"{child.label} carried the {dress.label} to the garden gate and left it where the light could find it.")
        world.say(f"A note tied to the ribbon showed it had once belonged to a lonely doll in the next yard.")
    else:
        world.say(f"But the ghost pointed to a dusty trunk in the attic and tapped the lid twice.")
        world.facts["repair_done"] = True
        world.say(f"{child.label} opened the trunk and found ribbon, thread, and a tiny card with a name on it.")
        world.say(f"The card made the mystery plain: the dress was not haunted by anger; it just needed to be found properly.")

    propagate(world, narrate=True)
    world.para()
    if world.facts.get("repair_done"):
        world.say(f"After that, {child.label} smiled at the ghost and the room felt warm again.")
        world.say(f"The {dress.label} was neat and still, and the ghost's whisper sounded almost like a song.")
    if world.facts.get("return_done"):
        world.say(f"After that, {child.label} understood the ghost's quiet warning.")
        world.say(f"The {dress.label} was returned safely, and the garden gate no longer felt spooky at all.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    dress = world.facts["dress_cfg"]
    ghost = world.facts["ghost_cfg"]
    return [
        f"Write a gentle ghost story for young children about {p.name} and a {dress.color} dress.",
        f"Tell a story where a child thinks {ghost.label} is frightening, but the ghost is actually helping.",
        f"Create a short mystery story about a dress, a whisper, and a misunderstanding in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    dress = world.facts["dress"]
    ghost = world.facts["ghost"]
    qas = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.label}, {parent.pronoun('possessive')} {parent.type}, and {ghost.label} near the {dress.label}.",
        ),
        QAItem(
            question=f"What did {child.label} first think the ghost wanted?",
            answer=f"{child.label} first thought {ghost.label} wanted to take the {dress.label} away.",
        ),
        QAItem(
            question=f"What was the ghost really trying to do?",
            answer=f"The ghost was really trying to help with the {dress.label}, not frighten anyone.",
        ),
    ]
    if world.facts.get("repair_done"):
        qas.append(
            QAItem(
                question=f"How did the misunderstanding end?",
                answer=f"It ended when {child.label} helped repair the {dress.label} and saw that the ghost only wanted help.",
            )
        )
    if world.facts.get("return_done"):
        qas.append(
            QAItem(
                question=f"How did {child.label} fix the problem?",
                answer=f"{child.label} fixed the problem by returning the {dress.label} to the right place and understanding the ghost's warning.",
            )
        )
    return qas


def world_qa(world: World) -> list[QAItem]:
    dress = world.facts["dress_cfg"]
    ghost = world.facts["ghost_cfg"]
    return [
        QAItem(
            question="What is a dress?",
            answer="A dress is a piece of clothing that someone can wear, and it can be soft, pretty, or special for an event.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky-looking character that can also be shy, sad, or helpful.",
        ),
        QAItem(
            question="Why can a misunderstanding be part of a mystery?",
            answer="A misunderstanding can make a mystery because someone sees something strange and guesses the wrong reason before learning the truth.",
        ),
        QAItem(
            question=f"Why might the {dress.label} matter in this story?",
            answer=f"The {dress.label} matters because it is the important thing the child notices, and the ghost's message is connected to it.",
        ),
        QAItem(
            question=f"Why is {ghost.label} not actually scary here?",
            answer=f"{ghost.label} is not actually scary because it is trying to help, and the strange behavior is only a misunderstanding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_house", dress="blue_dress", ghost="attic_ghost", name="Mia", gender="girl", parent="mother", trait="curious", action="find_dress"),
    StoryParams(place="attic", dress="white_dress", ghost="lantern_ghost", name="Theo", gender="boy", parent="father", trait="careful", action="repair_dress"),
    StoryParams(place="garden_gate", dress="red_dress", ghost="attic_ghost", name="Ruby", gender="girl", parent="mother", trait="gentle", action="return_dress"),
]


ASP_RULES = r"""
% A dress can be the center of a mystery when a ghost and a child both care about it.
misunderstanding(C,D,G) :- child(C), dress(D), ghost(G), ghost_wants_help(G), child_fears(C).

% If the dress is repaired or returned, the misunderstanding clears.
resolved(C,D,G) :- misunderstanding(C,D,G), fixed(D).
resolved(C,D,G) :- misunderstanding(C,D,G), returned(D).

#show misunderstanding/3.
#show resolved/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for did in DRESSES:
        lines.append(asp.fact("dress", did))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("child_fears", "child"))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost_wants_help", gid))
    lines.append(asp.fact("fixed", "blue_dress"))
    lines.append(asp.fact("returned", "red_dress"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/3.\n#show resolved/3."))
    atoms = set()
    for sym in model:
        if sym.name in {"misunderstanding", "resolved"}:
            atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    python_like = {
        ("misunderstanding", ("child", "blue_dress", "attic_ghost")),
        ("misunderstanding", ("child", "white_dress", "lantern_ghost")),
        ("misunderstanding", ("child", "red_dress", "attic_ghost")),
        ("resolved", ("child", "blue_dress", "attic_ghost")),
        ("resolved", ("child", "red_dress", "attic_ghost")),
    }
    if atoms == python_like:
        print("OK: ASP parity check passed.")
        return 0
    print("Mismatch in ASP parity.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python_like))
    return 1


def asp_validity() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/3.\n#show resolved/3."))
    return sorted({tuple(str(a) for a in sym.arguments) for sym in model if sym.name == "misunderstanding"})


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show misunderstanding/3.\n#show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/3.\n#show resolved/3."))
        print(f"{len(model)} shown atoms")
        for sym in model:
            print(sym)
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.dress}, {p.ghost})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
