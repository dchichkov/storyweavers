#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "storyworlds" / "results.py").is_file()),
    Path(__file__).resolve().parents[5],
)
sys.path.insert(0, str(_REPO_ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_one: str
    child_two: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def render(self) -> str:
        return "\n\n".join(paragraph for paragraph in self.paragraphs if paragraph)


NAMES = ["Eilidh", "Hamish", "Isla", "Callum", "Mairi", "Rowan", "Fiona", "Alasdair"]
PLACES = [
    "beside Loch Lomond",
    "in the Cairngorms",
    "above a quiet sea loch",
    "near a little Highland village",
]


ARCS = [
    {
        "key": "music_box",
        "source": "a tiny music box",
        "sound": "rrr-tick...ting",
        "premise": (
            "In a snug Scottish cottage {place}, {a} and {b} found a parcel "
            "wrapped in tartan paper beside the bedtime lamp. A note said it "
            "was a gift from Gran, but the box inside was still a mystery."
        ),
        "problem": (
            "When they set the parcel down, it gave a little "
            "{sound}. {a} frowned at the dark window."
        ),
        "first_line": "\"That sounds like a clock counting down,\" said {a}.",
        "second_line": "\"Maybe something inside is winding itself up,\" said {b}. "
        "\"Let's not guess. We can listen together.\"",
        "clue": (
            "They held still and listened again. The last bright ting came at "
            "the same place each time, like the end of a tune, not a clock's "
            "count. {a}'s worry softened: the sound had a pattern."
        ),
        "action": (
            "{a} said, \"You were right about listening first. Will you help me "
            "open it slowly?\" {b} nodded, and they loosened the paper and lifted "
            "the lid together."
        ),
        "reveal": (
            "Inside sat a little music box. Its key had turned a fraction in "
            "the parcel, making the soft ticking and the last clear note."
        ),
        "resolution": (
            "They wound the key gently, and the music box played a sleepy "
            "lullaby. {a} smiled at {b}; the strange sound had become a song "
            "they could share."
        ),
        "ending": (
            "The parcel rested open by the lamp while its tiny melody floated "
            "through the cottage and into their dreams."
        ),
        "method": "They listened for the repeating pattern, then opened the parcel gently.",
        "outcome": "The sound came from a music box whose key had turned in transit.",
    },
    {
        "key": "rainstick",
        "source": "a little rainstick",
        "sound": "shhh-ka, shhh-ka",
        "premise": (
            "In a snug Scottish cottage {place}, {a} and {b} carried a tartan-wrapped "
            "parcel to the bedside rug. Gran had sent it for their quiet-time "
            "shelf, though neither knew what was tucked inside."
        ),
        "problem": (
            "A soft {sound} came from the parcel, as if a tiny shower had "
            "started indoors. {a} glanced up at the ceiling."
        ),
        "first_line": "\"The roof must be leaking,\" whispered {a}.",
        "second_line": "\"I don't see a drip,\" replied {b}. \"Let's check the parcel "
        "before we worry.\"",
        "clue": (
            "They tilted the parcel just a little. The shushing sound slid from "
            "one end to the other and stopped when they held it still. There "
            "was no wet patch on the rug; the sound was moving inside the box."
        ),
        "action": (
            "{a} said, \"You noticed it moved. Let's open it over the rug.\" "
            "{b} carefully untied the string while {a} held the paper wide."
        ),
        "reveal": (
            "A small rainstick lay inside. Tiny seeds trickled through its "
            "hollow middle, making a gentle rain sound whenever it tipped."
        ),
        "resolution": (
            "{a} touched the dry rug and laughed softly. {b} turned the "
            "rainstick once, and the two agreed it made a lovely sound for a "
            "quiet evening, not a leaky roof."
        ),
        "ending": (
            "They set the rainstick beside the lamp, where its last hush faded "
            "like rain far away beyond the window."
        ),
        "method": "They tilted the parcel carefully and checked the rug before opening it.",
        "outcome": "A rainstick's tiny seeds made the shushing sound as they slid inside.",
    },
    {
        "key": "puffin_whistle",
        "source": "a wooden puffin whistle",
        "sound": "peep-ooo",
        "premise": (
            "At bedtime in a snug Scottish cottage {place}, {a} and {b} spotted "
            "a small parcel under the window. Its tartan paper was tied with "
            "blue string, and Gran's handwriting curled across the label."
        ),
        "problem": (
            "As they carried it to the rug, the parcel gave a tiny "
            "{sound}. {a} stopped short and listened toward the window."
        ),
        "first_line": "\"A bird must be trapped in there,\" said {a}.",
        "second_line": "\"It might be a toy making that call,\" said {b}. "
        "\"Let's find out together, gently.\"",
        "clue": (
            "The sound came again only when {b} lifted one end. It was the same "
            "two-note call, with no flutter or scratching afterward. {a} "
            "realized the parcel was making the sound when it moved."
        ),
        "action": (
            "{a} asked, \"Will you hold the string while I open the paper?\" "
            "{b} agreed, and they untied the parcel without pulling or shaking it."
        ),
        "reveal": (
            "A smooth wooden puffin whistle was nestled in soft cloth. A small "
            "air hole had been covered by the cloth, and shifting the parcel "
            "made it give its little call."
        ),
        "resolution": (
            "{a} looked relieved, and {b} showed how to blow the whistle softly. "
            "It answered with a gentle peep, and now they both knew where the "
            "sound came from."
        ),
        "ending": (
            "The puffin rested on the bedside table, quiet beneath the moon, "
            "while the two children settled under their blankets."
        ),
        "method": "They noticed the sound followed the parcel's movement and opened it gently.",
        "outcome": "A wooden puffin whistle had made its two-note call as the parcel shifted.",
    },
    {
        "key": "sheep_bell",
        "source": "a knitted sheep with a little bell",
        "sound": "jingle...jingle",
        "premise": (
            "A tartan parcel waited on the bedside rug in a snug Scottish cottage "
            "{place}. {a} and {b} had just said goodnight to the last bright "
            "window when they heard something stir inside it."
        ),
        "problem": (
            "The parcel gave a faint {sound}. {a} pulled the blanket closer "
            "around their shoulders."
        ),
        "first_line": "\"There could be a kitten in there,\" said {a}.",
        "second_line": "\"A kitten would need air,\" said {b}. \"Let's ask Gran's "
            "note and open the parcel carefully.\"",
        "clue": (
            "The note was tucked beneath the bow: 'For your bedside shelf.' "
            "When {b} lifted the parcel, the jingling came from its bottom, "
            "not from a paw or a mew. {a} began to see another explanation."
        ),
        "action": (
            "{a} said, \"Let's open it together so nothing gets startled.\" "
            "{b} held the parcel steady while {a} eased off the paper."
        ),
        "reveal": (
            "A soft knitted sheep was tucked inside. A tiny bell sewn beneath "
            "its woolly chin had jingled whenever the parcel moved."
        ),
        "resolution": (
            "{a} gave the sheep a careful pat and felt glad there was no kitten "
            "waiting in a box. {b} smiled; the two had checked their guesses "
            "together instead of letting them grow."
        ),
        "ending": (
            "The little sheep sat by the lamp, its bell quiet, as the cottage "
            "settled into a peaceful night."
        ),
        "method": "They read Gran's note, listened to where the bell rang, and opened the parcel together.",
        "outcome": "A bell sewn beneath a knitted sheep's chin had made the jingling sound.",
    },
    {
        "key": "star_projector",
        "source": "a small star projector",
        "sound": "click...whirr",
        "premise": (
            "In a snug Scottish cottage {place}, {a} and {b} found a parcel "
            "wrapped in silver paper at the foot of the bed. Gran had promised "
            "them something for their room, but the parcel had not yet been opened."
        ),
        "problem": (
            "A quiet {sound} came from inside. {a} looked at the dark glass "
            "of the window, where no stars showed through the cloud."
        ),
        "first_line": "\"That sounds like thunder starting,\" said {a}.",
        "second_line": "\"Thunder rumbles longer,\" said {b}. \"Let's see what "
            "makes this small sound before we decide.\"",
        "clue": (
            "They listened once more. The click came first, then a short "
            "whirring sound, then silence. {b} noticed the same little pattern "
            "each time the parcel was nudged."
        ),
        "action": (
            "{a} said, \"I was sure it was thunder. Will you help me open it?\" "
            "{b} answered, \"Of course,\" and they eased the silver paper apart."
        ),
        "reveal": (
            "A small star projector sat inside, with its switch pressed by the "
            "folded paper. Its tiny motor had made the click and whirr."
        ),
        "resolution": (
            "They freed the switch and turned the projector on. Stars drifted "
            "across the ceiling, and {a} saw that the little sound had been "
            "the beginning of something lovely."
        ),
        "ending": (
            "Under the slow-moving stars, the open parcel waited beside the "
            "bed while the children grew sleepy."
        ),
        "method": "They listened for the click-then-whirr pattern and opened the parcel carefully.",
        "outcome": "Folded paper had pressed the star projector's switch and started its tiny motor.",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = f"{params.child_one}|{params.child_two}|{params.place}"
    return random.Random(stable)


def _check_params(params: StoryParams) -> None:
    if not params.child_one.strip() or not params.child_two.strip():
        raise StoryError("Both children's names must be non-empty.")
    if params.child_one == params.child_two:
        raise StoryError("The two children's names must be different.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown Scottish setting: {params.place!r}.")


def python_reasonableness_gate(arc: dict[str, str]) -> bool:
    required = {
        "key", "source", "sound", "premise", "problem", "first_line",
        "second_line", "clue", "action", "reveal", "resolution", "ending",
        "method", "outcome",
    }
    return (
        required.issubset(arc)
        and bool(arc["sound"])
        and "parcel" in arc["premise"].lower()
        and "parcel" in arc["problem"].lower()
        and "together" in (arc["action"] + arc["resolution"]).lower()
        and all(arc[field].strip() for field in required)
    )


def tell(params: StoryParams) -> World:
    _check_params(params)
    rng = _rng_for(params)
    arc_index = rng.randrange(len(ARCS)) if params.seed is None else params.seed % len(ARCS)
    arc = ARCS[arc_index]
    if not python_reasonableness_gate(arc):
        raise StoryError(f"The {arc['key']} parcel story does not pass the reasonableness gate.")

    a, b = params.child_one, params.child_two
    values = {"a": a, "b": b, "place": params.place, "sound": arc["sound"]}
    parcel = Entity(
        id="parcel",
        kind="thing",
        type="parcel",
        label="tartan-wrapped parcel",
        meters={"sealed": 1.0, "sound_volume": 0.25},
        memes={"mystery": 1.0},
    )
    child_a = Entity(
        id=a, kind="character", type="child", label="child",
        meters={"attention": 1.0},
        memes={"worry": 0.2, "confidence": 0.6},
    )
    child_b = Entity(
        id=b, kind="character", type="child", label="child",
        meters={"attention": 1.0},
        memes={"worry": 0.1, "patience": 0.8},
    )

    world = World(params=params)
    world.add(child_a)
    world.add(child_b)
    world.add(parcel)

    world.paragraphs = [
        arc["premise"].format(**values),
        " ".join(
            [
                arc["problem"].format(**values),
                arc["first_line"].format(**values),
                arc["second_line"].format(**values),
            ]
        ),
        arc["clue"].format(**values),
        " ".join([arc["action"].format(**values), arc["reveal"].format(**values)]),
        " ".join([arc["resolution"].format(**values), arc["ending"].format(**values)]),
    ]

    parcel.meters.update({"sealed": 0.0, "opened": 1.0, "sound_volume": 0.0})
    parcel.memes.update({"mystery": 0.0, "understood": 1.0})
    child_a.memes.update({"worry": 0.0, "confidence": 1.0})
    child_b.memes.update({"patience": 1.0, "kindness": 1.0})

    world.facts = {
        "arc": arc,
        "child_one": child_a,
        "child_two": child_b,
        "parcel": parcel,
        "problem_event": arc["problem"].format(**values),
        "clue_event": arc["clue"].format(**values),
        "method": arc["method"],
        "outcome": arc["outcome"],
        "source": arc["source"],
        "sound": arc["sound"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    a = world.params.child_one
    b = world.params.child_two
    return [
        "Write a gentle Scottish bedtime story about a parcel that makes a mysterious sound.",
        f"Tell a cozy story where {a} and {b} misunderstand a sound, disagree, and listen to each other.",
        "Make a child-friendly parcel mystery with soft sound effects and a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = world.params.child_one, world.params.child_two
    return [
        QAItem(
            question=f"Where did {a} and {b} find the parcel?",
            answer=(
                f"{a} and {b} found the tartan-wrapped parcel in their Scottish "
                f"cottage {world.params.place}, ready for bedtime."
            ),
        ),
        QAItem(
            question="What sound made them wonder about the parcel?",
            answer=(
                f"The parcel made a soft {f['sound']} sound. {a} and {b} had "
                f"different guesses about what could be making it."
            ),
        ),
        QAItem(
            question="How did they figure out what was making the sound?",
            answer=f"{f['method']} {f['outcome']}",
        ),
        QAItem(
            question="How did the misunderstanding end?",
            answer=(
                f"{a} and {b} listened, opened the parcel gently, and discovered "
                f"that {f['outcome'][0].lower() + f['outcome'][1:]} They shared "
                "the discovery and felt calm enough to settle down for the night."
            ),
        ),
    ]


def world_knowledge_qa(_world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parcel?",
            answer=(
                "A parcel is something wrapped or packed to be carried or sent "
                "to someone. Opening it carefully can help protect what is inside."
            ),
        ),
        QAItem(
            question="Why can a sound be misunderstood?",
            answer=(
                "A sound can be hard to identify when its source is hidden. "
                "Listening carefully and looking for clues can help explain it."
            ),
        ),
        QAItem(
            question="What is a Scottish loch?",
            answer=(
                "A loch is a Scottish word for a lake or a long arm of the sea. "
                "Many lochs are surrounded by hills, villages, or quiet shores."
            ),
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id} ({entity.type}) meters={meters} memes={memes}")
    arc = world.facts["arc"]
    lines.append(f"  parcel_story={arc['key']}")
    lines.append(f"  parcel_source={world.facts['source']}")
    lines.append(f"  misunderstanding_resolved=True")
    return "\n".join(lines)


ASP_RULES = r"""
parcel_story(S) :- parcel(S), sound_effect(S), misunderstanding(S),
                   conflict(S), bedtime_style(S), resolution(S).
compatible(S) :- parcel_story(S).
#show compatible/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = []
    for arc in ARCS:
        key = arc["key"]
        facts.extend(
            [
                asp.fact("parcel", key),
                asp.fact("sound_effect", key),
                asp.fact("misunderstanding", key),
                asp.fact("conflict", key),
                asp.fact("bedtime_style", key),
                asp.fact("resolution", key),
            ]
        )
    return "\n".join(facts)


def asp_program(show: Optional[str] = None) -> str:
    selected_show = show if show is not None else "#show compatible/1."
    return f"{asp_facts()}\n{ASP_RULES}\n{selected_show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    py_compatible = {
        arc["key"] for arc in ARCS if python_reasonableness_gate(arc)
    }
    symbols = asp.one_model(asp_program())
    asp_compatible = {str(row[0]) for row in asp.atoms(symbols, "compatible")}
    if asp_compatible != py_compatible:
        print(
            "MISMATCH: Python and ASP gates differ "
            f"(Python={sorted(py_compatible)}, ASP={sorted(asp_compatible)})."
        )
        return 1

    for index, arc in enumerate(ARCS):
        sample = generate(
            StoryParams(
                child_one="Eilidh",
                child_two="Hamish",
                place=PLACES[index % len(PLACES)],
                seed=index,
            )
        )
        story = sample.story
        if (
            arc["key"] not in story and sample.world.facts["arc"]["key"] != arc["key"]
        ):
            print(f"MISMATCH: generated story {index} selected the wrong parcel tale.")
            return 1
        if (
            "?" in story
            or "{" in story
            or "}" in story
            or sample.world.entities["parcel"].meters.get("opened") != 1.0
            or len(sample.story_qa) < 4
            or not all(name in story for name in ('"That', '"Maybe', '"The', '"Let'))
        ):
            print(f"MISMATCH: generated story {index} failed its story checks.")
            return 1

    print(
        f"OK: Python and ASP agree on {len(py_compatible)} parcel stories; "
        f"all {len(ARCS)} generated stories pass."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Scottish bedtime parcel story about sounds, misunderstandings, and listening."
    )
    parser.add_argument("--child-one")
    parser.add_argument("--child-two")
    parser.add_argument("--place")
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
    child_one = args.child_one or rng.choice(NAMES)
    available_names = [name for name in NAMES if name != child_one]
    child_two = args.child_two or rng.choice(available_names)
    place = args.place or rng.choice(PLACES)
    params = StoryParams(
        child_one=child_one,
        child_two=child_two,
        place=place,
        seed=args.seed,
    )
    _check_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            compatible = asp.atoms(asp.one_model(asp_program()), "compatible")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        print(
            f"{len(compatible)} compatible Scottish bedtime parcel stories: "
            + ", ".join(str(row[0]) for row in compatible)
        )
        return
    if args.n < 1 and not args.all:
        raise StoryError("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(ARCS)):
            params = StoryParams(
                child_one="Eilidh",
                child_two="Hamish",
                place=PLACES[index % len(PLACES)],
                seed=index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            raise StoryError("Could not produce the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
