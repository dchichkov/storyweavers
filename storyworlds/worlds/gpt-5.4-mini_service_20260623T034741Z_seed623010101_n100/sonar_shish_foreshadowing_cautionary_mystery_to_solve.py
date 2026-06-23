#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/sonar_shish_foreshadowing_cautionary_mystery_to_solve.py
==============================================================================================================

A small, standalone storyworld for an animal story about a cave, a sonar
device, a shish sound, and a mystery to solve.

The domain centers on a child-friendly animal crew: a fox, a rabbit, a beaver,
and a bat explore a quiet riverside cave. The world is built around three
narrative instruments:
- Foreshadowing: a barely noticed clue points toward the mystery.
- Cautionary: a risky choice is warned against before trouble grows.
- Mystery to solve: the animals must use sonar, listening, and teamwork to
  learn where the missing sound came from.

The story is state-driven: physical meters track distance, darkness, wetness,
and the presence of clues; emotional memes track curiosity, worry, relief, and
trust. The prose changes according to the world state, and the ending image
proves what changed.

The generated tales always use the words "sonar" and "shish".
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

DEFAULT_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "beaver": {"subject": "he", "object": "him", "possessive": "his"},
            "bat": {"subject": "she", "object": "her", "possessive": "her"},
            "owl": {"subject": "she", "object": "her", "possessive": "her"},
            "cat": {"subject": "she", "object": "her", "possessive": "her"},
            "dog": {"subject": "he", "object": "him", "possessive": "his"},
            "parent": {"subject": "they", "object": "them", "possessive": "their"},
        }
        if self.type in mapping:
            return mapping[self.type][case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    darkness: float = 0.0
    wetness: float = 0.0
    echoes: float = 0.0
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    sound: str
    source_label: str
    source_kind: str
    risky_place: str
    foreshadow: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    makes_sound: bool = False
    safe: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if world.place.echoes < DEFAULT_THRESHOLD:
        return out
    for ent in world.characters():
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["surprise"] += 1
        out.append(f"The cave answered with a soft echo that made the animals look up.")
    return out


def _r_clue_glow(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_seen") and world.place.darkness >= DEFAULT_THRESHOLD:
        sig = ("clue_glow",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.place.echoes += 1
            out.append(f"The small clue seemed to glow in the dark, as if it wanted to be noticed.")
    return out


def _r_find_source(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("sonar_used"):
        return out
    mystery: Mystery = world.facts["mystery"]
    if world.facts.get("source_found"):
        return out
    if world.facts.get("unsafe_choice"):
        return out
    sig = ("source", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["source_found"] = True
    out.append(f"The sonar ticked back a clear answer, and the mystery finally made sense.")
    return out


def _r_wet_footprints(world: World) -> list[str]:
    out: list[str] = []
    if world.place.wetness < DEFAULT_THRESHOLD:
        return out
    for ent in world.characters():
        sig = ("wet", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["wet"] += 1
        ent.memes["worry"] += 1
        out.append(f"The ground near the river grew damp, and the animals had to step more carefully.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("clue_glow", "foreshadowing", _r_clue_glow),
    Rule("wet_footprints", "physical", _r_wet_footprints),
    Rule("echo", "sound", _r_echo),
    Rule("find_source", "mystery", _r_find_source),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.risky_place == place_id:
                combos.append((place_id, mystery_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str = "fox"
    helper: str = "rabbit"
    watcher: str = "bat"
    tool: str = "sonar"
    seed: Optional[int] = None


PLACES = {
    "river_cave": Place(
        id="river_cave",
        label="the river cave",
        darkness=2.0,
        wetness=1.0,
        echoes=0.0,
        tags={"cave", "river", "dark"},
    ),
    "reed_bend": Place(
        id="reed_bend",
        label="the reed bank",
        darkness=1.0,
        wetness=1.0,
        echoes=1.0,
        tags={"river", "reeds", "echo"},
    ),
}

MYSTERIES = {
    "missing_splash": Mystery(
        id="missing_splash",
        clue="a tiny wet footprint beside the stone",
        sound="shish",
        source_label="a hollow shell",
        source_kind="shell",
        risky_place="river_cave",
        foreshadow="a little wet print",
        caution="Don't rush deeper without listening first.",
        tags={"shell", "water", "echo"},
    ),
    "echo_pup": Mystery(
        id="echo_pup",
        clue="a lonely bark that came from nowhere",
        sound="shish",
        source_label="a puppy on a ledge",
        source_kind="animal",
        risky_place="reed_bend",
        foreshadow="a tiny bark in the reeds",
        caution="Don't follow a sound before you know where it started.",
        tags={"animal", "echo", "bark"},
    ),
}

TOOLS = {
    "sonar": Tool(
        id="sonar",
        label="sonar",
        phrase="a little sonar tube",
        purpose="to listen for hidden sounds",
        makes_sound=True,
        safe=True,
        tags={"sonar", "listen"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a lantern",
        purpose="to light the path",
        makes_sound=False,
        safe=True,
        tags={"light"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with sonar, shish, foreshadowing, and a mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero", choices=["fox", "rabbit", "beaver", "bat"])
    ap.add_argument("--helper", choices=["fox", "rabbit", "beaver", "bat"])
    ap.add_argument("--watcher", choices=["fox", "rabbit", "beaver", "bat"])
    ap.add_argument("--tool", choices=TOOLS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["fox", "rabbit", "beaver", "bat"])
    helper = args.helper or rng.choice([c for c in ["fox", "rabbit", "beaver", "bat"] if c != hero])
    watcher = args.watcher or rng.choice([c for c in ["fox", "rabbit", "beaver", "bat"] if c not in {hero, helper}])
    tool = args.tool or "sonar"
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper, watcher=watcher, tool=tool)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place)
    hero = world.add(Entity(id="Hero", kind="character", type=params.hero, label=f"the {params.hero}", role="hero"))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}", role="helper"))
    watcher = world.add(Entity(id="Watcher", kind="character", type=params.watcher, label=f"the {params.watcher}", role="watcher"))
    tool = world.add(Entity(id="sonar", kind="thing", type="tool", label="sonar", phrase="a little sonar tube", tags={"sonar"}))
    clue = world.add(Entity(id="clue", kind="thing", type=mystery.source_kind, label=mystery.source_label, phrase=mystery.clue, tags=set(mystery.tags)))
    world.facts.update(
        hero=hero,
        helper=helper,
        watcher=watcher,
        tool=tool,
        clue=clue,
        mystery=mystery,
        place=place,
        clue_seen=False,
        sonar_used=False,
        source_found=False,
        unsafe_choice=False,
    )
    hero.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    watcher.memes["watchful"] += 1
    world.say(f"{hero.label_word.capitalize()} and {helper.label_word} came to {place.label} with {tool.label}.")
    world.say(f"Long before they solved anything, {mystery.foreshadow} waited near the stone.")
    world.para()
    world.say(f"{helper.label_word.capitalize()} pointed at {mystery.clue} and whispered, \"{mystery.caution}\"")
    world.facts["clue_seen"] = True
    if params.mystery == "echo_pup":
        world.say(f"{watcher.label_word.capitalize()} said they could hear a soft {mystery.sound} from the reeds.")
    else:
        world.say(f"{watcher.label_word.capitalize()} heard a soft {mystery.sound} answer from the dark water.")
    world.para()
    if params.tool == "sonar":
        world.facts["sonar_used"] = True
        hero.memes["focus"] += 1
        world.say(f"{hero.label_word.capitalize()} tapped the sonar and listened closely.")
        world.say(f"The {mystery.sound} came back twice, then stopped, like a secret knocking on the cave wall.")
    else:
        world.facts["unsafe_choice"] = True
        world.say(f"{hero.label_word.capitalize()} tried the wrong tool first, and the answer stayed hidden.")
        world.say(f"The others had to call a pause and choose the sonar instead.")
        world.facts["sonar_used"] = True
        world.say(f"At last, the sonar hummed softly, and the hidden sound began to show its shape.")
    propagate(world)
    if world.facts.get("source_found"):
        world.say(f"It turned out to be {mystery.source_label}, tucked safely where the little sound could bounce back.")
        world.say(f"The animals smiled, and the cave felt friendly again.")
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        watcher.memes["relief"] += 1
    else:
        world.say(f"They still did not know the answer, so they backed out carefully and tried again with more patience.")
    world.para()
    world.say(f"In the end, the clue made sense, the sonar worked, and the shish sound was no longer a mystery.")
    if params.mystery == "missing_splash":
        world.say(f"The little wet footprint, the shell, and the echo all belonged together like pieces of one small puzzle.")
    else:
        world.say(f"The lonely bark in the reeds had seemed strange at first, but it led them to a tiny puppy and a happy ending.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f'Write an animal story for a young child about a mystery in {f["place"].label} that includes the words "sonar" and "shish".',
        f"Tell a gentle foreshadowing story where {f['hero'].label_word} notices {mystery.foreshadow} before solving the mystery.",
        f'Write a cautionary animal tale where the animals stop, listen, and use sonar to learn where the sound "shish" came from.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    watcher: Entity = f["watcher"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"Who solved the mystery at {place.label}?",
            answer=f"{hero.label_word.capitalize()}, {helper.label_word}, and {watcher.label_word} solved it together. {hero.label_word.capitalize()} used sonar, and the others helped by noticing the clues and listening carefully.",
        ),
        QAItem(
            question=f"What was the little clue that foreshadowed the answer?",
            answer=f"The clue was {mystery.foreshadow}. It showed that the strange sound had a real source nearby, so the animals should listen before they guessed.",
        ),
        QAItem(
            question=f"Why did the animals warn each other to be careful?",
            answer=f"They warned each other because the mystery was easy to rush past. The caution helped them slow down, keep safe, and solve the puzzle without making a bigger mess.",
        ),
    ]
    if f.get("source_found"):
        qa.append(QAItem(
            question="What did the sonar help them learn?",
            answer=f"It helped them learn that the shish sound came from {mystery.source_label}. The sonar made the hidden answer bounce back so they could find it with their own eyes.",
        ))
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the animals smiling in the cave, because the mystery had been solved and the scary sound made sense at last. The ending image proves they changed from puzzled to sure of the answer.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is sonar?",
            answer="Sonar is a way to send out a sound and listen for the echo that comes back. People and animals can use it to help find things they cannot see well.",
        ),
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back after it hits a wall, a cave, or another hard place. It can help you tell where something is hiding.",
        ),
        QAItem(
            question="Why should you listen carefully before you rush?",
            answer="Listening carefully helps you notice clues and stay safe. If you rush, you might miss an important warning or go toward a place that is not ready for you.",
        ),
    ]
    if world.facts["mystery"].source_kind == "shell":
        out.append(QAItem(
            question="What is a shell?",
            answer="A shell is the hard outer cover of some water animals. Shells can make a nice tapping or clicking sound when they bump against stone.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M) :- place(P), mystery(M), risky_place(M, P).
found_source(M) :- sonar_used, mystery(M), not unsafe_choice.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("risky_place", mid, m.risky_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
    sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, hero=None, helper=None, watcher=None, tool=None), random.Random(7)))
    if not sample.story or "sonar" not in sample.story or "shish" not in sample.story:
        rc = 1
        print("SMOKE FAIL: generated story missing required words")
    print("OK" if rc == 0 else "FAIL")
    return rc


CURATED = [
    StoryParams(place="river_cave", mystery="missing_splash", hero="fox", helper="rabbit", watcher="bat", tool="sonar"),
    StoryParams(place="reed_bend", mystery="echo_pup", hero="beaver", helper="fox", watcher="rabbit", tool="sonar"),
]


def explain_rejection() -> str:
    return "(No story: the chosen place and mystery do not match this little animal puzzle.)"


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES:
        raise StoryError(explain_rejection())
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.place.label}")
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with sonar and a mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero", choices=["fox", "rabbit", "beaver", "bat"])
    ap.add_argument("--helper", choices=["fox", "rabbit", "beaver", "bat"])
    ap.add_argument("--watcher", choices=["fox", "rabbit", "beaver", "bat"])
    ap.add_argument("--tool", choices=TOOLS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
