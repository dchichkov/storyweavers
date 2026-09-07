#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding what kindness needs."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)
    speaker: str = ""


@dataclass
class StoryParams:
    child: str = "Lena"
    helper: str = "Omar"
    problem: str = "missing_place"
    solution: str = "follow_clues"
    mood: str = "hopeful"
    dish: str = "blue_bowl"
    seed: int = 777


NAMES = ("Lena", "Omar", "Pia", "Theo", "Mara", "Jonah")
PROBLEMS = {
    "missing_place": "A darling guest's place at the table is missing.",
    "spilled_soup": "A warm soup spill threatens the family quest.",
    "dark_room": "A power flicker leaves the dining room uncertain.",
    "lost_note": "A thank-you note disappears before dinner.",
}
SOLUTIONS = {
    "follow_clues": "search_with_clues",
    "share_place": "make_new_place",
    "use_lantern": "light_safely",
    "ask_together": "ask_and_listen",
}
VALID = {
    ("missing_place", "follow_clues"),
    ("missing_place", "share_place"),
    ("spilled_soup", "share_place"),
    ("spilled_soup", "ask_together"),
    ("dark_room", "use_lantern"),
    ("dark_room", "ask_together"),
    ("lost_note", "follow_clues"),
    ("lost_note", "ask_together"),
}
DISHES = {
    "blue_bowl": ("a blue bowl", "blue"),
    "sun_plate": ("a yellow sun plate", "yellow"),
    "green_cup": ("a green cup", "green"),
}
MOODS = ("hopeful", "tender", "brave")
PROMPT = (
    "Write a heartwarming children's story set in a dining room, where a child "
    "must decide, darling, how to solve a small quest through inner monologue and suspense."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "child": Entity("child", params.child, "character", "dining_room",
                            memes={"courage": 0.4, "care": 0.7}),
            "helper": Entity("helper", params.helper, "character", "dining_room",
                             memes={"patience": 0.7, "care": 0.7}),
            "table": Entity("table", "the dining table", "furniture", "dining_room",
                            meters={"seats": 3, "ready": 0}),
            "window": Entity("window", "the round window", "place", "dining_room"),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def say(self, speaker: str, text: str):
        if speaker not in self.entities:
            raise StoryError("Unknown speaker.")
        label = self.entities[speaker].label
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {tag}.',
                                  state=self.snapshot(), speaker=speaker))

    def think(self, text: str):
        label = self.entities["child"].label
        self.history.append(Event("thought", f"{label} thought, “{text}”",
                                  state=self.snapshot()))

    def sample(self) -> StorySample:
        qa = [
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in self.history if event.question
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=qa,
            world_qa=[
                QAItem("Where does this quest happen?", "It happens in the dining room."),
                QAItem("What makes a quest feel safe?", "People notice clues, listen to one another, and choose a careful action."),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if (params.problem, params.solution) not in VALID:
        raise StoryError(
            f"{params.solution!r} cannot solve {params.problem!r}; choose a compatible solution."
        )
    if params.child == params.helper:
        raise StoryError("The child and helper need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", n) for n in (params.child, params.helper)):
        raise StoryError("Names must be simple capitalized words.")
    if params.dish not in DISHES or params.mood not in MOODS:
        raise StoryError("Unknown dish or mood.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    bowl, color = DISHES[params.dish]
    world.entities["dish"] = Entity(
        "dish", bowl, "dish", "cupboard", meters={"safe": 1},
        memes={"welcome": 0.8},
    )
    world.entities["note"] = Entity(
        "note", "the thank-you note", "paper", "dining_room",
        meters={"found": 0, "read": 0},
    )
    world.entities["lantern"] = Entity(
        "lantern", "the little lantern", "tool", "sideboard",
        meters={"lit": 0, "safe": 1},
    )
    world.entities["table"].memes["dish_color"] = color
    return world


def finish_check(world: World):
    p = world.params
    if p.problem == "missing_place":
        if world.entities["table"].meters["ready"] != 1:
            raise StoryError("The missing guest must receive a real place at the table.")
    elif p.problem == "spilled_soup":
        if not world.entities["table"].meters.get("cleaned"):
            raise StoryError("The soup spill must be cleaned before dinner.")
    elif p.problem == "dark_room":
        if not world.entities["lantern"].meters["lit"] and not world.entities["table"].meters.get("safe"):
            raise StoryError("The dining room must become safely bright.")
    elif p.problem == "lost_note":
        if not world.entities["note"].meters["found"]:
            raise StoryError("The lost note must be found.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    child = world.entities["child"].label
    helper = world.entities["helper"].label
    dish, _ = DISHES[params.dish]

    world.narrate(
        "beginning",
        f"In the dining room, {child} set {dish} beside three shining spoons. "
        f"Tonight's little quest was to make everyone feel expected.",
    )
    world.say("child", f"Darling, {helper}, do you think the table is ready?")
    world.say("helper", "It looks ready, but one small thing is not right.")

    if params.problem == "missing_place":
        world.entities["table"].meters["seats"] = 2
        world.think("I could squeeze in another chair, but what if that is not the real trouble?")
        world.narrate(
            "suspense",
            f"{child} counted the chairs. There were only two, though a third spoon waited by {dish}. "
            "The empty space seemed to hold a secret.",
            question="Why did the table not feel ready?",
            cause="There were only two chairs for three people, even though a third spoon was waiting.",
            result="The children had to decide whether to search for a chair or make a welcoming place another way.",
        )
        if params.solution == "follow_clues":
            world.say("child", "Let's follow the clues before we move anything.")
            world.say("helper", "The spoon points toward the cupboard.")
            world.think("A spoon is not a map, but it may be a small shiny arrow.")
            world.entities["table"].meters["ready"] = 1
            world.entities["table"].meters["seats"] = 3
            world.narrate(
                "turn",
                f"Behind the cupboard, {child} found a folding chair tucked beside a basket. "
                f"They carried it to the table and placed {dish} before it.",
                question="How did they find the missing chair?",
                cause="They treated the waiting spoon as a clue and searched near the cupboard.",
                result="They found a folding chair and added a true third place.",
            )
        else:
            world.say("child", "We do not need a perfect chair to welcome someone.")
            world.say("helper", "Then we can share the long bench.")
            world.think("A welcome is something we do, not just something furniture says.")
            world.entities["table"].meters["ready"] = 1
            world.entities["table"].meters["seats"] = 3
            world.entities["table"].meters["shared_bench"] = 1
            world.narrate(
                "turn",
                f"They moved the long bench close. {child} set {dish} between two plates, "
                "leaving a warm, comfortable place for the guest.",
                question="How did they welcome the guest without another chair?",
                cause="They decided that the long bench could be shared safely.",
                result="They made a real place by sitting close and sharing the bench.",
            )

    elif params.problem == "spilled_soup":
        world.entities["table"].meters["soup"] = 1
        world.think("I want to save the supper, but rushing could spread the puddle.")
        world.narrate(
            "suspense",
            f"A spoon slipped, and soup spread toward {dish}. The golden puddle trembled "
            "near the table's edge.",
            question="Why did the children pause before cleaning the soup?",
            cause="The soup was moving toward the dish and could spread if they rushed.",
            result="They needed to choose a calm, useful action.",
        )
        if params.solution == "share_place":
            world.say("child", "You guard the bowl while I make a dry place.")
            world.say("helper", "I will hold the tray steady.")
            world.entities["table"].meters["cleaned"] = 1
            world.entities["table"].meters["tray"] = 1
            world.narrate(
                "turn",
                f"{helper} held the tray while {child} moved {dish} away from the spill. "
                "Together they laid a cloth over the damp wood.",
                question="How did they keep the meal safe?",
                cause=f"{helper} held the tray steady while {child} moved {dish} away.",
                result="The bowl reached a dry tray and the table was covered with a cloth.",
            )
        else:
            world.say("child", "Please tell me where to start.")
            world.say("helper", "Start at the edge and wipe toward the spoon.")
            world.entities["table"].meters["cleaned"] = 1
            world.entities["table"].meters["spoon_saved"] = 1
            world.narrate(
                "turn",
                f"They wiped from the edge inward, just as {helper} explained. "
                "The soup stopped spreading, and the spoon was saved.",
                question="What advice solved the soup problem?",
                cause=f"{helper} explained to wipe from the edge toward the spoon.",
                result="The children stopped the spill from spreading and saved the spoon.",
            )

    elif params.problem == "dark_room":
        world.entities["table"].meters["safe"] = 0
        world.think("The shadows make every choice look larger. I must not grab blindly.")
        world.narrate(
            "suspense",
            "The dining-room lamp flickered out. Spoons became silver shadows, and the doorway seemed farther away.",
            question="Why did the children avoid rushing through the dark?",
            cause="The flickering lamp made objects hard to see and made a blind grab unsafe.",
            result="They needed light or a careful plan before touching anything.",
        )
        if params.solution == "use_lantern":
            world.say("child", "The little lantern is on the sideboard. May I fetch it with you?")
            world.say("helper", "Yes. We will keep one hand on the table.")
            world.entities["lantern"].meters["lit"] = 1
            world.entities["table"].meters["safe"] = 1
            world.narrate(
                "turn",
                f"With one hand on the table, they reached the sideboard. {child} lit the lantern, "
                "and its warm circle returned the dining room to them.",
                question="How did the children make the dark room safe?",
                cause="They used the table as a guide while fetching the little lantern.",
                result="The lantern lit a warm circle, so they could see safely.",
            )
        else:
            world.say("child", "Can we ask before anyone moves?")
            world.say("helper", "Yes. I know where the lantern is.")
            world.entities["lantern"].meters["lit"] = 1
            world.entities["table"].meters["safe"] = 1
            world.narrate(
                "turn",
                f"By speaking slowly, {helper} guided {child} to the sideboard. "
                "They lit the lantern together without knocking over a single cup.",
                question="How did asking together help in the dark?",
                cause=f"{child} asked before moving, and {helper} knew where the lantern was.",
                result="Their shared directions led them safely to the lantern.",
            )

    else:
        world.entities["note"].location = "under_table"
        world.think("The note is small, but the feeling inside it is not. I must look gently.")
        world.narrate(
            "suspense",
            f"The thank-you note was gone from the sideboard. A tiny corner of paper showed beneath the table, "
            f"but {child} was not sure whether it was the note or a napkin.",
            question="Why was finding the note difficult?",
            cause="Only a tiny corner showed beneath the table, and it might have been a napkin.",
            result="The children needed to inspect the clue instead of guessing.",
        )
        if params.solution == "follow_clues":
            world.say("child", "The corner has a red heart. That is our clue.")
            world.say("helper", "Then follow the heart, darling detective.")
            world.entities["note"].meters["found"] = 1
            world.entities["note"].meters["read"] = 1
            world.narrate(
                "turn",
                f"{child} knelt and followed the red heart to the note beneath the table. "
                "The message was still dry, folded beside a lost napkin.",
                question="What clue led them to the note?",
                cause="They noticed the red heart on the paper corner.",
                result="They followed it beneath the table and found the dry, folded note.",
            )
        else:
            world.say("child", "I could guess, or I could ask you what you saw.")
            world.say("helper", "I saw paper, not cloth. Let us look together.")
            world.entities["note"].meters["found"] = 1
            world.entities["note"].meters["read"] = 1
            world.narrate(
                "turn",
                f"They crouched together. {helper} held the corner while {child} pulled out "
                "the thank-you note and read its first bright word.",
                question="How did asking for another view help?",
                cause=f"{child} asked what {helper} had seen, and {helper} distinguished paper from cloth.",
                result="Together they identified and recovered the thank-you note.",
            )

    world.say("child", "We decided carefully, and now the table can welcome everyone.")
    world.say("helper", "A small quest can make a very big kind feeling.")
    world.entities["child"].memes["courage"] = 1.0
    world.entities["helper"].memes["patience"] = 1.0
    world.narrate(
        "ending",
        f"The dining room glowed with the finished choice. {dish} rested safely, "
        f"and the table held its welcome like a warm pair of hands.",
        question="What changed by the end of the quest?",
        cause="The children listened, noticed a useful clue, and chose an action suited to the problem.",
        result="The dining room became ready, safe, and welcoming for everyone.",
    )
    finish_check(world)
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    speech = [e for e in world.history if e.kind == "speech"]
    thoughts = [e for e in world.history if e.kind == "thought"]
    if len(speech) < 2 or not thoughts:
        raise StoryError("The story needs back-and-forth dialogue and inner monologue.")
    if {e.speaker for e in speech} != {"child", "helper"}:
        raise StoryError("Both characters must speak.")
    if not any("?" in e.text for e in speech):
        raise StoryError("Dialogue must include a question.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs causal grounded questions and answers.")
    if world.entities["child"].memes["courage"] < 1:
        raise StoryError("The child must grow more courageous.")


ASP_RULES = """
solves(follow_clues,missing_place).
solves(share_place,missing_place).
solves(share_place,spilled_soup).
solves(ask_together,spilled_soup).
solves(use_lantern,dark_room).
solves(ask_together,dark_room).
solves(follow_clues,lost_note).
solves(ask_together,lost_note).
#show solves/2.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        fact("problem", problem) for problem in PROBLEMS
    ) + "\n" + "\n".join(
        fact("solution", solution) for solution in SOLUTIONS
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    model = one_model(ASP_RULES)
    return {(solution, problem) for solution, problem in atoms(model, "solves")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--dish", choices=tuple(DISHES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        pair for pair in sorted(VALID)
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not combos:
        raise StoryError("No compatible problem and solution were selected.")
    problem, solution = rng.choice(combos)
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != child])
    params = StoryParams(
        child=child,
        helper=helper,
        problem=problem,
        solution=solution,
        mood=args.mood or rng.choice(MOODS),
        dish=args.dish or rng.choice(tuple(DISHES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if asp_combos() != {(s, p) for p, s in VALID}:
        raise StoryError("Python and ASP compatible pairs disagree.")
    count = 0
    for problem, solution in sorted(VALID):
        for mood in MOODS:
            for dish in DISHES:
                generate(StoryParams(problem=problem, solution=solution,
                                     mood=mood, dish=dish))
                count += 1
    print(f"OK: {count} story states; ASP parity verified.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(
            {"entities": sample.world.snapshot(),
             "history": [asdict(e) for e in sample.world.history]},
            indent=2,
        ))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            selected = [
                (problem, solution)
                for problem, solution in sorted(VALID)
                if args.problem is None or problem == args.problem
                if args.solution is None or solution == args.solution
            ]
            if not selected:
                raise StoryError("No compatible combinations match these options.")
            params_list = []
            for problem, solution in selected:
                fields = vars(args).copy()
                fields.update(problem=problem, solution=solution)
                params_list.append(resolve_params(argparse.Namespace(**fields), rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
