#!/usr/bin/env python3
"""
A cautionary myth about junk, a magical swoosh, and the wisdom of pausing.
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
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str
    helper: str
    elder: str
    place: str
    junk: str
    charm: str
    seed: Optional[int] = None
    variant: int = 0


HERO_NAMES = ["Luna", "Mira", "Orin", "Tavi", "Nia", "Sol"]
HELPER_NAMES = ["Pip", "Ari", "Bram", "Kito", "Fenn", "Uma"]
ELDER_NAMES = ["Grandmother Ash", "Old Rowan", "Mother Reed", "Keeper Sable"]
PLACES = ["the hill of listening stones", "the moonlit ravine", "the valley of seven bells", "the old cedar grove"]
JUNK_ITEMS = ["a bent tin cup", "a cracked wheel", "a bundle of rusty wire", "a broken lantern", "a heap of bottle caps"]
CHARMS = ["the Wind-Calling Shell", "the Blue Feather", "the Little Storm Drum", "the Silver Whistle"]

OPENINGS = [
    "{hero} lived where {place} met the sky, and every dawn taught the stones a new song.",
    "In the days when clouds still answered children, {hero} watched over {place}.",
    "{place} was quiet at sunrise, but {hero} knew that quiet did not always mean safe.",
    "The people of {place} told many myths, yet none began with such an ordinary thing as junk.",
]

CAUTION_LINES = [
    '"Wait," said {helper}. "A strange sound is not an invitation to touch."',
    '"Let us look before we leap," {helper} warned. "Even a small object may carry a large promise."',
    '{helper} lifted a hand. "The swoosh is loud, but loudness is not wisdom."',
    '"We should ask the elder first," said {helper}. "Caution can be a kind of courage."',
]

LESSONS = [
    "What is thrown away may still hold power, so wisdom begins with careful attention.",
    "A dazzling shortcut can hide a danger; patience protects the eager.",
    "The safest hand is the one that pauses before it grabs.",
    "Wonder is a gift, but caution is the key that keeps wonder from becoming harm.",
]

SCENES = [
    {
        "omen": "a blue spark slipped from the junk and circled the moon",
        "danger": "the junk heap began to spin, pulling loose stones toward the village",
        "cause": "the charm had been wedged beneath the junk, where careless hands had covered it",
        "turn": "Luna noticed that the swoosh grew louder whenever someone hurried closer",
        "fix": "they cleared a quiet path, covered the charm with a clay bowl, and lifted the junk away piece by piece",
        "ending": "When evening came, the charm rested on a clean altar, and the junk was sorted for useful repairs",
    },
    {
        "omen": "a silver swoosh flew from the junk and braided itself through the trees",
        "danger": "the wind began carrying baskets, blankets, and sleeping birds toward the ravine",
        "cause": "the forgotten charm had awakened beneath a pile of metal scraps",
        "turn": "Luna saw that the wind stopped whenever the group stood still",
        "fix": "they stopped chasing the wind, marked a safe circle, and gently uncovered the charm",
        "ending": "The trees became calm again, and the villagers turned the best junk into bird shelters",
    },
    {
        "omen": "the junk whispered whenever the first star appeared",
        "danger": "each whisper called a stronger swoosh until the village roof tiles rattled",
        "cause": "an old charm had been mistaken for rubbish and buried under broken tools",
        "turn": "Luna heard the whisper repeat the same warning: slow hands, clear eyes",
        "fix": "they worked slowly, naming each object before moving it, until the charm could be freed",
        "ending": "The stars shone on a tidy square where every useful scrap had found a new purpose",
    },
]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, str] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary myth about junk and a magical swoosh.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--elder")
    parser.add_argument("--place")
    parser.add_argument("--junk")
    parser.add_argument("--charm")
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


def generate_world(params: StoryParams) -> World:
    world = World(params.place)
    world.add(Entity("hero", "character", params.hero, memes={"curiosity": 0.7, "caution": 0.3}))
    world.add(Entity("helper", "character", params.helper, memes={"caution": 0.8}))
    world.add(Entity("elder", "character", params.elder, memes={"wisdom": 1.0}))
    world.add(Entity("junk", "thing", params.junk, owner="village", meters={"scattered": 0.8}))
    world.add(Entity("charm", "thing", params.charm, meters={"hidden": 1.0}, memes={"magic": 1.0}))
    return world


def tell(world: World, params: StoryParams) -> World:
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0xC0A57)
    scene = SCENES[params.variant % len(SCENES)]
    opening = OPENINGS[params.variant % len(OPENINGS)].format(hero=params.hero, place=params.place)
    caution = CAUTION_LINES[rng.randrange(len(CAUTION_LINES))].format(helper=params.helper)
    lesson = LESSONS[params.variant % len(LESSONS)]

    world.say(opening)
    world.say(f"Near the path lay {params.junk}, and beside it rested a covered basket holding {params.charm}.")
    world.say(f"One morning, {scene['omen']}.")
    world.say(f"{params.hero} stepped toward it, but {params.helper} called out, {caution}")

    world.para()
    world.say(f"The elder, {params.elder}, came slowly from the cedar shade.")
    world.say(f'"That swoosh is a voice from the old days," said {params.elder}. "Before touching the junk, learn what the voice is saying."')
    world.say(f"{params.hero} listened. {scene['turn']}.")
    world.say(f"{params.elder} nodded. " + f'"Good eyes," said {params.elder}. "Now let us discover the cause without making the danger greater."')

    world.para()
    world.say(f"Then the danger arrived: {scene['danger']}.")
    world.say(f"The people wanted to grab the nearest piece of junk, but {params.helper} held them back. " + f'"Do not wrestle the swoosh," said {params.helper}. "Give it room, and follow the clue."')
    world.say(f"{params.hero} noticed that {scene['cause']}.")
    world.say(f"That was the turn of the myth: the frightening swoosh was not a monster at all, but a warning made strong by careless clutter.")
    world.say(f"Together, they {scene['fix']}.")

    world.para()
    world.say(f"The wind softened. The charm glowed once, then became still.")
    world.say(f'"I thought fast hands would make me brave," {params.hero} admitted.')
    world.say(f'"A brave hand can also wait," {params.helper} replied.')
    world.say(f'{params.elder} smiled. "Remember this: {lesson}"')
    world.say(scene["ending"] + ".")
    world.say("From that day onward, the people called the place the Quiet Wind, and no one mistook a warning for a game.")

    junk = world.get("junk")
    charm = world.get("charm")
    junk.meters["scattered"] = 0.0
    junk.meters["sorted"] = 1.0
    charm.meters["hidden"] = 0.0
    charm.meters["safe"] = 1.0
    world.get("hero").memes["caution"] = 1.0
    world.get("helper").memes["courage"] = 0.9
    world.get("elder").memes["wisdom_shared"] = 1.0
    world.fired.update({"warning_heard", "cause_discovered", "swoosh_calmed", "junk_repaired"})

    world.facts = {
        "hero": params.hero,
        "helper": params.helper,
        "elder": params.elder,
        "place": params.place,
        "junk": params.junk,
        "charm": params.charm,
        "omen": scene["omen"],
        "danger": scene["danger"],
        "cause": scene["cause"],
        "turn": scene["turn"],
        "fix": scene["fix"],
        "ending": scene["ending"],
        "lesson": lesson,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a cautionary myth about {facts['hero']} discovering why junk near {facts['place']} must be handled carefully.",
        f"Tell a myth in which a magical swoosh warns {facts['hero']} and {facts['helper']} about {facts['charm']}.",
        f"Write a child-friendly myth with dialogue and the lesson: {facts['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who discovered the warning in the myth?", f"{f['hero']} discovered the warning with help from {f['helper']} and {f['elder']}."),
        QAItem("What strange sign appeared first?", f"The first sign was that {f['omen']}."),
        QAItem("What danger did the swoosh cause?", f"The swoosh caused this danger: {f['danger']}."),
        QAItem("What caused the strange danger?", f"The cause was that {f['cause']}."),
        QAItem("How did the characters make things safe?", f"They made things safe when they {f['fix']}."),
        QAItem("What lesson did the elder teach?", f"The elder taught that {f['lesson']}"),
        QAItem("What happened to the junk at the end?", f"The junk was sorted, and useful pieces were given new purposes instead of being left in a dangerous heap."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is junk?", "Junk is discarded or unwanted material, although some of it may still be repaired or reused."),
        QAItem("What is a swoosh?", "A swoosh is a rushing sound or movement, like wind passing quickly through the air."),
        QAItem("What is a cautionary myth?", "A cautionary myth is a traditional-style story that uses wonders and danger to teach people to act wisely."),
        QAItem("Why should people pause before touching unknown objects?", "Pausing gives people time to notice risks, ask for help, and choose a safer action."),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("lesson", "pause_before_touching"),
            asp.fact("object", "junk"),
            asp.fact("sound", "swoosh"),
            asp.fact("outcome", "safe"),
        ]
    )


ASP_RULES = r"""
safe_action(pause_before_touching) :- object(junk), sound(swoosh), lesson(pause_before_touching).
wisdom_gained :- safe_action(pause_before_touching), outcome(safe).
#show safe_action/1.
#show wisdom_gained/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    safe = set(asp.atoms(model, "safe_action"))
    wisdom = set(asp.atoms(model, "wisdom_gained"))
    if safe == {("pause_before_touching",)} and wisdom == {()}:
        print("OK: ASP caution gate matches Python.")
        return 0
    print("ASP verification failed.")
    print("safe_action:", sorted(safe))
    print("wisdom_gained:", sorted(wisdom))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Pip", "Grandmother Ash", "the hill of listening stones", "a bent tin cup", "the Wind-Calling Shell", 11, 0),
    StoryParams("Mira", "Ari", "Old Rowan", "the moonlit ravine", "a broken lantern", "the Blue Feather", 29, 1),
    StoryParams("Orin", "Bram", "Mother Reed", "the valley of seven bells", "a bundle of rusty wire", "the Little Storm Drum", 47, 2),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != hero]
    return StoryParams(
        hero=hero,
        helper=args.helper or rng.choice(helper_choices),
        elder=args.elder or rng.choice(ELDER_NAMES),
        place=args.place or rng.choice(PLACES),
        junk=args.junk or rng.choice(JUNK_ITEMS),
        charm=args.charm or rng.choice(CHARMS),
        seed=args.seed,
        variant=rng.randrange(1_000_000_000),
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        print(format_json(samples))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
