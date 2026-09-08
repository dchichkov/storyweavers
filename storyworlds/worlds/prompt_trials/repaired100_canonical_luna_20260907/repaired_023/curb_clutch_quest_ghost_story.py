#!/usr/bin/env python3
"""
A small ghost-story world about a curb, a clutch, and a quest.
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
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


METERS = {"light": 0.0, "distance": 0.0, "fear": 0.0, "safety": 0.0}
MEMES = {"worry": 0.0, "hope": 0.0, "trust": 0.0, "grief": 0.0}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class GhostWorld:
    place: str
    hero: str
    companion: str
    object_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: dict(METERS))
    memes: dict[str, float] = field(default_factory=lambda: dict(MEMES))


@dataclass
class StoryParams:
    hero_name: str
    companion_name: str
    place: str
    seed: Optional[int] = None


HERO_NAMES = ["Luna", "Mara", "Nell", "Ivy", "Tess", "Milo"]
COMPANION_NAMES = ["Ben", "Owen", "Ruth", "Aunt May", "Theo"]
PLACES = ["the old town", "the rain-dark village", "the hill road", "the quiet market square"]

QUESTS = [
    {
        "id": "silver_key",
        "object": "silver key",
        "omen": "a cold handprint appeared on the curb beside the closed bakery",
        "ghost": "a pale baker named Elian",
        "need": "the key had been lost before he could open the bakery for hungry children",
        "task": "find the silver key and return it to the bakery door",
        "clutch": "clutched the rusted gate chain",
        "turn": "the ghost pointed beneath the curb, where rain had washed the key into a crack",
        "ending": "The bakery window glowed softly, though no living baker stood inside.",
    },
    {
        "id": "blue_ribbon",
        "object": "blue ribbon",
        "omen": "a ribbon fluttered from an empty bicycle at the curb",
        "ghost": "a young rider named Sora",
        "need": "the ribbon was the last gift from her brother, and she could not leave while it lay in the road",
        "task": "lift the ribbon from the gutter and carry it to the old fountain",
        "clutch": "clutched the bicycle bell",
        "turn": "a gust pushed the ribbon toward a storm drain, but the ghost showed Luna a loose twig she could use as a hook",
        "ending": "The bicycle bell rang once, and the blue ribbon rested safely on the fountain stone.",
    },
    {
        "id": "brass_button",
        "object": "brass button",
        "omen": "three tiny footsteps crossed the wet curb and stopped at a dark doorway",
        "ghost": "a vanished drummer named Pip",
        "need": "the button belonged to his coat, which marked the place where his family had waited for him",
        "task": "search the curb and bring the button to the old doorway",
        "clutch": "clutched a little lantern",
        "turn": "the lantern dimmed until Luna remembered to turn its wick low and listen for the button's faint chime",
        "ending": "A small drumbeat sounded from the doorway, then the dark became peaceful.",
    },
    {
        "id": "glass_marble",
        "object": "green glass marble",
        "omen": "a green spark rolled along the curb though no one had touched it",
        "ghost": "a child named Bea",
        "need": "the marble was the final thing she wanted to show her mother before crossing into the light",
        "task": "follow the marble along the curb and place it on the chapel step",
        "clutch": "clutched the edge of her coat",
        "turn": "the marble slipped under a bench, so Luna asked the ghost to breathe on the dust and reveal its shining path",
        "ending": "The marble shone on the chapel step, and a warm breeze carried Bea away.",
    },
    {
        "id": "lost_thimble",
        "object": "a silver thimble",
        "omen": "a sewing thread wound itself around the curb like a pale line",
        "ghost": "a seamstress named Mira",
        "need": "the thimble held the memory of the coat she had promised to mend for her little brother",
        "task": "trace the thread beside the curb and return the thimble to the blue cottage",
        "clutch": "clutched a wooden spool",
        "turn": "the thread tangled in a hedge, but Luna used the spool to roll it gently free",
        "ending": "The cottage window filled with golden stitches of light.",
    },
]

INTRO_FORMS = [
    "Luna lived in {place}, where the streetlamps blinked whenever a ghost was near.",
    "In {place}, people hurried past the old curb before moonrise. Luna did not hurry.",
    "The rain had washed {place} clean, but one curb still held a secret, and Luna was the one who noticed it.",
    "Every child in {place} knew the old curb was haunted. Luna knew that frightened places sometimes needed help.",
]

DIALOGUE_FORMS = [
    ('"Are you looking for something?" Luna asked.', '"I am," whispered {ghost}. "Please {task}."'),
    ('"Why are you standing by the curb?" Luna said.', '"Because {need}," answered {ghost}.'),
    ('Luna raised her lantern. "Can you show me the way?"', '"Only if you promise not to leave me," said {ghost}.'),
    ('"I am afraid," Luna admitted.', '"So am I," said {ghost}, "but a brave quest begins with one small step."'),
]

ACTION_LEADS = [
    "Luna began the quest beneath the thin moon.",
    "The ghost floated beside her as the quest started.",
    "They moved slowly, listening between the raindrops.",
    "Luna took one careful step from the curb.",
]

SUPPORT_LINES = [
    "She kept her lantern low so its light would not frighten the ghost.",
    "She counted the paving stones to remember the way home.",
    "She asked the ghost to point instead of pulling her through the dark.",
    "She placed one hand on the cool wall and kept the other free.",
]


ASP_RULES = r"""
needs_quest(P) :- person(P), haunted_curb(P), lost_object(P).
can_begin(P) :- needs_quest(P), has_clue(P), has_helper(P).
valid_story(P) :- can_begin(P), ghost_needs_help(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A ghost story about a curb, a clutch, and a quest.")
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--companion", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([x for x in COMPANION_NAMES if x != hero])
    return StoryParams(
        hero_name=hero,
        companion_name=companion,
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The quest needs a known young hero.")
    if params.companion_name not in COMPANION_NAMES:
        raise StoryError("The quest needs a named companion.")
    if params.place not in PLACES:
        raise StoryError("The haunted curb must be in a known place.")
    if params.hero_name == params.companion_name:
        raise StoryError("The hero and companion must be different people.")


def make_world(params: StoryParams) -> GhostWorld:
    world = GhostWorld(
        place=params.place,
        hero=params.hero_name,
        companion=params.companion_name,
        object_name="lost keepsake",
    )
    world.entities["hero"] = Entity("hero", "person", params.hero_name)
    world.entities["companion"] = Entity("companion", "person", params.companion_name)
    world.entities["curb"] = Entity("curb", "place", "the old curb")
    world.entities["ghost"] = Entity("ghost", "spirit", "a waiting ghost")
    world.meters["fear"] = 1.0
    world.memes["worry"] = 1.0
    return world


def choose_quest(world: GhostWorld, rng: random.Random) -> dict[str, str]:
    quest = rng.choice(QUESTS)
    world.object_name = quest["object"]
    world.facts.update(quest)
    return quest


def tell_story(params: StoryParams) -> GhostWorld:
    reasonableness_gate(params)
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else params.hero_name + params.place)
    quest = choose_quest(world, rng)
    intro = rng.choice(INTRO_FORMS).format(place=params.place)
    omen = f"That night, {quest['omen']}. It was a sign that the ghost's unfinished quest had begun again."
    first, second = rng.choice(DIALOGUE_FORMS)
    dialogue = " ".join(
        [
            first.format(ghost=quest["ghost"], task=quest["task"], need=quest["need"]),
            second.format(ghost=quest["ghost"], task=quest["task"], need=quest["need"]),
        ]
    )
    lead = rng.choice(ACTION_LEADS)
    support = rng.choice(SUPPORT_LINES)
    action = (
        f"{lead} {support} {params.hero_name} {quest['clutch']} and followed the ghost. "
        f"At the narrowest part of the street, {quest['turn']}."
    )
    world.meters["distance"] = 1.0
    world.meters["fear"] = 0.0
    world.meters["safety"] = 1.0
    world.memes["worry"] = 0.0
    world.memes["hope"] = 1.0
    world.memes["trust"] = 1.0
    ending = (
        f"{params.hero_name} placed the {quest['object']} where the ghost had asked. "
        f"{quest['ending']} {params.companion_name} found {params.hero_name} at dawn, "
        f"and together they saw that the curb was only an ordinary curb again."
    )
    world.facts["resolved"] = True
    world.facts["story"] = "\n\n".join([intro, omen, dialogue, action, ending])
    return world


def prompts(world: GhostWorld) -> list[str]:
    return [
        'Write a gentle ghost story using the words "curb" and "clutch".',
        f"Tell a quest about {world.hero} helping a ghost near {world.place}.",
        f"End with the {world.facts['object']} proving that the ghost's quest is complete.",
    ]


def story_qa(world: GhostWorld) -> list[QAItem]:
    quest = world.facts
    return [
        QAItem(
            question=f"Why did {world.hero} begin a quest at the curb in {world.place}?",
            answer=f"{world.hero} saw the sign that {quest['omen']} and learned that {quest['ghost']} needed help because {quest['need']}.",
        ),
        QAItem(
            question=f"What did {world.hero} promise to do for {quest['ghost']}?",
            answer=f"{world.hero} promised to {quest['task']}, so the ghost could finish the unfinished quest.",
        ),
        QAItem(
            question=f"How did {world.hero} handle the trouble during the quest?",
            answer=f"{world.hero} {quest['clutch']} and stayed calm when {quest['turn']}.",
        ),
        QAItem(
            question=f"What showed that the ghost's quest was complete?",
            answer=f"{quest['ending']} The curb became ordinary again, showing that the ghost had finally found peace.",
        ),
    ]


def world_qa(world: GhostWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curb?",
            answer="A curb is the raised edge between a street and a sidewalk.",
        ),
        QAItem(
            question="What does clutch mean?",
            answer="To clutch something means to hold it tightly, often because it feels important or frightening.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or task undertaken to find something, solve a problem, or help someone.",
        ),
    ]


def dump_trace(world: GhostWorld) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"place={world.place}",
            f"hero={world.hero}",
            f"object={world.object_name}",
            f"resolved={world.facts.get('resolved', False)}",
            f"meters={world.meters}",
            f"memes={world.memes}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.facts["story"],
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("person", "hero"),
            asp.fact("haunted_curb", "hero"),
            asp.fact("lost_object", "hero"),
            asp.fact("has_clue", "hero"),
            asp.fact("has_helper", "hero"),
            asp.fact("ghost_needs_help", "hero"),
        ]
    )


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp
    return bool(asp.atoms(asp.one_model(asp_program()), "valid_story"))


def asp_verify() -> int:
    try:
        import asp
        valid = asp_valid()
    except ImportError:
        print("ASP verification requires clingo.")
        return 1
    if not valid:
        print("MISMATCH: ASP rejected the reasonable quest.")
        return 1
    sample = generate(
        StoryParams(
            hero_name="Luna",
            companion_name="Ben",
            place="the old town",
            seed=17,
        )
    )
    if "curb" not in sample.story or "clutch" not in sample.story or "quest" not in sample.story.lower():
        print("MISMATCH: generated story lacks required story evidence.")
        return 1
    print("OK: ASP and Python gates agree; generated story exercised.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Ben", "the old town", 101),
            StoryParams("Mara", "Ruth", "the hill road", 202),
            StoryParams("Ivy", "Theo", "the quiet market square", 303),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params_list.append(resolve_params(args, rng))

    samples = [generate(params) for params in params_list]
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
