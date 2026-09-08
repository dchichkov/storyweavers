#!/usr/bin/env python3
"""
A standalone Storyweavers world: a folk tale about a peekaboo probe and a lurking
conflict beneath a village bridge.
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


THEME = "the village bridge"
SEED_WORDS = {"peekaboo", "probe", "lurk"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("danger", "water", "weakness", "distance", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "curiosity", "courage", "trust", "anger", "relief"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    name: str = "Luna"
    companion: str = "Pip"
    elder: str = "Grandmother Sela"
    trial: int = 0
    voice: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    object_name: str
    trouble: str
    clue: str
    probe: str
    false_guess: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending_image: str


TRIALS = [
    Trial(
        "the moon bell",
        "the bridge bell stopped ringing whenever the evening wind arrived",
        "a thin line of mud crossed the bell rope and vanished under the bridge",
        "slid a willow probe through the reeds and tapped the hidden stones",
        "the villagers guessed that a jealous crow had stolen the ringing",
        "a family of beavers had wedged branches against the bell's lower rope while building a safe winter dam",
        "removed the branches one at a time and built the beavers a quieter side channel",
        "the bell rang three clear notes while the new channel carried the water gently",
        "A careful question can uncover a hidden need before anger builds a wall.",
        "the moon bell chimed above a silver stream and no branch tugged at its rope",
    ),
    Trial(
        "the baker's blue basket",
        "the basket of festival loaves disappeared before the first hungry neighbor arrived",
        "warm crumbs led from the bakery step toward the shadow beneath the bridge",
        "pushed a long reed beneath the bridge and felt something soft, then something wooden",
        "the villagers blamed a greedy fox who often lurked near the flour sacks",
        "a frightened family had carried the basket away from a falling roof tile and hidden it while they sought help",
        "called the family out, shared the loaves, and repaired the loose tile together",
        "the basket returned with every loaf counted and the roof held firm in the next gust",
        "A conflict may hide fear rather than wickedness, so listening can reveal the fair repair.",
        "blue cloth fluttered from the basket as the whole village ate beneath the mended roof",
    ),
    Trial(
        "the mayor's wooden key",
        "the key to the village storehouse vanished on the morning of the grain count",
        "a bright scratch on the lock matched a trail of splinters under the bridge rail",
        "used a small wooden probe to test the cracks between the old planks",
        "the mayor suspected the miller's apprentice because flour dust marked the path",
        "a loose plank had caught the key and slid it into a hollow beam when the bridge shook",
        "lifted the plank, returned the key, and replaced the worn bridge peg",
        "the lock opened smoothly and the grain count began without anyone being accused",
        "Evidence should guide a search, not turn a neighbor into a villain.",
        "the wooden key hung in its place while the bridge hummed safely over the stream",
    ),
    Trial(
        "the shepherd's red ribbon",
        "the ribbon used to mark the lamb path disappeared during a thick morning mist",
        "a red thread peeked from a clump of reeds where hoofprints ended",
        "lowered a woven probe into the reeds and traced the thread without pulling it",
        "the shepherd feared that a wandering goblin lurked among the misty stones",
        "the ribbon had caught on a thorn when a lamb slipped toward the water",
        "freed the ribbon, guided the lamb back, and tied bright markers along the safe bank",
        "the lamb followed the markers home while the mist lifted from the bridge",
        "When people share what they noticed, a frightening guess can become a solvable problem.",
        "the red ribbon waved above the path like a tiny flag of home",
    ),
    Trial(
        "the potter's silver cup",
        "the cup for the harvest toast rolled away from the village table",
        "a silver glimmer flashed each time the stream moved beneath the bridge",
        "sent a hooked probe between the wet stones and turned it slowly",
        "some villagers said a water spirit lurked below and wanted the cup for a treasure",
        "the cup had rolled through a gap in the table boards after a startled goat bumped the leg",
        "pulled it free, steadied the table, and gave the goat a safer feeding place",
        "the cup shone on the table and the goat stopped knocking against its legs",
        "A strange sight becomes less frightening when someone tests it patiently.",
        "the silver cup caught the sunset while the goat munched beside a steady table",
    ),
    Trial(
        "the school bell ribbon",
        "the ribbon on the school bell vanished just before the children crossed the bridge",
        "a blue tail peekabooed from behind a stone whenever the stream splashed",
        "touched the stone with a birch probe and listened for a hollow sound",
        "the children thought a bridge troll lurked there to frighten them",
        "the ribbon had slipped into a crack where rainwater washed away the soft earth",
        "filled the crack with pebbles, lifted the ribbon, and tied it to a safer hook",
        "the bell rang above the crossing and the children walked over without fear",
        "Courage grows when a frightening story is tested with care and kindness.",
        "the blue ribbon danced from the bell as the children crossed in a bright line",
    ),
    Trial(
        "the orchard lantern",
        "the lantern that guided people home disappeared at dusk",
        "a warm glow peekabooed beneath the bridge, then vanished when anyone stepped near",
        "slid a forked probe along the bank and found a nest of dry reeds",
        "the villagers whispered that a fox spirit lurked there with stolen fire",
        "a hedgehog had dragged the lantern's loose wick into the reeds while seeking warmth",
        "moved the lantern to a stone shelf and made a small dry shelter for the hedgehog",
        "the path shone again and the hedgehog slept safely away from the flame",
        "Kindness can solve a conflict better than chasing what first seems strange.",
        "the orchard lantern glowed above the bridge while a tiny hedgehog curled in its shelter",
    ),
    Trial(
        "the river map",
        "the old map showing the safe stepping stones tore loose from its post",
        "one corner peekabooed beneath the bridge, pinned by a smooth black pebble",
        "reached with a flat probe and tested the current before stepping closer",
        "the ferryman thought a rival had hidden the map to win more crossings",
        "a sudden flood had carried the map downstream and trapped it beneath the bridge",
        "rescued the map, copied it onto a board, and set a high post beyond the flood line",
        "everyone could read the safe route even after the next rain",
        "A shared solution is stronger than a story about who deserves blame.",
        "the new river map stood high while the old one dried beside the warm hearth",
    ),
]


@dataclass
class World:
    hero: Entity
    companion: Entity
    elder: Entity
    object: Entity
    bridge: Entity
    stream: Entity
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


def entity(eid: str, kind: str, type_: str, label: str, location: str = "") -> Entity:
    return Entity(eid, kind, type_, label, location=location)


def build_world(params: StoryParams) -> World:
    world = World(
        hero=entity(params.name, "character", "child", params.name, "village"),
        companion=entity(params.companion, "character", "animal", params.companion, "village"),
        elder=entity(params.elder, "character", "elder", params.elder, "village"),
        object=entity("mystery_object", "thing", "object", "the lost object", "bridge"),
        bridge=entity("bridge", "place", "bridge", "the old bridge", "river"),
        stream=entity("stream", "place", "stream", "the quick stream", "valley"),
    )
    world.facts["theme"] = THEME
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, c, e = world.hero, world.companion, world.elder
    trial = TRIALS[params.trial % len(TRIALS)]

    h.memes["worry"] = 1
    h.memes["curiosity"] = 1
    c.memes["curiosity"] = 1
    e.memes["trust"] = 1
    world.object.meters["distance"] = 1
    world.bridge.meters["weakness"] = 1

    openings = [
        f"Long ago, in a village beside a quick stream, {h.id} watched over {trial.object_name} with {c.id}, a small and nimble companion.",
        f"In the days when bridges had wooden voices, {h.id} and {c.id} crossed the old bridge to check {trial.object_name}.",
        f"At the edge of the village stood a bridge, a stream, and one useful duty. {h.id} carried that duty while {c.id} skipped beside them.",
        f"Every village has a tale about something that goes missing. In this village, {h.id} was guarding {trial.object_name} when trouble began.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"By midday, {trial.trouble}. The empty place made the villagers murmur.")
    world.say(f"{e.id} raised a hand. 'Do not let a conflict grow from a guess,' {e.id} said. 'First, look closely.'")

    world.para()
    world.say(f"Near the bridge, {trial.clue}.")
    world.say(f"{h.id} crouched low. The clue seemed to peekaboo between mud and reeds, showing itself and hiding again.")
    world.say(f"'I could chase the shadow beneath the bridge,' said {c.id}, 'but what if it only looks frightening?'")
    world.say(f"'Then we will probe the place instead of blaming it,' {h.id} replied. 'You watch the bank, and I will test the stones.'")
    world.say(f"Together they {trial.probe}.")
    h.memes["courage"] += 1
    c.memes["trust"] += 1
    world.say(f"At first, {trial.false_guess}. The idea made the villagers step back, for they imagined danger would lurk in every dark corner.")

    world.para()
    world.say(f"{h.id} remembered {e.id}'s advice and compared the marks with the place they found them.")
    world.say(f"The probe did not find a monster. It found a cause: {trial.cause}.")
    world.say(f"{h.id} called, 'Come out and tell us what happened. We can solve this without shouting.'")
    world.say(f"{c.id} added, 'We will listen before we choose sides.'")
    world.say(f"The hidden neighbor answered, and the real story became clear: {trial.cause}.")
    h.memes["trust"] += 1
    h.memes["relief"] += 1
    c.memes["relief"] += 1

    world.para()
    world.say(f"The village then {trial.repair}.")
    world.say(f"They tested the repair: {trial.proof}.")
    world.say(f"{e.id} smiled. 'A probe can find a fact,' {e.id} said, 'but trust helps people use the fact well.'")
    world.say(f"The villagers repeated the lesson: {trial.lesson}")

    world.para()
    endings = [
        trial.ending_image,
        f"From that day on, whenever a shadow seemed to lurk, the villagers remembered the truth. {trial.ending_image}",
        f"The conflict was gone, and a kinder custom remained. {trial.ending_image}",
        f"{c.id} gave a tiny peekaboo wave from the bridge rail. {trial.ending_image}",
    ]
    world.say(endings[params.ending % len(endings)])

    world.object.meters["distance"] = 0
    world.bridge.meters["weakness"] = 0
    world.facts.update(
        object_name=trial.object_name,
        trouble=trial.trouble,
        clue=trial.clue,
        probe=trial.probe,
        false_guess=trial.false_guess,
        cause=trial.cause,
        repair=trial.repair,
        proof=trial.proof,
        lesson=trial.lesson,
        ending=trial.ending_image,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.id
    c = world.companion.id
    f = world.facts
    return [
        QAItem(
            question=f"What went wrong with {f['object_name']}?",
            answer=f"{f['trouble'].capitalize()}. This created a conflict because the villagers did not yet know what had happened.",
        ),
        QAItem(
            question=f"How did {h} investigate the mystery?",
            answer=f"{h} followed {f['clue']} and {f['probe']}. The careful probe revealed evidence instead of relying on a frightening guess.",
        ),
        QAItem(
            question=f"What did {c} and {h} learn about the hidden cause?",
            answer=f"They learned that {f['cause']}. The cause explained the problem without making a neighbor into a villain.",
        ),
        QAItem(
            question="How was the conflict resolved?",
            answer=f"The villagers {f['repair']}. They checked their work and found that {f['proof']}.",
        ),
        QAItem(
            question="What lesson did the folk tale teach?",
            answer=f"It taught that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does peekaboo mean?",
            answer="Peekaboo describes something appearing briefly and then hiding again, often in a playful way.",
        ),
        QAItem(
            question="What is a probe?",
            answer="A probe is a tool or careful action used to test, explore, or learn about something that may be hard to reach.",
        ),
        QAItem(
            question="What does lurk mean?",
            answer="To lurk means to stay hidden while waiting or watching, often where other people cannot easily see you.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a disagreement, problem, or struggle between people, animals, or forces that needs a fair solution.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional story passed from person to person, often with a memorable problem and a lesson.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Tell a child-friendly folk tale at {THEME} about {world.facts['object_name']} and a conflict that seems mysterious at first.",
        f"Write a story using the words peekaboo, probe, and lurk. Let a careful investigation replace a frightening guess.",
        f"Create a folk tale in which {world.hero.id} and {world.companion.id} resolve a conflict through evidence, listening, and repair.",
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
    for obj in [world.hero, world.companion, world.elder, world.object, world.bridge, world.stream]:
        meters = {k: v for k, v in obj.meters.items() if v}
        memes = {k: v for k, v in obj.memes.items() if v}
        lines.append(
            f"  {obj.id:16} ({obj.kind:9}) location={obj.location!r} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(village_bridge).
seed(peekaboo).
seed(probe).
seed(lurk).
feature(conflict).
style(folk_tale).

valid_story :-
    setting(village_bridge),
    seed(peekaboo),
    seed(probe),
    seed(lurk),
    feature(conflict),
    style(folk_tale).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "village_bridge"),
            asp.fact("seed", "peekaboo"),
            asp.fact("seed", "probe"),
            asp.fact("seed", "lurk"),
            asp.fact("feature", "conflict"),
            asp.fact("style", "folk_tale"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program())
    if any(atom.name == "valid_story" for atom in models):
        for params in [
            StoryParams(seed=11),
            StoryParams(trial=3, voice=2, ending=1, seed=12),
        ]:
            sample = generate(params)
            text = sample.story.lower()
            if not all(word in text for word in SEED_WORDS):
                print("MISMATCH: generated story omitted a required seed word.")
                return 1
            if not sample.world or not sample.world.facts.get("resolved"):
                print("MISMATCH: generated story did not resolve its world state.")
                return 1
        print("OK: ASP and Python recognize the peekaboo probe folk-tale domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A folk tale about a peekaboo probe beneath a village bridge.")
    parser.add_argument("--name", default=None)
    parser.add_argument("--companion", default=None)
    parser.add_argument("--elder", default=None)
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
    name = args.name or rng.choice(["Luna", "Mara", "Nia", "Tala", "Rin"])
    companion = args.companion or rng.choice(["Pip", "Moss", "Tiko", "Bram", "Dove"])
    elder = args.elder or rng.choice(["Grandmother Sela", "Old Anja", "Grandfather Ren", "Aunt Omi"])
    if name == companion:
        raise StoryError("The hero and companion must have different names.")
    if name == elder or companion == elder:
        raise StoryError("The elder must be different from the hero and companion.")
    offset = sample_seed - base_seed
    return StoryParams(
        name=name,
        companion=companion,
        elder=elder,
        trial=offset % len(TRIALS),
        voice=(offset // len(TRIALS)) % 4,
        ending=(offset // (len(TRIALS) * 4)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.trial < 0:
        raise StoryError("The trial number cannot be negative.")
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
    StoryParams(name="Luna", companion="Pip", elder="Grandmother Sela", trial=0, seed=0),
    StoryParams(name="Mara", companion="Moss", elder="Old Anja", trial=2, voice=1, ending=1, seed=1),
    StoryParams(name="Nia", companion="Tiko", elder="Grandfather Ren", trial=5, voice=2, ending=2, seed=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP model:", [str(atom) for atom in model])
        return

    if args.n < 1:
        raise StoryError("The number of requested samples must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
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
