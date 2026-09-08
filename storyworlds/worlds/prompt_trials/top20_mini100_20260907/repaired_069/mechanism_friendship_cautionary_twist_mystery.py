#!/usr/bin/env python3
"""Mystery-leaning friendship storyworld about a mechanism, caution, and a twist."""

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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "owl", "cat", "dog", "mouse", "raccoon", "badger", "rabbit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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
    detective: str = "Mina"
    friend: str = "Jory"
    caution: str = "Bell"
    place: str = "workshop"
    clue: int = 0
    opening: int = 0
    twist: int = 0
    caution_line: int = 0
    ending: int = 0


NAMES = ["Mina", "Jory", "Tess", "Bram", "Lio", "Nora", "Pico", "Zin"]
CAUTIONS = ["Bell", "Rin", "Sage", "Dove", "Moss", "Fenn"]
PLACES = ["workshop", "attic", "garden shed", "clock room", "library corner", "boathouse"]

OPENINGS = [
    "In the {place}, {detective} noticed something odd before breakfast.",
    "At the {place}, {detective} and {friend} were already whispering about the mystery.",
    "The {place} was quiet, except for one curious sound that kept returning.",
    "Nobody in the {place} could explain the tiny noise, so {detective} listened harder.",
    "Late in the morning, {detective} found a strange pattern near the old machine in the {place}.",
    "A careful search of the {place} began when {friend} saw a clue under the table.",
]

CLUES = [
    {
        "premise": "A little mechanism inside the old tin door kept clicking by itself.",
        "mystery": "click... click... click",
        "problem": "Each click nudged a hidden latch, and the supply box kept opening on its own.",
        "wrong_guess": "{friend} thought a mouse was pulling the latch string.",
        "caution": "{caution} warned, 'Don't yank it yet. We should follow the sound first.'",
        "observation": "The clicks always came after a shaky shelf touched the wall.",
        "action": "{detective} slid a felt pad beneath the shelf while {friend} held the latch still.",
        "result": "The clicks stopped, and the supply box stayed shut until someone chose to open it.",
        "twist": "Then they found the real culprit: a loose spoon had been tapping the shelf leg all along.",
        "lesson": "A mystery can look like a trick until someone watches the mechanism closely.",
        "ending": "The spoon slept in a cup beside the now-quiet shelf.",
        "object": "tin door latch",
    },
    {
        "premise": "A wind-up music box in the corner kept starting and stopping by itself.",
        "mystery": "tink... trrriiiing",
        "problem": "Its lid opened when nobody touched it, spilling the note cards onto the floor.",
        "wrong_guess": "{friend} suspected the music box was haunted.",
        "caution": "{caution} said, 'Let's not blame ghosts before we check the spring.'",
        "observation": "The lid popped whenever the window rattled from the breeze.",
        "action": "{detective} tied the window shut while {friend} covered the music box with a soft cloth.",
        "result": "The notes stayed put, and the room grew calm again.",
        "twist": "The twist was simple: a bent key on the window hook had been striking the latch.",
        "lesson": "Careful watching can turn a spooky guess into a clear answer.",
        "ending": "The bent key rested on the sill like a tiny rescued clue.",
        "object": "music box",
    },
    {
        "premise": "A toy crane in the playroom kept dropping blocks from its claw.",
        "mystery": "clack! thump!",
        "problem": "Every time the crane turned left, the blocks tumbled into the same corner.",
        "wrong_guess": "{friend} blamed the blocks for being too slippery.",
        "caution": "{caution} advised, 'Wait. A pattern is trying to tell us something.'",
        "observation": "The claw slipped only when a rug fringe caught the wheel.",
        "action": "{detective} folded the fringe back while {friend} tested the wheel again and again.",
        "result": "The crane lifted the blocks straight and true.",
        "twist": "The twist was that a tiny nail had worked loose and only needed one careful twist to tighten it.",
        "lesson": "A small fix can solve a problem that looks larger than it is.",
        "ending": "Three blocks stood in a neat tower beside the repaired crane.",
        "object": "toy crane",
    },
    {
        "premise": "An old lantern in the hallway lit up whenever the door creaked.",
        "mystery": "hum... flicker",
        "problem": "The sudden light startled everyone, and the hallway kept feeling like a secret passage.",
        "wrong_guess": "{friend} thought someone was secretly turning the lantern on.",
        "caution": "{caution} said, 'We should look for a switch, not a spy.'",
        "observation": "The glow came only when the brass hook on the door brushed a metal plate.",
        "action": "{detective} wrapped the hook in cloth while {friend} held the lantern steady.",
        "result": "The light stayed off until nightfall, when someone chose to use it.",
        "twist": "The twist was that the metal plate had been serving as a very accidental button.",
        "lesson": "Not every strange event is a mystery person; sometimes it is just a mechanism.",
        "ending": "The lantern hung still, shining only on purpose.",
        "object": "hallway lantern",
    },
    {
        "premise": "A nest of drawers in the study kept sliding open one by one.",
        "mystery": "scrrrk... thud",
        "problem": "Papers slipped out and made the floor look like a trail of clues.",
        "wrong_guess": "{friend} blamed a draft from the chimney.",
        "caution": "{caution} warned, 'First we test, then we guess.'",
        "observation": "Only the middle drawer moved when the cabinet leaned on one uneven leg.",
        "action": "{detective} placed a folded card under the leg while {friend} gathered the papers.",
        "result": "The drawers stayed closed, and the papers went back where they belonged.",
        "twist": "The twist was that a marble had rolled beneath the cabinet and made the leg wobble.",
        "lesson": "A stable base can solve a trouble that seems to come from everywhere.",
        "ending": "The marble rolled into {friend}'s palm, bright as a found moon.",
        "object": "study cabinet",
    },
    {
        "premise": "The garden gate clicked in the night without anyone near it.",
        "mystery": "tik-tik",
        "problem": "Every click made the lock swing open a little farther.",
        "wrong_guess": "{friend} said a sneaky cat must be the thief.",
        "caution": "{caution} replied, 'Let's follow the clicks before we blame paws.'",
        "observation": "The latch moved only when the vine above it swayed in the wind.",
        "action": "{detective} tied the vine back and {friend} placed a stone under the gate to steady it.",
        "result": "The gate stayed shut through the whole evening.",
        "twist": "The twist was that a seed pod had fallen into the latch and kept nudging it open.",
        "lesson": "A good friend watches with you until the hidden cause shows itself.",
        "ending": "The seed pod sat in a jar beside the safe, still gate.",
        "object": "garden gate",
    },
]

TWISTS = [
    "The strange sound came from a spoon, not a thief.",
    "The mystery was caused by a bent key tapping metal.",
    "The answer hid in a loose nail that needed tightening.",
    "The culprit was a marble, not a monster.",
    "A seed pod, not a sneaky cat, made the lock move.",
    "The real clue was a hook brushing a plate.",
]

CAUTION_LINES = [
    "'Wait,' said {caution}. 'If we rush, we might break the mechanism.'",
    "'Careful,' warned {caution}. 'A small part can matter more than a big guess.'",
    "'Let's watch twice before we touch anything,' {caution} said.",
    "'The truth is usually quieter than the rumor,' {caution} whispered.",
]

ENDINGS = [
    "By evening, the room felt friendly again, and the solved mechanism sat quietly in the light.",
    "At last, the friends smiled at the repaired thing, happy that the mystery had an ordinary answer.",
    "When the sun set, the little mechanism rested still, and the friends knew they had done well.",
    "The final image was simple: a calm room, a fixed machine, and two friends sharing a proud grin.",
]


ASP_RULES = r"""
#show mystery/1.
#show solved/1.
#show twist/1.

mystery(X) :- clue(X).
solved(X) :- clue(X), fixed(X).
twist(X) :- clue(X), hidden_cause(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue", "mechanism"),
            asp.fact("fixed", "mechanism"),
            asp.fact("hidden_cause", "mechanism"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with friendship, caution, and a twist.")
    ap.add_argument("--detective", choices=NAMES)
    ap.add_argument("--friend", choices=NAMES)
    ap.add_argument("--caution", choices=CAUTIONS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", type=int, choices=range(len(CLUES)))
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
    d = args.detective or rng.choice(NAMES)
    f = args.friend or rng.choice([n for n in NAMES if n != d])
    c = args.caution or rng.choice(CAUTIONS)
    p = args.place or rng.choice(PLACES)
    return StoryParams(
        seed=args.seed,
        detective=d,
        friend=f,
        caution=c,
        place=p,
        clue=args.clue if args.clue is not None else rng.randrange(len(CLUES)),
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        caution_line=rng.randrange(len(CAUTION_LINES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.detective == params.friend:
        raise StoryError("detective and friend must be different characters")

    world = World()
    detective = world.add(Entity(id=params.detective, kind="character", type="mouse", label=params.detective))
    friend = world.add(Entity(id=params.friend, kind="character", type="rabbit", label=params.friend))
    caution = world.add(Entity(id=params.caution, kind="character", type="owl", label=params.caution))
    room = world.add(Entity(id=params.place, kind="place", type="place", label=params.place))
    clue = CLUES[params.clue % len(CLUES)]

    detective.meters["curiosity"] = 0.9
    friend.meters["imagination"] = 0.8
    caution.meters["care"] = 1.0
    detective.memes["certainty"] = 0.2
    friend.memes["certainty"] = 0.4
    caution.memes["certainty"] = 0.7

    common = {
        "detective": detective.id,
        "friend": friend.id,
        "caution": caution.id,
        "place": room.label,
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**common))
    world.say(clue["premise"])
    world.say(f"The mystery sound went {clue['mystery']}, and everyone stopped to listen.")
    world.say(CAUTION_LINES[params.caution_line % len(CAUTION_LINES)].format(**common))
    world.say(clue["problem"])
    world.say(clue["wrong_guess"].format(**common))
    world.say(clue["observation"])
    world.say(f"{detective.id} said, 'The pattern points to the mechanism, not a secret troublemaker.'")
    world.say(f"{friend.id} answered, 'Then let's test it together.'")
    world.say(clue["action"].format(**common))
    world.say(clue["result"])
    world.say(f"Then came the twist: {TWISTS[params.twist % len(TWISTS)]}")
    world.say(clue["twist"])
    world.say(f"{caution.id} smiled and said, 'Good friends make better detectives when they stay careful.'")
    world.say(clue["lesson"])
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    detective.memes["relief"] = 1.0
    friend.memes["relief"] = 1.0
    caution.memes["relief"] = 1.0
    world.facts.update(
        detective=detective,
        friend=friend,
        caution=caution,
        room=room,
        clue=clue,
        mechanism="mechanism",
        solved=True,
        twist_text=TWISTS[params.twist % len(TWISTS)],
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
        f"Write a child-friendly mystery about {f['detective'].id} and {f['friend'].id} investigating a strange mechanism in the {f['room'].label}.",
        f"Tell a friendship story where caution helps solve a puzzle and the answer has a twist.",
        "Write a short mystery with spoken dialogue, a careful test, and a clear ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = f["clue"]
    return [
        QAItem(
            question="What made the friends think the problem was mysterious?",
            answer=f"The strange sound and the odd repeated behavior made it feel like a mystery. The mechanism kept acting on its own.",
        ),
        QAItem(
            question=f"What caution did {f['caution'].id} give?",
            answer=f"{f['caution'].id} warned them to be careful and to check the mechanism before making guesses.",
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=clue["observation"],
        ),
        QAItem(
            question="How did the friendship matter in the story?",
            answer=(
                f"{f['detective'].id} and {f['friend'].id} worked together instead of arguing. "
                f"One watched the clue, and the other tested the fix."
            ),
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {f['twist_text'].rstrip('.')}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something happen, like a latch, spring, or wheel.",
        ),
        QAItem(
            question="What does caution mean in a story like this?",
            answer="Caution means being careful and not rushing into action when a problem could be made worse by a hasty choice.",
        ),
        QAItem(
            question="Why is a twist useful in a mystery?",
            answer="A twist changes what the reader thought was true and reveals a different, often simpler, answer.",
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show mystery/1.\n#show solved/1.\n#show twist/1.")
    model = asp.one_model(program)
    py = {("mechanism",)}
    clingo_mystery = set(asp.atoms(model, "mystery"))
    clingo_solved = set(asp.atoms(model, "solved"))
    clingo_twist = set(asp.atoms(model, "twist"))
    if clingo_mystery == py and clingo_solved == py and clingo_twist == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  mystery:", sorted(clingo_mystery))
    print("  solved:", sorted(clingo_solved))
    print("  twist:", sorted(clingo_twist))
    return 1


CURATED = [
    StoryParams(detective="Mina", friend="Jory", caution="Bell", place="workshop", clue=0),
    StoryParams(detective="Tess", friend="Bram", caution="Moss", place="attic", clue=1, opening=3, twist=1),
    StoryParams(detective="Lio", friend="Nora", caution="Sage", place="library corner", clue=4, opening=1, twist=3),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/1.\n#show solved/1.\n#show twist/1."))
    return sorted(set(asp.atoms(model, "mystery")))


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
        print(asp_program("#show mystery/1.\n#show solved/1.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} ASP-suggested mystery facts")
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
            header = f"### {sample.params.detective}: mystery in the {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
