#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ace_magic_twist_kindness_superhero_story.py
============================================================================

A standalone storyworld for a small superhero tale about Ace, a little helper
with a magical twist.  The world is built from typed entities with physical
meters and emotional memes, and it generates a complete child-facing story:
Ace meets a problem, a magical twist changes the plan, kindness saves the day,
and the ending proves what changed.

The core premise is simple:
- Ace wants to help as a superhero.
- A magic item causes a surprising twist.
- Kindness, not force, solves the problem.
- The ending shows Ace using the magic in a gentle, useful way.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/ace_magic_twist_kindness_superhero_story.py
    python storyworlds/worlds/gpt-5.4-mini/ace_magic_twist_kindness_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/ace_magic_twist_kindness_superhero_story.py --verify
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Theme:
    id: str
    scene: str
    opener: str
    hero_title: str
    helper_title: str
    goal: str
    place: str
    ending_image: str


@dataclass
class Twist:
    id: str
    label: str
    source: str
    effect: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessMove:
    id: str
    label: str
    action: str
    method: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("ace")
    if not hero or hero.meters["trouble"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    sidekick = world.entities.get("milo")
    if sidekick:
        sidekick.memes["hope"] += 1
    out.append("__twist__")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("ace", Entity("x")).memes["kindness"] < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy = world.entities.get("toy")
    if toy:
        toy.meters["safe"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_twist(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("ace")
    hero.meters["trouble"] += 1
    propagate(sim, narrate=False)
    return {"worry": hero.memes["worry"] >= THRESHOLD}


def can_use_magic(tw: Twist, move: KindnessMove) -> bool:
    return "magic" in tw.tags and "kindness" in move.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for twist in TWISTS:
            for move in KINDNESS_MOVES:
                if can_use_magic(twist, move):
                    combos.append((theme, twist, move))
    return combos


@dataclass
class StoryParams:
    theme: str
    twist: str
    kindness: str
    ace_name: str = "Ace"
    sidekick_name: str = "Milo"
    villain_name: str = "Dr. Grin"
    seed: Optional[int] = None


THEMES = {
    "city": Theme(
        id="city",
        scene="the bright city rooftops",
        opener="Ace leaped from roof to roof with a cape that shimmered in the sun.",
        hero_title="superhero",
        helper_title="sidekick",
        goal="stop the balloon storm",
        place="above the market",
        ending_image="the skyline gleaming behind a safe, smiling city",
    ),
    "park": Theme(
        id="park",
        scene="the leafy park benches and fountains",
        opener="Ace raced past the swings, ready to help anyone who needed a hero.",
        hero_title="hero",
        helper_title="friend",
        goal="save the picnic",
        place="near the pond",
        ending_image="the pond calm again, with children laughing under clear skies",
    ),
    "museum": Theme(
        id="museum",
        scene="the quiet museum halls",
        opener="Ace padded through the museum like a tiny hero on a grand mission.",
        hero_title="superhero",
        helper_title="helper",
        goal="protect the crystal exhibit",
        place="by the glass case",
        ending_image="the crystal sparkling safely under the museum lights",
    ),
}

TWISTS = {
    "magic_glove": Twist(
        id="magic_glove",
        label="magic glove",
        source="a glittering glove",
        effect="it made every touch turn into a trick of sparkling light",
        surprise="the glove tingled and the light jumped in a twisty loop",
        tags={"magic", "twist"},
    ),
    "magic_cape": Twist(
        id="magic_cape",
        label="magic cape",
        source="a blue cape with silver stars",
        effect="it could catch a gust and spin it into a safe shield",
        surprise="the cape swirled and tied the wind into a funny knot",
        tags={"magic", "twist"},
    ),
    "magic_baton": Twist(
        id="magic_baton",
        label="magic baton",
        source="a tiny baton with a glowing gem",
        effect="it could point a beam of light wherever kindness was needed",
        surprise="the baton winked and the beam bent like a playful ribbon",
        tags={"magic", "twist"},
    ),
}

KINDNESS_MOVES = {
    "share": KindnessMove(
        id="share",
        label="sharing",
        action="share the glowing shield",
        method="passed the light to the scared balloon kid first",
        result="the kid smiled and helped hold the balloons still",
        tags={"kindness"},
    ),
    "calm": KindnessMove(
        id="calm",
        label="calming",
        action="calm the crowd with a kind voice",
        method="spoke softly until the people stopped shouting",
        result="everyone made room and the trouble shrank",
        tags={"kindness"},
    ),
    "gentle": KindnessMove(
        id="gentle",
        label="gentle hands",
        action="fix the problem gently",
        method="used careful hands so nothing got broken",
        result="the broken thing stayed safe and could still work",
        tags={"kindness"},
    ),
}

ACE_TAGS = {"ace", "superhero", "magic", "kindness", "twist"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: Ace, magic, twist, and kindness.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--kindness", choices=KINDNESS_MOVES)
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
              if (args.theme is None or c[0] == args.theme)
              and (args.twist is None or c[1] == args.twist)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, twist, kindness = rng.choice(sorted(combos))
    return StoryParams(theme=theme, twist=twist, kindness=kindness)


def _story_action(theme: Theme, tw: Twist, move: KindnessMove, world: World) -> None:
    ace = world.add(Entity(id="ace", kind="character", type="boy", label="Ace", role="hero", tags=set(ACE_TAGS)))
    sidekick = world.add(Entity(id="milo", kind="character", type="boy", label="Milo", role="helper"))
    villain = world.add(Entity(id="villain", kind="character", type="thing", label="Dr. Grin", role="villain"))
    toy = world.add(Entity(id="toy", kind="thing", type="thing", label="the trouble toy"))
    ace.memes["kindness"] = 1
    sidekick.memes["trust"] = 1
    world.say(f"{theme.opener} {theme.scene.capitalize()} was buzzing because {theme.goal} was about to begin.")
    world.say(f"Ace was the {theme.hero_title}, and Milo was the {theme.helper_title} who stayed close by.")
    world.para()
    world.say(f"Then {villain.label_word} caused a problem {theme.place}, and Ace's {tw.source} appeared with a bright, magical twist.")
    ace.meters["trouble"] += 1
    if predict_twist(world)["worry"]:
        ace.memes["worry"] += 1
        world.say(f"{tw.surprise}. Ace took one breath and remembered that a real hero uses kindness first.")
    world.para()
    ace.memes["kindness"] += 1
    world.say(f"Ace decided to {move.action}. {move.method}. {move.result}.")
    toy.meters["safe"] += 1
    toy.meters["fixed"] += 1
    sidekick.memes["joy"] += 1
    world.say(f"Then Ace used the {tw.label} to make one last gentle twirl, and the trouble turned small.")
    world.para()
    world.say(f"In the end, {theme.ending_image}, and Ace waved like a true superhero.")
    world.facts.update(theme=theme, twist=tw, kindness=move, ace=ace, sidekick=sidekick, villain=villain, toy=toy)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.twist not in TWISTS or params.kindness not in KINDNESS_MOVES:
        raise StoryError("Invalid parameters for this world.")
    world = World()
    _story_action(THEMES[params.theme], TWISTS[params.twist], KINDNESS_MOVES[params.kindness], world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a superhero story for a young child that includes the words "Ace", "magic", "twist", and "kindness".',
        "Tell a short story where Ace gets a magical twist and solves the problem with kindness.",
        "Write a gentle superhero adventure with a surprising magic twist and a kind ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tw: Twist = f["twist"]
    move: KindnessMove = f["kindness"]
    theme: Theme = f["theme"]
    return [
        ("Who is the story about?",
         "It is about Ace, a little superhero who tries to help when trouble appears."),
        ("What surprising thing happens?",
         f"Ace finds {tw.label}, and it creates a magical twist that changes the problem in a playful way."),
        ("How does Ace solve the problem?",
         f"Ace uses kindness by {move.method}. That gentle choice helps everyone stay safe and calm."),
        ("How does the story end?",
         f"It ends with {theme.ending_image}. Ace's kindness is what makes the ending feel bright and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a superhero?",
         "A superhero is a brave helper who tries to protect people and solve problems."),
        ("What does kindness mean?",
         "Kindness means being gentle, helpful, and caring toward others."),
        ("What is magic in a story?",
         "Magic is something impossible in real life that can change the world in surprising ways."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="city", twist="magic_glove", kindness="share"),
    StoryParams(theme="park", twist="magic_cape", kindness="calm"),
    StoryParams(theme="museum", twist="magic_baton", kindness="gentle"),
]


def valid_story_params(params: StoryParams) -> bool:
    return params.theme in THEMES and params.twist in TWISTS and params.kindness in KINDNESS_MOVES


ASP_RULES = r"""
theme(city). theme(park). theme(museum).
twist(magic_glove). twist(magic_cape). twist(magic_baton).
kindness(share). kindness(calm). kindness(gentle).

magic(magic_glove). magic(magic_cape). magic(magic_baton).
twisty(magic_glove). twisty(magic_cape). twisty(magic_baton).
kindly(share). kindly(calm). kindly(gentle).

valid(T, X, K) :- theme(T), twist(X), kindness(K), magic(X), kindly(K).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for x in TWISTS:
        lines.append(asp.fact("twist", x))
        if "magic" in TWISTS[x].tags:
            lines.append(asp.fact("magic", x))
        if "twist" in TWISTS[x].tags:
            lines.append(asp.fact("twisty", x))
    for k in KINDNESS_MOVES:
        lines.append(asp.fact("kindness", k))
        lines.append(asp.fact("kindly", k))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible theme/twist/kindness combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
