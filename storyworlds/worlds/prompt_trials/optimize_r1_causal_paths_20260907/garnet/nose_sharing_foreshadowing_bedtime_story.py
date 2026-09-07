#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a little nose, a shared blanket, and clues
that help friends notice what will matter before sleep.
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
class Thing:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Thing
    friend: Thing
    nose: Thing
    blanket: Thing
    room: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    child_name: str
    friend_name: str
    room: str
    problem: str
    solution: str
    voice: str
    seed: Optional[int] = None


CHILDREN = ["Mina", "Theo", "Lulu", "Sam", "Nora", "Pip"]
FRIENDS = ["Bear", "Owl", "Bunny", "Fox", "Mouse"]
ROOMS = ["the moonlit bedroom", "the little attic room", "the quiet nursery", "the room beneath the stars"]
PROBLEMS = ["cold", "sneeze", "lost_lullaby", "darkness"]
SOLUTIONS = ["share_blanket", "share_warmth", "follow_clues", "lantern"]
VOICES = ["whispering", "cozy", "playful"]

ASP_RULES = r"""
#show needs_help/1.
#show shared/1.
#show ready_for_sleep/1.

needs_help(C) :- cold_nose(C).
needs_help(C) :- sneeze_waiting(C).
shared(C) :- blanket_shared(C).
shared(C) :- warmth_shared(C).
ready_for_sleep(C) :- needs_help(C), shared(C), clue_followed(C).
ready_for_sleep(C) :- needs_help(C), shared(C), lantern_shared(C).
ready_for_sleep(C) :- cold_nose(C), blanket_shared(C).
"""


def asp_facts(problem: str, solution: str) -> str:
    import asp
    facts = [
        asp.fact("cold_nose", "child") if problem == "cold" else "",
        asp.fact("sneeze_waiting", "child") if problem == "sneeze" else "",
        asp.fact("blanket_shared", "child") if solution == "share_blanket" else "",
        asp.fact("warmth_shared", "child") if solution == "share_warmth" else "",
        asp.fact("clue_followed", "child") if solution == "follow_clues" else "",
        asp.fact("lantern_shared", "child") if solution == "lantern" else "",
    ]
    return "\n".join(x for x in facts if x)


def asp_program(problem: str = "cold", solution: str = "share_blanket") -> str:
    return f"{asp_facts(problem, solution)}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("cold", "share_blanket")
    model = asp.one_model(program)
    names = {sym.name for sym in model}
    expected = {"needs_help", "shared", "ready_for_sleep"}
    if expected.issubset(names):
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(names))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime storyworld about a nose, sharing, and clues before sleep."
    )
    parser.add_argument("--child-name", choices=CHILDREN)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--room", choices=ROOMS)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
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
    allowed = {
        "cold": ["share_blanket", "share_warmth"],
        "sneeze": ["follow_clues", "share_warmth"],
        "lost_lullaby": ["follow_clues", "lantern"],
        "darkness": ["lantern", "share_blanket"],
    }[problem]
    solution = args.solution or rng.choice(allowed)
    if solution not in allowed:
        raise StoryError(
            f"Solution {solution!r} cannot resolve the {problem!r} problem; "
            f"choose one of {allowed}."
        )
    return StoryParams(
        child_name=args.child_name or rng.choice(CHILDREN),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        room=args.room or rng.choice(ROOMS),
        problem=problem,
        solution=solution,
        voice=args.voice or rng.choice(VOICES),
    )


def build_world(params: StoryParams) -> World:
    child = Thing(
        "child",
        params.child_name,
        "character",
        memes={"curiosity": 0.7, "care": 0.8},
    )
    friend = Thing(
        "friend",
        params.friend_name,
        "character",
        memes={"trust": 0.8, "sleepiness": 0.6},
    )
    nose = Thing(
        "nose",
        "nose",
        "body_part",
        owner="child",
        meters={"warmth": 0.4, "comfort": 0.5},
        memes={"warning": 0.8, "sensitivity": 0.7},
    )
    blanket = Thing(
        "blanket",
        "blue blanket",
        "covering",
        owner="friend",
        meters={"warmth": 0.8, "reach": 1.0},
        memes={"sharing": 0.9},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in "|".join(vars(params).values() if False else [
            params.child_name, params.friend_name, params.room,
            params.problem, params.solution, params.voice
        ]))
    return World(child, friend, nose, blanket, params.room, seed)


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _validate(params: StoryParams) -> None:
    allowed = {
        "cold": {"share_blanket", "share_warmth"},
        "sneeze": {"follow_clues", "share_warmth"},
        "lost_lullaby": {"follow_clues", "lantern"},
        "darkness": {"lantern", "share_blanket"},
    }
    if params.problem not in allowed:
        raise StoryError(f"Unknown bedtime problem: {params.problem}.")
    if params.solution not in allowed[params.problem]:
        raise StoryError(
            f"The {params.solution} plan does not fit the {params.problem} problem."
        )


def _cold_story(world: World, params: StoryParams, rng: random.Random) -> str:
    h, f, room = world.child.label, world.friend.label, world.room
    if params.solution == "share_blanket":
        opening = _pick(rng, [
            f"By bedtime in {room}, {h} tucked one chilly nose beneath the blue blanket.",
            f"The moon looked in through the window as {h} climbed into bed with a cold little nose.",
        ])
        lines = [
            opening,
            f"{h} rubbed the nose, but it stayed cold. {f} noticed that the blanket had crept toward one side of the bed.",
            f'"My nose feels like a snow pea," whispered {h}. "{f}, may I share your blanket?"',
            f'"Of course," said {f}. "But listen first. The window curtain is shivering, and the moon is drawing a silver line across the floor."',
            "That silver line was a clue: a draft slipped under the window and would soon reach the pillow.",
            f"Together they moved the bed away from the draft and spread the blanket wide, so {h}'s nose and {f}'s paws both rested in the warm middle.",
            f'"A blanket grows bigger when we share it," said {h}.',
            f'"And a room grows quieter when we notice its clues," murmured {f}.',
            f"Before long, the nose felt warm, the curtain became still, and both friends fell asleep beneath one soft blue roof.",
        ]
        resolution = f"{h} and {f} moved away from the draft and shared the blanket"
        ending = "the two friends slept beneath one wide blue blanket"
    else:
        opening = f"In {room}, {h} felt a cold nose while the moon climbed the wall."
        lines = [
            opening,
            f"The blue blanket belonged to {f}, who was already curled at the far edge.",
            f'"Could we share some warmth?" asked {h}.',
            f'"Yes," said {f}, holding out warm paws. "But your nose is telling us something. The candle flame leans toward the window."',
            "They followed that small sign and found a gap beneath the sill. Cold air was sneaking in like a quiet mouse.",
            f"{h} pressed a folded sock into the gap while {f} rubbed the nose gently between warm paws.",
            f'"Now the warmth can stay," said {h}.',
            f'"And the sock can guard the window until morning," said {f}.',
            "The candle stood straight again, the nose grew cozy, and the room settled into a hush made for dreaming.",
        ]
        resolution = f"{h} shared warmth with {f} and blocked the draft with a folded sock"
        ending = "the candle stood straight while the warm nose rested peacefully"
    world.facts.update(
        problem="cold nose",
        discovery="the nose noticed a draft before either friend could feel it",
        cause="cold air was slipping through a gap by the window",
        resolution=resolution,
        ending=ending,
        clue="the shivering curtain and leaning candle flame",
        shared=True,
    )
    return " ".join(lines)


def _sneeze_story(world: World, params: StoryParams, rng: random.Random) -> str:
    h, f, room = world.child.label, world.friend.label, world.room
    if params.solution == "follow_clues":
        lines = [
            f"In {room}, {h}'s nose gave a tiny warning twitch just as bedtime began.",
            f'"Was that a sneeze waiting to happen?" asked {f}.',
            f'"Maybe," whispered {h}. "The tickle is hiding somewhere."',
            f"They listened together. A feather floated from the pillow, then another drifted from beneath the bed.",
            f'"The feathers are clues," said {f}. "Let us follow them before the big achoo arrives."',
            f"The trail led to a loose pillow seam. Inside it, an old feather had been poking the nose.",
            f"{h} and {f} shared the work: {h} held the pillow, while {f} stitched the seam with a silver thread.",
            f'"Achoo!' + '"' + f" said {h}, but it was only a small sneeze. 'We found you in time.'",
            f"The nose relaxed, the pillow became smooth, and the two friends shared a sleepy giggle before closing their eyes.",
        ]
        resolution = f"{h} and {f} followed the floating feathers and repaired the loose pillow seam"
        ending = "the smooth pillow held no prickly feather, and the nose rested quietly"
        clue = "feathers drifting from the pillow"
    else:
        lines = [
            f"At bedtime in {room}, {h}'s nose began to tickle.",
            f'"I think a sneeze is coming," said {h}.',
            f'"Then take my warm scarf," said {f}, sharing it carefully. "But wait—the curtain is dusty too."',
            f"They covered the nose with the scarf and looked behind the curtain, where a little cloud of dust waited for morning.",
            f"{f} opened the window only a finger's width, while {h} held the scarf in place.",
            f"The dust drifted out. The nose gave one tiny achoo, and then the tickle faded.",
            f'"Your scarf helped me breathe slowly," said {h}.',
            f'"Your nose helped us notice the dusty corner," replied {f}.',
            "They folded the scarf at the foot of the bed, where it could be shared again tomorrow.",
        ]
        resolution = f"{h} shared {f}'s warm scarf while they aired out a dusty corner"
        ending = "the shared scarf waited at the foot of the bed"
        clue = "dust trembling behind the curtain"
    world.facts.update(
        problem="a sneeze waiting in the nose",
        discovery="the nose gave a warning before the sneeze grew large",
        cause="a feather or dust was tickling the nose",
        resolution=resolution,
        ending=ending,
        clue=clue,
        shared=True,
    )
    return " ".join(lines)


def _lost_lullaby_story(world: World, params: StoryParams, rng: random.Random) -> str:
    h, f, room = world.child.label, world.friend.label, world.room
    if params.solution == "follow_clues":
        lines = [
            f"The bedtime song vanished from {room}, leaving {h} and {f} wide awake.",
            f'"I remember the first note," said {h}, wrinkling a thoughtful nose. "But the rest has gone away."',
            f'"Your nose is pointing toward something," said {f}.',
            "They followed its little wiggle to the music box, then to the sock drawer, and finally to the window seat.",
            "At each place, a soft humming sound answered them. The clues grew quieter near the moonlit cushion.",
            f"{h} lifted the cushion while {f} looked underneath. There lay the missing paper with the lullaby written on it.",
            f'"You found the words," said {f}.',
            f'"We found them together," said {h}, sharing the paper between them.',
            "They sang the song slowly. The room remembered every note, and sleep returned like a small boat to shore.",
        ]
        resolution = f"{h} and {f} followed the nose's clues to the missing lullaby"
        ending = "the recovered song carried both friends gently into sleep"
        clue = "the nose turning toward each faint humming sound"
    else:
        lines = [
            f"In {room}, the lullaby seemed to hide just when {h} needed it.",
            f"{h} sniffed the air. A warm cinnamon smell came from {f}'s little lantern.",
            f'"Let us share the lantern light," said {f}. "Perhaps the song is hiding in the shadows."',
            f"They held the lantern between them and searched the bedside table, where a paper star cast a crooked shadow.",
            f"The shadow looked like a musical note. Beneath the star they found the missing song card.",
            f'"My nose found the cinnamon, and your lantern found the shadow," said {h}.',
            f'"Sharing clues makes a brighter search," answered {f}.',
            "They placed the card beside the lantern and sang until the shadows grew soft.",
        ]
        resolution = f"{h} and {f} shared the lantern and found the song card beneath a paper star"
        ending = "the lantern glowed beside the song card as sleep came near"
        clue = "the cinnamon scent leading toward the lantern"
    world.facts.update(
        problem="a missing lullaby",
        discovery="the nose noticed a clue that pointed toward the lost song",
        cause="the lullaby had slipped beneath or behind a familiar bedroom object",
        resolution=resolution,
        ending=ending,
        clue=clue,
        shared=True,
    )
    return " ".join(lines)


def _darkness_story(world: World, params: StoryParams, rng: random.Random) -> str:
    h, f, room = world.child.label, world.friend.label, world.room
    if params.solution == "lantern":
        lines = [
            f"When the lamp went out in {room}, {h}'s nose became the first thing to find the dark.",
            f'"I cannot see my way to bed," said {h}.',
            f'"Share my lantern," said {f}. "But notice the warm breeze on your nose."',
            "The breeze curled toward the bookcase. Behind a storybook, they found the loose cord that had pulled the lamp plug.",
            f"{h} held the lantern while {f} tucked the cord safely back into place.",
            f'"The nose found the direction," said {f}.',
            f'"The lantern let us follow it," said {h}.',
            "The lamp returned with a golden blink, and its light reached both beds.",
            "They shared the lantern's glow for one last page, then let the room become peacefully dark.",
        ]
        resolution = f"{h} and {f} shared a lantern and followed the warm breeze to the loose lamp cord"
        ending = "the lamp glowed softly over both beds before bedtime darkness returned"
        clue = "the warm breeze moving across the nose"
    else:
        lines = [
            f"The room turned dark in {room}, and {h} reached for the blue blanket.",
            f'"Stay close," said {f}. "We can share the blanket until the moon returns."',
            f"{h}'s nose touched the cool air and pointed toward the window.",
            f'"There is a draft," whispered {h}.',
            f"They pulled the blanket around both shoulders and placed a pillow along the window ledge.",
            "The draft softened. A stripe of moonlight appeared, showing the safe path to the beds.",
            f'"Your nose noticed the dark\'s little secret," said {f}.',
            f'"Your blanket made it less scary," said {h}.',
            "Together they climbed into bed, warm enough to let the moon finish its quiet work.",
        ]
        resolution = f"{h} and {f} shared the blanket and blocked the draft with a pillow"
        ending = "the moonlight returned while both friends slept under the shared blanket"
        clue = "the cool draft touching the nose"
    world.facts.update(
        problem="a suddenly dark room",
        discovery="the nose could notice a draft or warm direction when eyes could not",
        cause="the lamp failed and a draft changed the room's air",
        resolution=resolution,
        ending=ending,
        clue=clue,
        shared=True,
    )
    return " ".join(lines)


BUILDERS = {
    "cold": _cold_story,
    "sneeze": _sneeze_story,
    "lost_lullaby": _lost_lullaby_story,
    "darkness": _darkness_story,
}


def generate_story(world: World, params: StoryParams) -> str:
    _validate(params)
    rng = random.Random(world.seed ^ 0x51A7B2)
    return BUILDERS[params.problem](world, params, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.child.label
    f = world.facts
    return [
        QAItem(
            question=f"What did {h}'s nose help the friends notice?",
            answer=f"{h}'s nose helped the friends notice {f['discovery']}.",
        ),
        QAItem(
            question="What caused the bedtime trouble?",
            answer=f"The trouble began because {f['cause']}.",
        ),
        QAItem(
            question=f"How did {h} and {world.friend.label} solve the problem?",
            answer=f"They solved it when {f['resolution']}.",
        ),
        QAItem(
            question="What clue appeared before the solution?",
            answer=f"The important clue was {f['clue']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a nose be useful at bedtime?",
            answer="A nose can notice smells, dust, cool drafts, and warm air, so it may help someone understand what is happening nearby.",
        ),
        QAItem(
            question="Why is sharing helpful in a bedtime story?",
            answer="Sharing lets friends combine comfort, tools, and ideas so a problem becomes easier to solve together.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue placed early in a story that hints at something important that will happen later.",
        ),
        QAItem(
            question="Why should friends listen to small clues?",
            answer="Small clues can reveal the cause of a problem before it grows, giving friends time to choose a gentle solution.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle bedtime story in which a nose notices an important clue.",
        f"Tell a cozy story about {world.child.label} and {world.friend.label} sharing help before sleep.",
        "Use foreshadowing, friendship, and a concrete nighttime problem to create a warm ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.child, world.friend, world.nose, world.blanket]:
        lines.append(
            f"  {ent.id:8} {ent.kind:10} label={ent.label!r} owner={ent.owner!r} "
            f"meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  room={world.room!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world, params)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid() -> bool:
    try:
        import asp
        model = asp.one_model(asp_program("cold", "share_blanket"))
        names = {sym.name for sym in model}
        return {"needs_help", "shared", "ready_for_sleep"}.issubset(names)
    except Exception:
        return False


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
            model = asp.one_model(asp_program("cold", "share_blanket"))
            print("ASP model:", ", ".join(str(atom) for atom in model))
        except ImportError:
            print("ASP mode requires the optional clingo dependency.")
            sys.exit(1)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mina", "Bear", ROOMS[0], "cold", "share_blanket", "cozy"),
            StoryParams("Theo", "Owl", ROOMS[1], "sneeze", "follow_clues", "whispering"),
            StoryParams("Lulu", "Bunny", ROOMS[2], "lost_lullaby", "lantern", "playful"),
            StoryParams("Nora", "Fox", ROOMS[3], "darkness", "share_blanket", "cozy"),
        ]
        for i, params in enumerate(curated):
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for attempt in range(args.n):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} in {sample.params.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
