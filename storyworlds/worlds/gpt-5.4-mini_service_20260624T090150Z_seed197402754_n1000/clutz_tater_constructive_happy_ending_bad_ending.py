#!/usr/bin/env python3
"""
A small comedy storyworld about a clumsy helper, a tater, and a constructive
plan that can go hilariously wrong before turning into a happy ending.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

@dataclass
class CharacterSpec:
    type: str
    label: str


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    kind: str
    mess: str
    zone: str
    requires_constructive: bool = False


@dataclass
class EndingSpec:
    label: str
    image: str
    happy: bool
    surprise: bool = False


PLACES = {
    "kitchen": "the kitchen",
    "backyard": "the backyard",
    "garage": "the garage",
    "playroom": "the playroom",
}

CHARACTERS = {
    "clutz": CharacterSpec(type="boy", label="Clutz"),
    "tater": CharacterSpec(type="boy", label="Tater"),
    "constructive": CharacterSpec(type="girl", label="Constructive"),
}

OBJECTS = {
    "spoon": ObjectSpec(label="spoon", phrase="a shiny spoon", kind="metal", mess="clanky", zone="table"),
    "cake": ObjectSpec(label="cake", phrase="a frosted cake", kind="food", mess="squashed", zone="counter"),
    "kite": ObjectSpec(label="kite", phrase="a bright kite", kind="toy", mess="tangled", zone="yard"),
    "tower": ObjectSpec(label="tower", phrase="a block tower", kind="blocks", mess="toppled", zone="floor", requires_constructive=True),
}

ENDINGS = {
    "happy": EndingSpec(label="Happy Ending", image="the room ended tidy, with everyone laughing", happy=True),
    "bad": EndingSpec(label="Bad Ending", image="the mess stayed messy, and the sighs were long", happy=False),
    "surprise": EndingSpec(label="Surprise", image="the tater was hiding under a bowl with a grin", happy=True, surprise=True),
}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    object: str
    ending: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in CHARACTERS:
            for obj in OBJECTS:
                for ending in ENDINGS:
                    if hero == "constructive" and obj != "tower":
                        continue
                    if ending == "bad" and hero == "constructive":
                        continue
                    combos.append((place, hero, obj, ending))
    return combos


def explain_rejection(hero: str, obj: str, ending: str) -> str:
    if hero == "constructive" and obj != "tower":
        return "(No story: Constructive is the helper for fixing a tower, so this seed needs the tower object.)"
    if ending == "bad" and hero == "constructive":
        return "(No story: a bad ending is too mean for Constructive in this comedy setup.)"
    return "(No story: that combination is not reasonable for this small storyworld.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])

    hero_spec = CHARACTERS[params.hero]
    obj_spec = OBJECTS[params.object]
    ending_spec = ENDINGS[params.ending]

    hero = world.add(Entity(id="hero", kind="character", type=hero_spec.type, label=hero_spec.label))
    tater = world.add(Entity(id="tater", kind="character", type="boy", label="Tater"))
    helper = world.add(Entity(id="constructive", kind="character", type="girl", label="Constructive"))
    object_ent = world.add(Entity(id="object", type=obj_spec.kind, label=obj_spec.label, phrase=obj_spec.phrase))

    world.facts.update(
        hero=hero,
        tater=tater,
        helper=helper,
        object=object_ent,
        ending=ending_spec,
        obj_spec=obj_spec,
        place=world.place,
    )
    return world


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    obj = world.facts["object"]
    world.say(
        f"{hero.label} was a cheerful clutz who meant well, even when {hero.pronoun()} got "
        f"his toes and elbows into trouble."
    )
    world.say(
        f"One day, {hero.label} saw {obj.phrase} and decided it needed a constructive plan."
    )


def middle_turn(world: World) -> None:
    hero = world.facts["hero"]
    tater = world.facts["tater"]
    helper = world.facts["helper"]
    obj = world.facts["object"]
    obj_spec = world.facts["obj_spec"]

    world.para()
    world.say(
        f"In {world.place}, {hero.label} tried to help by moving things faster than {hero.pronoun()} could think."
    )
    world.say(
        f"{hero.label} bumped the table, and {obj.label} went wobble-wobble-whoops."
    )

    if obj_spec.requires_constructive:
        world.say(
            f"Constructive hurried over and said, \"No panic. We can make this a build-back-better day.\""
        )
        world.say(
            f"She stacked blocks carefully, turning the toppled tower into a sturdier one with a funny hat on top."
        )
        world.facts["fixed"] = True
    else:
        world.say(
            f"Tater ducked under the chair and declared, \"I meant to do that,\" which was such a bold lie that everyone laughed."
        )
        world.say(
            f"Constructive used a napkin, a spoon, and one very serious face to put the mess back in order."
        )
        world.facts["fixed"] = True

    world.facts["surprise"] = False
    if world.facts["ending"].surprise:
        world.say(
            f"Then came a surprise: Tater popped up with a tiny grin and a crumb on his nose."
        )
        world.say(
            f"He had been hiding the snack all along, hoping to save it for the perfect moment."
        )
        world.facts["surprise"] = True


def resolve(world: World) -> None:
    ending = world.facts["ending"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    tater = world.facts["tater"]
    obj = world.facts["object"]

    world.para()
    if ending.happy:
        if ending.surprise:
            world.say(
                f"In the end, {hero.label}, {helper.label}, and {tater.label} shared the snack, and nobody cared that the floor had briefly looked like a silly puzzle."
            )
        else:
            world.say(
                f"In the end, their constructive plan worked, {obj.label} was safe again, and the room looked proud of itself."
            )
        world.say(
            f"{hero.label} grinned because even a clutz can help when friends stay patient."
        )
    else:
        world.say(
            f"Bad ending: the mess won this round, and {hero.label} had to sit down and stare at the wobble with a tiny embarrassed sigh."
        )
        world.say(
            f"Even so, {helper.label} said they could try again tomorrow, which was at least a very constructive idea."
        )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    middle_turn(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child about {f["hero"].label}, {f["tater"].label}, and a constructive fix.',
        f"Tell a funny story set in {world.place} where a clutz causes a mess and a surprise changes the ending.",
        f"Write a tiny story that includes the words clutz, tater, and constructive and ends with a clear ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    tater = f["tater"]
    helper = f["helper"]
    obj = f["object"]
    ending = f["ending"]

    items = [
        QAItem(
            question=f"Who was the clutz in the story?",
            answer=f"{hero.label} was the clutz, and he kept meaning well even while making a funny mess.",
        ),
        QAItem(
            question=f"What did the characters need to fix?",
            answer=f"They needed to fix {obj.phrase} after {hero.label} bumped it and made things wobble.",
        ),
        QAItem(
            question=f"Who helped make the plan constructive?",
            answer=f"{helper.label} helped by turning the problem into a careful, constructive plan.",
        ),
    ]
    if ending.surprise:
        items.append(
            QAItem(
                question="What was the surprise?",
                answer=f"The surprise was that {tater.label} had been hiding the snack with a crumb on his nose.",
            )
        )
    if ending.happy:
        items.append(
            QAItem(
                question="How did the story end?",
                answer="It ended happily, with the mess fixed and everyone laughing together.",
            )
        )
    else:
        items.append(
            QAItem(
                question="How did the story end?",
                answer="It ended badly for the mess, but the friends still planned to try again tomorrow.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does constructive mean?",
            answer="Constructive means helpful in a way that builds something better or fixes a problem.",
        ),
        QAItem(
            question="What is a clutz?",
            answer="A clutz is a person who is clumsy and often knocks things over by accident.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you are not looking for it.",
        ),
        QAItem(
            question="What is a tater?",
            answer="A tater is a playful word for a potato, and sometimes it is used like a funny nickname.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero_ok(H) :- hero(H).
object_ok(O) :- object(O).
ending_ok(E) :- ending(E).

valid(Place, Hero, Object, Ending) :-
    place(Place),
    hero(Hero),
    object(Object),
    ending(Ending),
    not bad_combo(Hero, Object, Ending).

bad_combo(constructive, O, _) :- object(O), O != tower.
bad_combo(constructive, _, bad).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in CHARACTERS:
        lines.append(asp.fact("hero", h))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for e in ENDINGS:
        lines.append(asp.fact("ending", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / emit / main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: clutz, tater, constructive, and a surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=CHARACTERS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--ending", choices=ENDINGS)
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
    if args.hero == "constructive" and args.object and args.object != "tower":
        raise StoryError(explain_rejection("constructive", args.object, args.ending or "happy"))
    if args.ending == "bad" and args.hero == "constructive":
        raise StoryError(explain_rejection("constructive", args.object or "tower", "bad"))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hero is None or c[1] == args.hero)
              and (args.object is None or c[2] == args.object)
              and (args.ending is None or c[3] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hero, obj, ending = rng.choice(sorted(combos))
    return StoryParams(place=place, hero=hero, object=obj, ending=ending)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  place={world.place}")
    lines.append(f"  facts={ {k: v for k, v in world.facts.items() if k not in {'hero','tater','helper','object','ending','obj_spec'}} }")
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="kitchen", hero="clutz", object="cake", ending="happy"),
            StoryParams(place="garage", hero="tater", object="spoon", ending="surprise"),
            StoryParams(place="playroom", hero="constructive", object="tower", ending="happy"),
            StoryParams(place="backyard", hero="clutz", object="kite", ending="bad"),
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
