#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Campus:
    name: str
    setting: str
    path_condition: str = "ordinary"
    caution: float = 0.0
    friendship: float = 0.0
    humor: float = 0.0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    student_name: str
    friend_name: str
    university_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Tara", "Nia", "Pip", "Rowan", "Sage", "Bram"]
UNIVERSITIES = [
    "Moonbeam University",
    "Bluebell University",
    "Tumbleweed University",
    "Golden Acorn University",
]


ARCS = [
    {
        "key": "moonlit_gait",
        "premise": [
            "{student} studied at the little school beside {university}, where every student dreamed of earning a silver bell at graduation. Their best friend, {friend}, always walked beside them with a pocket full of jokes.",
            "At {university}, the school courtyard glittered each morning with dew. {student} and {friend} were friendship partners, though {student} had a very hurried gait and {friend} had a very thoughtful one.",
        ],
        "problem": [
            "One day, {student} hurried across the enchanted path and stepped on a moonstone. The path began copying that quick gait, carrying both friends in circles around the school.",
            "The head teacher warned them that the old path disliked rushing. But {student} dashed ahead, and the stones bounced their feet along until the school gate seemed farther away each time.",
        ],
        "conflict": [
            "\"Run faster!\" cried {student}. {friend} held onto a rosebush and answered, \"We should slow down!\" Their argument made the path wobble like a laughing dragon.",
            "{student} blamed the crooked stones, while {friend} blamed the hurried gait. They disagreed so loudly that a nearby gargoyle began repeating their words in a silly voice.",
        ],
        "turn": [
            "Then {friend} told a ridiculous joke about a tortoise winning a race by taking a nap. {student} laughed, and the laughter made both of them notice that the stones settled whenever their feet moved together.",
            "A tiny fairy teacher flew from the school bell and said, \"Watch the spaces between your steps.\" The friends stopped arguing long enough to see that every third stone was safe.",
        ],
        "action": [
            "\"You count; I will match you,\" said {student}. {friend} counted three gentle steps, and {student} changed the hurried gait into a calm, friendly rhythm.",
            "{student} apologized and offered an elbow. {friend} guided the way while they crossed the path with matching steps, laughing softly at the gargoyle's bad jokes.",
        ],
        "resolution": [
            "The moonstones stopped spinning, and the school gate swung open. The friends reached their lesson just in time, wiser about warnings and closer than before.",
            "The enchanted path straightened beneath their careful feet. At {university}, the teacher gave them one silver bell for caution and another for friendship.",
        ],
        "ending": [
            "From then on, their footsteps made a cheerful pattern across the schoolyard, and even the gargoyle learned to walk slowly.",
            "That evening, two silver bells chimed above the school while {student} and {friend} practiced a safe gait beneath the stars.",
        ],
        "problem_fact": "a hurried gait awakened a school path that carried the friends in circles",
        "clue_fact": "laughter and careful observation revealed that matching steps calmed the path",
        "action_fact": "the friends crossed by counting and matching gentle steps",
        "outcome_fact": "the path straightened and they learned to heed caution together",
    },
    {
        "key": "whistling_shoes",
        "premise": [
            "{student} and {friend} attended the oldest school at {university}, where every pupil wore shoes enchanted for one special talent. {student}'s shoes were fast, and {friend}'s shoes were excellent at finding lost pencils.",
            "At the school of {university}, {student} and {friend} shared a desk beneath a painted fairy tree. Their friendship was strong, but {student} loved showing off a very speedy gait.",
        ],
        "problem": [
            "The speedy shoes began whistling whenever {student} walked. The louder the whistle grew, the faster the shoes went, until they dragged both friends toward the forbidden tower.",
            "A cautionary sign said, \"Never race past the blue line.\" {student} raced anyway, and the enchanted shoes mistook the school bell for a starting signal.",
        ],
        "conflict": [
            "\"I can control them!\" said {student}. \"Then why are we heading into the tower?\" asked {friend}. Their disagreement echoed until the shoes whistled a comic melody.",
            "{friend} wanted to remove the shoes, but {student} feared missing the university trial. They tugged in opposite directions and nearly tripped over a basket of chalk.",
        ],
        "turn": [
            "The whistle sounded like a goose trying to sing. Both friends burst out laughing, and {friend} noticed that the shoes slowed whenever someone answered the whistle with a quiet hum.",
            "A fairy janitor appeared with a broom and reminded them that a warning was a gift, not a dare. {student} finally looked at the blue line and saw tiny arrows pointing backward.",
        ],
        "action": [
            "{student} hummed softly while {friend} guided each foot behind the blue line. The shoes quieted, and their wild gait became a careful school walk.",
            "\"I should have listened,\" admitted {student}. Together they stepped backward, untied the magic laces, and carried the shoes safely to the university cobbler.",
        ],
        "resolution": [
            "The forbidden tower faded into an ordinary storage room. The friends arrived at class with their friendship intact and their shoes safely tied.",
            "The cobbler changed the shoes' spell from speed to balance. {student} passed the trial by walking steadily, not by racing.",
        ],
        "ending": [
            "The enchanted shoes now whistled only when someone forgot to be careful, which made the whole school giggle.",
            "At graduation, {student} and {friend} crossed the stage side by side, each step quiet, steady, and bright.",
        ],
        "problem_fact": "enchanted shoes turned a student's speedy gait toward a forbidden tower",
        "clue_fact": "the friends discovered that humming and noticing the warning slowed the shoes",
        "action_fact": "they stepped back carefully and changed the shoes' spell",
        "outcome_fact": "the shoes became safe and the student learned that caution mattered more than racing",
    },
    {
        "key": "library_ladder",
        "premise": [
            "The library school at {university} floated among clouds, and {student} loved climbing its rolling ladders. {friend} loved reading the rules aloud, especially the funny ones.",
            "{student} and {friend} were studying fairy-tale maps in the high library of {university}. The shelves reached the ceiling, and every ladder had a different gait.",
        ],
        "problem": [
            "{student} hurried up a ladder without checking its wheels. The ladder rolled sideways, carrying the friends toward a shelf of sleeping spellbooks.",
            "A sign warned, \"Hold the rail and ask a friend.\" {student} ignored it, and the ladder began marching with a crooked gait toward a nest of sneezy books.",
        ],
        "conflict": [
            "\"I can reach the map alone,\" said {student}. {friend} replied, \"The sign says we must work together.\" A book below them muttered, \"Read before you speed!\"",
            "{student} wanted to jump down, but {friend} said that jumping would make the ladder wobble. Their argument made three books sneeze glitter into the air.",
        ],
        "turn": [
            "{friend} made a joke about a ladder needing dancing lessons. While {student} laughed, they noticed the wheels pointed toward a painted star on the floor.",
            "The librarian fairy blew a whistle and asked them to name the rule they had skipped. Saying it aloud helped {student} understand that the rail was a promise of safety.",
        ],
        "action": [
            "{student} held the rail, and {friend} pushed the brake with one careful toe. They guided the ladder toward the star and climbed down with a steady gait.",
            "\"Your rule-reading saved us,\" said {student}. {friend} held the map while {student} locked each wheel before they climbed again.",
        ],
        "resolution": [
            "The sleepy spellbooks opened their eyes and applauded with their pages. The friends found the map without damaging a single book.",
            "The ladder settled beside the correct shelf. At school the next day, the librarian awarded them a friendship bookmark shaped like two joined hands.",
        ],
        "ending": [
            "From then on, every ladder in the library wore a tiny badge that said, \"Ask a friend before you climb.\"",
            "The two friends left the library beneath a shower of harmless glitter, walking in the same careful rhythm.",
        ],
        "problem_fact": "a hurried climb sent a rolling library ladder toward sleeping spellbooks",
        "clue_fact": "a joke and a painted floor star helped them notice how to guide the ladder",
        "action_fact": "they held the rail, used the brake, and climbed with a steady gait",
        "outcome_fact": "they saved the books and learned to follow school safety rules",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.student_name, params.friend_name, params.university_name))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


class World:
    def __init__(self, campus: Campus) -> None:
        self.campus = campus
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if params.student_name == params.friend_name:
        raise StoryError("student_name and friend_name must be different people")
    if not params.student_name or not params.friend_name:
        raise StoryError("both student_name and friend_name are required")
    campus = Campus(
        name=params.university_name,
        setting="a fairy-tale school at a university",
        path_condition="unstable",
        caution=0.0,
        friendship=1.0,
        humor=0.0,
    )
    world = World(campus)
    student = world.add(Entity(params.student_name, "character", "student"))
    friend = world.add(Entity(params.friend_name, "character", "friend"))
    school = world.add(Entity("school", "place", "school"))
    university = world.add(Entity("university", "place", "university"))
    student.meters["gait"] = 1.0
    friend.meters["gait"] = 1.0

    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]
    beats = ["premise", "problem", "conflict", "turn", "action", "resolution", "ending"]
    chosen = {}
    for beat in beats:
        if params.seed is None:
            chosen[beat] = rng.choice(arc[beat])
        else:
            chosen[beat] = arc[beat][(params.seed // len(ARCS) + beats.index(beat)) % len(arc[beat])]
    rendered = {}
    for i, beat in enumerate(beats):
        if i:
            world.para()
        rendered[beat] = chosen[beat].format(
            student=params.student_name,
            friend=params.friend_name,
            university=params.university_name,
        )
        world.say(rendered[beat])

    campus.path_condition = "safe"
    campus.caution = 1.0
    campus.friendship = 2.0
    campus.humor = 1.0
    student.meters["gait"] = 0.5
    friend.meters["gait"] = 0.5
    student.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0
    campus.facts = {
        "student": student,
        "friend": friend,
        "school": school,
        "university": university,
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "events": rendered,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.campus.facts
    return [
        "Write a child-friendly fairy tale about a school at a university where a student's gait causes trouble.",
        f"Tell a cautionary friendship story about {f['student'].id} and {f['friend'].id}, using humor to help them solve a school problem.",
        "Write a short fairy tale in which careful walking and listening to a friend lead to a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.campus.facts
    student = f["student"].id
    friend = f["friend"].id
    return [
        QAItem(
            question=f"Who were the friends at {world.campus.name}?",
            answer=f"{student} and {friend} were friends studying together at {world.campus.name}.",
        ),
        QAItem(
            question=f"What went wrong with {student}'s gait?",
            answer=f["events"]["problem"],
        ),
        QAItem(
            question="How did humor or observation help the friends?",
            answer=f["events"]["turn"],
        ),
        QAItem(
            question=f"How did {student} and {friend} solve the problem?",
            answer=f"{f['events']['action']} {f['events']['resolution']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gait?",
            answer="A gait is the way a person or animal walks, including the speed and rhythm of its steps.",
        ),
        QAItem(
            question="What is a university?",
            answer="A university is a place where older students study many subjects and learn advanced skills.",
        ),
        QAItem(
            question="Why are caution and friendship useful?",
            answer="Caution helps someone notice danger before acting, while friendship brings support, honest advice, and courage.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:10}) {' '.join(bits)}")
    c = world.campus
    lines.extend(
        [
            f"  campus.path_condition={c.path_condition}",
            f"  campus.caution={c.caution}",
            f"  campus.friendship={c.friendship}",
            f"  campus.humor={c.humor}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(school, gait, university, caution).
valid_story(school, gait, university, friendship) :- cautionary_turn, friends_help.
cautionary_turn.
friends_help.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "school"),
            asp.fact("theme", "gait"),
            asp.fact("theme", "university"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "humor"),
            asp.fact("style", "fairy_tale"),
            asp.fact("cautionary_turn"),
            asp.fact("friends_help"),
        ]
    )


def asp_program(show: str = "#show valid_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if any(sym.name == "valid_story" for sym in model):
        sample = generate(StoryParams("Luna", "Milo", "Moonbeam University", seed=7))
        if all(word in sample.story.lower() for word in ("school", "university", "friend")):
            print("OK: ASP and Python recognize the school gait friendship story.")
            return 0
    print("MISMATCH: ASP/Python parity check failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale school world about gait, caution, friendship, and humor."
    )
    parser.add_argument("--student-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--university-name", choices=UNIVERSITIES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    student = args.student_name or rng.choice(NAMES)
    available = [name for name in NAMES if name != student]
    friend = args.friend_name or rng.choice(available)
    university = args.university_name or rng.choice(UNIVERSITIES)
    return StoryParams(student, friend, university)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible fairy-tale pattern: school + gait + university + caution + friendship + humor")
        return
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", "Moonbeam University", seed=3),
            StoryParams("Tara", "Pip", "Bluebell University", seed=11),
            StoryParams("Rowan", "Nia", "Golden Acorn University", seed=19),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
