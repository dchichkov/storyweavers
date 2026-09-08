#!/usr/bin/env python3
"""
A tiny superhero storyworld about bacon, removal, twists, and reconciliation.

The domain is intentionally small:
- A hero protects a city block with a simple gear-driven power.
- Bacon causes a problem that must be removed.
- A twist changes what the hero believes about the trouble.
- Reconciliation brings characters back together in a warm ending.
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
    hero: str = "Bolt"
    sidekick: str = "Pip"
    citizen: str = "Mara"
    setting: str = "the downtown square"
    bacon: str = "a bacon spill"
    remove: str = "remove the bacon"
    seed: Optional[int] = None
    twist_index: int = 0


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
    sidekick: Entity
    citizen: Entity
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


HERO_NAMES = ["Bolt", "Spark", "Nova", "Comet", "Ruby", "Atlas"]
SIDEKICK_NAMES = ["Pip", "Jade", "Tess", "Quill", "Mika", "Rae"]
CITIZEN_NAMES = ["Mara", "Ollie", "Nori", "Iris", "Zed", "Luna"]
SETTINGS = ["the downtown square", "the market street", "the river bridge", "the rooftop garden"]


TWISTS = [
    {
        "problem": "A bacon truck tipped in the square and made the pavement slippery",
        "stake": "People could slide into the fountain if nobody fixed it fast",
        "temptation": "dash in alone and grab credit for the cleanup",
        "clue": "the grease trail pointed not to the truck, but to a broken lunch cart",
        "action": "They used absorbent towels, a broom shield, and a long rope to sweep the mess into a bucket",
        "twist": "the real source was not the truck at all; a delivery cart had cracked and spilled the bacon",
        "reconciliation": "the truck driver apologized, the cart owner helped mop, and everyone shared a safe snack after the cleanup",
        "lesson": "A quick guess can be wrong, and asking kindly can heal hurt feelings",
        "ending": "the square sparkled again while a repaired cart rolled home beside the hero",
        "question": "What made the pavement slippery?",
        "answer": "The pavement was slippery because bacon grease had spilled across the square.",
    },
    {
        "problem": "A hero statue was stuck wearing a bacon-themed costume from the festival",
        "stake": "The mayor wanted the statue cleaned before the morning ceremony",
        "temptation": "pull the costume off in a hurry and tear it apart",
        "clue": "the costume had been stitched on by a nervous child who loved the statue",
        "action": "They cut the costume free thread by thread and folded the bright fabric carefully",
        "twist": "the costume was a surprise gift, not a prank, and the child only wanted to cheer the city",
        "reconciliation": "the child, the mayor, and the hero made a new banner together and hung it beside the statue",
        "lesson": "Not every strange sight is trouble; some surprises are made with care",
        "ending": "the statue stood clean again, with a cheerful banner fluttering at its feet",
        "question": "Why did the child cover the statue in bacon colors?",
        "answer": "The child meant it as a surprise gift to cheer the city, not as a prank.",
    },
    {
        "problem": "Smoke rose from the bakery and made the block nervous",
        "stake": "If the fire alarm kept ringing, the whole street would panic",
        "temptation": "remove the alarm battery and ignore the problem",
        "clue": "the smoke smelled like bacon, not burning wood",
        "action": "They opened the vents, lifted the tray with oven mitts, and waved the smoke out with a cape",
        "twist": "the alarm had not found fire; it had only spotted bacon sizzling too close to the sensor",
        "reconciliation": "the baker thanked the hero, the angry neighbors calmed down, and the same bacon became breakfast for everyone",
        "lesson": "A calm rescue can turn fear into a shared meal",
        "ending": "warm rolls and safe laughter filled the bakery while the alarm rested in silence",
        "question": "What did the smoke smell like?",
        "answer": "It smelled like bacon, which meant the problem was breakfast, not a dangerous fire.",
    },
    {
        "problem": "A parade balloon snagged on a sign above the avenue",
        "stake": "The crowd could lose the whole celebration if the balloon burst",
        "temptation": "climb too fast and yank the sign loose",
        "clue": "the balloon string was tied around a bacon box used as a weight",
        "action": "They lowered the sign, removed the heavy box, and guided the balloon down with a gentle tug",
        "twist": "the bacon box had been left there by mistake to hold the string, not to cause mischief",
        "reconciliation": "the parade helper and the sign painter laughed together and fixed the float before the band returned",
        "lesson": "Careful hands can repair an accident without blaming a friend",
        "ending": "the balloon bobbed above the avenue like a bright orange moon",
        "question": "Why was the balloon stuck?",
        "answer": "The balloon was stuck because its string had been tied around a bacon box weight.",
    },
    {
        "problem": "The city's rooftop garden had ants marching toward the tomato patch",
        "stake": "The plants would be ruined if the ants kept coming",
        "temptation": "spray everything and remove every bug",
        "clue": "the ants were following crumbs from a bacon sandwich dropped by a gardener",
        "action": "They swept the crumbs away, placed the sandwich in a sealed tin, and built a tiny bridge for the ants to leave",
        "twist": "the gardener had not ignored the ants; she had dropped lunch while saving seedlings from wind",
        "reconciliation": "the gardener and the hero made a plan for covered lunches and safer plant boxes",
        "lesson": "Solving a problem well means protecting both the garden and the people in it",
        "ending": "the tomatoes swayed safely while the ants marched away from the roof",
        "question": "What were the ants following?",
        "answer": "The ants were following crumbs from a bacon sandwich.",
    },
    {
        "problem": "A subway station lost power and the platform went dark",
        "stake": "Passengers needed light to find the train doors",
        "temptation": "fly ahead alone and remove the fuse without checking it",
        "clue": "the control box was sticky with bacon grease from a lunch break",
        "action": "They wiped the box clean, reset the fuse, and guided people with a glowing wristband",
        "twist": "the fuse was fine; the grease had only blocked the switch from closing",
        "reconciliation": "the station guard, the lunch cook, and the hero all apologized at once and laughed at the same time",
        "lesson": "Sometimes the fix is simple once everyone slows down",
        "ending": "the train lights came back on and the platform shone like a tunnel of stars",
        "question": "What stopped the switch from closing?",
        "answer": "Bacon grease on the control box blocked the switch.",
    },
    {
        "problem": "A museum costume display had one missing mask",
        "stake": "The exhibit would look unfinished for visiting children",
        "temptation": "take the spare mask and keep it as a trophy",
        "clue": "the lost mask was found under a tray of bacon-shaped cookies in the staff room",
        "action": "They returned the mask, cleaned the tray, and placed a note beside the exhibit",
        "twist": "the curator had moved the mask to protect it from paint dust and forgotten to say so",
        "reconciliation": "the curator, the guard, and the hero all smiled when the children read the note aloud",
        "lesson": "Clear words can stop worry before it grows",
        "ending": "the masks stood in a neat row while the children pointed and laughed in delight",
        "question": "Where was the missing mask found?",
        "answer": "It was found under a tray of bacon-shaped cookies in the staff room.",
    },
]

OPENINGS = [
    "A blue morning opened over the city and the windows shone like polished shields",
    "At noon, the streets buzzed while capes snapped in the wind",
    "By sunset, the block was bright with sirens, signs, and summer heat",
    "Early light touched the towers, and the hero watch on the roof began to tick",
]

DIALOGUE_LINES = [
    "{hero} said, 'We can fix this without making it worse.'",
    "{sidekick} answered, 'Then let's slow down and look for the real cause.'",
    "{citizen} said, 'I was worried, but now I can help.'",
    "{hero} replied, 'Thank you. A good rescue needs more than speed.'",
    "{sidekick} said, 'Maybe the answer is hidden in plain sight.'",
    "{citizen} smiled, 'I know who left that here, and I can explain.'",
]

RESOLUTION_LINES = [
    "{hero} nodded and said, 'Let's make things right together.'",
    "{sidekick} laughed softly and said, 'That sounds like a better kind of hero work.'",
    "{citizen} said, 'I feel better already now that we talked.'",
    "{hero} answered, 'No one needs to stay upset when we can fix it side by side.'",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with bacon, removal, twists, and reconciliation.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--citizen", choices=CITIZEN_NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
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
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    citizen = args.citizen or rng.choice(CITIZEN_NAMES)
    setting = args.setting or rng.choice(SETTINGS)
    if hero == sidekick or hero == citizen or sidekick == citizen:
        raise StoryError("Hero, sidekick, and citizen must be different characters.")
    return StoryParams(
        hero=hero,
        sidekick=sidekick,
        citizen=citizen,
        setting=setting,
        bacon="bacon grease",
        remove="remove the bacon grease",
        twist_index=rng.randrange(len(TWISTS)),
    )


def choose(rng: random.Random, options: list[str], **values: str) -> str:
    return rng.choice(options).format(**values)


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(name=params.hero, kind="hero"),
        sidekick=Entity(name=params.sidekick, kind="sidekick"),
        citizen=Entity(name=params.citizen, kind="citizen"),
    )


def simulate(world: World) -> None:
    p = world.params
    t = TWISTS[p.twist_index]
    rng = random.Random(p.seed)
    world.facts["setting"] = p.setting
    world.facts["bacon"] = p.bacon
    world.facts["remove"] = p.remove
    world.facts["twist"] = "twist"
    world.facts["reconciliation"] = "reconciliation"

    world.hero.memes["duty"] = 1.0
    world.sidekick.memes["care"] = 1.0
    world.citizen.memes["worry"] = 1.0

    opening = choose(rng, OPENINGS)
    world.say(f"{opening}. {p.hero} watched over {p.setting} with {p.sidekick}, ready for any trouble.")
    world.say(f"{t['problem']}. {t['stake']}.")
    world.para()

    world.say(f"{p.hero} saw the mess and thought about how to {p.remove}.")
    world.say(f"{p.sidekick} said, 'Slow down. We should ask what really happened.'")
    world.say(f"{p.citizen} added, 'I can tell you what I saw.'")
    world.say(f"{p.hero} replied, 'Good. Talking first will help us fix it the right way.'")
    world.say(f"{p.hero} almost chose to {t['temptation']}, but the warning from {p.sidekick} changed the plan.")
    world.para()

    world.say(f"Together they followed a clue: {t['clue']}.")
    world.say(f"{t['action']}.")
    world.say(f"Then came the twist: {t['twist']}.")
    world.say(f"{p.sidekick} said, 'Oh! That changes everything.' {p.hero} answered, 'It does, and now we can help instead of blame.'")
    world.para()

    world.say(f"That led to reconciliation. {t['reconciliation']}.")
    world.say(f"{choose(rng, RESOLUTION_LINES, hero=p.hero, sidekick=p.sidekick, citizen=p.citizen)}")
    world.say(f"In the end, {t['ending']}.")
    world.say(f"{p.hero} learned that {t['lesson']}.")
    world.facts["resolved"] = True
    world.hero.memes["confidence"] = 1.0
    world.sidekick.memes["relief"] = 1.0
    world.citizen.memes["trust"] = 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    t = TWISTS[params.twist_index]
    prompts = [
        f"Write a superhero story about {params.hero} who must {params.remove} at {params.setting}.",
        f"Tell a child-friendly tale with bacon, a twist, and reconciliation.",
        f"Make a short action story where {params.sidekick} helps {params.hero} solve {t['problem'].lower()}.",
    ]
    story_qa = [
        QAItem(question=f"What did {params.hero} need to remove?", answer=f"{params.hero} needed to {params.remove}."),
        QAItem(question=f"What problem first appeared at {params.setting}?", answer=t["problem"] + "."),
        QAItem(question="What clue changed the hero's thinking?", answer=f"The clue was that {t['clue']}." if not t["clue"].endswith(".") else f"The clue was that {t['clue']}"),
        QAItem(question="What was the twist in the story?", answer=f"The twist was that {t['twist']}." if not t["twist"].endswith(".") else f"The twist was that {t['twist']}"),
        QAItem(question="How did reconciliation happen?", answer=f"Reconciliation happened when {t['reconciliation']}."),
    ]
    world_qa = [
        QAItem(question="What is a superhero story?", answer="A superhero story is a tale about a character who uses special courage or powers to help others."),
        QAItem(question="What does reconcile mean?", answer="To reconcile means to make peace again after a problem or misunderstanding."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprising turn that changes what the characters thought was happening."),
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
    for ent in [world.hero, world.sidekick, world.citizen]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:10} ({ent.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "superhero_story"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("seed_word", "bacon"),
            asp.fact("seed_word", "remove"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Bolt", sidekick="Pip", citizen="Mara", setting="the downtown square", twist_index=0, seed=101),
    StoryParams(hero="Spark", sidekick="Jade", citizen="Ollie", setting="the market street", twist_index=2, seed=202),
    StoryParams(hero="Nova", sidekick="Tess", citizen="Iris", setting="the rooftop garden", twist_index=4, seed=303),
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
