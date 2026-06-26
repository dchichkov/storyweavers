#!/usr/bin/env python3
"""
A tall-tale story world about a mighty ginger root, a muddled misunderstanding,
and a sharing-based revolt that turns grumbles into a feast.

Seed tale idea:
A small farm store receives one enormous ginger root. The village mistakes it for
a treasure or a trick, the ginger sparks a noisy revolt, and the only thing big
enough to settle everybody is sharing the spicy prize.
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
    kind: str = "thing"  # character | thing | place
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "place":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    setting: str
    ginger_kind: str
    crowd: str
    leader: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    weather: str
    style_note: str


@dataclass
class Ginger:
    id: str
    label: str
    phrase: str
    smell: str
    size: str
    spark: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crowd:
    id: str
    label: str
    kind: str
    first_misunderstanding: str
    revolt_reason: str
    sharing_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Leader:
    id: str
    label: str
    kind: str
    voice: str
    shared_action: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
    "market": Setting(place="the village market", weather="windy", style_note="The stalls leaned like tired horses."),
    "barn": Setting(place="the red barn", weather="sunny", style_note="The rafters rang like old fiddle strings."),
    "kitchen": Setting(place="the cookhouse", weather="rainy", style_note="The roof drummed like a marching band."),
}

GINGERS = {
    "root": Ginger(
        id="root",
        label="ginger root",
        phrase="a ginger root as long as a canoe",
        smell="spicy",
        size="giant",
        spark="Its smell curled through the air like a campfire ribbon.",
        tags={"ginger"},
    ),
    "cookie": Ginger(
        id="cookie",
        label="ginger cookie",
        phrase="a ginger cookie as wide as a wagon wheel",
        smell="sweet-spicy",
        size="huge",
        spark="It smelled like a holiday parade.",
        tags={"ginger"},
    ),
    "tea": Ginger(
        id="tea",
        label="ginger tea",
        phrase="a steaming pot of ginger tea",
        smell="warm",
        size="large",
        spark="The steam made little halos over every head.",
        tags={"ginger"},
    ),
}

CROWDS = {
    "farmers": Crowd(
        id="farmers",
        label="the farmers",
        kind="folk",
        first_misunderstanding="a dragon tooth",
        revolt_reason="they thought the giant ginger was being kept from them",
        sharing_need="everyone wanted a fair taste",
        tags={"misunderstanding", "sharing", "revolt"},
    ),
    "children": Crowd(
        id="children",
        label="the children",
        kind="kids",
        first_misunderstanding="a buried gold bar",
        revolt_reason="they thought the ginger belonged to one greedy grown-up",
        sharing_need="every child wanted a tiny piece",
        tags={"misunderstanding", "sharing", "revolt"},
    ),
    "neighbors": Crowd(
        id="neighbors",
        label="the neighbors",
        kind="folks",
        first_misunderstanding="a prank from a giant",
        revolt_reason="they thought the smell meant somebody was hiding supper",
        sharing_need="each neighbor wanted to share the smell and the spice",
        tags={"misunderstanding", "sharing", "revolt"},
    ),
}

LEADERS = {
    "bess": Leader(
        id="bess",
        label="Bess",
        kind="woman",
        voice="plain as a plow handle",
        shared_action="handed out slices with a laugh",
        tags={"sharing"},
    ),
    "hank": Leader(
        id="hank",
        label="Hank",
        kind="man",
        voice="big as a church bell",
        shared_action="cut the ginger into honest pieces",
        tags={"sharing"},
    ),
    "mira": Leader(
        id="mira",
        label="Mira",
        kind="woman",
        voice="sweet as syrup on a biscuit",
        shared_action="poured ginger tea for everyone",
        tags={"sharing"},
    ),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable if the setting exists, the ginger is giant or large, and
% the crowd has both a misunderstanding and a sharing-based revolt.
story_ok(S, G, C, L) :- setting(S), ginger(G), crowd(C), leader(L),
                        giant_like(G), confused_about(C), shares_needed(C), can_settle(L).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for gid, g in GINGERS.items():
        lines.append(asp.fact("ginger", gid))
        if g.size in {"giant", "huge"}:
            lines.append(asp.fact("giant_like", gid))
        for tag in sorted(g.tags):
            lines.append(asp.fact("tagged", gid, tag))
    for cid, c in CROWDS.items():
        lines.append(asp.fact("crowd", cid))
        lines.append(asp.fact("confused_about", cid))
        lines.append(asp.fact("shares_needed", cid))
        lines.append(asp.fact("revolt_kind", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("tagged", cid, tag))
    for lid, l in LEADERS.items():
        lines.append(asp.fact("leader", lid))
        lines.append(asp.fact("can_settle", lid))
        for tag in sorted(l.tags):
            lines.append(asp.fact("tagged", lid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show story_ok/4."))
    clingo_set = set(asp.atoms(model, "story_ok"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GINGERS:
            for c in CROWDS:
                for l in LEADERS:
                    if reasonableness(s, g, c, l):
                        combos.append((s, g, c, l))
    return combos


def reasonableness(setting: str, ginger_kind: str, crowd: str, leader: str) -> bool:
    g = GINGERS[ginger_kind]
    c = CROWDS[crowd]
    l = LEADERS[leader]
    return bool(g.size in {"giant", "huge"} and {"misunderstanding", "sharing", "revolt"} <= c.tags and "sharing" in l.tags)


def explain_rejection(setting: str, ginger_kind: str, crowd: str, leader: str) -> str:
    return (
        f"(No story: {GINGERS[ginger_kind].label} in {SETTINGS[setting].place} "
        f"would not plausibly lead to {CROWDS[crowd].label} and {LEADERS[leader].label} "
        f"having a tall-tale misunderstanding and sharing revolt.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    ginger = GINGERS[params.ginger_kind]
    crowd = CROWDS[params.crowd]
    leader = LEADERS[params.leader]

    world.add(Entity(id="ginger", kind="thing", label=ginger.label, phrase=ginger.phrase, type="food"))
    world.add(Entity(id="crowd", kind="character", label=crowd.label, type=crowd.kind))
    world.add(Entity(id="leader", kind="character", label=leader.label, type=leader.kind))

    world.facts.update(setting=params.setting, ginger=params.ginger_kind, crowd=params.crowd, leader=params.leader)
    world.facts.update(ginger=ginger, crowd_cfg=crowd, leader_cfg=leader)
    return world


def tell(world: World) -> None:
    ginger: Ginger = world.facts["ginger"]  # type: ignore[assignment]
    crowd: Crowd = world.facts["crowd_cfg"]  # type: ignore[assignment]
    leader: Leader = world.facts["leader_cfg"]  # type: ignore[assignment]
    place = world.setting.place

    world.say(
        f"In {place}, there stood {ginger.phrase}. {ginger.spark} "
        f"The whole place smelled {ginger.smell}, and that smell traveled farther than a whistle on a windy hill."
    )
    world.say(
        f"The first to see it were {crowd.label}. They made a wild mistake and called it {crowd.first_misunderstanding}, "
        f"because tall tales have a way of making ordinary things seem twice as strange."
    )

    world.para()
    world.say(
        f"Soon the misunderstanding grew teeth. {crowd.label.capitalize()} began a great little revolt, "
        f"not with fire or swords, but with boots, voices, and very stern eyebrows. "
        f"They shouted that {crowd.revolt_reason}."
    )
    world.say(
        f"That is when {leader.label} stepped forward, {leader.voice}, and said the only sensible thing in ten miles: "
        f'"Hold your hats. That ginger is not a stolen star. It is supper, and supper can be shared."'
    )

    world.para()
    world.say(
        f"So {leader.label} led the sharing. {leader.shared_action}. "
        f"{crowd.sharing_need}, and every hand got a fair bit."
    )
    world.say(
        f"After the first bite, the revolt turned into laughter. The big bad guess shrank smaller and smaller, "
        f"until all that was left was warm breath, sticky fingers, and a happy little pile of ginger peels."
    )


def generation_prompts(world: World) -> list[str]:
    ginger: Ginger = world.facts["ginger"]  # type: ignore[assignment]
    crowd: Crowd = world.facts["crowd_cfg"]  # type: ignore[assignment]
    leader: Leader = world.facts["leader_cfg"]  # type: ignore[assignment]
    setting = world.setting.place
    return [
        f'Write a tall tale about {ginger.phrase} in {setting} that causes a misunderstanding and a sharing-based revolt.',
        f"Tell a child-friendly tall tale where {crowd.label} mistake {ginger.label} for something else, then calm down when {leader.label} shares it.",
        f"Write a funny story with the words 'ginger' and 'revolt' where a big misunderstanding ends in sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ginger: Ginger = world.facts["ginger"]  # type: ignore[assignment]
    crowd: Crowd = world.facts["crowd_cfg"]  # type: ignore[assignment]
    leader: Leader = world.facts["leader_cfg"]  # type: ignore[assignment]
    place = world.setting.place

    return [
        QAItem(
            question=f"What was the big ginger thing in {place}?",
            answer=f"It was {ginger.phrase}, smelling {ginger.smell} and looking mighty enough to fool a whole crowd.",
        ),
        QAItem(
            question=f"Why did {crowd.label} start their revolt?",
            answer=f"They started it because of a misunderstanding. They thought the ginger was {crowd.first_misunderstanding}, and they believed it was being kept from them.",
        ),
        QAItem(
            question=f"How did {leader.label} end the trouble?",
            answer=f"{leader.label} ended it by sharing. {leader.shared_action}, and that turned the angry noise into a feast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ginger?",
            answer="Ginger is a spicy root. People use it in cooking, and it can smell warm and sharp.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people get the wrong idea about something and react before they know the truth.",
        ),
        QAItem(
            question="Why can sharing calm people down?",
            answer="Sharing can calm people down because it helps everyone feel included and treated fairly.",
        ),
        QAItem(
            question="What is a revolt?",
            answer="A revolt is when a group of people pushes back loudly because they think something is unfair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind}, label={e.label}, meters={e.meters}, memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale world about ginger, misunderstanding, sharing, and revolt.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--ginger", dest="ginger_kind", choices=GINGERS.keys())
    ap.add_argument("--crowd", choices=CROWDS.keys())
    ap.add_argument("--leader", choices=LEADERS.keys())
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.ginger_kind and args.crowd and args.leader:
        if not reasonableness(args.setting, args.ginger_kind, args.crowd, args.leader):
            raise StoryError(explain_rejection(args.setting, args.ginger_kind, args.crowd, args.leader))
    choices = [c for c in valid_combos()
               if (args.setting is None or c[0] == args.setting)
               and (args.ginger_kind is None or c[1] == args.ginger_kind)
               and (args.crowd is None or c[2] == args.crowd)
               and (args.leader is None or c[3] == args.leader)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ginger_kind, crowd, leader = rng.choice(sorted(choices))
    return StoryParams(setting=setting, ginger_kind=ginger_kind, crowd=crowd, leader=leader)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GINGERS:
            for c in CROWDS:
                for l in LEADERS:
                    if reasonableness(s, g, c, l):
                        combos.append((s, g, c, l))
    return combos


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show story_ok/4."))
    return sorted(set(asp.atoms(model, "story_ok")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="market", ginger_kind="root", crowd="farmers", leader="bess"),
            StoryParams(setting="barn", ginger_kind="cookie", crowd="children", leader="hank"),
            StoryParams(setting="kitchen", ginger_kind="tea", crowd="neighbors", leader="mira"),
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
