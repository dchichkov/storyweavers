#!/usr/bin/env python3
"""
A small pirate tale about a historic shutter, friendship, and problem solving.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the historic harbor"
    hero: str = "Luna"
    friend: str = "Pip"
    captain: str = "Captain Maris"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the historic harbor": {"tags": {"historic", "shutter", "pirate"}, "mood": "salt-bright and busy"},
    "the old lighthouse island": {"tags": {"historic", "shutter", "pirate"}, "mood": "windy and echoing"},
    "the weathered fort quay": {"tags": {"historic", "shutter", "pirate"}, "mood": "rocky and shadowed"},
}


@dataclass(frozen=True)
class PirateArc:
    title: str
    premise: str
    problem: str
    dialogue: str
    action: str
    result: str
    ending: str
    problem_answer: str
    solution_answer: str
    result_answer: str


ARCS = [
    PirateArc(
        "The Shutter of Seven Bells",
        "At the historic harbor stood a blue shutter that had guarded the oldest map room for a hundred years.",
        "A storm slammed its rusted bar across the door while the tide rose around the dock.",
        '"We can pull harder," said Luna. "Or we can think together," Pip replied.',
        "They studied the hinges, slipped a rope through the shutter slats, and used the tide pole as a lever.",
        "The bar lifted without splintering the old wood, and the map room opened before the tide reached the steps.",
        "the blue shutter gleaming above the harbor while seven bells rang across the water",
        "The rusted bar trapped the historic map room as the storm tide rose.",
        "Luna and Pip solved the problem by studying the hinges and using a rope and tide pole as a lever.",
        "The shutter opened safely, saving the old map room before the rising tide reached it.",
    ),
    PirateArc(
        "The Captain's Crooked Window",
        "A historic shutter on the captain's house showed sailors the safe way through the reef.",
        "Its broken latch left the shutter swinging in the wind, hiding the warning mark from every passing boat.",
        '"If we nail it shut, the mark will vanish," Luna warned. "Then let us make it turn," said Pip.',
        "They tied two short ropes to opposite corners and balanced the shutter so it pointed toward the reef again.",
        "Boats saw the warning in time, and the captain replaced the latch without changing the old carving.",
        "the crooked shutter pointing like a friendly finger toward calm water",
        "A broken latch made the shutter hide the reef warning from passing boats.",
        "The friends balanced the shutter with two ropes so it could still point toward the reef.",
        "The warning became visible again, and boats avoided the dangerous reef.",
    ),
    PirateArc(
        "The Treasure Behind the Shutter",
        "Pirates once hid a kindness chest behind a historic shutter in the harbor wall.",
        "When Luna found the hidden key, the shutter would not open because sand packed its lower hinge.",
        '"Treasure first!" cried Luna. "A stuck door needs patient hands first," said Pip.',
        "They brushed away the sand, warmed the hinge with an oil lamp, and lifted together on the count of three.",
        "The shutter opened to a chest of blankets and food meant for sailors caught in storms.",
        "the friends sharing the chest beneath a shutter marked with a golden heart",
        "Sand and a stiff hinge blocked the shutter hiding the kindness chest.",
        "The friends cleared the sand, warmed the hinge, and lifted together.",
        "They found supplies meant to help storm-tossed sailors and shared them with the harbor.",
    ),
    PirateArc(
        "The Green Shutter Signal",
        "Long ago, a green shutter on the fort tower signaled friendship between two pirate crews.",
        "The signal rope snapped just as a frightened crew approached through the fog.",
        '"They may think we are enemies," said Pip. "Then we will build a new signal," Luna answered.',
        "They hung a green sailcloth outside the shutter and flashed a lantern in the old three-beat pattern.",
        "The visiting crew recognized the friendly sign, lowered their weapons, and helped guide everyone through the fog.",
        "the green cloth fluttering beside the historic shutter as two crews shared one lantern",
        "A snapped rope hid the historic friendship signal from a crew in the fog.",
        "The friends replaced the signal with green sailcloth and the old three-beat lantern pattern.",
        "The crews recognized one another as friends and safely crossed the fog together.",
    ),
    PirateArc(
        "The Shutter and the Sea Chart",
        "A historic shutter protected a sea chart that showed a safe path home.",
        "Rain soaked the chart because the shutter had warped open, and the ship was due to sail at dawn.",
        '"The chart is fading," said Luna. "We can copy its shapes before the rain wins," said Pip.',
        "They pressed cloth against the leak, traced the chart on a clean sail, and wedged the shutter straight with a spar.",
        "The copied route led the ship through calm water, while the old chart dried safely indoors.",
        "the repaired shutter closed over the chart as the ship sailed beneath a pink morning sky",
        "A warped shutter let rain damage the sea chart before the ship's morning departure.",
        "The friends copied the chart, stopped the leak with cloth, and straightened the shutter with a spar.",
        "The ship followed the copied safe route, and the historic chart was saved.",
    ),
    PirateArc(
        "The Harbor Mouse's Door",
        "Behind a tiny historic shutter beneath the pier lived a mouse that kept the sailors company.",
        "A fallen crate pinned the little shutter closed while high waves rushed below.",
        '"We need a small plan," said Pip. "And a small helper," Luna answered as the mouse squeaked.',
        "Luna moved the loose rope, Pip rolled the crate with a barrel, and the mouse tugged a thread from inside.",
        "The shutter sprang open, and the mouse led them to a dry ladder hidden under the pier.",
        "the tiny shutter open at sunset while the mouse shared a crumb with both friends",
        "A crate pinned the mouse's tiny shutter shut as high waves rose beneath the pier.",
        "The friends used a rope, a barrel, and the mouse's tug to move the crate safely.",
        "The mouse was freed and revealed a dry ladder that helped the friends reach safety.",
    ),
    PirateArc(
        "The Lighthouse Shutter Puzzle",
        "The lighthouse keeper trusted a historic shutter puzzle to protect the island's brightest lamp.",
        "Three wooden shutters had fallen together, and nobody knew which one should open first.",
        '"Guessing could break them," said Luna. "The scratches may tell us," said Pip.',
        "They matched old scratch marks, opened the smallest shutter first, and then turned the other two in order.",
        "The lamp shone through the storm, showing a lost boat the way around the rocks.",
        "three shutters resting neatly beside the lighthouse lamp while a grateful boat sailed home",
        "The lighthouse shutters had fallen together, and opening them in the wrong order could break them.",
        "The friends read the old scratch marks and opened the shutters in the marked order.",
        "The lamp shone safely and guided a lost boat around the rocks.",
    ),
    PirateArc(
        "The Shutter of Second Chances",
        "A historic shutter in the harbor jail once opened only when rival sailors solved a puzzle together.",
        "Two angry crews pulled from opposite sides, making the lock tighter.",
        '"Pulling apart is the trouble," said Pip. "Then we shall push toward one answer," said Luna.',
        "The friends asked each crew to name one useful clue, then fitted the clues into the lock's four-turn pattern.",
        "The lock opened, and the sailors left together to repair the storm-broken pier.",
        "the old shutter wide open while former rivals carried planks side by side",
        "Rival sailors tightened the lock by pulling in opposite directions.",
        "The friends gathered clues from both crews and used the four-turn pattern to open the lock.",
        "The sailors became helpers who repaired the pier together.",
    ),
    PirateArc(
        "The Moonlit Shutter",
        "A silver shutter on the historic customs house reflected moonlight toward ships entering the harbor.",
        "Clouds hid the moon, and a loose hinge made the shutter point at the dark sea instead of the channel.",
        '"We cannot command the moon," Luna said. "But we can aim what light we have," said Pip.',
        "They tightened the hinge, hung a polished cooking pan beside the shutter, and waited for a break in the clouds.",
        "A thin moonbeam flashed from the pan and shutter, marking the safe channel for a small boat.",
        "the silver shutter and cooking pan shining together like two stars above the water",
        "Clouds and a loose hinge hid the moonlit signal from a boat entering the harbor.",
        "The friends tightened the hinge and used a polished pan to reflect the first moonbeam.",
        "The reflected light marked the safe channel and guided the boat inside.",
    ),
    PirateArc(
        "The Shutter at Gull Rock",
        "The oldest shutter at Gull Rock carried a carved gull that meant every sailor could ask for help.",
        "A rope ladder snapped, leaving an injured deckhand stranded beside the high shutter.",
        '"We need a bridge, not a boast," said Pip. "Then let us use the sail," said Luna.',
        "They spread a spare sail from the rock to the deck, tied it to the shutter bars, and crawled across one at a time.",
        "The deckhand reached safe ground, and the carved gull became a sign of careful rescue.",
        "the carved gull above the shutter while rescued sailors mended the sail together",
        "A snapped ladder left an injured deckhand stranded beside the high shutter.",
        "The friends made a safe bridge from a spare sail tied to the sturdy shutter bars.",
        "The deckhand reached safety, and the sailors repaired the sail together.",
    ),
]


OPENINGS = [
    "Arrr, in {setting}, Luna and Pip sailed beneath a sky bright as a brass button.",
    "Listen close, matey, for this tale began when Luna and Pip reached {setting} at low tide.",
    "On a morning of salty wind, Luna and Pip came ashore at {setting}.",
    "The harbor folk still tell how Luna and Pip arrived at {setting} with one rope, one lantern, and plenty of courage.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.captain))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    facts = world.facts
    arc: PirateArc = facts["arc"]
    opening = _fill(OPENINGS[facts["opening_variant"]], facts)
    premise = _fill(arc.premise, facts)
    problem = _fill(arc.problem, facts)
    dialogue = _fill(arc.dialogue, facts)
    action = _fill(arc.action, facts)
    result = _fill(arc.result, facts)
    ending = _fill(arc.ending, facts)
    hero = facts["hero"]
    friend = facts["friend"]
    captain = facts["captain"]

    structures = [
        [
            opening,
            f"{premise} Soon, {problem[0].lower() + problem[1:]}",
            dialogue,
            action,
            f"{result} {captain} cheered, \"That is how clever friends save a day!\"",
            f"By sunset, {ending}.",
        ],
        [
            f"{opening} The sailors called the adventure \"{arc.title}.\"",
            premise,
            _start(problem),
            f"\"What would a good crew do?\" asked {hero}. {dialogue}",
            f"They tested the idea carefully. {action} {result}",
            f"After that, {ending}.",
        ],
        [
            f"{opening} {friend} carried the rope while {hero} watched the old buildings.",
            f"The historic place held a secret: {premise[0].lower() + premise[1:]}",
            f"Then trouble rose like a wave. {problem}",
            dialogue,
            f"Instead of blaming one another, the friends made a plan. {action}",
            f"{result} The harbor remembered that problem solving works best when friendship keeps everyone listening.",
            f"At night, {ending}.",
        ],
        [
            f"Whenever sailors sing \"{arc.title},\" they begin with this scene: {opening[0].lower() + opening[1:]}",
            premise,
            f"{captain} pointed toward the trouble. {_start(problem)}",
            f"\"I have an idea,\" said {hero}. {dialogue}",
            action,
            f"The plan changed the harbor. {result}",
            f"No treasure mattered more than the proof: {ending}.",
        ],
        [
            opening,
            f"\"Stay close, matey,\" said {friend}. \"We will solve this together.\" {premise}",
            problem,
            dialogue,
            f"First they listened, then they tried the safest method. {action}",
            f"{result} The captain raised a cup and said, \"To friendship and bright thinking!\"",
            f"The final picture was clear: {ending}.",
        ],
    ]
    return structures[facts["structure_variant"]]


ASP_RULES = r"""
setting(historic_harbor).
setting(old_lighthouse_island).
setting(weathered_fort_quay).

feature(friendship).
feature(problem_solving).
feature(historic).
feature(shutter).
feature(pirate).

can_tell_story(S) :- setting(S), feature(friendship), feature(problem_solving), feature(historic), feature(shutter), feature(pirate).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("friendship", "problem_solving", "historic", "shutter", "pirate"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about a historic shutter, friendship, and problem solving.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--captain")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Nell", "Rook", "Mara", "Jory"])
    friend = args.friend or rng.choice(["Pip", "Tess", "Bo", "Finn", "Kite"])
    captain = args.captain or rng.choice(["Captain Maris", "Captain Coral", "Captain Vale"])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    if not hero.strip() or not friend.strip() or not captain.strip():
        raise StoryError("Hero, friend, and captain names must not be empty.")
    return StoryParams(setting=setting, hero=hero, friend=friend, captain=captain)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)
    hero = world.add(Entity(params.hero, "character", meters={"strength": 0.6}, memes={"friendship": 1.0}))
    friend = world.add(Entity(params.friend, "character", meters={"cleverness": 0.8}, memes={"problem_solving": 1.0}))
    captain = world.add(Entity(params.captain, "captain", meters={"authority": 0.9}, memes={"trust": 0.7}))
    world.add(Entity("the historic shutter", "wooden landmark", meters={"age": 100.0, "stability": 0.4}, memes={"memory": 1.0}))
    world.add(Entity("the harbor tide", "water", meters={"height": 0.7, "danger": 0.5}, memes={"urgency": 0.8}))
    world.add(Entity("the shared rope", "tool", meters={"length": 1.0, "strength": 0.7}, memes={"cooperation": 1.0}))

    facts = {
        "hero": hero.name,
        "friend": friend.name,
        "captain": captain.name,
        "setting": params.setting,
        "arc": arc,
        "opening_variant": (seed // len(ARCS)) % len(OPENINGS),
        "structure_variant": (seed // (len(ARCS) * len(OPENINGS))) % 5,
    }
    world.facts.update(facts)
    story = "\n\n".join(_story_lines(world))

    prompts = [
        f"Write a child-friendly pirate tale about {params.hero}, {params.friend}, and a historic shutter in {params.setting}.",
        "Tell a pirate story where friendship and problem solving repair an old harbor treasure.",
        "Write a gentle adventure in which characters talk, make a plan, and protect a historic shutter.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="How did the friends use problem solving?",
            answer=arc.solution_answer,
        ),
        QAItem(
            question="What changed after the friends worked together?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes the pirate tale of {arc.title}?",
            answer=f"The tale ends with {arc.ending}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a historic object?",
            answer="A historic object is something from the past that people preserve because it helps them remember earlier times.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window or opening that can protect it or control light.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people trust, help, and listen to one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means understanding a difficulty, making a plan, and trying a safe way to improve it.",
        ),
        QAItem(
            question="Why can a pirate crew need teamwork?",
            answer="A pirate crew needs teamwork because shared ideas and careful hands can solve problems that one sailor cannot handle alone.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(f"{entity.name}: kind={entity.kind}, meters={dict(entity.meters)}, memes={dict(entity.memes)}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(setting.replace("the ", "").replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    try:
        py = {(setting,) for setting in _valid_python()}
        clingo_values = set(_asp_valid())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py != clingo_values:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(py - clingo_values))
        print("clingo only:", sorted(clingo_values - py))
        return 1
    rng = random.Random(197402754)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generation verification failed.")
            return 1
    print(f"OK: clingo gate matches python ({len(py)} settings), and generation passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            for item in _asp_valid():
                print(item[0])
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            params = StoryParams(setting=setting, hero="Luna", friend="Pip", captain="Captain Maris", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                if index > max(50, args.n * 50):
                    break
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
