#!/usr/bin/env python3
"""
A small heartwarming storyworld about a parade, a sailor, and an infantry band.

Seed premise:
During a town parade, a sailor expects to lead a proud march while an infantry
drummer seems to be missing. A gentle twist reveals that the drummer stopped to
help someone along the route, and the parade becomes warmer because of it.
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
class StoryParams:
    child: str
    sailor: str
    drummer: str
    helper: str
    parade_place: str
    keepsake: str
    incident: int = 0
    opening: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CHILDREN = ["Maya", "Leo", "Nina", "Owen", "Tessa", "Sam", "Ivy", "Noah"]
SAILORS = ["Sailor June", "Sailor Mateo", "Sailor Pearl", "Sailor Rowan"]
DRUMMERS = ["Corporal Bea", "Private Ellis", "Corporal Kai", "Private Rosa"]
HELPERS = ["Grandma Jo", "Mr. Bell", "Aunt Nia", "Coach Finn"]
PLACES = ["Maple Street", "Harbor Square", "Rosewood Avenue", "the town green"]
KEEPSAKES = ["a brass button", "a blue ribbon", "a shell whistle", "a tiny paper flag"]

INCIDENTS = [
    {
        "lead": "{sailor} lifted a bright signal flag while the infantry band practiced its first brave beat.",
        "trigger": "Just before the parade began, one small drumbeat came from the wrong end of the street, and the band could not see its drummer.",
        "risk": "The march was ready, but without that steady beat the groups might lose their places.",
        "action": "{child} followed the distant rhythm and found {drummer} beside a fallen stroller near the fountain.",
        "resolution": "{child} helped clear the wheel while {sailor} held the parade line open. Then {drummer} hurried back with the drum tucked safely against a coat.",
        "cause": "the infantry drummer had stopped to help a stroller stuck near the fountain",
        "deed": "followed the distant drumbeat and helped clear the stroller",
        "result": "the stroller rolled free and the drummer returned safely to the parade",
    },
    {
        "lead": "{sailor} polished a row of bright buttons while the infantry band lined up beneath the town flags.",
        "trigger": "A gust lifted the parade map from the mayor's hand and sent it skimming under a row of chairs.",
        "risk": "Without the map, the marching groups might turn too soon and miss the children waiting at the finish.",
        "action": "{child} noticed a corner of paper beneath a chair. At the same moment, {drummer} paused the band to guide a nervous puppy away from the wheels.",
        "resolution": "{sailor} retrieved the map, and the infantry band resumed after the puppy was reunited with its owner.",
        "cause": "a gust blew the parade map under the chairs while a puppy wandered near the route",
        "deed": "spotted the map and helped keep the route clear",
        "result": "the map was recovered and the puppy reached its owner",
    },
    {
        "lead": "The parade banner shone above {sailor}, and {drummer} tapped a gentle rhythm for the infantry line.",
        "trigger": "A little child at the curb dropped a red mitten between two parade wheels.",
        "risk": "The mitten was close to the moving route, and the child began to cry.",
        "action": "{child} told {sailor}, 'Please stop the line for a moment.' {sailor} raised the flag, and {drummer} held the beat while an adult safely retrieved the mitten.",
        "resolution": "When the mitten was returned, its owner waved it like a tiny flag, and the parade moved on.",
        "cause": "a child's mitten fell close to the moving parade route",
        "deed": "asked the sailor to pause the parade so the mitten could be retrieved safely",
        "result": "the mitten returned to its owner and the parade continued",
    },
    {
        "lead": "{sailor} showed {child} how a parade flag could flutter without tangling while the infantry band warmed up nearby.",
        "trigger": "The wind twisted the welcome banner around a lamp post, hiding the words meant for the waiting crowd.",
        "risk": "The parade's kind message was wrapped up tight just when everyone was ready to read it.",
        "action": "{child} called for a pause. {drummer} set down the sticks, and together with {sailor} they loosened the banner from the safe side of the post.",
        "resolution": "The banner opened wide again, revealing the words, 'Everyone Has a Place in the Parade.'",
        "cause": "the wind wrapped the welcome banner around a lamp post",
        "deed": "called for a pause and helped loosen the banner safely",
        "result": "the banner opened and shared its welcoming message",
    },
    {
        "lead": "At the front of the parade, {sailor} saluted the crowd while {drummer} gave the infantry a soft practice roll.",
        "trigger": "A bright balloon slipped from a child's hand and bobbed toward the tall trees beside the route.",
        "risk": "The child reached after it, but the balloon was already drifting beyond the safe curb.",
        "action": "{child} waved to {sailor}. The sailor stopped the group, and {drummer} used the drum's deep voice to guide everyone back from the road while an adult caught the string.",
        "resolution": "The balloon returned to its owner, who tied it to a stroller and joined the cheering crowd.",
        "cause": "a balloon drifted toward the trees while its owner moved near the road",
        "deed": "signaled the sailor to stop and helped keep the child safely back",
        "result": "an adult caught the balloon and the child stayed safe",
    },
]

OPENINGS = [
    "{child} arrived early at {parade_place}, where bunting danced above the street and neighbors carried cups of lemonade.",
    "The morning of the town parade smelled like warm bread and fresh grass. {child} stood near {parade_place}, waiting for the first drumbeat.",
    "{child} had practiced waving all week. At {parade_place}, the sailor uniforms gleamed and the infantry band gathered beneath red and gold flags.",
    "Clouds covered the sun, but {parade_place} still looked cheerful. {child} came with {helper} to watch the parade begin.",
    "The town had one rule for parade day: make room for every neighbor. {child} remembered that rule while watching {sailor} prepare the lead group.",
]

TWISTS = [
    "The surprising part was that the missing beat had never meant trouble. {drummer} had chosen kindness before marching.",
    "Everyone had expected the sailor to save the day alone, but the twist was gentler: a child noticed the need, and many people made space to help.",
    "The crowd thought the parade had been delayed. Then they learned the pause was part of the parade's best lesson.",
    "The infantry band's quiet moment became a signal of care. The crowd answered with claps instead of impatient whistles.",
    "What looked like a lost place in the line turned out to be a new place for someone who needed help.",
]

ENDINGS = [
    "At the finish, {child} pinned the {keepsake} to a community board beside a note that said, 'Kindness keeps the beat.'",
    "The parade ended at sunset. {sailor} gave {child} a salute, and the infantry drummer tapped three soft notes for every helper along the route.",
    "Before going home, {helper} helped {child} draw the parade as a long ribbon of people, with nobody left outside its edges.",
    "The final flag waved over a crowd that now marched in place, smiling and clapping. Even the smallest hands seemed to know the rhythm.",
    "As the streets grew quiet, {child} heard one last drumbeat from the square. It sounded less like a command and more like a thank-you.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

child_name(N) :- child(N).
sailor_name(S) :- sailor(S).
drummer_name(D) :- drummer(D).
place_name(P) :- place(P).
keepsake_name(K) :- keepsake(K).

twist(I) :- incident(I), helps_someone(I).
valid(C, I, P) :- child_name(C), incident(I), place_name(P), twist(I).
valid_story(C, I, P, K) :- valid(C, I, P), keepsake_name(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for value in CHILDREN:
        lines.append(asp.fact("child", value))
    for value in SAILORS:
        lines.append(asp.fact("sailor", value))
    for value in DRUMMERS:
        lines.append(asp.fact("drummer", value))
    for value in PLACES:
        lines.append(asp.fact("place", value))
    for value in KEEPSAKES:
        lines.append(asp.fact("keepsake", value))
    for index, incident in enumerate(INCIDENTS):
        lines.append(asp.fact("incident", index))
        lines.append(asp.fact("helps_someone", index))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[int]]:
    return [(index,) for index in range(len(INCIDENTS))]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted({(incident,) for _, incident, _ in asp.atoms(model, "valid")})


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values == asp_values:
        print(f"OK: clingo gate matches valid_combos() ({len(python_values)} incidents).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_values - asp_values:
        print("  only in python:", sorted(python_values - asp_values))
    if asp_values - python_values:
        print("  only in clingo:", sorted(asp_values - python_values))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade storyworld with a sailor, infantry band, and gentle twist."
    )
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--sailor", choices=SAILORS)
    parser.add_argument("--drummer", choices=DRUMMERS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--parade-place", choices=PLACES)
    parser.add_argument("--keepsake", choices=KEEPSAKES)
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
    return StoryParams(
        child=args.child or rng.choice(CHILDREN),
        sailor=args.sailor or rng.choice(SAILORS),
        drummer=args.drummer or rng.choice(DRUMMERS),
        helper=args.helper or rng.choice(HELPERS),
        parade_place=args.parade_place or rng.choice(PLACES),
        keepsake=args.keepsake or rng.choice(KEEPSAKES),
        incident=rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.incident = seed % len(INCIDENTS)
    params.opening = (seed // len(INCIDENTS)) % len(OPENINGS)
    params.twist = (seed // 3) % len(TWISTS)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "child": params.child,
        "sailor": params.sailor,
        "drummer": params.drummer,
        "helper": params.helper,
        "parade_place": params.parade_place,
        "keepsake": params.keepsake,
    }
    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    world = World()
    child = world.add(Entity(params.child, "character", params.child, memes={"curiosity": 0.0}))
    sailor = world.add(Entity(params.sailor, "character", params.sailor, memes={"confidence": 0.0}))
    drummer = world.add(Entity(params.drummer, "character", params.drummer, memes={"belonging": 0.0}))
    helper = world.add(Entity(params.helper, "character", params.helper))
    route = world.add(Entity("parade_route", "place", params.parade_place, meters={"crowd": 0.5}))
    beat = world.add(Entity("drumbeat", "thing", "the infantry drumbeat", meters={"volume": 0.2}, memes={"tension": 0.0}))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(
        f"{params.sailor} stood at the front with a bright flag, while {params.drummer} "
        f"and the infantry band waited for the first parade signal."
    )
    world.say(f"{params.child} waved to {params.helper}. '{params.helper}, I think everyone is ready,' {params.child} said.")

    world.para()
    child.memes["curiosity"] = 1.0
    beat.meters["volume"] = 0.8
    beat.memes["tension"] = 1.0
    world.say(incident["lead"].format(**values))
    world.say(incident["trigger"].format(**values))
    world.say(incident["risk"].format(**values))
    world.say(f"'{incident['cause'].capitalize()},' {params.child} whispered. 'We should find out before the parade moves.'")
    world.say(f"'{params.child} is right,' {params.sailor} replied. 'A good parade makes room for careful helpers.'")
    world.say(incident["action"].format(**values))

    world.para()
    child.memes["courage"] = 1.0
    sailor.memes["trust"] = 1.0
    drummer.memes["relief"] = 1.0
    beat.meters["volume"] = 1.0
    beat.memes["tension"] = 0.0
    world.say(incident["resolution"].format(**values))
    world.say(TWISTS[params.twist % len(TWISTS)].format(**values))
    world.say(f"'{params.child}, may I march beside you for one minute?' {params.drummer} asked.")
    world.say(f"'Yes,' {params.child} said. 'But first, let's make sure everyone has a safe place.'")
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        child=params.child,
        sailor=params.sailor,
        infantry_drummer=params.drummer,
        helper=params.helper,
        place=params.parade_place,
        incident=params.incident % len(INCIDENTS),
        cause=incident["cause"],
        helpful_action=incident["deed"],
        result=incident["result"],
        twist=True,
        resolved=True,
    )

    prompts = [
        "Write a heartwarming parade story with a sailor, an infantry drummer, a small problem, and a kind twist.",
        f"Tell a child-friendly story about {params.child} helping {params.sailor} and {params.drummer} during a parade.",
        f"Write a warm parade tale set at {params.parade_place} where kindness changes what the crowd thinks is happening.",
    ]

    story_qa = [
        QAItem(
            question="Who were the important parade characters?",
            answer=f"{params.child} watched {params.sailor} lead the parade and helped {params.drummer}, an infantry band member, while {params.helper} was nearby.",
        ),
        QAItem(
            question="What caused the parade's tense moment?",
            answer=f"The tense moment began because {incident['cause']}. The marching groups needed to pause and understand what was happening.",
        ),
        QAItem(
            question=f"What did {params.child} do?",
            answer=f"{params.child} {incident['deed']}. That choice helped the parade stay safe and made room for someone who needed help.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that the missing or delayed parade action was caused by kindness: {incident['cause']}. The pause was not a failure; it helped someone.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{incident['result']}. The parade continued with a warmer feeling because everyone understood that helping others mattered more than rushing.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized line or group of people, vehicles, or performers moving together while others watch and celebrate.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a boat or ship and may help guide, care for, or protect the vessel and its passengers.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers trained to move and work on foot. In a parade, an infantry group may march together in formation.",
        ),
        QAItem(
            question="Why are drums useful in a parade?",
            answer="Drums give marchers a steady beat so they can move together and keep a shared rhythm.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change in what readers think is happening, often revealing a new reason or meaning.",
        ),
        QAItem(
            question="Why can a parade pause be helpful?",
            answer="A pause can give people time to solve a problem safely, help someone, or make sure everyone can take part.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:9}) {' '.join(details)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Maya", "Sailor June", "Corporal Bea", "Grandma Jo", "Maple Street", "a brass button", 0, 0, 0, 0),
        StoryParams("Leo", "Sailor Mateo", "Private Ellis", "Mr. Bell", "Harbor Square", "a blue ribbon", 1, 1, 1, 1),
        StoryParams("Nina", "Sailor Pearl", "Corporal Kai", "Aunt Nia", "Rosewood Avenue", "a shell whistle", 2, 2, 2, 2),
        StoryParams("Owen", "Sailor Rowan", "Private Rosa", "Coach Finn", "the town green", "a tiny paper flag", 3, 3, 3, 3),
        StoryParams("Tessa", "Sailor June", "Private Ellis", "Grandma Jo", "Harbor Square", "a blue ribbon", 4, 4, 4, 4),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        values = asp_valid_combos()
        print(f"{len(values)} valid parade incidents:\n")
        for value in values:
            print(f"  incident {value[0]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            header = f"### {sample.params.child}: parade at {sample.params.parade_place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
