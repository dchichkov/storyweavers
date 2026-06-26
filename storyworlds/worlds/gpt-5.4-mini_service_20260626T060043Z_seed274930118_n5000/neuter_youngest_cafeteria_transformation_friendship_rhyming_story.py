#!/usr/bin/env python3
"""
A small rhyming storyworld: the youngest child in a cafeteria discovers a gentle
transformation, and friendship makes the change feel bright instead of scary.

The domain is intentionally tiny and constraint-checked:
- a neuter protagonist
- the youngest child in a cafeteria
- a transformation that changes the protagonist's form or role
- a friendship turn that helps resolve worry
- prose that aims for a soft, rhyming cadence without becoming a frozen template
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

FORMS = ["tiny mouse", "bright butterfly", "little kitten", "shiny robot", "small owl"]
MOODS = ["wary", "lonely", "glad", "brave", "shy"]
FRIEND_NAMES = ["June", "Milo", "Pip", "Nori", "Sage", "Tessa", "Rae", "Ollie"]
FOOD_NAMES = ["blueberry pie", "carrot soup", "apple slice", "cheese sandwich", "pear tart"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    pronoun_set: str = "neuter"  # neuter only in this storyworld
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Place:
    id: str
    label: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    from_form: str
    to_form: str
    trigger: str
    wonder: str
    rhyme_end: str


@dataclass
class StoryParams:
    place: str = "cafeteria"
    transformation: str = "butterfly"
    friend: str = "Milo"
    food: str = "blueberry pie"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "cafeteria": Place(id="cafeteria", label="the cafeteria", affordances={"share_food", "speak_softly"}),
}

TRANSFORMATIONS = {
    "butterfly": Transformation(
        id="butterfly",
        from_form="plain little child",
        to_form="bright butterfly",
        trigger="shared a kind bite and smiled",
        wonder="sparkled like a bun on a sunny tray",
        rhyme_end="light and bright",
    ),
    "mouse": Transformation(
        id="mouse",
        from_form="quiet little child",
        to_form="tiny mouse",
        trigger="nibbled a crumb and found a friend",
        wonder="moved with a soft little sway",
        rhyme_end="small and sweet",
    ),
    "kitten": Transformation(
        id="kitten",
        from_form="shy little child",
        to_form="little kitten",
        trigger="got a warm hello and a gentle seat",
        wonder="purred by the tray and the spoon",
        rhyme_end="soft and bright",
    ),
    "robot": Transformation(
        id="robot",
        from_form="busy little child",
        to_form="shiny robot",
        trigger="heard a friend say, 'You can start anew'",
        wonder="clicked with a cheerful beep",
        rhyme_end="new and true",
    ),
    "owl": Transformation(
        id="owl",
        from_form="watchful little child",
        to_form="small owl",
        trigger="shared a story under the glow",
        wonder="blinked with a wise little grin",
        rhyme_end="wise and kind",
    ),
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, transformation: str, friend: str, food: str) -> bool:
    return place == "cafeteria" and transformation in TRANSFORMATIONS and friend and food in FOOD_NAMES


def explain_rejection(place: str, transformation: str, friend: str, food: str) -> str:
    if place != "cafeteria":
        return "(No story: this little rhyming world only grows in a cafeteria.)"
    if transformation not in TRANSFORMATIONS:
        return "(No story: that transformation does not belong in this world.)"
    if food not in FOOD_NAMES:
        return "(No story: the meal choice is not part of the cafeteria table.)"
    return "(No story: the requested choices do not form a gentle transformation tale.)"


# ---------------------------------------------------------------------------
# Causal story engine
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, trans: Transformation, food: Entity) -> None:
    world.say(
        f"In the cafeteria near the cocoa and tray, "
        f"{child.id} sat smallest at the end of the day."
    )
    world.say(
        f"{child.cap_pronoun()} was the youngest one there, with a {child.memes['mood_word']} little stare, "
        f"and {child.pronoun('possessive')} {food.label} sat warm in the air."
    )
    world.say(
        f"{child.id} liked quiet corners and spoon-soft tune, "
        f"but {child.pronoun()} still hoped for a friend very soon."
    )
    world.facts["introduced"] = True


def notice_friend(world: World, child: Entity, friend: Entity) -> None:
    child.memes["lonely"] += 1
    world.say(
        f"Then {friend.id} came by with a grin like a beam, "
        f"and asked if {child.pronoun()} wanted to share in the dream."
    )
    world.say(
        f"{friend.id} said, \"Take a bite, take a bite; we can sit side by side, "
        f"and make this cafeteria feel warm and wide.\""
    )
    world.facts["friend_meet"] = True


def transformation_turn(world: World, child: Entity, friend: Entity, trans: Transformation, food: Entity) -> None:
    if child.memes["lonely"] < THRESHOLD:
        raise StoryError("Transformation needs a lonely start so the friendship can change the mood.")
    child.meters["change"] += 1
    child.memes["wonder"] += 1
    child.type = trans.to_form
    child.label = trans.to_form
    child.phrase = trans.to_form

    world.say(
        f"{child.id} took a small little taste of {food.label}, "
        f"and the room felt all sparkly and bright."
    )
    world.say(
        f"With {friend.id}'s kind company, {child.id} changed to {trans.to_form}; "
        f"{trans.wonder}."
    )
    world.say(
        f"{child.id} laughed in a sing-song way, \"Oh, look at me now; "
        f"I'm {trans.rhyme_end}, and I want to stay!\""
    )
    world.facts["transformed"] = True
    world.facts["new_form"] = trans.to_form


def friendship_resolution(world: World, child: Entity, friend: Entity, trans: Transformation) -> None:
    child.memes["friendship"] += 2
    child.memes["lonely"] = 0
    child.memes["glad"] += 2
    friend.memes["friendship"] += 2
    world.say(
        f"{friend.id} clapped and said, \"You're still you, through and through; "
        f"and I'm glad to be here, sitting with you.\""
    )
    world.say(
        f"So they shared one last crumb in a happy, soft hum, "
        f"and the cafeteria glowed like a sweet little drum."
    )
    world.say(
        f"{child.id}, once the youngest and quietest face, "
        f"was now {trans.to_form}, with a friend in their place."
    )
    world.facts["resolved"] = True


def tell(place: Place, trans: Transformation, friend_name: str, food_name: str) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id="Casey",
            kind="character",
            type="child",
            label=trans.from_form,
            phrase=trans.from_form,
            meters={"change": 0.0},
            memes={"lonely": 1.0, "glad": 0.0, "wonder": 0.0, "friendship": 0.0, "mood_word": 0.0},
        )
    )
    child.memes["mood_word"] = random.choice(MOODS)  # narrative texture only
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type="child",
            label="friend",
            phrase="friend",
            meters={"help": 0.0},
            memes={"friendship": 1.0},
        )
    )
    food = world.add(
        Entity(
            id=food_name,
            kind="thing",
            type="food",
            label=food_name,
            phrase=food_name,
        )
    )

    introduce(world, child, trans, food)
    world.para()
    notice_friend(world, child, friend)
    world.para()
    transformation_turn(world, child, friend, trans, food)
    world.para()
    friendship_resolution(world, child, friend, trans)

    world.facts.update(
        child=child,
        friend=friend,
        food=food,
        trans=trans,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about a youngest child in {f["place"].label} who changes after sharing {f["food"].label}.',
        f"Tell a gentle cafeteria tale where {f['child'].id} feels lonely, meets {f['friend'].id}, and transforms into {f['trans'].to_form}.",
        f"Write a child-friendly rhyme about friendship and transformation with {f['food'].label} and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    food: Entity = f["food"]
    trans: Transformation = f["trans"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was the youngest one in {place.label} at the start of the story?",
            answer=f"{child.id} was the youngest child in {place.label}, sitting small and quiet at first.",
        ),
        QAItem(
            question=f"What did {friend.id} do that helped {child.id} change?",
            answer=f"{friend.id} offered kindness, shared a bite of {food.label}, and stayed beside {child.id} as a friend.",
        ),
        QAItem(
            question=f"What did {child.id} transform into after the friendly moment?",
            answer=f"{child.id} transformed into {trans.to_form}, and the change felt bright and happy.",
        ),
        QAItem(
            question=f"How did the story end after the transformation?",
            answer=f"It ended with {child.id} and {friend.id} sharing a soft happy moment in the cafeteria, with friendship shining through.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a cafeteria?",
        answer="A cafeteria is a place where people choose food and sit together to eat.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is when people are kind to each other, help each other, and enjoy being together.",
    ),
    QAItem(
        question="What is a transformation?",
        answer="A transformation is a change from one form or state into another.",
    ),
    QAItem(
        question="Why can sharing food help friends?",
        answer="Sharing food can help friends because it is a caring thing to do, and caring actions make people feel close.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place={world.place.label}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(place).
% transformation(id).
% friend(name).
% food(name).

valid_story(P, T, F, Food) :- place(P), transformation(T), friend(F), food(Food), P = cafeteria.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, a))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend", name))
    for food in FOOD_NAMES:
        lines.append(asp.fact("food", food))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def valid_stories() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for tid in TRANSFORMATIONS:
            for friend in FRIEND_NAMES:
                for food in FOOD_NAMES:
                    if valid_combo(place, tid, friend, food):
                        out.append((place, tid, friend, food))
    return out


# ---------------------------------------------------------------------------
# Story generation interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming cafeteria storyworld of friendship and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--food", choices=FOOD_NAMES)
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
    place = args.place or "cafeteria"
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    friend = args.friend or rng.choice(FRIEND_NAMES)
    food = args.food or rng.choice(FOOD_NAMES)
    if not valid_combo(place, transformation, friend, food):
        raise StoryError(explain_rejection(place, transformation, friend, food))
    return StoryParams(place=place, transformation=transformation, friend=friend, food=food)


def generate(params: StoryParams) -> StorySample:
    trans = TRANSFORMATIONS[params.transformation]
    world = tell(PLACES[params.place], trans, params.friend, params.food)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for trans in TRANSFORMATIONS:
            params = StoryParams(place="cafeteria", transformation=trans, friend=FRIEND_NAMES[0], food=FOOD_NAMES[0])
            params.seed = base_seed
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
