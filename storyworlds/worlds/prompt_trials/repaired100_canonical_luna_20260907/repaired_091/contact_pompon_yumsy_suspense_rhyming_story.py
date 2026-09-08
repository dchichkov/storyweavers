#!/usr/bin/env python3
"""
Story world: a rhyming suspense tale about contact, a pompon, and Yumsy.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    yumsy: str = "Yumsy"
    setting: str = "the moonlit playroom"
    seed: Optional[int] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENARIOS = (
    {
        "name": "the whispering pompon",
        "clue": "a silver pompon trembled beside the closed toy chest",
        "threat": "a soft scratching sound came from inside the chest",
        "first_guess": "Luna guessed that a tiny ghost was dancing in the dark",
        "cause": "a loose wind-up ribbon inside the chest was brushing the wood",
        "action": "Milo held the lantern while Luna asked Yumsy to stay behind the bright rug",
        "contact": "Luna touched the chest only after the grown-up latch keeper gave permission",
        "ending": "the pompon rested in Yumsy's paws as the chest kept a quiet beat",
        "lesson": "contact is safest when we ask first and keep a calm distance",
    },
    {
        "name": "the vanishing pompon",
        "clue": "a red pompon left a dotted trail toward the curtain",
        "threat": "something unseen tugged the curtain whenever the bell rang",
        "first_guess": "Yumsy feared that a shadow creature had stolen the pompon",
        "cause": "a string tied to the curtain had caught the pompon's loose thread",
        "action": "Luna called for help, and Milo stopped the bell before anyone reached behind the curtain",
        "contact": "the children made contact with the string using a long cardboard ruler",
        "ending": "the pompon bobbed on its ribbon while Yumsy chirped a relieved little tune",
        "lesson": "careful contact can solve a mystery without putting curious hands in a hidden place",
    },
    {
        "name": "the midnight pompon",
        "clue": "the blue pompon glowed whenever Yumsy came near the window",
        "threat": "a tapping noise answered from the other side of the glass",
        "first_guess": "Milo wondered if someone outside was trying to contact Yumsy",
        "cause": "moonlight reflected from a bicycle reflector sewn inside the pompon",
        "action": "Luna closed the curtain, checked the locked window, and watched from the center of the room",
        "contact": "the only contact they made was a spoken greeting after the room was secure",
        "ending": "the pompon shone softly on the shelf, and Yumsy slept through the silver night",
        "lesson": "suspense feels smaller when friends check safety before making contact",
    },
    {
        "name": "the pompon under the floor",
        "clue": "a yellow pompon rolled beneath the loose floorboard and stopped",
        "threat": "a tiny knock answered whenever Yumsy nudged the board",
        "first_guess": "Luna imagined a beetle asking for contact from below",
        "cause": "the pompon had landed beside an old marble that moved with the house",
        "action": "Milo marked the spot while Luna called the caretaker instead of lifting the board",
        "contact": "the caretaker used a hook tool to make gentle contact with the pompon",
        "ending": "the pompon returned to Yumsy, and the floorboard no longer knocked",
        "lesson": "we can care about a lost thing without unsafe contact with a hidden space",
    ),
    {
        "name": "the stormy pompon",
        "clue": "a green pompon swung wildly although the playroom windows were shut",
        "threat": "Yumsy heard a low hum behind the bookcase",
        "first_guess": "Milo thought the storm had found a secret way indoors",
        "cause": "a small fan behind the bookcase had switched on during a power reset",
        "action": "Luna turned away from the bookcase, called the caretaker, and waited for the power to be checked",
        "contact": "the caretaker made contact with the switch only after unplugging the fan",
        "ending": "the pompon hung still while Yumsy watched raindrops race the glass",
        "lesson": "safe contact begins with stopping power and asking a trusted helper",
    ),
    {
        "name": "the golden pompon code",
        "clue": "a gold pompon blinked in a pattern beside the reading nook",
        "threat": "three knocks followed every blink from behind the curtain",
        "first_guess": "Yumsy wondered whether a hidden friend was trying to contact them",
        "cause": "a toy beacon was reflecting its light from the pompon's shiny thread",
        "action": "Milo counted the pattern while Luna checked the room with the caretaker",
        "contact": "they made contact with the hidden toy by pressing its large button with a book",
        "ending": "the beacon sang a bright tune, and the pompon gleamed above Yumsy's nest",
        "lesson": "a strange signal deserves a patient check before a risky response",
    ),
)

RHYME_OPENINGS = (
    "When moonbeams peeked and shadows crept, the little playroom softly slept.",
    "Beneath the stars, beside the chair, a secret shiver stirred the air.",
    "The clock went tick, the night went hush, then came a tremble, tap, and rush.",
    "In silver light, with curtains wide, three careful friends stood side by side.",
    "The room was still, the rug was bright, yet something moved beyond the light.",
)

RHYME_TRANSITIONS = (
    "They did not dash, they did not shout; they watched the clues and figured out.",
    "They counted beats and checked the floor, then asked a helper at the door.",
    "With steady feet and voices low, they kept a safe and careful glow.",
    "One looked near and one looked far; together they made a clue-map star.",
    "They shared each thought, then tested none until a trusted helper came.",
)

RHYME_LINES = (
    '"Do we make contact?" Luna said. "Not yet," said Milo. "Ask instead."',
    '"Stay by the rug," said Luna bright. "We will use care and keep good light."',
    '"A clue is not a call to race," said Milo. "Safety comes in first place."',
    '"Let us observe before we try," said Luna. "Then we will know just why."',
)

QA_PATTERNS = (
    (
        "What made {name} suspenseful?",
        "What clue helped the friends?",
        "What caused the strange event?",
        "How did the friends handle contact?",
        "How did Yumsy change?",
        "What lesson did they learn?",
    ),
    (
        "Why were Luna and Milo cautious about {name}?",
        "What did they notice first?",
        "What was really happening?",
        "Who helped make the situation safe?",
        "What happened to Yumsy at the end?",
        "What did the rhyme teach?",
    ),
)


def validate_params(params: StoryParams) -> None:
    for field_name in ("hero", "friend", "yumsy", "setting"):
        value = getattr(params, field_name)
        if not value or not value.strip():
            raise StoryError(f"{field_name} must not be empty.")
    if len({params.hero.lower(), params.friend.lower(), params.yumsy.lower()}) != 3:
        raise StoryError("hero, friend, and yumsy must have different names.")
    if params.seed is not None and params.seed < 0:
        raise StoryError("seed must be non-negative.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(RHYME_OPENINGS)
    transition = rng.choice(RHYME_TRANSITIONS)
    dialogue = rng.choice(RHYME_LINES)

    world = World(params.setting)
    hero = world.add(
        Entity(
            params.hero,
            kind="character",
            type="girl",
            label=params.hero,
            memes={"curiosity": 1, "care": 1, "bravery": 0},
        )
    )
    friend = world.add(
        Entity(
            params.friend,
            kind="character",
            type="boy",
            label=params.friend,
            memes={"friendship": 1, "care": 1, "bravery": 1},
        )
    )
    yumsy = world.add(
        Entity(
            params.yumsy,
            kind="animal",
            type="small_companion",
            label=params.yumsy,
            meters={"safe": 1, "calm": 0},
            memes={"trust": 1, "worry": 1},
        )
    )
    pompon = world.add(
        Entity(
            "pompon",
            kind="object",
            type="soft_toy",
            label="the pompon",
            meters={"visible": 1, "still": 0},
            memes={"comfort": 1},
        )
    )

    world.facts = {
        "scenario": scenario["name"],
        "clue": scenario["clue"],
        "threat": scenario["threat"],
        "first_guess": scenario["first_guess"],
        "cause": scenario["cause"],
        "action": scenario["action"],
        "contact": scenario["contact"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
        "opening": opening,
        "transition": transition,
        "dialogue": dialogue,
        "hero": hero.label,
        "friend": friend.label,
        "yumsy": yumsy.label,
        "pompon": pompon.label,
        "qa_style": str(rng.randrange(len(QA_PATTERNS))),
    }

    world.say(opening)
    world.say(
        f"In {world.setting}, {hero.label}, {friend.label}, and {yumsy.label} stayed close to the warm, bright rug. "
        f"They could see the pompon, but they would not touch anything hidden without a trusted helper."
    )
    world.say(f"Then suspense stirred: {scenario['threat']}.")
    world.para()

    world.say(f"{scenario['first_guess']}, but that was only a guess.")
    world.say(f"Here was the clue: {scenario['clue']}.")
    world.say(transition)
    world.say(dialogue)
    world.say(f"{hero.label} and {friend.label} kept {yumsy.label} beside them, where the light was clear.")
    world.para()

    world.say(f"The cause came into view: {scenario['cause']}.")
    world.say(f"To solve the puzzle, {scenario['action']}.")
    world.say(f"About contact, they remembered this: {scenario['contact']}.")
    yumsy.meters["calm"] = 1
    yumsy.memes["worry"] = 0
    hero.memes["bravery"] = 1
    pompon.meters["still"] = 1

    world.say(
        f'"We were scared, but we stayed wise," said {friend.label}. '
        f'"And we stayed together," answered {hero.label}.'
    )
    world.para()
    world.say(f"At last, {scenario['ending']}.")
    world.say(f"They learned that {scenario['lesson']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly suspense story in rhyming style about {f['hero']}, {f['friend']}, and {f['yumsy']} in {world.setting}.",
        f"Include contact, a pompon, and this clue: {f['clue']}.",
        f"End with this changed image: {f['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pattern = QA_PATTERNS[int(f["qa_style"])]
    questions = [
        item.format(name=f["scenario"], hero=f["hero"], friend=f["friend"], yumsy=f["yumsy"])
        for item in pattern
    ]
    return [
        QAItem(questions[0], f"The story was suspenseful because {f['threat']}."),
        QAItem(questions[1], f"The friends noticed that {f['clue']}."),
        QAItem(questions[2], f"They discovered that {f['cause']}."),
        QAItem(questions[3], f"They handled contact carefully: {f['contact']}."),
        QAItem(
            questions[4],
            f"{f['yumsy']} changed from worried to calm because the friends kept the situation safe and explained what was happening.",
        ),
        QAItem(questions[5], f"They learned that {f['lesson']}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is contact?",
            "Contact is touching or communicating with someone or something. Safe contact means checking permission and conditions first.",
        ),
        QAItem(
            "What is a pompon?",
            "A pompon is a soft ball or tuft made from yarn, thread, or fabric.",
        ),
        QAItem(
            "What does suspense mean?",
            "Suspense is a feeling of waiting and wondering what may happen next.",
        ),
        QAItem(
            "Who is Yumsy in this story?",
            "Yumsy is the small companion who stays near Luna and Milo while they solve the pompon mystery safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append("events:")
    lines.extend(f"- {event}" for event in world.events)
    return "\n".join(lines)


ASP_RULES = r"""
character(luna).
character(milo).
companion(yumsy).
object(pompon).
soft(pompon).
observed(pompon).
safe(yumsy).
calm(yumsy).
careful_contact.
solved(pompon) :- observed(pompon), careful_contact.
reassured(yumsy) :- calm(yumsy), solved(pompon).
#show solved/1.
#show reassured/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("character", "luna"),
            asp.fact("character", "milo"),
            asp.fact("companion", "yumsy"),
            asp.fact("object", "pompon"),
            asp.fact("soft", "pompon"),
            asp.fact("observed", "pompon"),
            asp.fact("safe", "yumsy"),
            asp.fact("calm", "yumsy"),
            asp.fact("careful_contact"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    program = asp_program("#show solved/1.\n#show reassured/1.")
    model = asp.one_model(program)
    names = {(symbol.name, len(symbol.arguments)) for symbol in model}
    expected = {("solved", 1), ("reassured", 1)}
    if expected <= names:
        print("OK: ASP rules produce solved pompon and reassured Yumsy.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected suspense resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming suspense story about contact, a pompon, and Yumsy."
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
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--yumsy", default=None)
    parser.add_argument("--setting", default="the moonlit playroom")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Pia", "Nora", "Mina"])
    friend = args.friend or rng.choice(["Milo", "Tavi", "Ollie", "Remy"])
    yumsy = args.yumsy or rng.choice(["Yumsy", "Bibi", "Pip", "Nunu"])
    if len({hero.lower(), friend.lower(), yumsy.lower()}) != 3:
        raise StoryError("chosen names must be different.")
    return StoryParams(
        hero=hero,
        friend=friend,
        yumsy=yumsy,
        setting=args.setting,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print()
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
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show solved/1.\n#show reassured/1."))
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        for index, scenario in enumerate(SCENARIOS):
            params = StoryParams(
                hero=args.hero or "Luna",
                friend=args.friend or "Milo",
                yumsy=args.yumsy or "Yumsy",
                setting=args.setting,
                seed=base_seed + index,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
    else:
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
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
