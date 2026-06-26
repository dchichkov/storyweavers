#!/usr/bin/env python3
"""
storyworlds/worlds/preference_dresser_sharing_rhyming_story.py
==============================================================

A small story world about a shared dresser, personal preferences, and a gentle
sharing fix, told in a light rhyming style.

Premise:
- Two children share a dresser in one bedroom.
- Each child has a strong preference for a favorite drawer and favorite clothes.
- A small conflict grows when the dresser gets crowded.
- A parent helps them sort, label, and share.
- The ending shows the dresser neat and both children happy.

The world model tracks:
- physical meters: clutter, tidy, drawer_space, clothing_order
- emotional memes: preference, frustration, fairness, pride, relief, affection
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    drawer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=lambda: {"share", "sort", "label"})


@dataclass
class Preference:
    id: str
    name: str
    drawer: str
    item: str
    color: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    preference: str
    dresser: str
    child_a_name: str
    child_a_type: str
    child_b_name: str
    child_b_type: str
    parent_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def rhyme_tail(word: str) -> str:
    return {
        "neat": "sweet",
        "bright": "light",
        "share": "care",
        "tide": "glide",
        "kind": "mind",
        "tame": "same",
        "sway": "play",
    }.get(word, word)


SETTING = Setting()


PREFERENCES = {
    "top": Preference(
        id="top",
        name="the top drawer",
        drawer="top",
        item="tiny hats",
        color="gold",
        rhyme="neat",
        tags={"drawer", "top", "sharing"},
    ),
    "middle": Preference(
        id="middle",
        name="the middle drawer",
        drawer="middle",
        item="striped shirts",
        color="blue",
        rhyme="bright",
        tags={"drawer", "middle", "sharing"},
    ),
    "bottom": Preference(
        id="bottom",
        name="the bottom drawer",
        drawer="bottom",
        item="soft socks",
        color="green",
        rhyme="kind",
        tags={"drawer", "bottom", "sharing"},
    ),
}


DRESSERS = {
    "wooden": "a wooden dresser with three smooth drawers",
    "white": "a white dresser with shiny knobs",
    "blue": "a blue dresser with a wide top shelf",
}


CHILD_A_NAMES = ["Mia", "Nora", "Lena", "Ada", "Ivy", "Zoe"]
CHILD_B_NAMES = ["Ben", "Owen", "Theo", "Max", "Leo", "Finn"]


def _init_world(params: StoryParams) -> World:
    world = World(SETTING)
    a = world.add(
        Entity(
            id=params.child_a_name,
            kind="character",
            type=params.child_a_type,
            label=params.child_a_name,
            meters={"tidy": 0.0, "drawer_space": 0.0},
            memes={"preference": 0.0, "fairness": 0.0, "affection": 0.0},
        )
    )
    b = world.add(
        Entity(
            id=params.child_b_name,
            kind="character",
            type=params.child_b_type,
            label=params.child_b_name,
            meters={"tidy": 0.0, "drawer_space": 0.0},
            memes={"preference": 0.0, "fairness": 0.0, "affection": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id=params.parent_name,
            kind="character",
            type="parent",
            label=params.parent_name,
            meters={"tidy": 0.0},
            memes={"fairness": 0.0, "calm": 0.0},
        )
    )
    dresser = world.add(
        Entity(
            id="dresser",
            kind="thing",
            type="dresser",
            label=DRESSERS[params.dresser],
            meters={"clutter": 0.0, "tidy": 0.0, "drawer_space": 3.0},
            memes={"pride": 0.0},
        )
    )
    pref = PREFERENCES[params.preference]
    world.facts.update(a=a, b=b, parent=parent, dresser=dresser, preference=pref)
    return world


def _intro(world: World) -> None:
    f = world.facts
    a, b, pref = f["a"], f["b"], f["preference"]
    world.say(
        f"In {world.setting.place}, {a.id} and {b.id} lived and played, by day and by night, "
        f"with a dresser that stood in the corner, tidy and bright."
    )
    world.say(
        f"{a.id} liked {pref.name}, and {b.id} liked their own way too; "
        f"one liked the top drawer, the other liked the middle drawer blue."
    )
    a.memes["preference"] += 1
    b.memes["preference"] += 1


def _set_up(conflict: bool = True) -> None:
    return None


def _crowd_dresser(world: World) -> None:
    f = world.facts
    a, b, dresser, pref = f["a"], f["b"], f["dresser"], f["preference"]
    dresser.meters["clutter"] += 1
    dresser.meters["drawer_space"] -= 1
    a.meters["drawer_space"] += 1
    b.meters["drawer_space"] += 1
    world.say(
        f"{a.id} tucked {pref.item} in the {pref.drawer} drawer with a hop and a hum; "
        f"{b.id} added a stack of clothes, and soon the drawers felt numb."
    )
    world.say(
        f"The dresser grew crowded, with sleeves in a squeeze and socks in a stack, "
        f"and the little house sighed, as if the room wanted its space back."
    )


def _conflict(world: World) -> None:
    f = world.facts
    a, b, parent, pref = f["a"], f["b"], f["parent"], f["preference"]
    a.memes["frustration"] = 1.0
    b.memes["frustration"] = 1.0
    parent.memes["fairness"] += 1
    world.say(
        f"{a.id} said, 'That drawer is mine!' with a pout and a frown; "
        f"{b.id} said, 'But I need room too,' and both felt let down."
    )
    world.say(
        f"{parent.id} came in with a soft little smile and a thoughtful tone, "
        f"'A shared dresser is a caring dresser; let's make the space our own.'"
    )


def _sort_and_share(world: World) -> None:
    f = world.facts
    a, b, parent, dresser, pref = f["a"], f["b"], f["parent"], f["dresser"], f["preference"]

    dresser.meters["clutter"] = max(0.0, dresser.meters["clutter"] - 1.0)
    dresser.meters["tidy"] += 1.0

    a.memes["frustration"] = 0.0
    b.memes["frustration"] = 0.0
    a.memes["fairness"] += 1.0
    b.memes["fairness"] += 1.0
    a.memes["affection"] += 1.0
    b.memes["affection"] += 1.0
    parent.memes["calm"] += 1.0

    world.say(
        f"They sorted the clothes with care, not in a whirl but in a row: "
        f"{pref.item} up top, shirts in the middle, socks down below."
    )
    world.say(
        f"{parent.id} labeled each drawer, so nobody had to guess; "
        f"the sharing plan was simple, and the room felt much less messy, yes."
    )


def _ending(world: World) -> None:
    f = world.facts
    a, b, dresser, pref = f["a"], f["b"], f["dresser"], f["preference"]
    world.say(
        f"{a.id} smiled at the tidy dresser and patted the wood with glee; "
        f"{b.id} smiled too, because sharing made space for you and me."
    )
    world.say(
        f"At the end, the dresser stayed neat, and both children were glad to see "
        f"that a little preference and a little patience can fit happily."
    )


def build_story(world: World) -> World:
    _intro(world)
    world.para()
    _crowd_dresser(world)
    _conflict(world)
    world.para()
    _sort_and_share(world)
    _ending(world)
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pref in PREFERENCES:
        for dresser in DRESSERS:
            combos.append((pref, dresser))
    return combos


@dataclass
class StorySampleParams:
    pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pref = f["preference"]
    a, b = f["a"], f["b"]
    return [
        f'Write a short rhyming story for young children about sharing a dresser and a {pref.drawer} drawer.',
        f"Tell a gentle story where {a.id} and {b.id} both want the same dresser space, but they find a fair way to share.",
        f'Write a tiny story with a cozy rhyme about a dresser, a preference, and a happy sharing plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, pref = f["a"], f["b"], f["parent"], f["preference"]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} need to share in the story?",
            answer=f"They needed to share the dresser and its drawers.",
        ),
        QAItem(
            question=f"Which drawer did {a.id} prefer at first?",
            answer=f"{a.id} preferred the {pref.drawer} drawer.",
        ),
        QAItem(
            question=f"Why did the children feel upset before the fix?",
            answer=f"They felt upset because the dresser got crowded and each child wanted more space.",
        ),
        QAItem(
            question="How did the parent help?",
            answer="The parent helped by sorting the clothes, labeling the drawers, and making a fair sharing plan.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="At the end the dresser was neat, and both children were happy to share it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dresser?",
            answer="A dresser is a piece of furniture with drawers that holds clothes and small things.",
        ),
        QAItem(
            question="Why do people label drawers?",
            answer="People label drawers so they can remember where things belong and keep them organized.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means more than one person uses something fairly and takes turns or makes room for each other.",
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
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world expects a dresser-sharing scene with a real preference and a fair fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about sharing a dresser.")
    ap.add_argument("--preference", choices=PREFERENCES)
    ap.add_argument("--dresser", choices=DRESSERS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--type-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "parent"])
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
    combos = valid_combos()
    if args.preference:
        combos = [c for c in combos if c[0] == args.preference]
    if args.dresser:
        combos = [c for c in combos if c[1] == args.dresser]
    if not combos:
        raise StoryError(explain_rejection())
    pref, dresser = rng.choice(sorted(combos))
    type_a = args.type_a or rng.choice(["girl", "boy"])
    type_b = args.type_b or ("boy" if type_a == "girl" else "girl")
    name_a = args.name_a or rng.choice(CHILD_A_NAMES)
    name_b = args.name_b or rng.choice(CHILD_B_NAMES)
    if name_a == name_b:
        name_b = rng.choice([n for n in CHILD_B_NAMES if n != name_a])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        preference=pref,
        dresser=dresser,
        child_a_name=name_a,
        child_a_type=type_a,
        child_b_name=name_b,
        child_b_type=type_b,
        parent_name=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = _init_world(params)
    build_story(world)
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


ASP_RULES = r"""
preference(top).
preference(middle).
preference(bottom).

dresser(wooden).
dresser(white).
dresser(blue).

shares_dresser(P, D) :- preference(P), dresser(D).
valid_story(P, D) :- shares_dresser(P, D).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PREFERENCES:
        lines.append(asp.fact("preference", p))
    for d in DRESSERS:
        lines.append(asp.fact("dresser", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(
        preference="top",
        dresser="wooden",
        child_a_name="Mia",
        child_a_type="girl",
        child_b_name="Ben",
        child_b_type="boy",
        parent_name="mother",
    ),
    StoryParams(
        preference="middle",
        dresser="white",
        child_a_name="Ada",
        child_a_type="girl",
        child_b_name="Leo",
        child_b_type="boy",
        parent_name="father",
    ),
    StoryParams(
        preference="bottom",
        dresser="blue",
        child_a_name="Nora",
        child_a_type="girl",
        child_b_name="Finn",
        child_b_type="boy",
        parent_name="mother",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for p, d in asp_valid_combos():
            print(f"  {p:7} {d}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a_name} and {p.child_b_name} share the {p.preference} drawer"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
