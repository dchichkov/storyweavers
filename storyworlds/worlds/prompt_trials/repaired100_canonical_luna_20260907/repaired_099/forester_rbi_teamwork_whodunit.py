#!/usr/bin/env python3
"""
A small child-facing teamwork whodunit about a forester and an RBI team.

A wooden trail marker disappears from a forest station. The forester and the
RBI (Riddle-solving Bureau of Investigators) gather clues, question helpers,
and solve the mystery together. The story's answer comes from physical traces,
not a lucky guess.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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

    def __post_init__(self) -> None:
        for key in ("energy", "urgency", "visibility", "confidence"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "trust", "pride", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    forester_name: str = "Luna"
    rbi_name: str = "The RBI"
    forest_name: str = "Pinewhistle Forest"
    marker_name: str = "the blue trail marker"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CASE_FILES = [
    {
        "object": "the blue trail marker",
        "problem": "the marker was gone from a fork where young hikers needed it",
        "clue": "a clean rectangle in the dust showed that the marker had been lifted, not blown away",
        "second_clue": "blue paint flecks led toward the creek bridge",
        "suspects": "a gusty wind, a curious beaver, and a cart driver",
        "answer": "the cart driver had moved it to brace a loose wheel",
        "plan": "followed the paint flecks while another investigator checked the safe paths",
        "resolution": "the team found the marker beside the bridge and returned it after the wheel was safely repaired",
        "ending": "the blue marker pointed down the path again while the cart rolled away slowly",
    },
    {
        "object": "the brass bell from the ranger gate",
        "problem": "the bell vanished before the forest walk began",
        "clue": "the empty hook held a smear of yellow pollen",
        "second_clue": "matching pollen dotted the route to the beehive garden",
        "suspects": "a prankster squirrel, a sleepy owl, and the school gardener",
        "answer": "the school gardener had carried it to scare deer away from new seedlings",
        "plan": "split into pairs and compared the pollen trail with each person's morning work",
        "resolution": "the bell was found near the seedlings and returned once a quieter deer signal was arranged",
        "ending": "the restored bell gave one gentle ring as the seedlings lifted their leaves",
    },
    {
        "object": "the red notebook from the fire lookout",
        "problem": "the notebook containing weather notes disappeared from the desk",
        "clue": "a damp corner mark matched the shape of a rain barrel lid",
        "second_clue": "tiny wet footprints crossed the porch toward the storage shed",
        "suspects": "a crow, a cloud of rain, and the supply keeper",
        "answer": "the supply keeper had moved it to the shed while wiping rain from the lookout desk",
        "plan": "checked the desk, porch, and shed in order instead of blaming the first creature they saw",
        "resolution": "the notebook was found dry inside the shed, and the weather notes were copied onto a fresh page",
        "ending": "the red notebook rested beside a sunny window, open to tomorrow's forecast",
    },
    {
        "object": "the silver compass from the nature table",
        "problem": "the compass disappeared during a lesson about directions",
        "clue": "a circle in the flour showed where its round case had rested",
        "second_clue": "a narrow flour trail crossed the table toward the model mountain",
        "suspects": "a mischievous jay, a gust from the window, and the science teacher",
        "answer": "the science teacher had placed it inside the model mountain to demonstrate a hidden tunnel",
        "plan": "recreated the compass's path and asked each helper what they had demonstrated",
        "resolution": "the compass came out of the model mountain, and the lesson continued with everyone informed",
        "ending": "the silver needle settled north while every child drew a careful map",
    },
    {
        "object": "the green seed pouch",
        "problem": "the pouch vanished from the planting bench",
        "clue": "three seeds lay in a line beneath the bench",
        "second_clue": "the line ended at a small open garden gate",
        "suspects": "a hungry mouse, a playful fox, and the nursery helper",
        "answer": "the nursery helper had moved it to the garden gate before the rain arrived",
        "plan": "worked together to follow the seeds and inspect places protected from the rain",
        "resolution": "the pouch was found under the gate roof, and the seeds were planted before the shower",
        "ending": "green shoots soon appeared in a neat row beside the garden gate",
    },
]


def _case_index(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed % len(CASE_FILES)
    return sum(ord(c) for c in params.forester_name + params.forest_name) % len(CASE_FILES)


def tell(params: StoryParams) -> World:
    if not params.forester_name.strip():
        raise StoryError("forester_name must not be empty")
    if not params.rbi_name.strip():
        raise StoryError("rbi_name must not be empty")
    if not params.forest_name.strip():
        raise StoryError("forest_name must not be empty")

    case_index = _case_index(params)
    case = dict(CASE_FILES[case_index])
    case["object"] = params.marker_name if case_index == 0 else case["object"]

    world = World()
    forester = world.add(Entity(
        id="forester",
        kind="character",
        type="forester",
        label=params.forester_name,
        location="forest station",
    ))
    rbi = world.add(Entity(
        id="rbi",
        kind="group",
        type="rbi",
        label=params.rbi_name,
        location="forest station",
    ))
    missing = world.add(Entity(
        id="missing_object",
        type="clue_object",
        label=case["object"],
        location="unknown",
    ))
    station = world.add(Entity(
        id="station",
        type="forest_station",
        label="the forest station",
        location=params.forest_name,
    ))

    forester.memes["curiosity"] = 2
    forester.memes["trust"] = 1
    rbi.memes["curiosity"] = 2
    rbi.memes["trust"] = 1
    forester.meters["urgency"] = 2
    rbi.meters["confidence"] = 1

    world.say(
        f"At the edge of {params.forest_name}, forester {params.forester_name} opened the station gate "
        f"and discovered that {case['problem']}."
    )
    world.say(
        f"{params.forester_name} called {params.rbi_name}, the Riddle-solving Bureau of Investigators. "
        f"They were a small team that solved mysteries by sharing observations."
    )

    world.para()
    forester.memes["worry"] += 1
    rbi.memes["curiosity"] += 1
    world.say(
        f"'We should question everyone at once,' said {params.forester_name}. "
        f"'We should first protect the clues,' replied {params.rbi_name}."
    )
    world.say(
        f"Together they examined the empty place. The first clue was clear: {case['clue']}. "
        f"That meant the missing object had been moved by someone or something nearby."
    )
    world.say(
        f"'Could it be {case['suspects']}?' asked the forester. "
        f"'Perhaps,' said the RBI, 'but a suspect is not an answer. We need evidence.'"
    )

    world.para()
    forester.meters["confidence"] += 1
    rbi.meters["confidence"] += 1
    world.say(
        f"The team {case['plan']}. Then they noticed another trace: {case['second_clue']}."
    )
    world.say(
        f"{params.forester_name} compared the trace with the forest map, while {params.rbi_name} "
        "asked calm questions and listened to every reply."
    )
    world.say(
        f"The clues pointed to one explanation: {case['answer']}. "
        f"'Now our guess has a reason,' said {params.forester_name}."
    )

    world.para()
    forester.memes["relief"] += 1
    rbi.memes["pride"] += 1
    missing.location = "returned"
    world.say(f"{case['resolution']}.")
    world.say(
        f"The forester thanked the RBI. 'I noticed the dust,' said {params.forester_name}, "
        f"'and you noticed what the dust meant.' 'That is teamwork,' answered {params.rbi_name}."
    )
    world.say(
        f"{case['ending']}. The mystery was solved because the team observed, compared, "
        "and decided together instead of blaming someone too soon."
    )

    world.facts.update(
        params=params,
        case=case,
        case_index=case_index,
        forester=forester,
        rbi=rbi,
        missing=missing,
        station=station,
        resolved=True,
        teamwork=True,
        evidence_used=[case["clue"], case["second_clue"]],
        culprit_explanation=case["answer"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a child-friendly whodunit about forester {params.forester_name} and {params.rbi_name} solving a forest mystery.",
        f"Use teamwork to investigate why {case['object']} disappeared, following physical clues before naming a suspect.",
        "End with a concrete image showing that the missing object was returned and the forest became safer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params = facts["params"]
    case = facts["case"]
    return [
        QAItem(
            question=f"Who worked on the mystery with forester {params.forester_name}?",
            answer=f"{params.rbi_name}, the Riddle-solving Bureau of Investigators, worked with the forester as a team."
        ),
        QAItem(
            question=f"What happened to {case['object']}?",
            answer=f"{case['object'].capitalize()} disappeared from its usual place, so the forester and the RBI investigated."
        ),
        QAItem(
            question="What was the first important clue?",
            answer=f"The first clue was that {case['clue']}. This showed that the object had been moved rather than simply lost to the weather."
        ),
        QAItem(
            question="What second clue helped solve the mystery?",
            answer=f"The team noticed that {case['second_clue']}. That trace connected the missing object to the place where it was found."
        ),
        QAItem(
            question="Who moved the object, and why?",
            answer=f"The evidence showed that {case['answer']}. The team reached that conclusion by comparing clues instead of guessing."
        ),
        QAItem(
            question="How did teamwork help the investigators?",
            answer=f"The forester compared the map and physical traces while the RBI asked questions and organized the evidence. Their different jobs made the explanation clear."
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{case['resolution']}. The object was returned and the forest problem was handled safely."
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does a forester do?",
        answer="A forester cares for forests, studies trees and wildlife, and helps keep woodland places healthy and safe."
    ),
    QAItem(
        question="What can RBI mean in this story?",
        answer="In this story, RBI means Riddle-solving Bureau of Investigators, a fictional team that studies clues."
    ),
    QAItem(
        question="What is teamwork?",
        answer="Teamwork means people share jobs, listen to one another, and combine their skills to reach a goal."
    ),
    QAItem(
        question="Why should investigators use evidence?",
        answer="Evidence gives a reason for an explanation and helps investigators avoid blaming someone based only on a guess."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if abs(v) > 1e-9}
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:16} ({entity.type:14}) {' '.join(details)}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    lines.append(f"  teamwork={world.facts.get('teamwork')}")
    return "\n".join(lines)


ASP_RULES = r"""
investigated :- forester, rbi, evidence_one, evidence_two.
teamwork :- forester, rbi, shared_plan.
resolved :- investigated, teamwork, returned.
reasonable :- resolved.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("forester", "forester"),
            asp.fact("rbi", "rbi"),
            asp.fact("evidence_one"),
            asp.fact("evidence_two"),
            asp.fact("shared_plan"),
            asp.fact("returned"),
            asp.fact("missing_object", "clue_object"),
            asp.fact("theme", "teamwork"),
            asp.fact("theme", "whodunit"),
        ]
    )


def asp_program(show: str = "#show reasonable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show reasonable/0."))
    if any(symbol.name == "reasonable" for symbol in model):
        print("OK: ASP and Python both recognize a resolved teamwork mystery.")
        return 0
    print("MISMATCH: ASP did not recognize the resolved mystery.")
    return 1


def _python_gate(world: World) -> bool:
    return bool(
        world.facts.get("resolved")
        and world.facts.get("teamwork")
        and len(world.facts.get("evidence_used", [])) >= 2
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Forester and RBI teamwork whodunit storyworld."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--forester-name")
    parser.add_argument("--rbi-name")
    parser.add_argument("--forest-name")
    parser.add_argument("--marker-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    forester = args.forester_name or rng.choice(["Luna", "Mira", "Rowan", "Tess"])
    rbi = args.rbi_name or rng.choice(["the RBI", "the Forest RBI", "the Little RBI"])
    forest = args.forest_name or rng.choice(
        ["Pinewhistle Forest", "Mossbell Wood", "Sunbeam Forest", "Whispering Pines"]
    )
    marker = args.marker_name or "the blue trail marker"
    return StoryParams(
        seed=args.seed,
        forester_name=forester,
        rbi_name=rbi,
        forest_name=forest,
        marker_name=marker,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    if not _python_gate(world):
        raise StoryError("generated world failed its reasonableness gate")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(seed=0, forester_name="Luna", rbi_name="the RBI", forest_name="Pinewhistle Forest"),
    StoryParams(seed=1, forester_name="Mira", rbi_name="the Forest RBI", forest_name="Mossbell Wood"),
    StoryParams(seed=2, forester_name="Rowan", rbi_name="the Little RBI", forest_name="Sunbeam Forest"),
    StoryParams(seed=3, forester_name="Tess", rbi_name="the RBI", forest_name="Whispering Pines"),
    StoryParams(seed=4, forester_name="Luna", rbi_name="the Forest RBI", forest_name="Pinewhistle Forest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            sample = generate(params)
            if not _python_gate(sample.world):
                print("MISMATCH: Python gate failed during generated-story verification.")
                sys.exit(1)
        print("OK: generated stories passed the Python reasonableness gate.")
        return

    if args.asp:
        import asp

        print(asp.one_model(asp_program("#show reasonable/0.")))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

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
