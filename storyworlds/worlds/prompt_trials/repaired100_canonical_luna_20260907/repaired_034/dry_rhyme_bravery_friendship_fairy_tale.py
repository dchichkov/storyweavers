#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a dry well, brave friendship, and rhyme.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Pip"
    village: str = "the Briar Village"
    well: str = "the old wishing well"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    well: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Luna", "Mira", "Nell", "Tessa", "Wren", "Elin"]
FRIEND_NAMES = ["Pip", "Bram", "Clover", "Finn", "Moss", "Robin"]
VILLAGES = ["the Briar Village", "the Clover Village", "the Moonbeam Village"]
WELLS = ["the old wishing well", "the stone well", "the silver well"]

ARCS = [
    {
        "premise": "For seven sunny days, no cloud had opened above the village",
        "problem": "the village well had gone dry",
        "stake": "the gardens drooped and the thirsty animals had no cool water",
        "temptation": "climb down alone and claim the rescue as a grand deed",
        "clue": "a faint bell rang whenever two friends sang beside the stones",
        "action": "They tied a braided rope, carried lanterns, and lowered a listening bucket together",
        "twist": "the well was not empty; a sleeping spring had been sealed by a fallen moonstone",
        "sharing": "They lifted the moonstone together and shared the first bright bucket among every household",
        "lesson": "bravery grows steadier when friendship gives it a hand",
        "ending": "water danced over the stones while every garden lifted a green leaf",
        "question": "Why did the villagers need to restore the well?",
        "answer": "They needed the well to water the gardens and give drinking water to the animals.",
    },
    {
        "premise": "The kingdom prepared for the Festival of First Rain",
        "problem": "the rain drum had cracked during a long dry spell",
        "stake": "the clouds might pass without noticing the village's invitation",
        "temptation": "hide the crack and beat the drum alone before anyone could laugh",
        "clue": "the drum made its strongest sound when many small hands tapped its sides",
        "action": "They stitched the hide with golden thread and taught every child a gentle rhythm",
        "twist": "the crack had become a smiling moon shape that made the drum's voice sweeter",
        "sharing": "They passed the drum around so the whole village could call for rain",
        "lesson": "a flaw can become a door when friends face it bravely",
        "ending": "one soft drop landed on the drum, then a silver curtain of rain filled the square",
        "question": "How did the villagers repair the rain drum?",
        "answer": "They stitched its cracked hide with golden thread and shared a rhythm for everyone to play.",
    },
    {
        "premise": "A dry wind had carried the queen's blue ribbon into the thornwood",
        "problem": "the ribbon hung from a branch above a deep ravine",
        "stake": "without it, the queen's coronation crown would be unfinished",
        "temptation": "dash across the ravine's narrow stones and win the queen's praise alone",
        "clue": "the ribbon's silver bells answered a rhyme spoken from the safe path",
        "action": "They made a rhyming call-and-answer and followed the bells around the ravine",
        "twist": "the ribbon had wrapped around a nest, keeping three baby birds warm",
        "sharing": "They freed the ribbon only after weaving a softer nest cover from their own scarves",
        "lesson": "true bravery protects small lives before seeking applause",
        "ending": "the queen wore her ribbon, and the rescued birds chirped the final rhyme",
        "question": "Why did Luna and Pip avoid pulling the ribbon at once?",
        "answer": "They saw that the ribbon was wrapped around a nest and wanted to protect the baby birds first.",
    },
    {
        "premise": "A little fairy lost her way across a meadow baked dry by the sun",
        "problem": "her dew-drop lantern had stopped glowing",
        "stake": "she could not find the moon gate before nightfall",
        "temptation": "run ahead with the lantern and leave the frightened fairy behind",
        "clue": "the lantern brightened whenever someone spoke a kind rhyming promise",
        "action": "They walked side by side and traded brave couplets with every step",
        "twist": "the lantern was powered by friendship, not dew",
        "sharing": "They invited the fairy to add her own verse and led her safely to the moon gate",
        "lesson": "a shared kind word can light a path through a dry dark",
        "ending": "the moon gate opened like a flower, glowing with three cheerful voices",
        "question": "What made the fairy's lantern glow?",
        "answer": "The lantern glowed when the friends and the fairy shared kind rhyming promises.",
    },
    {
        "premise": "The castle orchard had grown dry before the apples were ripe",
        "problem": "the golden watering crown had vanished",
        "stake": "the young trees might wither before harvest",
        "temptation": "search the thorn hedge alone and keep the crown's magic for one tree",
        "clue": "tiny wet footprints led from the hedge toward the sleeping dragon's cave",
        "action": "They approached with a calm rhyme instead of a sword",
        "twist": "the dragon had borrowed the crown to water a thirsty patch of blue flowers",
        "sharing": "They helped the dragon carry water to every tree and flower",
        "lesson": "courage listens before it labels someone a foe",
        "ending": "apples blushed beside blue flowers while the dragon hummed their shared rhyme",
        "question": "Why had the dragon taken the watering crown?",
        "answer": "The dragon had taken it to water a thirsty patch of blue flowers.",
    },
]

OPENINGS = [
    "Once, beneath a pale gold sun",
    "Long ago, where the thorn hedges curled",
    "In a little kingdom at the edge of the wild",
    "When the morning bells were thin and bright",
    "Beyond a hill shaped like a sleeping cat",
    "At the very end of a summer day",
]

RHYME_LINES = [
    "'When the road is dry and wide, brave hearts walk side by side.'",
    "'If the well is still and deep, friendship wakes what stones may keep.'",
    "'A fearful start need not remain; two kind voices call the rain.'",
    "'Step by step and rhyme by rhyme, friends can turn a troubled time.'",
    "'When shadows grow and courage thins, a faithful friend helps hope begin.'",
]

DIALOGUE = [
    ("'I am afraid,' said {hero}.", "'Then be afraid with me,' said {friend}. 'We will not face it alone.'"),
    ("'What if we fail?' asked {hero}.", "'Then we will learn the next step together,' said {friend}."),
    ("'The dark is watching,' whispered {hero}.", "'So are the stars,' replied {friend}. 'Let us give them a brave song.'"),
    ("'I cannot do this by myself,' said {hero}.", "'Good,' said {friend}. 'You have me, and I have you.'"),
]

CODAS = [
    "{hero} learned that courage is not the absence of fear, but a hand held through it.",
    "From then on, the villagers called friendship the oldest magic in the kingdom.",
    "{hero} kept the rhyme in heart and voice whenever a dry day seemed too long.",
    "The tale was told beside the water, where every listener added one brave line.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale storyworld about dryness, rhyme, bravery, and friendship."
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--well", choices=WELLS)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        village=args.village or rng.choice(VILLAGES),
        well=args.well or rng.choice(WELLS),
        arc=rng.randrange(len(ARCS)),
        seed=args.seed,
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(params.hero, "hero"),
        friend=Entity(params.friend, "friend"),
        well=Entity(params.well, "well"),
    )


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    world.hero.memes.update({"curiosity": 1.0, "fear": 1.0, "bravery": 0.0})
    world.friend.memes["friendship"] = 1.0
    world.well.meters["water"] = 0.0
    world.well.meters["depth"] = 1.0
    world.facts.update(
        {
            "dry": True,
            "problem": arc["problem"],
            "stake": arc["stake"],
            "clue": arc["clue"],
            "place": p.village,
            "rhyme": True,
        }
    )

    world.say(f"{rng.choice(OPENINGS)}. In {p.village}, {p.hero} and {p.friend} lived near {p.well}.")
    world.say(f"{arc['premise']}, and {arc['problem']}. {arc['stake']}.")
    world.para()

    world.say(f"For a moment, {p.hero} wanted to {arc['temptation']}.")
    first, second = rng.choice(DIALOGUE)
    world.say(first.format(hero=p.hero, friend=p.friend) + " " + second.format(hero=p.hero, friend=p.friend))
    world.say(f"{p.hero} took a breath, and {p.friend} offered a rhyme: {rng.choice(RHYME_LINES)}")
    world.hero.memes["bravery"] = 1.0
    world.hero.memes["fear"] = 0.5
    world.facts["temptation"] = arc["temptation"]
    world.facts["decision"] = "They chose to act together."

    world.para()
    world.say(f"Together, they noticed that {arc['clue']}.")
    world.say(f"{arc['action']}.")
    world.say(f"Then came the fairy-tale turn: {arc['twist']}.")
    world.hero.memes["fear"] = 0.0
    world.friend.memes["trust"] = 1.0
    world.facts["twist"] = arc["twist"]
    world.facts["solution"] = arc["action"]
    world.facts["resolved"] = True

    world.para()
    world.say(f"{arc['sharing']}.")
    world.say(f"{arc['ending']}.")
    world.say(f"{rng.choice(CODAS).format(hero=p.hero)} {p.hero} understood that {arc['lesson']}.")
    world.facts["dry"] = False
    world.facts["water_restored"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    if not 0 <= params.arc < len(ARCS):
        raise StoryError("The chosen tale arc does not exist.")
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a fairy tale about {params.hero} and {params.friend} facing a dry problem with bravery.",
        f"Use rhyme and friendship to help two friends solve this problem: {arc['problem']}.",
        f"Tell a child-friendly story in {params.village} with a surprising turn: {arc['twist']}.",
    ]
    story_qa = [
        QAItem(
            f"What did {params.hero} first think about doing?",
            f"{params.hero} first thought about trying to {arc['temptation']}.",
        ),
        QAItem(
            f"What clue did {params.hero} and {params.friend} notice?",
            f"They noticed that {arc['clue']}.",
        ),
        QAItem(
            f"What was the surprising turn in the tale?",
            f"The surprising turn was that {arc['twist']}.",
        ),
        QAItem(
            f"How did friendship help {params.hero}?",
            f"Friendship gave {params.hero} support to act bravely and solve the problem together with {params.friend}.",
        ),
        QAItem(
            f"What changed by the end of the story?",
            f"The dry trouble was solved: {arc['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            "What does dry mean?",
            "Dry means having little or no water or moisture.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing to do what is right even when something feels frightening.",
        ),
        QAItem(
            "What is friendship?",
            "Friendship is a caring bond in which people help, trust, and encourage one another.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a line or pair of words with matching or similar ending sounds.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.friend, world.well):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.name:18} ({entity.kind:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :-
    feature(dry),
    feature(rhyme),
    feature(bravery),
    feature(friendship),
    resolves(dry_trouble).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("domain", "fairy_tale"),
            asp.fact("feature", "dry"),
            asp.fact("feature", "rhyme"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "friendship"),
            asp.fact("resolves", "dry_trouble"),
        ]
    )


def asp_program(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    if asp.atoms(model, "valid") != [("story",)]:
        print("MISMATCH: ASP twin failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "dry" not in sample.story.lower():
            print("MISMATCH: generated story failed its dry-world check.")
            return 1
        if not sample.story_qa:
            print("MISMATCH: generated story has no story questions.")
            return 1
    print("OK: ASP twin and generated stories are consistent.")
    return 0


CURATED = [
    StoryParams(hero="Luna", friend="Pip", village="the Briar Village", well="the old wishing well", arc=0, seed=101),
    StoryParams(hero="Mira", friend="Bram", village="the Clover Village", well="the stone well", arc=2, seed=202),
    StoryParams(hero="Wren", friend="Clover", village="the Moonbeam Village", well="the silver well", arc=4, seed=303),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
