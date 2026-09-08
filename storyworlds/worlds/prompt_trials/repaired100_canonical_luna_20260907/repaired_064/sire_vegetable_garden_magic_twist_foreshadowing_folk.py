#!/usr/bin/env python3
"""A folk tale about a sire, a vegetable garden, and a magic twist."""

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    mood: str


@dataclass
class StoryParams:
    plot: str
    helper: str
    crop: str
    charm: str
    name: str = "Luna"
    sire: str = "Sire Rowan"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    missing: str
    warning: str
    magic: str
    twist: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SCENES = {
    "garden": Scene("the vegetable garden", "a warm wind", "quiet as a held breath"),
}
HELPERS = {
    "badger": "a patient badger",
    "wren": "a bright wren",
    "goat": "a gentle goat",
    "mole": "a small brown mole",
}
CROPS = {
    "pumpkins": "golden pumpkins",
    "beans": "blue beans",
    "carrots": "sweet carrots",
    "cabbages": "round cabbages",
}
CHARMS = {
    "acorn": "an acorn carved with a spiral",
    "bell": "a tiny silver bell",
    "stone": "a green stone warm as bread",
    "ribbon": "a red ribbon tied in three knots",
}
TALES = {
    "thirsty_rows": Tale(
        "the garden's first water",
        "the dry leaves curled whenever noon arrived",
        "the charm made dew gather in a shining ring around the roots",
        "the magic was not in the charm alone: Sire Rowan had hidden a cracked clay channel beneath the soil",
        "repaired the channel and shared the first full watering with every row",
        "old magic often waits for careful hands to finish its work",
        "the vegetables stood bright while little streams glittered between the beds",
    ),
    "singing_seeds": Tale(
        "the seeds saved for the village supper",
        "the seed basket whispered whenever anyone carried it",
        "the charm made the buried seeds hum a tune beneath the beds",
        "the whispering basket was not warning of thieves; it was pointing to seeds planted in the wrong rows",
        "dug gently, sorted the seeds, and planted them by the moon's markings",
        "a strange sign may be guidance rather than danger",
        "the new rows hummed softly until green shoots rose like a song",
    ),
    "vanishing_vines": Tale(
        "the climbing vines meant to shade the oven",
        "each vine ended in a neat curl beside the old well",
        "the charm caused the vines to glow wherever their roots needed room",
        "the vines had not vanished at all; they had grown beneath a loose wooden cover and curled toward hidden water",
        "lifted the cover, loosened the soil, and built a safe trellis",
        "what disappears may be traveling toward what it needs",
        "green vines climbed the trellis and cast a cool leaf-shadow over the oven",
    ),
    "moon_cucumbers": Tale(
        "the moon cucumbers promised to the queen",
        "their silver blossoms opened only when someone told an untrue boast",
        "the charm made every false boast fall as a blue petal",
        "the flowers were testing the gardener, not the crop: Sire Rowan had forgotten his own boast about never needing help",
        "admitted the truth and invited the neighbors to tend the beds together",
        "humility lets hidden plenty come into the light",
        "silver cucumbers filled the baskets after everyone had worked side by side",
    ),
}
PLOTS = tuple(sorted(TALES))
ASP_RULES = """
valid(Plot,Helper,Crop,Charm) :-
    plot(Plot), helper(Helper), crop(Crop), charm(Charm).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A folk tale of magic in a vegetable garden.")
    parser.add_argument("--plot", choices=PLOTS)
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--crop", choices=sorted(CROPS))
    parser.add_argument("--charm", choices=sorted(CHARMS))
    parser.add_argument("--name", default="Luna")
    parser.add_argument("--sire", default="Sire Rowan")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (plot, helper, crop, charm)
        for plot in PLOTS
        for helper in sorted(HELPERS)
        for crop in sorted(CROPS)
        for charm in sorted(CHARMS)
    ]


def asp_facts() -> str:
    import asp
    return "\n".join([
        *(asp.fact("plot", value) for value in PLOTS),
        *(asp.fact("helper", value) for value in HELPERS),
        *(asp.fact("crop", value) for value in CROPS),
        *(asp.fact("charm", value) for value in CHARMS),
    ])


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("MISMATCH:", sorted(expected - actual), sorted(actual - expected))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(expected)} combinations).")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo for combo in valid_combos()
        if not args.plot or combo[0] == args.plot
        if not args.helper or combo[1] == args.helper
        if not args.crop or combo[2] == args.crop
        if not args.charm or combo[3] == args.charm
    ]
    if not choices:
        raise StoryError("No valid vegetable-garden tale fits those options.")
    plot, helper, crop, charm = rng.choice(choices)
    return StoryParams(
        plot=plot,
        helper=helper,
        crop=crop,
        charm=charm,
        name=args.name,
        sire=args.sire,
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.plot, params.helper, params.crop, params.charm,
        params.name, params.sire,
    ))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = SCENES["garden"]
    tale = TALES[params.plot]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        memes={"curiosity": 1.0, "courage": 0.0},
    ))
    sire = world.add(Entity(
        id=params.sire,
        kind="character",
        type="sire",
        memes={"pride": 1.0, "wisdom": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="helper",
        type=params.helper,
        memes={"trust": 0.0},
    ))
    charm = world.add(Entity(
        id=params.charm,
        kind="magic",
        type="charm",
        label=CHARMS[params.charm],
        meters={"warmth": 1.0},
    ))

    crop = CROPS[params.crop]
    world.say(
        f"In the days when {scene.place} was guarded by a crooked gate, "
        f"{hero.id} tended {crop} with {sire.id}, her old sire and teacher."
    )
    world.say(
        f"At dawn, {scene.weather} moved through the beds, and {tale.missing} "
        f"was waiting beneath {CHARMS[params.charm]}."
    )
    world.say(
        f"{tale.warning.capitalize()}. Even the {HELPERS[params.helper]} paused at the gate."
    )
    world.para()

    world.say(
        f'"Do not touch it," {sire.id} warned. "A garden may hide a blessing, but it may also hide a lesson."'
    )
    world.say(
        f'"Then let us learn carefully," {hero.id} replied. '
        f'"Will you watch with me, {HELPERS[params.helper]}?"'
    )
    world.say(
        f"The {HELPERS[params.helper]} nodded, and its small movement changed {hero.id}'s mind: "
        "she would test the wonder before trusting it."
    )
    world.add(Entity(id="test", kind="action", type="careful_test", meters={"steps": 1.0}))
    world.para()

    world.say(
        f"{hero.id} placed one dry leaf beside the charm and waited. "
        f"At once, {tale.magic}."
    )
    world.say(
        f"{sire.id} frowned, for the magic seemed to promise an easy harvest. "
        f'"If the charm can do everything," he said, "perhaps we need do nothing."'
    )
    world.say(
        f'"That cannot be the whole truth," {hero.id} answered. '
        f'"The leaves still thirst, and the soil still needs our hands."'
    )
    world.say(
        f"She followed the faint sign left by the magic, while the {HELPERS[params.helper]} "
        "scratched at a place everyone had overlooked."
    )
    world.para()

    world.say(f"Then came the twist: {tale.twist}.")
    world.say(
        f"The charm flashed once and went quiet. {hero.id} understood that its wonder "
        "was a lantern, not a pair of hands."
    )
    world.say(
        f"{sire.id} lowered his head. 'I called myself the wisest gardener,' he said, "
        "'but I forgot to listen to the garden.'"
    )
    world.say(
        f'"A wise sire can change his plan," {hero.id} said. '
        f'"Help me, and we can mend what the magic revealed."'
    )
    world.para()

    world.say(f"Together, they {tale.repair}.")
    hero.memes["courage"] = 1.0
    sire.memes["pride"] = 0.0
    sire.memes["wisdom"] = 1.0
    helper.memes["trust"] = 1.0
    hero.meters["careful_actions"] = 3.0
    world.say(
        f"The {HELPERS[params.helper]} worked beside them, and the garden answered with "
        "a soft rustle through every leaf."
    )
    world.say(f"{hero.id} remembered the foreshadowing: {tale.warning}.")
    world.say(f"{sire.id} repeated the lesson aloud: {tale.lesson}.")
    world.say(
        f"By evening, {tale.ending}. The charm rested in the earth, "
        "quiet and warm, waiting for another careful gardener."
    )

    world.facts.update(
        hero=hero,
        sire=sire,
        helper=helper,
        charm=charm,
        crop=crop,
        tale=tale,
        warning=tale.warning,
        magic=tale.magic,
        twist=tale.twist,
        repair=tale.repair,
        lesson=tale.lesson,
        ending=tale.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    tale: Tale = facts["tale"]  # type: ignore[assignment]
    return [
        f"Tell a gentle folk tale about {facts['hero'].id}, their sire {facts['sire'].id}, and magic in a vegetable garden.",
        f"Write a child-facing story in which {facts['charm'].label} foreshadows that {tale.warning}.",
        f"Build to the twist that {tale.twist}, then end with {tale.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    tale: Tale = facts["tale"]  # type: ignore[assignment]
    hero: Entity = facts["hero"]  # type: ignore[assignment]
    sire: Entity = facts["sire"]  # type: ignore[assignment]
    helper: Entity = facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} and {sire.id} tend in the vegetable garden?",
            answer=f"They tended {facts['crop']} together in the vegetable garden.",
        ),
        QAItem(
            question=f"What warning foreshadowed the trouble with {facts['charm'].label}?",
            answer=f"The warning was that {tale.warning}. It showed that the garden needed careful attention.",
        ),
        QAItem(
            question=f"How did the {helper.type} help {hero.id} understand the magic?",
            answer=f"The {helper.type} helped by noticing a place everyone had overlooked, so {hero.id} tested the magic instead of trusting it blindly.",
        ),
        QAItem(
            question=f"What was the twist in the tale?",
            answer=f"The twist was that {tale.twist}. The charm revealed a problem but could not solve it by itself.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sire.id} repair the garden?",
            answer=f"They {tale.repair}. This taught them that {tale.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a folk tale?",
            answer="Foreshadowing is an early sign that quietly prepares the reader for something important later.",
        ),
        QAItem(
            question="Why should a gardener test a magical promise carefully?",
            answer="A magical sign may reveal a problem without fixing it. Careful testing helps the gardener choose a safe and useful action.",
        ),
        QAItem(
            question="What makes a twist satisfying?",
            answer="A satisfying twist changes what the characters thought while fitting clues that appeared earlier in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.extend((
        f"  warning={world.facts['warning']}",
        f"  twist={world.facts['twist']}",
        f"  repair={world.facts['repair']}",
    ))
    return "\n".join(lines)


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
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        plot="thirsty_rows",
        helper="badger",
        crop="pumpkins",
        charm="stone",
        seed=101,
    ),
    StoryParams(
        plot="singing_seeds",
        helper="wren",
        crop="beans",
        charm="bell",
        seed=202,
    ),
    StoryParams(
        plot="moon_cucumbers",
        helper="goat",
        crop="cucumbers" if "cucumbers" in CROPS else "cabbages",
        charm="ribbon",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible combinations:\n")
        for plot, helper, crop, charm in combinations:
            print(f"  {plot:16} {helper:8} {crop:10} {charm}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=(
                "### curated story"
                if args.all
                else (f"### variant {index + 1}" if len(samples) > 1 else "")
            ),
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
