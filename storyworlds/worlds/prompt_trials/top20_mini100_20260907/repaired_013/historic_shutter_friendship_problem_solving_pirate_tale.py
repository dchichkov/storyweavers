#!/usr/bin/env python3
"""
A tiny pirate tale world about an old shuttered harbor, friendship, and careful
problem solving.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    harbor: str = "the old harbor"
    hero: str = "Mina"
    friend: str = "Jory"
    captain: str = "Captain Reed"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    harbor: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]


HARBOR_REGISTRY = {
    "the old harbor": {"tags": {"historic", "shutter", "pirate"}, "mood": "windy and worn"},
    "the shuttered quay": {"tags": {"historic", "shutter", "pirate"}, "mood": "creaky and gray"},
    "the lantern dock": {"tags": {"historic", "shutter", "pirate"}, "mood": "salt-bright and narrow"},
}


@dataclass(frozen=True)
class PirateArc:
    title: str
    premise: str
    problem: str
    choice: str
    action: str
    result: str
    ending: str
    problem_answer: str
    choice_answer: str
    result_answer: str


PIRATE_ARCS = [
    PirateArc(
        title="The Shutter That Would Not Open",
        premise="At the edge of the harbor stood a historic shutter that hid the only safe path to the quay.",
        problem="A tide of tangled ropes pressed the shutter shut, and a stranded crab clicked for help on the other side.",
        choice="{hero} wanted to kick the shutter open, but {friend} said, \"Let's think first and spare the wood.\"",
        action="They counted the ropes, tied them into one loop, and used the loop like a handle to lift the jammed shutter.",
        result="The shutter swung wide without breaking, and the crab skittered to safety with a grateful snap of its claws.",
        ending="the old shutter rested open at sunset while the crab waved from a dry stone and the tide slipped gently by",
        problem_answer="The shutter was jammed by tangled ropes, and a stranded crab was trapped beyond it.",
        choice_answer="The friends chose careful thinking instead of forcing the shutter open.",
        result_answer="By counting and looping the ropes, they opened the shutter safely and freed the crab.",
    ),
    PirateArc(
        title="The Map Behind the Boards",
        premise="A historic shutter covered a barnacled wall where the captain swore a lost map was hidden.",
        problem="Rainwater soaked the boards, and every hard tug only made the nails groan louder.",
        choice="When {captain} demanded speed, {friend} whispered, \"Friendship first; we can solve this without wrecking the dock.\"",
        action="The pair used a spoon, a rope, and a careful pull in turn, easing each nail loose one by one.",
        result="Behind the boards they found the map, dry as parchment and twice as cheerful as the captain expected.",
        ending="the lantern on the pier shone over a neat row of bent nails and a map held safe in two hands",
        problem_answer="Rain had swollen the boards and hidden the map behind a shuttered wall.",
        choice_answer="The friends agreed to work carefully together instead of rushing or breaking the dock.",
        result_answer="Their patient, step-by-step work freed the map without damage.",
    ),
    PirateArc(
        title="The Bell Rope in the Wind",
        premise="A shuttered bell tower watched over the harbor, and its rope had frayed into three useless strands.",
        problem="Without the bell, the dockhands could not warn boats away from the rocks when fog rolled in.",
        choice="{hero} reached for a knife, but {friend} said, \"Wait—let's braid the strands instead of cutting them away.\"",
        action="They braided the rope with steady fingers, then tested it by ringing the bell once for the gulls and once for the crew.",
        result="The bell rang clear, and every boat turned away from the rocks before the fog could swallow them.",
        ending="a bright bell note floated over the water while the repaired rope swung like a sailor's grin",
        problem_answer="The bell rope had frayed, so the harbor had no warning signal in the fog.",
        choice_answer="The friends chose to braid and repair the rope rather than cut it.",
        result_answer="Their repair restored the warning bell and kept the boats safe.",
    ),
    PirateArc(
        title="The Barrel and the Narrow Door",
        premise="A historic shuttered storehouse held a barrel of fresh apples for the whole crew.",
        problem="The barrel rolled sideways and wedged itself in a narrow door, blocking both the apples and the way out.",
        choice="{captain} barked for a shove, but {hero} answered, \"Let's roll it back with boards and save the fruit.\"",
        action="Using two planks and a bit of chalk, they marked the barrel's path, then nudged it back inch by inch.",
        result="The barrel rolled free, the apples stayed unbruised, and the crew cheered as if the sea itself had applauded.",
        ending="red apples sat safe beside the open door, and not a single one wore a bruise",
        problem_answer="A barrel of apples was stuck in a narrow door and blocked the storehouse.",
        choice_answer="The friends chose a careful plan with boards instead of a rough shove.",
        result_answer="Their measured rolling freed the barrel without ruining the apples.",
    ),
    PirateArc(
        title="The Seal on the Captain's Chest",
        premise="An old chest sat behind a shutter in the captain's cabin, sealed with wax and a stubborn brass clasp.",
        problem="The clasp would not budge, and the crew feared the chest held the only spare sail.",
        choice="Rather than pry at it, {friend} said, \"Ask the cabin key, and listen to where the hinge complains.\"",
        action="They followed the squeak of the hinge, found a hidden key under the mat, and opened the chest with one calm turn.",
        result="Inside lay the spare sail, folded neat and ready for the next storm.",
        ending="the chest stood open like a smiling mouth while the spare sail fluttered once in the cabin breeze",
        problem_answer="The captain's chest was sealed shut, and the crew needed the spare sail inside it.",
        choice_answer="The friends chose to search carefully and listen instead of prying the chest open.",
        result_answer="Their careful search found the key and safely opened the chest.",
    ),
    PirateArc(
        title="The Shuttered Lighthouse Window",
        premise="A lighthouse window had been shuttered since an old storm, leaving the lamp half-blind to the sea.",
        problem="Each wave threw salt against the boards, and the lamp's beam slipped too low for the ships to see.",
        choice="{hero} wanted to climb and hammer, but {friend} said, \"Let's clean the glass first and see what the storm damaged.\"",
        action="They scrubbed the salt away, straightened one bent latch, and opened the shutters just enough for the lamp to breathe.",
        result="The beam leaped over the waves, and two cargo ships found the channel by its bright line.",
        ending="the lighthouse flashed gold across the harbor while the cleaned window shone like a new coin",
        problem_answer="The lighthouse window was shuttered and salty, so the lamp could not guide ships well.",
        choice_answer="The friends chose to inspect and clean the window before trying any repairs.",
        result_answer="Their careful cleaning and adjustment restored the beam and guided the ships.",
    ),
    PirateArc(
        title="The Hidden Dock Under the Mats",
        premise="A historic shuttered dock had been covered with mats to keep it dry for the winter.",
        problem="When the mats soaked through, the boards turned slippery and a crate of lantern oil began to slide toward the water.",
        choice="{captain} shouted, \"Grab it!\" but {hero} said, \"Let's make a path and stop the slide together.\"",
        action="The friends laid planks like stepping stones, then guided the crate along the safest route with slow shoves.",
        result="The oil crate reached dry ground, and the dockhands learned a safer way to move heavy things.",
        ending="wet mats hung over the rail while the lantern oil waited safely on dry boards",
        problem_answer="The wet mats made the dock slippery and sent a crate of lantern oil sliding toward the water.",
        choice_answer="The friends decided to make a safe path and work together instead of rushing.",
        result_answer="They guided the crate to dry ground and taught the crew a safer method.",
    ),
    PirateArc(
        title="The Key in the Kelp",
        premise="A shuttered gate at the harbor mouth kept stormwater from flooding the fish stalls.",
        problem="The iron key slipped from the captain's belt and vanished into a slick bed of kelp at low tide.",
        choice="{friend} said, \"We do not need a miracle; we need a patient search.\" {hero} nodded and rolled up their sleeves.",
        action="They combed the kelp with a hook, a basket, and a shared rope until the key glinted in the sun.",
        result="The gate opened just before the next wave, and the fish stalls stayed dry.",
        ending="the recovered key hung from the captain's hand like a tiny silver fish",
        problem_answer="The gate key was lost in kelp, so the harbor gate could not be opened in time.",
        choice_answer="The friends chose a patient search rather than panicking or waiting for luck.",
        result_answer="Their careful search found the key and opened the gate before flooding.",
    ),
    PirateArc(
        title="The Dock Lantern's Lesson",
        premise="A shutter above the dock lantern closed with a wooden peg every night to keep out gulls.",
        problem="One evening the peg stuck, and the lantern's flame grew faint inside the dark shutter.",
        choice="{hero} reached to yank the peg, but {friend} said, \"First check the grain of the wood, mate.\"",
        action="They twisted the peg with oil, then eased the shutter open just enough to let the flame catch the wind.",
        result="The lantern brightened, and the whole dock glowed safe for sailors returning home.",
        ending="the lantern burned steady beneath the half-open shutter while gulls circled far above",
        problem_answer="The stuck peg trapped the lantern flame inside the shutter.",
        choice_answer="The friends chose to inspect the wood and use oil instead of yanking the peg.",
        result_answer="Their careful repair let the lantern burn brightly again.",
    ),
    PirateArc(
        title="The Rooftop in the Rain",
        premise="A row of shuttered windows looked down on the harbor tavern where rain leaked through the roof.",
        problem="Buckets filled fast, and the tavern keeper feared the old beams would sag by morning.",
        choice="Instead of boasting, {hero} and {friend} asked the keeper where the drips began and listened to every tap.",
        action="They traced each leak to a cracked seam, then patched the roof with tar, cloth, and a steady hand.",
        result="The rain stayed outside, the buckets emptied, and the tavern keeper laughed with relief.",
        ending="steam rose from dry floorboards while the shuttered windows reflected a calm black sea",
        problem_answer="Rain leaks threatened to weaken the tavern roof and flood the room.",
        choice_answer="The friends listened carefully to find the source of each drip.",
        result_answer="Their patches stopped the leaks and saved the tavern from damage.",
    ),
]


OPENINGS = [
    "On a windy morning at {harbor}, {hero} and {friend} came walking like true shipmates.",
    "Long ago at {harbor}, the sea knew the names of {hero}, {friend}, and {captain}.",
    "The docks of {harbor} kept a historic secret, and {hero} with {friend} were the first to test it.",
    "In the old pirate days, {hero} and {friend} crossed {harbor} with a clever grin and a shared plan.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.harbor, params.hero, params.friend, params.captain))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: PirateArc = f["arc"]
    opening = _fill(OPENINGS[f["prose_variant"]], f)
    premise = _fill(arc.premise, f)
    problem = _fill(arc.problem, f)
    choice = _fill(arc.choice, f)
    action = _fill(arc.action, f)
    result = _fill(arc.result, f)
    ending = _fill(arc.ending, f)
    captain = _sentence_start(f["captain"])
    theme = "friendship and problem solving"

    structures = [
        [
            f"{opening} This was the tale of \"{arc.title}.\"",
            f"{premise} {problem}",
            f"{captain} watched and frowned. {choice}",
            action,
            f"{result} The captain said, \"A sharp mind can sail farther than a sharp boot.\"",
            f"By dusk, {ending}. The harbor remembered {theme}.",
        ],
        [
            opening,
            f"\"What do we do now?\" asked {f['friend']}. {premise}",
            _sentence_start(problem),
            f"{captain} called out from the pier. {choice}",
            f"They answered together, and {action[0].lower() + action[1:]}",
            f"{result} After that, every deckhand at {f['harbor']} talked about {theme} with respect.",
        ],
        [
            f"The old sailors still tell \"{arc.title},\" and they start with a shutter at {f['harbor']}.",
            premise,
            f"Then trouble came. {problem}",
            f"\"Let's solve it,\" said {f['hero']}. {choice}",
            f"With care and teamwork, {action[0].lower() + action[1:]}",
            f"{result} So the lesson stayed simple: {ending}.",
        ],
        [
            f"{opening} They did not expect a simple shutter to test their nerve.",
            f"The trouble appeared first. {problem}",
            f"Only then did {f['captain']} explain the old rule: {premise[0].lower() + premise[1:]}",
            choice,
            f"{f['friend']} asked, \"Will that keep everyone safe?\" {f['hero']} nodded, and {action[0].lower() + action[1:]}",
            f"Their answer showed in what changed: {result[0].lower() + result[1:]}",
            f"No gold was won. Instead, {ending}. That is why children remember {theme}.",
        ],
        [
            f"\"Easy does it,\" {f['friend']} told {f['hero']} beside the waves.",
            f"In those days, {premise[0].lower() + premise[1:]} But {problem[0].lower() + problem[1:]}",
            f"Many pirates would have rushed. These two did not. {choice}",
            action,
            f"{captain} laughed in relief. {result} \"Well done, shipmates,\" he said.",
            f"The proof remained after the shouting faded: {ending}.",
        ],
        [
            f"The ending of \"{arc.title}\" can still be seen from the pier: {ending}.",
            f"The pier remembers {f['hero']} and {f['friend']}. {opening}",
            f"Their journey mattered because {premise[0].lower() + premise[1:]} Soon, {problem[0].lower() + problem[1:]}",
            f"{captain} asked, \"What comes first: pride, or helping your crew?\" {choice}",
            action,
            f"{result} That is why the story means {theme}, not bragging.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
harbor(old_harbor).
harbor(shuttered_quay).
harbor(lantern_dock).

feature(friendship).
feature(problem_solving).

can_tell_story(H) :- harbor(H).
can_tell_story(H) :- harbor(H), feature(friendship), feature(problem_solving).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for h in HARBOR_REGISTRY:
        key = h.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("harbor", key))
    lines.append(asp.fact("feature", "friendship"))
    lines.append(asp.fact("feature", "problem_solving"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale story world with historic shutters.")
    ap.add_argument("--harbor", choices=list(HARBOR_REGISTRY))
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--captain")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    harbor = args.harbor or rng.choice(list(HARBOR_REGISTRY))
    hero = args.hero or rng.choice(["Mina", "Tess", "Rory", "Nell", "Pip"])
    friend = args.friend or rng.choice(["Jory", "Ada", "Bo", "Lina", "Finn"])
    captain = args.captain or rng.choice(["Captain Reed", "Captain Vale", "Captain June"])
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(harbor=harbor, hero=hero, friend=friend, captain=captain)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    arc = PIRATE_ARCS[seed % len(PIRATE_ARCS)]
    world = World(harbor=params.harbor)
    hero = world.add(Entity(name=params.hero, kind="character", memes={"friendship": 1.0}))
    friend = world.add(Entity(name=params.friend, kind="character", memes={"problem_solving": 1.0}))
    captain = world.add(Entity(name=params.captain, kind="captain", memes={"authority": 1.0}))
    world.add(Entity(name="the historic shutter", kind="object", meters={"closed": 1.0, "wood": 1.0}))
    world.add(Entity(name="the tide", kind="force", meters={"pressure": 1.0}))
    world.facts.update(
        hero=hero.name,
        friend=friend.name,
        captain=captain.name,
        harbor=params.harbor,
        arc=arc,
        prose_variant=(seed // (len(PIRATE_ARCS) * 6)) % len(OPENINGS),
        structure_variant=(seed // len(PIRATE_ARCS)) % 6,
        ending_image=_fill(arc.ending, {"hero": hero.name, "friend": friend.name, "captain": captain.name, "harbor": params.harbor}),
    )
    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a pirate tale about {params.hero} and {params.friend} at {params.harbor}.",
        "Tell a child-facing story where a historic shutter causes trouble and friendship solves it.",
        "Write a short pirate adventure with careful thinking instead of rough force.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} and {params.friend} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="How did they show friendship while solving the problem?",
            answer=arc.choice_answer,
        ),
        QAItem(
            question=f"What was the result of their careful action?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes the story?",
            answer=f"It ends with {world.facts['ending_image']}.",
        ),
    ]
    world_qa = [
        QAItem(question="What is friendship?", answer="Friendship is a caring bond where people help and trust each other."),
        QAItem(question="What is problem solving?", answer="Problem solving is finding a thoughtful way to fix trouble."),
        QAItem(question="What is a shutter?", answer="A shutter is a board or panel that can cover an opening like a window or gate."),
        QAItem(question="What is historic?", answer="Historic means old and important because it belongs to the past."),
        QAItem(question="What is a pirate tale?", answer="A pirate tale is an adventure story about ships, docks, treasure, or sea-going characters."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.name}: kind={e.kind}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
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


def _valid_python() -> list[str]:
    return sorted(s.replace("the ", "").replace(" ", "_") for s in HARBOR_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(s,) for s in _valid_python()}
    cl = set(_asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} harbors).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for harbor in HARBOR_REGISTRY:
            params = StoryParams(harbor=harbor, hero="Mina", friend="Jory", captain="Captain Reed")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = build_story_params(args, rng)
            except StoryError as err:
                print(err)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
