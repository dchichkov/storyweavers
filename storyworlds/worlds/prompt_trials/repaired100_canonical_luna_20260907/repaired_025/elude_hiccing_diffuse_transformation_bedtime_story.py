#!/usr/bin/env python3
"""
A tiny bedtime-story world about eluding a hiccing moonbeam, diffusing worry,
and finding a gentle transformation before sleep.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    awake: bool = True
    hiccing: bool = False
    hidden: bool = False


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class BedtimeArc:
    id: str
    opening: str
    trouble: str
    clue: str
    exchange: tuple[str, str]
    action: str
    release: str
    transformation: str
    ending: str


@dataclass
class StoryParams:
    name: str
    companion: str
    blanket: str
    arc: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.sentences: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.sentences[-1].append(text)

    def para(self) -> None:
        if self.sentences[-1]:
            self.sentences.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.sentences if p)


SETTING = Setting(
    place="the little bedroom beneath the listening moon",
    affords={"sleep", "moonlight", "comfort", "transformation"},
)

ARCS = {
    "curtain": BedtimeArc(
        id="curtain",
        opening="The bedroom was quiet except for the soft breathing of the house.",
        trouble="A silver moonbeam slipped through the curtain and began hiccing bright little flashes across the pillow.",
        clue="The flashes followed every hiccup, but they faded whenever the curtain was folded into a wide, calm wave.",
        exchange=(
            '"The moonbeam keeps finding me," whispered Luna.',
            '"Then we will give it a softer place to land," said Moss.',
        ),
        action="folded the curtain into a broad loop so the moonbeam could spread across the wall",
        release="The next hiccup became a pale glow on the wall instead of a jump on the pillow.",
        transformation="Luna changed from hiding inside her worry to shaping it into something gentle.",
        ending="Soon the wall held a quiet silver garden, and Luna fell asleep beneath its soft leaves.",
    ),
    "music_box": BedtimeArc(
        id="music_box",
        opening="Before bedtime, Luna found an old music box resting beside the lamp.",
        trouble="Each time the music box chimed, a moonbeam hicced through its tiny keyhole and made the room tremble.",
        clue="The trembling grew sharp near the closed lid, but it became diffuse when the lid was opened.",
        exchange=(
            '"Must the room keep jumping?" asked Luna.',
            '"We can let the music breathe," answered Pip.',
        ),
        action="lifted the lid and placed a warm cloth beneath the rattling box",
        release="The next hiccup spread through the cloth and faded into one long, sleepy note.",
        transformation="Luna changed from listening for danger to listening for the space between sounds.",
        ending="The music box hummed once, then rested while Luna dreamed of a moonlit boat.",
    ),
    "star_shadow": BedtimeArc(
        id="star_shadow",
        opening="A tiny star-shaped shadow waited at the foot of Luna's bed.",
        trouble="It kept hiccing whenever Luna tried to cross the room, darting away just before her toes touched it.",
        clue="The shadow did not flee from darkness; it fled from sudden movements.",
        exchange=(
            '"I cannot catch the little star," said Luna.',
            '"You do not need to catch it," said Fern. "Walk slowly with it."',
        ),
        action="took three quiet steps and let the shadow stretch beside her",
        release="The last hiccup loosened the shadow, and it diffused into a friendly patch of night.",
        transformation="Luna changed from chasing an answer to making room for one.",
        ending="The star-shaped patch rested beside the bed, guarding Luna until morning.",
    ),
    "window": BedtimeArc(
        id="window",
        opening="Rain whispered against the bedroom window while Luna arranged her pillows.",
        trouble="A moonbeam kept hiccing through the raindrops and scattering nervous sparks over the blankets.",
        clue="The sparks softened wherever the window's little paper stars overlapped.",
        exchange=(
            '"The rain is full of prickles," said Luna.',
            '"Let us join the stars together," said Rowan.',
        ),
        action="moved the paper stars until their points made one wide silver path",
        release="The hiccing beam crossed the path, diffused into the raindrops, and became a calm shimmer.",
        transformation="Luna changed from counting every frightening spark to noticing how small lights could help one another.",
        ending="Rain and moonlight whispered together until Luna's eyes closed.",
    ),
}


NAMES = ["Luna", "Mina", "Nori", "Tessa", "Ollie", "Pip"]
COMPANIONS = ["Moss", "Fern", "Pip", "Rowan", "Toby"]
BLANKETS = ["blue", "amber", "cloud-white", "green", "violet"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime story of eluding hiccing moonlight.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--blanket", choices=BLANKETS)
    parser.add_argument("--arc", choices=sorted(ARCS))
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
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice([x for x in COMPANIONS if x != name])
    return StoryParams(
        name=name,
        companion=companion,
        blanket=args.blanket or rng.choice(BLANKETS),
        arc=args.arc or rng.choice(sorted(ARCS)),
    )


def _diffuse_beam(world: World) -> list[str]:
    beam = world.entities["moonbeam"]
    child = world.entities["child"]
    if not beam.hiccing or not child.hidden:
        return []
    if child.meters.get("calm", 0) < THRESHOLD:
        return []
    if "diffuse" in world.fired:
        return []
    world.fired.add("diffuse")
    beam.hiccing = False
    beam.meters["diffuse"] = 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    return [str(world.facts["arc"].release)]


def _transform(world: World) -> list[str]:
    child = world.entities["child"]
    if child.memes.get("trust", 0) < THRESHOLD:
        return []
    if "transform" in world.fired:
        return []
    world.fired.add("transform")
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    child.meters["sleepiness"] = child.meters.get("sleepiness", 0.0) + 1.0
    return [str(world.facts["arc"].transformation)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_diffuse_beam, _transform):
            sentences = rule(world)
            if sentences:
                changed = True
                for sentence in sentences:
                    world.say(sentence)


def tell(params: StoryParams) -> World:
    arc = ARCS[params.arc]
    world = World(SETTING)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="child",
        label=params.name,
        meters={"calm": 0.0, "sleepiness": 0.0},
        memes={"worry": 1.0, "trust": 0.0, "bravery": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="night_friend",
        label=params.companion,
        meters={"comfort": 1.0},
        memes={"patience": 1.0},
    ))
    beam = world.add(Entity(
        id="moonbeam",
        type="moonbeam",
        label="moonbeam",
        meters={"diffuse": 0.0},
        memes={"restless": 1.0},
        hiccing=True,
    ))
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label=f"{params.blanket} blanket",
        meters={"warmth": 1.0},
    ))
    world.facts.update(child=child, companion=companion, beam=beam, blanket=blanket, arc=arc)

    world.say(f"{params.name} was tucked beneath a {params.blanket} blanket in {world.setting.place}.")
    world.say(arc.opening)
    world.para()
    world.say(arc.trouble)
    world.say(f"{params.name} tried to elude the hiccing light by pulling the blanket over their head, but the flashes still danced nearby.")
    world.para()
    world.say(arc.exchange[0])
    world.say(arc.clue)
    world.say(arc.exchange[1])
    world.say(f"{params.companion} stayed close while {params.name} {arc.action}.")
    child.hidden = True
    child.meters["calm"] = 1.0
    child.memes["worry"] = 0.0
    world.say(f"That careful plan helped {params.name} elude the sharp flashes without running away from the moon.")
    propagate(world)
    world.para()
    world.say(arc.ending)
    child.awake = False
    return world


def generate(params: StoryParams) -> StorySample:
    if params.arc not in ARCS:
        raise StoryError("The bedtime arc must be one of the registered gentle moonlight arcs.")
    if params.name == params.companion:
        raise StoryError("The sleeper and the companion need different names.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"] if "params" in world.facts else StoryParams(
        name=world.entities["child"].label,
        companion=world.entities["companion"].label,
        blanket=world.entities["blanket"].label.split()[0],
        arc=world.facts["arc"].id,
    )
    arc: BedtimeArc = world.facts["arc"]
    return [
        f"Write a Bedtime Story about {params.name} and {params.companion} in which a hiccing moonbeam is eluded.",
        f"Tell a gentle Transformation story using the clue: {arc.clue}",
        f"Write a sleepy story that includes the words elude, hiccing, and diffuse, and ends with this image: {arc.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts.get("params")
    arc: BedtimeArc = world.facts["arc"]
    name = world.entities["child"].label
    companion = world.entities["companion"].label
    blanket = world.entities["blanket"].label
    return [
        QAItem(
            question=f"What trouble woke {name}?",
            answer=arc.trouble,
        ),
        QAItem(
            question=f"How did {name} elude the hiccing moonbeam?",
            answer=f"{name} {arc.action}, which helped the moonbeam become gentle.",
        ),
        QAItem(
            question=f"What clue helped {name} and {companion}?",
            answer=arc.clue,
        ),
        QAItem(
            question=f"What did the moonbeam do after the plan worked?",
            answer=arc.release,
        ),
        QAItem(
            question=f"How did the experience transform {name}?",
            answer=arc.transformation,
        ),
        QAItem(
            question=f"What proved that {name} was ready for sleep?",
            answer=arc.ending,
        ),
        QAItem(
            question="Which blanket was part of the bedtime setting?",
            answer=f"{name} rested beneath the {blanket}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does elude mean?",
            answer="To elude means to get away from something or avoid being caught by it.",
        ),
        QAItem(
            question="What does hiccing mean in this story?",
            answer="Hiccing means making small, sudden jumps or flashes, like the moonbeam's repeated little hiccups.",
        ),
        QAItem(
            question="What does diffuse mean?",
            answer="To diffuse means to spread something out so it becomes softer and less concentrated.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a meaningful change, such as worry becoming trust or fear becoming calm.",
        ),
        QAItem(
            question="Why can a bedtime story feel comforting?",
            answer="A bedtime story can feel comforting because a gentle problem is met with care and ends in safety and rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        if entity.hiccing:
            state.append("hiccing=True")
        if entity.hidden:
            state.append("hidden=True")
        if not entity.awake:
            state.append("awake=False")
        lines.append(f"  {entity.id:10} ({entity.type:12}) {' '.join(state)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
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


ASP_RULES = r"""
valid_story(N, C, A) :-
    name(N),
    companion(C),
    arc(A),
    different(N, C),
    bedtime_arc(A).

different(N, C) :- N != C.
bedtime_arc(curtain).
bedtime_arc(music_box).
bedtime_arc(star_shadow).
bedtime_arc(window).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for companion in COMPANIONS:
        lines.append(asp.fact("companion", companion))
    for arc in ARCS:
        lines.append(asp.fact("arc", arc))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {
        (name, companion, arc)
        for name in NAMES
        for companion in COMPANIONS
        for arc in ARCS
        if name != companion
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combinations).")
        for seed in range(8):
            params = StoryParams(
                name=NAMES[seed % len(NAMES)],
                companion=COMPANIONS[(seed + 1) % len(COMPANIONS)],
                blanket=BLANKETS[seed % len(BLANKETS)],
                arc=sorted(ARCS)[seed % len(ARCS)],
                seed=seed,
            )
            sample = generate(params)
            required = ("elude", "hiccing", "diffuse")
            if not all(word in sample.story.lower() for word in required):
                print("Generated story omitted a required seed word.")
                return 1
            if not sample.story_qa:
                print("Generated story omitted grounded questions.")
                return 1
        print("OK: generated bedtime stories passed narrative checks.")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    seen = set()
    index = 0
    while len(samples) < args.n and index < max(50, args.n * 50):
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


CURATED = [
    StoryParams("Luna", "Moss", "blue", "curtain", 0),
    StoryParams("Mina", "Fern", "cloud-white", "music_box", 1),
    StoryParams("Nori", "Rowan", "violet", "star_shadow", 2),
    StoryParams("Tessa", "Pip", "green", "window", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        combinations = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combinations)} valid bedtime-story combinations.")
        for combination in combinations[:20]:
            print(combination)
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = build_story_from_args(args)

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
            header=f"### bedtime variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
