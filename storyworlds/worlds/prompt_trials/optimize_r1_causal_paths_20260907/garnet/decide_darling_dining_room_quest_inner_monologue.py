#!/usr/bin/env python3
"""
A heartwarming dining-room quest about deciding what to do with a lost darling
belonging, while suspense grows and an inner monologue becomes a brave request.
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
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    helper: Item
    dining_room: Item
    lost_item: Item
    quest: str
    problem: str
    solution: str
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    helper_name: str
    problem: str
    solution: str
    voice: str
    seed: Optional[int] = None


NAMES = ["Nora", "Milo", "Lena", "Sam", "Ivy", "Theo", "Pia", "Owen"]
HELPERS = ["Grandma", "Grandpa", "Aunt May", "Uncle Jo", "Dad", "Mom"]
PROBLEMS = ["missing_place_card", "spilled_soup", "silent_music_box", "stormy_window"]
SOLUTIONS = {
    "missing_place_card": ["search_clues", "ask_guest"],
    "spilled_soup": ["repair_table", "share_cleanup"],
    "silent_music_box": ["inspect_key", "ask_owner"],
    "stormy_window": ["secure_latch", "find_curtain_tie"],
}
VOICES = ["thoughtful", "playful", "gentle", "brave"]


ASP_RULES = r"""
#show quest_ready/1.
#show kindness/1.
#show safe/1.

quest_ready(H) :- has_clue(H), makes_plan(H).
kindness(H) :- speaks_honestly(H), helps_someone(H).
safe(H) :- checks_danger(H), gets_help(H).
"""


def _fact(name: str, *args: str) -> str:
    import asp
    return asp.fact(name, *args)


def asp_facts(world: Optional[World] = None) -> str:
    if world is None:
        return "\n".join([
            _fact("has_clue", "hero"),
            _fact("makes_plan", "hero"),
            _fact("speaks_honestly", "hero"),
            _fact("helps_someone", "hero"),
            _fact("checks_danger", "hero"),
            _fact("gets_help", "hero"),
        ])
    facts = world.facts
    return "\n".join([
        _fact("has_clue", "hero") if facts.get("clue") else "",
        _fact("makes_plan", "hero") if facts.get("plan") else "",
        _fact("speaks_honestly", "hero") if facts.get("honest") else "",
        _fact("helps_someone", "hero") if facts.get("helped") else "",
        _fact("checks_danger", "hero") if facts.get("checked") else "",
        _fact("gets_help", "hero") if facts.get("got_help") else "",
    ])


def asp_program(world: Optional[World] = None) -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    names = {sym.name for sym in model}
    expected = {"quest_ready", "kindness", "safe"}
    if expected <= names:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(names))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming dining-room quest about deciding what to do, darling."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution")
    parser.add_argument("--voice", choices=VOICES)
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
    problem = args.problem or rng.choice(PROBLEMS)
    allowed = SOLUTIONS[problem]
    if args.solution is not None and args.solution not in allowed:
        raise StoryError(
            f"Solution {args.solution!r} cannot resolve problem {problem!r}; "
            f"choose one of {', '.join(allowed)}."
        )
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        problem=problem,
        solution=args.solution or rng.choice(allowed),
        voice=args.voice or rng.choice(VOICES),
    )


def build_world(params: StoryParams) -> World:
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown dining-room problem: {params.problem}.")
    if params.solution not in SOLUTIONS[params.problem]:
        raise StoryError(
            f"The solution {params.solution!r} does not fit {params.problem!r}."
        )
    hero = Item(
        "hero", params.name, "character",
        meters={"courage": 0.5, "distance_to_table": 2.0},
        memes={"curiosity": 0.8, "worry": 0.4},
    )
    helper = Item(
        "helper", params.helper_name, "character",
        meters={"distance_to_table": 1.0},
        memes={"patience": 0.9, "trust": 0.8},
    )
    room = Item(
        "dining_room", "dining room", "place",
        meters={"table_length": 2.4, "window_height": 1.6},
        memes={"warmth": 0.8, "suspense": 0.0},
    )
    labels = {
        "missing_place_card": "a pearl-edged place card",
        "spilled_soup": "a blue soup bowl",
        "silent_music_box": "a silver music box",
        "stormy_window": "a little star-shaped candle",
    }
    lost = Item(
        "darling_item",
        labels[params.problem],
        "belonging",
        owner="family",
        meters={"table_distance": 0.0},
        memes={"meaning": 0.9},
    )
    return World(
        hero=hero,
        helper=helper,
        dining_room=room,
        lost_item=lost,
        quest=f"make the dining room ready before supper",
        problem=params.problem,
        solution=params.solution,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _set_facts(world: World, **facts: object) -> None:
    world.facts.update(facts)


def _missing_place_card(world: World, rng: random.Random) -> str:
    h, helper = world.hero.label, world.helper.label
    card = world.lost_item.label
    hiding = _choice(rng, ["under the folded napkin", "behind the salt cellar", "inside the recipe book"])
    clue = _choice(rng, [
        "a faint line of flour across the table",
        "a pearl glint beside the bread basket",
        "one neat corner showing beneath the linen",
    ])
    plan = _choice(rng, [
        "follow the tiny trail without disturbing the other settings",
        "lift each table piece in order and return it to the same place",
    ])
    if world.solution == "search_clues":
        resolution = (
            f"{h} followed {clue}, used the plan to {plan}, and found {card} {hiding}. "
            f"{helper} helped smooth its bent edge before they placed it beside the warmest chair"
        )
        dialogue = (
            f'"I want to look everywhere at once," said {h}. '
            f'"Then let the clue choose the next place," said {helper}.'
        )
        ending = f"the pearl on the card shone beside the warmest chair, ready to welcome its guest"
    else:
        resolution = (
            f"{h} noticed that the card belonged to the guest who had not arrived, "
            f"so {h} asked {helper} which chair should feel most welcoming; together they found {card} {hiding} "
            f"and set it at that chair"
        )
        dialogue = (
            f'"What if I put it anywhere?" asked {h}. '
            f'"Ask whose smile you are saving a place for," said {helper}.'
        )
        ending = f"the card waited at the chosen chair, with a tiny welcome written beside it"
    _set_facts(
        world, clue=clue, plan=plan, honest=True, helped=True, checked=True,
        got_help=True, discovery=f"{card} was {hiding}", cause="the card had slipped while the table was being set",
        resolution=resolution, ending=ending, object=card,
    )
    lines = [
        f"Before supper, {h} stood in the dining room and saw that {card} was missing.",
        f"The table looked almost ready, but one empty spot made the whole room feel as if it were holding its breath. {h} noticed {clue}.",
        f'{dialogue}',
        f'Inside, {h} thought, "I can decide carefully. I do not have to rush just because the room is quiet."',
        f"{h} began the quest and {resolution}.",
        f'"There you are, darling," whispered {h}, touching the card as gently as a bird feather.',
        f"{helper} smiled. Together they checked every chair, and the suspense softened into the sound of spoons being set down.",
        f"At last, {ending}. The dining room no longer waited sadly; it welcomed everyone home.",
    ]
    return " ".join(lines)


def _spilled_soup(world: World, rng: random.Random) -> str:
    h, helper = world.hero.label, world.helper.label
    bowl = world.lost_item.label
    cloth = _choice(rng, ["a stack of soft napkins", "a clean tea towel", "Grandma's striped cloth"])
    if world.solution == "repair_table":
        resolution = (
            f"{h} moved the salt cellar away, slid {cloth} beneath the tilted leaf, "
            f"and asked {helper} to steady the table while the spill was wiped"
        )
        dialogue = (
            f'"The table is crying soup," said {h}. '
            f'"First steady it, then save the cloth," answered {helper}.'
        )
        ending = "the table stood level again, and the blue bowl held a small, safe serving"
    else:
        resolution = (
            f"{h} admitted the spill had happened, and {helper} joined the cleanup; "
            f"they used {cloth} together and carried the wet setting to the kitchen"
        )
        dialogue = (
            f'"I was afraid you would be upset," said {h}. '
            f'"I am glad you told me, because two pairs of hands are quicker," said {helper}.'
        )
        ending = "the clean table carried a shared bowl, and nobody had to hide the little accident"
    _set_facts(
        world, clue="the table leg was resting on a folded menu", plan="steady the table before wiping",
        honest=True, helped=True, checked=True, got_help=True,
        discovery="the blue soup bowl had spilled because the table leaned",
        cause="a folded menu made one table leg uneven",
        resolution=resolution, ending=ending, object=bowl,
    )
    lines = [
        f"In the dining room, {h} heard a soft slurp and saw {bowl} tipping toward the tablecloth.",
        f"Soup crept across the white cloth. For one suspenseful moment, the spoon floated like a tiny boat.",
        f"{dialogue}",
        f'Inside, {h} thought, "If I tell the truth, we can decide what to do before the soup reaches the floor."',
        f"{resolution}. The spoon stopped swimming.",
        f'"There, darling," said {h} to the rescued bowl. "You may stay on the table, but not on a voyage."',
        f"{helper} laughed, and the dining room filled with the warm smell of bread instead of worry.",
        f"By supper, {ending}. The small spill had become a reason to help one another.",
    ]
    return " ".join(lines)


def _silent_music_box(world: World, rng: random.Random) -> str:
    h, helper = world.hero.label, world.helper.label
    box = world.lost_item.label
    tune = _choice(rng, ["a lullaby", "a waltz", "the song used at birthdays"])
    if world.solution == "inspect_key":
        resolution = (
            f"{h} noticed the winding key was turned too far, loosened it one careful notch, "
            f"and let {helper} place the box on a level napkin"
        )
        dialogue = (
            f'"Should I turn the key again?" asked {h}. '
            f'"Not yet. Listen to what the quiet is telling you," said {helper}.'
        )
        ending = f"the box played {tune} beside the candles, softly enough for every voice to be heard"
    else:
        resolution = (
            f"{h} asked the box's owner what had changed, and {helper} remembered that the box needed "
            f"to be wound gently; the owner showed {h} how to begin"
        )
        dialogue = (
            f'"I do not know why you stopped," said {h} to the box. '
            f'"Ask the one who knows your song," suggested {helper}.'
        )
        ending = f"the owner wound the box with {h}, and {tune} filled the room like a small golden thread"
    _set_facts(
        world, clue="the key felt tight instead of loose", plan="pause and inspect before turning",
        honest=True, helped=True, checked=True, got_help=True,
        discovery="the music box needed either a careful reset or its owner's familiar touch",
        cause="the winding key had been handled without noticing its limit",
        resolution=resolution, ending=ending, object=box,
    )
    lines = [
        f"At the center of the dining room, {h} found {box} silent before the guests arrived.",
        f"The candles flickered. The chairs waited. Even the clock seemed to lean closer, and suspense sat beneath the table.",
        f"{dialogue}",
        f'Inside, {h} thought, "A quiet box is not a broken box. I can decide after I learn more."',
        f"{resolution}.",
        f'"Thank you, darling," said {h}, resting a hand beside the shining lid.',
        f"The first notes came gently, and {helper} nodded as if the room had just remembered how to breathe.",
        f"At supper, {ending}. The music did not fill the room alone; the smiles did too.",
    ]
    return " ".join(lines)


def _stormy_window(world: World, rng: random.Random) -> str:
    h, helper = world.hero.label, world.helper.label
    candle = world.lost_item.label
    outside = _choice(rng, ["rain tapped hard against the glass", "wind shook the bare branches", "thunder rolled beyond the roof"])
    if world.solution == "secure_latch":
        resolution = (
            f"{h} stepped back from the rattling window, told {helper}, and helped check the lower latch; "
            f"together they secured it with a wooden spoon handle until the wind eased"
        )
        dialogue = (
            f'"The window is frightening me," said {h}. '
            f'"Good deciding begins with getting safe," said {helper}.'
        )
        ending = "the window held firm, and the star candle glowed on the table without trembling"
    else:
        resolution = (
            f"{h} asked where the curtain tie belonged, and {helper} showed how to loop it around the heavy fabric; "
            f"the curtain stopped brushing the candle"
        )
        dialogue = (
            f'"The flame keeps jumping," said {h}. '
            f'"Then let us move the curtain, not blame the flame," said {helper}.'
        )
        ending = "the curtain rested in its tie, and the star candle shone safely over the soup"
    _set_facts(
        world, clue="the curtain was brushing the candle whenever the window shook",
        plan="move back and check the danger before touching it",
        honest=True, helped=True, checked=True, got_help=True,
        discovery="the storm was moving either the latch or the curtain near the candle",
        cause="wind entered through the unsettled window and disturbed the table setting",
        resolution=resolution, ending=ending, object=candle,
    )
    lines = [
        f"Just before supper in the dining room, {h} placed {candle} beside the plates.",
        f"Outside, {outside}. The flame bent low, and the room's warm shadows stretched toward the door.",
        f"{dialogue}",
        f'Inside, {h} thought, "I want the dining room to be beautiful, but safe is the first beautiful thing."',
        f"{resolution}. The suspense loosened with the next quiet breath of wind.",
        f'"Stay bright, darling," {h} whispered to the candle, shielding it only after the danger was gone.',
        f"{helper} brought the bread closer to the table, and the storm became a story heard from indoors.",
        f"At last, {ending}. Everyone ate together while rain stitched silver lines across the dark window.",
    ]
    return " ".join(lines)


BUILDERS = {
    "missing_place_card": _missing_place_card,
    "spilled_soup": _spilled_soup,
    "silent_music_box": _silent_music_box,
    "stormy_window": _stormy_window,
}


def generate_story(world: World, seed: int) -> str:
    rng = random.Random(seed ^ 0x51D1E)
    return BUILDERS[world.problem](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    return [
        QAItem(
            f"What did {h} discover in the dining room?",
            f"{h} discovered that {world.facts['discovery']}.",
        ),
        QAItem(
            "What caused the problem?",
            f"The problem happened because {world.facts['cause']}.",
        ),
        QAItem(
            f"How did {h} decide what to do?",
            f"{h} paused, noticed {world.facts['clue']}, and chose to {world.facts['resolution'].split(';')[0].lower()}.",
        ),
        QAItem(
            "How did the suspense change?",
            "The suspense softened after the characters spoke honestly, checked the danger, and worked together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is it useful to pause before deciding?",
            "Pausing gives someone time to notice clues, consider safety, and choose an action that fits the real problem.",
        ),
        QAItem(
            "Why can asking for help be brave?",
            "Asking for help is brave because it admits what someone does not know and invites another person to solve the problem together.",
        ),
        QAItem(
            "What is suspense?",
            "Suspense is the feeling of wondering what will happen next while a problem remains uncertain.",
        ),
        QAItem(
            "What is a dining room?",
            "A dining room is a place where people gather to prepare, serve, and share meals.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming children's story about deciding what to do in a dining room.",
        f"Tell a suspenseful quest in which {world.hero.label} notices a problem and speaks honestly with {world.helper.label}.",
        "Use an inner monologue, a gentle spoken exchange, and a concrete ending image showing that kindness changed the room.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in [world.hero, world.helper, world.dining_room, world.lost_item]:
        lines.append(
            f"  {item.id:12} {item.kind:10} label={item.label!r} owner={item.owner!r} "
            f"meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  problem={world.problem}")
    lines.append(f"  solution={world.solution}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = ["== Generation prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story QA ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== World QA ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.problem}|{params.solution}|{params.voice}")
    story = generate_story(world, seed)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid(world: Optional[World] = None) -> bool:
    if world is None:
        return True
    return all(world.facts.get(key) for key in ("clue", "plan", "honest", "helped", "checked", "got_help"))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            world = build_world(StoryParams("Nora", "Grandma", "missing_place_card", "search_clues", "thoughtful", 1))
            world.facts.update(clue=True, plan=True, honest=True, helped=True, checked=True, got_help=True)
            model = asp.one_model(asp_program(world))
            shown = sorted(str(atom) for atom in model)
            print("ASP model:", ", ".join(shown))
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Nora", "Grandma", "missing_place_card", "search_clues", "thoughtful", base_seed),
            StoryParams("Milo", "Dad", "spilled_soup", "share_cleanup", "brave", base_seed + 1),
            StoryParams("Lena", "Aunt May", "silent_music_box", "ask_owner", "gentle", base_seed + 2),
            StoryParams("Theo", "Grandpa", "stormy_window", "secure_latch", "careful", base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 25)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.problem}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
