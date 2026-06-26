#!/usr/bin/env python3
"""
A nursery-rhyme storyworld set in a shopping mall, with dialogue,
repetition, and a gentle transformation at the center of the tale.

Premise:
A small child goes to the shopping mall with a shiny coin and hears a
repeating little song about "hallelujahs" in the echoing halls.

Turn:
A wishing machine or toy-window display offers a simple transformation:
one dull paper crown can become a bright parade crown if the child shares
a kind word and repeats the song.

Resolution:
The child speaks with a helper, repeats the rhyme, and the object changes
from plain to lovely. The mall feels brighter, and the story ends on a
happy, sing-song image.

This world is self-contained and classical: it models a tiny simulated
domain with meters and memes, a reasonableness gate, and an ASP twin.
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
# Model
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
    transformed_from: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap(self) -> str:
        return self.id.capitalize()


@dataclass
class Place:
    id: str = "mall"
    label: str = "the shopping mall"
    echo: bool = True
    shines: bool = True


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    from_form: str
    to_form: str
    spark: str
    requires: str = "hallelujahs"


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    charm: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACE = Place()

CHARMS = {
    "paper_crown": Charm(
        id="paper_crown",
        label="paper crown",
        phrase="a plain paper crown",
        from_form="plain paper crown",
        to_form="bright parade crown",
        spark="golden stars",
    ),
    "tin_bell": Charm(
        id="tin_bell",
        label="tin bell",
        phrase="a small tin bell",
        from_form="small tin bell",
        to_form="shining choir bell",
        spark="silver rings",
    ),
    "wooden_mask": Charm(
        id="wooden_mask",
        label="wooden mask",
        phrase="a wooden mask",
        from_form="wooden mask",
        to_form="smiling festival mask",
        spark="soft ribbons",
    ),
}

HEROES = [
    ("Mia", "girl"),
    ("Noah", "boy"),
    ("Lily", "girl"),
    ("Theo", "boy"),
    ("Ava", "girl"),
]

HELPERS = [
    ("Mimi", "girl"),
    ("Pip", "boy"),
    ("Nana", "woman"),
    ("Papa", "man"),
]

TRAITS = ["gentle", "cheery", "little", "bright", "tiny"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reasonable(place: str, charm: str) -> bool:
    return place == "mall" and charm in CHARMS


def explain_rejection(place: str, charm: str) -> str:
    if place != "mall":
        return "(No story: this nursery-rhyme world is only set in the shopping mall.)"
    return "(No story: that charm is not in the tiny mall transformation cabinet.)"


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when it is set in the mall, the charm exists,
% and the transformation is supported by the rhyming chorus.
can_story(P, C) :- place(P), charm(C), mall(P), supports_hallelujahs(C).

% The transformation is allowed only after the repeated song is heard.
transforms(C) :- supports_hallelujahs(C), repeats_song.

#show can_story/2.
#show transforms/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "mall"),
        asp.fact("mall", "mall"),
        asp.fact("repeats_song"),
    ]
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("supports_hallelujahs", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/2.\n#show transforms/1."))
    seen_can = set(asp.atoms(model, "can_story"))
    seen_transforms = set(asp.atoms(model, "transforms"))
    py_can = {(PLACE.id, cid) for cid in CHARMS}
    py_transforms = {cid for cid in CHARMS}
    asp_can = {(a, b) for (a, b) in seen_can}
    asp_transforms = {a for (a,) in seen_transforms}
    if asp_can != py_can or asp_transforms != py_transforms:
        print("MISMATCH between ASP and Python reasonableness.")
        if asp_can != py_can:
            print("  can_story only in ASP:", sorted(asp_can - py_can))
            print("  can_story only in Python:", sorted(py_can - asp_can))
        if asp_transforms != py_transforms:
            print("  transforms only in ASP:", sorted(asp_transforms - py_transforms))
            print("  transforms only in Python:", sorted(py_transforms - asp_transforms))
        return 1
    print("OK: ASP and Python agree.")
    return 0


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(PLACE)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    charm_def = CHARMS[params.charm]
    charm = world.add(Entity(
        id=charm_def.id,
        kind="thing",
        type="charm",
        label=charm_def.label,
        phrase=charm_def.phrase,
        owner=hero.id,
        meters={"plain": 1.0},
        memes={"want": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, charm=charm, charm_def=charm_def, params=params)
    return world


def rhyme_opening(world: World) -> None:
    h = world.facts["hero"]
    c = world.facts["charm"]
    world.say(
        f"At the shopping mall, {h.id} went tripping past the bright glass hall, "
        f"with a little heart and a little call: hallelujahs, hallelujahs, down the mall."
    )
    world.say(
        f"{h.id} had {h.pronoun('possessive')} {c.label}, plain as could be, and wanted it to sparkle for all to see."
    )


def dialogue(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    charm = world.facts["charm"]
    world.say(
        f'"What is it for?" asked {helper.id}. "{h.id}, why do you hold that crown so near?"'
    )
    world.say(
        f'"For hallelujahs," said {h.id}, "and for a merry cheer. If I sing it once, I sing it twice, '
        f'and the mall sounds sweet and nice."'
    )
    world.say(
        f'"Then sing it again," said {helper.id}, "soft and clear. Repetition can wake a little spark in here."'
    )
    world.facts["repeats"] = 2


def transformation(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    charm = world.facts["charm"]
    charm_def = world.facts["charm_def"]

    if world.facts.get("repeats", 0) < 2:
        raise StoryError("The nursery-rhyme transformation needs the song repeated at least twice.")

    if not reasonable("mall", charm.id):
        raise StoryError(explain_rejection("mall", charm.id))

    charm.meters["plain"] = 0.0
    charm.meters["bright"] = 1.0
    charm.transformed_from = charm_def.from_form
    charm.type = "festival_charm"
    charm.label = charm_def.to_form
    charm.phrase = f"a {charm_def.to_form}"
    charm.memes["joy"] = 1.0
    world.facts["transformed"] = True
    world.say(
        f"{h.id} sang, and sang again: hallelujahs, hallelujahs, all through the air. "
        f"Then {charm_def.spark} flashed like fairy lights there and there."
    )
    world.say(
        f"The plain {charm_def.from_form} turned into a {charm_def.to_form}, "
        f"and {helper.id} clapped while the mall seemed to smile."
    )


def ending(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    charm = world.facts["charm"]
    world.say(
        f"So {h.id} wore the bright new crown, and walked the mall with a proud little sway, "
        f"singing hallelujahs, hallelujahs, in a nursery-rhyme way."
    )
    world.say(
        f"{helper.id} walked beside {h.id}, and the shiny halls kept the tune. "
        f"The little change stayed changed, like a star on a spoon."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    rhyme_opening(world)
    world.para()
    dialogue(world)
    world.para()
    transformation(world)
    world.para()
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    c = world.facts["charm_def"]
    return [
        'Write a nursery-rhyme story set in a shopping mall about hallelujahs, a little dialogue, and a transformation.',
        f'Write a gentle story where {p.hero} and {p.helper} talk in the shopping mall and a {c.from_form} becomes a {c.to_form}.',
        f'Write a sing-song story that repeats "hallelujahs" and ends with a shiny change at the mall.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = world.facts["hero"]
    helper = world.facts["helper"]
    c = world.facts["charm_def"]
    return [
        QAItem(
            question=f"Where did {h.id} go in the story?",
            answer=f"{h.id} went to the shopping mall, where the halls echoed with hallelujahs.",
        ),
        QAItem(
            question=f"What did {helper.id} ask {h.id} to do?",
            answer=f"{helper.id} asked {h.id} to sing the rhyme again, because repeating the song could wake the little spark.",
        ),
        QAItem(
            question=f"What changed from plain to bright?",
            answer=f"The plain {c.from_form} changed into a {c.to_form}. That was the story's little transformation.",
        ),
        QAItem(
            question=f"Why was the song important in the story?",
            answer=f"The song mattered because hallelujahs were repeated, and the repeated rhyme helped the transformation happen.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shopping mall?",
            answer="A shopping mall is a big building with many stores, shiny floors, and places where people walk and shop together.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying or doing something again and again, which can make a story feel musical and easy to remember.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form, like something plain becoming something bright.",
        ),
        QAItem(
            question="What are hallelujahs?",
            answer="Hallelujahs are joyful words or song sounds used to praise or celebrate something happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed_from:
            bits.append(f"transformed_from={e.transformed_from}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP entry
# ---------------------------------------------------------------------------
def asp_show() -> str:
    return asp_program("#show can_story/2.\n#show transforms/1.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme shopping mall storyworld with hallelujahs.")
    ap.add_argument("--place", choices=["mall"], default="mall")
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[n for n, _ in HELPERS])
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--charm", choices=CHARMS)
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
    hero, hero_type = rng.choice(HEROES)
    helper, helper_type = rng.choice(HELPERS)
    charm = rng.choice(list(CHARMS))

    if args.hero is not None:
        hero = args.hero
    if args.hero_type is not None:
        hero_type = args.hero_type
    if args.helper is not None:
        helper = args.helper
    if args.helper_type is not None:
        helper_type = args.helper_type
    if args.charm is not None:
        charm = args.charm

    if args.place != "mall":
        raise StoryError(explain_rejection(args.place, charm))

    return StoryParams(
        place="mall",
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        charm=charm,
    )


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


CURATED = [
    StoryParams(place="mall", hero="Mia", hero_type="girl", helper="Nana", helper_type="woman", charm="paper_crown"),
    StoryParams(place="mall", hero="Noah", hero_type="boy", helper="Pip", helper_type="boy", charm="tin_bell"),
    StoryParams(place="mall", hero="Lily", hero_type="girl", helper="Papa", helper_type="man", charm="wooden_mask"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_show())
        can = sorted(set(asp.atoms(model, "can_story")))
        trans = sorted(set(asp.atoms(model, "transforms")))
        print(f"can_story: {can}")
        print(f"transforms: {trans}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
