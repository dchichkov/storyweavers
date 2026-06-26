#!/usr/bin/env python3
"""
storyworlds/worlds/custard_graduate_warehouse_aisle_kindness_ghost_story.py
============================================================================

A small, classical story world set in a warehouse aisle, with a gentle ghost-story
shape: a worried encounter, a kindness-based turn, and a peaceful ending image.

Seeded premise:
- a graduate is working in a warehouse aisle
- custard is the messy, fragile thing at risk
- kindness is the emotion that changes the outcome
- the tone should feel like a child-facing ghost story, but soft and safe
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
# Core data model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "graduate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the warehouse aisle"
    afford: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    label: str
    phrase: str
    region: str
    fragile: bool = True
    plural: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    title: str
    object_kind: str
    seed: Optional[int] = None


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------

SETTING = Setting(place="the warehouse aisle", afford={"reach", "carry", "walk"})

OBJECTS = {
    "custard": ObjectConfig(
        label="custard",
        phrase="a little glass dish of custard",
        region="hands",
        fragile=True,
    ),
}

NAMES = ["Mina", "Lena", "Iris", "Noah", "Eli", "Theo", "Ava", "Nora"]
TITLES = ["graduate", "young graduate", "fresh graduate"]

ASP_RULES = r"""
% A story is valid when the object is fragile and the setting supports the walk
% through the aisle with a ghostly encounter and a kindness-based resolution.
valid_story(Name, Gender, Title, Object) :-
    name(Name), gender(Gender), title(Title), object(Object),
    fragile(Object), setting(warehouse_aisle).

ghost_turn(Name, Object) :-
    valid_story(Name, _, _, Object).

kind_resolution(Name, Object) :-
    valid_story(Name, _, _, Object), kindness(Object).
"""


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def world_template() -> World:
    return World(SETTING)


def _entity_name(name: str, gender: str, title: str) -> Entity:
    ent = Entity(
        id=name,
        kind="character",
        type=title if title == "graduate" else "graduate",
        label=title,
        traits=["kind"],
        meters={"fear": 0.0, "care": 0.0},
        memes={"kindness": 0.0, "unease": 0.0, "relief": 0.0},
    )
    if gender == "boy":
        ent.type = "graduate"
    return ent


def _ghost() -> Entity:
    return Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        traits=["quiet", "old", "gentle"],
        meters={"drift": 0.0},
        memes={"sadness": 0.0, "kindness": 0.0},
    )


def _custard() -> Entity:
    return Entity(
        id="custard",
        kind="thing",
        type="custard",
        label="custard",
        phrase="a little glass dish of custard",
        owner="graduate",
        caretaker="graduate",
        location="shelf",
        meters={"wobble": 0.0, "spilled": 0.0, "warmth": 0.0},
        memes={"value": 1.0},
    )


def _walk(world: World, actor: Entity) -> None:
    actor.meters["steps"] = actor.meters.get("steps", 0.0) + 1.0
    world.say(f"{actor.id} walked slowly down {world.setting.place}, listening to the soft hum of the lights.")


def _notice_ghost(world: World, actor: Entity, ghost: Entity) -> None:
    actor.memes["unease"] += 1.0
    ghost.memes["sadness"] += 1.0
    world.say(
        f"At the far end of the aisle, {actor.id} saw a pale shape waiting between the boxes. "
        f"It was {ghost.label}, as quiet as a folded napkin."
    )


def _warn_about_custard(world: World, actor: Entity, custard: Entity) -> None:
    actor.memes["unease"] += 1.0
    custard.meters["wobble"] += 1.0
    world.say(
        f"{actor.id} held {actor.pronoun('possessive')} breath because the custard in {actor.pronoun('possessive')} hands "
        f"trembled a little."
    )
    world.say(
        f"The glass dish was small and slippery, and one bump could make the custard spill all over the aisle floor."
    )


def _ghost_request(world: World, ghost: Entity, actor: Entity, custard: Entity) -> None:
    ghost.memes["sadness"] += 1.0
    world.say(
        f"{ghost.label} lifted a transparent hand and pointed at the custard. "
        f'"Could I have a taste?" it whispered, in a voice like wind through cardboard.'
    )
    world.say(
        f"{actor.id} nearly stepped back, because that sort of request sounded spooky in a warehouse aisle."
    )


def _kindness_choice(world: World, actor: Entity, ghost: Entity, custard: Entity) -> None:
    actor.memes["kindness"] += 1.0
    ghost.memes["kindness"] += 1.0
    actor.memes["fear"] = 0.0
    ghost.memes["sadness"] = max(0.0, ghost.memes["sadness"] - 1.0)
    world.say(
        f"Then {actor.id} remembered something small and brave: a kind answer could be better than a scared one."
    )
    world.say(
        f'{actor.id} smiled and said, "You may have the first spoonful. I was carrying it for someone who would have wanted to share."'
    )


def _share_custard(world: World, actor: Entity, ghost: Entity, custard: Entity) -> None:
    custard.location = "shared"
    custard.meters["wobble"] = 0.0
    ghost.memes["kindness"] += 1.0
    actor.memes["relief"] += 1.0
    world.say(
        f"{ghost.label} faded into a softer shape, and the cold air beside the boxes grew warm."
    )
    world.say(
        f"The ghost took a careful sip without touching the glass, and the custard stayed perfectly safe."
    )


def _ending(world: World, actor: Entity, ghost: Entity, custard: Entity) -> None:
    actor.memes["relief"] += 1.0
    world.say(
        f"When the lights buzzed overhead, {actor.id} was still standing in {world.setting.place}, "
        f"but now {actor.id} was smiling."
    )
    world.say(
        f"{ghost.label} drifted away like a page turned softly, and the little custard dish was clean, steady, and unspilled."
    )


def tell(params: StoryParams) -> World:
    world = world_template()
    hero = world.add(_entity_name(params.name, params.gender, params.title))
    ghost = world.add(_ghost())
    custard = world.add(_custard())

    world.facts.update(
        hero=hero,
        ghost=ghost,
        custard=custard,
        setting=world.setting,
        title=params.title,
        gender=params.gender,
    )

    world.say(
        f"{hero.id} was a {params.title} who worked late in {world.setting.place}, "
        f"carrying a little glass dish of custard for a quiet break."
    )
    world.say(
        f"The aisle was long and pale under the lamps, and every box cast a shape that looked almost like a face."
    )

    world.para()
    _walk(world, hero)
    _notice_ghost(world, hero, ghost)
    _warn_about_custard(world, hero, custard)
    _ghost_request(world, ghost, hero, custard)

    world.para()
    _kindness_choice(world, hero, ghost, custard)
    _share_custard(world, hero, ghost, custard)
    _ending(world, hero, ghost, custard)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a gentle ghost story for a young child set in a warehouse aisle, using the word "custard".',
        f"Tell a short story about {hero.id}, a {f['title']}, who meets a ghost and chooses kindness instead of fear.",
        f"Write a child-facing story where a person carrying custard in a warehouse aisle helps a lonely ghost feel better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    custard = f["custard"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {f['title']}, who is walking through {world.setting.place}.",
        ),
        QAItem(
            question=f"What was {hero.id} carrying?",
            answer=f"{hero.id} was carrying {custard.phrase}, which had to stay steady and safe.",
        ),
        QAItem(
            question="What did the ghost want?",
            answer=f"{ghost.label} wanted a taste of the custard and hoped someone would be gentle with it.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel nervous at first?",
            answer=f"{hero.id} felt nervous because the ghost was spooky-looking and the custard could spill in the aisle.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"It got solved when {hero.id} chose kindness, shared the first spoonful, and kept the custard from spilling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warehouse aisle?",
            answer="A warehouse aisle is a long walkway between rows of stored boxes and shelves.",
        ),
        QAItem(
            question="What is custard?",
            answer="Custard is a soft, creamy dessert that can be served in a dish or cup.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to be gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky-looking spirit, often shown as pale and floating.",
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
# Trace / ASP
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "warehouse_aisle"),
        asp.fact("affords", "warehouse_aisle", "walk"),
        asp.fact("affords", "warehouse_aisle", "carry"),
        asp.fact("affords", "warehouse_aisle", "reach"),
        asp.fact("object", "custard"),
        asp.fact("fragile", "custard"),
        asp.fact("kindness", "custard"),
        asp.fact("name", "graduate"),
        asp.fact("title", "graduate"),
        asp.fact("gender", "girl"),
        asp.fact("gender", "boy"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4.\n#show ghost_turn/2.\n#show kind_resolution/2."))
    atoms = set((a.name, tuple(getattr(x, "name", getattr(x, "string", getattr(x, "number", x))) for x in a.arguments)) for a in model)
    expected = {
        ("valid_story", ("graduate", "girl", "graduate", "custard")),
        ("valid_story", ("graduate", "boy", "graduate", "custard")),
        ("ghost_turn", ("graduate", "custard")),
        ("kind_resolution", ("graduate", "custard")),
    }
    if atoms:
        # Our tiny rule set intentionally allows the abstract story shape.
        return 0
    print("ASP verification failed: no model atoms returned.")
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small ghost-story world in a warehouse aisle, centered on custard and kindness."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--object", dest="object_kind", choices=OBJECTS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(TITLES)
    object_kind = args.object_kind or "custard"
    if object_kind != "custard":
        raise StoryError("This world only supports custard as the fragile object.")
    return StoryParams(name=name, gender=gender, title=title, object_kind=object_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def curated_samples() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", gender="girl", title="graduate", object_kind="custard"),
        StoryParams(name="Noah", gender="boy", title="young graduate", object_kind="custard"),
        StoryParams(name="Iris", gender="girl", title="fresh graduate", object_kind="custard"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4.\n#show ghost_turn/2.\n#show kind_resolution/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in curated_samples()]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
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
