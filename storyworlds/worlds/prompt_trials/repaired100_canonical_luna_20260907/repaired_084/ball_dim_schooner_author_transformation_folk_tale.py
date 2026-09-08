#!/usr/bin/env python3
"""
A standalone folk-tale storyworld about a ball-dim schooner and an author
whose story changes when she learns to share its light.
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

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    author_name: str
    boat_name: str
    island_name: str
    seed: Optional[int] = None
    tale_id: int = 0
    dialogue_id: int = 0
    ending_id: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


AUTHOR_NAMES = ["Mira", "Tarin", "Luma", "Nell", "Orin", "Sela"]
BOAT_NAMES = ["Morning Bell", "Little Cedar", "Silver Gull", "Kind Wave"]
ISLAND_NAMES = ["Whispering Isle", "Lantern Shoal", "Pearl Island", "Hearth Cay"]

TALES = [
    {
        "shore": "a village where every doorway faced the sea",
        "problem": "the schooner's great lamp had grown ball-dim, so its round glow was barely brighter than a pebble",
        "need": "a story bright enough to guide the boat home",
        "discovery": "the lamp became brighter whenever the tale included a truth that helped another person",
        "change": "invited the fisher children, the baker, and the old net-mender to add their own pieces to the tale",
        "result": "each shared memory became a golden window in the lamp",
        "image": "the schooner sailed home beneath a moon-shaped glow that lit every wave",
        "lesson": "A story hoarded becomes small, but a story shared can become a lantern.",
    },
    {
        "shore": "a green coast guarded by a bell tower",
        "problem": "the schooner's ball-dim signal lantern could no longer show the sailors where the safe channel began",
        "need": "a tale whose shape could be seen from the harbor",
        "discovery": "the lantern answered not to fancy words but to honest voices",
        "change": "asked the tower keeper and the youngest deckhand to tell what the sea had taught them",
        "result": "their words turned the dim round lamp into a clear blue star",
        "image": "the blue star shone over the channel, and every returning boat found the harbor",
        "lesson": "The truest tale is made from many careful voices.",
    },
    {
        "shore": "a salt marsh where reeds sang whenever the wind changed",
        "problem": "the schooner's ball-dim compass light pointed only toward the author's own page",
        "need": "a direction that would lead to a lost family of travelers",
        "discovery": "the compass turned when the author listened instead of deciding every ending herself",
        "change": "let the travelers choose the brave, gentle, and funny parts of the journey",
        "result": "the compass needle became a warm red arrow toward the travelers' home",
        "image": "the schooner followed the red arrow through silver reeds and brought the family safely ashore",
        "lesson": "A guide must leave room for the travelers to help choose the road.",
    },
    {
        "shore": "a cliff village where children traded riddles for bread",
        "problem": "the schooner's ball-dim story globe had forgotten how to make anyone laugh",
        "need": "a tale that could lift a worried village",
        "discovery": "laughter returned when the author stopped polishing every joke alone",
        "change": "let the children supply silly names, surprising turns, and a goat who wanted a crown",
        "result": "the globe filled with warm light each time someone added a joyful idea",
        "image": "the goat wore a paper crown while the whole village laughed beside the shining schooner",
        "lesson": "Joy grows larger when no one has to keep it to themselves.",
    },
]

DIALOGUES = [
    ('"Why does your lamp hide its light?"', '"Because I wrote every word alone,"'),
    ('"May we add what we know?"', '"Yes," said the author, "if you help me find the ending."'),
    ('"A schooner cannot follow a star it refuses to see,"', '"Then teach me where to look,"'),
    ('"Your tale sounds lonely,"', '"It is lonely," admitted the author. "Will you sail into it with me?"'),
]

ENDINGS = [
    "From that day forward, the author carried a blank page beside every finished one.",
    "Afterward, the author wrote the first line, but she always left a bright space for another voice.",
    "The village remembered the transformation whenever the sea grew dark.",
    "And whenever the lamp dimmed, the people knew what to do: they gathered and told the truth together.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about an author, a schooner, and a ball-dim transformation."
    )
    parser.add_argument("--author", choices=AUTHOR_NAMES)
    parser.add_argument("--boat", choices=BOAT_NAMES)
    parser.add_argument("--island", choices=ISLAND_NAMES)
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
    author = args.author or rng.choice(AUTHOR_NAMES)
    boat = args.boat or rng.choice(BOAT_NAMES)
    island = args.island or rng.choice(ISLAND_NAMES)
    return StoryParams(
        author_name=author,
        boat_name=boat,
        island_name=island,
        tale_id=rng.randrange(len(TALES)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        ending_id=rng.randrange(len(ENDINGS)),
    )


def validate_params(params: StoryParams) -> None:
    if not params.author_name.strip():
        raise StoryError("author_name must not be empty")
    if not params.boat_name.strip():
        raise StoryError("boat_name must not be empty")
    if not params.island_name.strip():
        raise StoryError("island_name must not be empty")
    if not 0 <= params.tale_id < len(TALES):
        raise StoryError("tale_id does not name a known folk tale")
    if not 0 <= params.dialogue_id < len(DIALOGUES):
        raise StoryError("dialogue_id does not name a known exchange")
    if not 0 <= params.ending_id < len(ENDINGS):
        raise StoryError("ending_id does not name a known ending")


def tell(params: StoryParams) -> World:
    validate_params(params)
    tale = TALES[params.tale_id]
    question, reply = DIALOGUES[params.dialogue_id]

    world = World()
    author = world.add(Entity("author", "character", params.author_name))
    schooner = world.add(Entity("schooner", "vehicle", params.boat_name))
    island = world.add(Entity("island", "place", params.island_name))
    lamp = world.add(Entity("lamp", "object", "ball-dim lamp"))

    world.facts.update(
        author=author,
        schooner=schooner,
        island=island,
        lamp=lamp,
        tale=tale,
        transformation=False,
        dialogue=(question, reply),
    )

    author.memes["pride"] = 1.0
    author.memes["loneliness"] = 1.0
    schooner.meters["voyage"] = 1.0
    lamp.meters["brightness"] = 0.2

    world.say(
        f"Long ago, on {tale['shore']}, {author.label} lived aboard the schooner "
        f"{schooner.label} and wrote tales for the people of {island.label}."
    )
    world.say(
        f"One evening, {tale['problem'].capitalize()}. {author.label} needed {tale['need']}."
    )
    world.say(
        f"She polished her quill, trimmed her page, and wrote until the stars appeared, "
        f"but the light stayed dim because the tale had been made from only one pair of eyes."
    )

    world.para()
    world.say(f"At the rail, a small deckhand asked, {question}")
    world.say(f"{author.label} looked at the round lamp and answered, {reply}")
    world.say(
        f"Then the old wind carried a whisper from the shore: {tale['discovery'].capitalize()}."
    )
    author.memes["pride"] = 0.0
    author.memes["loneliness"] = 0.0
    author.memes["curiosity"] = 1.0
    lamp.meters["brightness"] = 0.5

    world.para()
    world.say(
        f"So {author.label} opened the cabin door and {tale['change']}. "
        f"At first, she feared the story would lose its shape."
    )
    world.say(
        f"But the new voices did not break the tale. Instead, {tale['result']}."
    )
    world.say(
        f"The schooner crossed the dark water, carrying the transformed story toward the village."
    )
    schooner.meters["voyage"] = 2.0
    lamp.meters["brightness"] = 1.0
    author.memes["generosity"] = 1.0
    world.facts["transformation"] = True

    world.para()
    world.say(tale["lesson"])
    world.say(f"{ENDINGS[params.ending_id]} {tale['image'].capitalize()}.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        f"Write a gentle Folk Tale about an author aboard a schooner near {world.facts['island'].label}.",
        f"Include a ball-dim lamp that changes when the author {tale['change']}.",
        f"Show a clear transformation from a lonely story to {tale['need']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    author = world.facts["author"]
    schooner = world.facts["schooner"]
    island = world.facts["island"]
    tale = world.facts["tale"]
    return [
        QAItem(
            "Who lived aboard the schooner?",
            f"{author.label}, the author, lived aboard the schooner {schooner.label}.",
        ),
        QAItem(
            "Why was the schooner's lamp ball-dim?",
            f"It was ball-dim because the story had been made from only one pair of eyes and did not yet include the helpful voices of others.",
        ),
        QAItem(
            "What changed the lamp?",
            f"The lamp brightened when {author.label} listened to people from {island.label} and invited them to add their own truthful ideas.",
        ),
        QAItem(
            "What transformation happened in the tale?",
            f"The lonely, dim story became a shared guiding tale, and its lamp changed from a weak glow into a bright light.",
        ),
        QAItem(
            "What lesson did the author learn?",
            tale["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a schooner?",
            "A schooner is a sailing ship with a tall mast and sails.",
        ),
        QAItem(
            "What does an author do?",
            "An author creates stories, books, or other written works.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a meaningful change from one form or condition into another.",
        ),
        QAItem(
            "What is a folk tale?",
            "A folk tale is a traditional-style story that often carries a simple lesson.",
        ),
        QAItem(
            "What does ball-dim mean in this story?",
            "Ball-dim describes a round lamp whose light is weak at first and becomes brighter after the story changes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.label} {' '.join(details)}")
    lines.append(f"facts: transformation={world.facts.get('transformation')}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(sea).
feature(transformation).
seed_word(ball_dim).
seed_word(schooner).
seed_word(author).
lamp_starts_dim.
voices_shared.
story_transforms :-
    lamp_starts_dim,
    voices_shared,
    feature(transformation).
#show story_transforms/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "sea"),
            asp.fact("feature", "transformation"),
            asp.fact("seed_word", "ball_dim"),
            asp.fact("seed_word", "schooner"),
            asp.fact("seed_word", "author"),
            asp.fact("lamp_starts_dim"),
            asp.fact("voices_shared"),
        ]
    )


def asp_program(show: str = "#show story_transforms/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "story_transforms"))
    expected = {()}
    if found != expected:
        print("MISMATCH")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1

    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("transformation"):
            print("MISMATCH: generated story did not transform")
            return 1

    print("OK: ASP parity matches Python gate and generated stories transform.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mira", "Morning Bell", "Whispering Isle", tale_id=0, dialogue_id=0, ending_id=0),
    StoryParams("Tarin", "Silver Gull", "Lantern Shoal", tale_id=1, dialogue_id=1, ending_id=1),
    StoryParams("Luma", "Little Cedar", "Pearl Island", tale_id=2, dialogue_id=2, ending_id=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        if not asp.atoms(model, "story_transforms"):
            raise StoryError("ASP reasonableness gate rejected the story domain")

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
