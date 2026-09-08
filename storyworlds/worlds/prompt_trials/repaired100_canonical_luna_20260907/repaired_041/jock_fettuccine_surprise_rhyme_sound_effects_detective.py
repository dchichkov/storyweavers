#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle detective story about a missing
fettuccine dish, a boastful jock, and clues hidden in rhymes and sounds.
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
    type: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("warmth", "noise", "distance", "fullness"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "pride", "trust", "surprise", "teamwork"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    detective: str = "Luna"
    jock: str = "Jock"
    case: int = 0
    voice: int = 0
    rhyme: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    dish: str
    opening: str
    clue: str
    sound: str
    rhyme: str
    false_lead: str
    discovery: str
    cause: str
    repair: str
    proof: str
    ending: str


CASES = [
    Case(
        dish="a steaming plate of fettuccine",
        opening="the lunch bell rang, but the chef's proud fettuccine was gone",
        clue="a curl of parsley on the floor beside three floury shoeprints",
        sound="a soft clink came from behind the trophy shelf",
        rhyme="When noodles hide from hungry eyes, follow the clink where silver lies.",
        false_lead="an open window made everyone suspect a hungry bird",
        discovery="slid the missing plate from behind the trophy shelf",
        cause="had carried it there to practice a victory speech and forgotten where he set it",
        repair="brought the fettuccine back, warmed a fresh portion, and placed a serving cart beside the kitchen",
        proof="the cart rolled safely, and the clink stopped when the plate was set down",
        ending="Luna wrote the solved case in her notebook while the fettuccine curled like golden ribbons in the bowl.",
    ),
    Case(
        dish="a bowl of creamy fettuccine",
        opening="the dinner table was ready, yet the bowl of fettuccine had vanished",
        clue="a red ribbon from the table decoration caught on a blue gym bag",
        sound="three tiny taps sounded under the wooden bench",
        rhyme="Tap, tap, tap beneath the seat; seek the noodles, warm and neat.",
        false_lead="a sauce spot near the pantry pointed toward the wrong cupboard",
        discovery="lifted the bench and found the bowl tucked safely beneath it",
        cause="had moved it while showing off a strength pose and then covered it with his gym bag",
        repair="cleaned the sauce spot, moved the gym bag to its hook, and served the meal at a clear table",
        proof="nothing blocked the bench, and every bowl stayed visible",
        ending="The detective's pencil tapped a happy rhythm as everyone shared the rescued fettuccine.",
    ),
    Case(
        dish="a basket of fettuccine nests",
        opening="the picnic blanket was spread, but the basket of fettuccine nests had disappeared",
        clue="a strand of pasta trailed toward the old scoreboard",
        sound="the scoreboard made a squeaky chirp whenever the breeze shook it",
        rhyme="A pasta trail will tell the tale; chase each curl beside the rail.",
        false_lead="a picnic kite flying overhead seemed to have carried the basket away",
        discovery="found the basket behind the scoreboard",
        cause="had hidden it while pretending to guard the picnic and then chased a bouncing ball",
        repair="returned the basket, tied the scoreboard gate open, and marked a safe picnic spot",
        proof="the pasta trail ended at the basket, and the gate no longer swung shut",
        ending="The scoreboard chirped once, then the picnic began with warm fettuccine and a solved mystery.",
    ),
]


@dataclass
class World:
    detective: Entity
    jock: Entity
    pasta: Entity
    bell: Entity
    shelf: Entity
    notebook: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    detective = Entity(params.detective, "character", "child", "the detective")
    jock = Entity(params.jock, "character", "child", "the jock")
    pasta = Entity("fettuccine", "food", "dish", "the fettuccine", "kitchen")
    bell = Entity("bell", "thing", "bell", "the lunch bell", "hall")
    shelf = Entity("shelf", "thing", "shelf", "the trophy shelf", "hall")
    notebook = Entity("notebook", "thing", "book", "the detective notebook", "hall")
    return World(detective, jock, pasta, bell, shelf, notebook)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    d, j, p = world.detective, world.jock, world.pasta
    case = CASES[params.case % len(CASES)]

    d.memes["curiosity"] = 2
    d.memes["worry"] = 1
    j.memes["pride"] = 2
    p.meters["warmth"] = 1
    p.meters["distance"] = 1

    openings = [
        f"{d.id} kept a detective notebook in the school hall, where {j.id}, the jock, was helping prepare {case.dish}.",
        f"The school smelled delicious when {d.id} arrived to investigate a new case: {case.dish}. {j.id}, the team's jock, was nearby.",
        f"At lunchtime, {d.id} was checking clues while {j.id} showed off beside the table holding {case.dish}.",
        f"Everything seemed ready for lunch until {d.id} noticed that {case.dish} was no longer where it belonged.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"Then {case.opening}.")
    world.say("Luna's first surprise was not that food had moved, but that someone had left clues behind.")

    world.para()
    world.say(f"On the floor, {case.clue}. {case.false_lead.capitalize()}.")
    world.say(f"Just then, {case.sound}.")
    world.say(f"{d.id} whispered the rhyme, '{case.rhyme}'")
    dialogue = [
        f"'{case.rhyme}' {d.id} said. '{case.false_lead.capitalize()},' {j.id} replied. '{case.sound.capitalize()}'",
        f"'Should we search the window?' {j.id} asked. 'Not yet,' said {d.id}. 'The sound and the pasta clue make a stronger trail.'",
        f"'I am good at spotting things,' {j.id} said. 'Then help me listen carefully,' {d.id} answered. 'A detective tests a clue.'",
        f"'Could the rhyme be right?' {j.id} asked. {d.id} nodded. 'We will follow it, but we will check each step.'",
    ]
    world.say(dialogue[(params.voice + params.rhyme) % len(dialogue)])
    world.say("The jock stopped posing and listened. His pride softened into trust.")

    world.para()
    j.memes["trust"] += 1
    d.memes["curiosity"] += 1
    world.say(f"They followed the sound effect: tap, clink, squeak, then silence.")
    world.say(f"The false lead explained one mark, but it did not explain the sound. {d.id} followed the stronger trail.")
    world.say(f"At last, {d.id} {case.discovery}.")
    p.meters["distance"] = 0
    p.location = "table"
    j.memes["surprise"] += 2
    world.say(f"{j.id} blinked in surprise. 'I can explain,' the jock said. 'I {case.cause}.'")
    world.say(f"{d.id} closed the notebook halfway. 'Thank you for telling the truth. Now we can fix the cause instead of blaming a guess.'")

    world.para()
    d.memes["teamwork"] += 2
    j.memes["teamwork"] += 2
    j.memes["pride"] = max(0, j.memes["pride"] - 1)
    world.say(f"Together, they {case.repair}.")
    world.say(f"They tested the solution: {case.proof}.")
    world.say(f"The rhyme had led them to the sound, and the sound had led them to the surprise.")
    world.say("Luna wrote, 'A fair detective follows evidence, listens to people, and gives a mistake a chance to be repaired.'")

    world.para()
    world.say(case.ending)

    world.facts.update(
        dish=case.dish,
        opening=case.opening,
        clue=case.clue,
        sound=case.sound,
        rhyme=case.rhyme,
        false_lead=case.false_lead,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        ending=case.ending,
        resolved=True,
        location=p.location,
        teamwork=d.memes["teamwork"],
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What went wrong in Luna's detective case?",
            f"The fettuccine disappeared because {f['opening']}.",
        ),
        QAItem(
            "Which clues helped Luna solve the mystery?",
            f"Luna used {f['clue']} and listened when {f['sound']}. The rhyme pointed her toward the real hiding place.",
        ),
        QAItem(
            "What did the jock explain after the fettuccine was found?",
            f"The jock admitted that he {f['cause']}.",
        ),
        QAItem(
            "How did the friends repair the problem?",
            f"Together, they {f['repair']}. They knew it worked because {f['proof']}.",
        ),
        QAItem(
            "What lesson did Luna write down?",
            "A fair detective follows evidence, listens to people, and gives a mistake a chance to be repaired.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is fettuccine?", "Fettuccine is a kind of pasta made in long, flat ribbons."),
        QAItem("What is a jock?", "A jock is an informal word for someone strongly interested in sports or athletic activity."),
        QAItem("What is a rhyme?", "A rhyme is a pattern in which words have matching or similar ending sounds."),
        QAItem("What are sound effects?", "Sound effects are written or performed sounds that help people imagine an action, such as tap, clink, or squeak."),
        QAItem("What does a detective do?", "A detective gathers clues, asks questions, and reasons carefully to solve a mystery."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly detective story in which {world.facts['dish']} goes missing and a jock helps Luna follow a rhyme and sound effects.",
        f"Create a mystery using this clue: {world.facts['clue']}. Include surprise, fair questions, and a concrete repaired ending.",
        "Tell a detective story with the words jock and fettuccine, using a rhyme and sound effects to make the clues memorable.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for entity in [world.detective, world.jock, world.pasta, world.bell, world.shelf, world.notebook]:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: location={entity.location!r} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(detective_story).
requires(detective_story, jock).
requires(detective_story, fettuccine).
feature(detective_story, surprise).
feature(detective_story, rhyme).
feature(detective_story, sound_effects).
valid_story(S) :- setting(S), requires(S,jock), requires(S,fettuccine),
                   feature(S,surprise), feature(S,rhyme), feature(S,sound_effects).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "detective_story"),
        asp.fact("requires", "detective_story", "jock"),
        asp.fact("requires", "detective_story", "fettuccine"),
        asp.fact("feature", "detective_story", "surprise"),
        asp.fact("feature", "detective_story", "rhyme"),
        asp.fact("feature", "detective_story", "sound_effects"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in model)
    if not ok:
        print("MISMATCH: ASP did not accept the detective story domain.")
        return 1
    for i in range(len(CASES)):
        sample = generate(StoryParams(case=i))
        if "fettuccine" not in sample.story.lower() or "jock" not in sample.story.lower():
            print("MISMATCH: generated story omitted required seed words.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detective story world with fettuccine clues.")
    parser.add_argument("--detective", default=None)
    parser.add_argument("--jock", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    detective = args.detective or rng.choice(["Luna", "Mira", "Nell", "Penny"])
    jock = args.jock or rng.choice(["Jock", "Max", "Kai", "Bo"])
    if detective == jock:
        raise StoryError("The detective and jock must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        detective=detective,
        jock=jock,
        case=offset % len(CASES),
        voice=(offset // len(CASES)) % 4,
        rhyme=(offset // (len(CASES) * 4)) % 3,
        ending=(offset // (len(CASES) * 4 * 3)) % 2,
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
    StoryParams(detective="Luna", jock="Jock", case=0),
    StoryParams(detective="Mira", jock="Max", case=1),
    StoryParams(detective="Nell", jock="Kai", case=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print("ASP model:", [str(atom) for atom in asp.one_model(asp_program("#show valid_story/1."))])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample_seed = base_seed + i
            sample = generate(resolve_params(args, random.Random(sample_seed), sample_seed, base_seed))
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
