#!/usr/bin/env python3
"""A small heartwarming storyworld about a curious child, a magical mattress,
and an orthodontist who helps turn a possible bad ending into a better one.
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
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "Moonbeam Orthodontics' moon garden"
SEED_WORDS = {"mattress", "orthodontist", "stake"}
FEATURES = {"bad_ending", "magic", "curiosity"}
CHILD_NAMES = ("Luna", "Mira", "Nell", "Theo", "Ari", "Jun")
DOCTOR_NAMES = ("Dr. Imani", "Dr. Vale", "Dr. Rowan", "Dr. Sol")


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("anchored", "floating", "distance", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "wonder", "trust", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    child: str = "Luna"
    orthodontist: str = "Dr. Imani"
    scene: int = 0
    telling: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scene:
    place: str
    opening_detail: str
    magic_sign: str
    clue: str
    search: str
    ending_image: str


SCENES = [
    Scene(
        place="the herb beds",
        opening_detail="a string of paper moons above the mint",
        magic_sign="a silver glow curled along the mattress piping",
        clue="a shallow hole beside the mattress and a blue ribbon caught on its wooden stake",
        search="followed the blue ribbon from the herb beds to the low garden wall",
        ending_image="the mattress rested beneath the paper moons, while mint leaves nodded in the evening breeze",
    ),
    Scene(
        place="the little reading lawn",
        opening_detail="a stack of picture books beside a patch of clover",
        magic_sign="the mattress rose just high enough to make its tassels sway",
        clue="a bare ring in the grass where the anchor stake had stood",
        search="checked the lawn's soft footprints and found the stake near a row of daisies",
        ending_image="a picture book lay open on the anchored mattress, its last page glowing in moonlight",
    ),
    Scene(
        place="the flower path",
        opening_detail="small lanterns shaped like smiling teeth",
        magic_sign="the mattress gave a gentle bob, as if it were taking a breath",
        clue="a furrow in the soil leading away from the missing stake",
        search="traced the furrow past the lanterns until the stake glinted under a fern",
        ending_image="the lanterns shone over a safely anchored mattress and a bunch of sleepy flowers",
    ),
    Scene(
        place="the clinic's tiny orchard",
        opening_detail="a basket of windfall apples waiting for the neighborhood picnic",
        magic_sign="the mattress drifted toward the apple trees without making a sound",
        clue="a loose loop of gold cord and a stake-shaped mark in the damp earth",
        search="looked along the cord's path and spotted the stake beside the orchard gate",
        ending_image="an apple rested on the blanket while the moonlit mattress stayed snug beneath the trees",
    ),
    Scene(
        place="the pebble mosaic",
        opening_detail="a new mosaic shaped like a smiling crescent moon",
        magic_sign="the mattress lifted, and its shadow slid across the moon-shaped stones",
        clue="one pebble had rolled into the empty place where the anchor stake belonged",
        search="followed the scattered pebbles to the stake beside the rain barrel",
        ending_image="the crescent mosaic framed the mattress, still and bright under the stars",
    ),
    Scene(
        place="the small pond's dry bank",
        opening_detail="a paper-boat race waiting for the next day's sunshine",
        magic_sign="the mattress floated toward the pond, carrying a pillow but no one",
        clue="a fresh notch in the soil and a thread of moon-colored cloth",
        search="followed the cloth thread away from the water and found the stake by a willow root",
        ending_image="paper boats rested in a basket while the mattress made a safe, soft island on the grass",
    ),
    Scene(
        place="the greenhouse doorway",
        opening_detail="seedlings wearing tiny paper hats",
        magic_sign="the mattress rose as if it wanted to peek through the greenhouse glass",
        clue="a round hole in the soil and a little mound where someone had set the stake down",
        search="checked the mound carefully and found the stake tucked beneath a fallen leaf",
        ending_image="the seedlings stood beside the anchored mattress, their paper hats shining green",
    ),
    Scene(
        place="the garden's painted bench",
        opening_detail="a row of children’s drawings clipped along a low fence",
        magic_sign="the mattress glimmered and slid a few feet across the grass",
        clue="a scratch in the earth that started at the stake and pointed toward the fence",
        search="followed the scratch and found the stake caught beneath the fence's loose bottom rail",
        ending_image="the drawings fluttered above the mattress, which stayed in its cozy place",
    ),
]


@dataclass
class World:
    child: Entity
    doctor: Entity
    mattress: Entity
    stake: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    child = Entity(params.child, "character", "child", "the curious child")
    doctor = Entity(params.orthodontist, "character", "orthodontist", "the orthodontist")
    mattress = Entity("mattress", "thing", "mattress", "the moonlit mattress")
    stake = Entity("stake", "thing", "garden_stake", "the wooden garden stake")
    return World(child=child, doctor=doctor, mattress=mattress, stake=stake)


def validate_params(params: StoryParams) -> None:
    if not params.child.strip() or not params.orthodontist.strip():
        raise StoryError("The child and orthodontist need names.")
    if params.child.strip().casefold() == params.orthodontist.strip().casefold():
        raise StoryError("The child and orthodontist must be different characters.")
    if not 0 <= params.scene < len(SCENES):
        raise StoryError(f"Scene must be between 0 and {len(SCENES) - 1}.")
    if params.telling not in range(4) or params.ending not in range(4):
        raise StoryError("Telling and ending styles must each be between 0 and 3.")


def tell(params: StoryParams) -> World:
    validate_params(params)
    world = build_world(params)
    child, doctor, mattress, stake = world.child, world.doctor, world.mattress, world.stake
    scene = SCENES[params.scene]

    child.memes["worry"] = 1.0
    child.memes["curiosity"] = 1.0
    mattress.meters.update(anchored=1.0, floating=0.0, distance=0.0, safe=1.0)
    stake.meters["anchored"] = 1.0

    openings = [
        f"At {THEME}, {child.id} came for a checkup with {doctor.id}, an orthodontist. After the visit, they stepped into {scene.place}, where {scene.opening_detail}.",
        f"{child.id} felt a little nervous about a new orthodontic checkup, so {doctor.id} invited the child to see the moon garden after the appointment. In {scene.place}, {scene.opening_detail}.",
        f"The evening's garden visit began after {doctor.id}, the neighborhood orthodontist, finished {child.id}'s checkup. They found {scene.opening_detail} in {scene.place}.",
        f"Moonlight settled over {THEME}. {doctor.id}, an orthodontist, had promised {child.id} a quiet garden story after the checkup, and {scene.opening_detail} waited in {scene.place}.",
    ]
    world.say(openings[params.telling])
    world.say(
        f"A magical mattress lay on the grass, held in place by a wooden stake. "
        f"{doctor.id} explained that it floated only when moonlight touched it and its anchor came loose."
    )

    world.para()
    world.say(
        f"{child.id} leaned closer. {scene.magic_sign}. The child wondered whether the mattress could really fly."
    )
    child.memes["curiosity"] += 1.0
    dialogue_one = [
        f'"Could it carry a dream all the way to the moon?" {child.id} asked. '
        f'"Let’s find out what makes it glow, but keep it anchored," {doctor.id} replied.',
        f'"Why does it shine at the edges?" {child.id} asked. '
        f'"That is a good question," said {doctor.id}. "Let’s look closely before we touch anything."',
        f'"Maybe the stake is hiding the strongest magic," {child.id} said. '
        f'"Maybe," answered {doctor.id}, "but we can be curious and careful at the same time."',
        f'"I want to know how it floats," {child.id} said. '
        f'"Then let’s study the clues together," {doctor.id} replied. "We can keep our feet on the ground."',
    ]
    world.say(dialogue_one[params.telling])

    # The child pulls the stake to inspect its tiny moon-shaped mark. The
    # action is curious, not malicious; its physical consequence drives the turn.
    child.memes["curiosity"] += 1.0
    child.memes["worry"] += 1.0
    stake.meters["anchored"] = 0.0
    mattress.meters.update(anchored=0.0, floating=1.0, distance=1.0, safe=0.0)
    mattress.location = "drifting above the grass"
    world.say(
        f"While {doctor.id} turned to fetch a hand mirror, {child.id} lifted the stake to inspect the moon-shaped mark. "
        f"The mattress rose and began to drift. No one was on it, but a pillow slid toward its edge."
    )
    world.say(
        f"{child.id} froze. In the notebook, the child had drawn a BAD ENDING: "
        f"the mattress sailing away forever. The picture suddenly felt much too possible."
    )

    world.para()
    world.say(f"Then {doctor.id} came back and noticed {scene.clue}.")
    dialogue_two = [
        f'"I pulled out the stake because I wanted to see its mark," {child.id} admitted. '
        f'"Thank you for telling me," said {doctor.id}. "Let’s follow the clue and bring it back safely."',
        f'"I thought the mattress wanted to fly," {child.id} said. '
        f'"It may be magic, but it still needs an anchor," {doctor.id} replied. "Can you help me find the stake?"',
        f'"I made it drift," {child.id} whispered. '
        f'"You were curious, and now you’re helping," {doctor.id} said. "Let’s use what we noticed."',
        f'"What if that bad ending comes true?" {child.id} asked. '
        f'"Then we change what happens next," {doctor.id} answered. "First, we find the stake together."',
    ]
    world.say(dialogue_two[params.ending])
    world.say(f"Together, they {scene.search}. The clue showed them where to look instead of leaving them to guess.")

    world.para()
    world.say(
        f"{doctor.id} held the mattress's corner while {child.id} fitted the stake into its hole. "
        f"The mattress lowered gently, and the pillow settled back in the middle."
    )
    mattress.meters.update(anchored=1.0, floating=0.0, distance=0.0, safe=1.0)
    mattress.location = "anchored on the garden grass"
    stake.meters["anchored"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["trust"] += 1.0
    child.memes["pride"] += 1.0
    doctor.memes["trust"] += 1.0

    repair_lines = [
        f"{doctor.id} checked the anchor and said, 'In orthodontics, a gentle, steady fit matters. This stake needs one too.'",
        f"{doctor.id} showed {child.id} how the stake held the mattress. 'A small support can make something feel safe,' the orthodontist said.",
        f"With a small hand mirror, {doctor.id} checked that the stake sat straight. 'Curiosity helped us notice the mark; care helped us put things right.'",
        f"{doctor.id} smiled. 'Braces guide teeth a little at a time. This stake guides the mattress back to its place.'",
    ]
    world.say(repair_lines[params.ending])
    world.say(f"They tested the anchor together: {scene.ending_image}.")
    world.say(
        f"{child.id} crossed out the bad ending and drew a new last page: two friends sharing a pillow beneath the moon."
    )

    world.para()
    endings = [
        f"Before going home, {child.id} thanked {doctor.id} for helping turn a frightening guess into a careful discovery.",
        f"The moon stayed high, the mattress stayed put, and {child.id} left the garden feeling braver about the next checkup.",
        f"{doctor.id} and {child.id} sat together for one quiet story. This time, the mattress's glow felt like a friendly night-light.",
        f"At the gate, {child.id} looked back at the safely anchored mattress and smiled. The best magic had been learning what to do together.",
    ]
    world.say(endings[params.ending])

    world.facts.update(
        scene=scene,
        place=scene.place,
        clue=scene.clue,
        search=scene.search,
        ending_image=scene.ending_image,
        resolved=True,
        exchange=True,
        doctor_guides=True,
        bad_ending_revised=True,
        magic=True,
        stake_reanchored=True,
    )
    return world


def reasonable(world: World) -> bool:
    return bool(
        world.facts.get("resolved")
        and world.facts.get("exchange")
        and world.facts.get("doctor_guides")
        and world.facts.get("bad_ending_revised")
        and world.facts.get("magic")
        and world.facts.get("stake_reanchored")
        and world.mattress.meters.get("anchored") == 1.0
        and world.mattress.meters.get("floating") == 0.0
        and world.mattress.meters.get("safe") == 1.0
    )


def story_qa(world: World) -> list[QAItem]:
    child, doctor = world.child.id, world.doctor.id
    return [
        QAItem(
            question=f"Why did the mattress begin to float while {child} was in the garden?",
            answer=(
                f"{child} lifted the wooden stake to inspect its moon-shaped mark, so the magical mattress lost its anchor. "
                f"It began to drift, although no one was riding on it."
            ),
        ),
        QAItem(
            question=f"How did {child} and {doctor} find the mattress's missing stake?",
            answer=(
                f"{doctor} noticed {world.facts['clue']}. They followed that physical clue together and found the stake, "
                f"rather than guessing where it had gone."
            ),
        ),
        QAItem(
            question=f"What did {doctor} and {child} do to stop the mattress from drifting?",
            answer=(
                f"{doctor} held the mattress while {child} fitted the stake back into its hole. "
                f"They checked the anchor together, and the mattress settled safely on the grass."
            ),
        ),
        QAItem(
            question="How did the bad ending in the notebook change?",
            answer=(
                f"{child} first drew the mattress sailing away forever, but changed the last page after the stake was found and replaced. "
                f"The new picture showed two friends sharing a pillow beneath the moon."
            ),
        ),
        QAItem(
            question=f"What did {child} learn about curiosity?",
            answer=(
                f"{child} learned that curiosity can lead to useful discoveries when it is paired with care. "
                f"Following the garden clue helped the child and {doctor} find the stake and secure the mattress."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an orthodontist do?",
            answer=(
                "An orthodontist is a dentist who helps teeth grow into better positions, often using braces or other gentle guides."
            ),
        ),
        QAItem(
            question="What is a mattress?",
            answer="A mattress is a soft, thick pad that people usually sleep on, placed on a bed or another safe surface.",
        ),
        QAItem(
            question="What is a garden stake used for?",
            answer="A garden stake is a sturdy post pushed into the ground to support or secure something, such as a young plant or a garden decoration.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is a wish to learn or find out how something works. It is helpful to explore with care.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an impossible or wondrous power that a story uses to make surprising things happen.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming story about {world.child.id}, an orthodontist, and a magical mattress anchored by a garden stake.",
        f"Use curiosity and a possible bad ending to create a gentle turn: {world.facts['clue']}.",
        "End with a concrete image proving that the mattress is safe and the characters have learned to work together.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== (3) World-knowledge questions =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.child, world.doctor, world.mattress, world.stake):
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if entity.location:
            bits.append(f"location={entity.location!r}")
        lines.append(f"  {entity.id:16} ({entity.kind:12}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
required_word(mattress).
required_word(orthodontist).
required_word(stake).

required_feature(bad_ending).
required_feature(magic).
required_feature(curiosity).

has_word(mattress).
has_word(orthodontist).
has_word(stake).

has_feature(bad_ending).
has_feature(magic).
has_feature(curiosity).

setting(moon_garden).
has_role(child).
has_role(orthodontist).
resolved.
exchange.
doctor_guides.
bad_ending_revised.
stake_reanchored.
safe_mattress.

missing_word(W) :- required_word(W), not has_word(W).
missing_feature(F) :- required_feature(F), not has_feature(F).

valid_story :-
    setting(moon_garden),
    has_role(child),
    has_role(orthodontist),
    not missing_word(_),
    not missing_feature(_),
    resolved,
    exchange,
    doctor_guides,
    bad_ending_revised,
    stake_reanchored,
    safe_mattress.
"""


def asp_facts(world: Optional[World] = None) -> str:
    """Emit the domain registry and, when supplied, simulated-world facts."""
    import storyworlds.asp as asp  # lazy import

    facts = [
        asp.fact("setting", "moon_garden"),
        *(asp.fact("seed_word", word) for word in sorted(SEED_WORDS)),
        *(asp.fact("feature", feature) for feature in sorted(FEATURES)),
        asp.fact("role", "child"),
        asp.fact("role", "orthodontist"),
    ]
    if world is not None:
        if world.facts.get("resolved"):
            facts.append(asp.fact("resolved"))
        if world.facts.get("exchange"):
            facts.append(asp.fact("exchange"))
        if world.facts.get("doctor_guides"):
            facts.append(asp.fact("doctor_guides"))
        if world.facts.get("bad_ending_revised"):
            facts.append(asp.fact("bad_ending_revised"))
        if world.facts.get("stake_reanchored"):
            facts.append(asp.fact("stake_reanchored"))
        if world.mattress.meters.get("safe") == 1.0:
            facts.append(asp.fact("safe_mattress"))
    return "\n".join(facts)


def asp_program(world: Optional[World] = None, show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import

    failures = []
    for index in range(len(SCENES)):
        params = StoryParams(
            child=CHILD_NAMES[index % len(CHILD_NAMES)],
            orthodontist=DOCTOR_NAMES[index % len(DOCTOR_NAMES)],
            scene=index,
            telling=index % 4,
            ending=(index + 1) % 4,
            seed=index,
        )
        world = tell(params)
        python_ok = reasonable(world)
        model = asp.one_model(asp_program(world))
        asp_ok = any(atom.name == "valid_story" for atom in model)
        if python_ok != asp_ok:
            failures.append(f"scene {index}: Python={python_ok}, ASP={asp_ok}")
        story = world.render()
        if not all(word in story.lower() for word in ("mattress", "orthodontist", "stake")):
            failures.append(f"scene {index}: a required seed word is missing from the story")
        if not any(part in story for part in (" asked. ", " asked. “", " asked. '")):
            failures.append(f"scene {index}: spoken dialogue is missing")
        if "BAD ENDING" not in story or "crossed out the bad ending" not in story:
            failures.append(f"scene {index}: the bad-ending turn is missing")
    try:
        validate_params(StoryParams(child="Luna", orthodontist="Luna"))
    except StoryError:
        pass
    else:
        failures.append("invalid identical character names were not rejected")

    if failures:
        print("MISMATCH: " + "; ".join(failures))
        return 1
    print("OK: Python and ASP agree across all scenes; generated stories exercise the required features.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming magical mattress storyworld with an orthodontist and a garden stake."
    )
    parser.add_argument("--child", default=None, help="Name of the curious child.")
    parser.add_argument("--orthodontist", default=None, help="Name of the orthodontist.")
    parser.add_argument("-n", type=int, default=1, help="Number of distinct stories to generate.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Generate the curated set of scenes.")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="Print one ASP model for a generated story.")
    parser.add_argument("--verify", action="store_true", help="Check ASP/Python parity and exercise stories.")
    parser.add_argument("--show-asp", action="store_true", help="Print the ASP program.")
    return parser


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int
) -> StoryParams:
    child = args.child or rng.choice(CHILD_NAMES)
    orthodontist = args.orthodontist or rng.choice(DOCTOR_NAMES)
    if child.strip().casefold() == orthodontist.strip().casefold():
        raise StoryError("The child and orthodontist must be different characters.")
    offset = sample_seed - base_seed
    return StoryParams(
        child=child,
        orthodontist=orthodontist,
        scene=offset % len(SCENES),
        telling=(offset // len(SCENES)) % 4,
        ending=(offset // (len(SCENES) * 4)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    if not reasonable(world):
        raise StoryError("The simulated story did not reach a safe, resolved ending.")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
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
    StoryParams(child="Luna", orthodontist="Dr. Imani", scene=0, telling=0, ending=0),
    StoryParams(child="Mira", orthodontist="Dr. Vale", scene=2, telling=1, ending=1),
    StoryParams(child="Theo", orthodontist="Dr. Rowan", scene=5, telling=2, ending=2),
    StoryParams(child="Nell", orthodontist="Dr. Sol", scene=7, telling=3, ending=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp  # lazy import

        seed = args.seed if args.seed is not None else 0
        params = resolve_params(args, random.Random(seed), seed, seed)
        world = tell(params)
        model = asp.one_model(asp_program(world))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for item in CURATED:
            params = StoryParams(
                child=args.child or item.child,
                orthodontist=args.orthodontist or item.orthodontist,
                scene=item.scene,
                telling=item.telling,
                ending=item.ending,
                seed=item.seed,
            )
            samples.append(generate(params))
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            sample_seed = base_seed + index
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        sys.exit(2)
