#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    __import__("os").path.dirname(
        __import__("os").path.dirname(
            __import__("os").path.dirname(
                __import__("os").path.dirname(__import__("os").path.abspath(__file__))
            )
        )
    ),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective_name: str
    friend_name: str
    mystery_place: str
    seed: Optional[int] = None


LOCATIONS = [
    "the attic of the old library",
    "the back room of the clock shop",
    "the greenhouse behind the museum",
    "the little station by the river",
]
NAMES = ["Mina", "Leo", "Iris", "Owen", "Pia", "Noah", "Ruby", "Sam"]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    case_notes: list[str] = field(default_factory=list)
    solved: bool = False
    caution_heeded: bool = False
    twist_found: bool = False
    mechanism_seen: bool = False
    friendship_strong: bool = False
    danger_avoided: bool = False

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict(sorted(e.meters.items()))}")
            if e.memes:
                bits.append(f"memes={dict(sorted(e.memes.items()))}")
            lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
        lines.append(f"  solved={self.solved}")
        lines.append(f"  caution_heeded={self.caution_heeded}")
        lines.append(f"  twist_found={self.twist_found}")
        lines.append(f"  mechanism_seen={self.mechanism_seen}")
        lines.append(f"  friendship_strong={self.friendship_strong}")
        lines.append(f"  danger_avoided={self.danger_avoided}")
        return "\n".join(lines)


ARCS = [
    {
        "premise": [
            "At dusk, Detective {d} and friend {f} entered {place} after someone whispered about a missing key and a strange mechanism under the floorboards.",
            "Detective {d} and friend {f} arrived at {place} with a lantern and a notebook. The place was quiet, but a hidden mechanism kept clicking behind the walls.",
        ],
        "clue": [
            "A brass seam on the shelf matched the click. The mechanism was not a monster at all, but a small clockwork latch hidden in plain sight.",
            "The ticking came in threes, like a toy winding itself. That pattern told {d} the mechanism had been built to open only when pushed the right way.",
        ],
        "friendship": [
            "\"I trust your eyes,\" said {f}. {d} answered, \"And I trust your courage.\" Their friendship made them slow down instead of rushing the door.",
            "\"Stay close,\" {d} said. {f} nodded, and the two friends checked each corner together, sharing the lantern and their nerves.",
        ],
        "cautionary": [
            "They nearly tugged the latch too hard, but {f} stopped them in time. \"Careful,\" {f} whispered. \"Old mechanisms can snap and hide a worse surprise.\"",
            "{d} reached for the handle, then froze when {f} pointed at a thin wire. The caution was wise: one wrong pull could have slammed the door shut forever.",
        ],
        "twist": [
            "When they lifted the hatch gently, they found a tiny kitten inside, guarding the lost key with bright yellow eyes.",
            "The secret was not stolen treasure at all. The mechanism had been hiding a music box that played whenever the wind touched its gears.",
        ],
        "resolution": [
            "{d} picked up the key, and {f} laughed softly when the kitten rubbed against their shoes. The mystery ended as the hidden room opened like a sigh.",
            "{f} wound the music box once, and the little tune filled {place}. The strange clicking stopped, proving the mechanism only wanted to be heard.",
        ],
        "ending": [
            "By moonlight, the friends left {place} together, their lantern glowing over one solved mystery and two relieved smiles.",
            "The next click from the wall was only the clock in {d}'s pocket, and both friends walked home with the case safely closed.",
        ],
    },
    {
        "premise": [
            "{d} and {f} were searching {place} for a note that had vanished from a locked drawer. A mechanism beneath the desk kept making the same soft click.",
            "The mystery began with a missing envelope and a quiet room. Detective {d} and friend {f} listened to a hidden mechanism ticking under {place}.",
        ],
        "clue": [
            "{f} noticed dust on one side of the drawer and none on the other. The mechanism had slid the note sideways, not swallowed it.",
            "A silver knob was warm to the touch. That meant the mechanism had been used recently, and someone had not gone far.",
        ],
        "friendship": [
            "\"You look low to the floor,\" said {d}. \"Then I will watch the ceiling,\" replied {f}. Working together made the room feel less lonely.",
            "\"I get scared of locked places,\" {f} admitted. {d} squeezed their hand and said, \"Then we solve it together.\"",
        ],
        "cautionary": [
            "They were careful not to force the drawer. {d} knew a jammed mechanism could tear the paper or pinch a finger.",
            "{f} warned, \"Don't yank it. If the latch is old, it may hide a trick.\" Their caution kept the drawer steady.",
        ],
        "twist": [
            "The missing envelope slid out from behind the drawer after all. Someone had tucked it there on purpose to keep it safe from rain.",
            "Inside the drawer was a second note: the first message had been moved by a helpful neighbor, not a thief.",
        ],
        "resolution": [
            "{d} read the note aloud, and {f} smiled when the mystery became a misunderstanding instead of a crime.",
            "The mechanism clicked once more, then stilled. It had only been a spring-loaded guard, and the friends had uncovered the truth gently.",
        ],
        "ending": [
            "Outside {place}, rain began to fall, but the rescued note stayed dry in {f}'s pocket.",
            "The friends pinned the harmless note to the board, and the quiet room finally felt ordinary again.",
        ],
    },
    {
        "premise": [
            "On a stormy evening, {d} and {f} explored {place} after hearing that a mechanism had locked every cabinet at once.",
            "The old building at {place} shivered in the wind. Detective {d} and friend {f} followed the sound of a hidden mechanism into the dark.",
        ],
        "clue": [
            "A line of crumbs led under the rug. The mechanism was not broken; it was being fed by tiny bits of metal dust from the floor.",
            "{f} spotted a bent paperclip near the baseboard. That clue fit the mechanism like a missing tooth.",
        ],
        "friendship": [
            "\"I don't like the dark hall,\" {f} said. {d} replied, \"Then keep my lantern. I will keep your back safe.\"",
            "{d} said, \"We can leave if you want.\" {f} shook their head. \"Not yet. Not while we are solving this together.\"",
        ],
        "cautionary": [
            "They moved slowly, because the floorboards looked thin. A careful step could prevent a loud crack and a dangerous fall.",
            "{d} knelt to examine the lock, but {f} stopped them from slipping a pin inside. \"Careful,\" {f} warned, \"the mechanism may spring back.\"",
        ],
        "twist": [
            "The locked cabinets were empty on purpose. The mechanism had been built by the owner to keep curious mice out of the flour.",
            "Behind the cabinet doors sat a row of candles, not valuables. The twist was that the mystery was a pantry protection device.",
        ],
        "resolution": [
            "{d} and {f} reset the latch so it would open more gently. The owner had meant well, and the friends had learned the secret without breaking it.",
            "{f} laughed in relief. \"So the culprit was caution itself.\" {d} nodded, and together they left the cabinets undamaged.",
        ],
        "ending": [
            "By the time they stepped back into the rain, {place} was quiet again, and the mechanism no longer sounded threatening.",
            "The last cabinet click faded behind them, while the friends shared one umbrella and one solved puzzle.",
        ],
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = "|".join([params.detective_name, params.friend_name, params.mystery_place])
    seed = int.from_bytes(hashlib.sha256(stable.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    d = args.detective_name or rng.choice(NAMES)
    f = args.friend_name or rng.choice([n for n in NAMES if n != d])
    place = args.place or rng.choice(LOCATIONS)
    return StoryParams(detective_name=d, friend_name=f, mystery_place=place)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery world with a mechanism, friendship, caution, and a twist.")
    ap.add_argument("--detective-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--place")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_arc(params: StoryParams) -> dict:
    rng = _rng_for(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    return arc


def generate(params: StoryParams) -> StorySample:
    arc = _pick_arc(params)
    rng = _rng_for(params)
    variant = (params.seed or rng.randrange(10_000)) % 97
    chosen = {}
    for key in ["premise", "clue", "friendship", "cautionary", "twist", "resolution", "ending"]:
        options = arc[key]
        chosen[key] = options[variant % len(options)]

    d = params.detective_name
    f = params.friend_name
    place = params.mystery_place
    rendered = {
        key: chosen[key].format(d=d, f=f, place=place)
        for key in chosen
    }

    world = World(params=params)
    detective = world.add(Entity(id=d, kind="character", type="detective", label="detective", meters={"attention": 1.0}, memes={"curiosity": 1.0}))
    friend = world.add(Entity(id=f, kind="character", type="friend", label="friend", meters={"bravery": 1.0}, memes={"trust": 1.0}))
    mechanism = world.add(Entity(id="mechanism", kind="thing", type="mechanism", label="mechanism", phrase="a hidden mechanism", meters={"click": 1.0}))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="clue", phrase="a small clue"))
    world.mechanism_seen = True
    world.friendship_strong = True
    world.caution_heeded = True
    world.twist_found = True
    world.danger_avoided = True
    world.solved = True
    detective.meters["attention"] = 2.0
    friend.meters["bravery"] = 2.0
    detective.memes["curiosity"] = 2.0
    friend.memes["trust"] = 2.0
    mechanism.meters["click"] = 0.0
    clue.meters["found"] = 1.0

    for i, key in enumerate(["premise", "clue", "friendship", "cautionary", "twist", "resolution", "ending"]):
        if i:
            world.para()
        world.say(rendered[key])

    prompts = [
        "Write a child-friendly mystery about a hidden mechanism and a surprising twist.",
        f"Tell a story where {d} and {f} solve a clue by being careful and trusting each other.",
        "Write a short mystery ending with the truth about what the mechanism was for.",
    ]

    story_qa = [
        QAItem(question="What kind of story is this?", answer="It is a mystery story about a hidden mechanism, careful choices, and a surprising twist."),
        QAItem(question=f"Who worked together in {place}?", answer=f"{d} and {f} worked together and trusted each other while solving the mystery."),
        QAItem(question="What did the friends need to be careful about?", answer="They needed to be careful not to force the old mechanism too hard, because it could snap or shut them out."),
        QAItem(question="What was the twist?", answer=rendered["twist"]),
        QAItem(question="How did the story end?", answer=f"{rendered['resolution']} {rendered['ending']}"),
    ]

    world_qa = [
        QAItem(question="What is a mechanism?", answer="A mechanism is a set of parts that move together to make something work, like a latch, clock, or spring."),
        QAItem(question="What does caution mean?", answer="Caution means being careful and thinking before acting so that nobody gets hurt or makes a bigger problem."),
        QAItem(question="What does friendship do in a mystery?", answer="Friendship helps the characters stay brave, listen to each other, and solve problems together."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def generate_prompts() -> str:
    return ""


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
% Inline ASP twin for a mystery about a mechanism, friendship, caution, and twist.
story(mystery).
feature(friendship).
feature(cautionary).
feature(twist).
mechanism(hidden_mechanism).
valid_story :- story(mystery), feature(friendship), feature(cautionary), feature(twist), mechanism(hidden_mechanism).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("story", "mystery"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("mechanism", "hidden_mechanism"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if any(sym.name == "valid_story" for sym in model):
        sample = generate(StoryParams("Mina", "Leo", "the attic of the old library", seed=7))
        if "mechanism" in sample.story.lower() and "friend" in sample.story.lower():
            print("OK: ASP and Python story gates agree.")
            return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid_story/mystery/friendship/cautionary/twist/mechanism")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mina", "Leo", "the attic of the old library", seed=base_seed + 1),
            StoryParams("Iris", "Owen", "the back room of the clock shop", seed=base_seed + 2),
            StoryParams("Pia", "Sam", "the greenhouse behind the museum", seed=base_seed + 3),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
