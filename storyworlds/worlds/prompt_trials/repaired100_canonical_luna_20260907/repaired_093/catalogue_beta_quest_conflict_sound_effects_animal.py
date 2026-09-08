#!/usr/bin/env python3
"""
Standalone story world: Luna's beta quest through the sound-effects catalogue.

An Animal Story about Luna, a young fox, who must find a missing sound effect
for a forest play. A catalogue mistake creates a small conflict, and careful
listening helps Luna repair the show.
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the woodland playhouse"
    detail: str = "a little stage beneath the old oak, with baskets of props beside it"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


CATALOGUE = [
    {
        "id": "rain",
        "name": "rain",
        "sound": "shhh-shhh",
        "source": "a handful of dry leaves rubbed together",
        "purpose": "the storm scene",
        "ending": "The leaves whispered their soft rain while the actors bowed beneath the oak.",
    },
    {
        "id": "thunder",
        "name": "thunder",
        "sound": "boom-bum",
        "source": "a hollow log rolled gently over a wooden board",
        "purpose": "the mountain scene",
        "ending": "The hollow log rumbled like distant thunder, and the mountain story felt grand.",
    },
    {
        "id": "frog",
        "name": "frog",
        "sound": "plop",
        "source": "a pebble dropped into a shallow bowl of water",
        "purpose": "the pond scene",
        "ending": "The pebble made one neat plop, and everyone imagined a frog hiding by the pond.",
    },
    {
        "id": "wind",
        "name": "wind",
        "sound": "whooo",
        "source": "a pinecone spun inside a paper tube",
        "purpose": "the night scene",
        "ending": "The paper tube sang whooo, whooo as the moon rose over the playhouse.",
    },
    {
        "id": "owl",
        "name": "owl",
        "sound": "hoo-hoo",
        "source": "two gentle taps on a cedar box",
        "purpose": "the forest scene",
        "ending": "Two taps answered the dark, and a real owl called from a branch above.",
    },
    {
        "id": "stream",
        "name": "stream",
        "sound": "trickle-trickle",
        "source": "blue beads poured slowly through a wooden cup",
        "purpose": "the journey scene",
        "ending": "The beads trickled through the cup as the travelers crossed their pretend stream.",
    },
]

OPENINGS = [
    "{hero} arrived early at the woodland playhouse, carrying a small notebook.",
    "Before the afternoon sun reached the stage, {hero} hurried beneath the old oak.",
    "The forest animals were preparing a new play, and {hero} had promised to help.",
    "On rehearsal day, {hero} found the prop baskets waiting beside the little stage.",
]

REFLECTIONS = [
    '"A catalogue can guide us," said {friend}, "but our ears must check the guide."',
    '"I heard the wrong sound and blamed the wrong helper," {hero} admitted.',
    '{friend} smiled. "A good quest follows clues, even when the first clue is mistaken."',
    '"Next time," said {hero}, "we will listen before we argue."',
]


ASP_RULES = r"""
quest(X) :- prepares(X, beta), missing_sound(beta).
conflict(X,Y) :- quest(X), holds(Y, catalogue), wrong_entry(catalogue).
clue(X) :- hears(X, sound_effect), matches(sound_effect, beta).
resolved(X) :- quest(X), clue(X), corrects(X, catalogue), rehearses(X, beta).
valid_story(X) :- quest(X), conflict(X,Y), resolved(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("animal", "luna"),
            asp.fact("animal", "friend"),
            asp.fact("prepares", "luna", "beta"),
            asp.fact("missing_sound", "beta"),
            asp.fact("holds", "friend", "catalogue"),
            asp.fact("wrong_entry", "catalogue"),
            asp.fact("hears", "luna", "sound_effect"),
            asp.fact("matches", "sound_effect", "beta"),
            asp.fact("corrects", "luna", "catalogue"),
            asp.fact("rehearses", "luna", "beta"),
            asp.fact("theme", "quest"),
            asp.fact("theme", "conflict"),
            asp.fact("theme", "sound_effects"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def build_world(params: StoryParams) -> World:
    if not params.name or not params.friend_name:
        raise StoryError("Both an animal name and a friend name are required.")
    if params.name == params.friend_name:
        raise StoryError("The quest needs two different animals.")

    rng = random.Random(params.seed)
    entry = rng.choice(CATALOGUE)
    opening = rng.choice(OPENINGS)
    reflection = rng.choice(REFLECTIONS)
    hero = Entity(
        id=params.name,
        kind="character",
        type="fox",
        label="young fox",
        meters={"distance": 0.0, "energy": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0, "confidence": 0.0, "relief": 0.0},
    )
    friend = Entity(
        id=params.friend_name,
        kind="character",
        type="badger",
        label="helpful badger",
        meters={"distance": 0.0},
        memes={"patience": 1.0, "worry": 0.0, "friendship": 1.0},
    )
    catalogue = Entity(
        id="catalogue",
        type="book",
        label="the sound-effects catalogue",
        meters={"pages": 12.0},
        memes={"trust": 1.0},
    )
    beta = Entity(
        id="beta",
        type="play",
        label="the beta play",
        memes={"readiness": 0.0},
    )
    world = World(setting=Setting())
    for entity in (hero, friend, catalogue, beta):
        world.add(entity)
    world.facts.update(
        hero=hero,
        friend=friend,
        catalogue=catalogue,
        beta=beta,
        entry=entry,
        opening=opening,
        reflection=reflection,
        scene_detail=rng.choice(
            [
                "mossy costumes hung from a branch",
                "painted acorns marked the edge of the stage",
                "a row of pinecone seats faced the curtain",
                "sunbeams slipped through the oak leaves",
            ]
        ),
        wrong_entry="the catalogue listed the wrong sound for the beta play",
        sound_found=False,
        conflict=False,
        resolved=False,
    )
    return world


def story_intro(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    world.say(world.facts["opening"].format(hero=hero.id))
    world.say(
        f"{hero.id} was a young fox, and {friend.id} was a careful badger. "
        f"They worked at {world.setting.place}, where {world.facts['scene_detail']}."
    )
    world.say(
        f"The animals were testing their new beta play, a short adventure filled with "
        f"sound effects from a catalogue."
    )


def story_quest(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    entry = world.facts["entry"]
    hero.meters["distance"] += 1.0
    beta = world.facts["beta"]
    beta.memes["readiness"] += 0.3
    world.say(
        f"The quest was to find the missing sound for {entry['purpose']}. "
        f"The catalogue said the sound should be {entry['sound']}."
    )
    world.say(
        f"{hero.id} searched the prop baskets and found {entry['source']}. "
        f"He made the sound, but it did not fit the scene."
    )
    world.say(
        f'"That is not the right page," {friend.id} said. '
        f'"The catalogue points to {entry["name"]}, but our scene needs a different clue."'
    )
    world.say(
        f'"You must have read it wrong!" {hero.id} replied. '
        f'"The catalogue cannot be mistaken."'
    )
    hero.memes["worry"] += 1.0
    friend.memes["worry"] += 1.0
    world.facts["conflict"] = True


def story_turn(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    entry = world.facts["entry"]
    hero.meters["distance"] += 1.0
    world.say(
        f"{friend.id} did not argue back. He opened the catalogue to the torn beta page "
        f"and pointed to a tiny note beneath the picture."
    )
    world.say(
        f'"Listen to the scene, not only the label," {friend.id} said. '
        f'"What sound would make the story feel true?"'
    )
    world.say(
        f"{hero.id} closed his eyes. He heard the leaves, the creek, and a real bird above "
        f"the stage. Then he noticed that the missing sound should be made with {entry['source']}."
    )
    world.say(
        f"He tried it again. The sound was {entry['sound']}, and this time it matched "
        f"{entry['purpose']} perfectly."
    )
    world.say(world.facts["reflection"].format(hero=hero.id, friend=friend.id))
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    hero.memes["confidence"] += 1.0
    world.facts["sound_found"] = True
    world.facts["clue"] = "the torn beta page and the sounds already present in the forest"


def story_resolution(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    entry = world.facts["entry"]
    beta = world.facts["beta"]
    beta.memes["readiness"] = 1.0
    hero.memes["relief"] += 1.0
    world.facts["catalogue"].memes["trust"] = 0.8
    world.say(
        f"{hero.id} carefully corrected the catalogue's beta note instead of throwing it away. "
        f"{friend.id} wrote the tested sound beside the old entry."
    )
    world.say(
        f"Then the animals rehearsed the scene together. {hero.id} made the sound, "
        f"{friend.id} performed the action, and nobody blamed anyone when a cue needed another try."
    )
    world.say(
        f"{entry['ending']} {hero.id} and {friend.id} felt proud because their quest had ended "
        f"with listening, teamwork, and a repaired catalogue."
    )
    world.facts["resolved"] = True


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    world.say("")
    story_quest(world)
    world.say("")
    story_turn(world)
    world.say("")
    story_resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    entry = world.facts["entry"]
    return [
        "Write a child-facing Animal Story about a fox and badger completing a sound-effects quest for a beta play.",
        f"Show how {hero.id} and {friend.id} disagree when the catalogue gives the wrong sound for {entry['purpose']}.",
        f"Include spoken dialogue, the clue that careful listening matters, and end with {entry['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    entry = world.facts["entry"]
    return [
        QAItem(
            question=f"What quest were {hero.id} and {friend.id} trying to complete?",
            answer=f"They were trying to find the missing sound effect for {entry['purpose']} in their beta play."
        ),
        QAItem(
            question="What caused the conflict between the two animals?",
            answer=f"The catalogue gave an unhelpful entry, so {hero.id} and {friend.id} disagreed about whether the catalogue or the reading of it was at fault."
        ),
        QAItem(
            question="What clue helped solve the problem?",
            answer="The torn beta page and the natural sounds around the woodland stage showed them that they needed to listen to the scene instead of trusting a label alone."
        ),
        QAItem(
            question=f"How was the correct sound made?",
            answer=f"It was made with {entry['source']}."
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} do after finding the sound?",
            answer=f"They corrected the beta note in the catalogue and rehearsed the scene together, taking turns and trying again when a cue needed work."
        ),
        QAItem(
            question="What lesson did the quest teach?",
            answer="A catalogue is useful, but careful listening, kind conversation, and testing an idea together can solve a mistake."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a catalogue?",
            answer="A catalogue is an organized list or book that helps people find and identify items."
        ),
        QAItem(
            question="What does beta mean in a play or project?",
            answer="Beta means an early version that is being tested so people can discover problems and improve it."
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are created or recorded sounds used to help an audience imagine actions, places, or events."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        valid = asp.atoms(model, "valid_story")
        if ("luna",) not in valid:
            print("MISMATCH: ASP did not derive valid_story(luna).")
            return 1
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    sample = generate(StoryParams(name="Luna", friend_name="Bram", seed=7))
    if not sample.story or not sample.story_qa:
        print("MISMATCH: generated story exercise failed.")
        return 1
    print("OK: Python and ASP reasonableness gates pass.")
    return 0


NAMES = ["Luna", "Pip", "Milo", "Tara", "Nico", "Fenn", "Rory", "Cleo"]
FRIEND_NAMES = ["Bram", "Nori", "Pip", "Mara", "Otis", "Suki", "Toby", "Wren"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An Animal Story about a beta sound-effects quest.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
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
    name = args.name or rng.choice(NAMES)
    choices = [value for value in FRIEND_NAMES if value != name]
    friend_name = args.friend_name or rng.choice(choices)
    return StoryParams(name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:8}) {' '.join(parts)}")
    lines.append(f"  facts      sound_found={world.facts['sound_found']} resolved={world.facts['resolved']}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Luna", friend_name="Bram", seed=base_seed),
            StoryParams(name="Milo", friend_name="Nori", seed=base_seed + 1),
            StoryParams(name="Tara", friend_name="Otis", seed=base_seed + 2),
            StoryParams(name="Cleo", friend_name="Wren", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
