#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/switch_converse_whelm_teamwork_friendship_space_adventure.py
===========================================================================================

A standalone story world for a tiny Space Adventure tale about two friends,
a switch that changes the ship's course, a calm conversation that helps them
work together, and a moment when the looming problem almost whelms them.

The world is small on purpose:
- a ship with a failing system,
- a pair of child crewmates,
- a sensible helper action,
- a turn from panic to teamwork,
- and a bright ending image proving the problem changed.

The seed words are woven into the simulation:
- switch
- converse
- whelm
- teamwork
- friendship
- space adventure
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
WHELM_LIMIT = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
class Setting:
    id: str
    place: str
    backdrop: str
    problem: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    effect: str
    power: int
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    label: str
    danger: int
    cure: int
    whelm_gain: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "asteroid_post": Setting(
        "asteroid_post",
        "the asteroid post",
        "The tiny station floated beside a silver asteroid belt, with windows full of stars.",
        "A blinking panel kept the hallway dim and shaky.",
        "The station windows glowed steady again.",
        tags={"space", "station"},
    ),
    "moon_hub": Setting(
        "moon_hub",
        "the moon hub",
        "The moon hub sat under a bowl of dark sky, with tunnels that hummed like soft songs.",
        "A rusty hatch kept one room too warm and too loud.",
        "The tunnels hummed softly again.",
        tags={"space", "moon"},
    ),
    "comet_camp": Setting(
        "the comet camp",
        "The comet camp perched on bright ice, and the ship lights sparkled over the snow.",
        "A foggy console kept the landing bay uncertain.",
        "The camp lights shone clear and bright.",
        tags={"space", "comet"},
    ),
}

EVENTS = {
    "blink": Event("blink", "the blinking panel", danger=2, cure=1, whelm_gain=1, tags={"panel"}),
    "hatch": Event("hatch", "the rusty hatch", danger=2, cure=1, whelm_gain=1, tags={"hatch"}),
    "fog": Event("fog", "the foggy console", danger=3, cure=2, whelm_gain=2, tags={"console"}),
}

TOOLS = {
    "switch": Tool("switch", "the switch", "switch the backup system on", power=2, safe=True, tags={"switch"}),
    "converse": Tool("converse", "their calm conversation", "talk together and make a plan", power=2, safe=True, tags={"converse", "talk"}),
    "whelm": Tool("whelm", "the whelm meter", "let the problem feel huge", power=0, safe=False, tags={"whelm"}),
    "wrench": Tool("wrench", "the ship wrench", "tighten the loose piece", power=1, safe=True, tags={"tool"}),
    "lamp": Tool("lamp", "the signal lamp", "shine a guiding light", power=1, safe=True, tags={"light"}),
}

TEAM_TOKENS = ["teamwork", "friendship"]
CREW_NAMES = ["Mina", "Jules", "Tari", "Nova", "Rin", "Pia", "Lio", "Sora"]
PARENT_NAMES = ["Captain Ada", "Commander Sol"]


@dataclass
class StoryParams:
    setting: str
    event: str
    tool: str
    helper_tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    captain: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for eid in EVENTS:
            for tid in ("switch", "converse"):
                combos.append((sid, eid, tid))
    return combos


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in CREW_NAMES if n != avoid]
    return rng.choice(pool), gender


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world about teamwork and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--tool", choices=["switch", "converse"])
    ap.add_argument("--helper-tool", choices=["wrench", "lamp"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=PARENT_NAMES)
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
    if args.tool == "whelm":
        raise StoryError("The whelm word belongs in the story as a feeling, not as the main tool.")
    sid = args.setting or rng.choice(list(SETTINGS))
    eid = args.event or rng.choice(list(EVENTS))
    tool = args.tool or rng.choice(["switch", "converse"])
    helper = args.helper_tool or rng.choice(["wrench", "lamp"])
    hero = args.hero or _pick_name(rng)[0]
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend = args.friend or _pick_name(rng, avoid=hero)[0]
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    captain = args.captain or rng.choice(PARENT_NAMES)
    return StoryParams(sid, eid, tool, helper, hero, hero_gender, friend, friend_gender, captain)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("danger", eid, e.danger))
        lines.append(asp.fact("cure", eid, e.cure))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
        if t.safe:
            lines.append(asp.fact("safe", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, E, T) :- setting(S), event(E), tool(T), safe(T).
calm(T) :- tool(T), power(T, P), P >= 2.
solution(switch) :- tool(switch).
solution(converse) :- tool(converse).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP failed: {exc}")
        return 1
    py_set = set(valid_combos())
    if clingo_set != py_set:
        print("MISMATCH in valid combos:")
        print(" only in clingo:", sorted(clingo_set - py_set))
        print(" only in python:", sorted(py_set - clingo_set))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, event=None, tool=None, helper_tool=None,
            hero=None, hero_gender=None, friend=None, friend_gender=None,
            captain=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print(f"OK: ASP parity and smoke test passed ({len(clingo_set)} combos).")
    return 0


def stage_story(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    event = EVENTS[params.event]
    tool = TOOLS[params.tool]
    helper = TOOLS[params.helper_tool]

    hero = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(params.friend, kind="character", type=params.friend_gender, role="friend"))
    captain = world.add(Entity("captain", kind="character", type="adult", label=params.captain, role="captain"))

    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    hero.memes["teamwork"] = 0
    friend.memes["teamwork"] = 0

    world.say(
        f"{hero.id} and {friend.id} were on {setting.place}, where {setting.backdrop} "
        f"They were excited for a little space adventure together."
    )
    world.say(
        f"They loved to converse while they explored, because friendship made the ship feel warmer."
    )

    world.para()
    world.say(
        f"Then {setting.problem} {event.label} started to whelm them a little, and the hallway felt too big."
    )
    hero.memes["fear"] = 1
    friend.memes["fear"] = 1
    hero.meters["whelm"] = 1
    friend.meters["whelm"] = 1

    if params.tool == "switch":
        world.say(
            f"{hero.id} spotted a switch on the wall. {friend.id} pointed to the loose panel and said the backup system might help."
        )
        world.say(f"Their little teamwork plan was simple: {hero.id} would switch it while {friend.id} held the light.")
        hero.memes["courage"] = 1
        friend.memes["helping"] = 1
        hero.meters["action"] = 1
        world.get("captain").memes["trust"] = 1
        world.para()
        world.say(
            f"{hero.id} flipped the switch, and the backup hum came on like a sleepy song."
        )
        world.say(
            f"{helper.label.capitalize()} helped the last loose piece settle, and the problem shrank."
        )
        hero.meters["whelm"] = 0
        friend.meters["whelm"] = 0
        hero.memes["teamwork"] = 2
        friend.memes["teamwork"] = 2
        world.say(
            f"{event.ending} Soon the two friends were smiling again, proud of how they had helped each other."
        )
    else:
        world.say(
            f"{friend.id} told {hero.id} to converse for a second instead of rushing."
        )
        world.say(
            f"They took a breath, listened, and made a plan together. That calm conversation kept the worry from growing."
        )
        world.para()
        world.say(
            f"After that, {hero.id} used the {helper.label} to fix the small loose piece while {friend.id} checked the lights."
        )
        hero.meters["whelm"] = 0
        friend.meters["whelm"] = 0
        hero.memes["teamwork"] = 2
        friend.memes["teamwork"] = 2
        world.say(
            f"{setting.ending} The ship glowed steady, and their friendship felt even stronger than before."
        )

    world.facts.update(
        setting=setting,
        event=event,
        tool=tool,
        helper=helper,
        hero=hero,
        friend=friend,
        captain=captain,
        outcome="fixed",
    )


def generate_story_text(params: StoryParams) -> World:
    w = World()
    w.add(Entity("ship", kind="thing", type="ship", label="ship"))
    stage_story(w, params)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short space adventure story for a young child that includes the words switch, converse, and whelm.",
        f"Tell a story about two friends on {f['setting'].place} who use a {f['tool'].label} and a calm conversation to solve a ship problem.",
        f"Write a teamwork story where friendship helps two children turn a scary space problem into a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    setting: Setting = f["setting"]
    event: Event = f["event"]
    helper: Tool = f["helper"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {friend.id}, two friends on {setting.place}. They faced a small ship problem together and kept going as a team.",
        ),
        QAItem(
            question="What made the problem feel hard at first?",
            answer=f"{event.label} started to whelm them, so the hallway felt too big and the children felt a little scared. The worry was real, but it did not stay in charge for long.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} do to fix it?",
            answer=f"They talked with each other, chose teamwork, and used the {helper.label} or the switch to help the ship settle down. That is how the problem became safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork is when people help each other and do a job together. It works best when everyone listens and shares the work."),
        QAItem("What is friendship?", "Friendship is when people care about each other and enjoy being together. Friends can be brave for each other when something feels scary."),
        QAItem("What is a switch?", "A switch is something you flip or press to turn a machine on or off. On a ship, a switch can change how a system works."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams("asteroid_post", "blink", "switch", "wrench", "Mina", "girl", "Jules", "boy", "Captain Ada"),
    StoryParams("moon_hub", "hatch", "converse", "lamp", "Tari", "boy", "Nova", "girl", "Commander Sol"),
    StoryParams("comet_camp", "fog", "switch", "lamp", "Rin", "girl", "Pia", "girl", "Captain Ada"),
]


def resolve_story_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show calm/1.\n#show solution/1."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, e, t in combos:
            print(f"  {s:14} {e:8} {t}")
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
                params = resolve_story_choice(args, random.Random(seed))
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
