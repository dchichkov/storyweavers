#!/usr/bin/env python3
"""
A small mystery storyworld built around a delicate mechanism, with friendship,
a cautionary turn, and a twist ending.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
% A mystery is reasonable when there is a clue, a careful search, and a twist.
mystery_story(S) :- setting(S), has_friendship(S), has_cautionary_turn(S), has_twist(S).
safe_clue(C) :- clue(C), not dangerous(C).
good_resolution(S) :- mystery_story(S), solved(S).
"""

SETTING = "old clock tower"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    friend: str
    object: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    wrong_try: str
    clue: str
    dialogue: str
    correction: str
    twist: str
    ending: str
    lesson: str


@dataclass
class World:
    place: str = SETTING
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
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
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.label:
                bits.append(f"label={e.label!r}")
            lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The main character needs a name.")
    if not params.friend.strip():
        raise StoryError("The friend needs a name.")
    if params.object not in {"key", "gear", "map", "lantern", "note", "coin"}:
        raise StoryError("The mystery object must be a small plausible item.")
    if params.name == params.friend:
        raise StoryError("The character and friend should be different people.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "old_clock_tower"),
        asp.fact("has_friendship", "old_clock_tower"),
        asp.fact("has_cautionary_turn", "old_clock_tower"),
        asp.fact("has_twist", "old_clock_tower"),
        asp.fact("mystery_clue", "old_clock_tower"),
        asp.fact("safe_clue", "old_clock_tower"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_objects() -> list[str]:
    return ["key", "gear", "map", "lantern", "note", "coin"]


NAMES = ["Mara", "Nico", "Ari", "Elin", "Tomas", "Pia", "Jude", "Lina"]
FRIENDS = ["bearded boy", "quiet girl", "curious child", "small neighbor", "old helper", "brave friend"]
SCENARIOS = [
    Scenario(
        key="missing_tick",
        premise="were listening to the tower and found the ticking sounded wrong",
        trouble="The middle bell had stopped, and the whole room felt too still.",
        wrong_try="pulling the chain harder only made the brass wheel slip",
        clue="a thin trail of dust pointed toward a panel behind the dial",
        dialogue='"That dust is telling us something," the friend whispered. "Then we should follow it," answered the other.',
        correction="opened the panel gently, reset the loose spring, and turned the wheel by hand",
        twist="inside the panel, they found a small paper note saying the tower had been testing them all along",
        ending="the bell rang again, bright and clear, while the note fluttered safely into Mara's pocket",
        lesson="some warnings are clues in disguise",
    ),
    Scenario(
        key="locked_drawer",
        premise="had come to find why a desk drawer kept opening by itself",
        trouble="Every time the friends stepped away, the drawer slid out one finger's width.",
        wrong_try="pressing the handle down made the latch snap more loudly",
        clue="a shiny gear tooth was bent just enough to catch on the wood",
        dialogue='"It is not a ghost," the friend said. "It is a stuck part." "Then we can be careful," came the reply.',
        correction="lifted the gear free, straightened the tooth, and oiled the latch with one careful drop",
        twist="the drawer was hiding the same map they had been searching for, folded beneath a false bottom",
        ending="the map lay open at last, and the drawer stayed still like it had never wanted to run away",
        lesson="a mystery can hide in a simple mechanism",
    ),
    Scenario(
        key="fading_lantern",
        premise="were searching the tower stairs by lantern light",
        trouble="The lantern kept dimming whenever they reached the turn above the spiral step.",
        wrong_try="shaking it made the flame sputter and smoke the glass",
        clue="the wick was intact, but the little air hole was nearly blocked by lint",
        dialogue='"Hold it steady," the friend said. "I can see the problem now."',
        correction="cleaned the hole with a pin, trimmed the wick, and shielded the flame with both hands",
        twist="the brightened lantern revealed not a thief, but a hidden family crest painted on the wall",
        ending="the crest glowed softly in the lantern beam while the stairs became safe again",
        lesson="care solves more than hurry does",
    ),
    Scenario(
        key="ticking_box",
        premise="were examining a small tin box left on a windowsill",
        trouble="The box ticked whenever the wind touched it, and nobody knew why.",
        wrong_try="opening it too fast only sent the lid bouncing shut",
        clue="a tiny magnet had slipped from the clasp and rolled under a ribbon",
        dialogue='"Let us not force it," the friend warned. "Let us look first." "Good idea," said the other.',
        correction="moved the magnet back into place and eased the clasp apart with a pencil tip",
        twist="the box held a pocket watch set to the exact minute their grandmother used to visit",
        ending="the watch stayed silent in the friends' hands, and the wind no longer fooled the box",
        lesson="a caution can keep a surprise from breaking",
    ),
    Scenario(
        key="secret_compass",
        premise="were tracing a strange arrow scratched into the tower floor",
        trouble="The arrow pointed in two directions at once, which made no sense.",
        wrong_try="guessing randomly led them into a dusty dead end",
        clue="the arrow was really the shadow of a dangling gear, not a mark in the wood",
        dialogue='"Look at the light, not just the floor," the friend said. "Then the answer changes," replied the other.',
        correction="moved the curtain aside, steadied the gear, and followed the shadow where it landed",
        twist="the shadow pointed to a hidden stair and a doorway they had passed twice before",
        ending="they laughed quietly when the secret stair opened under the same familiar dust",
        lesson="sometimes the clue is made by what moves, not what stays",
    ),
    Scenario(
        key="false_alarm",
        premise="were guarding the tower room after hearing a strange clatter",
        trouble="A metal clang echoed from the floor below and frightened them both.",
        wrong_try="running at the noise only made the echo bounce faster",
        clue="the sound came from a loose chain swinging into a bell brace",
        dialogue='"We should slow down," the friend said, breathing hard. "Yes, and then listen," the other answered.',
        correction="tied the chain back with twine and padded the brace with cloth",
        twist="the clang had been triggered by the tower cat, who led them straight to the missing keys",
        ending="the cat purred on the keys while the room grew calm and ordinary again",
        lesson="not every alarm is danger, but every alarm deserves care",
    ),
]

OPENINGS = [
    "In the old clock tower, {name} and {friend} found a mystery waiting beside the mechanism.",
    "One windy evening, {name} climbed into the old clock tower with {friend} and one small question.",
    "The old clock tower clicked twice, and {name} knew something about the mechanism had gone wrong.",
    "When the lamps were lit in the tower room, {name} and {friend} spotted a curious sign of trouble.",
    "At the top of the stairs, {name} and {friend} paused beside the tall mechanism and listened.",
]

REACTIONS = [
    "{name} wanted to solve it at once, but caution asked for a slower look.",
    '"Let us not make it worse," {friend} said, and {name} nodded.',
    "{name} held back from touching anything until the clue made sense.",
    '"A careful guess is better than a loud mistake," {name} whispered.',
    "The friends shared one worried glance, then chose to search with care.",
]

ACTIONS = [
    "checked the loose parts one by one",
    "moved the fragile piece aside before trying again",
    "followed the sound to its source",
    "lit the dark corner and searched for a small clue",
    "tested the mechanism with a gentle touch",
    "looked where the dust had gathered most thickly",
]

CELEBRATIONS = [
    "Their shoulders relaxed when the answer finally fit.",
    "The room felt friendlier once the mechanism behaved again.",
    "They smiled at each other, glad they had chosen care over haste.",
    "The tower seemed to breathe easier with the mystery solved.",
    "Their quiet triumph felt bigger than the room itself.",
]


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        friend=rng.choice(FRIENDS),
        object=rng.choice(valid_objects()),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with friendship and caution.")
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--object")
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.friend:
        params.friend = args.friend
    if args.object:
        params.object = args.object
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    friend = world.add(Entity(id="friend", kind="character", label=params.friend))
    obj = world.add(Entity(id="object", kind="thing", label=params.object))
    mechanism = world.add(Entity(id="mechanism", kind="thing", label="mechanism"))
    world.facts.update(
        hero=hero,
        friend=friend,
        object=obj,
        mechanism=mechanism,
        setting=SETTING,
        friendship=True,
        cautionary=True,
        twist=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    obj = world.get("object")
    mechanism = world.get("mechanism")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    opening = rng.choice(OPENINGS).format(name=hero.label, friend=friend.label)
    reaction = rng.choice(REACTIONS).format(name=hero.label, friend=friend.label)
    action = rng.choice(ACTIONS)
    celebration = rng.choice(CELEBRATIONS)

    hero.bump_meme("curiosity")
    friend.bump_meme("loyalty")
    mechanism.bump_meter("used", 1)

    world.say(opening)
    world.say(
        f"{hero.label} had brought the {obj.label} because it seemed tied to the strange mechanism, "
        f"and {friend.label} stayed close. Together they {scenario.premise}."
    )
    world.para()
    world.say(scenario.trouble)
    world.say(f"The first attempt was too hasty: {scenario.wrong_try}.")
    world.say(reaction)
    world.para()
    world.say(f"They began by {action}.")
    world.say(scenario.dialogue)
    world.say(f"That caution led them to the true clue: {scenario.clue}.")
    world.para()
    world.say(f"With careful hands, they {scenario.correction}.")
    world.say(scenario.twist)
    world.say(celebration)
    world.para()
    world.say(
        f"In the end, {scenario.ending}. {hero.label} and {friend.label} kept the {obj.label} safe and agreed that {scenario.lesson}."
    )

    world.facts.update(
        scenario=scenario.key,
        clue=scenario.clue,
        trouble=scenario.trouble,
        wrong_try=scenario.wrong_try,
        correction=scenario.correction,
        twist_text=scenario.twist,
        ending_image=scenario.ending,
        lesson=scenario.lesson,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    obj = f["object"].label
    return [
        f"Write a child-friendly mystery story about {hero} and {friend} in the {SETTING}.",
        f"Use the word mechanism and show a cautious friendship that uncovers a twist.",
        f"Tell a mystery with a small object like a {obj} and a careful ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    obj = f["object"].label
    return [
        QAItem(
            question="What setting does the story take place in?",
            answer=f"It takes place in the {SETTING}.",
        ),
        QAItem(
            question="What problem started the mystery?",
            answer=str(f["trouble"]),
        ),
        QAItem(
            question=f"What clue did {hero} and {friend} notice?",
            answer=f"They noticed that {f['clue']}.",
        ),
        QAItem(
            question="What twist changed the way the friends understood the mystery?",
            answer=str(f["twist_text"]),
        ),
        QAItem(
            question=f"What object did they keep safe at the end?",
            answer=f"They kept the {obj} safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of working parts that move together to do a job.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means warning someone to be careful so they can avoid trouble.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story feel different from what you expected.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


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


def asp_verify() -> int:
    import asp

    program = asp_program("#show mystery_story/1.\n#show safe_clue/1.\n#show good_resolution/1.")
    model = asp.one_model(program)
    atoms = {(sym.name, tuple(arg.name if arg.type != 3 else arg.string for arg in sym.arguments)) for sym in model}
    expected = {
        ("mystery_story", ("old_clock_tower",)),
        ("safe_clue", ("old_clock_tower",)),
        ("good_resolution", ("old_clock_tower",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_resolution/1."))
    return sorted(set(asp.atoms(model, "good_resolution")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
    StoryParams(name="Mara", friend="quiet girl", object="key", seed=11),
    StoryParams(name="Nico", friend="curious child", object="map", seed=29),
    StoryParams(name="Ari", friend="old helper", object="lantern", seed=47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible mystery stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
