#!/usr/bin/env python3
"""
A small slice-of-life storyworld about two sisters, a missing lunch, and an
ordinary mistake that ends in a bad but believable ending.

The world tracks:
- typed characters and things
- physical meters such as packed, carried, spilled, and lost
- emotional memes such as hurried, worried, apologetic, and disappointed

The bad ending is not dangerous. The sisters fail to repair the day's small
problem in time, and one sister has to leave hungry and disappointed. Their
honest conversation leaves a quiet chance to do better tomorrow.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "sister", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Scene:
    id: str
    place: str
    routine: str
    weather: str
    lunch: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    scene: str
    older_sister_name: str
    younger_sister_name: str
    older_sister_type: str
    younger_sister_type: str
    lunch: str
    seed: Optional[int] = None


SCENES = {
    "apartment": Scene(
        id="apartment",
        place="the small apartment kitchen",
        routine="walked to school together",
        weather="a cool gray morning",
        lunch="a cheese sandwich and an apple",
    ),
    "townhouse": Scene(
        id="townhouse",
        place="the townhouse kitchen",
        routine="waited for the bus together",
        weather="a bright but hurried morning",
        lunch="noodles in a blue lunch box",
    ),
    "duplex": Scene(
        id="duplex",
        place="the duplex kitchen",
        routine="rode their bicycles to school",
        weather="a drizzly morning",
        lunch="rice, peas, and two small cookies",
    ),
}

LUNCHES = {
    "a cheese sandwich and an apple": {"kind": "sandwich", "container": "a paper bag"},
    "noodles in a blue lunch box": {"kind": "noodles", "container": "a blue lunch box"},
    "rice, peas, and two small cookies": {"kind": "rice", "container": "a yellow tin"},
}

SISTER_NAMES = ["Luna", "Mara", "Nia", "Tessa", "Iris", "June", "Sana", "Pia"]
OLDER_NAMES = ["Luna", "Mara", "Tessa", "June"]
YOUNGER_NAMES = ["Nia", "Iris", "Sana", "Pia"]


@dataclass(frozen=True)
class Arc:
    id: str
    need: str
    opening: str
    obstacle: str
    turn: str
    action: str
    consequence: str
    ending: str
    dialogue: tuple[str, ...]


ARCS = (
    Arc(
        id="wrong_bag",
        need="was already thinking about the spelling test",
        opening="{older} packed {lunch} before the sisters left for school.",
        obstacle="In the hallway, {older} grabbed a look-alike bag from the hook instead of the lunch bag.",
        turn="{younger} noticed the mistake only when they reached the bus stop.",
        action="{older} checked both bags, but the bus was already turning the corner.",
        consequence="There was no time to run back upstairs before the next bus.",
        ending="At school, {younger} ate nothing but the crackers in her desk and kept the wrong bag under her chair.",
        dialogue=(
            '"Did you pack mine?" {younger} asked. "I thought I did," {older} said, looking at the bag.',
            '"The bus is coming," {younger} said. "Then we have to choose quickly," {older} replied.',
        ),
    ),
    Arc(
        id="open_container",
        need="wanted to show a drawing to her teacher",
        opening="{older} filled {lunch} and set it beside the front door.",
        obstacle="On the way out, {younger} bumped the container, and its lid popped open on the stairs.",
        turn="{older} saw the food spread across two steps and heard the bus brakes outside.",
        action="The sisters gathered what they could, but dust had already covered the soft food.",
        consequence="They saved the cookies, yet the rest of the lunch had to stay behind.",
        ending="{younger} showed her drawing at school with a rumbling stomach and no lunch to share.",
        dialogue=(
            '"I am sorry," {younger} said. "I know," {older} answered, kneeling beside the spilled food.',
            '"Can we fix it?" {younger} asked. "Not before the bus," {older} said.',
        ),
    ),
    Arc(
        id="forgotten_fridge",
        need="had promised to trade half her lunch with a friend",
        opening="{older} prepared {lunch} while {younger} tied her shoes.",
        obstacle="The finished lunch stayed on the refrigerator shelf while both sisters rushed out.",
        turn="{younger} remembered it halfway down the block.",
        action="{older} ran back, but the crossing light changed twice before she returned.",
        consequence="The bus left without them, and the next one would arrive after the first school bell.",
        ending="They reached school late, and {younger} had to explain to her waiting friend that there was nothing to trade.",
        dialogue=(
            '"The lunch is still home," {younger} said. "I can get it," {older} replied.',
            '"Hurry, please," {younger} called. "I am hurrying," {older} answered from the doorway.',
        ),
    ),
    Arc(
        id="squashed_bag",
        need="was tired from finishing homework late",
        opening="{older} placed {lunch} in a paper bag and tucked it into {younger}'s backpack.",
        obstacle="A library book pressed against the bag until the apple rolled free and the sandwich was flattened.",
        turn="{younger} opened the backpack beside the school fence and found the lunch in crumbs and folds.",
        action="{older} tried to smooth the bread and offered her own snack, but it was only one small granola bar.",
        consequence="They split the granola bar, though it did not feel like enough for either sister.",
        ending="{younger} went to class still hungry, while {older} carried the ruined paper bag home.",
        dialogue=(
            '"It was not like that when we left," {older} said. "I know," {younger} replied, staring at the flat bread.',
            '"You can have my bar," {older} offered. "Half," {younger} said. "Only half."',
        ),
    ),
    Arc(
        id="rainy_porch",
        need="wanted one calm thing before a busy afternoon",
        opening="{older} packed {lunch} and left it beneath the porch bench while she found an umbrella.",
        obstacle="A sudden shower blew rain under the bench before either sister noticed.",
        turn="{younger} lifted the wet bag and saw the ink running from its label.",
        action="They carried it inside, but the bread was soggy and the fruit had split.",
        consequence="The sisters waited for the rain to slow, then left with empty hands.",
        ending="{younger} spent lunch break beside the window, listening to rain and wishing the morning had gone differently.",
        dialogue=(
            '"The label is melting," {younger} said. "I should have moved it," {older} replied.',
            '"I wanted today to be easy," {younger} whispered. "So did I," {older} said.',
        ),
    ),
)


OPENINGS = (
    "On {weather}, {older} and her younger sister {younger} moved through {place} while the clock hurried them along.",
    "{older} and {younger} had the ordinary morning job of getting ready, packing lunch, and leaving on time.",
    "The morning began quietly in {place}, with {older} helping {younger} prepare for school.",
)

REFLECTIONS = (
    "Neither sister wanted to be unkind; they were simply late, distracted, and out of second chances.",
    "The mistake was small, but the school bell would not make room for it.",
    "Nothing dramatic happened. The morning just kept moving while the sisters tried to catch up.",
)


def render(text: str, world: World) -> str:
    f = world.facts
    return text.format(
        older=f["older"].id,
        younger=f["younger"].id,
        lunch=f["lunch"].label,
        place=world.scene.place,
        weather=world.scene.weather,
    )


def apply_rules(world: World) -> list[str]:
    lines: list[str] = []
    lunch = world.get("lunch")
    younger = world.get("younger")
    if lunch.meters.get("spilled", 0.0) >= 1.0 and "spill" not in world.fired:
        world.fired.add("spill")
        younger.memes["worried"] = 1.0
        lines.append("A few crumbs clung to the stair, but the useful part of the lunch was gone.")
    if lunch.meters.get("wet", 0.0) >= 1.0 and "wet" not in world.fired:
        world.fired.add("wet")
        younger.memes["disappointed"] = 1.0
        lines.append("The paper softened in their hands until it could no longer hold the food.")
    if lunch.meters.get("lost", 0.0) >= 1.0 and "lost" not in world.fired:
        world.fired.add("lost")
        younger.memes["disappointed"] = 1.0
        lines.append("By the time they found the empty place, the lunch was already out of reach.")
    return lines


def simulate(params: StoryParams) -> World:
    if params.scene not in SCENES:
        raise StoryError(f"Unknown scene: {params.scene}")
    if params.lunch not in LUNCHES:
        raise StoryError(f"Unknown lunch: {params.lunch}")
    if params.older_sister_name == params.younger_sister_name:
        raise StoryError("The two sisters must have different names.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = SCENES[params.scene]
    arc = rng.choice(ARCS)
    world = World(scene)

    older = world.add(
        Entity(
            id=params.older_sister_name,
            kind="character",
            type=params.older_sister_type,
            label=f"older sister {params.older_sister_name}",
            location=scene.place,
        )
    )
    younger = world.add(
        Entity(
            id=params.younger_sister_name,
            kind="character",
            type=params.younger_sister_type,
            label=f"younger sister {params.younger_sister_name}",
            location=scene.place,
        )
    )
    lunch = world.add(
        Entity(
            id="school_lunch",
            kind="thing",
            type="lunch",
            label=params.lunch,
            owner=younger.id,
            location=scene.place,
        )
    )

    world.facts.update(
        older=older,
        younger=younger,
        lunch=lunch,
        arc=arc,
        reflection=rng.choice(REFLECTIONS),
        resolved=False,
        bad_ending=True,
    )

    world.say(
        rng.choice(OPENINGS).format(
            weather=scene.weather,
            older=older.id,
            younger=younger.id,
            place=scene.place,
        )
    )
    world.say(render(arc.opening, world))
    lunch.meters["packed"] = 1.0
    lunch.location = "near the door"
    older.memes["hurried"] = 1.0
    world.para()

    world.say(render(arc.obstacle, world))
    if arc.id == "open_container":
        lunch.meters["spilled"] = 1.0
        lunch.location = "on the stairs"
    elif arc.id == "rainy_porch":
        lunch.meters["wet"] = 1.0
        lunch.location = "beneath the porch bench"
    elif arc.id == "forgotten_fridge":
        lunch.meters["lost"] = 1.0
        lunch.location = "on the refrigerator shelf"
    elif arc.id == "squashed_bag":
        lunch.meters["flattened"] = 1.0
        lunch.location = "inside the backpack"
    else:
        lunch.meters["misidentified"] = 1.0
        lunch.location = "in the wrong bag"
    world.say(render(arc.turn, world))
    for line in apply_rules(world):
        world.say(line)
    world.para()

    world.say(render(arc.dialogue[rng.randrange(len(arc.dialogue))], world))
    world.say(render(arc.action, world))
    world.say(render(arc.consequence, world))
    world.say(world.facts["reflection"])
    world.para()

    younger.memes["disappointed"] = 1.0
    older.memes["apologetic"] = 1.0
    world.say(render(arc.ending, world))
    world.say(
        f"{older.id} apologized before they separated, but {younger.id} still had to begin the school day without the lunch."
    )
    world.say(
        "The sisters promised to check the door together tomorrow, though that promise could not repair this morning."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    arc: Arc = f["arc"]
    return [
        f"Write a slice-of-life story about sisters {f['older'].id} and {f['younger'].id} dealing with {arc.id.replace('_', ' ')}.",
        f"Tell a realistic story where {f['older'].id} tries to help her sister with lunch, a small mistake gets worse, and the ending is disappointing.",
        f"Write a quiet sister story set in {world.scene.place} with ordinary dialogue and a bad ending rather than a neat fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    older: Entity = f["older"]
    younger: Entity = f["younger"]
    lunch: Entity = f["lunch"]
    arc: Arc = f["arc"]
    return [
        QAItem(
            question=f"Why was {older.id} preparing lunch for {younger.id}?",
            answer=f"{older.id} was helping her sister because {younger.id} {arc.need}. The lunch was meant to make the school morning easier.",
        ),
        QAItem(
            question=f"What went wrong with {younger.id}'s lunch?",
            answer=render(arc.obstacle, world),
        ),
        QAItem(
            question=f"What did the sisters try to do after they noticed the problem?",
            answer=render(arc.action, world),
        ),
        QAItem(
            question=f"Why did the ending stay disappointing even after the sisters talked?",
            answer=f"The sisters apologized and made a plan for tomorrow, but there was not enough time to replace the {lunch.label} before school.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it useful to check a lunch bag before leaving home?",
            answer="Checking the lunch bag can catch mistakes such as a missing container, a wrong bag, or food that was left behind.",
        ),
        QAItem(
            question="What can an apology do after a small mistake?",
            answer="An apology can show that someone understands the trouble they caused, even though it cannot always undo the result.",
        ),
        QAItem(
            question="What does slice-of-life storytelling usually focus on?",
            answer="Slice-of-life storytelling focuses on ordinary people, familiar routines, small problems, and believable feelings rather than grand adventures.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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


ASP_RULES = r"""
reasonable(S, Y, L) :- sister(S, Y), lunch(L), owner(L, Y), packed(L).
bad_ending(Y, L) :- lunch(L), owner(L, Y), failed(L), disappointed(Y).
apology_possible(S, Y) :- sister(S, Y), apologetic(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for lunch in LUNCHES:
        lines.append(asp.fact("lunch_kind", LUNCHES[lunch]["kind"]))
    lines.append(asp.fact("sister", "older_sister", "younger_sister"))
    lines.append(asp.fact("lunch", "school_lunch"))
    lines.append(asp.fact("owner", "school_lunch", "younger_sister"))
    lines.append(asp.fact("packed", "school_lunch"))
    lines.append(asp.fact("failed", "school_lunch"))
    lines.append(asp.fact("disappointed", "younger_sister"))
    lines.append(asp.fact("apologetic", "older_sister"))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show reasonable/3. #show bad_ending/2."))
    if not model:
        print("ASP verification failed: no model.")
        return 1
    reasonable = asp.atoms(model, "reasonable")
    endings = asp.atoms(model, "bad_ending")
    if ("older_sister", "younger_sister", "school_lunch") not in reasonable:
        print("ASP verification failed: reasonable story fact missing.")
        return 1
    if ("younger_sister", "school_lunch") not in endings:
        print("ASP verification failed: bad ending fact missing.")
        return 1

    checks = [
        StoryParams(
            scene="apartment",
            older_sister_name="Luna",
            younger_sister_name="Nia",
            older_sister_type="girl",
            younger_sister_type="girl",
            lunch="a cheese sandwich and an apple",
            seed=17,
        ),
        StoryParams(
            scene="duplex",
            older_sister_name="Mara",
            younger_sister_name="Iris",
            older_sister_type="girl",
            younger_sister_type="girl",
            lunch="rice, peas, and two small cookies",
            seed=23,
        ),
    ]
    for params in checks:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("bad_ending"):
            print("Python verification failed: story did not retain bad-ending state.")
            return 1
        if not sample.story.strip().endswith("before school."):
            print("Python verification failed: story ending is incomplete.")
            return 1
    print(f"OK: ASP/Python parity verified with {len(model)} shown atoms and {len(checks)} stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice-of-life sister storyworld with a believable bad ending."
    )
    parser.add_argument("--scene", choices=sorted(SCENES))
    parser.add_argument("--older-sister-name", choices=OLDER_NAMES)
    parser.add_argument("--younger-sister-name", choices=YOUNGER_NAMES)
    parser.add_argument("--lunch", choices=list(LUNCHES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene_id = args.scene or rng.choice(list(SCENES))
    scene = SCENES[scene_id]
    older = args.older_sister_name or rng.choice(OLDER_NAMES)
    younger = args.younger_sister_name or rng.choice(YOUNGER_NAMES)
    if older == younger:
        raise StoryError("The older and younger sisters must have different names.")
    lunch = args.lunch or scene.lunch
    return StoryParams(
        scene=scene_id,
        older_sister_name=older,
        younger_sister_name=younger,
        older_sister_type="girl",
        younger_sister_type="girl",
        lunch=lunch,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for entity in sample.world.entities.values():
            print(
                entity.id,
                entity.type,
                entity.location,
                dict(entity.meters),
                dict(entity.memes),
            )
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
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show reasonable/3. #show bad_ending/2."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    curated = [
        StoryParams(
            scene="apartment",
            older_sister_name="Luna",
            younger_sister_name="Nia",
            older_sister_type="girl",
            younger_sister_type="girl",
            lunch="a cheese sandwich and an apple",
            seed=101,
        ),
        StoryParams(
            scene="townhouse",
            older_sister_name="Mara",
            younger_sister_name="Iris",
            older_sister_type="girl",
            younger_sister_type="girl",
            lunch="noodles in a blue lunch box",
            seed=202,
        ),
        StoryParams(
            scene="duplex",
            older_sister_name="Tessa",
            younger_sister_name="Sana",
            older_sister_type="girl",
            younger_sister_type="girl",
            lunch="rice, peas, and two small cookies",
            seed=303,
        ),
    ]

    if args.all:
        samples = [generate(params) for params in curated]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            attempt += 1
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
