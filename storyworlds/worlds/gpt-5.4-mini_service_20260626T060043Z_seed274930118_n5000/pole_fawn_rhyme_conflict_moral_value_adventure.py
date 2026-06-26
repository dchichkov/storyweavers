#!/usr/bin/env python3
"""
A small adventure storyworld about a fawn, a pole, a creek crossing, and a
careful compromise.

The seed tale behind this world:
A young fawn wants to cross a stream by balancing on a pole bridge and chasing a
shiny berry on the far bank. A cautious older helper worries the pole is slick
and the gap is too wide. The fawn feels frustrated and starts to argue, until
they notice a safer way: move slowly, share the pole, and sing a little rhyme
for courage. The crossing succeeds, the fawn learns patience, and the moral is
that brave hearts still need wise steps.

This file keeps the world small and classical:
- physically grounded meters: balance, wetness, distance, carried items
- emotional memes: curiosity, worry, conflict, relief, pride
- a short adventure turn with a moral value at the end
- a rhyme instrument woven into the narration, without becoming a nursery rhyme
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
# World vocab
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    summary: str
    danger: str = ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Character:
    id: str
    kind: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    items: list[str] = field(default_factory=list)

    def pronoun(self) -> str:
        return "she" if self.role in {"fawn", "deer"} else "they"

    def poss(self) -> str:
        return "her" if self.role in {"fawn", "deer"} else "their"


@dataclass
class World:
    place: Place
    entities: dict[str, object] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "creek"
    pole: str = "bridge-pole"
    token: str = "red berry"
    name: str = "Pip"
    companion: str = "heron"
    seed: Optional[int] = None


PLACES = {
    "creek": Place(
        id="creek",
        label="the creek",
        summary="a narrow stream with slippery stones and a single old pole bridge",
        danger="The water moved quickly under the pole.",
    ),
    "woodland": Place(
        id="woodland",
        label="the woodland path",
        summary="a winding trail with a low pole over a muddy dip",
        danger="The mud below made the pole tricky to trust.",
    ),
}

POLES = {
    "bridge-pole": Item(
        id="bridge-pole",
        label="the pole bridge",
        phrase="an old pole bridge",
    ),
    "rail-pole": Item(
        id="rail-pole",
        label="the rail pole",
        phrase="a smooth rail-like pole",
    ),
}

TOKENS = {
    "red berry": Item(id="red-berry", label="red berry", phrase="a shiny red berry"),
    "blue feather": Item(id="blue-feather", label="blue feather", phrase="a bright blue feather"),
    "gold acorn": Item(id="gold-acorn", label="gold acorn", phrase="a tiny gold acorn"),
}

COMPANIONS = {
    "heron": ("heron", "tall heron"),
    "fox": ("fox", "clever fox"),
    "goat": ("goat", "steady goat"),
}

CURATED = [
    StoryParams(place="creek", pole="bridge-pole", token="red berry", name="Pip", companion="heron"),
    StoryParams(place="woodland", pole="rail-pole", token="blue feather", name="Mina", companion="goat"),
]


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

class SimWorld(World):
    pass


def build_world(params: StoryParams) -> SimWorld:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.pole not in POLES:
        raise StoryError(f"Unknown pole: {params.pole}")
    if params.token not in TOKENS:
        raise StoryError(f"Unknown token: {params.token}")
    if params.companion not in COMPANIONS:
        raise StoryError(f"Unknown companion: {params.companion}")

    world = SimWorld(place=PLACES[params.place])
    fawn = world.add(Character(
        id=params.name,
        kind="character",
        label=params.name,
        role="fawn",
        meters={"balance": 1.0, "distance": 0.0, "wetness": 0.0},
        memes={"curiosity": 2.0, "worry": 0.0, "conflict": 0.0, "relief": 0.0, "pride": 0.0},
        items=[],
    ))
    helper_name, helper_label = COMPANIONS[params.companion]
    helper = world.add(Character(
        id=helper_name,
        kind="character",
        label=helper_label,
        role="guide",
        meters={"balance": 1.0},
        memes={"worry": 1.0, "kindness": 2.0},
        items=[],
    ))
    pole = world.add(Item(
        id=params.pole,
        label=POLES[params.pole].label,
        phrase=POLES[params.pole].phrase,
        meters={"slickness": 1.0 if params.place == "creek" else 0.6},
    ))
    token = world.add(Item(
        id=params.token.replace(" ", "-"),
        label=TOKENS[params.token].label,
        phrase=TOKENS[params.token].phrase,
        owner=params.name,
        carried_by=params.name,
        meters={"shine": 1.0},
    ))
    world.facts.update(fawn=fawn, helper=helper, pole=pole, token=token)
    return world


def describe_setting(world: SimWorld) -> None:
    world.say(f"At {world.place.label}, {world.place.summary}.")
    if world.place.danger:
        world.say(world.place.danger)


def desire_and_warning(world: SimWorld) -> None:
    fawn: Character = world.get(world.facts["fawn"].id)
    helper: Character = world.get(world.facts["helper"].id)
    token: Item = world.get(world.facts["token"].id)
    pole: Item = world.get(world.facts["pole"].id)

    world.say(f"{fawn.label} spotted {token.phrase} on the far side and wanted it at once.")
    fawn.memes["curiosity"] += 1.0
    world.say(f"She whispered, “Over the pole, quick as a mole,” and stepped toward {pole.label}.")
    helper.memes["worry"] += 1.0
    world.say(f"{helper.label} stopped her with a calm wing-tip. “Slow feet stay neat; fast feet meet trouble,” {helper.label} said.")
    world.say(f"The {pole.label} looked narrow and a little slick.")

    world.facts["risk"] = True
    world.facts["warning"] = True


def conflict_turn(world: SimWorld) -> None:
    fawn: Character = world.get(world.facts["fawn"].id)
    helper: Character = world.get(world.facts["helper"].id)
    pole: Item = world.get(world.facts["pole"].id)

    fawn.memes["conflict"] += 1.0
    fawn.memes["worry"] += 0.5
    world.say(f"{fawn.label} stamped a hoof and argued, because the shiny token felt worth the rush.")
    world.say(f"“I can do it in a blink and a wink,” she said, but {helper.label} shook {helper.poss()} head.")
    world.say(f"{helper.label} pointed to the {pole.label} and said the water below did not forgive slips.")
    world.facts["conflict"] = True
    world.facts["pole_slick"] = pole.meters["slickness"] > 0.5


def compromise_and_crossing(world: SimWorld) -> None:
    fawn: Character = world.get(world.facts["fawn"].id)
    helper: Character = world.get(world.facts["helper"].id)
    token: Item = world.get(world.facts["token"].id)

    world.say(f"Then {helper.label} offered a safer way: “Take my side, keep your eyes wide, and step when I step.”")
    world.say("Together they began a careful rhyme: “One step, two step, breathe and see; brave and slow is best for me.”")

    fawn.memes["conflict"] = 0.0
    fawn.memes["relief"] += 1.0
    fawn.memes["pride"] += 1.0
    fawn.meters["distance"] = 1.0
    fawn.meters["balance"] = 1.0

    world.say(f"{fawn.label} crossed the pole beside {helper.label}, without a wobble or a tumble.")
    world.say(f"On the far side, she picked up {token.phrase}, and the water stayed below where it belonged.")
    world.say(f"She smiled at the little lesson in her chest: a brave heart can still choose a wise path.")

    world.facts["resolved"] = True
    world.facts["moral"] = "Patience and courage can travel together."


def tell_story(params: StoryParams) -> SimWorld:
    world = build_world(params)
    describe_setting(world)
    world.say("")
    desire_and_warning(world)
    world.say("")
    conflict_turn(world)
    world.say("")
    compromise_and_crossing(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: SimWorld) -> list[str]:
    fawn: Character = world.facts["fawn"]
    helper: Character = world.facts["helper"]
    token: Item = world.facts["token"]
    return [
        "Write a short adventure story for a child about a fawn, a pole, and a wise helper.",
        f"Tell a gentle conflict story where {fawn.label} wants to reach {token.phrase} but {helper.label} worries about the slippery pole.",
        "End the story with a rhyme and a moral value about patience or courage.",
    ]


def story_qa(world: SimWorld) -> list[QAItem]:
    fawn: Character = world.facts["fawn"]
    helper: Character = world.facts["helper"]
    token: Item = world.facts["token"]
    place = world.place.label
    return [
        QAItem(
            question=f"Who wanted to cross the pole and get the shiny prize?",
            answer=f"The young fawn named {fawn.label} wanted to cross the pole and reach {token.phrase}.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {fawn.label}?",
            answer=f"{helper.label} warned {fawn.label} because the pole was slick and the water below made a fall risky.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{fawn.label} crossed carefully with help, got the prize, and learned that patience and courage can travel together at {place}.",
        ),
    ]


def world_knowledge_qa(world: SimWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fawn?",
            answer="A fawn is a young deer.",
        ),
        QAItem(
            question="What is a pole bridge?",
            answer="A pole bridge is a narrow support you can cross carefully, often like a simple bridge or beam.",
        ),
        QAItem(
            question="Why can a slick pole be dangerous?",
            answer="A slick pole can be dangerous because feet may slip, which can make a crossing unsafe.",
        ),
        QAItem(
            question="What is a moral value in a story?",
            answer="A moral value is the lesson the story leaves behind, like kindness, patience, or courage.",
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


def dump_trace(world: SimWorld) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        if isinstance(ent, Character):
            lines.append(
                f"{ent.id}: meters={ent.meters} memes={ent.memes}"
            )
        else:
            lines.append(f"{ent.id}: {ent.phrase} meters={ent.meters}")
    lines.append(f"facts={world.facts.keys()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/1.
#show valid_story/2.

valid(place, token) :- place_ok(place), token_ok(token), risk(place), has_helper(helper), moral_value.
valid_story(place, token) :- valid(place, token).

place_ok(creek).
place_ok(woodland).

token_ok(red_berry).
token_ok(blue_feather).
token_ok(gold_acorn).

risk(creek).
risk(woodland).

has_helper(heron).
has_helper(fox).
has_helper(goat).

moral_value.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_ok", pid))
        lines.append(asp.fact("risk", pid))
    for tid in TOKENS:
        lines.append(asp.fact("token_ok", tid.replace(" ", "_")))
    for cname in COMPANIONS:
        lines.append(asp.fact("has_helper", cname))
    lines.append(asp.fact("moral_value"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set((p, t.replace(" ", "_")) for p in PLACES for t in TOKENS)
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo parity matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(python_set - clingo_set))
    print("only clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a fawn, a pole, a warning, and a moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pole", choices=POLES)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    choices = []
    for place in PLACES:
        if args.place and place != args.place:
            continue
        for pole in POLES:
            if args.pole and pole != args.pole:
                continue
            for token in TOKENS:
                if args.token and token != args.token:
                    continue
                for companion in COMPANIONS:
                    if args.companion and companion != args.companion:
                        continue
                    choices.append((place, pole, token, companion))
    if not choices:
        raise StoryError("No valid story combination matches the given options.")
    place, pole, token, companion = rng.choice(choices)
    return StoryParams(
        place=place,
        pole=pole,
        token=token,
        name=args.name or rng.choice(["Pip", "Luna", "Briar", "Moss", "Nia"]),
        companion=companion,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a[0]} {a[1]}" for a in asp_valid_combos()))
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
            header = f"### {p.name}: {p.place}, {p.pole}, {p.token}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
