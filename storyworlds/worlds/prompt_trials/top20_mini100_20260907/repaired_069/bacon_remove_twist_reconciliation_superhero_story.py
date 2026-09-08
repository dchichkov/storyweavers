#!/usr/bin/env python3
"""Tiny superhero stories about bacon, removal, a twist, and reconciliation."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Captain Crisp"
    sidekick: str = "Zip"
    rival: str = "The Twist"
    place: str = "City Hall"
    scene: int = 0
    twist: int = 0
    reconciliation: int = 0
    opening: int = 0
    rescue: int = 0
    ending: int = 0


HEROES = ["Captain Crisp", "Beacon Kid", "Star Spoon", "Bolt Bunny"]
SIDEKICKS = ["Zip", "Milo", "Pip", "Nova"]
RIVALS = ["The Twist", "Captain Curl", "Dr. Spin", "Lady Loop"]
PLACES = ["City Hall", "the Harbor", "Pancake Plaza", "Sky Bridge"]

OPENINGS = [
    "At {place}, {hero} watched the morning crowd hurry past the statues.",
    "Near {place}, {hero} and {sidekick} heard a siren and saw the sky go orange.",
    "The day began in {place}, where {hero} kept a careful watch from a rooftop.",
    "Before lunch, {hero} arrived at {place} with {sidekick} by their side.",
]

SCENES = [
    {
        "premise": "A lunch delivery drone had dropped a crate of bacon right into the fountain.",
        "problem": "The slick crate blocked the water and splashed everyone nearby.",
        "dialogue": "{sidekick} said, 'We should remove the crate before it sinks.' {hero} answered, 'Easy. I have a plan.'",
        "clue": "The fountain rim had a hidden pulley hook that could lift the crate safely.",
        "action": "{hero} clipped the hook, {sidekick} tied the rope, and together they lifted the bacon crate: heave, ho!",
        "result": "The fountain flowed again, and the delivery drone could land without trouble.",
        "ending": "By sunset, the bacon crate was removed and the water shone like a silver cape.",
        "object": "bacon crate",
    },
    {
        "premise": "A giant bacon billboard had blown loose above the train station.",
        "problem": "It swung over the tracks like a flashing shield and scared the crowd.",
        "dialogue": "{rival} laughed, 'No one can remove that sign.' {hero} said, 'Watch the twist in the cable.'",
        "clue": "The left cable was tangled around a vent, but the right cable was loose and low.",
        "action": "{hero} used a rooftop twist to turn the sign flat while {sidekick} guided the crowd away: whoosh!",
        "result": "The billboard settled onto the roof, and the train rolled through safely.",
        "ending": "The station lights glowed under a calm sign that no longer dangled over the rails.",
        "object": "billboard",
    },
    {
        "premise": "At the bakery fair, a bacon mascot costume had a stuck zipper and could not move.",
        "problem": "The crowd worried the performer would miss the hero parade.",
        "dialogue": "{sidekick} asked, 'Can you remove the costume panel?' {rival} muttered, 'That looks too tricky.'",
        "clue": "A side seam could twist open if the costume buttons were lined up first.",
        "action": "{hero} turned the seam, {sidekick} held the zipper, and the mascot stepped free: zip, snap!",
        "result": "The performer waved to the children and joined the parade in time.",
        "ending": "The bacon mascot marched beside the heroes with a bright, grateful wave.",
        "object": "mascot costume",
    },
    {
        "premise": "A fog machine had filled the park with a bacon-scented cloud from a broken festival cart.",
        "problem": "The sticky fog hid the playground and made little kids cough.",
        "dialogue": "{rival} said, 'Just remove the cart and be done.' {hero} replied, 'First we need to twist the valve shut.'",
        "clue": "The valve would stop hissing if it was turned a half twist left.",
        "action": "{hero} twisted the valve while {sidekick} opened the cart hatch and pulled the power plug: click!",
        "result": "The fog thinned, the playground reappeared, and the children cheered.",
        "ending": "A clear blue sky returned above the park swings and the quiet cart.",
        "object": "festival cart",
    },
    {
        "premise": "A bacon snack truck had rolled into the fountain square with its brakes locked.",
        "problem": "It sat crooked on the steps and blocked the hero walk.",
        "dialogue": "{sidekick} said, 'Maybe we can remove the wheel block.' {hero} nodded, 'And I see a safer twist.'",
        "clue": "One tire rested on a wooden wedge that could be nudged out from the side.",
        "action": "{hero} twisted the steering wheel, {sidekick} pulled the wedge, and the truck rolled straight: rumble!",
        "result": "The truck parked safely at the curb, and the square opened for the parade.",
        "ending": "The heroes stood in the center of the square with the bacon truck safely out of the way.",
        "object": "snack truck",
    },
]

TURNS = [
    "The twist was not a trick villain at all; it was a broken cable that bent the whole scene out of shape.",
    "The twist came when the heroes learned the problem was smaller than it looked and needed gentler hands.",
    "The twist was that the crowd already had a solution, but nobody had listened long enough to hear it.",
    "The twist was simple: the loudest plan was not the best plan, and a calm one worked faster.",
]

RECONCILIATIONS = [
    "{rival} frowned, then said, 'I was wrong to laugh. Thank you for showing me how to help.'",
    "{rival} lowered the chin. 'I should not have mocked your plan. Can I help finish the job?'",
    "{rival} took off the cape and said, 'That was a good rescue. I want to make it right.'",
    "{rival} looked at {hero} and admitted, 'I made it harder by being proud. Let's do it your way.'",
]

ENDINGS = [
    "The city felt safe again, and the heroes shared bacon sandwiches beside the clean-up crew.",
    "The crowd cheered, and the day ended with bright lights, warm smiles, and one tidy street.",
    "The heroes flew home under the stars, happy that the trouble had been removed without harm.",
    "The square grew quiet again, and the team left behind a better, kinder, steadier city.",
]

ASP_RULES = r"""
#show lesson/1.
#show reconciliation/2.
#show twist/1.

lesson(helping_is_better_than_mocking) :- resolved(_).
reconciliation(H, R) :- hero(H), rival(R), sorry(R).
twist(T) :- revealed(T).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "captain_crisp"),
            asp.fact("hero", "beacon_kid"),
            asp.fact("rival", "the_twist"),
            asp.fact("rival", "captain_curl"),
            asp.fact("sorry", "the_twist"),
            asp.fact("revealed", "broken_cable"),
            asp.fact("resolved", "bacon_problem"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: bacon, remove, twist, and reconciliation.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--scene", type=int, choices=range(len(SCENES)))
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        rival=args.rival or rng.choice(RIVALS),
        place=args.place or rng.choice(PLACES),
        scene=args.scene if args.scene is not None else rng.randrange(len(SCENES)),
        twist=rng.randrange(len(TURNS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
        opening=rng.randrange(len(OPENINGS)),
        rescue=rng.randrange(len(SCENES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="sidekick", label=params.sidekick))
    rival = world.add(Entity(id=params.rival, kind="character", type="villain", label=params.rival))
    scene = SCENES[params.scene % len(SCENES)]

    hero.meters["courage"] = 9.0
    sidekick.meters["quickness"] = 7.0
    rival.memes["pride"] = 6.0
    rival.memes["shame"] = 0.0

    common = {"hero": hero.id, "sidekick": sidekick.id, "rival": rival.id, "place": params.place}
    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**common))
    world.say(scene["premise"])
    world.say(scene["problem"])
    world.say(scene["dialogue"].format(**common))
    world.say(TURNS[params.twist % len(TURNS)])
    world.say(scene["clue"])
    world.say(scene["action"].format(**common))
    world.say(scene["result"])
    world.say(RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)].format(**common))
    world.say(f"The lesson was clear: bacon problems can be removed, but pride should be removed too.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.say(scene["ending"])

    rival.memes["pride"] = 1.0
    rival.memes["shame"] = 4.0
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        rival=rival,
        scene=scene,
        lesson="helping_is_better_than_mocking",
        resolved=True,
        removed_object=scene["object"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story where {f['hero'].id} and {f['sidekick'].id} remove a bacon-related problem at {f['scene']['object']}.",
        f"Tell a child-friendly comic-style tale with {f['rival'].id}, a twist, and a reconciliation at the end.",
        "Write an upbeat superhero story with a clear rescue, spoken dialogue, and a closing image that shows what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    rival = f["rival"]
    scene = f["scene"]
    return [
        QAItem(
            question="What problem did the heroes face?",
            answer=f"They faced {scene['problem'].lower()}",
        ),
        QAItem(
            question="What twist changed the way they solved it?",
            answer=TURNS[0],
        ),
        QAItem(
            question=f"What did {hero.id} and {sidekick.id} do together?",
            answer=scene["action"].format(hero=hero.id, sidekick=sidekick.id, rival=rival.id),
        ),
        QAItem(
            question="How did the story show reconciliation?",
            answer=f"{rival.id} admitted the mistake and offered to help instead of mocking the heroes.",
        ),
        QAItem(
            question="What was removed by the end of the story?",
            answer=f"The story removed the {scene['object']} problem and the danger that came with it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how the reader understands what is happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting or feeling upset and make peace again.",
        ),
        QAItem(
            question="Why do superhero stories often include teamwork?",
            answer="Teamwork lets different helpers use different strengths to solve a bigger problem safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    py = {("Captain Crisp", "The Twist")}
    model = asp.one_model(asp_program("#show reconciliation/2."))
    cl = set(asp.atoms(model, "reconciliation"))
    if cl == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(cl))
    print("  python:", sorted(py))
    return 1


CURATED = [
    StoryParams(hero="Captain Crisp", sidekick="Zip", rival="The Twist", place="City Hall", scene=0, opening=0, twist=0, reconciliation=0, ending=0),
    StoryParams(hero="Beacon Kid", sidekick="Nova", rival="Captain Curl", place="the Harbor", scene=1, opening=1, twist=1, reconciliation=1, ending=1),
    StoryParams(hero="Star Spoon", sidekick="Milo", rival="Dr. Spin", place="Pancake Plaza", scene=2, opening=2, twist=2, reconciliation=2, ending=2),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reconciliation/2.\n#show twist/1."))
    return sorted(set(asp.atoms(model, "reconciliation")))


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
        print(asp_program("#show reconciliation/2.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested reconciliation facts")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero}: superhero story"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
