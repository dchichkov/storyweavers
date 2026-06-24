#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/gimmick_gots_quest_lesson_learned_tall_tale.py
=====================================================================================================

A standalone tall-tale storyworld about a big-hearted quest, a clever gimmick,
and a lesson learned.

Premise:
- A child character sets out on a small quest to reach a faraway thing they want.
- They try a boastful gimmick that promises to make the trip easy.
- The gimmick backfires in a comic, exaggerated way.
- A helper or parent suggests a humbler method.
- The child learns a lesson and completes the quest.

The prose is driven by a tiny simulation over physical meters and emotional
memes. The story should feel like a complete tale with a beginning, a turn, and
an ending image that proves what changed.
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
# World data model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0, "dust": 0.0, "wear": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "pride": 0.0, "worry": 0.0, "joy": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    kind: str
    distance: int
    wonder: str


@dataclass
class Quest:
    goal: str
    item: str
    route: str
    risk: str
    finish: str


@dataclass
class Gimmick:
    name: str
    pitch: str
    bonus: str
    backlash: str
    fragile: bool = True


@dataclass
class StoryParams:
    place: str
    quest: str
    gimmick: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, quest: Quest, gimmick: Gimmick):
        self.place = place
        self.quest = quest
        self.gimmick = gimmick
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.place, self.quest, self.gimmick)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hill": Place(label="the tallest hill in town", kind="hill", distance=9, wonder="wind"),
    "woods": Place(label="the whispering woods", kind="woods", distance=7, wonder="moss"),
    "river": Place(label="the broad riverbank", kind="river", distance=8, wonder="water"),
    "barn": Place(label="the old red barn", kind="barn", distance=5, wonder="hay"),
    "fair": Place(label="the county fairgrounds", kind="fair", distance=6, wonder="music"),
}

QUESTS = {
    "kite": Quest(
        goal="bring back the moon-fish kite",
        item="moon-fish kite",
        route="follow the long road and the high wind",
        risk="the path might tangle the string and send the kite spinning away",
        finish="the kite could sail all the way home in one proud swoop",
    ),
    "bell": Quest(
        goal="fetch the golden weather-bell",
        item="golden weather-bell",
        route="cross the bridge and climb the creek path",
        risk="a stumble could make the bell clang so loud it wakes the geese",
        finish="the bell could sing in a bright little chime",
    ),
    "seed": Quest(
        goal="get the giant bean seed from the market",
        item="giant bean seed",
        route="walk past the creek and through the dust road",
        risk="a foolish shortcut could drop the seed in the mud",
        finish="the seed could nestle safely in a pocket",
    ),
    "map": Quest(
        goal="find the star-map tucked in the old attic",
        item="star-map",
        route="climb the ladder and tiptoe across the beam",
        risk="a clumsy rush could tear the paper and lose the stars",
        finish="the map could be folded flat as a pancake",
    ),
}

GIMMICKS = {
    "ladderhat": Gimmick(
        name="a ladder-hat",
        pitch="a hat with tiny ladder rungs sewn right into it",
        bonus="it promised to make any climb feel easy as pie",
        backlash="the hat wobbled, slipped, and made the climb look like a goose on roller skates",
    ),
    "whirlboots": Gimmick(
        name="whirlboots",
        pitch="boots with spinning wheels hidden in the soles",
        bonus="they bragged that they could whisk a child anywhere in a blink",
        backlash="they spun too fast, kicked up dust, and zipped in the wrong direction",
    ),
    "jumprope": Gimmick(
        name="a springy jump-rope harness",
        pitch="a harness tied to a jump rope and a buckle full of springs",
        bonus="it claimed a person could bounce over trouble without touching the ground",
        backlash="it bounced like a rabbit in a thunderstorm and flung the quest sideways",
    ),
    "megabucket": Gimmick(
        name="a megabucket cart",
        pitch="a bucket on little wheels with a horn that shouted 'I GOT THIS!'",
        bonus="it vowed to carry everything in one grand parade",
        backlash="the horn blared, the wheels wobbled, and the cart rolled into a pile of hay",
    ),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandpa": "grandpa",
    "aunt": "aunt",
}

GIRL_NAMES = ["Mabel", "Mina", "Ruby", "Nell", "Ivy", "June", "Pearl", "Lola"]
BOY_NAMES = ["Otis", "Benny", "Clive", "Hank", "Wes", "Ezra", "Milo", "Gus"]
TRAITS = ["brave", "curious", "boastful", "stubborn", "cheerful", "spunky"]


def valid_pairs() -> list[tuple[str, str, str]]:
    out = []
    for pid in PLACES:
        for qid in QUESTS:
            for gid in GIMMICKS:
                out.append((pid, qid, gid))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest_combo(P,Q,G) :- place(P), quest(Q), gimmick(G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid in GIMMICKS:
        lines.append(asp.fact("gimmick", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show quest_combo/3."))
    return sorted(set(asp.atoms(model, "quest_combo")))


def asp_verify() -> int:
    py = set(valid_pairs())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    if py - ac:
        print("only in python:", sorted(py - ac))
    if ac - py:
        print("only in clingo:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(place: Place, quest: Quest, gimmick: Gimmick) -> None:
    if place.distance < 5:
        raise StoryError("This quest needs a bigger road than a short stroll.")
    if gimmick.name == "megabucket cart" and quest.item == "star-map":
        raise StoryError("The megabucket cart is too clumsy for a paper quest.")
    if quest.item == "giant bean seed" and gimmick.name == "a ladder-hat":
        raise StoryError("A ladder-hat does not help with a pocket-sized seed quest.")


def predict_backfire(world: World) -> bool:
    return True  # all gimmicks are boastful and backfire before the lesson


def opening(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Long ago and twice told, {hero.id} was a {hero.pronoun('object')} little {hero.type} with a head full of thunder and a heart full of road."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {world.quest.goal}, and the whole thing felt as grand as a wagon race under a noon sun."
    )
    world.say(
        f"When {helper.id} showed up with {world.gimmick.pitch}, {hero.id} squinted, grinned, and said it {world.gimmick.bonus}."
    )


def take_gimmick(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"So {hero.id} grabbed {world.gimmick.name} and marched off like a tiny sheriff headed for a storm."
    )


def setback(world: World, hero: Entity) -> None:
    hero.meters["wear"] += 1
    hero.meters["dust"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But the gimmick gave a great big flop: {world.gimmick.backlash}."
    )
    world.say(
        f"The road got dustier, the plan got wobblier, and {hero.id} felt as small as a peanut in a barrel."
    )


def lesson(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"Then {helper.id} laughed a kind laugh and said, 'Big talk is not the same as steady feet.'"
    )
    world.say(
        f"{hero.id} nodded, set the gimmick aside, and chose the plain old way: one careful step, then another."
    )


def complete_quest(world: World, hero: Entity) -> None:
    hero.meters["distance"] += world.place.distance
    hero.memes["joy"] += 1
    world.say(
        f"That slow way worked better than any bragging trick. Before the sun slipped down, {hero.id} reached {world.place.label} and got the {world.quest.item} at last."
    )
    world.say(
        f"In the end, {hero.id} came home dusty, cheerful, and wiser, with {world.quest.finish} and a lesson learned the tall-tale way."
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    gimmick = GIMMICKS[params.gimmick]
    reasonableness_gate(place, quest, gimmick)
    world = World(place, quest, gimmick)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    world.facts.update(hero=hero, helper=helper, place=place, quest=quest, gimmick=gimmick, params=params)

    opening(world, hero, helper)
    world.para()
    take_gimmick(world, hero)
    setback(world, hero)
    world.para()
    lesson(world, hero, helper)
    complete_quest(world, hero)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for children about a quest for {f["quest"].item} and a gimmick called {f["gimmick"].name}.',
        f'Tell a short story where {f["hero"].id} tries {f["gimmick"].pitch} but learns a lesson before finishing the quest.',
        f'Write a big, funny adventure with the words "gimmick" and "gots" and an ending that shows a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    gimmick: Gimmick = f["gimmick"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do?",
            answer=f"{hero.id} was trying to {quest.goal}, which meant getting the {quest.item}.",
        ),
        QAItem(
            question=f"What gimmick did {hero.id} trust at first?",
            answer=f"{hero.id} trusted {gimmick.name}, the one that sounded clever but caused trouble.",
        ),
        QAItem(
            question=f"Who helped {hero.id} learn the better way?",
            answer=f"{helper.id} helped by reminding {hero.id} that steady steps work better than bragging tricks.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The lesson was that a big promise is not enough; careful work and patience do the real job.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} bringing home the {quest.item} after choosing the plain, careful way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find, get, or do something important.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding a better way after something goes wrong.",
        ),
        QAItem(
            question="What is a gimmick?",
            answer="A gimmick is a clever trick or device that sounds exciting, but it may not really solve the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: gimmick, quest, lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gimmick", choices=GIMMICKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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
    choices = valid_pairs()
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.quest:
        choices = [c for c in choices if c[1] == args.quest]
    if args.gimmick:
        choices = [c for c in choices if c[2] == args.gimmick]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, quest, gimmick = rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, gimmick=gimmick, name=name, gender=gender, helper=helper, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show quest_combo/3."))
        print(sorted(set(asp.atoms(model, "quest_combo"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hill", quest="kite", gimmick="ladderhat", name="Mabel", gender="girl", helper="mother", trait="brave"),
            StoryParams(place="woods", quest="bell", gimmick="whirlboots", name="Otis", gender="boy", helper="grandpa", trait="curious"),
            StoryParams(place="river", quest="seed", gimmick="megabucket", name="Ruby", gender="girl", helper="aunt", trait="spunky"),
            StoryParams(place="barn", quest="map", gimmick="jumprope", name="Gus", gender="boy", helper="father", trait="stubborn"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
