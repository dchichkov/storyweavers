#!/usr/bin/env python3
"""
storyworlds/worlds/repeat_curiosity_happy_ending_nursery_rhyme.py
=================================================================

A small story world in a nursery-rhyme style about a curious little one who
repeats a safe action, learns something, and ends happily.

Premise:
- A child or small animal is curious about a place or thing.
- They repeat a simple action: peek, tap, count, or ring a bell.
- The repeated curiosity leads to a gentle surprise, but not harm.

Turn:
- The curious one wants to repeat the action again and again.
- A caregiver or friend warns about one small risk or limitation.
- The curious one tries a safer repeat with help.

Resolution:
- The world changes in a visible way: the box is opened, the path is found,
  the bell is heard, or the hidden thing is discovered.
- The ending image proves the curiosity was welcomed, not punished.

This file follows the Storyweavers contract:
- self-contained stdlib script under storyworlds/worlds/
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py only inside ASP helpers
- includes StoryParams, registries, build_parser, resolve_params, generate,
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    openable: bool = False
    opened: bool = False
    repeatable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class CuriousAction:
    id: str
    verb: str
    repeat_verb: str
    noun: str
    sound: str
    risk: str
    safe_way: str
    reveal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    help_line: str
    tail: str
    covers: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden_gate": Setting(place="the garden gate", indoors=False, light="sunny", affords={"peek", "count", "listen"}),
    "toy_corner": Setting(place="the toy corner", indoors=True, light="soft", affords={"peek", "tap", "count"}),
    "barn_door": Setting(place="the barn door", indoors=False, light="golden", affords={"peek", "knock", "listen"}),
    "window": Setting(place="the little window", indoors=True, light="bright", affords={"peek", "tap", "listen"}),
}

ACTIONS = {
    "peek": CuriousAction(
        id="peek",
        verb="peek at the hidden thing",
        repeat_verb="peek again",
        noun="peek",
        sound="peek-a-boo",
        risk="might startle the shy thing",
        safe_way="peek very gently with a grown-up nearby",
        reveal="a soft surprise was waiting",
        keyword="peek",
        tags={"curiosity", "reveal"},
    ),
    "tap": CuriousAction(
        id="tap",
        verb="tap on the little door",
        repeat_verb="tap once more",
        noun="tap",
        sound="rap-rap",
        risk="might be too loud",
        safe_way="tap softly with one finger",
        reveal="the door sang a tiny song",
        keyword="tap",
        tags={"curiosity", "sound"},
    ),
    "count": CuriousAction(
        id="count",
        verb="count the bright buttons",
        repeat_verb="count them again",
        noun="count",
        sound="one-two-three",
        risk="might lose track",
        safe_way="count slowly and point carefully",
        reveal="the buttons lined up like stars",
        keyword="count",
        tags={"curiosity", "number"},
    ),
    "listen": CuriousAction(
        id="listen",
        verb="listen for the little hum",
        repeat_verb="listen once more",
        noun="listen",
        sound="hum-hum",
        risk="might miss the quiet sound",
        safe_way="cup an ear and stand still",
        reveal="the hum came from a happy hive",
        keyword="listen",
        tags={"curiosity", "sound"},
    ),
    "knock": CuriousAction(
        id="knock",
        verb="knock on the closed door",
        repeat_verb="knock again",
        noun="knock",
        sound="knock-knock",
        risk="might wake the sleepy cat",
        safe_way="knock softly and wait",
        reveal="the door opened to a smiling friend",
        keyword="knock",
        tags={"curiosity", "friend"},
    ),
}

TREASURES = {
    "box": Treasure(label="box", phrase="a small painted box", type="box", location="table", genders={"girl", "boy"}),
    "door": Treasure(label="door", phrase="a tiny blue door", type="door", location="wall"),
    "basket": Treasure(label="basket", phrase="a woven basket", type="basket", location="bench"),
    "bell": Treasure(label="bell", phrase="a shiny brass bell", type="bell", location="hook"),
}

AIDS = [
    Aid(
        id="lamp",
        label="a little lamp",
        help_line="held up a little lamp so the curious one could see",
        tail="stood by and smiled",
        covers={"dark"},
        fixes={"peek", "listen"},
    ),
    Aid(
        id="finger",
        label="one gentle finger",
        help_line="showed how to tap with one gentle finger",
        tail="helped with the soft tap",
        covers={"sound"},
        fixes={"tap"},
    ),
    Aid(
        id="string",
        label="a bit of string",
        help_line="tied a bit of string so the box could be opened slowly",
        tail="pulled the string with care",
        covers={"lock"},
        fixes={"peek", "count"},
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ruby", "Ella"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Max", "Noah", "Ben"]
TRAITS = ["curious", "tiny", "cheery", "brave", "bright"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    treasure: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            act = ACTIONS[action_id]
            for treasure_id, tr in TREASURES.items():
                if action_id == "peek" or action_id == "count" or action_id == "listen" or action_id == "tap" or action_id == "knock":
                    combos.append((place, action_id, treasure_id))
    return combos


def explain_rejection(action: CuriousAction, treasure: Treasure) -> str:
    return (
        f"(No story: {action.verb} and {treasure.phrase} do not make a gentle nursery-rhyme "
        f"curiosity tale together in a safe way.)"
    )


def explain_gender(treasure_id: str, gender: str) -> str:
    ok = " / ".join(sorted(TREASURES[treasure_id].genders))
    return f"(No story: try --gender {ok}; this treasure does not fit the requested choice.)"


def _do_action(world: World, hero: Entity, action: CuriousAction) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["delight"] = hero.memes.get("delight", 0) + 1
    world.say(f"{hero.id} went to {world.setting.place} and liked to {action.verb}.")


def _repeat_action(world: World, hero: Entity, action: CuriousAction) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["repeat"] = hero.memes.get("repeat", 0) + 1
    world.say(f"Then {hero.id} wanted to {action.repeat_verb}, just once more and more.")


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in [hero.type] if t), 'child')} "
        f"with a curious heart and a bright little hop."
    )


def loves_setting(world: World, hero: Entity, action: CuriousAction) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved the {world.setting.light} day, "
        f"the small sounds, and the chance to {action.verb}."
    )


def arrive(world: World, hero: Entity, helper: Entity, action: CuriousAction) -> None:
    world.say(
        f"One day, {hero.id} and {helper.label} came to {world.setting.place}, "
        f"where the air felt soft and sweet."
    )
    world.say(f"{hero.id} heard {action.sound} and smiled a smile so wide.")


def wants_repeat(world: World, hero: Entity, action: CuriousAction) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    world.say(
        f"{hero.id} wanted to {action.repeat_verb}, then {action.repeat_verb} again, "
        f"for curious children like to know what comes next."
    )


def warn(world: World, helper: Entity, hero: Entity, action: CuriousAction, treasure: Entity) -> None:
    world.facts["risk"] = action.risk
    world.say(
        f'"Softly now," said {helper.label}. "{action.risk}, and {treasure.label} may stay shy."'
    )


def safe_turn(world: World, helper: Entity, hero: Entity, action: CuriousAction) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"So {helper.label} showed {hero.id} a safer way: {action.safe_way}."
    )


def resolution(world: World, hero: Entity, helper: Entity, action: CuriousAction, treasure: Entity, aid: Optional[Aid]) -> None:
    world.say(
        f"{hero.id} tried the gentle way, and {action.reveal}."
    )
    if aid:
        world.say(
            f"{aid.help_line}. {helper.label} {aid.tail}, and the little {treasure.label} opened at last."
        )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"At the end, {hero.id} laughed in the bright light, and the curious day turned happy and sweet."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    action = ACTIONS[params.action]
    treasure = TREASURES[params.treasure]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper))
    tr = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        openable=True,
        repeatable=True,
        plural=treasure.plural,
    ))

    introduce(world, hero)
    loves_setting(world, hero, action)
    world.para()
    arrive(world, hero, helper, action)
    wants_repeat(world, hero, action)
    warn(world, helper, hero, action, tr)
    safe_turn(world, helper, hero, action)
    world.para()

    aid = None
    if action.id in {"peek", "count", "listen"}:
        aid = AIDS[0]
    elif action.id == "tap":
        aid = AIDS[1]
    elif action.id == "knock":
        aid = AIDS[2]

    resolution(world, hero, helper, action, tr, aid)
    world.facts.update(hero=hero, helper=helper, treasure=tr, action=action, aid=aid, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f'Write a short nursery-rhyme style story about {hero.id}, who is curious and likes to {action.verb}.',
        f"Tell a gentle story where a child keeps wanting to {action.repeat_verb} and finds a happy ending.",
        f'Write a simple story with the word "{action.keyword}" and a repeated curious action.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    action = f["action"]
    treasure = f["treasure"]
    return [
        QAItem(
            question=f"What did {hero.id} keep wanting to do?",
            answer=f"{hero.id} kept wanting to {action.repeat_verb}, because {hero.id} was very curious.",
        ),
        QAItem(
            question=f"Who helped {hero.id} choose a gentler way?",
            answer=f"{helper.label} helped {hero.id} choose a safer way to explore.",
        ),
        QAItem(
            question=f"What happy thing happened at the end?",
            answer=f"The {treasure.label} opened or revealed its surprise, and the day ended happily.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn, look, listen, and ask what something is like.",
        )
    ],
    "repeat": [
        QAItem(
            question="What does it mean to repeat something?",
            answer="To repeat something means to do it again one more time.",
        )
    ],
    "peek": [
        QAItem(
            question="What does it mean to peek?",
            answer="To peek means to look quickly and carefully, often from a small opening.",
        )
    ],
    "tap": [
        QAItem(
            question="What does a soft tap sound like?",
            answer="A soft tap sounds small and light, like tiny fingers touching a table.",
        )
    ],
    "listen": [
        QAItem(
            question="Why do people listen quietly sometimes?",
            answer="People listen quietly so they can hear small sounds that would be missed in loud noise.",
        )
    ],
    "count": [
        QAItem(
            question="Why do children count things?",
            answer="Children count things to learn how many there are and to notice details one by one.",
        )
    ],
    "knock": [
        QAItem(
            question="Why do people knock before entering?",
            answer="People knock to let others know they are there and to be polite.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    tags.add("curiosity")
    tags.add("repeat")
    out: list[QAItem] = []
    for tag in ["curiosity", "repeat", "peek", "tap", "listen", "count", "knock"]:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.openable:
            bits.append(f"opened={e.opened}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
curious(H) :- hero(H), meme(H,curiosity).
repeat_happens(H,A) :- curious(H), action(A), meme(H,repeat), repeats(A).
safe_story(P,A,T) :- setting(P), action(A), treasure(T), affords(P,A), safe(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("repeats", aid))
        if act.id in {"peek", "tap", "listen", "count", "knock"}:
            lines.append(asp.fact("safe", aid))
    for tid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if tr.plural:
            lines.append(asp.fact("treasure_plural", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    py = {(p, a, t) for p, a, t in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about curiosity and repeating safely.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mama", "papa", "grandma", "grandpa"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(sorted(SETTINGS[place].affords))
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.treasure and args.gender not in TREASURES[args.treasure].genders:
        raise StoryError(explain_gender(args.treasure, args.gender))
    if args.action and args.treasure:
        if action not in ACTIONS or treasure not in TREASURES:
            raise StoryError("(No valid combination.)")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mama", "papa", "grandma", "grandpa"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, treasure=treasure, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for treasure in TREASURES:
                combos.append((place, action, treasure))
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} safe story combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="toy_corner", action="peek", treasure="box", name="Mia", gender="girl", helper="mama", trait="curious"),
            StoryParams(place="window", action="tap", treasure="door", name="Leo", gender="boy", helper="grandma", trait="bright"),
            StoryParams(place="garden_gate", action="listen", treasure="bell", name="Nora", gender="girl", helper="papa", trait="cheery"),
            StoryParams(place="barn_door", action="knock", treasure="basket", name="Finn", gender="boy", helper="grandpa", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
