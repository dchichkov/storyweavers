#!/usr/bin/env python3
"""
storyworlds/worlds/dismiss_panda_children_s_museum_friendship_pirate.py
=======================================================================

A standalone story world for a tiny Pirate Tale–style adventure in a children's
museum, where a child and a panda friend must handle a dismissal and keep their
friendship strong.

Seed tale sketch:
---
A small child comes to a children's museum dressed like a little pirate and
brings along a panda friend. They love exploring the ship exhibit together.
But when the museum guide says it is time to leave, the child feels sad and
tries to stay. The guide dismisses the protest, and the child worries the day
is ending too soon. Then the panda friend helps the child make a brave goodbye
plan: they leave a treasure note, promise to return, and walk out together
smiling.

Core causal shape:
---
    explore exhibit                 -> joy + curiosity
    closing call / dismissal        -> sadness + urgency
    child clings to friend          -> friendship tested
    helper offers keepsake / plan    -> courage + friendship + resolution
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
class Setting:
    place: str = "the children's museum"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    type: str
    trait: str = ""


@dataclass
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTING = Setting(place="the children's museum", affords={"pirate_play", "map_making", "ship_story"})


ACTIVITIES = {
    "pirate_play": Activity(
        id="pirate_play",
        verb="play pirates",
        gerund="playing pirates",
        rush="dash back to the ship exhibit",
        mess="scuffed",
        zone={"hands", "feet"},
        keyword="pirate",
        tags={"pirate", "ship"},
    ),
    "map_making": Activity(
        id="map_making",
        verb="draw a treasure map",
        gerund="drawing treasure maps",
        rush="grab the crayons and draw fast",
        mess="smeared",
        zone={"hands"},
        keyword="map",
        tags={"map", "treasure"},
    ),
    "ship_story": Activity(
        id="ship_story",
        verb="listen to a pirate story",
        gerund="listening to pirate stories",
        rush="run to the story rug",
        mess="tired",
        zone={"mind"},
        keyword="story",
        tags={"story", "pirate"},
    ),
}


PARTNERS = {
    "panda": Keepsake(
        id="panda",
        label="panda friend",
        phrase="a soft panda friend with a striped scarf",
        type="panda",
        trait="gentle",
    ),
    "note": Keepsake(
        id="note",
        label="treasure note",
        phrase="a tiny treasure note",
        type="note",
        trait="hopeful",
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Jack", "Noah", "Eli"]
TRAITS = ["brave", "curious", "cheerful", "spirited", "playful", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    partner: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate-flavored children's museum story about friendship and dismissal."
    )
    ap.add_argument("--place", choices=[SETTING.place])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--partner", choices=PARTNERS, default="panda")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    if args.place and args.place != SETTING.place:
        raise StoryError("The requested place is not available in this world.")
    return StoryParams(
        place=SETTING.place,
        activity=activity,
        partner=args.partner,
        name=name,
        gender=gender,
        trait=trait,
    )


def pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type="adult",
        label="museum guide",
        traits=["kind", "steady"],
    ))
    partner = world.add(Entity(
        id=params.partner,
        kind="character",
        type="panda",
        label="panda friend",
        traits=["gentle", "loyal"],
    ))
    keepsake = world.add(Entity(
        id="note",
        type="note",
        label="treasure note",
        phrase="a tiny treasure note",
        owner=hero.id,
    ))
    return world


def opening(world: World, hero: Entity, partner: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('possessive')} {hero.type} who loved the "
        f"{world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and the {partner.label} liked {activity.gerund} "
        f"by the ship exhibit, pretending the floor was a rolling sea."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    world.facts["hero"] = hero
    world.facts["partner"] = partner
    world.facts["activity"] = activity


def closing_call(world: World, hero: Entity, guide: Entity, partner: Entity) -> None:
    world.para()
    hero.memes["sadness"] = hero.memes.get("sadness", 0) + 1
    world.say(
        f"Then the museum lights blinked soft and low, and the {guide.label} said it was time to leave."
    )
    world.say(
        f"{hero.id} did not want the day to end. {hero.pronoun().capitalize()} tried to stay by the ship, "
        f"but the {guide.label} gently dismissed {hero.pronoun('object')} with a shake of the head."
    )
    hero.memes["dismissed"] = hero.memes.get("dismissed", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} clutched the {partner.label} close and felt the fun slipping away like water from a bucket."
    )


def bridge(world: World, hero: Entity, partner: Entity, activity: Activity) -> None:
    world.para()
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.say(
        f"Then the {partner.label} nudged {hero.pronoun('object')} and pointed at a scrap of paper."
    )
    world.say(
        f"{hero.id} got an idea: {hero.pronoun().capitalize()} could leave a treasure note and come back another day."
    )
    hero.meters["resolve"] = hero.meters.get("resolve", 0) + 1


def ending(world: World, hero: Entity, guide: Entity, partner: Entity, activity: Activity) -> None:
    note = world.add(Entity(
        id="note",
        type="note",
        label="treasure note",
        phrase="a tiny treasure note",
        owner=hero.id,
    ))
    note.worn_by = None
    hero.memes["sadness"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} drew a little ship on the note and wrote, 'See you soon, friend.'"
    )
    world.say(
        f"The {guide.label} smiled, and the {partner.label} stayed beside {hero.pronoun('object')} while "
        f"{hero.id} walked out with a brave grin."
    )
    world.say(
        f"By the door, {hero.id} turned once more toward the pirate ship, and the {partner.label} waved like a tiny first mate."
    )
    world.facts["note"] = note
    world.facts["guide"] = guide
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get(params.name)
    guide = world.get("Guide")
    partner = world.get(params.partner)
    activity = ACTIVITIES[params.activity]
    opening(world, hero, partner, activity)
    closing_call(world, hero, guide, partner)
    bridge(world, hero, partner, activity)
    ending(world, hero, guide, partner, activity)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    activity = f["activity"]
    return [
        f'Write a short pirate-style story for a child named {hero.id} in a children\'s museum with a panda friend.',
        f"Tell a gentle story where {hero.id} wants to {activity.verb}, but a museum guide dismisses the delay and the panda friend helps with a goodbye plan.",
        f'Write a small friendship story that includes a panda, a treasure note, and the word "dismiss".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    activity = f["activity"]
    guide = f["guide"]
    return [
        QAItem(
            question=f"Who is the story about at the children's museum?",
            answer=f"The story is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} panda friend.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the ship exhibit?",
            answer=f"{hero.id} wanted to {activity.verb} and keep the pirate game going a little longer.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel sad when the guide spoke?",
            answer=f"{hero.id} felt sad because the {guide.label} said it was time to leave and dismissed the idea of staying longer.",
        ),
        QAItem(
            question=f"How did the panda friend help {hero.id} at the end?",
            answer=f"The panda friend helped by pointing out the note idea, so {hero.id} could make a brave goodbye and keep the friendship strong.",
        ),
        QAItem(
            question=f"What did {hero.id} leave behind?",
            answer=f"{hero.id} left a treasure note that promised a future visit.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a panda?",
            answer="A panda is a black-and-white bear that looks fluffy and gentle.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind bond between friends who care about each other and help each other feel better.",
        ),
        QAItem(
            question="What does dismiss mean?",
            answer="To dismiss someone can mean to send them away or say that it is time to stop and leave.",
        ),
        QAItem(
            question="What is a museum?",
            answer="A museum is a place where people can look at special things, learn, and explore new ideas.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place=SETTING.place, activity="pirate_play", partner="panda", name="Mia", gender="girl", trait="brave"),
    StoryParams(place=SETTING.place, activity="map_making", partner="panda", name="Leo", gender="boy", trait="curious"),
    StoryParams(place=SETTING.place, activity="ship_story", partner="panda", name="Nora", gender="girl", trait="gentle"),
]


ASP_RULES = r"""
activity_ok(A) :- activity(A).
friendship_theme.
dismissal_happens :- dismissed(guide).
resolution :- note_made, friendship_theme.
valid_story(Place, Activity, Partner) :- setting(Place), activity_ok(Activity), partner(Partner),
                                         theme(friendship), setting_place(Place).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    lines.append(asp.fact("setting_place", SETTING.place))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PARTNERS:
        lines.append(asp.fact("partner", p))
    lines.append(asp.fact("theme", "friendship"))
    lines.append(asp.fact("style", "pirate"))
    lines.append(asp.fact("setting", "childrens_museum"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(SETTING.place, a, "panda") for a in ACTIVITIES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params_from_explicit(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != SETTING.place:
        raise StoryError("This world only takes place in the children's museum.")
    activity = args.activity or rng.choice(list(ACTIVITIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=SETTING.place,
        activity=activity,
        partner=args.partner,
        name=name,
        gender=gender,
        trait=trait,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (panda friendship)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
