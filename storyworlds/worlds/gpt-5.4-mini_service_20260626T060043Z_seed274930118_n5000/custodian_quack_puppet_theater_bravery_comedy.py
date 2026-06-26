#!/usr/bin/env python3
"""
Storyworld: custodian, quack, bravery, comedy, puppet theater.

A small standalone simulation about a puppet theater show where a cautious
custodian, a squeaky quack, and a burst of bravery turn a backstage mishap
into a funny, happy performance.
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

THEATER_NAMES = [
    "the Little Lantern Theater",
    "the Ribbon Stage",
    "the Moonbeam Puppet Hall",
    "the Red Curtain Theater",
]

SHOW_NAMES = [
    "The Brave Duck Puppet",
    "The Quacking Crown",
    "The Tiny Hero's Day",
    "The Laughing Lantern",
]

PUPPET_TYPES = [
    "duck puppet",
    "fox puppet",
    "rabbit puppet",
    "bear puppet",
    "frog puppet",
]

HUMAN_NAMES = [
    "Maya",
    "Leo",
    "Nina",
    "Owen",
    "Sage",
    "Iris",
    "Ben",
    "Tia",
]

CUSTODIAN_TITLES = [
    "custodian",
    "stage custodian",
    "the custodian",
]

BRAVERY_LEVELS = ["small", "steady", "bright", "bold"]

COMEDY_BEATS = [
    "everyone laughed when the puppet bowed to the mop",
    "the squeaky quack made the curtain twitch like it had a joke of its own",
    "the duck puppet flapped in a very serious way that was somehow very funny",
    "the audience giggled when the tiny prop crown rolled under a chair",
]


@dataclass
class Item:
    id: str
    kind: str
    label: str
    phrase: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords_quack: bool = True
    affords_show: bool = True


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    noisy: bool = False
    breakable: bool = False
    stage_use: str = ""


@dataclass
class StoryParams:
    theater: str
    show: str
    puppet: str
    custodian_name: str
    performer_name: str
    bravery: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, item: Item) -> Item:
        self.entities[item.id] = item
        return item

    def get(self, eid: str) -> Item:
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def art_of_bravery(level: str) -> str:
    return {
        "small": "a small brave breath",
        "steady": "a steady brave nod",
        "bright": "a bright brave grin",
        "bold": "a bold brave step",
    }[level]


def quack_line() -> str:
    return random.choice([
        "quack!",
        "quack-quack!",
        "quaaack!",
    ])


def prop_catalog() -> dict[str, Prop]:
    return {
        "duck": Prop(
            id="duck",
            label="duck puppet",
            phrase="a cheerful duck puppet with a yellow beak",
            noisy=True,
            stage_use="make the audience laugh",
        ),
        "crown": Prop(
            id="crown",
            label="tiny prop crown",
            phrase="a tiny prop crown made of shiny cardboard",
            breakable=True,
            stage_use="sit on the hero puppet's head",
        ),
        "spotlight": Prop(
            id="spotlight",
            label="spotlight rope",
            phrase="a long rope for the stage spotlight",
            stage_use="raise the light at the right time",
        ),
        "mop": Prop(
            id="mop",
            label="mop",
            phrase="a big blue mop with a funny wobbly handle",
            stage_use="clean the floor",
        ),
    }


PROPS = prop_catalog()


def setting_catalog() -> dict[str, Setting]:
    return {
        "lantern": Setting(place="the Little Lantern Theater"),
        "ribbon": Setting(place="the Ribbon Stage"),
        "moonbeam": Setting(place="the Moonbeam Puppet Hall"),
        "redcurtain": Setting(place="the Red Curtain Theater"),
    }


SETTINGS = setting_catalog()


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theater_id, setting in SETTINGS.items():
        if not setting.affords_show:
            continue
        for show_id in SHOW_NAMES:
            for puppet in PUPPET_TYPES:
                combos.append((theater_id, show_id, puppet))
    return combos


def explain_rejection(theater: str, show: str, puppet: str) -> str:
    return (
        f"(No story: the requested show '{show}' with '{puppet}' does not fit "
        f"the puppet theater world in a grounded way.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld set in a puppet theater, with custodian, quack, and bravery."
    )
    ap.add_argument("--theater", choices=SETTINGS)
    ap.add_argument("--show", choices=SHOW_NAMES)
    ap.add_argument("--puppet", choices=PUPPET_TYPES)
    ap.add_argument("--custodian-name", choices=HUMAN_NAMES)
    ap.add_argument("--performer-name", choices=HUMAN_NAMES)
    ap.add_argument("--bravery", choices=BRAVERY_LEVELS)
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
    if args.theater is not None:
        combos = [c for c in combos if c[0] == args.theater]
    if args.show is not None:
        combos = [c for c in combos if c[1] == args.show]
    if args.puppet is not None:
        combos = [c for c in combos if c[2] == args.puppet]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theater, show, puppet = rng.choice(sorted(combos))
    custodian_name = args.custodian_name or rng.choice(HUMAN_NAMES)
    performer_name = args.performer_name or rng.choice([n for n in HUMAN_NAMES if n != custodian_name])
    bravery = args.bravery or rng.choice(BRAVERY_LEVELS)
    return StoryParams(
        theater=theater,
        show=show,
        puppet=puppet,
        custodian_name=custodian_name,
        performer_name=performer_name,
        bravery=bravery,
    )


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.theater])
    custodian = world.add(Item(
        id="custodian",
        kind="character",
        label="the custodian",
        phrase=f"the custodian named {params.custodian_name}",
        location="backstage",
        memes={"duty": 1.0, "care": 1.0},
    ))
    performer = world.add(Item(
        id="performer",
        kind="character",
        label="the performer",
        phrase=f"the performer named {params.performer_name}",
        location="stage",
        memes={"hope": 1.0},
    ))
    puppet = world.add(Item(
        id="puppet",
        kind="puppet",
        label=params.puppet,
        phrase=f"a {params.puppet}",
        location="basket",
        meters={"dust": 0.0},
        memes={"stage_fear": 0.0, "bravery": 0.0},
    ))
    duck = world.add(Item(
        id="duck_quack",
        kind="sound",
        label="quack",
        phrase="a loud quack from the duck puppet",
        location="table",
        meters={"noise": 0.0},
    ))
    crown = world.add(Item(
        id="crown",
        kind="prop",
        label="tiny prop crown",
        phrase=PROPS["crown"].phrase,
        owner="puppet",
        location="prop shelf",
        meters={"shine": 1.0},
    ))
    world.facts.update(
        custodian=custodian,
        performer=performer,
        puppet=puppet,
        duck=duck,
        crown=crown,
        bravery=params.bravery,
        show=params.show,
        theater=params.theater,
    )
    return world


def nudge_quack(world: World) -> None:
    duck = world.get("duck_quack")
    duck.meters["noise"] = duck.meters.get("noise", 0.0) + 1.0
    world.say(f"Backstage, the duck puppet made a {quack_line()}")


def stage_mess(world: World) -> None:
    puppet = world.get("puppet")
    puppet.meters["dust"] = puppet.meters.get("dust", 0.0) + 1.0
    world.say(
        f"The {puppet.label} tipped into a puff of stage dust, and the glitter "
        f"tried very hard to act innocent."
    )


def clean_fix(world: World) -> None:
    custodian = world.get("custodian")
    puppet = world.get("puppet")
    crown = world.get("crown")
    puppet.meters["dust"] = 0.0
    crown.location = "on the puppet"
    world.say(
        f"{custodian.phrase} brushed the dust away with a careful smile, and "
        f"put the tiny prop crown where it belonged."
    )


def bravery_turn(world: World, level: str) -> None:
    puppet = world.get("puppet")
    puppet.memes["bravery"] = puppet.memes.get("bravery", 0.0) + 1.0
    world.say(
        f"{art_of_bravery(level).capitalize()} helped the puppet stand tall, "
        f"even while the curtain seemed to be hiding a joke."
    )


def tell_story(world: World, params: StoryParams) -> None:
    custodian = world.get("custodian")
    performer = world.get("performer")
    puppet = world.get("puppet")
    show = params.show

    world.say(
        f"At {world.setting.place}, {custodian.phrase} was getting ready for "
        f"'{show}', because a puppet show only works when someone kind keeps the "
        f"little things in order."
    )
    world.say(
        f"{performer.phrase} wanted the {puppet.label} to shine, and the puppet "
        f"looked very proud to be part of the fun."
    )
    world.para()

    world.say(
        f"Just then, the stage box wobbled, the rope slipped, and a loud {quack_line()} "
        f"popped out like a surprise cookie."
    )
    stage_mess(world)
    world.say(
        f"The puppet froze for one tiny second, because bravery is often just "
        f"choosing not to run from the funny problem."
    )
    bravery_turn(world, params.bravery)
    world.para()

    clean_fix(world)
    world.say(
        f"{performer.phrase} clapped, and the puppet gave a grand bow that made "
        f"the audience laugh before the show even began."
    )
    world.say(
        f"Then {custodian.phrase} opened the curtain, the duck puppet said {quack_line()} "
        f"on purpose this time, and the whole theater giggled."
    )
    world.say(
        f"By the end, the brave little puppet was ready for the spotlight, the "
        f"crown sat straight, and the custodian was smiling at a job well done."
    )

    world.facts["resolved"] = True
    world.facts["comedy_line"] = random.choice(COMEDY_BEATS)
    world.facts["quack_used"] = True


def generate_story_text(params: StoryParams) -> World:
    world = setup_world(params)
    tell_story(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for young children set in {world.setting.place} that includes the word "quack".',
        f"Tell a puppet-theater story where a custodian helps after a funny backstage mishap and bravery matters.",
        f"Write a simple story about a puppet show, a quack, and a brave fix that ends with everyone laughing.",
        f"Create a child-friendly comedy about {f['custodian'].phrase}, {f['performer'].phrase}, and a puppet getting ready for '{f['show']}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    custodian = f["custodian"]
    performer = f["performer"]
    puppet = f["puppet"]
    bravery = f["bravery"]
    show = f["show"]
    qa = [
        QAItem(
            question="Where did the story happen?",
            answer=f"The story happened at {world.setting.place}, a puppet theater where a show was being prepared.",
        ),
        QAItem(
            question="Who kept the stage in order?",
            answer=f"{custodian.phrase} kept the stage in order and helped after the funny backstage problem.",
        ),
        QAItem(
            question="What funny sound came from backstage?",
            answer="A loud quack came from backstage, and it made the whole moment feel silly and surprising.",
        ),
        QAItem(
            question="What made the puppet brave?",
            answer=f"The puppet used {bravery} bravery, which helped it stand tall instead of hiding from the problem.",
        ),
        QAItem(
            question="What was the show called?",
            answer=f"The show was called '{show}'.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"The custodian cleaned the mess, the puppet wore the crown again, "
                f"and everyone laughed as the show got ready to begin."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a custodian do?",
            answer="A custodian helps keep a place clean, safe, and ready for people to use.",
        ),
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a place where puppets are shown in a play for an audience.",
        ),
        QAItem(
            question="Why can quacking be funny in a story?",
            answer="Quacking can be funny because it sounds bright and silly, especially when a puppet makes the sound at a surprising time.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing to do something even when you feel nervous or worried.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.location:
            parts.append(f"location={e.location}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}): " + ", ".join(parts))
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theater="lantern",
        show="The Brave Duck Puppet",
        puppet="duck puppet",
        custodian_name="Maya",
        performer_name="Leo",
        bravery="bright",
    ),
    StoryParams(
        theater="moonbeam",
        show="The Quacking Crown",
        puppet="frog puppet",
        custodian_name="Nina",
        performer_name="Owen",
        bravery="bold",
    ),
    StoryParams(
        theater="redcurtain",
        show="The Tiny Hero's Day",
        puppet="bear puppet",
        custodian_name="Tia",
        performer_name="Ben",
        bravery="steady",
    ),
]


ASP_RULES = r"""
show(Show) :- show_name(Show).
puppet(P) :- puppet_name(P).
custodian_ok.
brave(Level) :- bravery(Level).
comedy_story(Theater, Show, Puppet) :- theater(Theater), show_name(Show), puppet_name(Puppet), custodian_ok, brave(_).
#show comedy_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, setting in SETTINGS.items():
        lines.append(asp.fact("theater", tid))
        if setting.affords_show:
            lines.append(asp.fact("affords_show", tid))
    for show in SHOW_NAMES:
        lines.append(asp.fact("show_name", show))
    for puppet in PUPPET_TYPES:
        lines.append(asp.fact("puppet_name", puppet))
    for level in BRAVERY_LEVELS:
        lines.append(asp.fact("bravery", level))
    lines.append(asp.fact("custodian_ok"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show comedy_story/3."))
    return sorted(set(asp.atoms(model, "comedy_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in python:", sorted(python_set - clingo_set))
    print("only in clingo:", sorted(clingo_set - python_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = generate_story_text(params)
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
        print(asp_program("#show comedy_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        triples = asp_valid_combos()
        print(f"{len(triples)} compatible comedy story combinations:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.custodian_name} at {p.theater} / {p.show}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
