#!/usr/bin/env python3
"""
A heartwarming storyworld about Bonnie, a brave child who learns to speak
publicly about healing from a hernia, while a gentle rhyme gives courage to
others.
"""

from __future__ import annotations

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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, ...]] = field(default_factory=set)

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


@dataclass(frozen=True)
class Rhyme:
    line_one: str
    line_two: str
    message: str


@dataclass(frozen=True)
class Event:
    place: str
    audience: str
    obstacle: str
    fear: str
    helper_action: str
    public_action: str
    changed_image: str
    obstacle_answer: str
    lesson: str


@dataclass
class StoryParams:
    name: str = "Bonnie"
    audience: str = "the village"
    event: str = "garden_fair"
    trait: str = "brave"
    seed: Optional[int] = None


SETTING = Setting(
    place="the bright village hall",
    affordances={"welcome", "story", "rhyme", "healing", "public-ize"},
)

NAMES = ["Bonnie", "Mara", "Lina", "Poppy", "Nell"]
AUDIENCES = ["the village", "the school", "the neighborhood", "the garden club"]
TRAITS = ["brave", "kind", "patient", "hopeful"]

RHYMES = [
    Rhyme(
        "A tender scar can heal in time,",
        "A helping heart can make it shine.",
        "Healing is not something to hide, and caring friends can stand beside us.",
    ),
    Rhyme(
        "When wobbly knees begin to sway,",
        "A loving voice can light the way.",
        "Courage can grow when someone listens and stays close.",
    ),
    Rhyme(
        "Speak your truth, both soft and clear,",
        "Kind hearts will draw it safely near.",
        "Sharing a hard experience can help another person feel less alone.",
    ),
    Rhyme(
        "A little step, a little cheer,",
        "Can turn a far-off goal quite near.",
        "Small acts of courage become easier when a community offers support.",
    ),
]

EVENTS = [
    Event(
        place="the bright village hall",
        audience="the village",
        obstacle="the health circle's empty story chair made Bonnie's stomach flutter",
        fear="Bonnie worried that people would stare at the small scar left by her hernia operation",
        helper_action="her grandmother squeezed her hand and reminded her that the scar was proof that healing had happened",
        public_action="Bonnie stepped to the chair and told the village, in a clear little voice, how the doctor had helped her hernia heal",
        changed_image="Soon other children placed paper hearts around the story chair, and the empty seat looked like a welcome instead of a warning",
        obstacle_answer="The empty story chair made Bonnie nervous because she worried people would stare at her hernia scar.",
        lesson="A healed body deserves kindness, and an honest story can make room for someone else to feel safe.",
    ),
    Event(
        place="the school garden",
        audience="the school",
        obstacle="a microphone squeaked just as Bonnie was ready to speak",
        fear="Bonnie thought the noisy microphone meant her story should stay private",
        helper_action="her teacher switched it off and invited everyone to listen with their own ears",
        public_action="Bonnie told the children how resting and asking for help had helped her recover from a hernia",
        changed_image="The children hung bright ribbons on the garden fence, one for every helper who had made healing gentler",
        obstacle_answer="The microphone squeaked, and Bonnie thought the noise meant she should keep her story private.",
        lesson="A caring audience does not need a perfect performance; it needs a listening heart.",
    ),
    Event(
        place="the neighborhood porch",
        audience="the neighborhood",
        obstacle="the wind scattered Bonnie's speaking cards beneath the steps",
        fear="Bonnie feared she would forget the important words about her hernia",
        helper_action="her friend gathered the cards while Bonnie chose three simple ideas to remember",
        public_action="Bonnie spoke without the cards and shared that asking for medical help had been a strong choice",
        changed_image="The recovered cards became little flags along the porch rail, fluttering above a table of warm tea",
        obstacle_answer="The wind blew Bonnie's speaking cards away, so she had to remember her message without them.",
        lesson="Courage is not knowing every word; it is sharing what matters even when plans change.",
    ),
    Event(
        place="the moonlit library",
        audience="the garden club",
        obstacle="the reading lamp flickered and left the front page in shadow",
        fear="Bonnie wondered whether anyone could understand a story about hernia healing",
        helper_action="the librarian brought a lantern and sat beside her",
        public_action="Bonnie read her short account aloud and explained that recovery had included rest, checkups, and love",
        changed_image="The lantern glowed on the last page while listeners added their own hopeful notes to a basket",
        obstacle_answer="The reading lamp flickered, and Bonnie worried that people would not understand her story.",
        lesson="Clear truth, shared gently, can turn a dark corner into a place of understanding.",
    ),
]

MORALS = [
    "Kind truth can turn private worry into public hope.",
    "When people share courage with care, no one has to heal alone.",
    "A brave voice does not need to be loud; it only needs to tell the truth kindly.",
]

CAUSAL_RULES = r"""
ready_to_share :- healed(bonnie), support(bonnie), safe_place.
helpful_public_story :- ready_to_share, chooses_public_voice.
moral_value(hope) :- helpful_public_story.
rhyme_supports_courage :- rhyme_present, helpful_public_story.
resolved :- moral_value(hope), rhyme_supports_courage.
#show ready_to_share/0.
#show helpful_public_story/0.
#show moral_value/1.
#show rhyme_supports_courage/0.
#show resolved/0.
"""


def valid_combos() -> list[tuple[str, str, str]]:
    return [(name, audience, event.place) for name in NAMES for audience in AUDIENCES for event in EVENTS]


def choose_event(params: StoryParams) -> Event:
    for event in EVENTS:
        if event.place == params.event:
            return event
    if params.event == "garden_fair":
        return EVENTS[0]
    raise StoryError(f"Unknown event {params.event!r}; choose a registered story event.")


def build_world(params: StoryParams) -> World:
    if params.name not in NAMES:
        raise StoryError(f"Unknown name {params.name!r}; choose a name from the registry.")
    if params.audience not in AUDIENCES:
        raise StoryError(f"Unknown audience {params.audience!r}; choose an audience from the registry.")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait {params.trait!r}; choose a trait from the registry.")

    event = choose_event(params)
    world = World(SETTING)
    bonnie = world.add(Entity("bonnie", "child", params.name))
    helper = world.add(Entity("helper", "adult", "Grandma June"))
    hernia = world.add(Entity("hernia", "health_condition", "a hernia"))
    rhyme = world.add(Entity("rhyme", "story_tool", "a hopeful rhyme"))

    bonnie.meters.update(healing=1.0, confidence=0.2)
    bonnie.memes.update(worry=0.8, hope=0.3)
    helper.memes.update(care=1.0)
    hernia.meters["healed"] = 1.0

    world.facts.update(
        bonnie=bonnie,
        helper=helper,
        hernia=hernia,
        rhyme=rhyme,
        event=event,
        moral=random.choice(MORALS),
    )
    return world


def tell(params: StoryParams) -> World:
    stable_seed = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(f"{params.name}:{params.audience}:{params.event}:{params.trait}")
    )
    rng = random.Random(stable_seed)
    world = build_world(params)
    event: Event = world.facts["event"]
    rhyme: Rhyme = rng.choice(RHYMES)
    world.facts["rhyme_text"] = rhyme
    world.facts["moral"] = rng.choice(MORALS)

    bonnie: Entity = world.facts["bonnie"]
    helper: Entity = world.facts["helper"]

    world.say(
        f"At {event.place}, {bonnie.label}, a {params.trait} child, helped prepare a warm gathering for {event.audience}."
    )
    world.say(
        f"Bonnie had healed from {world.facts['hernia'].label}, and today the gathering would public-ize a message about kindness, recovery, and asking for help."
    )
    world.say(
        f"{helper.label} arranged a soft chair near the front. She said, \"You may tell only what feels safe, Bonnie.\""
    )
    world.say(
        f"Bonnie looked at her and answered, \"I want to tell it gently, because someone else may need hope.\""
    )
    world.para()

    world.say(f"But {event.obstacle}. {event.fear.capitalize()}.")
    world.say(f"Bonnie touched the place where her body had healed and whispered, \"Maybe my story is too small.\"")
    world.say(
        f"{helper.label} replied, \"A small story can open a big door. You can stop whenever you need.\""
    )
    world.para()

    bonnie.memes["worry"] = 0.2
    bonnie.memes["hope"] = 1.0
    bonnie.meters["confidence"] = 0.8
    world.fired.add(("support", "bonnie"))
    world.say(event.helper_action.capitalize() + ".")
    world.say(f"Then Bonnie remembered her rhyme:")
    world.say(f"\"{rhyme.line_one} {rhyme.line_two}\"")
    world.say(f"The rhyme helped Bonnie stand tall without pretending that speaking was easy.")
    world.say(event.public_action.capitalize() + ".")
    world.para()

    bonnie.meters["confidence"] = 1.0
    bonnie.memes["joy"] = 1.0
    world.fired.add(("public_voice", "bonnie"))
    world.say(
        f"The listeners grew quiet, then warm. They did not see Bonnie as a problem; they saw a child who had healed and was choosing to help."
    )
    world.say(event.changed_image + ".")
    world.say(
        f"Bonnie smiled at {helper.label}. \"I was scared,\" she said, \"but I am glad I shared.\""
    )
    world.say(
        f"{helper.label} hugged her and answered, \"That is the {world.facts['moral'].lower()}\""
    )
    world.say(
        f"Bonnie's rhyme stayed in the room like a little lantern: {rhyme.message}"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    event: Event = world.facts["event"]
    return [
        "Write a heartwarming child-facing story using the words public-ize, Bonnie, and hernia.",
        f"Tell a gentle story about Bonnie speaking to {event.audience} after healing from a hernia.",
        f"Include a short rhyme and a clear Moral Value while Bonnie faces this problem: {event.obstacle}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    event: Event = world.facts["event"]
    rhyme: Rhyme = world.facts["rhyme"]
    bonnie: Entity = world.facts["bonnie"]
    return [
        QAItem(
            "Who is the main character?",
            f"{bonnie.label} is the main character, a child who has healed from a hernia.",
        ),
        QAItem(
            "Why was Bonnie nervous?",
            event.obstacle_answer,
        ),
        QAItem(
            "What did Bonnie decide to do?",
            f"Bonnie decided to speak publicly and gently about healing from her hernia so her story could offer hope.",
        ),
        QAItem(
            "What rhyme gave Bonnie courage?",
            f"Bonnie remembered, \"{rhyme.line_one} {rhyme.line_two}\"",
        ),
        QAItem(
            "What Moral Value does the story teach?",
            f"The story teaches that {world.facts['moral'].lower()}",
        ),
        QAItem(
            "How did the audience respond?",
            "The audience listened warmly and added caring signs of support, showing Bonnie that her story had made the gathering safer and brighter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a hernia?",
            "A hernia is a health problem in which part of the body pushes through a weak spot; a doctor can explain the safest treatment.",
        ),
        QAItem(
            "What does public-ize mean here?",
            "Here, public-ize means to share an idea or story openly with a group in a thoughtful and safe way.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a pair or group of lines whose sounds match in a pleasing way.",
        ),
        QAItem(
            "What is a Moral Value?",
            "A Moral Value is a good principle, such as kindness, honesty, courage, or helping others.",
        ),
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
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} type={entity.type:14} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("healed", "bonnie"),
            asp.fact("support", "bonnie"),
            asp.fact("safe_place"),
            asp.fact("chooses_public_voice"),
            asp.fact("rhyme_present"),
        ]
    )


def asp_program(show: bool = True) -> str:
    suffix = "" if show else "\n".join(
        line for line in CAUSAL_RULES.splitlines() if not line.startswith("#show")
    )
    return f"{asp_facts()}\n{suffix}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {str(symbol) for symbol in model}
    expected = {
        "ready_to_share",
        "helpful_public_story",
        "moral_value(hope)",
        "rhyme_supports_courage",
        "resolved",
    }
    if expected.issubset(atoms):
        print("OK: ASP twin confirms the healing, sharing, rhyme, and moral-value chain.")
        return 0
    print("ASP mismatch:")
    print("  missing:", sorted(expected - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming Bonnie story about public-izing hope after a hernia."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--audience", choices=AUDIENCES)
    parser.add_argument("--event", choices=["garden_fair"] + [e.place for e in EVENTS])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
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
        audience=args.audience or rng.choice(AUDIENCES),
        event=args.event or rng.choice(["garden_fair"] + [e.place for e in EVENTS]),
        trait=args.trait or rng.choice(TRAITS),
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Bonnie", "the village", "garden_fair", "brave"),
    StoryParams("Bonnie", "the school", "the school garden", "kind"),
    StoryParams("Bonnie", "the neighborhood", "the neighborhood porch", "patient"),
    StoryParams("Bonnie", "the garden club", "the moonlit library", "hopeful"),
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
        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
