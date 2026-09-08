#!/usr/bin/env python3
"""
A small heartwarming story world about a parade, a sailor, and infantry,
with a gentle twist that turns confusion into kindness.
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
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
    parade_name: str
    sailor_name: str
    infantry_name: str
    place: str
    seed: Optional[int] = None
    twist: Optional[str] = None
    mood: Optional[str] = None


@dataclass(frozen=True)
class TwistScenario:
    key: str
    premise: str
    setup: str
    misunderstanding: str
    clue: str
    turn: str
    spoken_exchange: str
    repair: str
    ending: str
    lesson: str


PARADE_NAMES = ["Lantern Parade", "Harbor Parade", "Spring Parade", "Seaside Parade", "Rose Parade"]
SAILOR_NAMES = ["Mina", "Jon", "Luca", "Nell", "Toma", "Ria"]
INFANTRY_NAMES = ["Coral", "Bram", "Eli", "Sage", "Perry", "Uma"]
PLACES = [
    "the bright harbor road",
    "the old town square",
    "the windward pier",
    "the sunlit academy lane",
]

MOODS = ["arrival", "memory", "dialogue", "question", "warning", "promise"]

SCENARIOS = [
    TwistScenario(
        key="drum_parade",
        premise="was underway to welcome the homecoming boats at the harbor",
        setup="The sailor carried a drum, and the infantry marched in a neat row beside the parade banners.",
        misunderstanding="A small, puffing noise made everyone think the drum was about to burst.",
        clue="The noise came in little warm sighs, not in sharp cracks.",
        turn="The sailor opened the drum and found a sleepy kitten curled inside, using the drum as a bed.",
        spoken_exchange='"You were the noisy one," the infantry said softly. "I was only warming the drum so the kitten would not shiver," the sailor replied.',
        repair="The infantry wrapped the kitten in a banner, and the sailor moved the drum to a safer cart.",
        ending="By evening, the parade played its music again, and the kitten marched at the front in a tiny ribbon collar.",
        lesson="kindness often looks like a mistake before it is understood.",
    ),
    TwistScenario(
        key="confetti_dove",
        premise="was celebrating the first day of spring on the town square",
        setup="The sailor had brought bright confetti from the sea, and the infantry were guarding the float with careful steps.",
        misunderstanding="When white feathers began to spill from the float, people feared the decorations were ruined.",
        clue="The feathers were moving on purpose, as if they belonged to something alive.",
        turn="A dove hopped out from under the ribbons, carrying the parade's missing ribbon ring in its beak.",
        spoken_exchange='"Oh!" said the infantry. "It was not ruined at all," the sailor laughed. "It was nesting," said the dove keeper nearby.',
        repair="The infantry placed the ring back on the float, and the sailor scattered gentler confetti around the nest.",
        ending="The parade rolled on with a happy flutter overhead, and the dove rode along as if it had always belonged there.",
        lesson="sometimes a surprise is only a living thing making a home.",
    ),
    TwistScenario(
        key="lantern_message",
        premise="was stepping through the windward pier to honor the night watch",
        setup="The sailor carried a lantern, and the infantry kept the parade line steady against the wind.",
        misunderstanding="The lantern flashed red, and everyone thought it was an alarm.",
        clue="The red light blinked in a slow pattern like tapping fingers.",
        turn="The sailor discovered a tiny message inside the lantern glass: a thank-you note from the lighthouse keeper.",
        spoken_exchange='"Is this an alarm?" the infantry asked. "No," said the sailor, smiling, "it is a thank-you that learned to blink."',
        repair="The infantry turned the parade toward the lighthouse so the keeper could see the cheering crowd.",
        ending="The lighthouse answered with a golden beam, and the parade bowed to the sea in warm silence.",
        lesson="not every flashing light is a warning; some are gratitude asking to be seen.",
    ),
    TwistScenario(
        key="sandcastle_escort",
        premise="was escorting a child's sandcastle to the beach festival on a covered cart",
        setup="The sailor steered the cart slowly, and the infantry marched beside it like careful guards.",
        misunderstanding="A splash of water made everyone think the sandcastle had already melted.",
        clue="Tiny walls were still standing under the cloth, just damp and hidden.",
        turn="The sailcloth cover lifted, and the sandcastle was safe, with a family of crabs decorating the gates.",
        spoken_exchange='"We thought it was lost," whispered the infantry. "It was only taking shelter," said the sailor, kneeling to let the crabs pass.',
        repair="The infantry carried shells to the festival stage, and the sailor fixed a shade over the castle.",
        ending="The sandcastle became the parade's favorite float, with crabs waving from the towers.",
        lesson="careful help can protect what looks fragile at first glance.",
    ),
    TwistScenario(
        key="lost_hatband",
        premise="was honoring a retired captain at the parade square",
        setup="The sailor wore a striped hatband, and the infantry had stitched flowers onto their sleeves for the march.",
        misunderstanding="When the hatband disappeared, people thought someone had taken it on purpose.",
        clue="The missing band left tiny threads leading under the parade bench.",
        turn="The infantry found a nest of ducklings playing with the hatband as if it were a soft road.",
        spoken_exchange='"Did someone steal it?" asked the sailor. "No," said the infantry, laughing gently, "it was borrowed by the youngest marchers."',
        repair="The sailor tied a ribbon toy for the ducklings, and the infantry returned the hatband to the captain's chair.",
        ending="The captain wore the hatband proudly, while the ducklings followed the parade in a waddling line.",
        lesson="a missing thing can become a shared joy when nobody rushes to blame.",
    ),
    TwistScenario(
        key="rain_boots",
        premise="was beginning under a sudden summer rain near the academy lane",
        setup="The sailor had brought extra boots, and the infantry had kept the parade drums under cloth.",
        misunderstanding="One boot was found floating in a puddle, and everyone feared the march was ruined.",
        clue="The boot floated because something light and round was tucked inside it.",
        turn="The sailor tipped out a kitten and a bundle of painted pebbles, both dry and warm.",
        spoken_exchange='"I only left it there to keep them safe," the sailor said. "Then the parade had a secret passenger," the infantry replied with a grin.',
        repair="The infantry dried the boot by the drums, and the sailor carried the kitten home in the hat.",
        ending="When the rain ended, the parade splashed through the lane with one extra happy tail peeking out.",
        lesson="a careful secret can be safer than a loud explanation.",
    ),
    TwistScenario(
        key="flower_baton",
        premise="was winding through the rose garden for the afternoon ceremony",
        setup="The sailor led the first row, and the infantry carried the parade banner between them.",
        misunderstanding="A thorny baton was mistaken for a broken branch and nearly tossed away.",
        clue="The baton smelled of roses and had fresh water on its handle.",
        turn="The gardener returned, laughing, because the 'branch' was a flower wand used to teach bees a safe path.",
        spoken_exchange='"We nearly threw it out," said the infantry. "That would have been a shame," said the sailor. "It helps the garden keep its way."',
        repair="The infantry planted the baton back in the soil, and the sailor watered the roses around it.",
        ending="The parade left a glowing path behind, and bees traced it like tiny dancers.",
        lesson="one person's strange object may be another's careful tool.",
    ),
    TwistScenario(
        key="torn_banner",
        premise="was carrying the old victory banner to the community hall",
        setup="The sailor held one side of the cloth, and the infantry held the other so it would not drag.",
        misunderstanding="A long rip made the crowd gasp and assume the banner was ruined forever.",
        clue="The rip matched the pattern of a folded seam, not a sharp cut.",
        turn="The sailor unfolded the cloth and revealed a second hidden banner stitched inside, made for the children to sign.",
        spoken_exchange='"It was not torn," the infantry said. "It was folded." "And hiding a better surprise," the sailor added.',
        repair="The infantry fetched markers, and the sailor helped the children sign the hidden banner.",
        ending="By sunset, both banners flew together, one old and one new, above a parade full of smiles.",
        lesson="what looks broken can sometimes be a door to something kind.",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade storyworld with sailor, infantry, and a gentle twist.")
    ap.add_argument("--parade-name", choices=PARADE_NAMES)
    ap.add_argument("--sailor-name", choices=SAILOR_NAMES)
    ap.add_argument("--infantry-name", choices=INFANTRY_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--twist", choices=[s.key for s in SCENARIOS])
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    parade_name = args.parade_name or rng.choice(PARADE_NAMES)
    sailor_name = args.sailor_name or rng.choice(SAILOR_NAMES)
    infantry_name = args.infantry_name or rng.choice([n for n in INFANTRY_NAMES if n != sailor_name])
    place = args.place or rng.choice(PLACES)
    twist = args.twist or rng.choice(SCENARIOS).key
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(
        parade_name=parade_name,
        sailor_name=sailor_name,
        infantry_name=infantry_name,
        place=place,
        seed=None,
        twist=twist,
        mood=mood,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("domain", "parade"),
            asp.fact("feature", "twist"),
            asp.fact("style", "heartwarming"),
            asp.fact("seed_word", "parade"),
            asp.fact("seed_word", "sailor"),
            asp.fact("seed_word", "infantry"),
        ]
    )


ASP_RULES = r"""
feature(twist) :- domain(parade).
feature(heartwarming) :- style(heartwarming).
required(seed_word(parade)).
required(seed_word(sailor)).
required(seed_word(infantry)).
#show feature/1.
#show seed_word/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show feature/1.")
    model = asp.one_model(program)
    feats = sorted(set(asp.atoms(model, "feature")))
    wanted = [("heartwarming",), ("twist",)]
    if sorted(feats) != wanted:
        print("MISMATCH: ASP features are wrong.")
        print(feats)
        return 1
    params = StoryParams(
        parade_name="Lantern Parade",
        sailor_name="Mina",
        infantry_name="Bram",
        place=PLACES[0],
        seed=7,
        twist="drum_parade",
        mood="dialogue",
    )
    sample = generate(params)
    if "parade" not in sample.story.lower() or "sailor" not in sample.story.lower() or "infantry" not in sample.story.lower():
        print("MISMATCH: generated story does not include seed words.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    scenario = next((s for s in SCENARIOS if s.key == params.twist), SCENARIOS[0])
    world = World()

    sailor = world.add(Entity(
        id=params.sailor_name,
        kind="character",
        type="sailor",
        label="sailor",
        phrase=params.sailor_name,
        location=params.place,
        meters={"energy": 0.7, "worry": 0.2},
        memes={"care": 0.6},
        traits=["gentle", "steady"],
    ))
    infantry = world.add(Entity(
        id=params.infantry_name,
        kind="character",
        type="infantry",
        label="infantry",
        phrase=params.infantry_name,
        location=params.place,
        meters={"energy": 0.8, "worry": 0.3},
        memes={"duty": 0.7},
        traits=["careful", "brave"],
    ))
    parade = world.add(Entity(
        id="parade",
        kind="event",
        type="parade",
        label=params.parade_name,
        phrase=params.parade_name,
        location=params.place,
        meters={"music": 0.6, "joy": 0.5},
        memes={"community": 0.8},
        traits=["festive"],
    ))
    twist = world.add(Entity(
        id="twist",
        kind="thing",
        type="twist",
        label="twist",
        phrase="a twist",
        location=params.place,
        meters={"mystery": 0.8},
        memes={"surprise": 0.9},
        traits=["unexpected"],
    ))
    world.facts.update(params=params, scenario=scenario.key)

    opening = [
        f"The {params.parade_name.lower()} was moving along {params.place} when {params.sailor_name} the sailor led the music forward.",
        f"{params.infantry_name} the infantry walked beside the parade so the little crowd would not be jostled.",
        scenario.setup,
    ]
    for line in opening:
        world.say(line)

    world.say(
        rng.choice(
            [
                f"Then came the twist: {scenario.misunderstanding}",
                f"At the same moment, the twist appeared in the crowd's eyes: {scenario.misunderstanding}",
                f"A warm, confusing twist followed the drums: {scenario.misunderstanding}",
            ]
        )
    )

    world.para()
    world.say(f"{params.infantry_name} frowned and said, \"Should we stop the parade?\"")
    world.say(f"{params.sailor_name} answered, \"Not yet. Let's look closer first.\"")
    world.say(f"They slowed their steps, and {scenario.clue}")
    world.say(f"That clue changed everything, because {scenario.turn}")

    world.para()
    world.say(f"{scenario.spoken_exchange}")
    world.say(f"The infantry helped with a careful repair, and the sailor kept the parade calm while everyone understood what was happening.")
    world.say(scenario.repair)
    world.say(f"In the end, {scenario.ending}")

    world.para()
    world.say(f"The heartwarming lesson stayed with them: {scenario.lesson}")
    world.say("What looked like trouble had turned into a kinder kind of parade.")

    sailor.meters["worry"] = 0.0
    infantry.meters["worry"] = 0.0
    parade.meters["joy"] = 1.0
    twist.memes["surprise"] = 0.1
    world.facts["resolved"] = True

    prompts = [
        f"Write a heartwarming story about a parade, a sailor, and infantry, and include a twist.",
        f"Tell a child-friendly parade tale where {params.sailor_name} and {params.infantry_name} must misunderstand something before helping it.",
        f"Make the ending warm and kind, with the parade becoming happier after the twist.",
    ]
    story_qa = [
        QAItem(
            question="Who led the parade?",
            answer=f"The sailor {params.sailor_name} led the parade forward along {params.place}.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"The misunderstanding was that {scenario.misunderstanding}",
        ),
        QAItem(
            question="What clue helped the characters understand the truth?",
            answer=f"They noticed that {scenario.clue}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended when {scenario.ending}",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {scenario.lesson}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful public march or celebration where people move together and often make music.",
        ),
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is someone who works with boats and the sea.",
        ),
        QAItem(
            question="Who is infantry?",
            answer="Infantry are soldiers who march and travel on foot.",
        ),
        QAItem(
            question="What does twist mean in a story?",
            answer="A twist is a surprising turn that changes what the characters thought was happening.",
        ),
        QAItem(
            question="What makes this kind of story heartwarming?",
            answer="It ends with kindness, understanding, and a feeling that everyone is better off than before.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            bits = []
            if e.location:
                bits.append(f"location={e.location}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Lantern Parade", "Mina", "Bram", PLACES[0], 101, "drum_parade", "dialogue"),
            StoryParams("Spring Parade", "Nell", "Eli", PLACES[1], 202, "confetti_dove", "memory"),
            StoryParams("Harbor Parade", "Luca", "Sage", PLACES[2], 303, "lantern_message", "question"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            attempt_seed = base_seed + i
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.parade_name} with {p.sailor_name} and {p.infantry_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
