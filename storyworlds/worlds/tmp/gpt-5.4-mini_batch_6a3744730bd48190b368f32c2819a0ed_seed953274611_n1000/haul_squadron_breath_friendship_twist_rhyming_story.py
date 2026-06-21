#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/haul_squadron_breath_friendship_twist_rhyming_story.py
======================================================================================

A small standalone storyworld for a rhyming TinyStories-style tale about a
friendship, a twist, and the words haul / squadron / breath.

Premise
-------
Two friends are preparing a tiny toy air-squadron for a windy kite festival.
One child insists on hauling everything at once, but the load is too heavy and
the paper planes bend. A helper twist changes the plan: they share the haul,
take a breath, repair the planes, and arrive together with a bright ending.

The story is deliberately state-driven:
- weight affects strain
- strain affects breathing and mood
- a twist can redirect the plan
- shared hauling restores friendship and joy

The script supports the standard Storyweavers CLI: default runs, -n, --all,
--seed, --trace, --qa, --json, --asp, --verify, and --show-asp.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"load": 0.0, "strain": 0.0, "repair": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "friendship": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    setting: str
    task: str
    load: str
    helper: str
    twist: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None
    load_weight: int = 0
    wind: int = 0


@dataclass
class Setting:
    id: str
    scene: str
    place: str
    sound: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    weight: int
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "hangar": Setting(
        id="hangar",
        scene="a bright little hangar",
        place="the hangar floor",
        sound="The fans hummed softly, and the banners swayed.",
        ending="The squadron rolled out in a neat line.",
        tags={"squadron", "breath"},
    ),
    "hill": Setting(
        id="hill",
        scene="a windy hilltop",
        place="the windy hill",
        sound="The grass bowed low, and the kites snapped above them.",
        ending="The squadron lifted into the sky like silver birds.",
        tags={"squadron", "breath"},
    ),
}

LOADS = {
    "boxes": Load(
        id="boxes",
        label="boxes",
        phrase="three packed boxes of tiny planes",
        weight=3,
        fragile=False,
        tags={"haul"},
    ),
    "glider_cart": Load(
        id="glider_cart",
        label="glider cart",
        phrase="a little cart full of gliders",
        weight=2,
        fragile=True,
        tags={"haul"},
    ),
    "single_bag": Load(
        id="single_bag",
        label="bag",
        phrase="one soft bag of paper wings",
        weight=1,
        fragile=True,
        tags={"haul"},
    ),
}

HELPERS = {
    "rope": Helper(
        id="rope",
        label="rope",
        phrase="a long rope they could loop between the handles",
        tag="share",
        tags={"friendship"},
    ),
    "trolley": Helper(
        id="trolley",
        label="trolley",
        phrase="a little trolley with a squeaky wheel",
        tag="roll",
        tags={"twist"},
    ),
    "bench": Helper(
        id="bench",
        label="bench",
        phrase="the low bench by the door, where they could sort the pieces",
        tag="sort",
        tags={"twist"},
    ),
}

TWISTS = {
    "share": Twist(
        id="share",
        label="shared haul",
        phrase="a shared haul was better than a lonely one",
        action="split the load",
        tags={"friendship", "twist"},
    ),
    "repair": Twist(
        id="repair",
        label="repair twist",
        phrase="a quick repair could save the squadron",
        action="mend the bent wings",
        tags={"twist"},
    ),
    "breath": Twist(
        id="breath",
        label="breath twist",
        phrase="a slow breath could steady the rush",
        action="take a breath and try again",
        tags={"breath", "twist"},
    ),
}

HEROES = ["Mina", "Toby", "Lena", "Noah", "Iris", "Eli"]
FRIENDS = ["Pip", "Zara", "Omar", "June", "Ari", "Bea"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for l in LOADS:
            for h in HELPERS:
                for t in TWISTS:
                    if LOADS[l].weight >= 2 or t in {"share", "breath"}:
                        combos.append((s, l, h, t))
    return combos


def explain_rejection(load: Load, twist: Twist) -> str:
    if load.weight < 2 and twist.id == "repair":
        return "(No story: the load is light, so there is no strong haul problem to twist into a repair tale.)"
    return "(No story: that combination does not make a clear friendship-and-twist story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about a haul, a squadron, and a breath.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.load is None or c[1] == args.load)
              and (args.helper is None or c[2] == args.helper)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        if args.load and args.twist:
            raise StoryError(explain_rejection(LOADS[args.load], TWISTS[args.twist]))
        raise StoryError("(No valid combination matches the given options.)")
    setting, load, helper, twist = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != hero])
    hero_gender = "girl" if hero in {"Mina", "Lena", "Iris"} else "boy"
    friend_gender = "girl" if friend in {"Zara", "June", "Bea"} else "boy"
    return StoryParams(
        setting=setting,
        task="haul",
        load=load,
        helper=helper,
        twist=twist,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        load_weight=LOADS[load].weight,
        wind=rng.randint(0, 2),
    )


def _rhymes(text: str) -> str:
    return text


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    load = world.add(Entity(id="load", label=LOADS[params.load].label, role="load"))
    helper = world.add(Entity(id="helper", label=HELPERS[params.helper].label, role="helper"))
    twist = world.add(Entity(id="twist", label=TWISTS[params.twist].label, role="twist"))
    setting = SETTINGS[params.setting]

    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1

    world.say(
        f"In {setting.scene}, {hero.id} and {friend.id} made a plan that sounded bright and spry."
        f" {setting.sound}"
    )
    world.say(
        f"They wanted to {params.task} {LOADS[params.load].phrase}, a tiny squadron for the sky."
    )
    world.para()

    hero.meters["load"] += LOADS[params.load].weight
    friend.memes["worry"] += 1
    if LOADS[params.load].weight >= 2:
        hero.meters["strain"] += 1
        world.say(
            f"But {hero.id} tried to haul it alone, and soon {hero.pronoun()} needed a breath."
        )
        world.say(
            f"The boxes tipped and bent, and the brave little squadron looked wobbly and shy."
        )
    else:
        world.say(
            f"The load was small, yet the wind gave it a twist, so they still paused to think why."
        )

    world.para()
    if params.twist == "share":
        world.say(
            f"Then {friend.id} laughed, and {helper.phrase} made the answer plain and neat."
        )
        world.say(
            f"'{TWISTS[params.twist].phrase.capitalize()},' said {friend.id}; 'let's split the haul in two, and walk with steady feet.'"
        )
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        hero.meters["strain"] = max(0.0, hero.meters["strain"] - 1)
    elif params.twist == "repair":
        world.say(
            f"At the {helper.label}, they saw one bent wing and gave a careful grin."
        )
        world.say(
            f"They set the squadron down, mended the twist, and let the tiny planes begin again."
        )
        load.meters["repair"] += 1
        hero.memes["pride"] += 1
        friend.memes["pride"] += 1
    else:
        world.say(
            f"{helper.phrase.capitalize()} was the clue: they stopped, took a breath, and let the rush grow still."
        )
        world.say(
            f"That little pause changed the mood, and {hero.id} and {friend.id} chose the softer hill."
        )
        hero.meters["strain"] = max(0.0, hero.meters["strain"] - 0.5)
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1

    world.para()
    world.say(
        f"Together they lifted the squadron again, and {setting.ending}"
    )
    world.say(
        f"{hero.id} and {friend.id} shared the haul, shared the smile, and shared one steady breath."
    )
    world.say(
        f"In the end, their friendship held the day, and the twist turned worry into cheer, not death."
    )

    world.facts.update(
        setting=setting,
        load=LOADS[params.load],
        helper=HELPERS[params.helper],
        twist=TWISTS[params.twist],
        hero=hero,
        friend=friend,
        outcome="shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "haul", "squadron", and "breath".',
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} face a heavy haul, then a twist changes the plan.",
        f"Write a gentle rhyming tale about a little squadron, a shared haul, and one calming breath.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    twist = f["twist"]
    load = f["load"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {friend.id}, two friends who try to haul a tiny squadron together. Their friendship is what keeps the story warm and bright."
        ),
        QAItem(
            question="What problem did they have?",
            answer=f"They tried to haul {load.phrase} and it was too much for one child. The load made the squadron wobble, so they had to stop and think."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that they did not keep struggling the same way. Instead, they shared the haul, took a breath, and found a kinder plan."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does haul mean?", "To haul something means to pull or carry it with effort. It is what you do when a load feels heavy."),
        QAItem("What is a squadron?", "A squadron is a group of things working together, like a little team. In this story it means the tiny planes or gliders moving as one."),
        QAItem("Why take a breath?", "A breath can help you slow down and feel calmer. When you pause, it is easier to make a better choice."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hangar", task="haul", load="boxes", helper="rope", twist="share", hero="Mina", hero_gender="girl", friend="Pip", friend_gender="boy", load_weight=3, wind=1),
    StoryParams(setting="hill", task="haul", load="glider_cart", helper="trolley", twist="breath", hero="Toby", hero_gender="boy", friend="Zara", friend_gender="girl", load_weight=2, wind=2),
    StoryParams(setting="hangar", task="haul", load="single_bag", helper="bench", twist="repair", hero="Lena", hero_gender="girl", friend="Omar", friend_gender="boy", load_weight=1, wind=0),
]


ASP_RULES = r"""
load_heavy(L) :- load(L), weight(L, W), W >= 2.
needs_breath(H) :- hero(H), hauling(H), strain(H, S), S >= 1.
shared_plan(T) :- twist(T), twist_kind(T, share).
better_plan(T) :- twist(T), twist_kind(T, breath).
outcome(shared) :- shared_plan(_).
outcome(shared) :- better_plan(_).
outcome(shared) :- load_heavy(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("weight", lid, l.weight))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("twist_kind", tid, t.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("", "#show outcome/1."))
        if not model:
            raise RuntimeError("no ASP model")
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    try:
        generate(CURATED[0])
    except Exception as exc:
        print(f"generate smoke test failed: {exc}")
        return 1
    print("OK: ASP program loaded and generate() smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.load not in LOADS or params.helper not in HELPERS or params.twist not in TWISTS:
        raise StoryError("(Invalid parameters for this storyworld.)")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.load is None or c[1] == args.load)
              and (args.helper is None or c[2] == args.helper)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        if args.load and args.twist:
            raise StoryError(explain_rejection(LOADS[args.load], TWISTS[args.twist]))
        raise StoryError("(No valid combination matches the given options.)")
    setting, load, helper, twist = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != hero])
    return StoryParams(
        setting=setting, task="haul", load=load, helper=helper, twist=twist,
        hero=hero, hero_gender="girl" if hero in {"Mina", "Lena", "Iris"} else "boy",
        friend=friend, friend_gender="girl" if friend in {"Zara", "June", "Bea"} else "boy",
        load_weight=LOADS[load].weight, wind=rng.randint(0, 2),
    )


def valid_combos_asp() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show allowed/4."))
    return asp.atoms(model, "allowed")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world is small and deterministic; use --verify or --json for samples.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
