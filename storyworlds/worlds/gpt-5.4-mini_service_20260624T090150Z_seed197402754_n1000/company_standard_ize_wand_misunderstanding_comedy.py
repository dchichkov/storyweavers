#!/usr/bin/env python3
"""
A small comedy storyworld about a company trying to standard-ize wands,
with a misunderstanding that turns into a harmless, funny fix.

The premise:
- A busy company wants every wand to match a standard size and shape.
- The hero thinks "standard-ize" means the wand must be made of "standard"
  office supplies, while the manager means "make all wands consistent."
- The misunderstanding causes a silly test-room mix-up.
- The resolution is a simple chart and a labeled drawer that makes the
  standard clear, so the work can continue and the day ends in laughter.

This script follows the Storyweavers contract:
- stdlib-only, standalone
- imports results eagerly
- imports asp lazily in ASP helpers
- exposes StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the company workshop"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = _meter(ent, key) + amt


def _inc_mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = _mem(ent, key) + amt


def _say_company(world: World, hero: Entity, boss: Entity) -> None:
    world.say(
        f"{hero.id} worked at {world.setting.place}, where {boss.label} ran the "
        f"small company with a very serious clipboard."
    )
    world.say(
        f"{hero.id} liked the busy shelves, the bright labels, and the funny little "
        f"wand rack by the window."
    )


def _say_motivation(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    _inc_mem(hero, "curiosity")
    world.say(
        f"{hero.id} loved to {activity.verb}, because {activity.gerund} made the "
        f"workroom feel like a game."
    )
    world.say(
        f"Today the company wanted to standard-ize the wands so every {prize.label} "
        f"looked neat and matched the same size."
    )


def _say_misunderstanding(world: World, hero: Entity, manager: Entity, activity: Activity) -> None:
    _inc_mem(hero, "confusion")
    _inc_mem(manager, "impatience")
    world.say(
        f"{hero.id} heard \"standard-ize\" and thought it meant, \"put the word "
        f"standard on the wand.\""
    )
    world.say(
        f"So {hero.id} rushed to {activity.rush}, proud of the idea, while "
        f"{manager.id} looked up from the chart and blinked twice."
    )


def _say_broken_plan(world: World, hero: Entity, prize: Entity) -> None:
    _inc_meter(hero, "messy")
    _inc_mem(hero, "embarrassment")
    world.say(
        f"The result was silly: {hero.id} tried to tape a shiny label onto "
        f"{hero.pronoun('possessive')} {prize.label}, and the label curled like a "
        f"tiny snail."
    )
    world.say(
        f"The other workers giggled, because that was not the kind of standard-izing "
        f"the boss had meant."
    )


def _say_fix(world: World, hero: Entity, manager: Entity, prize: Entity, tool: Tool) -> None:
    _inc_mem(hero, "relief", 1.0)
    _inc_mem(manager, "amusement", 1.0)
    world.say(
        f"Then {manager.id} smiled and said, \"Oh! I mean the wands should match each "
        f"other, not wear the word standard.\""
    )
    world.say(
        f"{manager.id} brought out a ruler, a stamp pad, and {tool.label}. "
        f"Together they made one clear example and one neat shelf."
    )
    world.say(
        f"{tool.tail.capitalize()}, and soon the company had a real standard for every "
        f"{prize.label} in the room."
    )


def _say_ending(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} laughed, because the whole mix-up had been caused by one tiny "
        f"word and one very literal guess."
    )
    world.say(
        f"At the end of the day, the {prize.label} all lined up in a tidy row, and "
        f"the company sounded happy as a bell."
    )


def _run_rules(world: World) -> None:
    # No deep forward engine is needed for this small comedy domain, but we keep
    # a tiny deterministic check for a "resolved" state.
    hero = world.get("Hero")
    if _mem(hero, "relief") >= THRESHOLD:
        world.facts["resolved"] = True


SETTINGS = {
    "workshop": Setting(place="the company workshop", affords={"labeling", "sorting"}),
    "mailroom": Setting(place="the mailroom", affords={"labeling", "sorting"}),
    "office": Setting(place="the office corner", affords={"labeling", "sorting"}),
}

ACTIVITIES = {
    "labeling": Activity(
        id="labeling",
        verb="label the wand boxes",
        gerund="labeling boxes",
        rush="dash to the label maker",
        mess="ink",
        zone={"hands"},
        keyword="standard",
        tags={"company", "wand", "standard"},
    ),
    "sorting": Activity(
        id="sorting",
        verb="sort the wand drawer",
        gerund="sorting drawers",
        rush="shuffle the trays",
        mess="paper",
        zone={"hands"},
        keyword="wand",
        tags={"company", "wand"},
    ),
}

PRIZES = {
    "wand": Prize(
        label="wand",
        phrase="a neat little wand",
        type="wand",
        region="hands",
    ),
    "wands": Prize(
        label="wands",
        phrase="a box of wands",
        type="wands",
        region="hands",
        plural=True,
    ),
}

TOOLS = {
    "chart": Tool(
        id="chart",
        label="a clear chart",
        prep="draw a clean chart",
        tail="the chart showed the same size, the same shape, and the same shelf name",
    ),
    "drawer": Tool(
        id="drawer",
        label="a labeled drawer",
        prep="label the drawer",
        tail="the drawer kept all the wands in one easy row",
    ),
}

NAMES = {
    "worker": ["Mina", "Toby", "Ada", "Pip", "Luca", "Nia", "Eli", "June"],
    "manager": ["Ms. Reed", "Mr. Bell"],
}

TRAITS = ["careful", "curious", "cheerful", "silly", "busy"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    tool: str
    worker_name: str
    manager_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                for t in TOOLS:
                    combos.append((s, a, p, t))
    return combos


def explain_rejection() -> str:
    return "(No story: this tiny comedy world only works with a company, a wand, and a clear misunderstanding that can be fixed politely.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: a company standard-izes wands after a misunderstanding."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--manager")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    filt = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not filt:
        raise StoryError(explain_rejection())
    setting, activity, prize, tool = rng.choice(sorted(filt))
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        tool=tool,
        worker_name=args.name or rng.choice(NAMES["worker"]),
        manager_name=args.manager or rng.choice(NAMES["manager"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(setting: Setting, activity: Activity, prize: Prize, tool: Tool,
         worker_name: str, manager_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type="person", label=worker_name))
    manager = world.add(Entity(id="Manager", kind="character", type="person", label=manager_name))
    wand = world.add(Entity(id="Wand", type=prize.type, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    world.facts.update(hero=hero, manager=manager, wand=wand, activity=activity, prize=prize, tool=tool, trait=trait)

    _say_company(world, hero, manager)
    _say_motivation(world, hero, activity, wand)

    world.para()
    world.say(f"{hero.id} was a {trait} worker who wanted to help the company look neat and official.")
    world.say(f"But \"standard-ize\" sounded funny in {hero.id}'s head.")

    world.para()
    _say_misunderstanding(world, hero, manager, activity)
    _say_broken_plan(world, hero, wand)

    world.para()
    _say_fix(world, hero, manager, wand, tool)
    _say_ending(world, hero, wand)
    _run_rules(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for young children about a company that wants to standard-ize a wand.',
        f"Tell a funny story where {f['hero'].label} misunderstands the word 'standard-ize' while helping at {world.setting.place}.",
        f"Write a gentle workplace story about a wand, a misunderstanding, and a clear fix that makes everyone laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, manager = f["hero"], f["manager"]
    wand, activity, tool = f["wand"], f["activity"], f["tool"]
    return [
        QAItem(
            question="What did the company want to do to the wands?",
            answer="The company wanted to standard-ize the wands so they would all look neat and match the same size.",
        ),
        QAItem(
            question=f"Why did {hero.label} get confused?",
            answer=f"{hero.label} got confused because the word standard-ize sounded like it might mean putting the word standard onto the wand.",
        ),
        QAItem(
            question=f"How did {manager.label} fix the misunderstanding?",
            answer=f"{manager.label} explained that the wands should match each other, then used {tool.label} to make the rule clear.",
        ),
        QAItem(
            question=f"What silly thing did {hero.label} try first?",
            answer=f"{hero.label} tried to label the wand instead of standard-izing the whole set of wands.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The story ended with the wands lined up neatly, the misunderstanding cleared up, and everyone laughing together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a company?",
            answer="A company is a group of people who work together to make, sell, or do something useful.",
        ),
        QAItem(
            question="What is a wand?",
            answer="A wand is a thin stick or tool that someone can wave, often in stories about magic.",
        ),
        QAItem(
            question="What does it mean to standardize something?",
            answer="To standardize something means to make it follow the same rule, size, shape, or pattern as the others.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing and acts on it by mistake.",
        ),
        QAItem(
            question="Why can comedy feel funny?",
            answer="Comedy feels funny when an honest mistake, a mix-up, or a silly idea turns into a harmless surprise.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("workshop", "labeling", "wand", "chart", "Mina", "Ms. Reed", "curious"),
    StoryParams("office", "sorting", "wands", "drawer", "Toby", "Mr. Bell", "silly"),
    StoryParams("mailroom", "labeling", "wand", "drawer", "Ada", "Ms. Reed", "cheerful"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
activity(A) :- activity_fact(A).
prize(P) :- prize_fact(P).
tool(T) :- tool_fact(T).

match(S,A,P,T) :- setting(S), activity(A), prize(P), tool(T).
valid_story(S,A,P,T) :- match(S,A,P,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity_fact", a))
    for p in PRIZES:
        lines.append(asp.fact("prize_fact", p))
    for t in TOOLS:
        lines.append(asp.fact("tool_fact", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        TOOLS[params.tool],
        params.worker_name,
        params.manager_name,
        params.trait,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combos:\n")
        for s in stories:
            print("  ", s)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.worker_name}: {p.activity} at {p.setting} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
