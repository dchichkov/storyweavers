#!/usr/bin/env python3
"""
A small folk-tale storyworld about a child, a kidney-shaped apparatus, and a
construction-site quest that becomes a transformation through careful teamwork.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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


@dataclass(frozen=True)
class Trial:
    title: str
    beginning: str
    danger: str
    first_try: str
    clue: str
    quest_action: str
    transformation: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


@dataclass
class StoryParams:
    place: str
    object_name: str
    child_name: str
    gender: str
    helper: str
    trait: str
    trial: str
    mode: str
    seed: Optional[int] = None


SETTING = Setting(
    place="the construction site",
    affords={"building", "measuring", "repairing", "teamwork"},
)

TRIALS = [
    Trial(
        title="the crooked bridge",
        beginning="At the edge of the new building stood a little bridge of planks, waiting to carry tools across a muddy trench.",
        danger="The bridge sagged in the middle, and a silver bolt had slipped beneath a stack of pipes.",
        first_try="The child tried to pull the pipes away alone, but the stack groaned and rolled a handspan toward the trench.",
        clue="The foreman noticed two matching chalk marks on the beams: the bridge had been designed to use a lifting frame, not a lone pair of hands.",
        quest_action="The child fetched the wooden lifting frame, while the foreman steadied the pipes and the helper marked a safe path.",
        transformation="When the frame rose, the bent bridge became a strong little crossing, and the kidney-shaped apparatus fit beneath it like a patient golden guardian.",
        resolution="Together they found the bolt, secured the bridge, and carried the apparatus across without a wobble.",
        lesson="A brave quest begins by asking what the work needs, not by showing how strong one person can be.",
        ending="By sunset, the once-crooked bridge held a row of bright tools, and the apparatus rested safely on the far side.",
        question="How did the team repair the crooked bridge?",
        answer="They used the wooden lifting frame, steadied the pipes, found the missing bolt, and secured the bridge together.",
    ),
    Trial(
        title="the vanished blueprints",
        beginning="One morning, the construction crew found an empty table where the plans for the rain room had been kept.",
        danger="Without the blueprints, the kidney-shaped apparatus could be placed backward, leaving its narrow pipe facing the wall.",
        first_try="The child guessed at the shape and began pointing workers toward the nearest open space.",
        clue="A trail of blue pencil dust led from the table to a stack of roof boards, where a corner of paper showed a sun and three arrows.",
        quest_action="The child followed the marks with the helper, found the rolled plans beneath the boards, and asked the foreman to check every arrow.",
        transformation="The blank-looking worksite changed into a map of possibilities: the apparatus turned toward the water line, and the rain room took its proper shape.",
        resolution="The crew rebuilt their plan before lifting anything, then placed each piece where the drawings promised it would work.",
        lesson="A missing answer may leave clues behind, if a curious traveler looks before guessing.",
        ending="The recovered blueprints fluttered on the table while rainwater whispered through the finished room.",
        question="Where were the missing blueprints found?",
        answer="They were found rolled beneath the roof boards, along a trail of blue pencil dust.",
    ),
    Trial(
        title="the stubborn crane",
        beginning="A small crane stood beside the half-built hall, its hook hanging still above the kidney-shaped apparatus.",
        danger="The crane would not lift, and the apparatus was too heavy for anyone to move safely by hand.",
        first_try="The child tugged the control lever twice, but the crane only gave a rusty cough.",
        clue="The helper heard a click near the wheels and found that one safety pin had not been pushed all the way through.",
        quest_action="The child called the foreman, kept everyone beyond the painted line, and helped hold the flashlight while the pin was checked.",
        transformation="Once the pin was set correctly, the silent crane woke like a sleepy giant and changed the whole site from waiting to working.",
        resolution="The foreman operated the crane, and the child guided the apparatus with a rope from a safe distance.",
        lesson="When a powerful tool is quiet, patience and a careful check are stronger than a hard pull.",
        ending="The crane lifted the apparatus gently, and its new place shone beneath the hall's wide beams.",
        question="What made the crane work again?",
        answer="A safety pin near the wheels had not been pushed all the way through, and the foreman checked it before operating the crane.",
    ),
    Trial(
        title="the wall that whispered",
        beginning="The new wall made a hollow whisper whenever the evening wind passed through the construction site.",
        danger="The child feared that the wall would fall, and the kidney-shaped apparatus stood directly beside it.",
        first_try="The child reached for a loose brick, hoping to patch the sound before anyone noticed.",
        clue="The helper placed a hand on the wall and heard the whisper only near a small vent drawn on the building plan.",
        quest_action="They showed the foreman the plan, moved the apparatus away from the wall, and tested the vent with a ribbon.",
        transformation="The frightening whisper became a useful breath, and the wall changed from a mystery into a working part of the building.",
        resolution="The crew secured the vent cover and returned the apparatus after checking that the wall stood firm.",
        lesson="A strange sound can be a warning, a message, or simply a new part doing its job.",
        ending="The ribbon fluttered through the vent, and the wall sang softly while the apparatus gleamed nearby.",
        question="Why was the wall whispering?",
        answer="The sound came from a planned vent that let air move through the new wall.",
    ),
    Trial(
        title="the red mud road",
        beginning="A red-mud road led from the gate to the work shed, where the kidney-shaped apparatus waited beneath a canvas.",
        danger="A storm had carved deep puddles across the road, so a heavy cart could sink before reaching the shed.",
        first_try="The child pushed the cart toward the mud, but its front wheel vanished into a puddle.",
        clue="The helper found flat boards stacked beside the shed and noticed old wheel marks crossing the wet ground.",
        quest_action="They laid the boards as a temporary road, checked each one with the foreman, and pulled the cart slowly over the path.",
        transformation="The muddy road became a firm silver track, and the difficult journey turned into a line of careful steps.",
        resolution="The apparatus reached the shed dry and steady, while the boards were gathered for another rainy day.",
        lesson="A long quest grows shorter when travelers build the road they need.",
        ending="After the storm, the board road shone red at its edges, and the covered apparatus waited safely in the shed.",
        question="How did the crew move the apparatus through the mud?",
        answer="They laid flat boards over the puddles to make a temporary road, then pulled the cart slowly across it.",
    ),
    Trial(
        title="the bell in the toolbox",
        beginning="A tiny bell rang inside the toolbox whenever the wind crossed the construction site.",
        danger="The child thought the bell meant that a tool had been lost beneath the fresh floor.",
        first_try="The child opened every drawer and scattered measuring tapes, gloves, and chalk across the workbench.",
        clue="The helper noticed that the bell rang only when the toolbox lid leaned against a small metal gauge.",
        quest_action="They returned the tools, lifted the lid carefully, and asked the foreman which gauge belonged in the apparatus kit.",
        transformation="The noisy box became a clear warning: the gauge had been resting against the lid, showing that the apparatus still needed a pressure check.",
        resolution="The foreman tested the gauge, corrected the pressure, and closed the toolbox with its tools in order.",
        lesson="A puzzle becomes useful when we notice exactly when and how it speaks.",
        ending="The toolbox grew quiet, and one small gauge rested in its proper slot beside the shining apparatus.",
        question="What caused the bell to ring?",
        answer="The toolbox lid was leaning against a small metal gauge, so the wind made the gauge tap the lid.",
    ),
]

OPENINGS = [
    "In the old days, every new building had a riddle waiting in its walls.",
    "Once, when the morning sun touched the cranes, a small quest began.",
    "There was a construction site where even a loose bolt could tell a tale.",
    "Long ago, beneath a sky bright as a polished nail, a careful child came to work.",
    "At the place where beams rose like young trees, a curious problem appeared.",
]

NAMES = {
    "girl": ["Luna", "Mira", "Nora", "Tess", "Ivy"],
    "boy": ["Leo", "Finn", "Milo", "Owen", "Sam"],
}
TRAITS = ["curious", "patient", "bright", "brave", "thoughtful"]
HELPERS = ["the foreman", "the site engineer", "the crane operator"]


def can_story(place: str, object_name: str) -> bool:
    return place == "construction_site" and object_name == "kidney_apparatus"


ASP_RULES = r"""
place(construction_site).
object(kidney_apparatus).
feature(quest).
feature(transformation).
style(folk_tale).

compatible(P,O) :-
    place(P),
    object(O),
    P = construction_site,
    O = kidney_apparatus.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "construction_site"),
            asp.fact("object", "kidney_apparatus"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "transformation"),
            asp.fact("style", "folk_tale"),
        ]
    )


def asp_program(show: str = "#show compatible/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("construction_site", "kidney_apparatus")]


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "construction_site":
        raise StoryError("This storyworld is set only at a construction site.")
    if args.object_name and args.object_name != "kidney_apparatus":
        raise StoryError("This storyworld requires the kidney apparatus.")
    if args.gender and args.gender not in NAMES:
        raise StoryError("Gender must be girl or boy.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place="construction_site",
        object_name="kidney_apparatus",
        child_name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        trial=f"trial_{seed % len(TRIALS):02d}",
        mode=f"mode_{(seed // len(TRIALS)) % len(OPENINGS):02d}",
        seed=seed,
    )


def tell(params: StoryParams) -> World:
    trial = TRIALS[int(params.trial.rsplit("_", 1)[1])]
    opening = OPENINGS[int(params.mode.rsplit("_", 1)[1])]

    world = World(SETTING)
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=params.gender,
            label=params.child_name,
            memes={"curiosity": 1.0, "courage": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="adult",
            label=params.helper,
            memes={"care": 1.0},
        )
    )
    apparatus = world.add(
        Entity(
            id="apparatus",
            kind="device",
            type="kidney_apparatus",
            label="kidney apparatus",
            phrase="the kidney-shaped apparatus",
            meters={"stability": 0.0, "readiness": 0.0},
        )
    )
    world.facts.update(child=child, helper=helper, apparatus=apparatus, trial=trial)

    world.say(opening)
    world.say(
        f"{params.child_name}, a {params.trait} child, came to the construction site "
        f"where a kidney-shaped apparatus waited to be fitted into the new building."
    )
    world.say(
        f"{params.helper.capitalize()} watched the lifting gear and said, "
        f'"A good builder listens before lifting."'
    )
    world.para()

    world.say(trial.beginning)
    world.say(trial.danger)
    world.say(
        f'"I will solve it quickly," {params.child_name} said. '
        f'"Then the apparatus can be ready!"'
    )
    world.say(trial.first_try)
    child.meters["risk"] = 1.0
    child.memes["haste"] = 1.0
    world.say(
        f'"Stop at the painted line," {params.helper} replied. '
        f'"Tell me what you notice, and we will choose a safe path."'
    )
    world.para()

    world.say(trial.clue)
    child.memes["attention"] = 1.0
    child.memes["trust"] = 1.0
    world.say(
        f'"Now I know what the site is telling us," {params.child_name} said. '
        f'"I will help, but I will not guess."'
    )
    world.say(trial.quest_action)
    world.para()

    apparatus.meters["stability"] = 1.0
    apparatus.meters["readiness"] = 1.0
    child.meters["risk"] = 0.0
    world.say(trial.transformation)
    world.say(trial.resolution)
    world.say(
        f'"The quest changed us too," {params.helper} said. '
        f'"You began with hurry and finished with good judgment."'
    )
    world.say(trial.lesson)
    world.say(trial.ending)

    world.facts.update(
        clue=trial.clue,
        transformation=trial.transformation,
        resolution=trial.resolution,
        lesson=trial.lesson,
        ending=trial.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trial = world.facts["trial"]
    child = world.facts["child"]
    return [
        "Write a child-friendly Folk Tale set at a construction site, featuring a kidney apparatus, a Quest, and a Transformation.",
        f"Tell a folk tale in which {child.label} solves {trial.title} through careful teamwork.",
        f"Make this clue change the quest: {trial.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {child.label} find at the construction site?",
            answer=f"{child.label} found a kidney-shaped apparatus waiting to be fitted into the new building.",
        ),
        QAItem(question=trial.question, answer=trial.answer),
        QAItem(
            question=f"What Transformation happened during {child.label}'s Quest?",
            answer=trial.transformation,
        ),
        QAItem(
            question=f"What did {child.label} learn from the Quest?",
            answer=trial.lesson,
        ),
        QAItem(
            question="How did the ending show that the work was complete?",
            answer=trial.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kidney?",
            answer="A kidney is an organ in the body that helps clean the blood and make urine.",
        ),
        QAItem(
            question="What is an apparatus?",
            answer="An apparatus is a set of tools or parts made for a particular job.",
        ),
        QAItem(
            question="What is a Quest in a story?",
            answer="A Quest is a purposeful journey or challenge that a character works to complete.",
        ),
        QAItem(
            question="What is a Transformation in a story?",
            answer="A Transformation is a meaningful change in a character, object, or situation.",
        ),
        QAItem(
            question="Why should children stay behind safety lines at a construction site?",
            answer="Safety lines keep children away from heavy machines, falling materials, and other dangerous work areas.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.type:18}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting: {world.setting.place}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Folk Tale storyworld about a kidney apparatus at a construction site."
    )
    parser.add_argument("--place", choices=["construction_site"])
    parser.add_argument("--object-name", dest="object_name", choices=["kidney_apparatus"])
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("MISMATCH between Python and ASP compatibility gates.")
        print("Only in Python:", sorted(python_combos - asp_combos))
        print("Only in ASP:", sorted(asp_combos - python_combos))
        return 1

    for seed in range(8):
        params = resolve_params(
            argparse.Namespace(
                place=None,
                object_name=None,
                gender=None,
                name=None,
                helper=None,
                trait=None,
            ),
            random.Random(seed),
            seed,
        )
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated-story verification failed.")
            return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(TRIALS) if args.all else max(args.n, 1)
    samples: list[StorySample] = []

    for index in range(count):
        seed = base_seed if args.all else base_seed + index
        rng = random.Random(seed)
        params = resolve_params(args, rng, seed)
        samples.append(generate(params))

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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
