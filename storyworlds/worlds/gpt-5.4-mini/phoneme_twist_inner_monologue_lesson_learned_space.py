#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/phoneme_twist_inner_monologue_lesson_learned_space.py
=====================================================================================

A standalone storyworld for a small Space Adventure domain: two kid astronauts
prepare a launch, hear a strange phoneme from the radio, chase a mistaken clue,
discover a friendly twist, and learn that careful listening changes the whole
mission.

The world is intentionally tiny: one ship, one launchpad, one helper robot, one
odd sound, and one lesson. The story is driven by simulated meters and memes,
not by frozen prose templates.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional


# Make the shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"fuel": 0.0, "damage": 0.0, "signal": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "lesson": 0.0})
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    hero: str
    sibling: str
    robot: str
    ship: str
    planet: str
    phoneme: str
    signal_source: str
    twist: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SPACE_NAMES = {
    "hero": ["Mina", "Toby", "Luna", "Kai", "Nora", "Jasper"],
    "sibling": ["Pip", "Bea", "Suri", "Ari", "Finn", "Zia"],
    "robot": ["Bolt", "Tick", "Milo", "Robo", "Spark", "Orbit"],
    "ship": ["Comet Car", "Star Hopper", "Moon Kite", "Rocket Boat"],
    "planet": ["Moon Base", "Blue Orbit", "Red Dune Station", "Silver Crater"],
    "phoneme": ["sh", "th", "oo", "ai", "er", "ph"],
    "signal_source": ["a beacon", "a helper radio", "the ship speaker", "a tiny scanner"],
    "twist": ["it was only a practice signal", "the sound came from the robot", "the clue belonged to a lost puppy in a space crate"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld about a phoneme clue, a twist, and a lesson learned.")
    ap.add_argument("--hero", choices=SPACE_NAMES["hero"])
    ap.add_argument("--sibling", choices=SPACE_NAMES["sibling"])
    ap.add_argument("--robot", choices=SPACE_NAMES["robot"])
    ap.add_argument("--ship", choices=SPACE_NAMES["ship"])
    ap.add_argument("--planet", choices=SPACE_NAMES["planet"])
    ap.add_argument("--phoneme", choices=SPACE_NAMES["phoneme"])
    ap.add_argument("--signal-source", choices=SPACE_NAMES["signal_source"])
    ap.add_argument("--twist", choices=SPACE_NAMES["twist"])
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("space", "phoneme", "twist", "lesson")]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("domain", "space"),
        asp.fact("has_feature", "twist"),
        asp.fact("has_feature", "inner_monologue"),
        asp.fact("has_feature", "lesson_learned"),
        asp.fact("word", "phoneme"),
    ]
    for h in SPACE_NAMES["hero"]:
        lines.append(asp.fact("hero_name", h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(space, phoneme, twist, lesson).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        asp_set = set(asp.atoms(model, "valid"))
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH between ASP and Python valid combos.")
        print("ASP:", sorted(asp_set))
        print("PY :", sorted(py_set))
        return 1

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1

    print("OK: ASP parity and generation smoke test passed.")
    return 0


def predict_signal(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] += 1
    return {"worry": sim.get(hero.id).memes["worry"], "signal": sim.get("radio").meters["signal"]}


def propagate(world: World) -> None:
    if world.get("radio").meters["signal"] >= THRESHOLD and ("signal",) not in world.fired:
        world.fired.add(("signal",))
        for e in list(world.entities.values()):
            if e.role in {"hero", "sibling"}:
                e.memes["curiosity"] += 1


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="boy", role="hero"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="girl", role="sibling"))
    robot = world.add(Entity(id=params.robot, kind="character", type="thing", role="robot"))
    ship = world.add(Entity(id="ship", kind="thing", label=params.ship))
    planet = world.add(Entity(id="planet", kind="thing", label=params.planet))
    radio = world.add(Entity(id="radio", kind="thing", label="radio"))

    world.facts.update(hero=hero, sibling=sibling, robot=robot, ship=ship, planet=planet, radio=radio, params=params)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.get(params.hero)
    sibling = world.get(params.sibling)
    robot = world.get(params.robot)
    radio = world.get("radio")
    ship = world.get("ship")
    planet = world.get("planet")

    hero.memes["curiosity"] += 1
    sibling.memes["curiosity"] += 1

    world.say(
        f"On {planet.label_word}, {hero.id} and {sibling.id} were getting {ship.label_word} ready for a night launch. "
        f"{robot.id} blinked beside them, and the whole deck smelled like metal and moon dust."
    )
    world.say(
        f"Then the radio crackled with a strange little phoneme: “{params.phoneme}.” "
        f"It sounded like a tiny space whisper hiding inside the static."
    )

    world.para()
    pred = predict_signal(world, hero)
    hero.memes["worry"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{hero.id} frowned and looked at the radio in a private little thought: "
        f"Maybe the sound means trouble. Maybe the ship is calling for help."
    )
    world.say(
        f"{sibling.id} leaned closer and said the phoneme again, trying to figure it out before the launch timer reached zero."
    )

    world.para()
    radio.meters["signal"] += 1
    propagate(world)
    world.say(
        f"At last, {robot.id} tapped the speaker and the answer came out with a bright twist: {params.twist}."
    )

    world.para()
    if "practice" in params.twist:
        robot.memes["joy"] += 1
        hero.memes["lesson"] += 1
        sibling.memes["lesson"] += 1
        world.say(
            f"Their big surprise was that the signal was not danger at all. "
            f"It was a practice message, and the phoneme had been a clue to listen more carefully."
        )
    elif "robot" in params.twist:
        robot.meters["signal"] += 1
        hero.memes["lesson"] += 1
        sibling.memes["lesson"] += 1
        world.say(
            f"The sound had come from {robot.id}'s own chest speaker, which had been testing a new voice chip. "
            f"The odd phoneme was not a warning; it was a machine learning to speak more clearly."
        )
    else:
        hero.memes["lesson"] += 1
        sibling.memes["lesson"] += 1
        world.say(
            f"The clue led to a tiny crate tucked under the console. Inside was a lost puppy wearing a blinking tag, and the phoneme had been the tag's soft chirp."
        )

    world.para()
    hero.memes["joy"] += 1
    sibling.memes["joy"] += 1
    world.say(
        f"{hero.id} laughed, because the universe had played a gentle trick on their guess. "
        f"Now they knew that one sound can mean more than one thing, and careful listening matters."
    )
    world.say(
        f"When the launch finally started, {hero.id} and {sibling.id} rode into the dark sky with steadier hearts than before."
    )

    world.facts["outcome"] = "learned"
    world.facts["lesson"] = True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a space adventure story for a young child that includes the word "{p.phoneme}".',
        f"Tell a story where {p.hero} hears a strange phoneme on a spaceship radio, thinks it means trouble, and then learns a helpful lesson.",
        "Write a story with an inner monologue, a twist, and a lesson learned, all set on a moon base.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.get(p.hero)
    sibling = world.get(p.sibling)
    return [
        QAItem(
            question="What strange sound did they hear?",
            answer=f"They heard the phoneme “{p.phoneme}” crackle out of the radio. It sounded mysterious because the ship was quiet and the message was so small.",
        ),
        QAItem(
            question="What was {hero} thinking in their head?".format(hero=hero.id),
            answer=(
                f"{hero.id} thought the sound might mean trouble and worried that the ship was calling for help. "
                f"That inner thought made the moment feel tense before the twist arrived."
            ),
        ),
        QAItem(
            question="What was the twist?",
            answer=(
                f"The twist was that {p.twist}. "
                f"Instead of danger, the strange sound turned out to be something harmless and useful."
            ),
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=(
                "They learned to listen carefully before jumping to conclusions. "
                "A tiny sound can trick you, but patience can show what it really means."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a phoneme?",
            answer="A phoneme is a small sound in a word. Changing one phoneme can change how a word sounds or what it means.",
        ),
        QAItem(
            question="What does a robot helper do on a space mission?",
            answer="A robot helper can watch the controls, speak from the radio, and check small problems so the crew can stay safe.",
        ),
        QAItem(
            question="Why is listening important in space?",
            answer="Space missions use many signals and alarms. Careful listening helps the crew tell a real warning from a simple practice sound.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mina", "Pip", "Bolt", "Star Hopper", "Moon Base", "sh", "a beacon", "it was only a practice signal"),
    StoryParams("Toby", "Bea", "Tick", "Comet Car", "Blue Orbit", "th", "a helper radio", "the sound came from the robot"),
    StoryParams("Luna", "Zia", "Orbit", "Moon Kite", "Red Dune Station", "oo", "the ship speaker", "the clue belonged to a lost puppy in a space crate"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    vals = {
        "hero": args.hero or rng.choice(SPACE_NAMES["hero"]),
        "sibling": args.sibling or rng.choice(SPACE_NAMES["sibling"]),
        "robot": args.robot or rng.choice(SPACE_NAMES["robot"]),
        "ship": args.ship or rng.choice(SPACE_NAMES["ship"]),
        "planet": args.planet or rng.choice(SPACE_NAMES["planet"]),
        "phoneme": args.phoneme or rng.choice(SPACE_NAMES["phoneme"]),
        "signal_source": args.signal_source or rng.choice(SPACE_NAMES["signal_source"]),
        "twist": args.twist or rng.choice(SPACE_NAMES["twist"]),
    }
    if vals["hero"] == vals["sibling"]:
        raise StoryError("The hero and sibling must be different names.")
    return StoryParams(**vals)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} on {p.planet} ({p.phoneme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
