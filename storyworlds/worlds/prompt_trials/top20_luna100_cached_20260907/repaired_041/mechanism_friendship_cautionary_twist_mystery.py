#!/usr/bin/env python3
"""
A standalone Storyweavers world about a mysterious clockwork friendship.

A small mechanism stops working in the village garden. Two friends follow
physical clues, discover a cautionary truth about rushing repairs, and solve
the mystery through honest teamwork.
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
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("loose", "wound", "jammed", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "trust", "patience", "joy", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    caretaker: str = "Aunt Fern"
    case: int = 0
    dialogue_style: int = 0
    clue_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    project: str
    trouble: str
    clue: str
    false_lead: str
    question: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


CASES = [
    Case(
        project="a brass watering wheel beside the moon garden",
        trouble="the wheel stopped turning just before the thirsty seedlings could be watered",
        clue="a bright blue thread caught around one small gear",
        false_lead="muddy footprints led toward the tool shed",
        question="Which clue touched the mechanism itself?",
        discovery="lifted the guard and found a ribbon tangled around the axle",
        cause="had tied the ribbon to the wheel as a shortcut for marking the garden path, then pulled it too close",
        repair="freed the ribbon, cleaned the axle, and added a wooden marker away from the moving parts",
        proof="the wheel turned smoothly and sent a gentle stream into every planting bed",
        lesson="A quick shortcut can become a hidden danger when it reaches a moving mechanism.",
        ending="Under the moon-shaped sign, the repaired wheel sprinkled silver drops across the leaves.",
    ),
    Case(
        project="a tiny bell mechanism that called children to story hour",
        trouble="the bell stayed silent when the library doors opened",
        clue="a bent paper star lay beneath the spring lever",
        false_lead="a trail of cookie crumbs disappeared under the reading bench",
        question="What object could have pressed the spring?",
        discovery="slid the paper star from between the lever and its wooden stop",
        cause="had pushed the star into the bell while decorating, hoping it would make the bell sound brighter",
        repair="removed the paper, straightened the lever, and made a safe decoration holder beside the bell",
        proof="the bell gave three clear notes without catching",
        lesson="A decoration belongs beside a mechanism, not inside the part that must move.",
        ending="The bell rang above the story rug, and every child looked up with a smile.",
    ),
    Case(
        project="a wind-up lantern for the evening friendship walk",
        trouble="the lantern flickered and went dark halfway along the garden path",
        clue="one gear tooth held a smear of honey",
        false_lead="a dropped matchbox rested near the pond",
        question="What could make a gear stick without leaving a large mark?",
        discovery="found a sticky honey wrapper folded around the smallest gear",
        cause="had tucked the wrapper near the lantern while eating and the breeze pulled it inside",
        repair="removed the wrapper, washed the gear, and made a covered snack basket for the walk",
        proof="the lantern shone steadily from the gate to the old oak",
        lesson="Small bits of rubbish can stop a careful mechanism and create a larger problem.",
        ending="The lantern glowed between the two friends as their shadows walked side by side.",
    ),
    Case(
        project="a wooden music box for the village friendship festival",
        trouble="the music box played only one sour note",
        clue="a tiny screw rested in the sawdust beneath its open lid",
        false_lead="a broken toy drum sat beside the festival stage",
        question="Which missing piece could explain the music stopping?",
        discovery="noticed that the loose screw belonged to the comb's support plate",
        cause="had opened the box with a knife instead of asking for the proper key",
        repair="returned the screw with the right screwdriver and locked the lid until a grown-up could help",
        proof="the music box played its whole tune without a wobble",
        lesson="When a repair needs a special tool, asking first is safer than forcing the problem.",
        ending="The music box played a bright tune while friends hung lanterns over the stage.",
    ),
    Case(
        project="a hand-cranked model bridge for the school mystery fair",
        trouble="the bridge would not rise when the first team reached the river display",
        clue="a red thread stretched from the crank to a loose wheel",
        false_lead="wet footprints crossed the paper river",
        question="What did the thread show about the stopped bridge?",
        discovery="followed the thread and found it wound around the lifting wheel",
        cause="had used the crank to pull a banner into place while the bridge was still attached",
        repair="unwound the thread, secured the banner separately, and tested the bridge with gentle turns",
        proof="the bridge rose and lowered without tugging the banner",
        lesson="One tool should not be asked to do two jobs when the jobs can interfere.",
        ending="The model bridge lifted for the judges, revealing a painted river shining below.",
    ),
]


@dataclass
class World:
    hero: Entity
    friend: Entity
    caretaker: Entity
    mechanism: Entity
    clue_object: Entity
    garden: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def make_entity(eid: str, kind: str, label: str, type_: str = "thing", location: str = "") -> Entity:
    return Entity(id=eid, kind=kind, label=label, type=type_, location=location)


def build_world(params: StoryParams) -> World:
    return World(
        hero=make_entity(params.hero, "character", params.hero, "child"),
        friend=make_entity(params.friend, "character", params.friend, "child"),
        caretaker=make_entity(params.caretaker, "character", params.caretaker, "adult"),
        mechanism=make_entity("mechanism", "device", "the mechanism", "machine", "the garden"),
        clue_object=make_entity("clue", "object", "the clue", "object"),
        garden=make_entity("garden", "place", "the garden", "place"),
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, f, c, m = world.hero, world.friend, world.caretaker, world.mechanism
    case = CASES[params.case % len(CASES)]

    h.memes["worry"] = 1
    f.memes["trust"] = 1
    f.memes["curiosity"] = 1
    m.meters["jammed"] = 1
    m.meters["loose"] = 1

    openings = [
        f"At sunrise, {h.id} and {f.id} hurried to the garden to finish {case.project}.",
        f"The village was preparing for a special day, and {h.id} and {f.id} were checking {case.project}.",
        f"{h.id} and {f.id} had promised to care for the garden before breakfast, beginning with {case.project}.",
        f"Near the quiet garden gate, {h.id} and {f.id} worked side by side on {case.project}.",
    ]
    world.say(openings[params.dialogue_style % len(openings)])
    world.say(f"Then {case.trouble}. {c.id} had trusted the children to inspect it carefully.")
    world.say(f"The silent device made {h.id} worry, because the mechanism was needed before the day grew hot.")

    world.para()
    world.say(f"Beside the stopped parts, they saw {case.clue}.")
    world.say(f"At the same time, {case.false_lead}.")
    clue_lines = [
        f"{h.id} whispered, 'The footprints may explain who walked here, but {case.question}'",
        f"'{case.question}' {f.id} asked. {h.id} looked closely at the gears.",
        f"{h.id} pointed to the moving parts. 'We should test the clue that actually touched the mechanism.'",
        f"'Let us not blame the first thing we notice,' {f.id} said. 'The mechanism can tell us what happened.'",
    ]
    world.say(clue_lines[params.clue_style % len(clue_lines)])
    world.say(f"{h.id} replied, 'You are right. We will search together and check each idea.'")
    f.memes["trust"] += 1
    h.memes["patience"] += 1

    world.para()
    searches = [
        f"They checked the false lead first, but it ended at the shed door. Then they returned to the part that had actually touched the mechanism.",
        f"The easy answer led nowhere. Because the friends compared their observations instead of arguing, the stronger clue became clear.",
        f"They searched slowly, keeping their hands away from the moving parts until {c.id} brought the safe tools.",
        f"One friend watched the axle while the other traced the clue. Their separate observations joined into one useful answer.",
    ]
    world.say(searches[params.dialogue_style % len(searches)])
    world.say(f"At last, {h.id} and {f.id} {case.discovery}.")
    m.meters["jammed"] = 0
    m.meters["loose"] = 0
    h.memes["curiosity"] += 1
    f.memes["curiosity"] += 1

    twists = [
        f"{f.id} blinked. 'I thought the mystery was about the footprints.' {h.id} answered, 'The twist is that the smallest object stopped the largest part.'",
        f"{c.id} looked surprised. 'So the loud clue was not the true clue?' 'No,' said {h.id}. 'The mechanism kept the secret in a tiny place.'",
        f"The friends had expected a broken gear, but the real trouble was something placed there by a friend trying to help.",
        f"The mystery turned gently: nobody had meant to damage anything, yet a hurried helpful act had made the mechanism unsafe.",
    ]
    world.say(twists[params.clue_style % len(twists)])
    world.say(f"{c.id} admitted, 'I {case.cause}. I should have asked before changing anything.'")
    c.memes["worry"] += 1

    world.para()
    world.say(f"{h.id} said, 'Thank you for telling us. We can fix the cause, not just the symptom.'")
    world.say(f"The friends {case.repair}.")
    h.memes["trust"] += 1
    f.memes["trust"] += 1
    c.memes["pride"] += 1
    world.say(f"They tested the repair: {case.proof}.")
    world.say(f"{c.id} added a cautionary sign: {case.lesson}")
    world.say(f"{f.id} smiled. 'A good friendship tells the truth and makes room for a safer next try.'")

    world.para()
    world.say(case.ending)

    world.facts.update(
        case=case,
        project=case.project,
        trouble=case.trouble,
        clue=case.clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What mystery did the friends investigate?",
            answer=f"The mechanism stopped working while they were preparing {f['project']}. They investigated why it had jammed.",
        ),
        QAItem(
            question="Which clue helped solve the mystery?",
            answer=f"They followed {f['clue']} because it had touched or affected the mechanism, while the false lead did not explain the stopped parts.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The problem was not caused by the obvious clue. The mechanism was stopped because {f['cause']}.",
        ),
        QAItem(
            question="How did friendship help the characters?",
            answer=f"They listened without blaming, shared their observations, and {f['repair']}. Their trust made the repair safer.",
        ),
        QAItem(
            question="What cautionary lesson did they learn?",
            answer=f"They learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of moving parts that work together to make something happen, such as turning a wheel, ringing a bell, or lifting a bridge.",
        ),
        QAItem(
            question="Why should people be careful around moving parts?",
            answer="Moving parts can pinch, catch, or break objects, so people should keep fingers and loose items away and ask for help when a repair needs special tools.",
        ),
        QAItem(
            question="What makes a good friendship?",
            answer="A good friendship includes honesty, listening, trust, and helping one another make safe choices.",
        ),
        QAItem(
            question="What is a mystery clue?",
            answer="A mystery clue is a detail that helps explain what happened. The strongest clue usually connects directly to the problem.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means giving a warning about danger or about a mistake that people should avoid repeating.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly mystery about {world.facts['project']} and a mechanism that suddenly stops.",
        f"Use friendship, a cautionary lesson, and a surprising twist involving this clue: {world.facts['clue']}.",
        "Tell the story with concrete evidence, brief dialogue, a safe repair, and an ending image that proves the mechanism works again.",
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
    for entity in [world.hero, world.friend, world.caretaker, world.mechanism, world.clue_object, world.garden]:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:10}) "
            f"meters={meters} memes={memes} location={entity.location or 'unspecified'}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(garden).
has_feature(garden, mechanism).
has_feature(garden, friendship).
has_feature(garden, cautionary).
has_feature(garden, twist).
has_feature(garden, mystery).

valid_story(S) :-
    setting(S),
    has_feature(S, mechanism),
    has_feature(S, friendship),
    has_feature(S, cautionary),
    has_feature(S, twist),
    has_feature(S, mystery).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "garden"),
            asp.fact("has_feature", "garden", "mechanism"),
            asp.fact("has_feature", "garden", "friendship"),
            asp.fact("has_feature", "garden", "cautionary"),
            asp.fact("has_feature", "garden", "twist"),
            asp.fact("has_feature", "garden", "mystery"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.one_model(asp_program("#show valid_story/1."))
    if any(atom.name == "valid_story" for atom in models):
        sample = generate(StoryParams(seed=0))
        if all(word in sample.story.lower() for word in ("mechanism", "friendship", "mystery")):
            print("OK: ASP and Python recognize the mechanism friendship mystery domain.")
            return 0
        print("MISMATCH: generated story lacks required domain language.")
        return 1
    print("MISMATCH: ASP rules rejected the domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A friendship mystery about a stopped mechanism.")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--caretaker", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nia", "Pip", "Suri", "Mara"])
    friend = args.friend or rng.choice(["Milo", "Tavi", "Ren", "Ollie", "Bea"])
    caretaker = args.caretaker or rng.choice(["Aunt Fern", "Uncle Sol", "Mara's Dad", "Grandma Jo"])
    if hero == friend:
        raise StoryError("The hero and friend must have different names.")
    if caretaker in {hero, friend}:
        raise StoryError("The caretaker must be different from the children.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        case=offset % len(CASES),
        dialogue_style=(offset // len(CASES)) % 4,
        clue_style=(offset // (len(CASES) * 4)) % 4,
        ending_style=(offset // (len(CASES) * 16)) % 4,
        seed=sample_seed,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero="Luna", friend="Milo", caretaker="Aunt Fern", case=0, seed=0),
    StoryParams(hero="Nia", friend="Tavi", caretaker="Uncle Sol", case=1, seed=1),
    StoryParams(hero="Pip", friend="Ren", caretaker="Grandma Jo", case=2, seed=2),
    StoryParams(hero="Suri", friend="Ollie", caretaker="Mara's Dad", case=3, seed=3),
    StoryParams(hero="Mara", friend="Bea", caretaker="Aunt Fern", case=4, seed=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print("ASP model:", [str(atom) for atom in asp.one_model(asp_program("#show valid_story/1."))])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 50):
            sample_seed = base_seed + index
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
