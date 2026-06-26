#!/usr/bin/env python3
"""
A small superhero storyworld about writing, friendship, and conflict.

A seed tale imagined for this world:
A young hero named Nova wants to write a thank-you note to her best friend
after a rooftop rescue. But her teammate wants to rush off to a new mission
first, and the hero worries their friendship will crack if the note never gets
written. In the end, they pause, write the note together, and the team feels
closer than before.

This script builds that premise into a compact simulation:
- a hero with a cape and a notepad
- a friend who may be hurt or impatient
- a conflict caused by urgency and misunderstanding
- a turn where writing becomes the bridge back to friendship
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
# Entities / world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the skylight roof"
    affords: set[str] = field(default_factory=lambda: {"write", "talk", "watch"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    owner: Optional[str] = None
    worn_by: Optional[str] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "roof": Setting(place="the skylight roof", affords={"write", "talk", "watch"}),
    "tower": Setting(place="the watchtower balcony", affords={"write", "talk", "watch"}),
    "hideout": Setting(place="the team hideout", affords={"write", "talk", "plan"}),
    "library": Setting(place="the city library corner", affords={"write", "talk", "read"}),
}

ACTIONS = {
    "write": Action(
        id="write",
        verb="write a note",
        gerund="writing a note",
        rush="dash off before the ink dries",
        keyword="write",
        tags={"write", "friendship"},
    ),
    "plan": Action(
        id="plan",
        verb="plan the next rescue",
        gerund="planning the next rescue",
        rush="rush to another mission",
        keyword="plan",
        tags={"conflict"},
    ),
    "read": Action(
        id="read",
        verb="read a message",
        gerund="reading a message",
        rush="grab the paper first",
        keyword="read",
        tags={"write", "friendship"},
    ),
}

PROPS = {
    "notebook": Item(
        id="notebook",
        label="a small notebook",
        phrase="a small notebook with a blue star on the cover",
        type="notebook",
    ),
    "cape": Item(
        id="cape",
        label="a red cape",
        phrase="a red cape that snapped in the wind",
        type="cape",
    ),
    "letter": Item(
        id="letter",
        label="a thank-you letter",
        phrase="a thank-you letter folded into a square",
        type="letter",
    ),
}

HERO_NAMES = ["Nova", "Jet", "Mira", "Theo", "Zara", "Kite"]
FRIEND_NAMES = ["Pip", "Rue", "Bex", "Ollie", "Sunny", "Max"]
TRAITS = ["brave", "gentle", "quick", "bold", "curious", "steady"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
action(A) :- act(A).
practical(A) :- action(A), useful(A).
friendship_story(P,A) :- place(P), action(A), writes(A).
conflict_story(P,A) :- place(P), action(A), causes_conflict(A).
valid(P,A) :- place(P), action(A), practical(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIONS.values():
        lines.append(asp.fact("act", a.id))
        if a.id == "write":
            lines.append(asp.fact("useful", a.id))
            lines.append(asp.fact("writes", a.id))
        if a.id == "plan":
            lines.append(asp.fact("causes_conflict", a.id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.action == "write" and params.place not in {"hideout", "library", "tower", "roof"}:
        raise StoryError("This story needs a place where a hero can pause long enough to write.")
    if params.action == "plan" and params.place == "library":
        # okay, but if explicitly choosing a quiet story with conflict, that's fine.
        return

def choose_companion(action: Action) -> str:
    return "friendship" if "friendship" in action.tags else "conflict"

def predict_conflict(world: World, hero: Entity, friend: Entity, action: Action) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    friend2 = sim.get(friend.id)
    if action.id == "plan":
        hero2.memes["rush"] = 1
        friend2.memes["hurt"] = 1
        return True
    if action.id == "write":
        return False
    return False

def introduce(world: World, hero: Entity, friend: Entity, prop: Item, action: Action) -> None:
    world.say(
        f"{hero.id} was a {hero.meters.get('trait', '') or 'young'} {hero.type} who loved {action.gerund} "
        f"with {friend.id} under {world.setting.place}."
    )

def setup(world: World, hero: Entity, friend: Entity, prop: Item, action: Action) -> None:
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    world.say(
        f"One evening, {hero.id} and {friend.id} stood at {world.setting.place}, "
        f"where the city lights blinked below like tiny stars."
    )
    world.say(
        f"{hero.id} carried {prop.phrase}, because {hero.pronoun('possessive')} idea of a good hero day was {action.gerund}."
    )

def conflict_scene(world: World, hero: Entity, friend: Entity, action: Action) -> None:
    hero.memes["concern"] = 1
    friend.memes["rush"] = 1
    world.say(
        f"{hero.id} wanted to {action.verb}, but {friend.id} pointed at the dark sky and said, "
        f'"We have to move now!"'
    )
    world.say(
        f"{hero.id} felt a sharp twist in {hero.pronoun('possessive')} chest. "
        f"{hero.id} worried that if they ran away, the promise between them would break."
    )

def turn_to_write(world: World, hero: Entity, friend: Entity, prop: Item) -> None:
    world.say(
        f"Then {hero.id} opened {prop.label}, took a breath, and began to write."
    )
    world.say(
        f"{hero.id} wrote, 'Thank you for helping me,' and {friend.id} watched the words appear line by line."
    )

def resolve(world: World, hero: Entity, friend: Entity, prop: Item) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["conflict"] = 0
    friend.memes["hurt"] = 0
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"{friend.id}'s face softened. 'You were writing for me?' {friend.id} asked."
    )
    world.say(
        f"{hero.id} nodded, and the two friends finished the note together. "
        f"By the time they tied the letter to the cape, the wind felt less sharp and the roof felt warm."
    )
    world.say(
        f"Below them, the city still needed heroes, but now {hero.id} had something stronger than speed: a friend who understood."
    )

def tell(setting: Setting, action: Action, hero_name: str, hero_type: str, friend_name: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add_entity(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add_entity(Entity(id=friend_name, kind="character", type=friend_type))
    notebook = world.add_item(PROPS["notebook"])
    cape = world.add_item(PROPS["cape"])
    letter = world.add_item(PROPS["letter"])

    world.facts.update(hero=hero, friend=friend, action=action, notebook=notebook, cape=cape, letter=letter)
    world.say(f"{hero.id} was a {trait} young {hero.type}, and {friend.id} was the friend who always ran beside {hero.pronoun('object')}.")
    world.say(f"Together they kept {cape.label} ready for nights when the whole city needed help.")
    world.para()
    setup(world, hero, friend, notebook, action)
    if action.id == "plan":
        conflict_scene(world, hero, friend, action)
    else:
        world.say(
            f"Still, something in the air felt tense, because heroes could save a town and still forget to say thank you."
        )
        conflict_scene(world, hero, friend, action)
    world.para()
    turn_to_write(world, hero, friend, notebook)
    resolve(world, hero, friend, letter)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    return [
        f"Write a short superhero story about {hero.id} and {friend.id} where someone must {action.verb} instead of rushing away.",
        f"Tell a friendship story with capes and city lights, and make the hero write a note that helps fix a conflict.",
        f"Write a gentle superhero tale where a promise, a notebook, and a friend bring two heroes back together.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id} and {friend.id}, two young heroes who had to handle a friendship problem."
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {action.verb}, because that felt like the right heroic thing to do."
        ),
        QAItem(
            question=f"What helped the friendship in the end?",
            answer=f"Writing a note helped the friendship, because {hero.id} and {friend.id} slowed down, listened, and finished the message together."
        ),
        QAItem(
            question=f"How did the conflict end?",
            answer=f"The conflict ended when they chose to write instead of rush away, and the two friends felt close again."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale about brave characters who try to help others, solve problems, and do the right thing."
        ),
        QAItem(
            question="Why can writing help with friendship?",
            answer="Writing can help with friendship because a note can explain feelings, say thank you, or make up after a fight."
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or tension that makes characters disagree, worry, or struggle before they find a way forward."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind}, type={e.type}, meters={e.meters}, memes={e.memes}")
    for i in world.items.values():
        lines.append(f"{i.id}: label={i.label}, type={i.type}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def python_valid_pairs() -> list[tuple]:
    return sorted((p, a) for p in SETTINGS for a in ACTIONS if a == "write" or p in {"hideout", "library", "tower", "roof"})

def asp_verify() -> int:
    py = set(python_valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid pairs.")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about write, friendship, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if hero == friend:
        raise StoryError("Hero and friend must be different characters.")
    return StoryParams(place=place, action=action, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type, trait=trait)

def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        params.hero,
        params.hero_type,
        params.friend,
        params.friend_type,
        params.trait,
    )
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
        pairs = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(pairs)} valid setting/action pairs:")
        for p, a in pairs:
            print(f"  {p} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="roof", action="write", hero="Nova", hero_type="girl", friend="Pip", friend_type="boy", trait="brave"),
            StoryParams(place="tower", action="plan", hero="Jet", hero_type="boy", friend="Rue", friend_type="girl", trait="steady"),
            StoryParams(place="hideout", action="read", hero="Mira", hero_type="girl", friend="Bex", friend_type="boy", trait="gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
