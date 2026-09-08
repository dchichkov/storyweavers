#!/usr/bin/env python3
"""A child-friendly ghost story about a report, repeated clues, and a misunderstanding."""

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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))

from results import QAItem, StoryError, StorySample  # noqa: E402


TITLE = "The Ghost's Repeated Report"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str = "Luna"
    place: str = "the old moonlit library"
    object_name: str = "the brass bell"
    ghost_name: str = "Mister Whisper"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    name: str
    report: str
    repeated_sound: str
    misunderstanding: str
    clue: str
    ghost_need: str
    resolution: str
    ending: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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


INCIDENTS = [
    Incident(
        "the bell report",
        "someone had written, 'The bell is ringing. Please help.'",
        "Ding. Ding. Ding.",
        "Luna thought the ghost was warning her that the bell was broken",
        "three silver dust marks curved from the bell toward a locked reading room",
        "to show that his old library report had never reached the keeper",
        "the report was read aloud, and the ghost finally received an answer",
        "the brass bell gave one gentle chime, as if the library itself had sighed with relief",
    ),
    Incident(
        "the missing book report",
        "a report said, 'The blue book is gone. Please look below.'",
        "Below. Below. Below.",
        "Luna thought the ghost wanted her to crawl under every table",
        "blue threads clung to a high window latch",
        "to point out that the book had blown onto the roof",
        "Luna followed the repeated words upward and found the book beside the chimney",
        "the blue book rested safely on the desk while moonlight silvered its dusty cover",
    ),
    Incident(
        "the lantern report",
        "a report said, 'The lantern is dark. Do not be afraid.'",
        "Do not be afraid. Do not be afraid.",
        "Luna thought the ghost was telling her that a monster was nearby",
        "warm wax drops led from the lantern to a cold fireplace",
        "to explain that he had carried the lantern there long ago",
        "Luna understood that the ghost was repeating comfort, not a warning",
        "the lantern glowed again, and a soft shadow waved beside Luna on the wall",
    ),
    Incident(
        "the window report",
        "a report said, 'The window knocks three times. Listen carefully.'",
        "Knock. Knock. Knock.",
        "Luna thought the ghost was trapped outside and wanted the window opened",
        "a paper star trembled on the inside sill",
        "to show that the knocking came from a loose shutter",
        "Luna fixed the shutter while the ghost explained the old signal",
        "rain tapped the quiet glass, but the window no longer made a frightening sound",
    ),
    Incident(
        "the portrait report",
        "a report said, 'The portrait cries at midnight. Bring a cloth.'",
        "Crying. Crying. Crying.",
        "Luna thought a sad ghost was hiding inside the painting",
        "a fresh leak shone above the portrait's wooden frame",
        "to ask for help protecting the portrait from rain",
        "Luna covered the frame and discovered that the tears were only water",
        "the portrait smiled in the candlelight, and Mister Whisper's voice sounded less lonely",
    ),
    Incident(
        "the staircase report",
        "a report said, 'The seventh step whispers. Count twice.'",
        "Seven. Seven. Seven.",
        "Luna thought the ghost wanted her to climb the dark stairs alone",
        "a loose floorboard rested beside the seventh step",
        "to warn her about the board and teach her the safe path",
        "Luna placed a bright ribbon by the loose board and counted with a friend",
        "the staircase creaked kindly as everyone walked down together",
    ),
    Incident(
        "the clock report",
        "a report said, 'The clock stops at twelve. Wait and watch.'",
        "Wait. Wait. Wait.",
        "Luna thought the ghost wanted to keep her trapped until midnight",
        "a tiny moth blocked the clock's silver gear",
        "to ask someone patient to clear the clock",
        "Luna waited, opened the clock's little door, and freed the moth",
        "the clock ticked on, and its twelve chimes sounded peaceful instead of spooky",
    ),
    Incident(
        "the candle report",
        "a report said, 'The candle bends toward the garden. Follow gently.'",
        "Gently. Gently. Gently.",
        "Luna thought the ghost was ordering her to carry fire through the dark",
        "a trail of cold ash ended at the garden gate",
        "to guide her toward a lost silver key",
        "Luna left the candle on its safe table and followed the ash with a lantern",
        "the silver key shone in the grass, and no flame came near the dry leaves",
    ),
]


PLACES = [
    "the old moonlit library",
    "the quiet hilltop museum",
    "the little theater beside the cemetery",
]

OBJECTS = [
    "the brass bell",
    "the blue book",
    "the silver lantern",
]

CHILDREN = ["Luna", "Milo", "Nia", "Tess"]
GHOSTS = ["Mister Whisper", "Auntie Echo", "The Pale Librarian"]


def choose_incident(params: StoryParams) -> Incident:
    if params.seed is None:
        return INCIDENTS[0]
    return INCIDENTS[params.seed % len(INCIDENTS)]


def setup_world(params: StoryParams, incident: Incident) -> World:
    world = World(params.place)
    child = world.add(Entity("child", "character", "child", params.child_name))
    ghost = world.add(Entity("ghost", "character", "ghost", params.ghost_name))
    report = world.add(Entity("report", "thing", "report", "the report"))
    object_entity = world.add(Entity("object", "thing", "object", params.object_name))
    world.facts.update(
        child=child,
        ghost=ghost,
        report=report,
        object=object_entity,
        incident=incident,
        place=params.place,
        repeated=True,
        misunderstanding=True,
    )
    return world


def tell(params: StoryParams) -> World:
    incident = choose_incident(params)
    world = setup_world(params, incident)
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    report = world.facts["report"]

    world.say(
        f"At {world.place}, {child.label} found {report.label} tucked beneath a dusty candle. "
        f"It was signed by {ghost.label}, a gentle ghost who had once cared for the place."
    )
    world.say(
        f"The report said, “{incident.report}” Then the same sound or words came again: "
        f"“{incident.repeated_sound}”"
    )
    world.say(
        f"{child.label} read the report twice. “I think {ghost.label} is warning me,” "
        f"{child.label} whispered. “I must be very brave.”"
    )
    world.facts["inner_monologue"] = (
        f"I must be very brave, even if {ghost.label} sounds frightened."
    )
    child.memes["fear"] = 1
    report.meters["unread"] = 1
    world.fired.add(("report_found", incident.name))
    world.para()

    world.say(
        f"Just then, a pale shape floated beside the shelves. {ghost.label} repeated, "
        f"“{incident.repeated_sound}”"
    )
    world.say(
        f"{child.label} stepped back. “Please stop repeating that!” "
        f"{ghost.label} answered, “I am not trying to scare you. I am trying to make you notice.”"
    )
    world.say(
        f"{child.label} had misunderstood the message: {incident.misunderstanding}. "
        f"Instead of guessing, {child.label} asked, “What do you need me to see?”"
    )
    world.say(f"{ghost.label} pointed silently. {incident.clue.capitalize()}.")
    child.memes["fear"] = 0
    child.memes["curiosity"] = 1
    report.meters["unread"] = 0
    world.fired.add(("misunderstanding_named", incident.name))
    world.fired.add(("clue_observed", incident.name))
    world.para()

    world.say(
        f"{ghost.label} explained that the repeated words were an old signal. "
        f"He had repeated them because he wanted {incident.ghost_need}."
    )
    world.say(
        f"{child.label} took a slow breath. “So the report was asking for help, not telling me to panic.” "
        f"“Exactly,” said {ghost.label}. “A repeated message can be a clue, but we must ask what it means.”"
    )
    world.say(f"{incident.resolution.capitalize()}.")
    child.memes["understanding"] = 1
    world.facts.update(
        report_text=incident.report,
        repeated_sound=incident.repeated_sound,
        misunderstanding=incident.misunderstanding,
        clue=incident.clue,
        ghost_need=incident.ghost_need,
        resolution=incident.resolution,
    )
    world.fired.add(("report_understood", incident.name))
    world.para()

    world.say(
        f"Afterward, {child.label} wrote a new report: “{ghost.label} needs someone to listen carefully. "
        "Ask questions before becoming frightened.”"
    )
    world.say(
        f"{ghost.label} smiled, and {child.label} smiled back. {incident.ending.capitalize()}."
    )
    world.fired.add(("ghost_helped", incident.name))
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly ghost story about {facts['child'].label} finding a report in {facts['place']}.",
        f"Use repetition of “{facts['repeated_sound']}” as a clue that is misunderstood at first.",
        "Include the child's inner monologue, a spoken back-and-forth with the ghost, and a happy explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    ghost = facts["ghost"]
    return [
        QAItem(
            question=f"What did {child.label} find?",
            answer=f"{child.label} found a report from {ghost.label} that said, “{facts['report_text']}”",
        ),
        QAItem(
            question="What was repeated in the story?",
            answer=f"The message repeated these words or sounds: “{facts['repeated_sound']}” The repetition was an old signal and a clue.",
        ),
        QAItem(
            question=f"What did {child.label} misunderstand?",
            answer=f"{child.label} thought that {facts['misunderstanding']}. The ghost explained that the repeated message was asking for help instead.",
        ),
        QAItem(
            question="How did the misunderstanding get fixed?",
            answer=f"{child.label} stopped guessing and asked a question. The clue was that {facts['clue']}. Then the ghost explained what he needed.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer=f"{facts['resolution'].capitalize()} {child.label} learned to listen carefully and ask what a mysterious message means before becoming frightened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a report?",
            answer="A report is a message that tells someone what happened, what was noticed, or what help is needed.",
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can make an important clue easier to notice, but people still need to understand what the repeated words mean.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought, such as a worry or plan that the character thinks silently.",
        ),
        QAItem(
            question="How can someone solve a misunderstanding?",
            answer="Someone can solve a misunderstanding by stopping, asking a clear question, listening to the answer, and checking the evidence.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) " + (" ".join(state) or "stable")
        )
    lines.append(f"  fired rules: {sorted({rule for rule, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("feature", "report"),
        asp.fact("feature", "repetition"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("genre", "ghost_story"),
        "needs_clue.",
        "asks_question.",
        "explains_message.",
    ]
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for object_name in OBJECTS:
        lines.append(asp.fact("object", object_name))
    return "\n".join(lines)


ASP_RULES = r"""
report_story :- feature(report), needs_clue, asks_question.
repeated_clue :- feature(repetition), report_story.
thought_present :- feature(inner_monologue), report_story.
misunderstanding_fixed :- feature(misunderstanding), explains_message, asks_question.
good_ghost_story :- report_story, repeated_clue, thought_present, misunderstanding_fixed, genre(ghost_story).
#show report_story/0.
#show repeated_clue/0.
#show thought_present/0.
#show misunderstanding_fixed/0.
#show good_ghost_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_ghost_story/0."))
    if asp.atoms(model, "good_ghost_story"):
        for seed in range(8):
            sample = generate(StoryParams(seed=seed))
            if "report" not in sample.story.lower():
                print("ASP verification failed: report missing from generated story.")
                return 1
            if not sample.story_qa:
                print("ASP verification failed: story QA missing.")
                return 1
        print("OK: ASP parity and generated-story checks passed.")
        return 0
    print("ASP verification failed: no complete ghost story model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ghost story world about a report, repetition, and misunderstanding."
    )
    parser.add_argument("--child-name", choices=CHILDREN, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--object-name", choices=OBJECTS, default=None)
    parser.add_argument("--ghost-name", choices=GHOSTS, default=None)
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
        child_name=args.child_name or rng.choice(CHILDREN),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        ghost_name=args.ghost_name or rng.choice(GHOSTS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if not params.child_name.strip():
        raise StoryError("child_name must not be empty")
    if not params.place.strip():
        raise StoryError("place must not be empty")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(
        child_name="Luna",
        place="the old moonlit library",
        object_name="the brass bell",
        ghost_name="Mister Whisper",
        seed=0,
    ),
    StoryParams(
        child_name="Milo",
        place="the quiet hilltop museum",
        object_name="the blue book",
        ghost_name="Auntie Echo",
        seed=1,
    ),
    StoryParams(
        child_name="Nia",
        place="the little theater beside the cemetery",
        object_name="the silver lantern",
        ghost_name="The Pale Librarian",
        seed=2,
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
        print(asp_program("#show good_ghost_story/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show report_story/0. "
                "#show repeated_clue/0. "
                "#show thought_present/0. "
                "#show misunderstanding_fixed/0. "
                "#show good_ghost_story/0."
            )
        )
        for predicate in (
            "report_story",
            "repeated_clue",
            "thought_present",
            "misunderstanding_fixed",
            "good_ghost_story",
        ):
            print(asp.atoms(model, predicate))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
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

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} / {sample.params.ghost_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
