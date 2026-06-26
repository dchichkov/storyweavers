#!/usr/bin/env python3
"""
storyworlds/worlds/cockatoo_succeed_snooze_transformation_mystery.py
====================================================================

A small mystery storyworld about a cockatoo, a quiet clue, and a
transformation that helps the truth come out.

Premise:
- A curious child or caretaker notices something odd.
- A cockatoo snoozes through part of the scene and may be the only witness.
- A transformation changes how the problem can be solved: the cockatoo's
  feathers, color, voice, or stance reveal a hidden clue.

The stories are intentionally compact, child-facing, and state-driven:
the world tracks physical state in meters and emotional state in memes,
then turns that state into prose, Q&A, and ASP facts.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    states: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old greenhouse"
    indoor: bool = True
    clue_spots: set[str] = field(default_factory=lambda: {"bench", "windowsill", "floor"})
    quiet: bool = True


@dataclass
class Mystery:
    id: str
    clue: str
    hidden_truth: str
    oddity: str
    transform: str
    reveal: str
    keyword: str = "cockatoo"
    tags: set[str] = field(default_factory=set)


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "greenhouse": Setting(place="the old greenhouse", indoor=True, clue_spots={"bench", "windowsill", "floor"}),
    "attic": Setting(place="the dusty attic", indoor=True, clue_spots={"box", "beam", "floor"}),
    "garden": Setting(place="the moonlit garden", indoor=False, clue_spots={"path", "gate", "bush"}),
}

MYSTERIES = {
    "ink_feather": Mystery(
        id="ink_feather",
        clue="a blue feather with a dot of ink",
        hidden_truth="the missing key had brushed past the cockatoo's paint jar",
        oddity="one feather looked darker than all the others",
        transform="its feathers ruffled and changed from pale white to a bright blue stripe",
        reveal="the ink on the feather matched the keybox",
        keyword="cockatoo",
        tags={"bird", "feather", "ink", "key"},
    ),
    "bell_leaf": Mystery(
        id="bell_leaf",
        clue="a leaf tied to a tiny bell",
        hidden_truth="the wind had blown the bell onto the windowsill",
        oddity="the bell was quiet at first, as if it were sleeping",
        transform="the cockatoo woke, stretched, and its green crest stood up",
        reveal="the lifted crest pointed straight at the windowsill",
        keyword="snooze",
        tags={"bird", "leaf", "bell", "wind"},
    ),
    "mask_mirror": Mystery(
        id="mask_mirror",
        clue="a small silver mask under a chair",
        hidden_truth="the costume box had been moved by mistake",
        oddity="the mask was hiding in the shadow",
        transform="its sleepy gray tail turned into a shiny gold fan",
        reveal="the bright tail reflected the missing box's handle",
        keyword="succeed",
        tags={"bird", "mask", "mirror", "box"},
    ),
}

CHARACTER_NAMES = ["Mina", "Leo", "Nora", "Ari", "Tess", "Milo", "June", "Owen"]
TRAITS = ["curious", "quiet", "careful", "brave", "gentle"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for mid in MYSTERIES:
            combos.append((place, mid))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: the mystery at {setting.place} does not have a believable clue path.)"


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def _add(entity: Entity) -> Entity:
    return entity


def describe_setting(world: World) -> str:
    return {
        "the old greenhouse": "The old greenhouse smelled like wet leaves and warm glass.",
        "the dusty attic": "The dusty attic held quiet boxes and a thin line of light.",
        "the moonlit garden": "The moonlit garden was still, with paths silvered by the sky.",
    }[world.setting.place]


def mystery_hook(mystery: Mystery) -> str:
    return {
        "ink_feather": "Something had happened near the cockatoo's cage, but the clue was hiding in plain sight.",
        "bell_leaf": "A little bell had gone quiet, and that was the strangest part.",
        "mask_mirror": "A costume piece was missing, and only a tiny shape remained behind.",
    }[mystery.id]


def transform_line(mystery: Mystery) -> str:
    return mystery.transform


def reveal_line(mystery: Mystery) -> str:
    return mystery.reveal


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def story_beat_setup(world: World, child: Entity, bird: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    bird.states.add("snoozing")
    world.say(f"{child.id} was a {child.memes.get('trait', '') or 'curious'} little {child.type} who liked to notice small things.")
    world.say(f"At {world.setting.place}, a cockatoo named {bird.label} was snoozing in its perch.")
    world.say(mystery_hook(mystery))


def story_beat_clue(world: World, child: Entity, bird: Entity, mystery: Mystery) -> None:
    bird.memes["mood"] = bird.memes.get("mood", 0) + 0.5
    world.para()
    world.say(f"Then {child.id} found {mystery.clue}.")
    world.say(f"{bird.label} did not wake up right away, which made the clue feel even stranger.")


def story_beat_tension(world: World, child: Entity, bird: Entity, mystery: Mystery) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"{child.id} wondered if the clue meant someone had lost something important.")
    world.say(f"Still, the sleepy cockatoo seemed to know more than it could say.")


def story_beat_transformation(world: World, child: Entity, bird: Entity, mystery: Mystery) -> None:
    world.para()
    bird.states.add("transforming")
    bird.meters["brightness"] = bird.meters.get("brightness", 0.0) + 1.0
    bird.meters["evidence"] = bird.meters.get("evidence", 0.0) + 1.0
    world.say(f"{child.id} gently touched the perch, and {bird.label} finally stirred.")
    world.say(transform_line(mystery))
    world.say(f"That change made the clue clearer: {reveal_line(mystery)}.")


def story_beat_resolution(world: World, child: Entity, bird: Entity, mystery: Mystery) -> None:
    world.para()
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    bird.states.discard("snoozing")
    bird.states.add("awake")
    world.say(f"{child.id} smiled, because the mystery was not scary after all.")
    world.say(f"The cockatoo had only been snoozing, and the transformed clue helped everything make sense.")
    world.say(f"By the end, {child.id} could tell what had happened, and the little mystery was solved.")


def tell(setting: Setting, mystery: Mystery, name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    child.memes["trait"] = trait
    bird = world.add(Entity(id="cockatoo", kind="character", type="cockatoo", label="Pip"))
    bird.meters["sleep"] = 1.0
    bird.states.add("sleeping")
    item = world.add(Entity(id="clue", type="clue", label="clue"))

    story_beat_setup(world, child, bird, mystery)
    story_beat_clue(world, child, bird, mystery)
    story_beat_tension(world, child, bird, mystery)
    story_beat_transformation(world, child, bird, mystery)
    story_beat_resolution(world, child, bird, mystery)

    world.facts.update(
        child=child,
        bird=bird,
        clue=item,
        mystery=mystery,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a small child that includes a cockatoo, the word "snooze", and a clue that changes shape.',
        f"Tell a gentle mystery at {f['setting'].place} where {f['child'].id} notices {f['mystery'].clue} and a cockatoo helps solve it.",
        f'Write a story where a cockatoo snoozes, then a transformation reveals what the clue really means.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    bird = f["bird"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who found the clue at {setting.place}?",
            answer=f"{child.id} found the clue while exploring {setting.place}.",
        ),
        QAItem(
            question="What was the cockatoo doing at first?",
            answer=f"The cockatoo was snoozing at first, so it looked sleepy and quiet.",
        ),
        QAItem(
            question="What happened after the transformation?",
            answer=f"After the transformation, the cockatoo changed in a way that made the clue easier to understand.",
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"The mystery ended with the clue making sense and the child feeling relieved that the cockatoo had helped.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cockatoo?",
            answer="A cockatoo is a bird with a curved beak and a playful crest of feathers on its head.",
        ),
        QAItem(
            question="What does snooze mean?",
            answer="To snooze means to sleep lightly or nap for a little while.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state or form into another.",
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
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.states:
            bits.append(f"states={sorted(e.states)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the place and mystery are registered.
valid(P, M) :- setting(P), mystery(M).

% The bird can be in a snoozing state before the transformation.
snoozing(bird) :- mystery(M), clue(M, _).

% A transformation reveals a clue if the bird awakens.
revealed(M) :- mystery(M), transformed(M), clue(M, _).

% Show the valid story pairs.
#show valid/2.
#show revealed/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for spot in sorted(s.clue_spots):
            lines.append(asp.fact("spot", pid, spot))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("truth", mid, m.hidden_truth))
        lines.append(asp.fact("oddity", mid, m.oddity))
        lines.append(asp.fact("transformed", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a cockatoo, snooze, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHARACTER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid place/mystery combos:")
        for place, mystery in combos:
            print(f"  {place:12} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="greenhouse", mystery="ink_feather", name="Mina", trait="curious"),
            StoryParams(place="attic", mystery="bell_leaf", name="Leo", trait="careful"),
            StoryParams(place="garden", mystery="mask_mirror", name="Nora", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
