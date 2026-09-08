#!/usr/bin/env python3
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

THEME = "the moonlit kingdom"
SEED_WORDS = {"slay"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self):
        for key in ("distance", "danger", "brightness", "strength"):
            self.meters.setdefault(key, 0.0)
        for key in ("fear", "hope", "courage", "trust", "wonder", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    companion: str = "Pip"
    dragon: str = "Ember"
    trial: int = 0
    suspense: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    object: str
    threat: str
    clue: str
    false_lead: str
    question: str
    discovery: str
    truth: str
    brave_action: str
    resolution: str
    final_image: str
    lesson: str


TRIALS = [
    Trial(
        object="the silver crown",
        threat="a shadow dragon circled the castle tower and the crown's moonstone went dark",
        clue="three warm scales beside the locked bell rope",
        false_lead="a broken window seemed to show that the dragon had flown away with the crown",
        question="Why would a dragon leave warm scales beside a bell rope if it had stolen the crown?",
        discovery="found a hidden stair behind the old bell",
        truth="the dragon had not stolen the crown; it had been trapped below the tower and was trying to warn the kingdom",
        brave_action="rang the bell three times, then lowered a silk rope into the darkness",
        resolution="helped the dragon climb free and placed the crown beneath the moonstone lantern",
        final_image="the moonstone shone over the tower while the dragon curled peacefully beside the bell",
        lesson="Courage listens for the truth before it strikes at a frightening shape.",
    ),
    Trial(
        object="the sleeping princess's blue rose",
        threat="a misty beast crept through the garden, and every blue rose bent toward its footsteps",
        clue="silver dew shaped like tiny footprints around the dry fountain",
        false_lead="a thorny hedge appeared to hide a monster's long arm",
        question="Why were the footprints silver when the beast's path was covered in ordinary dust?",
        discovery="lifted the fountain's loose stone and revealed a crystal tunnel",
        truth="the beast was a lonely garden keeper whose magic had gone wild when the fountain ran dry",
        brave_action="carried the last bucket of water through the tunnel instead of raising a sword",
        resolution="filled the fountain and returned the blue rose to the princess's bedside",
        final_image="the rose opened beside the sleeping princess as the garden keeper hummed under the stars",
        lesson="A gentle act can break a spell that a sharp weapon would only deepen.",
    ),
    Trial(
        object="the golden harp",
        threat="a giant wolf's howl shook the royal hall, and one harp string snapped by itself",
        clue="a feather caught in the harp's golden frame",
        false_lead="deep claw marks pointed toward the wolf's cave",
        question="What could a soft feather reveal that heavy claw marks could not?",
        discovery="followed the feather trail to a nest beneath the stage",
        truth="the wolf was guarding a tiny gryphon whose wing had tangled in the harp strings",
        brave_action="sang a steady tune while the wolf held still and the gryphon was freed",
        resolution="mended the harp with a moon-thread and carried the gryphon to its mountain nest",
        final_image="the repaired harp played softly while the wolf watched dawn rise beside the stage",
        lesson="Suspense fades when frightened creatures share what they know.",
    ),
    Trial(
        object="the lantern of first light",
        threat="the forest swallowed every path, and a horned giant whispered that dawn would never return",
        clue="a line of glowing seeds led away from the giant's footprints",
        false_lead="the giant's enormous shadow covered the only road home",
        question="Why did the glowing seeds point away from the giant instead of toward his cave?",
        discovery="opened a hollow oak and found the stolen lantern hidden inside",
        truth="the giant had been guarding the lantern from a cold wind that wanted to extinguish it",
        brave_action="shielded the flame with her cloak and asked the giant to walk beside her",
        resolution="carried the lantern to the forest gate with the giant as her guide",
        final_image="golden dawn spilled between the trees, and the giant's shadow became a welcoming arch",
        lesson="A frightening guard may be protecting the very hope you seek.",
    ),
]


@dataclass
class World:
    hero: Entity
    companion: Entity
    dragon: Entity
    relic: Entity
    tower: Entity
    forest: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero, "character", "girl", params.hero, location="castle")
    companion = Entity(params.companion, "character", "fox", params.companion, location="castle")
    dragon = Entity(params.dragon, "creature", "dragon", params.dragon, location="beyond the mist")
    relic = Entity("relic", "thing", "relic", "the royal relic", location="castle")
    tower = Entity("tower", "place", "tower", "the moon tower", location="castle")
    forest = Entity("forest", "place", "forest", "the whispering forest", location="kingdom")
    return World(hero, companion, dragon, relic, tower, forest)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, c, d = world.hero, world.companion, world.dragon
    trial = TRIALS[params.trial % len(TRIALS)]

    h.memes["fear"] = 2
    h.memes["hope"] = 1
    c.memes["fear"] = 1
    c.memes["trust"] = 1
    d.meters["danger"] = 3
    d.memes["fear"] = 2
    world.relic.meters["brightness"] = 1

    openings = [
        f"Once, beneath a pearly moon, {h.id} lived in a kingdom where every promise was kept.",
        f"In the oldest corner of the kingdom, {h.id} watched moonlight silver the castle roofs.",
        f"Long ago, when bells could speak and rivers remembered names, {h.id} served as the kingdom's young guardian.",
        f"At midnight, {h.id} stood beside the castle gate while the stars trembled like tiny candles.",
    ]
    world.say(openings[params.suspense % len(openings)])
    world.say(f"That night, {trial.threat}. Without {trial.object}, the kingdom's ancient protection would fail.")
    world.say(f"{h.id} took a lantern, and {c.id} tucked a bright scarf around their neck. They stepped into the {world.forest.label}.")
    world.para()

    world.say(f"The first sign was {trial.clue}. Ahead, {trial.false_lead}.")
    world.say(f"{c.id} whispered, 'Should we run before the monster sees us?'")
    world.say(f"{h.id} answered, 'We may run from danger, but first we must learn what the clues are saying.'")
    world.say(f"The question that steadied {h.id} was this: {trial.question}")
    h.memes["courage"] += 1
    c.memes["trust"] += 1
    world.say("The forest grew so quiet that they could hear one silver drop fall from a leaf.")
    world.para()

    world.say(f"Then {h.id} {trial.discovery}.")
    world.say(f"Inside waited a darkness shaped like wings. {d.id} lifted its head, and the lantern flame shrank.")
    world.say(f"{c.id} cried, 'The beast will slay us!'")
    world.say(f"{h.id} held up a hand. 'No,' {h.id} said. 'A true hero does not slay what fear has not yet explained.'")
    world.say(f"The dragon spoke in a tired voice: 'I did not take {trial.object}; {trial.truth}.'")
    d.memes["fear"] = 1
    d.memes["trust"] += 2
    h.memes["wonder"] += 1
    world.para()

    world.say(f"{h.id} saw that the dragon's claws were shaking. Instead of drawing a blade, {h.id} {trial.brave_action}.")
    world.say(f"{c.id} asked, 'Can we believe the dragon?'")
    world.say(f"{h.id} replied, 'We can test its words by helping carefully.'")
    world.say(f"The dragon lowered its head and showed them the path. Its warning matched every clue.")
    world.para()

    world.say(f"Together, the three travelers {trial.resolution}.")
    world.say(f"The danger faded because the hidden truth had been faced, not because anyone had been slain.")
    world.say(f"{trial.final_image}.")
    world.say(f"Before returning home, {h.id} wrote the lesson in the castle book: {trial.lesson}")

    world.facts.update(
        trial=trial,
        resolved=True,
        hero=h.id,
        companion=c.id,
        dragon=d.id,
        relic=trial.object,
        clue=trial.clue,
        false_lead=trial.false_lead,
        question=trial.question,
        discovery=trial.discovery,
        truth=trial.truth,
        brave_action=trial.brave_action,
        resolution=trial.resolution,
        final_image=trial.final_image,
        lesson=trial.lesson,
        suspense=params.suspense,
    )
    h.memes["hope"] += 2
    h.memes["courage"] += 2
    c.memes["hope"] += 1
    d.memes["trust"] += 1
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What danger threatened the kingdom?",
            f"The kingdom faced this danger: {f['trial'].threat}. The missing {f['relic']} made the threat especially serious.",
        ),
        QAItem(
            "What clue helped the heroes understand the mystery?",
            f"They noticed {f['clue']}. That clue mattered because it led them to {f['discovery']}.",
        ),
        QAItem(
            "Why did the dragon seem dangerous at first?",
            f"The dragon seemed dangerous because it appeared during a frightening event. Later it explained that {f['truth']}.",
        ),
        QAItem(
            "Why did the hero choose not to slay the dragon?",
            f"The hero chose not to slay the dragon because fear had not proved it guilty. The hero listened, tested the clues, and discovered the dragon needed help.",
        ),
        QAItem(
            "How was the kingdom saved?",
            f"The travelers {f['resolution']}. Their careful courage restored safety and hope.",
        ),
        QAItem(
            "What lesson did the hero learn?",
            f"The hero learned this lesson: {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is suspense?",
            "Suspense is the feeling of wondering what will happen next while a danger, secret, or difficult choice is still unresolved.",
        ),
        QAItem(
            "What does slay mean?",
            "Slay is an old-fashioned word meaning to kill, especially in a tale about a battle or monster. In this story, the heroes choose understanding instead of slaying a frightened creature.",
        ),
        QAItem(
            "What is a fairy tale?",
            "A fairy tale is a story that may include magic, brave heroes, talking animals, enchanted places, and a lesson.",
        ),
        QAItem(
            "Why are clues useful in a mystery?",
            "Clues are useful because they give evidence about what happened and help characters test guesses instead of blaming someone too quickly.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a suspenseful fairy tale in which {f['hero']} searches for {f['relic']} in a moonlit kingdom.",
        f"Use the word 'slay', but show why the hero refuses to slay a creature before learning the truth. Include this clue: {f['clue']}.",
        f"Tell a child-friendly fairy tale where {f['hero']}, {f['companion']}, and a dragon solve a danger through courage and careful listening. End with: {f['final_image']}",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    for entity in [world.hero, world.companion, world.dragon, world.relic, world.tower, world.forest]:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(moonlit_kingdom).
feature(moonlit_kingdom, suspense).
style(moonlit_kingdom, fairy_tale).
word(moonlit_kingdom, slay).
requires(moonlit_kingdom, courage).
requires(moonlit_kingdom, truth).
valid_story(S) :- setting(S), feature(S, suspense), style(S, fairy_tale),
                   word(S, slay), requires(S, courage), requires(S, truth).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "moonlit_kingdom"),
            asp.fact("feature", "moonlit_kingdom", "suspense"),
            asp.fact("style", "moonlit_kingdom", "fairy_tale"),
            asp.fact("word", "moonlit_kingdom", "slay"),
            asp.fact("requires", "moonlit_kingdom", "courage"),
            asp.fact("requires", "moonlit_kingdom", "truth"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if not ok:
        print("MISMATCH: ASP rules rejected the story domain.")
        return 1
    for seed in range(4):
        sample = generate(
            StoryParams(
                hero="Luna",
                companion="Pip",
                dragon="Ember",
                trial=seed,
                suspense=seed,
                ending=seed,
                seed=seed,
            )
        )
        if "slay" not in sample.story.lower():
            print("MISMATCH: generated story omitted the seed word.")
            return 1
        if not sample.story_qa:
            print("MISMATCH: generated story omitted grounded questions.")
            return 1
    print("OK: ASP and Python agree; generated stories pass the world checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suspenseful fairy tales in a moonlit kingdom.")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--companion", default=None)
    parser.add_argument("--dragon", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Mira", "Elara", "Nessa", "Rose"])
    companion = args.companion or rng.choice(["Pip", "Wren", "Tobin", "Moss", "Fenn"])
    dragon = args.dragon or rng.choice(["Ember", "Ashwing", "Cinder", "Glimmer"])
    if hero == companion:
        raise StoryError("The hero and companion must have different names.")
    if dragon in {hero, companion}:
        raise StoryError("The dragon must have a name different from the hero and companion.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        companion=companion,
        dragon=dragon,
        trial=offset % len(TRIALS),
        suspense=(offset // len(TRIALS)) % 4,
        ending=(offset // (len(TRIALS) * 4)) % 4,
        seed=sample_seed,
    )


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
    StoryParams(hero="Luna", companion="Pip", dragon="Ember", trial=0, suspense=0, ending=0),
    StoryParams(hero="Mira", companion="Wren", dragon="Ashwing", trial=1, suspense=1, ending=1),
    StoryParams(hero="Elara", companion="Moss", dragon="Glimmer", trial=2, suspense=2, ending=2),
    StoryParams(hero="Nessa", companion="Fenn", dragon="Cinder", trial=3, suspense=3, ending=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
    main()
