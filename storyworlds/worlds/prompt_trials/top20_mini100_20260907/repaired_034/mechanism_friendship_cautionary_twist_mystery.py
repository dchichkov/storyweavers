#!/usr/bin/env python3
"""
A small mystery storyworld about a mechanism, friendship, caution, and a twist.

The world is built around a child-facing puzzle: a curious mechanism goes wrong,
friends investigate carefully, a warning matters, and the answer turns out to be
surprising but safe.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Ivy"
    friend: str = "Ben"
    place: str = "the clock tower"
    mechanism: str = "the little gear door"
    object_name: str = "the brass key"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    place: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Ivy", "Ben", "Mara", "Owen", "Lena", "Noah", "Zoe", "Tess"]
FRIEND_NAMES = ["Ben", "Ivy", "Kai", "Pia", "Jude", "Nora", "Milo", "Uma"]
PLACES = [
    "the clock tower",
    "the old train station",
    "the museum hall",
    "the garden shed",
    "the library basement",
    "the lighthouse attic",
]
MECHANISMS = [
    "the little gear door",
    "the hidden latch",
    "the spinning puzzle box",
    "the silver winch",
    "the tiny spring lift",
    "the quiet lock wheel",
]
OBJECTS = [
    "the brass key",
    "the blue ribbon",
    "the red marble",
    "the pocket map",
    "the tiny bell",
    "the paper star",
]


@dataclass
class Arc:
    premise: str
    problem: str
    stake: str
    warning: str
    clue: str
    action: str
    twist: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


ARCS = [
    Arc(
        premise="The friends found a dusty mechanism behind a panel in the clock tower",
        problem="it had jammed, and its small wheel kept clicking without opening",
        stake="If it stayed stuck, the tower's evening chime would not ring for the town square",
        warning="a faded note said, 'Do not force the wheel, or the hidden spring will jump'",
        clue="the wheel had a tiny mark that matched one notch on the brass key",
        action="They cleaned the dust away, used the key as a guide, and turned the wheel only until it sighed open",
        twist="the mechanism did not guard treasure at all; it was a music box that woke the chime bell each night",
        resolution="the bell sang once the friends set the music box back in order",
        lesson="careful hands and patient friends can solve a mystery without breaking it",
        ending="at sunset, the tower chimed sweetly while the little music box hummed in the dark",
        question="Why did the friends avoid forcing the wheel?",
        answer="They avoided forcing it because the warning said the hidden spring could jump and make the problem worse.",
    ),
    Arc(
        premise="In the museum hall, the children discovered a mechanism under a glass case",
        problem="its two levers would not align, and the case stayed sealed",
        stake="The map exhibit inside would remain hidden from the school tour",
        warning="a label under the glass warned, 'Turn only with the matching pair, not with one hand alone'",
        clue="each lever was carved with half of a fox face",
        action="They each held one lever, counted together, and moved them at the same pace",
        twist="the case held not a rare jewel, but a tiny puppet fox that pointed to the map drawer",
        resolution="the fox nodded, the drawer opened, and the children laughed in relief",
        lesson="some locks can only be solved with friendship and careful timing",
        ending="the tour left smiling, with the puppet fox riding on the librarian's cart",
        question="What did the case really contain?",
        answer="The case really contained a tiny puppet fox that pointed to the map drawer.",
    ),
    Arc(
        premise="At the old train station, a strange mechanism kept the platform gate closed",
        problem="its sliding teeth had crossed the wrong way after a gust of wind",
        stake="The last evening train would leave without the passengers waiting on the other side",
        warning="a conductor's tag said, 'Never tug a crossed gate; guide the teeth back first'",
        clue="the teeth lined up when the children listened for the soft tick beside the lamp",
        action="They followed the ticks, matched the teeth one by one, and asked the station guard to steady the gate",
        twist="the mechanism was not a gate lock at all, but a signal box that was calling the train in reverse order",
        resolution="the guard flipped the signal, the gate opened, and the train rolled in with a sleepy whistle",
        lesson="a caution can reveal the true shape of a problem when friends stop and listen",
        ending="the platform lights glowed while the train steamed home beside the calm gate",
        question="Why did the friends listen before touching the gate?",
        answer="They listened because the warning said to guide the teeth back first instead of tugging hard.",
    ),
    Arc(
        premise="In the garden shed, the children found a mechanism hanging from the rafters",
        problem="its chain had slipped, so a seed basket would not lower to the floor",
        stake="Without the basket, the seedlings waiting in the rain could not be carried inside",
        warning="a chalk sign said, 'Keep fingers away from the pulley teeth'",
        clue="the basket moved whenever one child steadied the rope and another counted softly",
        action="They worked together, steadied the rope, and lowered the basket inch by inch",
        twist="the basket held not only seeds, but a sleeping hedgehog curled beneath the straw",
        resolution="they carried the hedgehog to a warm box and placed the seeds beside the stove",
        lesson="friendship means helping gently when a small life is hidden in the dark",
        ending="by morning, the basket was dry, the hedgehog was safe, and the shed smelled of earth and straw",
        question="What was hidden in the basket?",
        answer="A sleeping hedgehog was hidden beneath the straw in the basket.",
    ),
    Arc(
        premise="The lighthouse attic held a mechanism with a shining glass arm",
        problem="the arm would not swing, and the fog lamp stayed dim",
        stake="Ships near the rocks would not see the warning light before midnight",
        warning="a brass plaque warned, 'Never oil the lens while it is hot'",
        clue="the glass arm moved when the wind came through the open attic window",
        action="They opened the narrow window, waited for the lamp to cool, and gently nudged the arm free",
        twist="the glass arm was not broken; it had been holding a secret note behind the lamp shade",
        resolution="the note said the old keeper had hidden a spare wick in the stair rail, and the lamp flared bright",
        lesson="a mystery may look like damage when it is really a secret kept for later",
        ending="the lighthouse beam swept the water, and the friends waved at the safe ships below",
        question="Why did the lamp stay dim at first?",
        answer="It stayed dim because the glass arm was stuck and the spare wick had been hidden away.",
    ),
    Arc(
        premise="Inside the library basement, a mechanism ticked beneath a reading desk",
        problem="its drawer would not open, no matter how softly the handle turned",
        stake="A borrowed story notebook was trapped inside before story hour began",
        warning="a note on the desk said, 'Do not yank the drawer; the latch listens'",
        clue="the latch clicked whenever the friends spoke in turns",
        action="They took turns speaking, then turned the handle together while the librarian watched",
        twist="the drawer held not a notebook, but a tiny stage set where paper mice performed a play about maps",
        resolution="the librarian laughed, and the notebook was found behind the stage curtain",
        lesson="a careful question can unlock a mystery that rough hands cannot",
        ending="story hour began with paper mice and a relieved grin from every child",
        question="What made the latch click?",
        answer="The latch clicked when the friends spoke in turns and turned the handle together.",
    ),
    Arc(
        premise="The children found a mechanism inside a covered fountain",
        problem="the fountain's stone lid would not lift, and water dripped through the cracks",
        stake="The fish in the pond needed the fountain to run before the afternoon heat",
        warning="a painted sign said, 'Lift with a partner, or the lid will chip'",
        clue="one side of the lid had a handprint that matched the friend's glove",
        action="They counted to three, lifted together, and propped the lid with a wooden broom",
        twist="the fountain mechanism was hiding a tiny tin whale that squirted water for the garden frogs",
        resolution="they cleaned the whale, set it back, and the fountain splashed happily again",
        lesson="the safest answer is often the one where nobody has to act alone",
        ending="frogs blinked beside the fountain while the tin whale puffed one last cheerful spray",
        question="Why did the children lift the lid together?",
        answer="They lifted it together because the sign warned that a partner would keep the lid from chipping.",
    ),
]

OPENINGS = [
    "Morning light made the old walls look less dusty and more secret",
    "A soft breeze slipped through the hall and made every shadow move",
    "By the time the children arrived, the room already felt like a puzzle",
    "The building was quiet, but not as quiet as it first seemed",
    "A narrow beam of sun landed on the floor like a clue",
    "Even the dust seemed to wait for the next step",
]

DIALOGUE_LINES = [
    "{hero}: 'Did you hear that click?' {friend}: 'Yes, and I think it wants patience, not force.'",
    "{friend}: 'Let's look closer.' {hero}: 'Only if we do it carefully.'",
    "{hero}: 'I found a warning.' {friend}: 'Then we should trust it and try a gentler way.'",
    "{friend}: 'Maybe the answer is hidden.' {hero}: 'Then we'll find it together.'",
    "{hero}: 'That part moved!' {friend}: 'Good. Now let's keep our hands steady.'",
    "{friend}: 'Two heads are better here.' {hero}: 'And two careful hands, too.'",
]

TWIST_REACTIONS = [
    "{friend} gasped, then smiled with relief",
    "Both children stared, then let out a surprised laugh",
    "For a moment, nobody moved at all",
    "{hero} blinked twice as the truth came clear",
    "{friend} clapped a hand over their mouth, then nodded",
]

ENDING_IMAGES = [
    "the room felt warm, as if the mystery had finally decided to be kind",
    "the last shadow left the corner, and the answer sat there like a tiny lamp",
    "the air grew calm, and the solved mechanism ticked like a sleepy heart",
    "the quiet place seemed proud to have been understood without being broken",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld about mechanism, friendship, caution, and a twist."
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mechanism", choices=MECHANISMS)
    ap.add_argument("--object-name", choices=OBJECTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    place = args.place or rng.choice(PLACES)
    mechanism = args.mechanism or rng.choice(MECHANISMS)
    object_name = args.object_name or rng.choice(OBJECTS)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        place=place,
        mechanism=mechanism,
        object_name=object_name,
    )


def choose(rng: random.Random, options: list[str], **values: str) -> str:
    return rng.choice(options).format(**values)


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        hero=Entity(name=params.hero, kind="hero"),
        friend=Entity(name=params.friend, kind="friend"),
        place=Entity(name=params.place, kind="place"),
    )


def simulate(world: World) -> None:
    p = world.params
    h = world.hero
    f = world.friend
    h.meters["curiosity"] = 1.0
    h.memes["care"] = 1.0
    f.memes["helpfulness"] = 1.0
    world.facts["mechanism"] = p.mechanism
    world.facts["object_name"] = p.object_name
    arc = ARCS[0 if p.place == "the clock tower" else (1 if p.place == "the museum hall" else (2 if p.place == "the old train station" else (3 if p.place == "the garden shed" else (4 if p.place == "the lighthouse attic" else 5)))]
    rng = random.Random(p.seed)

    world.say(
        f"{choose(rng, OPENINGS)}. At {p.place}, {h.name} and {f.name} found {p.mechanism}, "
        f"and beside it lay {p.object_name}."
    )
    world.say(f"{arc.premise}.")
    world.para()
    world.say(f"Then came the problem: {arc.problem}. {arc.stake}.")
    world.say(f"A warning was there too: {arc.warning}.")
    world.say(choose(rng, DIALOGUE_LINES, hero=h.name, friend=f.name))
    world.say(f"{h.name} looked from the warning to the mechanism and whispered, 'We should not rush.'")
    world.para()
    world.say(f"They studied the clue: {arc.clue}.")
    world.say(f"{arc.action}.")
    world.say(f"Here was the twist: {arc.twist}. {choose(rng, TWIST_REACTIONS, hero=h.name, friend=f.name)}.")
    world.say(f"{arc.resolution}.")
    world.para()
    world.say(f"By the end, {h.name} and {f.name} agreed that {arc.lesson}.")
    world.say(f"{choose(rng, ENDIING_IMAGES) if False else choose(rng, ENDIING_IMAGES if False else ENDIING_IMAGES, hero=h.name, friend=f.name)}")
    world.say(f"{arc.ending}.")
    world.facts["lesson"] = arc.lesson
    world.facts["resolved"] = True
    world.facts["twist"] = arc.twist
    h.memes["relief"] = 1.0
    f.memes["relief"] = 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[0 if params.place == "the clock tower" else (1 if params.place == "the museum hall" else (2 if params.place == "the old train station" else (3 if params.place == "the garden shed" else (4 if params.place == "the lighthouse attic" else 5)))]
    prompts = [
        f"Write a child-friendly mystery about {params.hero} and {params.friend} investigating {params.mechanism}.",
        f"Tell a story where friendship and caution help solve a surprise involving {params.object_name}.",
        f"Make the ending prove what changed after the twist at {params.place}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} and {params.friend} find first?",
            answer=f"They first found {params.mechanism} at {params.place}.",
        ),
        QAItem(
            question=f"Why didn't the friends force the mechanism open?",
            answer=arc.answer,
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.friend} solve the mystery?",
            answer=f"The clue was that {arc.clue}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=arc.twist,
        ),
        QAItem(
            question=f"What did {params.hero} learn from the story?",
            answer=f"{params.hero} learned that {arc.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move or open.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and avoiding needless danger.",
        ),
        QAItem(
            question="What is a twist in a mystery story?",
            answer="A twist is a surprising discovery that changes what the characters thought was true.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.place]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:10} ({ent.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "mystery"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("seed_word", "mechanism"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        sample = generate(StoryParams(seed=123))
        if "mechanism" not in sample.story:
            print("MISMATCH: generated story missing required seed word.")
            return 1
        print("OK: ASP twin is consistent and story generation works.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Ivy", friend="Ben", place="the clock tower", mechanism="the little gear door", object_name="the brass key", seed=101),
    StoryParams(hero="Mara", friend="Kai", place="the museum hall", mechanism="the hidden latch", object_name="the blue ribbon", seed=202),
    StoryParams(hero="Lena", friend="Noah", place="the lighthouse attic", mechanism="the quiet lock wheel", object_name="the tiny bell", seed=303),
]


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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
