#!/usr/bin/env python3
"""
A standalone storyworld for a small Detective Story about a child who finds
surprise, conflict, and reconciliation outside near a bin.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["surprise", "conflict", "reconciliation", "curiosity", "relief", "joy"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str = "outside"
    place_detail: str = "the sidewalk by the bin"
    weather: str = "cool"


@dataclass
class Clue:
    label: str
    phrase: str
    hidden_in_bin: bool = False
    surprising: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.story_lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def para(self) -> None:
        if self.story_lines and self.story_lines[-1] != "":
            self.story_lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.story_lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SCENES = {
    "outside": Scene(place="outside", place_detail="the sidewalk by the bin", weather="cool"),
    "alley": Scene(place="outside", place_detail="the little alley behind the shop bin", weather="breezy"),
    "yard": Scene(place="outside", place_detail="the yard near the recycling bin", weather="bright"),
}

CLUES = {
    "toy_whistle": Clue(label="whistle", phrase="a tiny silver whistle", hidden_in_bin=True, surprising=True),
    "red_hat": Clue(label="hat", phrase="a red hat with a blue ribbon", hidden_in_bin=True, surprising=True),
    "cookie_tin": Clue(label="tin", phrase="an old cookie tin", hidden_in_bin=True, surprising=False),
    "lost_note": Clue(label="note", phrase="a folded note with one clue written on it", hidden_in_bin=True, surprising=True),
}

DETECTIVE_NAMES = ["Mina", "Noah", "Lena", "Eli", "Tess", "Owen"]
HELPER_NAMES = ["Pip", "Mila", "Rafi", "June", "Ari", "Bess"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def clue_is_reasonable(place: str, clue_id: str) -> bool:
    return place in SCENES and clue_id in CLUES and CLUES[clue_id].hidden_in_bin


def explain_rejection(place: str, clue_id: str) -> str:
    if place not in SCENES:
        return "(No story: that place is not part of this little detective world.)"
    if clue_id not in CLUES:
        return "(No story: that clue is not in the bin mystery catalog.)"
    if not CLUES[clue_id].hidden_in_bin:
        return "(No story: this clue is not something the detective can find in the bin.)"
    return "(No story: the options do not make a believable detective mystery.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    scene = SCENES[params.place]
    world = World(scene=scene)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="helper",
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=CLUES[params.clue].label,
        phrase=CLUES[params.clue].phrase,
        location="bin",
    ))
    bin_obj = world.add(Entity(
        id="bin",
        kind="thing",
        type="bin",
        label="bin",
        phrase="a dented blue bin",
        location=params.place,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        clue=clue,
        bin=bin_obj,
        clue_def=CLUES[params.clue],
        scene=scene,
    )

    return world


def intro(world: World) -> None:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    c: Clue = world.facts["clue_def"]  # type: ignore[assignment]
    world.say(
        f"{d.id} was a little detective who loved to look for answers."
    )
    world.say(
        f"{d.pronoun('subject').capitalize()} and {h.id} liked to perform small detective games outside, "
        f"walking slow, watching close, and asking smart questions."
    )
    world.say(
        f"That day, they noticed the {c.label} mystery near {world.scene.place_detail}."
    )


def investigate(world: World) -> None:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    clue_def: Clue = world.facts["clue_def"]  # type: ignore[assignment]

    d.meters["curiosity"] += 1
    world.say(
        f"{d.id} knelt by the bin and peered inside. {d.pronoun('subject').capitalize()} found {clue.phrase}."
    )
    if clue_def.surprising:
        d.meters["surprise"] += 1
        h.meters["surprise"] += 1
        world.say(
            f"It was a surprise, because nobody expected such a tiny thing to be hiding there."
        )
    else:
        world.say("It was a plain clue, but it still mattered.")
    world.say(
        f"{h.id} pointed at the marks around the bin and said the clue did not get there by magic."
    )


def conflict(world: World) -> None:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    d.meters["conflict"] += 1
    h.meters["conflict"] += 1
    world.say(
        f"{d.id} thought someone must have taken the clue on purpose, and {h.id} worried it might have been lost forever."
    )
    world.say(
        f"The two friends had a small conflict, because each one had a different guess."
    )
    world.say(
        f"{d.id} tapped the bin lid and looked around the outside path for more signs."
    )
    world.say(
        f"Then {d.id} noticed a small line of crumbs leading away from the bin."
    )
    world.facts["trail"] = "crumbs"


def turn(world: World) -> None:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    d.meters["reconciliation"] += 1
    h.meters["reconciliation"] += 1
    d.meters["conflict"] = 0
    h.meters["conflict"] = 0
    d.meters["joy"] += 1
    h.meters["joy"] += 1
    world.say(
        f"{d.id} stopped, smiled, and shared the clue with {h.id}."
    )
    world.say(
        f"{d.id} said, 'Maybe this is not a stealing mystery. Maybe it is a lost-and-found mystery.'"
    )
    world.say(
        f"{h.id} blinked, then laughed, because that made sense."
    )
    world.say(
        f"Together they looked outside the bin and found a little label tucked under the lid."
    )
    world.say(
        f"The label matched {clue.phrase}, so the answer was not a thief at all."
    )


def resolve(world: World) -> None:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    world.say(
        f"It turned out the clue had fallen from a nearby pocket and slid beside the bin."
    )
    world.say(
        f"{d.id} and {h.id} put it back where it belonged and told the owner the good news."
    )
    world.say(
        f"The case ended with reconciliation, because both friends agreed on the truth at last."
    )
    world.say(
        f"{d.id} left the sidewalk with {clue.phrase} safely returned and a happy grin."
    )


def tell_story(world: World) -> World:
    intro(world)
    world.para()
    investigate(world)
    conflict(world)
    world.para()
    turn(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    clue_def: Clue = world.facts["clue_def"]  # type: ignore[assignment]
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    return [
        f"Write a short Detective Story for a child about {d.id} finding {clue_def.phrase} outside near a bin.",
        f"Tell a gentle mystery where a little detective performs a search outside, feels surprise, has conflict, and ends in reconciliation.",
        f"Write a story that includes the words perform, bin, and outside, and ends with friends agreeing on what the clue means.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    h: Entity = world.facts["helper"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    clue_def: Clue = world.facts["clue_def"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {d.id}, a little detective, and {h.id}, who helped look for clues outside.",
        ),
        QAItem(
            question=f"What did {d.id} find near the bin?",
            answer=f"{d.id} found {clue.phrase} near the bin outside.",
        ),
        QAItem(
            question="Why was there conflict in the story?",
            answer="There was conflict because the two friends first had different ideas about what the clue meant.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation, because the friends agreed on the truth and put the clue back where it belonged.",
        ),
        QAItem(
            question="Why was the clue a surprise?",
            answer=(
                "It was a surprise because the tiny clue was hiding by the bin, and nobody expected to find it there."
                if clue_def.surprising else
                "It was not a big surprise, but it still mattered to the mystery."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is a bin?",
            answer="A bin is a container where people can throw things away or keep collected items together.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop disagreeing and come back together again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(outside).
place(alley).
place(yard).

clue(toy_whistle).
clue(red_hat).
clue(cookie_tin).
clue(lost_note).

hidden_in_bin(toy_whistle).
hidden_in_bin(red_hat).
hidden_in_bin(cookie_tin).
hidden_in_bin(lost_note).

surprising(toy_whistle).
surprising(red_hat).
surprising(lost_note).

valid(Place, Clue) :- place(Place), clue(Clue), hidden_in_bin(Clue).
surprise_story(Place, Clue) :- valid(Place, Clue), surprising(Clue).
#show valid/2.
#show surprise_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SCENES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        if CLUES[c].hidden_in_bin:
            lines.append(asp.fact("hidden_in_bin", c))
        if CLUES[c].surprising:
            lines.append(asp.fact("surprising", c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(p, c) for p in SCENES for c in CLUES if clue_is_reasonable(p, c)}
    asp_set = set(asp_valid_pairs())
    if asp_set == python_set:
        print(f"OK: ASP matches Python gate ({len(asp_set)} valid pairs).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective Story world: perform, bin, outside.")
    ap.add_argument("--place", choices=sorted(SCENES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SCENES))
    clue = args.clue or rng.choice(list(CLUES))
    if not clue_is_reasonable(place, clue):
        raise StoryError(explain_rejection(place, clue))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != detective_name])
    return StoryParams(
        place=place,
        clue=clue,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        lines.append(f"{ent.id}: type={ent.type} meters={meters}")
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
    StoryParams(place="outside", clue="toy_whistle", detective_name="Mina", detective_type="girl", helper_name="Pip", helper_type="boy"),
    StoryParams(place="yard", clue="red_hat", detective_name="Owen", detective_type="boy", helper_name="June", helper_type="girl"),
    StoryParams(place="alley", clue="lost_note", detective_name="Tess", detective_type="girl", helper_name="Rafi", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid pairs:")
        for p in pairs:
            print(" ", p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
