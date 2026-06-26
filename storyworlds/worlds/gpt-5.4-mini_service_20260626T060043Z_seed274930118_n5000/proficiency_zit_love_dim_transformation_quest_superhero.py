#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero-story domain.

Premise:
- A young hero wants to earn proficiency in a power skill.
- A stubborn zit appears before an important quest.
- The hero's love-dim for the city, mentor, or friend becomes the emotional engine.
- A transformation is offered as the turning point: a mask, suit, or calm focus that
  changes how the hero can act.

The world is intentionally small and constraint-checked:
- The quest must be plausible for the hero's current skill.
- The zit must matter to the story and create a social/emotional wrinkle.
- The transformation must actually solve the quest or the confidence problem.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    inside: bool = False
    supports: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    hazard: str
    danger: str
    needed_skill: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    covers: set[str]
    counters: set[str]
    prep: str
    result_line: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "rooftop": Place("the rooftop", inside=False, supports={"dodge", "rescue", "sprint"}),
    "lab": Place("the lab", inside=True, supports={"dodge", "suitup"}),
    "alley": Place("the alley", inside=False, supports={"rescue", "sprint"}),
    "skybridge": Place("the skybridge", inside=False, supports={"dodge", "rescue"}),
}

QUESTS = {
    "rescue": Quest(
        id="rescue",
        verb="rescue the kitten",
        gerund="rescuing the kitten",
        hazard="wind",
        danger="blown off balance",
        needed_skill="bravery",
        zone={"hands", "torso"},
        keyword="rescue",
        tags={"heroic", "helping"},
    ),
    "dodge": Quest(
        id="dodge",
        verb="dodge the hover-drones",
        gerund="dodging the hover-drones",
        hazard="lights",
        danger="spotted",
        needed_skill="speed",
        zone={"head", "torso"},
        keyword="drones",
        tags={"tech", "speed"},
    ),
    "sprint": Quest(
        id="sprint",
        verb="sprint to the alarm tower",
        gerund="sprinting to the alarm tower",
        hazard="rain",
        danger="slipped",
        needed_skill="stamina",
        zone={"legs", "torso"},
        keyword="alarm",
        tags={"speed", "city"},
    ),
}

TRANSFORMS = {
    "mask": Transformation(
        id="mask",
        label="a focused mask",
        phrase="a focused mask with a calm blue stripe",
        covers={"face"},
        counters={"self-conscious"},
        prep="put on the focused mask",
        result_line="The mask helped the hero look steady and feel ready.",
    ),
    "cape": Transformation(
        id="cape",
        label="a wind-proof cape",
        phrase="a wind-proof cape with bright lightning stitching",
        covers={"torso"},
        counters={"wind"},
        prep="fasten the wind-proof cape",
        result_line="The cape held firm against the wind and made the hero feel bigger than fear.",
    ),
    "gloves": Transformation(
        id="gloves",
        label="sticky gloves",
        phrase="sticky gloves that helped with careful grabbing",
        covers={"hands"},
        counters={"slippery"},
        prep="pull on the sticky gloves",
        result_line="The gloves kept the hero's hands sure and quick.",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Jace", "Luna", "Tari", "Zane", "Iris", "Kai"]
MENTORS = ["mentor", "captain", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    quest: str
    transform: str
    name: str
    mentor: str
    skill: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def quest_at_risk(quest: Quest, place: Place) -> bool:
    return quest.id in place.supports


def select_transform(quest: Quest) -> Optional[Transformation]:
    for t in TRANSFORMS.values():
        if quest.hazard in t.counters:
            return t
    return None


def build_story_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    transform = TRANSFORMS[params.transform]

    if not quest_at_risk(quest, place):
        raise StoryError("The chosen place does not support this quest.")

    if quest.hazard not in transform.counters:
        raise StoryError(
            f"No transformation in this world can honestly help with {quest.hazard}."
        )

    world = World(place=place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Nova", "Mira", "Luna", "Iris"} else "boy",
        meters={"proficiency": 0.0},
        memes={"love_dim": 0.0, "worry": 0.0, "pride": 0.0, "zit_shame": 0.0},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="mentor",
        label=f"the {params.mentor}",
        meters={"patience": 1.0},
        memes={"care": 1.0},
    ))
    zit = world.add(Entity(
        id="zit",
        type="zit",
        label="a stubborn zit",
        phrase="a stubborn zit right on the hero's cheek",
        owner=hero.id,
        meters={"redness": 1.0, "noticeability": 1.0},
        memes={"self-conscious": 1.0},
    ))
    gear = world.add(Entity(
        id=transform.id,
        type="gear",
        label=transform.label,
        phrase=transform.phrase,
        owner=hero.id,
        protective=True,
        covers=set(transform.covers),
    ))
    world.facts.update(hero=hero, mentor=mentor, zit=zit, gear=gear, quest=quest, transform=transform, place=place)
    return world


def predict_success(world: World, quest: Quest, transform: Transformation) -> bool:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    hero.meters["proficiency"] += 1.0
    if quest.hazard in transform.counters:
        return True
    return hero.meters["proficiency"] >= THRESHOLD


def introduce(world: World, hero: Entity, mentor: Entity) -> None:
    world.say(f"{hero.id} was a young hero who wanted to help the city every day.")
    world.say(f"{hero.pronoun().capitalize()} trained with {mentor.label} and chased tiny sparks of {hero.meters['proficiency']:.0f} skill.")


def start_with_love(world: World, hero: Entity) -> None:
    hero.memes["love_dim"] += 1.0
    world.say(
        f"{hero.id} had a big love-dim for the city: every siren, rooftop, and warm window "
        f"felt like a promise worth keeping."
    )


def show_zit(world: World, hero: Entity, zit: Entity) -> None:
    hero.memes["zit_shame"] += 1.0
    world.say(
        f"Then {zit.label} appeared, bright and annoying, and {hero.id} kept wanting to hide {hero.pronoun('possessive')} face."
    )


def warn_about_quest(world: World, mentor: Entity, hero: Entity, quest: Quest, transform: Transformation) -> None:
    world.say(
        f"That same evening, {mentor.label} pointed toward {world.place.name} and said, "
        f"\"Tonight's quest is to {quest.verb}.\""
    )
    world.say(
        f"{hero.id} wanted to go, but {quest.hazard} could make {hero.pronoun('object')} {quest.danger}, "
        f"and the zit made {hero.pronoun('object')} feel even more exposed."
    )
    hero.memes["worry"] += 1.0
    if predict_success(world, quest, transform):
        world.facts["predicted_success"] = True


def transformation_turn(world: World, hero: Entity, mentor: Entity, transform: Transformation) -> None:
    hero.meters["proficiency"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    world.say(
        f"{mentor.label} reached into {hero.pronoun('possessive')} pack and offered {transform.phrase}. "
        f"\"Try this,\" {mentor.pronoun().capitalize()} said."
    )
    world.say(f"{hero.id} {transform.prep}, and the whole pose changed.")
    world.say(transform.result_line)


def quest_action(world: World, hero: Entity, quest: Quest, transform: Transformation) -> None:
    hero.meters["proficiency"] += 1.0
    hero.memes["pride"] += 1.0
    hero.memes["love_dim"] += 1.0
    world.say(
        f"At {world.place.name}, {hero.id} used {quest.verb} skill and kept {hero.pronoun('possessive')} balance steady."
    )
    world.say(
        f"The {quest.hazard} rushed by, but the new look and calm focus kept {hero.id} from being {quest.danger}."
    )


def ending(world: World, hero: Entity, zit: Entity, quest: Quest) -> None:
    world.say(
        f"When the quest was done, {zit.label} still sat on {hero.id}'s cheek, but it did not matter anymore."
    )
    world.say(
        f"{hero.id} smiled for the city, proud of the growing {hero.meters['proficiency']:.0f} skill and the brighter love-dim inside {hero.pronoun('object')}."
    )


def tell(params: StoryParams) -> World:
    world = build_story_world(params)
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    zit = world.facts["zit"]
    quest = world.facts["quest"]
    transform = world.facts["transform"]

    introduce(world, hero, mentor)
    start_with_love(world, hero)
    world.para()
    show_zit(world, hero, zit)
    warn_about_quest(world, mentor, hero, quest, transform)
    world.para()
    transformation_turn(world, hero, mentor, transform)
    quest_action(world, hero, quest, transform)
    world.para()
    ending(world, hero, zit, quest)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, transform = f["hero"], f["quest"], f["transform"]
    return [
        f'Write a short superhero story for children about {hero.id}, a quest, and a small but annoying zit.',
        f"Tell a gentle superhero tale where {hero.id} must {quest.verb} and learns to use {transform.label}.",
        f'Write a story about "proficiency" growing through practice, love for the city, and a brave transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, quest, transform, zit = f["hero"], f["mentor"], f["quest"], f["transform"], f["zit"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=f"It is a superhero story about {hero.id}, {mentor.label}, a quest, and a transformation that helps {hero.id} act bravely.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried before the quest to {quest.verb}?",
            answer=f"{hero.id} felt worried because {quest.hazard} could make {hero.pronoun('object')} {quest.danger}, and the stubborn zit made {hero.pronoun('object')} feel self-conscious too.",
        ),
        QAItem(
            question=f"What helped {hero.id} get ready for the quest?",
            answer=f"{transform.phrase} helped {hero.id}. It changed how {hero.id} looked and felt, and it matched the danger from {quest.hazard}.",
        ),
        QAItem(
            question=f"What happened to {hero.id}'s proficiency by the end?",
            answer=f"{hero.id}'s proficiency grew because {hero.id} practiced, used the transformation, and finished the quest successfully.",
        ),
        QAItem(
            question=f"Did the zit disappear?",
            answer=f"No, the zit was still there at the end, but it stopped mattering once {hero.id} finished the quest and felt proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest: Quest = f["quest"]
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to do something important, often with a challenge to overcome.",
        ),
        QAItem(
            question="What does proficiency mean?",
            answer="Proficiency means being good at a skill because you have practiced it enough.",
        ),
        QAItem(
            question="What is a zit?",
            answer="A zit is a small bump on the skin, often on the face, that can make someone feel embarrassed even though it is harmless.",
        ),
        QAItem(
            question="What is a transformation in a superhero story?",
            answer="A transformation is a big change in a hero's appearance, tool, or mindset that helps them face danger.",
        ),
        QAItem(
            question=f"Why was the hero's love-dim important in this story?",
            answer=f"It gave {f['hero'].id} the desire to keep helping the city, even when a zit and a risky quest made things harder.",
        ),
        QAItem(
            question=f"What kind of danger was tied to the quest to {quest.verb}?",
            answer=f"The quest was tied to {quest.hazard}, which could make the hero {quest.danger}.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(rooftop). place(lab). place(alley). place(skybridge).
inside(lab).
supports(rooftop,rescue). supports(rooftop,dodge). supports(rooftop,sprint).
supports(lab,dodge). supports(lab,suitup).
supports(alley,rescue). supports(alley,sprint).
supports(skybridge,dodge). supports(skybridge,rescue).

quest(rescue). quest(dodge). quest(sprint).
hazard(rescue,wind). hazard(dodge,lights). hazard(sprint,rain).
zone(rescue,hands). zone(rescue,torso).
zone(dodge,head). zone(dodge,torso).
zone(sprint,legs). zone(sprint,torso).

transform(mask). transform(cape). transform(gloves).
covers(mask,face). counters(mask,self-conscious).
covers(cape,torso). counters(cape,wind).
covers(gloves,hands). counters(gloves,slippery).

valid(Place,Quest,Transform) :- supports(Place,Quest), hazard(Quest,H), counters(Transform,H).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].inside:
            lines.append(asp.fact("inside", p))
        for q in sorted(PLACES[p].supports):
            lines.append(asp.fact("supports", p, q))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        lines.append(asp.fact("hazard", q, QUESTS[q].hazard))
        for z in sorted(QUESTS[q].zone):
            lines.append(asp.fact("zone", q, z))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
        for c in sorted(TRANSFORMS[t].covers):
            lines.append(asp.fact("covers", t, c))
        for c in sorted(TRANSFORMS[t].counters):
            lines.append(asp.fact("counters", t, c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in PLACES.items():
        for qid, q in QUESTS.items():
            if qid not in p.supports:
                continue
            for tid, t in TRANSFORMS.items():
                if q.hazard in t.counters:
                    out.append((place, qid, tid))
    return out


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python gate ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only ASP:", sorted(a - b))
    print("only Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: proficiency, zit, love-dim, transformation, quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("--skill", default="proficiency")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.transform:
        combos = [c for c in combos if c[2] == args.transform]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, transform = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        quest=quest,
        transform=transform,
        name=args.name or rng.choice(HERO_NAMES),
        mentor=args.mentor or rng.choice(MENTORS),
        skill=args.skill,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("\n== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, quest, transform in triples:
            print(f"  {place:9} {quest:8} {transform}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("rooftop", "rescue", "cape", "Nova", "mentor", "proficiency"),
            StoryParams("lab", "dodge", "mask", "Mira", "captain", "proficiency"),
            StoryParams("alley", "sprint", "gloves", "Jace", "aunt", "proficiency"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
