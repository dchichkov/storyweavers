#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yankee_arrival_quest_humor_sharing_myth.py
==============================================================================================================

A small mythic storyworld about arrival, questing, humor, and sharing.

Seed tale:
---
A traveler called Yankee arrived at a quiet shore carrying a sealed map and a
question in his heart. The old keeper of the shore said the map would only open
for someone who could reach the hill shrine, make the moon statue laugh, and
share what he had with the people waiting there.

Yankee set out at once. The path was steep and the shrine was stern, but Yankee
told a few funny lines to the stone birds, and their caws turned to chuckles.
At the end, Yankee split his travel bread with the keeper and the children.
Then the map opened, not for a prize, but for a promise: the quest was not to
take, but to arrive kindly and leave room for others.

The world model uses:
- meters for physical state: distance, hunger, fatigue, gifts, openness
- memes for emotional state: hope, worry, humor, trust, generosity

Narrative instruments:
- Quest: the hero must reach a sacred place and complete a trial.
- Humor: a funny line lowers tension and opens a path.
- Sharing: food or light is divided, turning strangers into allies.
- Myth: the story is told in a legendary, elder-bard voice.
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "father", "boy", "traveler"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    gate: str
    shrine: str
    welcomes: set[str] = field(default_factory=set)
    mythic: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    trial: str
    reward: str
    risk: str
    required_place: str
    needed_humor: float = 1.0
    needed_sharing: float = 1.0


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "shore": Place(id="shore", label="the quiet shore", gate="sea gate", shrine="moon shrine", welcomes={"traveler", "elder"}),
    "hill": Place(id="hill", label="the windy hill", gate="stone gate", shrine="moon shrine", welcomes={"traveler", "elder"}),
    "courtyard": Place(id="courtyard", label="the old courtyard", gate="oak gate", shrine="sun arch", welcomes={"traveler", "elder", "child"}),
}

QUESTS = {
    "moon": Quest(
        id="moon",
        goal="reach the moon shrine",
        trial="make the stone birds laugh",
        reward="the map opens",
        risk="the keeper refuses the path",
        required_place="shore",
        needed_humor=1.0,
        needed_sharing=1.0,
    ),
    "harbor": Quest(
        id="harbor",
        goal="reach the harbor lantern",
        trial="share bread with the gate watchers",
        reward="the lantern lights the road",
        risk="the gate stays shut",
        required_place="shore",
        needed_humor=1.0,
        needed_sharing=1.0,
    ),
    "hill": Quest(
        id="hill",
        goal="reach the hill shrine",
        trial="tell a joke to the stern idol",
        reward="the idol smiles and points",
        risk="the path remains silent",
        required_place="hill",
        needed_humor=1.0,
        needed_sharing=1.0,
    ),
}

GIFT_KINDS = {
    "bread": ("a round loaf of bread", "bread"),
    "tea": ("a small kettle of tea", "tea"),
    "lamp": ("a little lantern", "lamp"),
}

NAMES = ["Yankee", "Milo", "Iris", "Jonah", "Mara", "Tomas"]
TRAITS = ["brave", "wry", "gentle", "curious", "hopeful"]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def make_world(place: Place, quest: Quest, name: str, gift: str, trait: str) -> World:
    w = World(place)
    hero = w.add(Entity(
        id=name,
        kind="character",
        type="traveler",
        label=name,
        meters={"distance": 0.0, "hunger": 2.0, "fatigue": 1.0, "gift": 1.0},
        memes={"hope": 1.0, "worry": 1.0, "humor": 0.0, "trust": 0.0, "generosity": 0.0},
    ))
    keeper = w.add(Entity(
        id="keeper",
        kind="character",
        type="elder",
        label="the keeper",
        meters={"presence": 1.0},
        memes={"watchful": 1.0, "patience": 1.0},
    ))
    children = w.add(Entity(
        id="children",
        kind="character",
        type="child",
        label="the children",
        plural=True,
        meters={"presence": 1.0},
        memes={"curiosity": 1.0, "hunger": 1.0},
    ))
    item = w.add(Entity(
        id="gift",
        type=gift,
        label=GIFT_KINDS[gift][1],
        phrase=GIFT_KINDS[gift][0],
        owner=hero.id,
        meters={"whole": 1.0},
    ))
    w.facts.update(hero=hero, keeper=keeper, children=children, gift=item, quest=quest, trait=trait)
    return w


def check_fit(world: World, quest: Quest) -> None:
    if world.place.id != quest.required_place:
        raise StoryError(
            f"This quest belongs at {quest.required_place}, but the chosen setting is {world.place.id}."
        )


def predict_outcome(world: World, humor: float, sharing: float) -> dict[str, bool]:
    sim = world.copy()
    sim.get(sim.facts["hero"].id).memes["humor"] = humor
    sim.get(sim.facts["hero"].id).memes["generosity"] = sharing
    return {
        "opens": humor >= 1.0 and sharing >= 1.0,
        "accepted": humor >= 1.0 and sharing >= 1.0,
    }


def arrival(world: World) -> None:
    hero = world.facts["hero"]
    world.say(
        f"One day, {hero.id} arrived at {world.place.label} carrying a sealed map and a steady heart."
    )
    world.say(
        f"The keeper of {world.place.shrine} watched in silence, as if the stones themselves were listening."
    )


def quest_call(world: World) -> None:
    hero = world.facts["hero"]
    q = world.facts["quest"]
    hero.memes["hope"] += 1.0
    hero.meters["distance"] += 1.0
    world.say(
        f"{hero.id} had come for a quest: to {q.goal}, even though {q.risk}."
    )


def climb_and_try(world: World) -> None:
    hero = world.facts["hero"]
    q = world.facts["quest"]
    hero.meters["fatigue"] += 1.0
    hero.meters["distance"] += 1.0
    world.say(
        f"{hero.id} climbed the steep path until the wind tugged at {hero.pronoun('possessive')} sleeves."
    )
    world.say(
        f"At the shrine, {hero.id} tried to {q.trial}, but the stone birds only stared back."
    )
    hero.memes["worry"] += 1.0


def humor_turn(world: World) -> None:
    hero = world.facts["hero"]
    keeper = world.facts["keeper"]
    hero.memes["humor"] += 1.0
    world.say(
        f"Then {hero.id} told a tiny joke about a fish who feared puddles, and the birds blinked."
    )
    world.say(
        f"The keeper's stern mouth twitched, because even old stones like a little laugh."
    )
    keeper.memes["patience"] += 1.0


def sharing_turn(world: World) -> None:
    hero = world.facts["hero"]
    keeper = world.facts["keeper"]
    children = world.facts["children"]
    gift = world.facts["gift"]
    hero.meters["gift"] = 0.0
    hero.meters["hunger"] = max(0.0, hero.meters["hunger"] - 1.0)
    hero.memes["generosity"] += 1.0
    hero.memes["trust"] += 1.0
    world.say(
        f"{hero.id} broke the {gift.label} in two and shared it with {keeper.label} and the waiting children."
    )
    world.say(
        f"The fragrance of the bread softened the air, and {children.label} leaned closer without fear."
    )


def resolve(world: World) -> None:
    hero = world.facts["hero"]
    keeper = world.facts["keeper"]
    q = world.facts["quest"]
    hero.memes["hope"] += 1.0
    keeper.memes["watchful"] += 0.5
    world.say(
        f"At last, the sealed map warmed in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"It opened at once, and {q.reward}; the keeper bowed, for the quest had been answered by arrival, humor, and sharing together."
    )


def tell(place_key: str, quest_key: str, name: str, gift: str, trait: str) -> World:
    place = PLACES[place_key]
    quest = QUESTS[quest_key]
    check_fit(World(place), quest)
    w = make_world(place, quest, name, gift, trait)
    arrival(w)
    quest_call(w)
    climb_and_try(w)
    humor_turn(w)
    sharing_turn(w)
    resolve(w)
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts_for(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f"Write a mythic story about {hero.id} arriving at {world.place.label} for a quest, using humor and sharing to win a blessing.",
        f"Tell an elder-bard tale where a traveler named {hero.id} reaches a shrine, makes the stone birds laugh, and shares food before the final sign appears.",
        f"Create a short myth for a child about arrival, quest, humor, and sharing, ending with a map opening in a sacred place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    quest = f["quest"]
    gift = f["gift"]
    return [
        QAItem(
            question=f"Who arrived at {world.place.label} in the story?",
            answer=f"{hero.id} arrived at {world.place.label} carrying {gift.phrase}.",
        ),
        QAItem(
            question=f"What was {hero.id}'s quest?",
            answer=f"{hero.id}'s quest was to {quest.goal}. The way forward asked for a little humor and a little sharing.",
        ),
        QAItem(
            question=f"Why did the keeper finally allow the quest to succeed?",
            answer=f"The keeper saw that {hero.id} could laugh gently, share {gift.label}, and treat the people there with kindness. That was enough to open the path.",
        ),
        QAItem(
            question=f"What changed at the end of the myth?",
            answer=f"At the end, the sealed map opened, and the quest turned into a welcome instead of a test. {hero.id} left the shrine with trust and the people with bread shared among them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in a myth?",
            answer="A quest is a journey or task where someone must travel, face a test, and learn something important before they can finish.",
        ),
        QAItem(
            question="Why can humor help strangers?",
            answer="Humor can help because a kind joke makes people relax, feel safer, and listen with less fear.",
        ),
        QAItem(
            question="Why is sharing food important in stories?",
            answer="Sharing food shows generosity, and it can turn strangers into allies by making everyone feel included.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(shore). place(hill). place(courtyard).
quest(moon). quest(harbor). quest(hill).
gift(bread). gift(tea). gift(lamp).

requires(shore, moon).
requires(shore, harbor).
requires(hill, hill).

needs_humor(moon). needs_sharing(moon).
needs_humor(harbor). needs_sharing(harbor).
needs_humor(hill). needs_sharing(hill).

valid(P, Q) :- place(P), quest(Q), requires(P, Q).
complete(Q) :- valid(P, Q), needs_humor(Q), needs_sharing(Q).
#show valid/2.
#show complete/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid in GIFT_KINDS:
        lines.append(asp.fact("gift", gid))
    for place_id, quest in (("shore", "moon"), ("shore", "harbor"), ("hill", "hill")):
        lines.append(asp.fact("requires", place_id, quest))
    for qid in QUESTS:
        lines.append(asp.fact("needs_humor", qid))
        lines.append(asp.fact("needs_sharing", qid))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, q) for p, place in PLACES.items() for q, quest in QUESTS.items() if p == quest.required_place)


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gift: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="shore", quest="moon", name="Yankee", gift="bread", trait="wry"),
    StoryParams(place="shore", quest="harbor", name="Mara", gift="tea", trait="gentle"),
    StoryParams(place="hill", quest="hill", name="Jonah", gift="lamp", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest:
        if (args.place, args.quest) not in valid_combos():
            raise StoryError("That quest does not belong in that place.")
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, quest = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    gift = args.gift or rng.choice(list(GIFT_KINDS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gift=gift, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.quest, params.name, params.gift, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: arrival, quest, humor, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gift", choices=GIFT_KINDS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
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
