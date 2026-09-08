#!/usr/bin/env python3
"""
A small detective storyworld about a hangar register, an o'clock clue, and sharing.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    detective: str = "Luna"
    helper: str = "Pip"
    hangar: str = "the moon hangar"
    object_name: str = "the brass compass"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    detective: Entity
    helper: Entity
    hangar: Entity
    register: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


DETECTIVES = ["Luna", "Mara", "Theo", "Nell", "Ivo", "Sami"]
HELPERS = ["Pip", "Bea", "Ollie", "Rae", "Tess", "Bo"]
HANGARS = ["the moon hangar", "the red hangar", "the cloud hangar"]
OBJECTS = ["the brass compass", "the silver key", "the blue lens", "the tiny clock"]


ARCS = [
    {
        "premise": "The morning keeper found one empty place on the hangar register",
        "missing": "the brass compass",
        "risk": "Without it, the small airship could lose its way above the clouds",
        "clue": "the ink beside the empty line was still wet",
        "method": "they compared the register with the chalk marks on every tool cart",
        "twist": "the compass had not been stolen; a young mechanic had borrowed it to guide a lost moth outside",
        "sharing": "they returned the compass and taught the mechanic how to record every loan in the register",
        "lesson": "a careful record becomes more useful when everyone is trusted to share the truth",
        "ending": "the compass rested in its drawer while three new names filled the register with neat, honest ink",
        "question": "Why did the hangar need the compass?",
        "answer": "The hangar needed the compass to help the small airship keep its way above the clouds.",
    },
    {
        "premise": "At seven o'clock, the night watch noticed a smudge beside one line in the hangar register",
        "missing": "the silver key",
        "risk": "The locked fuel cabinet could not be opened for the evening flight",
        "clue": "a trail of flour crossed the floor from the lunch table to the cabinet",
        "method": "they shared flashlights and followed the flour trail beneath the workbenches",
        "twist": "the key had been carried by a sleepy baker's cat that wanted to reach a warm shelf",
        "sharing": "they freed the key, gave the cat a soft basket, and added the borrowed-key rule to the register",
        "lesson": "a mystery grows smaller when each person adds one small observation",
        "ending": "at eight o'clock, the cabinet opened, and the cat slept beside the newly shared basket",
        "question": "What clue led the detectives to the fuel cabinet?",
        "answer": "A trail of flour led from the lunch table to the fuel cabinet.",
    },
    {
        "premise": "The hangar register said the blue lens had been checked in at four o'clock",
        "missing": "the blue lens",
        "risk": "The signal lamp could not flash its safe landing color",
        "clue": "the register's four had a long tail unlike the other numbers",
        "method": "they asked each worker to show how they wrote the time and compared the marks",
        "twist": "the line had been read upside down; the lens was safely stored on the upper shelf",
        "sharing": "they turned the register together and drew a clear clock beside every future time",
        "lesson": "checking another viewpoint can reveal what a hurried glance hides",
        "ending": "the signal lamp shone blue at five o'clock, and every worker could read the new clock marks",
        "question": "Where was the blue lens?",
        "answer": "The blue lens was safely stored on the upper shelf because the register line had been read upside down.",
    },
    {
        "premise": "At nine o'clock, Luna found a blank square in the hangar register",
        "missing": "the tiny clock",
        "risk": "No one knew when the supply cart had entered the building",
        "clue": "three workers remembered hearing the same soft bell",
        "method": "they shared their memories and placed each bell sound on a paper time line",
        "twist": "the tiny clock had rung from inside a crate that had arrived before sunrise",
        "sharing": "they opened the crate together and made a bright shared time chart for the whole hangar",
        "lesson": "different memories can fit together like pieces of one careful map",
        "ending": "the tiny clock ticked above the register while everyone could see the supply cart's true arrival time",
        "question": "How did the detectives find the tiny clock?",
        "answer": "They matched three workers' memories of a bell and discovered the clock inside an early supply crate.",
    },
    {
        "premise": "A red stamp appeared beside the wrong name in the hangar register",
        "missing": "the brass compass",
        "risk": "The owner might be blamed for a tool they had never touched",
        "clue": "the stamp was shaped like a star, but only the children's table used star stamps",
        "method": "they invited every worker to show their stamps instead of accusing anyone",
        "twist": "a child had stamped the line while making a pretend flight plan",
        "sharing": "the child helped repair the register and shared a new page marked for practice notes",
        "lesson": "kind questions can uncover mistakes without making a frightened person hide",
        "ending": "the true owner signed beside the compass, and the practice page filled with cheerful stars",
        "question": "Who made the mistaken red stamp?",
        "answer": "A child made the mistaken red stamp while creating a pretend flight plan.",
    },
]


OPENINGS = [
    "Rain tapped the long glass roof",
    "Moonlight silvered the sleeping runway",
    "Sunrise poured gold across the metal doors",
    "A cool wind hummed through the rafters",
    "The last evening light rested on the polished wings",
]

QUESTION_STARTS = [
    "Luna pointed to the register and asked",
    "Pip leaned close and wondered",
    "Luna held up the page and said",
    "Pip checked the clock and asked",
]

REACTIONS = [
    "Pip's eyes widened, but the answer made sense",
    "Luna smiled because every clue now had a place",
    "The workers leaned together and gave a relieved cheer",
    "Pip nodded and wrote the lesson in careful letters",
]

CODAS = [
    "Luna knew that a shared clue was stronger than a secret guess.",
    "The two detectives learned that honest records help everyone feel safe.",
    "From then on, nobody guarded a clue alone; they placed it where every helper could see.",
    "The hangar grew calmer because questions were shared before blame was given.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective storyworld about a hangar register and an o'clock clue."
    )
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hangar", choices=HANGARS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective or rng.choice(DETECTIVES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != detective])
    if detective == helper:
        raise StoryError("The detective and helper must be different characters.")
    return StoryParams(
        detective=detective,
        helper=helper,
        hangar=args.hangar or rng.choice(HANGARS),
        object_name=args.object_name or rng.choice(OBJECTS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        detective=Entity(params.detective, "detective"),
        helper=Entity(params.helper, "helper"),
        hangar=Entity(params.hangar, "hangar"),
        register=Entity("the hangar register", "register"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    world.detective.memes["curiosity"] = 1.0
    world.detective.memes["care"] = 1.0
    world.helper.memes["cooperation"] = 1.0
    world.hangar.meters["safe"] = 1.0
    world.register.meters["records"] = 1.0
    world.facts.update(
        {
            "hangar": p.hangar,
            "register": "the hangar register",
            "o_clock": True,
            "missing": arc["missing"],
            "clue": arc["clue"],
            "sharing": True,
        }
    )

    world.say(
        f"{rng.choice(OPENINGS)}. In {p.hangar}, {p.detective} and {p.helper} "
        f"kept watch beside the hangar register."
    )
    world.say(f"{arc['premise']}. The line named {arc['missing']}, but its place was empty.")
    world.para()

    world.say(f"{arc['risk']}.")
    world.say(
        f"{p.detective} wanted to solve the puzzle quickly, but {p.helper} reminded "
        f"everyone to share clues before choosing a suspect."
    )
    world.say(
        f"“What does the register tell us?” asked {p.helper}. "
        f"“And what does it leave out?” said {p.detective}."
    )
    world.say(f"The important clue was that {arc['clue']}.")
    world.detective.memes["patience"] = 1.0
    world.facts["risk"] = arc["risk"]
    world.para()

    world.say(f"At exactly seven o'clock, they began: {arc['method']}.")
    world.say(
        f"“I found one part,” said {p.helper}. “Then let us put it beside your part,” "
        f"replied {p.detective}."
    )
    world.say(f"Together they discovered that {arc['twist']}.")
    world.say(rng.choice(REACTIONS))
    world.helper.memes["sharing"] = 1.0
    world.detective.memes["sharing"] = 1.0
    world.facts["solution"] = arc["twist"]
    world.facts["method"] = arc["method"]
    world.para()

    world.say(f"{arc['sharing']}. {rng.choice(CODAS)}")
    world.say(f"At the next o'clock mark, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a child-friendly detective story in {params.hangar} about a missing item in a register.",
        f"Tell a mystery where {params.detective} and {params.helper} share clues at an o'clock time.",
        f"Create a gentle detective story about {arc['missing']} and a surprising register clue.",
    ]
    story_qa = [
        QAItem(
            question=f"What disappeared from the hangar register?",
            answer=f"The missing item was {arc['missing']}.",
        ),
        QAItem(
            question=f"What clue did {params.detective} and {params.helper} share?",
            answer=f"They shared the clue that {arc['clue']}.",
        ),
        QAItem(
            question="When did the detectives begin their careful search?",
            answer="They began their careful search at exactly seven o'clock.",
        ),
        QAItem(
            question="What was the surprising truth?",
            answer=f"The surprising truth was that {arc['twist']}.",
        ),
        QAItem(
            question="What did the detectives learn about sharing?",
            answer=f"They learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a hangar?",
            answer="A hangar is a large building where aircraft or other machines are kept and repaired.",
        ),
        QAItem(
            question="What is a register?",
            answer="A register is a written record that keeps track of people, objects, or events.",
        ),
        QAItem(
            question="What does o'clock mean?",
            answer="O'clock tells the exact hour shown by a clock, such as seven o'clock.",
        ),
        QAItem(
            question="Why can sharing clues help a detective?",
            answer="Sharing clues lets people compare what they noticed and can reveal a safer, clearer answer.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [
        world.detective,
        world.helper,
        world.hangar,
        world.register,
    ]:
        lines.append(
            f"  {entity.name:20} ({entity.kind:9}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
#show sharing_ok/1.
valid(story) :- domain(hangar), feature(register), feature(o_clock), feature(sharing).
sharing_ok(story) :- valid(story), clue_shared, resolved.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "hangar"),
            asp.fact("feature", "register"),
            asp.fact("feature", "o_clock"),
            asp.fact("feature", "sharing"),
            asp.fact("clue_shared"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "#show valid/1.\n#show sharing_ok/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    valid = asp.atoms(model, "valid")
    sharing = asp.atoms(model, "sharing_ok")
    if valid == [("story",)] and sharing == [("story",)]:
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("MISMATCH: generated story check failed.")
                return 1
        print("OK: ASP twin and generated stories are consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(
        detective="Luna",
        helper="Pip",
        hangar="the moon hangar",
        object_name="the brass compass",
        arc=0,
        seed=101,
    ),
    StoryParams(
        detective="Mara",
        helper="Bea",
        hangar="the red hangar",
        object_name="the silver key",
        arc=1,
        seed=202,
    ),
    StoryParams(
        detective="Theo",
        helper="Ollie",
        hangar="the cloud hangar",
        object_name="the blue lens",
        arc=2,
        seed=303,
    ),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        print(asp.atoms(model, "sharing_ok"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 30):
            if len(samples) >= max(args.n, 1):
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
