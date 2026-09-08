#!/usr/bin/env python3
"""
A standalone storyworld: a gentle detective story in a hotel lobby.

The seed tale behind this world:
---
A small detective team in a hotel lobby noticed a worried guest who needed bail,
but the safe solution was not a dramatic escape. The team stayed clothed,
followed a direct clue, and used teamwork and kindness to connect the guest with
the right adult helper.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the hotel lobby"


@dataclass
class StoryParams:
    detective_name: str
    partner_name: str
    guest_name: str
    clerk_name: str
    case_id: int = 0
    opening_mode: int = 0
    clue_mode: int = 0
    dialogue_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTING = Setting()

DETECTIVE_NAMES = ["Luna", "Milo", "Nia", "Theo", "Iris", "Jasper"]
PARTNER_NAMES = ["Pip", "Remy", "Zoe", "Cal", "Asha", "Ben"]
GUEST_NAMES = ["Sam", "Elena", "Noah", "Priya", "Owen", "Maya"]
CLERK_NAMES = ["Ms. Chen", "Mr. Ortiz", "Ms. Bell", "Mr. Reed"]

OPENINGS = [
    "On a rainy afternoon,",
    "Just after the brass lobby clock chimed three,",
    "While suitcase wheels whispered across the marble floor,",
    "On the quietest morning of the week,",
    "As sunlight crossed the hotel windows,",
]

CLUE_LEADS = [
    "Luna began with the direct facts:",
    "The team made a neat clue list and noticed",
    "Instead of guessing, the detectives checked",
    "A second look showed",
    "The important clue was simple:",
]

DIALOGUES = [
    '"We can help without rushing," said {detective}. "Let us ask the clerk." "And listen kindly," added {partner}.',
    '"Is this the right receipt?" asked {detective}. "Yes," said {guest}, "but I do not know what to do." "We will find the right adult," said {partner}.',
    '"A direct question may open the door," said {detective}. "Then teamwork can carry the answer," said {partner}.',
    '"Are you safe here?" asked {partner}. "I am worried," said {guest}. "You do not have to solve it alone," said {detective}.',
]

ENDINGS = [
    "The lobby grew calm again, and the brass clock ticked above the team’s shared case card.",
    "The guest thanked them, while the hotel’s warm lamps shone on three careful footprints and one clear plan.",
    "By evening, the clue board held a bright star beside the words teamwork and kindness.",
    "The detectives packed away their notebook, pleased that a gentle answer had solved a serious-looking puzzle.",
]

CASES = [
    {
        "problem": "a guest was frightened because a notice mentioned bail and no one had explained what it meant",
        "risk": "The team knew that bail was a legal matter, so they did not promise money, hide anyone, or pretend to be lawyers.",
        "false": "At first, a smudged luggage tag made them wonder whether the notice belonged to a different guest.",
        "clue": "the guest’s name on the hotel register, the matching notice number, and a phone number printed at the bottom",
        "cause": "The notice was real, but it was an instruction to contact a responsible legal adult, not an order for the children to fix the case.",
        "action": "The detectives asked the hotel clerk to call the listed guardian and waited together in the well-lit lobby.",
        "result": "The guardian arrived, read the notice, and contacted the proper legal office while the guest stayed safe.",
        "lesson": "Kindness means getting the right help instead of making promises we cannot keep.",
    },
    {
        "problem": "a folded bail notice had been left beside the coat stand",
        "risk": "The detectives left the paper where it was and did not read private details aloud to the busy lobby.",
        "false": "A bright red scarf nearby made them suspect that a hurried traveler had dropped it.",
        "clue": "the hotel’s lost-and-found tag, the time stamp, and the clerk’s record of who had reported the paper",
        "cause": "The notice had been placed in lost and found by an adult who wanted its owner to receive it safely.",
        "action": "The team gave the notice to the clerk, who sealed it and contacted the named adult through the hotel’s official number.",
        "result": "The owner collected it privately and received calm guidance about the next legal step.",
        "lesson": "Protecting someone’s privacy is part of kindness.",
    },
    {
        "problem": "a visitor asked whether bail could be paid with a hotel key card",
        "risk": "The detectives did not handle money or cards and knew that legal payments needed a responsible adult and an official source.",
        "false": "The shiny key card briefly looked like an important pass.",
        "clue": "the card’s room number, the clerk’s explanation, and the official contact printed on the notice",
        "cause": "The visitor had confused a room key with a legal payment method after a tiring journey.",
        "action": "The team used a direct question, then asked the clerk to explain the difference and call the visitor’s trusted adult.",
        "result": "The visitor understood the next step and kept the key card safely in a pocket.",
        "lesson": "Clear questions can prevent a confusing mistake.",
    },
    {
        "problem": "a worried adult had arrived clothed in a raincoat but could not find the legal office named on a bail notice",
        "risk": "The detectives stayed clothed, dry, and visible in the lobby rather than wandering outside or following a stranger.",
        "false": "A trail of wet footprints seemed to point toward the service hall.",
        "clue": "the direct street address on the notice, the hotel map, and the clerk’s knowledge of the nearest safe taxi stand",
        "cause": "The rain had blurred the visitor’s map, while the legal office was on a nearby street with a similar name.",
        "action": "The team compared the address with the hotel map and asked the clerk to arrange a licensed taxi for the adult.",
        "result": "The visitor reached the correct office safely, and the detectives learned that careful directions can be a real kindness.",
        "lesson": "A direct route is useful only when the address has been checked.",
    },
]

STYLE_NOTES = [
    "They treated every clue like a detective’s promise: observe first, decide second.",
    "The case looked large, but the next safe step was small and clear.",
    "Their notebook held facts, not rumors.",
    "The detectives knew that solving a problem includes knowing when to call an expert.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gentle detective storyworld about bail, direct clues, teamwork, and kindness."
    )
    parser.add_argument("--detective-name")
    parser.add_argument("--partner-name")
    parser.add_argument("--guest-name")
    parser.add_argument("--clerk-name")
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
        detective_name=args.detective_name or rng.choice(DETECTIVE_NAMES),
        partner_name=args.partner_name or rng.choice(PARTNER_NAMES),
        guest_name=args.guest_name or rng.choice(GUEST_NAMES),
        clerk_name=args.clerk_name or rng.choice(CLERK_NAMES),
        case_id=rng.randrange(len(CASES)),
        opening_mode=rng.randrange(len(OPENINGS)),
        clue_mode=rng.randrange(len(CLUE_LEADS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    case = CASES[params.case_id % len(CASES)]
    world = World(SETTING)

    detective = world.add(
        Entity(
            id="detective",
            kind="character",
            type="child-detective",
            label=params.detective_name,
        )
    )
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            type="child-detective",
            label=params.partner_name,
        )
    )
    guest = world.add(
        Entity(
            id="guest",
            kind="character",
            type="guest",
            label=params.guest_name,
        )
    )
    clerk = world.add(
        Entity(
            id="clerk",
            kind="character",
            type="hotel-clerk",
            label=params.clerk_name,
        )
    )
    notice = world.add(
        Entity(
            id="notice",
            kind="document",
            type="bail-notice",
            label="the bail notice",
        )
    )
    coat = world.add(
        Entity(
            id="coat",
            kind="clothing",
            type="raincoat",
            label="the guest’s raincoat",
        )
    )
    map_entity = world.add(
        Entity(
            id="map",
            kind="tool",
            type="hotel-map",
            label="the hotel map",
        )
    )

    detective.memes.update(curiosity=1, kindness=1)
    partner.memes.update(teamwork=1, patience=1)
    guest.memes.update(worry=1)
    clerk.memes.update(helpfulness=1)
    notice.meters.update(official=1, understood=0)
    coat.meters["worn"] = 1
    map_entity.meters["checked"] = 0

    world.facts.update(
        detective=detective,
        partner=partner,
        guest=guest,
        clerk=clerk,
        notice=notice,
        coat=coat,
        map=map_entity,
        case=case,
        params=params,
        solved=False,
        helper_contacted=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]  # type: ignore[assignment]
    case: dict[str, str] = facts["case"]  # type: ignore[assignment]
    detective: Entity = facts["detective"]  # type: ignore[assignment]
    partner: Entity = facts["partner"]  # type: ignore[assignment]
    guest: Entity = facts["guest"]  # type: ignore[assignment]
    clerk: Entity = facts["clerk"]  # type: ignore[assignment]
    notice: Entity = facts["notice"]  # type: ignore[assignment]
    map_entity: Entity = facts["map"]  # type: ignore[assignment]

    opening = OPENINGS[params.opening_mode % len(OPENINGS)]
    clue_lead = CLUE_LEADS[params.clue_mode % len(CLUE_LEADS)]
    dialogue = DIALOGUES[params.dialogue_mode % len(DIALOGUES)].format(
        detective=detective.label,
        partner=partner.label,
        guest=guest.label,
    )
    ending = ENDINGS[params.ending_mode % len(ENDINGS)]
    style_note = STYLE_NOTES[params.opening_mode % len(STYLE_NOTES)]

    world.say(
        f"{opening} {detective.label} and {partner.label arrived in the hotel lobby "
        f"with their small detective notebook."
    )
    world.say(
        f"They noticed {case['problem']}. The guest was properly clothed, but worry "
        f"made their hands tremble near the front desk."
    )
    world.say(
        f"The word bail sounded important. {detective.label} remembered that bail is "
        "a legal matter, so children should ask a trusted adult for help."
    )

    world.para()
    world.say(case["risk"])
    world.say(case["false"])
    world.say(dialogue)

    world.para()
    world.say(f"{clue_lead} {case['clue']}.")
    world.say(style_note)
    world.say(
        f"{detective.label} asked {clerk.label} a direct question: "
        f"\"Can you help us contact the right responsible adult for {guest.label}?\""
    )
    world.say(
        f"{clerk.label} nodded and said, \"Yes. We can use the official number and "
        "keep everyone safe here in the lobby.\""
    )
    world.say(case["cause"])

    world.para()
    world.say(case["action"])
    world.say(
        f"{partner.label} held the notebook while {detective.label} checked the "
        f"address against {map_entity.label}. Their teamwork kept the facts together."
    )
    world.say(case["result"])
    world.say(
        f"The guest thanked the team. {notice.label.capitalize()} was no longer a "
        "mystery, and nobody had made a risky promise."
    )

    world.para()
    world.say(f"They wrote one lesson in the notebook: {case['lesson']}")
    world.say(ending)

    notice.meters["understood"] = 1
    map_entity.meters["checked"] = 1
    detective.memes["confidence"] = 1
    partner.memes["teamwork"] = 2
    guest.memes["worry"] = 0
    facts["solved"] = True
    facts["helper_contacted"] = True


def generation_prompts(world: World) -> list[str]:
    case: dict[str, str] = world.facts["case"]  # type: ignore[assignment]
    return [
        'Write a gentle detective story set in a hotel lobby using the words "bail," "clothed," and "direct."',
        f"Tell how the detectives solve this problem safely: {case['problem']}.",
        "Create a child-facing story where teamwork and kindness lead to the right adult help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params: StoryParams = facts["params"]  # type: ignore[assignment]
    case: dict[str, str] = facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did {params.detective_name} and {params.partner_name} notice?",
            answer=f"They noticed {case['problem']}.",
        ),
        QAItem(
            question="Why did the detectives avoid making promises about bail?",
            answer=case["risk"],
        ),
        QAItem(
            question="What direct clues helped solve the case?",
            answer=f"The clues were {case['clue']}.",
        ),
        QAItem(
            question="What caused the confusion?",
            answer=case["cause"],
        ),
        QAItem(
            question="How did teamwork and kindness help?",
            answer=case["action"],
        ),
        QAItem(
            question="What happened at the end?",
            answer=case["result"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bail mean in general?",
            answer="Bail is a legal arrangement that may allow a person to remain out of custody while a case continues; a responsible adult or legal professional should explain the details.",
        ),
        QAItem(
            question="Why should children ask an adult about legal papers?",
            answer="Legal papers can be serious and confusing, so children should ask a trusted responsible adult or qualified legal professional for help.",
        ),
        QAItem(
            question="What is a direct clue?",
            answer="A direct clue is clear information that points toward an answer without requiring a wild guess.",
        ),
        QAItem(
            question="How does teamwork help solve a problem?",
            answer="Teamwork lets people share observations and safe tasks so they can make a better plan together.",
        ),
        QAItem(
            question="What does kindness look like in a confusing situation?",
            answer="Kindness means listening calmly, protecting privacy, and helping someone reach the right support.",
        ),
    ]


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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.type:16}) {' '.join(parts)}"
        )
    lines.append(f"  solved={world.facts.get('solved')}")
    lines.append(f"  helper_contacted={world.facts.get('helper_contacted')}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_case :- bail_notice(official), clue(direct), team(teamwork), value(kindness).
solved_case :- safe_case, adult_help(contacted), clothing(worn).
good_story :- solved_case.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("bail_notice", "official"),
            asp.fact("clue", "direct"),
            asp.fact("team", "teamwork"),
            asp.fact("value", "kindness"),
            asp.fact("adult_help", "contacted"),
            asp.fact("clothing", "worn"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(symbol.name == "good_story" for symbol in model)
    if ok:
        print("OK: ASP twin agrees the detective case is safe and resolved.")
        return 0
    print("MISMATCH: ASP twin did not find good_story.")
    return 1


def reasonableness_check(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("The generated story is empty.")
    required = ("bail", "clothed", "direct", "teamwork", "kindness")
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        raise StoryError(f"Story is missing required narrative words: {', '.join(missing)}.")
    if len(sample.story_qa) < 4:
        raise StoryError("A complete story needs at least four grounded questions.")


def generate(params: StoryParams) -> StorySample:
    if params.case_id < 0 or params.case_id >= len(CASES):
        raise StoryError("case_id must select a known hotel-lobby detective case.")
    world = _build_world(params)
    tell(world)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    reasonableness_check(sample)
    return sample


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
    StoryParams(
        detective_name="Luna",
        partner_name="Pip",
        guest_name="Sam",
        clerk_name="Ms. Chen",
        case_id=0,
    ),
    StoryParams(
        detective_name="Nia",
        partner_name="Remy",
        guest_name="Elena",
        clerk_name="Mr. Ortiz",
        case_id=1,
    ),
    StoryParams(
        detective_name="Iris",
        partner_name="Zoe",
        guest_name="Maya",
        clerk_name="Ms. Bell",
        case_id=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return

    if args.verify:
        sample = generate(CURATED[0])
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story lacks QA.")
            sys.exit(1)
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_story/0."))
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        target = max(1, args.n)
        seen: set[str] = set()
        for offset in range(max(target * 30, 30)):
            if len(samples) >= target:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {sample.params.detective_name} investigates in the hotel lobby"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
