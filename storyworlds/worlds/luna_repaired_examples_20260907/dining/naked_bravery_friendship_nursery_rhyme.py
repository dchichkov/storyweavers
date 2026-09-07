#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about naked bravery and friendship.

A child and a friend find a shivering moonbeam in the garden. The child feels
naked of courage, but friendship helps bravery grow. The story is state-driven:
fear rises at the dark gate, a shared song and a small lantern build courage, and
the ending proves the change with a brave step into the moonlit garden.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Rhyme:
    id: str
    opening: str
    fear: str
    clue: str
    friendship: str
    song: str
    ending: str
    lesson: str


RHYME_REGISTRY = [
    Rhyme(
        "silver_gate",
        "By the silver gate at the end of the lane, a little moonbeam trembled in the rain.",
        "Brave Pip felt naked of courage, as bare as a branch with no leaf in the night.",
        "A tiny bell chimed beneath the thyme, though no wind had touched it.",
        "Mara took Pip's hand and said, 'One small step is lighter when two friends share it.'",
        "Together they sang, 'Moon above and toes below, friendship helps our courage grow.'",
        "Pip stepped through the gate, and the moonbeam danced around both friends like a ribbon of light.",
        "Bravery is not having no fear; it is moving kindly while a friend stays near.",
    ),
    Rhyme(
        "well_of_stars",
        "Beside the old wishing well, three pale stars bobbed like boats on a quiet sea.",
        "Nell felt naked of bravery and hid behind a lavender pot when the well began to hum.",
        "A blue feather floated up, pointing toward a forgotten lantern.",
        "Toby lifted the lantern and waited, giving Nell time to stand beside him.",
        "They sang, 'Star and stone, shine and gleam, friends can wake a sleepy dream.'",
        "Nell carried the lantern to the well, and the three stars rose into the sky with a happy wink.",
        "Friendship can lend a hand until your own brave heart remembers how to shine.",
    ),
    Rhyme(
        "hedge_song",
        "Under the tall green hedge, a lost robin chirped a tune with one note missing.",
        "Ollie felt naked of courage when the shadowy hedge rustled beside his feet.",
        "The missing note came from a golden seed caught in the leaves.",
        "June stood shoulder to shoulder with Ollie and promised not to laugh at his worried face.",
        "They sang, 'Rustle, rattle, hedge so wide, brave friends walk side by side.'",
        "Ollie reached into the leaves, freed the seed, and heard the robin finish its bright little song.",
        "A frightened heart can become brave when friendship makes room for one careful try.",
    ),
    Rhyme(
        "lantern_bridge",
        "Across the brook, a lantern swung above a bridge made of moon-white boards.",
        "Rose felt naked of courage when the boards creaked under the evening dew.",
        "A small paper crown had fallen on the far side, waiting for its owner.",
        "Finn crossed one board first, then turned back so Rose could match his slow, steady steps.",
        "They sang, 'Creek and plank, silver bright, friends make footsteps warm at night.'",
        "Rose crossed the bridge, fetched the crown, and placed it on a stump for the brook's lost fairy.",
        "Bravery grows board by board when friendship keeps the path gentle.",
    ),
    Rhyme(
        "sleepy_bell",
        "In the meadow, a sleepy bellflower drooped beneath a cloud shaped like a gray sheep.",
        "Bess felt naked of courage when a deep rumble rolled beyond the hill.",
        "A warm golden glow shone from a snail shell near the thirsty flower.",
        "Cal knelt beside Bess and helped her carry a cup of rainwater to the bellflower.",
        "They sang, 'Rain and root, wake and swell, friends can ring the little bell.'",
        "The flower lifted its blue head and rang a clear note that sent the gray cloud drifting away.",
        "Courage may begin as a whisper, then bloom when a friend helps you care.",
    ),
]

RHYME_BY_ID = {item.id: item for item in RHYME_REGISTRY}

CHILD_NAMES = ["Pip", "Nell", "Ollie", "Rose", "Bess", "Mina"]
FRIEND_NAMES = ["Mara", "Toby", "June", "Finn", "Cal", "Robin"]
TELLING_MODES = ["soft", "song_first", "question", "moonlight", "little_rhyme"]


@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    rhyme_id: Optional[str] = None
    telling_mode: Optional[str] = None
    seed: Optional[int] = None


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xBRA7E)
    material = f"{params.child_name}|{params.friend_name}|{params.rhyme_id or ''}"
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(material)))


def _sentence(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else text + "."


def build_world(params: StoryParams) -> World:
    rng = _rng(params)
    rhyme = RHYME_BY_ID.get(params.rhyme_id or "")
    if rhyme is None:
        rhyme = rng.choice(RHYME_REGISTRY)
    mode = params.telling_mode if params.telling_mode in TELLING_MODES else rng.choice(TELLING_MODES)

    if params.child_name == params.friend_name:
        raise StoryError("The child and friend must have different names.")
    if not params.child_name.strip() or not params.friend_name.strip():
        raise StoryError("Both the child and friend names must be non-empty.")

    world = World()
    child = world.add(Entity(params.child_name, "child", params.child_name))
    friend = world.add(Entity(params.friend_name, "friend", params.friend_name))
    moonbeam = world.add(Entity("moonbeam", "wonder", "moonbeam"))
    lantern = world.add(Entity("lantern", "thing", "little lantern"))

    child.meters.update(fear=2.0, courage=0.0)
    friend.meters.update(fear=0.5, courage=1.0)
    child.memes.update(bravery=0.0, friendship=1.0)
    friend.memes.update(bravery=1.0, friendship=1.0)
    moonbeam.meters["brightness"] = 1.0
    lantern.meters["light"] = 0.0

    openings = {
        "soft": f"{rhyme.opening} {params.child_name} listened, while {params.friend_name} hummed softly nearby.",
        "song_first": f'"Moon above, moon bright," sang {params.friend_name}. {rhyme.opening}',
        "question": f"Who would help the moonbeam tonight? {rhyme.opening}",
        "moonlight": f"The moon laid a silver path over the grass. {rhyme.opening}",
        "little_rhyme": f"Gate and glow, star and rain, {rhyme.opening.lower()}",
    }
    world.say(_sentence(openings[mode]))
    world.say(_sentence(rhyme.fear))
    world.facts.update(
        rhyme=rhyme,
        mode=mode,
        place="the moonlit garden",
        initial_fear=child.meters["fear"],
    )

    world.para()
    child.meters["fear"] += 0.5
    world.say(f"{params.child_name} wanted to help, but the dark made the little heart beat quick.")
    world.say(_sentence(rhyme.clue))
    world.say(f'"I am here," said {params.friend_name}, and friendship made a warm place beside {params.child_name}.')
    child.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    child.meters["fear"] -= 0.5
    child.meters["courage"] += 0.5

    world.para()
    world.say(_sentence(rhyme.friendship))
    world.say(_sentence(rhyme.song))
    lantern.meters["light"] = 1.0
    child.meters["fear"] = max(0.0, child.meters["fear"] - 1.0)
    child.meters["courage"] += 1.5
    friend.meters["courage"] += 0.5
    child.memes["bravery"] = child.meters["courage"]
    friend.memes["bravery"] = friend.meters["courage"]
    child.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.facts["song_used"] = True
    world.facts["lantern_lit"] = True
    world.say(f"The song filled the garden with a small, steady glow. {params.child_name} took a breath and looked at the waiting path.")

    world.para()
    if child.meters["courage"] < 1.5 or child.meters["fear"] > 1.0:
        raise StoryError("The friendship turn did not build enough courage for a safe resolution.")
    world.say(_sentence(rhyme.ending))
    world.say(_sentence(rhyme.lesson))
    child.memes["bravery"] = 2.0
    child.meters["courage"] = 2.0
    child.meters["fear"] = 0.0
    world.facts.update(
        brave_step=True,
        resolved=True,
        ending=rhyme.ending,
        lesson=rhyme.lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rhyme: Rhyme = f["rhyme"]
    child = next(e for e in world.entities.values() if e.type == "child")
    friend = next(e for e in world.entities.values() if e.type == "friend")
    return [
        f"Write a nursery rhyme about {child.label} feeling naked of courage in {f['place']}.",
        f"Show how {friend.label}'s friendship helps {child.label} become brave without pretending fear is absent.",
        f"Use this turning clue: {rhyme.clue} End with a concrete moonlit image proving that bravery and friendship changed the night.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rhyme: Rhyme = f["rhyme"]
    child = next(e for e in world.entities.values() if e.type == "child")
    friend = next(e for e in world.entities.values() if e.type == "friend")
    return [
        QAItem(
            question=f"Why did {child.label} feel naked of courage?",
            answer=f"{child.label} felt naked of courage because the dark garden and its strange sound made fear grow before the brave step.",
        ),
        QAItem(
            question=f"How did {friend.label} show friendship?",
            answer=f"{friend.label} stayed close, offered a steady hand, and helped {child.label} take one careful step instead of rushing or teasing.",
        ),
        QAItem(
            question="What helped bravery grow?",
            answer=f"The shared song, the little lantern, and a friend's patient company helped bravery grow while the fear became smaller.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{rhyme.ending} This showed that the child had acted bravely with friendship nearby.",
        ),
        QAItem(
            question="What lesson did the rhyme teach?",
            answer=rhyme.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing a helpful or right action even when you feel afraid.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring connection in which people help, trust, and stay kind to one another.",
        ),
        QAItem(
            question="What does naked mean?",
            answer="Naked means wearing no clothes; in this gentle rhyme, it also describes feeling unprotected or without courage.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, rhythmic poem or song, often with repetition and playful images.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "moonlit_garden"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "friendship"),
            asp.fact("word", "naked"),
            asp.fact("action", "share_song"),
            asp.fact("action", "take_brave_step"),
            asp.fact("object", "lantern"),
        ]
    )


ASP_RULES = r"""
has_friendship :- feature(friendship), action(share_song).
has_bravery :- feature(bravery), action(take_brave_step).
safe_light :- object(lantern), action(share_song).
valid_story :- setting(moonlit_garden), word(naked), has_friendship, has_bravery, safe_light.
#show valid_story/0.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "valid_story" for symbol in model)
    if not valid:
        print("MISMATCH: ASP twin did not confirm validity.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
    print("OK: ASP twin confirms bravery and friendship parity.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme storyworld of naked fear, bravery, and friendship.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--rhyme")
    parser.add_argument("--mode", choices=TELLING_MODES)
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
    child = args.name or rng.choice(CHILD_NAMES)
    friend = args.friend or rng.choice([name for name in FRIEND_NAMES if name != child])
    rhyme_id = args.rhyme or rng.choice(RHYME_REGISTRY).id
    return StoryParams(
        child_name=child,
        friend_name=friend,
        rhyme_id=rhyme_id,
        telling_mode=args.mode or rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams("Pip", "Mara", "silver_gate", "soft"),
    StoryParams("Nell", "Toby", "well_of_stars", "song_first"),
    StoryParams("Rose", "Finn", "lantern_bridge", "moonlight"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
