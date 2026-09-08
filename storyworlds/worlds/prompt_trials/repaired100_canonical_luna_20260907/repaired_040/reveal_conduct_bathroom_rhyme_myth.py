#!/usr/bin/env python3
"""
reveal_conduct_bathroom_rhyme_myth.py
=====================================

A small mythic storyworld set in a bathroom, where a shy moon-dragon must
reveal the truth about a vanished rhyme and learn that good conduct means
choosing honesty and care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "character"
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
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    line: str
    pair: str
    meaning: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "bathroom": Setting(
        id="bathroom",
        place="the old bathroom",
        affords={"reveal", "conduct", "rhyme"},
    )
}

RHYMES = {
    "moon_tune": Rhyme(
        id="moon_tune",
        line="When truth is shown, the clean tiles shine; kind hands make every heart align.",
        pair="shine/align",
        meaning="honesty and kindness belong together",
    ),
    "mirror_clear": Rhyme(
        id="mirror_clear",
        line="A careful deed makes mirrors bright; a truthful word can guide the night.",
        pair="bright/night",
        meaning="good conduct helps everyone see clearly",
    ),
    "water_song": Rhyme(
        id="water_song",
        line="Let water run and worries go; tell what you know, then help it grow.",
        pair="go/know",
        meaning="a truthful confession can begin repair",
    ),
}

SCENARIOS = [
    {
        "id": "silver_drip",
        "premise": "At midnight, a silver drop appeared beneath the bathroom mirror.",
        "tension": "The moon-dragon had hidden the missing rhyme tablet after cracking it with a careless tail-swish.",
        "clue": "a line of pearly scales led from the tablet shelf to the dragon's bath mat",
        "reveal": "admitted that the crack came from her own tail",
        "repair": "gathered the pieces, washed the dusty shelf, and spoke the rhyme aloud",
        "ending": "the repaired tablet gleamed beside the basin while moonlight made a bright path across the tiles",
        "lesson": "good conduct means telling the truth and helping mend what your actions have harmed",
    },
    {
        "id": "fogged_mirror",
        "premise": "A cloud of warm steam covered every mirror in the bathroom.",
        "tension": "Someone had rubbed away the final words of the guardian rhyme, and the young dragon feared being blamed.",
        "clue": "the missing words were written in tiny claw marks on the dragon's damp towel",
        "reveal": "told the truth about practicing the rhyme on the mirror",
        "repair": "cleaned the glass with the caretaker and rewrote the line in washable blue chalk",
        "ending": "the mirror cleared to show two smiling faces and a neat blue rhyme beneath them",
        "lesson": "honest conduct can turn a frightening secret into a shared solution",
    },
    {
        "id": "runaway_bubbles",
        "premise": "Soap bubbles floated through the bathroom like tiny moons.",
        "tension": "The dragon had opened the enchanted tap too far, sending bubbles toward the doorway and making the floor slippery.",
        "clue": "the tap's star-shaped handle was still caught beneath her folded wing",
        "reveal": "said she had turned the handle because she wanted to hear the bubbles sing",
        "repair": "closed the tap, dried the floor, and asked before touching the magic fixtures again",
        "ending": "one small bubble rested on the basin, carrying the whole rhyme in a rainbow skin",
        "lesson": "good conduct includes caring for a shared place before chasing a wonder",
    },
    {
        "id": "echoing_tooth",
        "premise": "A loose baby tooth rang like a bell in the bathroom cup.",
        "tension": "The old rhyme warned that only truthful conduct could summon the tooth fairy's silver moth.",
        "clue": "the dragon's reflection looked away whenever the last line was spoken",
        "reveal": "confessed that she had pretended to brush while hiding a sweet berry under her pillow",
        "repair": "brushed carefully, returned the berry, and recited the rhyme without skipping a word",
        "ending": "a silver moth appeared above the clean cup and left a moon-shaped coin by the brush",
        "lesson": "truth makes a promise strong enough to carry a little magic",
    },
]

NAMES = ["Luna", "Mira", "Tavi", "Nia", "Orin"]
HELPERS = ["Aunt Sera", "Grandmother Ione", "Pip", "the bathroom sprite"]
TRAITS = ["curious", "gentle", "brave", "quiet", "restless"]

OPENINGS = [
    "Long ago, when the moon was still learning its path, {hero} entered {place} on silver claws.",
    "In the age when mirrors remembered every secret, {hero} lived beside {place}.",
    "At the hour when faucets whispered to stars, {hero}, a {trait} moon-dragon, heard a rhyme inside {place}.",
    "The old tiles of {place} glowed blue as {hero} came to practice an ancient rhyme.",
]

DIALOGUES = [
    '"Tell me what happened," {helper} said. "A truth can be the first clean step."',
    '"I am listening," said {helper}. "Your conduct now matters more than your fear."',
    '"Look into the mirror," {helper} whispered. "What does it reveal?"',
    '"We can repair a mistake," {helper} said, "but only after we name it."',
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, action, rhyme)
        for place, setting in SETTINGS.items()
        for action in ("reveal", "conduct")
        if action in setting.affords
        for rhyme in RHYMES
        if "rhyme" in setting.affords
    ]


ASP_RULES = r"""
place(bathroom).
affords(bathroom,reveal).
affords(bathroom,conduct).
affords(bathroom,rhyme).
rhyme(moon_tune).
rhyme(mirror_clear).
rhyme(water_song).
valid(P,A,R) :- place(P), affords(P,A), affords(P,rhyme), rhyme(R).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", place, feature))
    for rhyme in RHYMES:
        lines.append(asp.fact("rhyme", rhyme))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    print("only in Python:", sorted(py - clingo))
    print("only in clingo:", sorted(clingo - py))
    return 1


@dataclass
class StoryParams:
    place: str
    action: str
    rhyme: str
    name: str
    helper: str
    trait: str
    scenario: str = "silver_drip"
    seed: Optional[int] = None
    telling: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic bathroom storyworld about reveal, conduct, and rhyme."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--action", choices=["reveal", "conduct"])
    parser.add_argument("--rhyme", choices=RHYMES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.action is None or combo[1] == args.action
        if args.rhyme is None or combo[2] == args.rhyme
    ]
    if not combos:
        raise StoryError("No valid bathroom story combination matches those options.")
    place, action, rhyme = rng.choice(combos)
    return StoryParams(
        place=place,
        action=action,
        rhyme=rhyme,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        scenario=rng.choice(SCENARIOS)["id"],
        telling=rng.randrange(1_000_000),
    )


def generation_prompts(world: World) -> list[str]:
    fact = world.facts
    return [
        "Write a gentle myth set in a bathroom where a character must reveal a truth.",
        f"Tell a story about {fact['hero'].id} learning that conduct matters after a mistake.",
        f"Include the rhyme: {fact['rhyme'].line}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Where did {hero.id}'s myth take place?",
            answer=f"It took place in {world.setting.place}, where mirrors, water, and old magic kept watch.",
        ),
        QAItem(
            question=f"What did {hero.id} reveal?",
            answer=f"{hero.id} revealed that {f['reveal']}. Telling the truth made it possible to repair the trouble.",
        ),
        QAItem(
            question=f"How did {hero.id} show good conduct?",
            answer=f"{hero.id} {f['repair']}. That careful action showed respect for {helper.id} and the shared bathroom.",
        ),
        QAItem(
            question="What was the rhyme in the story?",
            answer=f"The rhyme was: “{f['rhyme'].line}” Its meaning was that {f['rhyme'].meaning}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=f"{hero.id} learned that {f['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style tale that uses memorable characters and wonders to explore a meaningful truth.",
        ),
        QAItem(
            question="What does reveal mean?",
            answer="Reveal means to make something hidden or unknown become known.",
        ),
        QAItem(
            question="What is good conduct?",
            answer="Good conduct means behaving responsibly, respectfully, and carefully toward others and shared places.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words whose sounds match, often at the ends of lines.",
        ),
        QAItem(
            question="Why can honesty help repair a mistake?",
            answer="Honesty helps because people can understand what happened and choose a real way to make things better.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    scenario = next(item for item in SCENARIOS if item["id"] == params.scenario)
    rhyme = RHYMES[params.rhyme]
    world = World(SETTINGS[params.place])
    hero = world.add(
        Entity(
            id=params.name,
            type="dragon",
            label="moon-dragon",
            meters={"care": 0.0, "truth": 0.0},
            memes={"fear": 1.0, "wonder": 1.0},
        )
    )
    helper = world.add(Entity(id=params.helper, type="adult", label="helper"))
    world.add(Entity(id="mirror", kind="thing", type="mirror", label="old mirror"))
    world.add(Entity(id="basin", kind="thing", type="basin", label="moon basin"))

    rng = random.Random(params.telling)
    values = {
        "hero": hero.id,
        "helper": helper.id,
        "place": world.setting.place,
        "trait": params.trait,
    }
    opening = rng.choice(OPENINGS).format(**values)
    dialogue = rng.choice(DIALOGUES).format(**values)
    turning = rng.choice(
        [
            "The clue changed the shape of the mystery.",
            f"For the first time, {hero.id} saw that fear was hiding the real answer.",
            "The mirror did not punish the truth; it made room for it.",
            f"{hero.id} understood that a secret grows heavier when no one carries it honestly.",
        ]
    )
    reflection = rng.choice(
        [
            f"{helper.id} nodded, not because the mistake was small, but because {hero.id} had chosen to face it.",
            f"The bathroom grew calmer when {hero.id} stopped defending the old choice.",
            f"Together, they made the repair slow enough to be trusted.",
        ]
    )

    world.say(opening)
    world.say(scenario["premise"])
    world.para()
    world.say(scenario["tension"])
    world.say(f"The only clue was that {scenario['clue']}.")
    world.say(dialogue)
    world.say(f"{turning} {hero.id} took a breath and {scenario['reveal']}.")
    world.para()
    world.say(f"To make the reveal honest, {hero.id} {scenario['repair']}.")
    world.say(reflection)
    world.say(f"Then they spoke the rhyme together: “{rhyme.line}”")
    world.para()
    world.say(f"The rhyme meant that {rhyme.meaning}.")
    world.say(f"{hero.id} learned that {scenario['lesson']}.")
    world.say(f"At last, {scenario['ending']}.")

    hero.meters["truth"] = 1.0
    hero.meters["care"] = 1.0
    hero.memes["fear"] = 0.0
    hero.memes["peace"] = 1.0
    helper.memes["trust"] = 1.0

    world.facts = {
        "hero": hero,
        "helper": helper,
        "rhyme": rhyme,
        "scenario": scenario,
        "reveal": scenario["reveal"],
        "repair": scenario["repair"],
        "lesson": scenario["lesson"],
        "reconciled": True,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"{entity.id}: {entity.type} meters={meters} memes={memes}")
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"facts: reconciled={world.facts.get('reconciled', False)}")
    return "\n".join(lines)


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
    StoryParams(
        place="bathroom",
        action="reveal",
        rhyme="moon_tune",
        name="Luna",
        helper="Aunt Sera",
        trait="brave",
        scenario="silver_drip",
        telling=11,
    ),
    StoryParams(
        place="bathroom",
        action="conduct",
        rhyme="mirror_clear",
        name="Mira",
        helper="Pip",
        trait="curious",
        scenario="runaway_bubbles",
        telling=22,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 30, 30):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
