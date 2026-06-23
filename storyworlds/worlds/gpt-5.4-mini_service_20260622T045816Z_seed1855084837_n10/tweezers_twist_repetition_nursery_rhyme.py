#!/usr/bin/env python3
"""
storyworlds/worlds/tweezers_twist_repetition_nursery_rhyme.py
==============================================================

A tiny storyworld for a nursery-rhyme style tale about tweezers, a small twist,
and a gentle repeated refrain.

Premise:
- A child, a little pet, and a tiny problem.
- Tweezers are the helpful tool.
- The twist is that the child first wants to use the tweezers for a shiny trinket,
  but they are actually needed to remove a tiny thorn from a paw.
- Repetition is woven into the narration with a refrain that changes as the
  world changes.

This file is standalone and uses only stdlib plus the shared storyworld result
and ASP helper modules.
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

# Robust import path discovery: walk upward until we find storyworlds/results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_SCAN = _HERE
while True:
    if os.path.exists(os.path.join(_SCAN, "results.py")):
        if _SCAN not in sys.path:
            sys.path.insert(0, _SCAN)
        break
    parent = os.path.dirname(_SCAN)
    if parent == _SCAN:
        break
    _SCAN = parent

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
    held_by: Optional[str] = None
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    parent_type: str
    pet_kind: str
    problem: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affordances={"tweezers"}),
    "playroom": Setting(place="the playroom", indoors=True, affordances={"tweezers"}),
    "windowseat": Setting(place="the window seat", indoors=True, affordances={"tweezers"}),
}

CHILD_NAMES = ["Mia", "Nora", "Lily", "Toby", "Finn", "Eli"]
PETS = {
    "kitten": ("kitten", "a tiny kitten", "paw"),
    "puppy": ("puppy", "a fluffy puppy", "paw"),
    "mouse": ("mouse", "a little mouse", "paw"),
}

PROBLEMS = {
    "thorn": {
        "label": "a tiny thorn",
        "phrase": "a tiny thorn in the paw",
        "risk": "hurts the paw",
        "reveal": "the paw had a tiny thorn",
    },
    "splinter": {
        "label": "a small splinter",
        "phrase": "a small splinter in the paw",
        "risk": "makes the paw sore",
        "reveal": "the paw had a small splinter",
    },
}

TWEEZERS = {
    "tweezers": {
        "label": "tweezers",
        "phrase": "a pair of tweezers",
        "use": "lift out the little thorn",
        "shine": "glinted like a silver fish",
    }
}

GENTLE_ACTIONS = {
    "nest": "carefully make a nest from a soft cloth",
    "snack": "bring a crumbly snack",
    "song": "sing a small sleepy song",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PETS:
            for prob in PROBLEMS:
                combos.append((s, p, prob))
    return combos


def _pick_name(rng: random.Random, child_type: str) -> str:
    return rng.choice(CHILD_NAMES)


def _article(phrase: str) -> str:
    return "an" if phrase[0].lower() in "aeiou" else "a"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    pet_key = params.pet_kind
    pet_type, pet_phrase, paw = PETS[pet_key]
    problem = PROBLEMS[params.problem]

    world = World(setting)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        label=params.child_name,
        phrase=params.child_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        phrase="the parent",
    ))
    pet = world.add(Entity(
        id="Pet",
        kind="character",
        type=pet_type,
        label=pet_type,
        phrase=pet_phrase,
        owner=child.id,
        attrs={"paw": paw},
    ))
    tool = world.add(Entity(
        id="Tweezers",
        type="tool",
        label="tweezers",
        phrase="a pair of tweezers",
        held_by=parent.id,
        tags={"tweezers"},
    ))
    trinket = world.add(Entity(
        id="Bead",
        type="thing",
        label="a shiny bead",
        phrase="a shiny bead",
        owner=child.id,
        tags={"shiny"},
    ))
    thorn = world.add(Entity(
        id="Problem",
        type="thing",
        label=problem["label"],
        phrase=problem["phrase"],
        owner=pet.id,
        tags={params.problem},
    ))
    world.facts.update(
        child=child,
        parent=parent,
        pet=pet,
        tool=tool,
        trinket=trinket,
        thorn=thorn,
        problem=problem,
    )

    child.memes["curiosity"] += 1
    child.memes["love"] += 1
    pet.memes["unease"] += 1
    thorn.meters["stuck"] += 1
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    pet: Entity = f["pet"]
    tool: Entity = f["tool"]
    trinket: Entity = f["trinket"]
    thorn: Entity = f["thorn"]
    problem = f["problem"]

    world.say(f"{child.id} lived in {world.setting.place}, where soft rugs lay and little lamps glowed.")
    world.say(f"{child.id} loved {pet.phrase}, and {pet.id} loved curling up near {child.id}.")
    world.say(f"One day {child.id} saw {trinket.phrase} sparkle on the floor, and {child.id} chirped, 'Mine, mine, mine!'")
    world.say(f"{child.id} reached for {tool.label}, because {tool.phrase} {tool.attrs.get('shine', 'looked bright')}.")

    world.para()
    world.say(f"\"Not for beads,\" said {parent.label}. \"Tweezers are for tiny troubles.\"")
    world.say(f"{child.id} paused, then paused again. The nursery seemed still, so still.")
    world.say(f"\"Tweezers, tweezers, gentle tweezers,\" sang {child.id}, and the little song went round and round.")

    world.para()
    child.memes["desire"] += 1
    child.memes["patience"] += 1
    world.say(f"Then came the twist: {pet.id} gave a small yip, and {pet.id} lifted {pet.pronoun('possessive')} paw.")
    world.say(f"{parent.label.capitalize()} looked close and saw {problem['reveal']}.")
    world.say(f"{parent.label.capitalize()} said, \"Tweezers, tweezers, gentle tweezers -- now they help.\"")

    thorn.meters["stuck"] += 1
    child.memes["concern"] += 1
    tool.held_by = parent.id
    thorn.meters["stuck"] += 1

    world.para()
    world.say(f"{parent.id} held the paw soft and steady, and {child.id} held the lamp steady and bright.")
    thorn.meters["stuck"] += 1
    thorn.meters["loose"] += 1
    thorn.meters["stuck"] = 0
    pet.memes["relief"] += 1
    child.memes["pride"] += 1
    world.say(f"The tweezers slipped in, the tweezers slipped out, and out came {problem['label']}.")
    world.say(f"{pet.id} blinked, then licked {child.pronoun('possessive')} cheek as if to say thank you.")

    world.para()
    world.say(f"\"Tweezers for beads? No, no, no,\" sang {child.id}. \"Tweezers for thorns? Yes, yes, yes.\"")
    world.say(f"So {child.id} put {trinket.phrase} in a cup, and {pet.id} trotted away light and free.")
    world.say(f"In the quiet nursery, the tiny song came back one last time: \"Gentle tweezers, gentle tweezers,\" and now it meant help.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    pet: Entity = f["pet"]
    problem = f["problem"]
    return [
        f'Write a nursery-rhyme style story about {child.id}, {pet.phrase}, and {TWEEZERS["tweezers"]["label"]}.',
        f"Tell a gentle story where {child.id} first wants {TWEEZERS['tweezers']['phrase']} for a shiny trinket, then uses them to help {pet.id}.",
        f'Write a rhyming, repetitive story that includes "{TWEEZERS["tweezers"]["label"]}" and ends with {problem["label"]} safely removed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    pet: Entity = f["pet"]
    thorn: Entity = f["thorn"]
    trinket: Entity = f["trinket"]
    return [
        QAItem(
            question=f"What did {child.id} first want to use for {trinket.label}?",
            answer=f"{child.id} first wanted to use tweezers for {trinket.label}, because the shiny bead looked so bright. But that changed when the tiny problem in {pet.id}'s paw was found.",
        ),
        QAItem(
            question=f"Why did the tweezers matter in the story?",
            answer=f"They mattered because they could gently lift out the little problem from {pet.id}'s paw. The tweezers were the right tool once everyone saw what was stuck.",
        ),
        QAItem(
            question=f"How did {child.id} feel after helping {pet.id}?",
            answer=f"{child.id} felt proud and calmer at the end. The bead was put away, the paw was better, and the child got to see the helpful side of the tweezers.",
        ),
        QAItem(
            question=f"What did {parent.id} show {child.id} about tweezers?",
            answer=f"{parent.id} showed that tweezers are for tiny troubles, not for grabbing shiny toys. That lesson helped {child.id} wait, watch, and then help the right way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are tweezers?",
            answer="Tweezers are a small tool with two skinny sides that pinch together. People use them to pick up little things or pull out tiny bits that should not stay stuck.",
        ),
        QAItem(
            question="Why are tweezers useful for tiny splinters or thorns?",
            answer="Tweezers can hold a tiny bit very closely and pull it out without pressing too hard. That makes them useful when something small is stuck in skin or fur.",
        ),
        QAItem(
            question="Why should children be gentle with pets?",
            answer="Pets have soft bodies and tiny feelings, so gentle hands keep them safe and calm. A gentle touch helps a pet trust the person helping.",
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
pet_helped :- stuck(Problem), remove_with_tweezers.
valid_story(Setting, Pet, Problem) :- setting(Setting), pet(Pet), problem(Problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PETS:
        lines.append(asp.fact("pet", p))
    for prob in PROBLEMS:
        lines.append(asp.fact("problem", prob))
    lines.append(asp.fact("tool", "tweezers"))
    lines.append(asp.fact("remove_with_tweezers", True) if False else asp.fact("remove_with_tweezers", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between Python and ASP.")
        print("python only:", sorted(py - asp_set))
        print("asp only:", sorted(asp_set - py))
        return 1

    # Smoke test a normal generate path.
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, child_name=None, child_type=None, parent_type=None, pet_kind=None, problem=None, seed=None), random.Random(777)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    print(f"OK: ASP parity and generate smoke test passed ({len(py)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about tweezers, a twist, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--pet-kind", choices=PETS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_story_combo(setting: str, pet_kind: str, problem: str) -> bool:
    return setting in SETTINGS and pet_kind in PETS and problem in PROBLEMS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.pet_kind is None or c[1] == args.pet_kind)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, pet_kind, problem = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_type)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        pet_kind=pet_kind,
        problem=problem,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.pet_kind not in PETS:
        raise StoryError("Unknown pet.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    world = build_world(params)
    tell(world)
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
    StoryParams(setting="nursery", child_name="Mia", child_type="girl", parent_type="mother", pet_kind="kitten", problem="thorn"),
    StoryParams(setting="playroom", child_name="Toby", child_type="boy", parent_type="father", pet_kind="puppy", problem="splinter"),
    StoryParams(setting="windowseat", child_name="Nora", child_type="girl", parent_type="mother", pet_kind="mouse", problem="thorn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
