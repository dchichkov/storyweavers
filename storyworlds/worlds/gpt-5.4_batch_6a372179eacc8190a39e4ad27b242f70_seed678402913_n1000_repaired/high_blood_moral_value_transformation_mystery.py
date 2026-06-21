#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py
==============================================================================

A standalone story world for a child-friendly mystery about a trail of red drops
found beneath a high place. The drops first look like blood, but the mystery is
solved by clues, honesty, and a gentle transformation project that changes an
ordinary object into something bright and beautiful.

The world models:
- a child solver noticing a red trail under a high shelf or ledge
- a helper who has accidentally spilled a red material while working on a
  transformation project
- suspicion, clue-gathering, worry, confession, relief, and repair
- a reasonableness gate: only some red materials fit some transformation projects

The story aims for a TinyStories-style mystery:
beginning -> strange clue -> careful investigation -> honest confession ->
ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py
    python storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py --all
    python storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/high_blood_moral_value_transformation_mystery.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    high_place: str
    floor: str
    tone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    spill_word: str
    smell: str
    clue: str
    material: str
    looks_like_blood: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    start_item: str
    final_item: str
    process: str
    material_need: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeightSpot:
    id: str
    phrase: str
    path: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def source_fits_project(source: Source, project: Project) -> bool:
    return source.material == project.material_need and source.looks_like_blood


def honesty_leads_early_confession(helper_trait: str, adult_nearby: bool) -> bool:
    brave_traits = {"honest", "gentle", "careful"}
    return helper_trait in brave_traits or adult_nearby


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for source_id, source in SOURCES.items():
            for project_id, project in PROJECTS.items():
                for height_id in HEIGHTS:
                    if source_fits_project(source, project):
                        combos.append((setting_id, source_id, project_id, height_id))
    return combos


def explain_rejection(source: Source, project: Project) -> str:
    return (
        f"(No story: {source.label} does not sensibly fit the project of turning "
        f"{project.start_item} into {project.final_item}. The red clue should come "
        f"from the same material that helps the transformation happen.)"
    )


def investigate(world: World, solver: Entity, helper: Entity, source: Source, height: HeightSpot) -> None:
    solver.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{solver.id} saw tiny red drops on {world.setting.floor}. They led from {height.phrase} "
        f"down in a crooked little trail."
    )
    world.say(
        f'"That looks like blood," {solver.id} whispered, and the room suddenly felt more mysterious.'
    )
    if helper.memes["worry"] >= THRESHOLD:
        world.say(
            f"{helper.id} grew very still beside {solver.pronoun('object')}. "
            f"{helper.pronoun('possessive').capitalize()} eyes flicked to {height.phrase} and back again."
        )


def clue_step(world: World, solver: Entity, source: Source, project: Project, height: HeightSpot) -> None:
    world.say(
        f"{solver.id} stood on tiptoe and looked up. On {height.phrase} sat {source.phrase}, "
        f"and nearby lay {project.start_item} waiting to change."
    )
    world.say(
        f"There was no hurt animal, no broken toe, no sad cry at all. Instead there was {source.clue}."
    )
    if source.smell:
        world.say(f"The air even smelled faintly of {source.smell}.")


def confess(world: World, helper: Entity, source: Source, project: Project, early: bool) -> None:
    helper.memes["honesty"] += 1
    helper.memes["worry"] = 0.0
    helper.memes["relief"] += 1
    if early:
        world.say(
            f'"Wait," {helper.id} said, tugging at {helper.pronoun("possessive")} sleeves. '
            f'"It is not blood. I spilled {source.label}."'
        )
    else:
        world.say(
            f"At last {helper.id} took a breath and told the truth. "
            f'"It is not blood," {helper.pronoun()} said softly. "I spilled {source.label}."'
        )
    world.say(
        f'{helper.pronoun("subject").capitalize()} had wanted to use it to {project.process}, '
        f'but had been afraid of getting in trouble for the mess.'
    )


def repair_and_transform(world: World, solver: Entity, helper: Entity, adult: Entity, source: Source, project: Project) -> None:
    solver.memes["relief"] += 1
    helper.memes["trust"] += 1
    solver.memes["kindness"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over with a damp cloth. "
        f'"Thank you for telling the truth," {adult.pronoun()} said. '
        f'"A spill can be cleaned. Honesty helps much faster than hiding."'
    )
    world.say(
        f"So the three of them wiped up the red trail together. Then {helper.id} tried again, "
        f"this time more slowly, and {project.process}."
    )
    world.say(
        f"Soon {project.ending_image}. The scary mystery melted into a bright surprise."
    )


def tell(
    setting: Setting,
    source: Source,
    project: Project,
    height: HeightSpot,
    solver_name: str = "Lina",
    solver_gender: str = "girl",
    helper_name: str = "Owen",
    helper_gender: str = "boy",
    helper_trait: str = "honest",
    adult_type: str = "mother",
    adult_nearby: bool = True,
) -> World:
    world = World(setting)
    solver = world.add(Entity(
        id=solver_name,
        kind="character",
        type=solver_gender,
        role="solver",
        traits=["curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
    ))
    adult = world.add(Entity(
        id="Parent",
        kind="character",
        type=adult_type,
        role="adult",
        label="the parent",
    ))
    world.add(Entity(
        id="source",
        type="source",
        label=source.label,
        phrase=source.phrase,
        tags=set(source.tags),
    ))
    world.add(Entity(
        id="project",
        type="project",
        label=project.final_item,
        phrase=project.final_item,
        tags=set(project.tags),
    ))

    world.say(
        f"One quiet day in {setting.place}, {solver.id} and {helper.id} were working at a small table. "
        f"The room felt soft and still, except for the hush around {setting.high_place}."
    )
    world.say(
        f"{helper.id} had a plan to turn {project.start_item} into {project.final_item}. "
        f"It felt like a tiny kind of transformation magic."
    )

    world.para()
    investigate(world, solver, helper, source, height)

    early = honesty_leads_early_confession(helper_trait, adult_nearby)
    if not early:
        clue_step(world, solver, source, project, height)

    world.para()
    confess(world, helper, source, project, early)

    world.para()
    repair_and_transform(world, solver, helper, adult, source, project)

    outcome = "early_confession" if early else "confession_after_clues"
    world.facts.update(
        solver=solver,
        helper=helper,
        adult=adult,
        source_cfg=source,
        project_cfg=project,
        setting=setting,
        height=height,
        adult_nearby=adult_nearby,
        outcome=outcome,
        looked_like_blood=source.looks_like_blood,
        moral="honesty",
        transformed=True,
    )
    return world


KNOWLEDGE = {
    "blood": [
        (
            "What is blood?",
            "Blood is the red liquid inside bodies that helps carry important things around. If someone is bleeding, a grown-up should help right away.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something that seems hard to explain at first. You solve it by noticing clues and thinking carefully.",
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty helps people fix problems together. Telling the truth quickly can stop fear from growing bigger.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean?",
            "Transformation means something changes into a new form or look. A plain object can be transformed into something colorful or special.",
        )
    ],
    "beet": [
        (
            "Why can beet juice look like blood?",
            "Beet juice is deep red, so a spill can look surprising at first. But it is plant juice, not blood.",
        )
    ],
    "berry": [
        (
            "Why do berries leave red stains?",
            "Many berries have strong colored juice inside them. When they burst, the juice can leave bright red or purple marks.",
        )
    ],
    "paint": [
        (
            "Why can red paint make a mess?",
            "Red paint spreads in drops and smears if it tips over. That is why people use cups, brushes, and cloths when they paint.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    solver = f["solver"]
    helper = f["helper"]
    source = f["source_cfg"]
    project = f["project_cfg"]
    setting = f["setting"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old that includes the words "high" and "blood".',
        f"Tell a story where {solver.id} finds red drops beneath a high place in {setting.place} and first thinks they might be blood, but the truth is kinder.",
        f"Write a child-facing mystery in which {helper.id} tells the truth after a spill, and the ending shows {project.start_item} transformed into {project.final_item}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    solver = f["solver"]
    helper = f["helper"]
    adult = f["adult"]
    source = f["source_cfg"]
    project = f["project_cfg"]
    height = f["height"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {solver.id} and {helper.id} in {f['setting'].place}. They solve a small mystery together with {adult.label_word}.",
        ),
        (
            f"Why did {solver.id} think the red drops might be blood?",
            f"{solver.id} saw a red trail on {f['setting'].floor} under {height.phrase}, and it looked strange and sudden. With no answer yet, the drops felt mysterious and a little scary.",
        ),
        (
            f"What was the red trail really made of?",
            f"It was really {source.label}, not blood. {helper.id} had spilled it while trying to {project.process}.",
        ),
    ]
    if outcome == "confession_after_clues":
        qa.append(
            (
                f"How was the mystery solved?",
                f"{solver.id} looked for clues instead of running away. When {solver.pronoun()} noticed {source.clue} near {project.start_item}, {helper.id} felt safe enough to tell the truth.",
            )
        )
    else:
        qa.append(
            (
                f"How was the mystery solved so quickly?",
                f"{helper.id} chose honesty and spoke up right away. That stopped the fear from growing and helped everyone understand the red drops were not blood.",
            )
        )
    qa.append(
        (
            f"What moral did {helper.id} learn?",
            f"{helper.id} learned that telling the truth is better than hiding a mistake. Once {helper.pronoun()} was honest, everyone could clean up together and keep going.",
        )
    )
    qa.append(
        (
            "What changed by the end of the story?",
            f"The frightening mystery changed into a happy transformation. After the spill was cleaned, {project.start_item} became {project.final_item}.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"blood", "mystery", "honesty", "transformation"}
    source = world.facts["source_cfg"]
    if source.material == "beet":
        tags.add("beet")
    elif source.material == "berry":
        tags.add("berry")
    elif source.material == "paint":
        tags.add("paint")
    out: list[tuple[str, str]] = []
    order = ["blood", "mystery", "honesty", "transformation", "beet", "berry", "paint"]
    for tag in order:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.traits:
            bits.append(f"traits={entity.traits}")
        if entity.tags:
            bits.append(f"tags={sorted(entity.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(bits)}")
    facts = {
        "outcome": world.facts.get("outcome"),
        "moral": world.facts.get("moral"),
        "transformed": world.facts.get("transformed"),
        "adult_nearby": world.facts.get("adult_nearby"),
    }
    lines.append(f"  facts={facts}")
    return "\n".join(lines)


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic playroom",
        high_place="the high rafters",
        floor="the wooden floor",
        tone="hushed",
        tags={"mystery"},
    ),
    "library": Setting(
        id="library",
        place="the little library corner",
        high_place="the high book ledge",
        floor="the checkerboard floor",
        tone="quiet",
        tags={"mystery"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the warm greenhouse room",
        high_place="the high plant shelf",
        floor="the stone floor",
        tone="glassy",
        tags={"mystery"},
    ),
}

SOURCES = {
    "beet_jar": Source(
        id="beet_jar",
        label="beet juice",
        phrase="a small jar of beet juice",
        spill_word="dripped",
        smell="earthy beets",
        clue="a purple-red brush and beet-stained napkin",
        material="beet",
        tags={"blood", "beet"},
    ),
    "berry_bowl": Source(
        id="berry_bowl",
        label="crushed berry juice",
        phrase="a bowl of crushed berry juice",
        spill_word="splashed",
        smell="sweet berries",
        clue="berry skins and a sticky spoon",
        material="berry",
        tags={"blood", "berry"},
    ),
    "paint_cup": Source(
        id="paint_cup",
        label="red paint",
        phrase="a wobbly cup of red paint",
        spill_word="spilled",
        smell="paint",
        clue="a wet brush and a red thumbprint",
        material="paint",
        tags={"blood", "paint"},
    ),
    "tomato_soup": Source(
        id="tomato_soup",
        label="tomato soup",
        phrase="a bowl of tomato soup",
        spill_word="dribbled",
        smell="tomatoes",
        clue="a spoon and a supper napkin",
        material="soup",
        tags={"food"},
    ),
}

PROJECTS = {
    "mask": Project(
        id="mask",
        start_item="a plain paper mask",
        final_item="a bright fox mask",
        process="brush the red color across a plain paper mask until it turned into a bright fox mask",
        material_need="paint",
        ending_image="the mask gleamed orange-red on the table like a tiny festival face",
        tags={"transformation", "paint"},
    ),
    "banner": Project(
        id="banner",
        start_item="a white cloth banner",
        final_item="a ruby garden banner",
        process="dab the color into a white cloth banner until it turned into a ruby garden banner",
        material_need="berry",
        ending_image="the banner hung by the window, no longer plain at all, but soft and red in the light",
        tags={"transformation", "berry"},
    ),
    "egg": Project(
        id="egg",
        start_item="a pale egg for the craft basket",
        final_item="a rosy speckled egg",
        process="dip a pale egg into the color until it turned into a rosy speckled egg",
        material_need="beet",
        ending_image="the little egg sat in its nest cup looking newly rosy and almost magical",
        tags={"transformation", "beet"},
    ),
}

HEIGHTS = {
    "shelf": HeightSpot(
        id="shelf",
        phrase="the high shelf",
        path="down from the high shelf to the floor",
        tags={"high"},
    ),
    "ledge": HeightSpot(
        id="ledge",
        phrase="the high window ledge",
        path="down from the high window ledge to the floor",
        tags={"high"},
    ),
    "stool_top": HeightSpot(
        id="stool_top",
        phrase="the top of a high stool",
        path="down from the top of the high stool to the floor",
        tags={"high"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ella", "Ruby", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Finn", "Sam", "Theo", "Max", "Eli"]
HELPER_TRAITS = ["honest", "gentle", "careful", "shy", "worried", "timid"]


@dataclass
class StoryParams:
    setting: str
    source: str
    project: str
    height: str
    solver_name: str
    solver_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    adult: str
    adult_nearby: bool = True
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="attic",
        source="paint_cup",
        project="mask",
        height="shelf",
        solver_name="Lina",
        solver_gender="girl",
        helper_name="Owen",
        helper_gender="boy",
        helper_trait="honest",
        adult="mother",
        adult_nearby=True,
    ),
    StoryParams(
        setting="library",
        source="berry_bowl",
        project="banner",
        height="ledge",
        solver_name="Maya",
        solver_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        helper_trait="shy",
        adult="father",
        adult_nearby=False,
    ),
    StoryParams(
        setting="greenhouse",
        source="beet_jar",
        project="egg",
        height="stool_top",
        solver_name="Leo",
        solver_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        helper_trait="careful",
        adult="mother",
        adult_nearby=True,
    ),
]


ASP_RULES = r"""
fits(S, P) :- source(S), project(P), material(S, M), needs(P, M), looks_like_blood(S).

early_confession :- helper_trait(T), brave_trait(T).
early_confession :- adult_nearby.

outcome(early_confession) :- early_confession.
outcome(confession_after_clues) :- not early_confession.

valid(Setting, Source, Project, Height) :-
    setting(Setting), source(Source), project(Project), height(Height),
    fits(Source, Project).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("material", source_id, source.material))
        if source.looks_like_blood:
            lines.append(asp.fact("looks_like_blood", source_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("needs", project_id, project.material_need))
    for height_id in HEIGHTS:
        lines.append(asp.fact("height", height_id))
    for trait in sorted({"honest", "gentle", "careful"}):
        lines.append(asp.fact("brave_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("helper_trait", params.helper_trait),
            asp.fact("adult_nearby") if params.adult_nearby else "",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "early_confession" if honesty_leads_early_confession(params.helper_trait, params.adult_nearby) else "confession_after_clues"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A child-friendly mystery about red drops under a high place, honesty, and a transformation project."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--height", choices=HEIGHTS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--adult-nearby", dest="adult_nearby", action="store_true", help="adult is close enough that the helper confesses sooner")
    ap.add_argument("--adult-away", dest="adult_nearby", action="store_false", help="adult is not nearby, so clues may be needed before confession")
    ap.set_defaults(adult_nearby=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.project:
        source = SOURCES[args.source]
        project = PROJECTS[args.project]
        if not source_fits_project(source, project):
            raise StoryError(explain_rejection(source, project))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.source is None or combo[1] == args.source)
        and (args.project is None or combo[2] == args.project)
        and (args.height is None or combo[3] == args.height)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, project_id, height_id = rng.choice(sorted(combos))
    solver_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    solver_name = _pick_name(rng, solver_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=solver_name)
    helper_trait = rng.choice(HELPER_TRAITS)
    adult = args.adult or rng.choice(["mother", "father"])
    adult_nearby = args.adult_nearby if args.adult_nearby is not None else rng.choice([True, False])
    return StoryParams(
        setting=setting_id,
        source=source_id,
        project=project_id,
        height=height_id,
        solver_name=solver_name,
        solver_gender=solver_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        adult=adult,
        adult_nearby=adult_nearby,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.height not in HEIGHTS:
        raise StoryError(f"(Unknown height: {params.height})")
    source = SOURCES[params.source]
    project = PROJECTS[params.project]
    if not source_fits_project(source, project):
        raise StoryError(explain_rejection(source, project))

    world = tell(
        setting=SETTINGS[params.setting],
        source=source,
        project=project,
        height=HEIGHTS[params.height],
        solver_name=params.solver_name,
        solver_gender=params.solver_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        adult_type=params.adult,
        adult_nearby=params.adult_nearby,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, source, project, height) combos:\n")
        for setting_id, source_id, project_id, height_id in combos:
            print(f"  {setting_id:10} {source_id:12} {project_id:8} {height_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.solver_name} & {p.helper_name}: {p.source} -> {p.project} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
