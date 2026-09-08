#!/usr/bin/env python3
"""
A standalone folk-tale storyworld about a negligent email, a radish, and a
crowded market where careful problem solving restores trust.
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

_here = os.path.dirname(os.path.abspath(__file__))
_worlds = os.path.dirname(os.path.dirname(_here))
if not os.path.exists(os.path.join(_worlds, "results.py")):
    _worlds = os.path.dirname(_worlds)
sys.path.insert(0, _worlds)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class MarketWorld:
    place: str = "crowded market"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    elder_name: str
    vendor_name: str
    radish_kind: str
    market_feature: str
    scenario_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    action_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


CHILD_NAMES = ["Luna", "Mara", "Tavi", "Niko", "Suri", "Oren"]
ELDER_NAMES = ["Aunt Pella", "Grandmother Iva", "Uncle Rowan", "Old Mira"]
VENDOR_NAMES = ["Bram", "Nell", "Sefa", "Daro"]
RADISHES = ["red radish", "striped radish", "round radish", "long white radish"]
MARKET_FEATURES = ["bell tower", "blue awning", "fountain", "carved wooden gate"]

SCENARIOS = [
    {
        "problem": "a negligent message had sent the market's radishes to the wrong stall",
        "email": "Bring the radish basket to Stall Nine before the noon bell.",
        "mistake": "The email left out the word 'not' beside a hurried correction.",
        "clue": "a damp scrap of the email was caught beneath a basket wheel",
        "plan": "compare the message with the stall numbers and follow the wheel marks",
        "turn": "the basket had not been stolen; a porter had moved it away from a leaking roof",
        "result": "the radishes reached the right stall before the noon bell",
        "image": "the red radishes shone in a neat row beneath a dry red cloth",
        "lesson": "a careless message can cause trouble, but patient checking can mend what haste has tangled",
    },
    {
        "problem": "an email warned that one special radish would vanish when the market drum sounded",
        "email": "Keep the moon radish hidden until the drum is quiet.",
        "mistake": "A negligent sender had addressed the note to every stall instead of one trusted keeper.",
        "clue": "the message carried the same crooked seal as the basket tag",
        "plan": "read the full address, ask each stall keeper, and trace who had received the note",
        "turn": "the radish was safe inside the baker's cool flour room",
        "result": "the special radish was returned after everyone understood the message",
        "image": "the pale radish rested in a small bowl while the market drum slept",
        "lesson": "when a warning spreads too widely, clear questions can keep fear from leading the way",
    },
    {
        "problem": "a crowded market had received an email saying that the radish cart was dangerous",
        "email": "Do not push the radish cart through the east lane.",
        "mistake": "The negligent note omitted that the east lane was blocked only during rain.",
        "clue": "fresh mud covered the wheels, though the sky above the west lane was dry",
        "plan": "inspect both lanes, move the crowd behind the rope, and choose the safe path",
        "turn": "a loose roof tile had fallen in the east lane",
        "result": "the cart rolled safely through the west lane",
        "image": "the radish cart passed under the blue awning while shoppers made a calm passage",
        "lesson": "good problem solving joins evidence with care for everyone nearby",
    },
    {
        "problem": "the market bell rang, but no one knew whether an email had called for a radish delivery",
        "email": "When the bell rings, bring the radish basket to the fountain.",
        "mistake": "The negligent clerk had sent the message before checking which bell would ring.",
        "clue": "a tiny drawing showed the fountain, while the loud bell stood beside the gate",
        "plan": "match the drawing to the places and ask the bell keeper what had happened",
        "turn": "the fountain bell had rung softly under a stack of cloth",
        "result": "the basket reached the fountain and the mystery bell was found",
        "image": "a green radish leaf floated beside the fountain as the correct bell chimed",
        "lesson": "small details can guide a wise choice when a hurried message causes confusion",
    },
]

OPENINGS = [
    "In the crowded market, Luna noticed that {problem}.",
    "At the busiest hour of the market, {child} heard a troubling rumor: {problem}.",
    "The market was bright with cloth and voices when {child} learned that {problem}.",
    "Before the noon bell, {child} found a mystery among the baskets: {problem}.",
]

DIALOGUES = [
    '"Do not chase a rumor," {elder} said. "Show me the message and the clues."',
    '"A message may hurry, but we must not," {elder} told {child}.',
    '"Ask the people who saw the basket," {elder} said. "Truth leaves tracks."',
    '"We can solve this one step at a time," {elder} promised.',
]

ACTIONS = [
    "{child} read the email aloud, checked the stall numbers, and followed the clue",
    "{child} asked the nearby sellers what they had seen and marked each answer",
    "{child} held the crowd behind a rope, inspected the path, and compared the two lanes",
    "{child} matched every picture and word in the email to the places in the market",
]

ENDINGS = [
    "By sunset, {result}. {image}.",
    "At last, {result}, and {image}.",
    "The market breathed easily again because {result}. Then {image}.",
    "When the crowd went home, {result}. Under the evening light, {image}.",
]


def tell(params: StoryParams) -> MarketWorld:
    if not params.child_name or not params.elder_name:
        raise StoryError("A child and a guide are required.")
    if params.radish_kind not in RADISHES:
        raise StoryError("The radish choice is not in the market registry.")

    world = MarketWorld()
    child = world.add(Entity(
        params.child_name, "child", params.child_name, params.child_type,
        meters={"attention": 1.0, "courage": 0.5},
        memes={"worry": 0.0, "curiosity": 1.0, "relief": 0.0},
    ))
    elder = world.add(Entity(
        "elder", "helper", params.elder_name, "adult",
        meters={"patience": 1.0},
        memes={"trust": 1.0, "calm": 1.0},
    ))
    vendor = world.add(Entity(
        "vendor", "vendor", params.vendor_name, "adult",
        meters={"market_knowledge": 1.0},
        memes={"worry": 0.5},
    ))
    radish = world.add(Entity(
        "radish", "food", params.radish_kind, "radish",
        owner=params.vendor_name,
        meters={"freshness": 1.0, "safety": 1.0},
        memes={"importance": 1.0},
    ))
    email = world.add(Entity(
        "email", "message", "the email", "email",
        meters={"clarity": 0.3, "urgency": 1.0},
        memes={"trust": 0.2},
        props={"sender": "negligent clerk"},
    ))

    scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    world.facts.update(
        child=child, elder=elder, vendor=vendor, radish=radish, email=email,
        problem=scene["problem"], email_text=scene["email"],
        mistake=scene["mistake"], clue=scene["clue"], plan=scene["plan"],
        turn=scene["turn"], result=scene["result"], image=scene["image"],
        lesson=scene["lesson"], resolved=True, dialogue=True,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        child=params.child_name, problem=scene["problem"],
    ))
    world.say(f"Stalls leaned against one another, shoppers brushed sleeves, and the {params.radish_kind} basket seemed to be slipping farther into the crowd.")
    world.say(f"{params.child_name} thought, *If I guess wrongly, someone may lose the harvest. I must find what truly happened.*")
    child.memes["worry"] += 1.0
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        elder=params.elder_name, child=params.child_name,
    ))
    world.say(f'"Here is the email," {params.child_name} said. "It reads, \u201c{scene["email"]}\u201d."')
    world.say(f'"The message was negligent," said {params.elder_name}. "It did not clearly say what the sender meant. That is a problem, not proof of theft."')
    world.say(f'"I saw {params.vendor_name} near the basket," a nearby seller called.')
    world.say(f'"And I saw a porter move it," {params.vendor_name} replied. "Let us check before we blame anyone."')
    child.memes["curiosity"] += 1.0
    world.para()

    world.say(f"{params.child_name} found the first useful clue: {scene['clue']}.")
    world.say(f"{params.child_name} thought, *The clue must connect the message to the basket, or it is only a shiny distraction.*")
    world.say(f"Following the plan, {params.child_name} {scene['plan']}.")
    world.say(f"The search revealed the turn: {scene['turn']}.")
    child.meters["attention"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1.0
    email.meters["clarity"] += 0.7
    email.memes["trust"] += 0.5
    radish.meters["safety"] += 1.0

    world.say(f'"Now we know what the email failed to explain," {params.elder_name} said.')
    world.say(f'"I will write the correction clearly," {params.vendor_name} promised. "The {params.radish_kind} belongs at the proper stall."')
    world.say(f'"And next time," {params.child_name} said, "we will read the whole message before we run."')
    world.para()

    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(
        result=scene["result"], image=scene["image"],
    ))
    world.say(f"{params.child_name} learned that {scene['lesson']}")
    world.say(f"The crowded market grew calm, and the corrected email rested beside the {params.radish_kind} basket.")
    return world


def valid_combo(params: StoryParams) -> bool:
    return (
        bool(params.child_name and params.elder_name and params.vendor_name)
        and params.radish_kind in RADISHES
        and params.market_feature in MARKET_FEATURES
    )


ASP_RULES = r"""
message_negligent(email) :- clarity(email, low).
clue_found(child) :- reads_email(child), follows_track(child).
problem_solved(child) :- clue_found(child), checks_evidence(child), finds_safe_path(child).
trust_restored :- problem_solved(child), corrects_message(email).
#show message_negligent/1.
#show clue_found/1.
#show problem_solved/1.
#show trust_restored/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clarity", "email", "low"),
        asp.fact("reads_email", "child"),
        asp.fact("follows_track", "child"),
        asp.fact("checks_evidence", "child"),
        asp.fact("finds_safe_path", "child"),
        asp.fact("corrects_message", "email"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    needed = {"message_negligent", "clue_found", "problem_solved", "trust_restored"}
    if needed.issubset(names):
        return 0
    print("MISMATCH: ASP model did not preserve the story's causal chain.")
    return 1


def generation_prompts(world: MarketWorld) -> list[str]:
    f = world.facts
    return [
        f"Write a Folk Tale in a crowded market where a negligent email causes trouble with a {f['radish'].label}.",
        f"Use suspense, problem solving, and inner monologue as {f['child'].label} investigates: {f['problem']}.",
        "Include dialogue that changes what the characters know, then end with a concrete image proving the problem was solved.",
    ]


def story_qa(world: MarketWorld) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    elder = f["elder"].label
    radish = f["radish"].label
    return [
        QAItem(
            f"Why did the market problem begin?",
            f"The problem began because {f['mistake'].lower()} The negligent email was not clear enough.",
        ),
        QAItem(
            f"What clue did {child} find?",
            f"{child} found that {f['clue']}. This connected the message to the missing {radish}.",
        ),
        QAItem(
            f"How did {child} solve the mystery?",
            f"{child} {f['plan']}. The search showed that {f['turn']}.",
        ),
        QAItem(
            f"What did {elder} teach {child}?",
            f"{elder} taught {child} to check evidence before blaming anyone, because {f['lesson']}.",
        ),
        QAItem(
            "How did the story end?",
            f"{f['result'].capitalize()}. The ending image was that {f['image']}.",
        ),
    ]


def world_knowledge_qa(world: MarketWorld) -> list[QAItem]:
    return [
        QAItem("What is a crowded market?", "A crowded market is a busy place where many sellers and shoppers gather among stalls and goods."),
        QAItem("What is an email?", "An email is a written electronic message sent from one person or place to another."),
        QAItem("What is a radish?", "A radish is a crisp root vegetable that can be red, white, or striped and often has a peppery taste."),
        QAItem("Why should people check a message?", "People should check a message because missing or careless words can cause confusion and unsafe decisions."),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A crowded-market folk tale about a negligent email and a radish.")
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--vendor")
    ap.add_argument("--radish", choices=RADISHES)
    ap.add_argument("--market-feature", choices=MARKET_FEATURES)
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
    params = StoryParams(
        child_name=args.name or rng.choice(CHILD_NAMES),
        child_type="girl" if rng.random() < 0.5 else "boy",
        elder_name=args.elder or rng.choice(ELDER_NAMES),
        vendor_name=args.vendor or rng.choice(VENDOR_NAMES),
        radish_kind=args.radish or rng.choice(RADISHES),
        market_feature=args.market_feature or rng.choice(MARKET_FEATURES),
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        action_id=rng.randrange(len(ACTIONS)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=args.seed,
    )
    if not valid_combo(params):
        raise StoryError("The selected market characters or radish are invalid.")
    return params


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


def dump_trace(world: MarketWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:7}) "
            f"meters={entity.meters} memes={entity.memes} props={entity.props}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show trust_restored/0."))
        return
    if args.verify:
        try:
            result = asp_verify()
        except ImportError:
            print("ASP verification requires clingo.")
            result = 1
        sys.exit(result)
    if args.asp:
        try:
            import asp
            print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        except ImportError:
            print("ASP mode requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        fixed = [
            StoryParams("Luna", "girl", "Aunt Pella", "Bram", "red radish", "bell tower", 0, 0, 0, 0, 0),
            StoryParams("Mara", "girl", "Grandmother Iva", "Nell", "striped radish", "blue awning", 1, 1, 1, 1, 1),
            StoryParams("Tavi", "boy", "Uncle Rowan", "Sefa", "long white radish", "fountain", 2, 2, 2, 2, 2),
            StoryParams("Niko", "boy", "Old Mira", "Daro", "round radish", "carved wooden gate", 3, 3, 3, 3, 3),
        ]
        samples = [generate(p) for p in fixed]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + i)
            sample = generate(resolve_params(args, rng))
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} at the crowded market"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
