#!/usr/bin/env python3
"""
A standalone storyworld: a gentle metro whodunit about a nurse, careful clues,
and the moral value of helping without blaming.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "Maple Street metro station"


@dataclass
class StoryParams:
    name: str
    nurse_name: str
    companion_name: str
    case_id: int = 0
    opening_mode: int = 0
    clue_mode: int = 0
    dialogue_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
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


SETTING = Setting()

NAMES = ["Luna", "Milo", "Sana", "Theo", "Ivy", "Noah", "Cleo", "Jae"]
NURSES = ["Nurse Ada", "Nurse Priya", "Nurse Rosa", "Nurse Eli"]
COMPANIONS = ["Grandma Jo", "Uncle Ben", "Aunt Mei", "Mr. Omar"]

CASES = [
    {
        "object": "the station's bright blue first-aid satchel",
        "mystery": "who had moved it from the bench before the evening metro arrived",
        "risk": "The satchel held medical supplies, so everyone kept calm and asked a station worker to check the platform.",
        "suspect": "A hurried passenger had been seen near the bench, and some riders quickly blamed that stranger.",
        "clue": "a silver wheelchair brake mark, a smear of orange chalk, and a note saying 'lift gate'",
        "cause": "A wheelchair user had moved the satchel to the lift gate so the crowded bench would stay clear, then an announcement sent them away before they could explain.",
        "action": "Luna showed the clues to the station worker, who checked the lift gate and called the nurse instead of accusing anyone.",
        "result": "The satchel was found untouched beside the lift, and the nurse returned it to its marked shelf.",
        "lesson": "A missing explanation is not proof that someone did wrong.",
        "image": "When the next metro sighed into the station, the blue satchel rested under its red safety label while every rider had room to pass.",
    },
    {
        "object": "a small red envelope taped beneath the metro timetable",
        "mystery": "who had left a private-looking message where children could see it",
        "risk": "The envelope might contain sensitive information, so nobody opened it or read over another person's shoulder.",
        "suspect": "A teenager with a red backpack had just left, and whispers began to follow him down the stairs.",
        "clue": "the envelope had a clinic logo, a return address, and a printed instruction to give it to the nurse",
        "cause": "A clinic courier had placed the envelope under the timetable while searching for the nurse, but the tape loosened and hid the message.",
        "action": "Luna asked the station clerk to contact the clinic and handed the sealed envelope to Nurse Ada.",
        "result": "The message reached its intended nurse without exposing anyone's private words.",
        "lesson": "Respecting privacy is part of being helpful.",
        "image": "The timetable fluttered above the sealed envelope's new safe pocket as the metro lights streamed past.",
    },
    {
        "object": "a blinking yellow help button beside the quiet platform lift",
        "mystery": "why the lift alarm had sounded when no one seemed to need help",
        "risk": "The lift might stop unexpectedly, so riders stayed behind the line and used the stairs only with an adult's help.",
        "suspect": "A muddy boot print made people suspect a careless visitor had pressed the button as a joke.",
        "clue": "two short alarm flashes, a dropped mitten, and a lift log showing a delayed door",
        "cause": "A child had been trapped briefly when the lift door sensed the mitten, and the alarm had worked exactly as it should.",
        "action": "Luna told the station worker about the mitten and waited while the worker tested the lift and spoke with the child's family.",
        "result": "The lift was checked, the mitten was returned, and the alarm was left ready for a real emergency.",
        "lesson": "Before calling something mischief, look for the person who may need care.",
        "image": "The yellow button blinked steadily beside a clean lift door, like a tiny promise that help could be called.",
    },
    {
        "object": "a paper crown lying beside the metro map",
        "mystery": "why the crown had appeared after the children's art cart disappeared",
        "risk": "The map case was glass, so nobody pressed against it or climbed over the platform rail to search.",
        "suspect": "A performer with a purple coat had been seen nearby, and riders guessed the crown was a trick.",
        "clue": "blue paint on the crown, three child-sized fingerprints, and a smudge leading toward the nurse's waiting area",
        "cause": "A child had carried the crown from an art activity while looking for a parent, then left it beside the map when the nurse helped them.",
        "action": "Luna brought the crown to Nurse Priya, who asked the clerk to make a gentle station announcement.",
        "result": "The child and parent were reunited, and the crown returned to the art cart.",
        "lesson": "Careful questions can find a worried person faster than a hurried accusation.",
        "image": "The paper crown went back on the art cart, where its blue points shone above a drawing of the metro.",
    },
    {
        "object": "a warm lunch bag tucked behind a metro seat",
        "mystery": "who had left food where the closing train crew might throw it away",
        "risk": "The bag could belong to someone with allergies or medicine inside, so nobody opened it.",
        "suspect": "A street musician had been eating nearby, and a few riders blamed him without evidence.",
        "clue": "a name tag reading 'Nurse Rosa,' a clinic sticker, and a route card for the late train",
        "cause": "Nurse Rosa had set the bag down while helping a dizzy passenger and then boarded a different train to get assistance.",
        "action": "Luna gave the sealed bag to the station desk and described where it had been found.",
        "result": "The desk reached Nurse Rosa, who collected her lunch after finishing the passenger's care.",
        "lesson": "The kind thing is often to protect what belongs to someone until it can be returned.",
        "image": "At the station desk, the lunch bag sat beneath a note marked RETURNED, while the last train carried its owner home.",
    },
    {
        "object": "a trail of white paper stars leading across the metro concourse",
        "mystery": "who had scattered the stars and why they stopped at the locked service door",
        "risk": "The service door was for workers only, so the children stayed on the public side and did not follow the trail inside.",
        "suspect": "A rushed cleaner had been carrying a box of decorations, so riders wondered if the trail was careless littering.",
        "clue": "a hospital wristband, a child-sized mitten, and stars folded from appointment forms",
        "cause": "A nervous child had folded the stars while waiting for a nurse and dropped them while following a parent toward the service elevator.",
        "action": "Luna told the nurse and clerk, who checked the waiting area and reunited the child with the parent.",
        "result": "The stars were gathered without blame, and the child received a fresh paper to fold.",
        "lesson": "Kindness looks for a frightened person before it looks for fault.",
        "image": "One paper star remained on the noticeboard, pointing toward the warm waiting room.",
    },
]

OPENINGS = [
    "Just before the evening rush,",
    "On a rainy afternoon,",
    "As the first metro hummed underground,",
    "During the quiet part of the morning,",
    "When the station clock chimed six,",
    "While commuters hurried beneath the city,",
]

CLUE_LEADS = [
    "Luna made a careful list of what they knew:",
    "Instead of guessing, they examined the scene and found",
    "Nurse {nurse} said, \"Facts first.\" Together they noticed",
    "The mystery grew smaller when they compared",
    "Luna crouched beside the safe line and pointed out",
    "They checked the ordinary details: ",
]

DIALOGUES = [
    ('"{name}, do you think the stranger took it?" asked {companion}.', '"I do not know yet," said {name}. "Let us find facts before we choose a culprit."'),
    ('"Should we open it?" asked {companion}.', '"No," said {nurse}. "Helping also means respecting what is not ours."'),
    ('"The clue looks suspicious," whispered {companion}.', '"A clue is a question, not an answer," said {name}. "We should ask kindly."'),
    ('"What can we do?" asked {name}.', '"Tell the right adult and keep everyone safe," said {nurse}. "That is brave enough."'),
]

ENDINGS = [
    "Luna understood that a fair guess needs evidence, and a good neighbor leaves room for a kinder explanation.",
    "The station felt less mysterious now, not because every person was perfect, but because everyone had chosen care over blame.",
    "Luna wrote the case in a notebook: Notice. Ask. Help. Do not accuse without proof.",
    "The whodunit ended with a return, an apology for the rushed rumor, and a safer station for everyone.",
]

NURSE_EXPLANATION = (
    "A nurse is a trained health-care professional who cares for people, observes their needs, "
    "and helps provide safe treatment."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metro nurse whodunit storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--nurse-name")
    parser.add_argument("--companion-name")
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        nurse_name=args.nurse_name or rng.choice(NURSES),
        companion_name=args.companion_name or rng.choice(COMPANIONS),
        case_id=rng.randrange(len(CASES)),
        opening_mode=rng.randrange(len(OPENINGS)),
        clue_mode=rng.randrange(len(CLUE_LEADS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    case = CASES[params.case_id % len(CASES)]
    world = World(SETTING)
    hero = world.add(Entity("hero", "child", params.name))
    nurse = world.add(Entity("nurse", "nurse", params.nurse_name))
    companion = world.add(Entity("companion", "companion", params.companion_name))
    object_found = world.add(Entity("object", "case-object", case["object"]))
    clue = world.add(Entity("clue", "evidence", case["clue"]))
    metro = world.add(Entity("metro", "vehicle", "the evening metro"))

    hero.memes.update(curiosity=1, fairness=1)
    nurse.memes.update(calm=1, care=1)
    companion.memes.update(worry=1)
    object_found.meters.update(found=1, returned=0)
    clue.meters.update(observed=1)
    metro.meters.update(waiting=1)

    world.facts.update(
        hero=hero,
        nurse=nurse,
        companion=companion,
        object=object_found,
        clue=clue,
        metro=metro,
        case=case,
        solved=False,
        params=params,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]
    case = facts["case"]
    hero = facts["hero"]
    nurse = facts["nurse"]
    companion = facts["companion"]

    world.say(
        f"{OPENINGS[params.opening_mode % len(OPENINGS)]} {hero.label} and "
        f"{companion.label} waited at {world.setting.place}."
    )
    world.say(f"They found {case['object']}.")
    world.say(f"The question was {case['mystery']}.")

    world.para()
    world.say(case["risk"])
    world.say(case["suspect"])

    first, second = DIALOGUES[params.dialogue_mode % len(DIALOGUES)]
    world.say(first.format(name=hero.label, companion=companion.label, nurse=nurse.label))
    world.say(second.format(name=hero.label, companion=companion.label, nurse=nurse.label))
    world.say(f"{nurse.label} was a nurse, trained to care for people and notice when someone needed help.")

    world.para()
    lead = CLUE_LEADS[params.clue_mode % len(CLUE_LEADS)].format(nurse=nurse.label)
    world.say(f"{lead} {case['clue']}.")
    world.say(f"{nurse.label} explained, \"{NURSE_EXPLANATION}\"")
    world.say(case["cause"])
    world.say(f"{hero.label} compared the explanation with every clue before deciding it made sense.")

    world.para()
    action = case["action"]
    world.say(action)
    world.say(case["result"])
    world.say(f"{hero.label} and {companion.label} agreed that {case['lesson'].lower()}")

    world.para()
    world.say(ENDINGS[params.ending_mode % len(ENDINGS)])
    world.say(case["image"])

    facts["solved"] = True
    facts["object"].meters["returned"] = 1
    hero.memes["wisdom"] = 1
    nurse.memes["trust"] = 1


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        "Write a child-friendly metro whodunit featuring a nurse and a suspenseful but gentle mystery.",
        f"Tell how {world.facts['hero'].label} solves who moved {case['object']} without blaming anyone unfairly.",
        "Include evidence, a brief dialogue exchange, a moral value about kindness, and an ending image.",
    ]


def story_questions(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    hero = facts["hero"]
    nurse = facts["nurse"]
    return [
        QAItem(
            question=f"What did {hero.label} find at the metro station?",
            answer=f"{hero.label} found {case['object']}.",
        ),
        QAItem(
            question="Who did people wrongly suspect?",
            answer=case["suspect"],
        ),
        QAItem(
            question=f"What clues helped {hero.label} and {nurse.label} solve the mystery?",
            answer=f"The clues were {case['clue']}.",
        ),
        QAItem(
            question="What really happened?",
            answer=case["cause"],
        ),
        QAItem(
            question="How did the characters respond?",
            answer=case["action"],
        ),
        QAItem(
            question="What moral value does the story teach?",
            answer=case["lesson"],
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a nurse do?",
            answer=NURSE_EXPLANATION,
        ),
        QAItem(
            question="Why should people avoid blaming someone without proof?",
            answer="People should avoid blaming without proof because a rushed guess can hurt an innocent person and hide the real problem.",
        ),
        QAItem(
            question="What is evidence?",
            answer="Evidence is information or an observation that helps people decide what really happened.",
        ),
        QAItem(
            question="Why are metro platform safety lines important?",
            answer="They give riders a clear safe boundary away from the track and moving trains.",
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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  solved={world.facts['solved']}")
    return "\n".join(lines)


ASP_RULES = r"""
observed(clue).
safe_method(ask_before_accusing).
moral_value(kindness).
resolved(case) :- observed(clue), safe_method(ask_before_accusing), moral_value(kindness).
good_story :- resolved(case), helper(nurse).
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("helper", "nurse"),
            asp.fact("observed", "clue"),
            asp.fact("safe_method", "ask_before_accusing"),
            asp.fact("moral_value", "kindness"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    good = any(symbol.name == "good_story" for symbol in model)
    if not good:
        print("MISMATCH: ASP twin rejected the metro nurse story.")
        return 1
    for params in [
        StoryParams("Luna", "Nurse Ada", "Grandma Jo"),
        StoryParams("Milo", "Nurse Priya", "Uncle Ben", case_id=3),
    ]:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated story verification failed.")
            return 1
    print("OK: ASP twin and generated metro stories agree.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.nurse_name.strip():
        raise StoryError("nurse_name must not be empty")
    if not 0 <= params.case_id < len(CASES):
        raise StoryError("case_id is outside the available metro cases")
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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


CURATED = [
    StoryParams("Luna", "Nurse Ada", "Grandma Jo", case_id=0),
    StoryParams("Milo", "Nurse Priya", "Uncle Ben", case_id=2),
    StoryParams("Sana", "Nurse Rosa", "Aunt Mei", case_id=5),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("good_story" if any(s.name == "good_story" for s in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        target = max(1, args.n)
        seen: set[str] = set()
        for offset in range(max(20, target * 20)):
            if len(samples) >= target:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        if args.all:
            header = f"### {sample.params.name} and the metro mystery"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
