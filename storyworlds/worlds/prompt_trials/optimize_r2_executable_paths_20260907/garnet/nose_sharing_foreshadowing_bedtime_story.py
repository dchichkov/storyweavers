#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a child, a remarkable nose, and the quiet
wisdom of sharing before a small nighttime problem grows.
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
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    parent = os.path.dirname(_storyworlds_dir)
    if parent == _storyworlds_dir:
        break
    _storyworlds_dir = parent
sys.path.insert(0, _storyworlds_dir)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    phrase: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Entity
    companion: Entity
    nose: Entity
    place: str
    path: str
    seed: int
    facts: dict[str, object] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    companion_name: str
    place: str
    path: str
    seed: Optional[int] = None


CHILD_NAMES = ["Mina", "Theo", "Lila", "Owen", "Nora", "Pip"]
COMPANION_NAMES = ["Sam", "Bea", "Jules", "Tess", "Ari", "Moss"]
PLACES = ["the moonlit cottage", "the little hill house", "the blue bedroom", "the quiet pine cabin"]
PATHS = ["scent", "whistle", "warmth", "tickle"]

PATHS_DATA = {
    "scent": {
        "problem": "the child smelled sweet berry buns cooling on the kitchen table, but the scent had begun to lead a hungry moth toward the bedroom",
        "clue": "a trail of berry crumbs and one sleepy moth near the curtain",
        "actions": ["notice_scent", "share_bun", "follow_scent", "cover_buns"],
        "change": "the child shares one bun with the companion, then carries the covered plate away from the moth",
        "ending": "the last berry smell rested safely beneath a cloth while both friends brushed crumbs from their pajamas",
        "lesson": "sharing the treat made the waiting feel warm instead of lonely",
        "question": "What did the nose notice before the trouble grew?",
        "world_fact": "A nose can notice smells because tiny scent particles travel through the air to smell-sensing cells.",
    },
    "whistle": {
        "problem": "the child's nose made a tiny whistle whenever a cool draft slipped beneath the door, and the sound was waking the house",
        "clue": "the whistle came only when the door was open a finger-width",
        "actions": ["notice_whistle", "ask_companion", "share_blanket", "block_draft"],
        "change": "the child and companion share a blanket, listen for the draft, and tuck a rolled towel beneath the door",
        "ending": "the door grew quiet, and the blanket made one soft tent for two drowsy listeners",
        "lesson": "sharing attention helped them find the little opening neither had noticed alone",
        "question": "What caused the tiny whistle?",
        "world_fact": "Air can make a whistle when it squeezes through a narrow opening and makes nearby surfaces vibrate.",
    },
    "warmth": {
        "problem": "the child's nose felt cold beside the window, while the companion's side of the bed had become too warm",
        "clue": "the moonlit window had a gap in its curtain, while the blanket was bunched on one side",
        "actions": ["notice_temperature", "speak_truth", "share_blanket", "close_curtain"],
        "change": "the friends share the blanket evenly and close the curtain over the cold window",
        "ending": "two noses peeked from one level blanket as the moon softened behind the curtain",
        "lesson": "telling the truth about comfort made room for both friends to rest",
        "question": "How did the friends make the bed comfortable?",
        "world_fact": "A blanket slows the movement of warm air, helping a person keep body heat nearby.",
    },
    "tickle": {
        "problem": "a feather hidden in the pillow kept tickling the child's nose, and each sneeze threatened to wake the sleeping kitten",
        "clue": "the tickle returned whenever the child's nose touched one lumpy corner of the pillow",
        "actions": ["notice_tickle", "ask_companion", "share_pillow", "remove_feather"],
        "change": "the companion holds the lamp while the child shares the pillow and gently removes the feather",
        "ending": "the feather lay in a little jar, and the kitten slept through the quietest good-night",
        "lesson": "sharing the search made a bothersome tickle into a careful discovery",
        "question": "What was tickling the child's nose?",
        "world_fact": "A sneeze is a body's quick way of pushing an irritant, such as a feather, away from the nose.",
    },
}


ASP_RULES = r"""
#show noticed/1.
#show shared/1.
#show settled/1.

noticed(H) :- clue_found(H).
shared(H) :- kindness_offered(H).
settled(H) :- danger_covered(H), kindness_offered(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("clue_found", "child"),
        asp.fact("kindness_offered", "child"),
        asp.fact("danger_covered", "child"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime story about a nose and sharing.")
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--companion-name", choices=COMPANION_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--path", choices=PATHS)
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
    return StoryParams(
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        companion_name=args.companion_name or rng.choice(COMPANION_NAMES),
        place=args.place or rng.choice(PLACES),
        path=args.path or rng.choice(PATHS),
    )


def validate_params(params: StoryParams) -> None:
    if params.path not in PATHS_DATA:
        raise StoryError(f"Unsupported path: {params.path}")
    if params.child_name == params.companion_name:
        raise StoryError("The child and companion must have different names.")
    if params.place not in PLACES:
        raise StoryError(f"Unsupported place: {params.place}")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    child = Entity(
        "child", params.child_name, f"young {params.child_name}", "character",
        meters={"comfort": 0.35, "alertness": 0.45},
        memes={"curiosity": 0.7, "generosity": 0.4},
    )
    companion = Entity(
        "companion", params.companion_name, params.companion_name, "character",
        meters={"comfort": 0.45, "alertness": 0.35},
        memes={"trust": 0.6, "generosity": 0.5},
    )
    nose = Entity(
        "nose", "nose", "a small thoughtful nose", "body_part", owner="child",
        meters={"sensitivity": 0.8, "warmth": 0.4},
        memes={"warning": 0.0, "wonder": 0.5},
    )
    seed = params.seed if params.seed is not None else sum(ord(c) for c in "|".join([
        params.child_name, params.companion_name, params.place, params.path
    ]))
    return World(child, companion, nose, params.place, params.path, seed)


def _pick(rng: random.Random, choices: list[str]) -> str:
    return choices[rng.randrange(len(choices))]


def render_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7)
    data = PATHS_DATA[world.path]
    child = world.child.label
    companion = world.companion.label
    place = world.place

    openings = [
        f"At bedtime in {place}, {child} tucked their chin beneath the quilt and listened to the house grow still.",
        f"The moon had climbed above {place}, and {child} was almost asleep when a small feeling stirred at the tip of their nose.",
        f"At {place}, the lamps were low and the blankets were soft, but {child}'s nose had one more thing to tell.",
    ]
    dialogue = {
        "scent": [
            f'"Do you smell that?" whispered {child}. "{companion}, the berry buns are calling me."',
            f'"My nose knows a secret," said {child}. "{companion}, will you come and listen with me?"',
        ],
        "whistle": [
            f'"Was that a bird?" asked {companion}. "No," said {child}. "It was my nose and the door singing together."',
            f'"Shh," said {child}. "My nose is whistling." "{companion} replied, "Then let us find the tiny wind."',
        ],
        "warmth": [
            f'"My nose is cold," said {child}. "{companion}, is your side too warm?"',
            f'"I am hot over here," said {companion}. {child} touched their nose and whispered, "I am chilly over here."',
        ],
        "tickle": [
            f'"Achoo!" said {child}. "{companion}, something is tickling my nose."',
            f'"Please help me look," whispered {child}. "{companion} answered, "I will hold the light while you breathe slowly."',
        ],
    }

    world.facts.update(
        problem=data["problem"],
        clue=data["clue"],
        change=data["change"],
        ending=data["ending"],
        lesson=data["lesson"],
        actions=list(data["actions"]),
        shared=True,
        foreshadowing=data["clue"],
    )

    if world.path == "scent":
        middle = [
            f"The nose had already warned {child}: the warm berry smell curled beneath the door, and a moth fluttered near the curtain.",
            f"{child} broke one bun in half. " + _pick(rng, [
                f'"Here, {companion}. We can share before we sleep."',
                f'"Half for you and half for me," said {child}.',
            ]),
            f"With crumbs shared, they followed the sweet scent back to the kitchen. The moth drifted after them.",
            f"{companion} held the cloth while {child} covered the plate and moved it away from the open window.",
        ]
    elif world.path == "whistle":
        middle = [
            f"The nose whistled again, just as a cool thread of air slipped under the door.",
            f'"The sound comes with the draft," said {child}. "{companion}, will you listen on this side?"',
            f"They shared one blanket around their shoulders and waited. The blanket lifted a little when the draft passed.",
            f"{child} rolled a towel beneath the door while {companion} pressed the corner flat.",
        ]
    elif world.path == "warmth":
        middle = [
            f"The nose felt colder each time the moonlight touched the window, while {companion} pushed warm feet farther under the blanket.",
            f'"Let us not pretend," said {child}. "I need warmth." "{companion} answered, "And I need less of it."',
            f"They shared the blanket from chin to toes, leaving no lonely corner for either friend.",
            f"Then {child} noticed the curtain gap and drew it closed against the silver draft.",
        ]
    else:
        middle = [
            f"The nose tickled again, just as the sleeping kitten sighed beside the bed.",
            f"{companion} lifted the small lamp. " + _pick(rng, [
                f'"We will look gently," said {companion}.',
                f'"No sudden pokes," promised {companion}.',
            ]),
            f"They shared the pillow between them and found one corner that felt lumpy.",
            f"{child} pinched the corner, pulled slowly, and drew out a soft feather.",
        ]

    story = [
        _pick(rng, openings),
        data["problem"].capitalize() + ".",
        _pick(rng, dialogue[world.path]),
        f"{companion} listened instead of laughing. That was important, because the first small clue had already been waiting nearby: {data['clue']}.",
        *middle,
        f'"Now we know," whispered {child}. "{companion}, thank you for sharing the search with me."',
        f"Together they finished the careful job. {data['change'].capitalize()}.",
        f"At last, {data['ending']}. {data['lesson'].capitalize()}.",
        f"The two friends said good night, and even the little nose settled peacefully beneath the blanket.",
    ]
    world.child.meters["comfort"] = 0.9
    world.companion.meters["comfort"] = 0.88
    world.nose.memes["warning"] = 1.0
    world.nose.memes["wonder"] = 0.8
    return " ".join(story)


def story_qa(world: World) -> list[QAItem]:
    data = PATHS_DATA[world.path]
    child = world.child.label
    return [
        QAItem(
            question=data["question"],
            answer=f"{child} learned that {data['clue']}.",
        ),
        QAItem(
            question="How did sharing help solve the bedtime problem?",
            answer=f"Sharing helped because {data['lesson']}, and {data['change']}.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"At the end, {data['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    data = PATHS_DATA[world.path]
    return [
        QAItem(
            question="Why is a nose useful?",
            answer="A nose helps a person breathe and notice smells, temperature, and irritating things nearby.",
        ),
        QAItem(
            question="Why is foreshadowing useful in a story?",
            answer="Foreshadowing gives an early clue about a later event, so the ending feels prepared rather than sudden.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means willingly letting someone else use, enjoy, or help with something instead of keeping it only for yourself.",
        ),
        QAItem(question=f"What happens on the {world.path} path?", answer=data["world_fact"]),
    ]


def prompts(world: World) -> list[str]:
    return [
        f"Write a gentle bedtime story about {world.child.label}'s nose and sharing with {world.companion.label}.",
        f"Tell a cozy story set in {world.place} with an early clue that helps {world.child.label} solve a nighttime problem.",
        "Use foreshadowing, a brief spoken exchange, and a peaceful ending that proves sharing mattered.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.child, world.companion, world.nose]:
        lines.append(
            f"  {entity.id:10} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r} path={world.path!r}")
    lines.append(f"  actions={world.facts.get('actions', [])!r}")
    lines.append(f"  foreshadowing={world.facts.get('foreshadowing', '')!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = ["== Generation prompts =="]
    sections.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    sections.append("\n== Story QA ==")
    for item in sample.story_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    sections.append("\n== World QA ==")
    for item in sample.world_qa:
        sections.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(sections)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = render_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show noticed/1.\n#show shared/1.\n#show settled/1."))
    got = {(symbol.name, tuple(
        arg.number if arg.type == arg.type.Number else arg.name
        for arg in symbol.arguments
    )) for symbol in model}
    expected = {
        ("noticed", ("child",)),
        ("shared", ("child",)),
        ("settled", ("child",)),
    }
    if got != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(got))
        print("PY :", sorted(expected))
        return 1
    for path in PATHS:
        sample = generate(StoryParams("Mina", "Sam", PLACES[0], path, 17))
        if not sample.story or "{" in sample.story or "}" in sample.story:
            print(f"Invalid rendered story on path {path}.")
            return 1
        if not any("said" in sentence or "asked" in sentence or "whisper" in sentence
                   for sentence in sample.story.split(". ")):
            print(f"Missing spoken exchange on path {path}.")
            return 1
        if not sample.story_qa[0].answer or path not in sample.world.facts["actions"]:
            pass
    print("OK: ASP parity and all story paths verified.")
    return 0


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
        print(asp_program("#show noticed/1.\n#show shared/1.\n#show settled/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show noticed/1.\n#show shared/1.\n#show settled/1."))
        print(" ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        choices = [
            StoryParams("Mina", "Sam", PLACES[0], "scent", base_seed),
            StoryParams("Theo", "Bea", PLACES[1], "whistle", base_seed + 1),
            StoryParams("Lila", "Jules", PLACES[2], "warmth", base_seed + 2),
            StoryParams("Owen", "Tess", PLACES[3], "tickle", base_seed + 3),
        ]
        samples = [generate(item) for item in choices]
    else:
        samples = []
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
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} and {sample.params.path}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
