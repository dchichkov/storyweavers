#!/usr/bin/env python3
"""A myth-like cautionary StoryWorld about glare, parentheses, and a mystery to solve."""

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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the hill of mirrors"
    child_name: str = "Luna"
    guide_name: str = "Ivo"
    relic: str = "the moon tablet"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    omen: str
    trouble: str
    false_guess: str
    clue: str
    warning: str
    plan: str
    child_job: str
    guide_job: str
    discovery: str
    consequence: str
    ending: str
    lesson: str


SETTINGS = {
    "the hill of mirrors",
    "the old observatory",
    "the valley of white stones",
    "the mountain archive",
}
NAMES = ["Luna", "Mira", "Tavi", "Niko", "Sela", "Oren", "Pia", "Ravi"]
GUIDES = ["Ivo", "Suri", "Bram", "Eda", "Kian", "Mara"]
RELICS = [
    "the moon tablet",
    "the bronze star",
    "the whispering seal",
    "the black-ink map",
]

SCENARIOS = [
    Scenario(
        "sunken-letter",
        "At noon, a hard glare flashed from a stone door.",
        "A message on the door seemed to vanish whenever Luna looked straight at it.",
        "She guessed that the mountain spirit had hidden the words because it was angry.",
        "the only visible marks were two curved strokes facing one another",
        "Never stare into a glare to prove courage; shade your eyes and study the light's path.",
        "make a shade, look from the side, and read the marks inside the parentheses",
        "held the blue cloth above the door",
        "turned the relic so its dull edge blocked the glare",
        "The curved strokes were parentheses, and inside them was a warning about a loose bridge.",
        "Because they read before crossing, they found a safer path around the ravine.",
        "The stone door stood quiet beneath its shade, with the warning safe inside its parentheses.",
        "A bright sign may hide its meaning, and caution can be braver than a bold guess.",
    ),
    Scenario(
        "missing-star",
        "A star-shaped light struck the floor beneath the observatory dome.",
        "The bronze star vanished whenever anyone stepped toward the shining patch.",
        "Luna thought the star was alive and fleeing from her.",
        "dust showed a curved trail that began beside a pair of parentheses",
        "Do not chase a shining thing while looking only at its glare.",
        "close the dome, follow the shadowed trail, and read the small inscription",
        "pulled the dome lever slowly",
        "searched where the light could not reach",
        "The bronze star was behind a panel, and its parentheses named the panel's hidden latch.",
        "They recovered the star without touching the dangerous lens.",
        "The dome opened at dusk, when the star shone softly instead of glaring.",
        "A mystery grows when fear fills the spaces that patient looking could explain.",
    ),
    Scenario(
        "river-warning",
        "The river gave off a silver glare beneath the first moon.",
        "A stepping stone seemed to appear in the water, but every approach made it fade.",
        "Luna nearly stepped toward the gleam and blamed the river for moving the stone.",
        "a reed pointed from the glare toward parentheses carved on the bank",
        "Water and light can deceive a hurried traveler.",
        "cover the reflection, read the bank, and test each stone with a staff",
        "held a woven mat over the water",
        "read the carved words from the bank",
        "The parentheses contained the words 'wait for the low tide.'",
        "At low tide, the real stones rose in a safe line across the river.",
        "The river darkened around the true path while the false glare broke apart.",
        "Caution keeps a traveler from mistaking a reflection for a road.",
    ),
    Scenario(
        "sleeping-giant",
        "A pale glare rested on the eyelid of a sleeping stone giant.",
        "A golden key lay near the giant, but its shine made every small movement look enormous.",
        "Luna thought the giant had awakened and reached for the key.",
        "parentheses on the key's handle enclosed a tiny drawing of a feather",
        "When a mystery lies beside a sleeper, noise can turn a clue into danger.",
        "dim the glare, use the feather mark, and move only when the wind moves",
        "covered the key with a soft sleeve",
        "watched the giant's breathing and counted the wind gusts",
        "The feather mark showed a silent latch beneath the giant's hand.",
        "They opened the latch and left the key untouched until the giant's dream passed.",
        "Morning found the key in its niche, while the giant slept beneath a gentler sun.",
        "The safest answer is sometimes the one that does not take what is within reach.",
    ),
    Scenario(
        "echoing-gate",
        "A gate of black glass threw a fierce glare across the path.",
        "Every question spoken to the gate returned with one word missing.",
        "Luna believed the gate demanded a louder voice.",
        "two parentheses around the missing word grew warm when she whispered",
        "Loudness can hide an answer instead of calling it forth.",
        "speak softly, find the missing word, and place it inside the parentheses",
        "shielded the glass with a cloak",
        "listened for the echo's empty place",
        "The missing word was 'mercy,' and the gate opened when it was spoken gently.",
        "The glare faded, revealing a road that had been hidden behind the gate.",
        "The gate remained open only while the word mercy rested between its marks.",
        "A mystery may ask for kindness, not force.",
    ),
    Scenario(
        "the-wrong-shadow",
        "At sunset, a long glare made Luna's shadow point toward a sealed shrine.",
        "The shadow seemed to accuse Ivo of stealing the relic.",
        "Luna almost trusted the shadow more than the person beside her.",
        "parentheses on the shrine wall showed that the shadow was cast by a tilted spear",
        "Never condemn a friend from a shape made by changing light.",
        "move the spear, compare both shadows, and inspect the shrine together",
        "marked the first shadow with a pebble",
        "lifted the spear without touching the shrine",
        "The second shadow pointed toward the true clue: a loose tile bearing the relic's sign.",
        "They found the relic and cleared Ivo's name before the sun disappeared.",
        "The shrine's wall held two shadows, but only one honest story.",
        "Caution protects trust when appearances try to become accusations.",
    ),
    Scenario(
        "lantern-under-ice",
        "A blue glare shone beneath the frozen lake.",
        "A lantern under the ice seemed close enough to reach.",
        "Luna considered breaking the ice because the light looked warm.",
        "parentheses scratched in the snow showed a picture of a hooked pole",
        "A bright prize is not worth standing on a doubtful surface.",
        "stay on the shore, use the hooked pole, and follow the snow clue",
        "kept both feet behind the safe line",
        "pulled the lantern toward the bank",
        "The lantern came free, and its parentheses revealed the name of a lost village.",
        "They carried it to the village elder instead of keeping it.",
        "The blue glare became a welcoming lamp in the elder's window.",
        "Caution can turn a tempting discovery into a gift.",
    ),
    Scenario(
        "the-blind-statue",
        "A statue's silver eyes cast a glare over the temple floor.",
        "The path to the altar was marked only when Luna closed one eye.",
        "She thought the statue wanted her to walk blindly.",
        "parentheses beside the eye marks said, 'Look through a narrow opening.'",
        "A strange instruction should be tested carefully, not obeyed recklessly.",
        "make a small paper slit, look through it, and mark the safe stones",
        "held the paper slit at arm's length",
        "placed stones on the path from the side",
        "The narrow view revealed a pattern of safe white stones.",
        "They reached the altar without stepping on the cracked dark tiles.",
        "The statue's silver eyes no longer glared once the altar candle was lit.",
        "Good caution narrows a danger until the true path can be seen.",
    ),
]

OPENINGS = [
    "{child} came to {setting} while the sun burned like a polished shield.",
    "In the age when stones remembered names, {child} climbed toward {setting}.",
    "Before the evening star appeared, {child} and {guide} reached {setting}.",
    "The old people warned travelers about {setting}, but {child} wanted to see it.",
    "A mystery waited beneath the bright sky at {setting}.",
    "The mountain wind carried {child} to {setting}, where every bright thing seemed to watch.",
]

INNER_THOUGHTS = [
    "Luna thought, 'If I rush, the glare will choose for me.'",
    "Inside, Luna wondered, 'What am I seeing, and what am I only guessing?'",
    "Luna told herself, 'A brave heart can still wait.'",
    "For a moment Luna thought, 'Perhaps the mystery is warning us, not challenging us.'",
    "Luna's first thought was to run forward, but her wiser thought asked her to look again.",
]

DIALOGUE = [
    "'The glare is a clue, not an answer,' said {guide}.",
    "'Then we will shade it and read what remains,' said {child}.",
    "'What if the mark is a trap?' asked {child}.",
    "'Then we will not touch it until we understand it,' said {guide}.",
    "'The parentheses hold something back,' said {child}.",
    "'Or they hold something safe for careful eyes,' replied {guide}.",
]

MORALS = [
    "The mountain remembers those who look twice.",
    "A wise traveler does not call a reflection a road.",
    "Caution is a lantern carried inside the mind.",
    "The eye sees brightness first, but patience sees meaning.",
]


def generate_world(p: StoryParams) -> World:
    if p.child_name == p.guide_name:
        raise StoryError("The seeker and guide must have different names.")
    if p.setting not in SETTINGS:
        raise StoryError("That setting is not part of the available mythic map.")
    if p.relic not in RELICS:
        raise StoryError("That relic is not registered in the mountain archive.")

    world = World(p.setting)
    child = world.add(Entity("C", "seeker", p.child_name))
    guide = world.add(Entity("G", "guide", p.guide_name))
    relic = world.add(Entity("R", "relic", p.relic))

    value = abs(p.seed if p.seed is not None else 0)
    scene = SCENARIOS[value % len(SCENARIOS)]
    opening = OPENINGS[(value // 8) % len(OPENINGS)]
    thought = INNER_THOUGHTS[(value // 48) % len(INNER_THOUGHTS)]
    exchange = DIALOGUE[(value // 288) % len(DIALOGUE)]

    world.say(opening.format(child=child.label, guide=guide.label, setting=p.setting))
    world.say(f"They carried {relic.label}, an old object said to remember the truth when people forgot it.")
    world.say(scene.omen)
    world.para()
    world.say(scene.trouble)
    world.say(scene.false_guess)
    world.say(thought)
    world.say(exchange.format(child=child.label, guide=guide.label))
    world.say(f"{guide.label} pointed to a clue: {scene.clue}.")
    world.para()
    world.say(f"{child.label} and {guide.label} agreed to {scene.plan}.")
    world.say(f"{child.label} {scene.child_job}, while {guide.label} {scene.guide_job}.")
    world.say(f"They discovered that {scene.discovery}")
    world.say(scene.warning)
    world.say(f"The mystery was solved: {scene.consequence}")
    world.para()
    world.say(f"{child.label} said, 'Now I understand why the parentheses mattered.'")
    world.say(f"{guide.label} answered, 'Yes. They made room for the truth, but they did not shout it.'")
    world.say(f"{scene.ending} {scene.lesson}")
    world.say(random.Random(value + 91).choice(MORALS))

    child.meters.update(attention=1.0, caution=1.0)
    child.memes.update(wisdom=1.0, trust=1.0)
    guide.meters.update(observation=1.0, guidance=1.0)
    guide.memes.update(patience=1.0, trust=1.0)
    relic.meters.update(recovered=1.0, protected=1.0)
    relic.memes.update(memory=1.0)

    world.facts.update(
        child=child.label,
        guide=guide.label,
        relic=relic.label,
        setting=p.setting,
        scenario=scene.key,
        omen=scene.omen,
        trouble=scene.trouble,
        false_guess=scene.false_guess,
        clue=scene.clue,
        warning=scene.warning,
        plan=scene.plan,
        child_job=scene.child_job,
        guide_job=scene.guide_job,
        discovery=scene.discovery,
        consequence=scene.consequence,
        ending=scene.ending,
        lesson=scene.lesson,
        glare=True,
        parentheses=True,
        solved=True,
        cautious=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {f['child']} and {f['guide']} face?",
            answer=f"They faced a mystery in {f['setting']}: {str(f['trouble'])[0].lower() + str(f['trouble'])[1:]}",
        ),
        QAItem(
            question="What did the glare make difficult to understand?",
            answer=f"The glare made it difficult to understand the real clue because {f['false_guess'][0].lower() + f['false_guess'][1:]}",
        ),
        QAItem(
            question="How did the parentheses help?",
            answer=f"The parentheses helped by holding the important clue: {f['discovery']}",
        ),
        QAItem(
            question="What cautious plan solved the mystery?",
            answer=f"They decided to {f['plan']}. {f['child']} {f['child_job']}, while {f['guide']} {f['guide_job']}.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer=f"They solved the mystery and avoided the danger. {f['ending']} The lesson was that {f['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is glare?",
            answer="Glare is harsh or dazzling light that can make it difficult to see details clearly.",
        ),
        QAItem(
            question="What are parentheses?",
            answer="Parentheses are curved marks that set extra words or information apart inside a sentence.",
        ),
        QAItem(
            question="Why is caution useful near a mystery?",
            answer="Caution is useful because it gives a person time to test clues and avoid harm before acting.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has while deciding what to do.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a myth-like mystery story about {f['child']} facing glare in {f['setting']}.",
        f"Tell a cautionary tale in which parentheses hide the clue that {f['clue']}.",
        "Create a child-facing myth where an inner thought changes a dangerous choice into a careful plan.",
    ]


ASP_RULES = r"""
cautious(seeker) :- attention(seeker), patience(guide), glare_present.
parenthetical_clue(relic) :- parentheses_present, relic(relic), clue_found.
mystery_solved :- cautious(seeker), parenthetical_clue(relic), recovered(relic).
safe_resolution :- mystery_solved, avoided_danger.
#show cautious/1.
#show parenthetical_clue/1.
#show mystery_solved/0.
#show safe_resolution/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("seeker", "luna"),
            asp.fact("guide", "ivo"),
            asp.fact("relic", "moon_tablet"),
            asp.fact("attention", "seeker"),
            asp.fact("patience", "guide"),
            asp.fact("glare_present"),
            asp.fact("parentheses_present"),
            asp.fact("clue_found"),
            asp.fact("recovered", "moon_tablet"),
            asp.fact("avoided_danger"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(
        asp_program(
            "#show cautious/1. #show parenthetical_clue/1. "
            "#show mystery_solved/0. #show safe_resolution/0."
        )
    )
    solved = asp.atoms(symbols, "mystery_solved")
    safe = asp.atoms(symbols, "safe_resolution")
    if solved and safe:
        print("OK: ASP and Python both resolve the cautious mystery.")
        return 0
    print("MISMATCH: ASP did not derive the expected safe resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--child-name")
    parser.add_argument("--guide-name")
    parser.add_argument("--relic", choices=RELICS)
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
    child = args.child_name or rng.choice(NAMES)
    guide = args.guide_name or rng.choice([name for name in GUIDES if name != child])
    if child == guide:
        raise StoryError("The seeker and guide must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        child_name=child,
        guide_name=guide,
        relic=args.relic or rng.choice(RELICS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the hill of mirrors", "Luna", "Ivo", "the moon tablet", 7),
    StoryParams("the old observatory", "Mira", "Suri", "the bronze star", 19),
    StoryParams("the valley of white stones", "Tavi", "Bram", "the whispering seal", 31),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"scenario={facts['scenario']} glare=True parentheses=True "
            f"solved=True cautious=True"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautious/1. #show parenthetical_clue/1. #show mystery_solved/0. #show safe_resolution/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show mystery_solved/0. #show safe_resolution/0."))
        print("ASP model:", " ".join(str(symbol) for symbol in symbols))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base + index))
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
