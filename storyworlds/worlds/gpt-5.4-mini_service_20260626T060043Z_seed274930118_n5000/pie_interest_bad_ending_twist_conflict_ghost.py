#!/usr/bin/env python3
"""
Standalone storyworld: a child, a pie, a ghostly interest, and a spooky twist
that can end in a bad ending unless someone makes a careful choice.

This world stays small and classical:
- one haunted room
- one child
- one ghost
- one pie
- one interest meter that grows when the ghost is curious about the pie
- one conflict meter that grows when the child is frightened
- one twist that changes what the pie really means
- one bad ending that is possible, but only when the pie is lost to the ghost's claim
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
    eaten: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("interest", "fear", "conflict", "hope", "loss", "mystery"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old kitchen"
    mood: str = "moonlit"
    affability: str = "quiet"


@dataclass
class Pie:
    flavor: str
    phrase: str
    label: str = "pie"
    precious: bool = True
    cursed: bool = False


@dataclass
class StoryParams:
    place: str
    pie: str
    child_name: str
    child_type: str
    ghost_name: str
    twist: str
    ending: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


def _story_style(setting: Setting) -> str:
    return f"{setting.mood.capitalize()} air hung over {setting.place}, and everything sounded a little hushed."


def _ghost_interest(world: World, ghost: Entity, pie: Entity) -> None:
    ghost.meters["interest"] += 1
    ghost.memes["mystery"] += 1
    world.say(f"{ghost.id} drifted closer, full of interest in the {pie.label}.")


def _child_notice(world: World, child: Entity, ghost: Entity, pie: Entity) -> None:
    child.meters["fear"] += 1
    child.memes["conflict"] += 1
    world.say(
        f"{child.id} saw the pale shape near the {pie.label} and felt a cold knot of fear."
    )


def _twist(world: World, child: Entity, ghost: Entity, pie: Entity, twist: str) -> None:
    if twist == "memory":
        world.say(
            f"Then came the twist: the {pie.label} was not just dessert. It had been made for a promise."
        )
        world.say(
            f"The promise belonged to {ghost.id}, who had been waiting for one last shared bite."
        )
    elif twist == "kindness":
        world.say(
            f"Then came the twist: {ghost.id} did not want to steal the {pie.label} at all."
        )
        world.say(
            f"{ghost.id} only wanted someone to listen, because the room felt lonely without a voice."
        )
    elif twist == "warning":
        world.say(
            f"Then came the twist: the {pie.label} carried a warning inside its sweet smell."
        )
        world.say(
            f"{ghost.id} had stayed to keep the child from eating it too fast."
        )
    else:
        world.say("Then came the twist, and the room seemed even stranger than before.")


def _resolve_bad_ending(world: World, child: Entity, ghost: Entity, pie: Entity) -> None:
    pie.eaten = True
    child.meters["loss"] += 1
    child.memes["hope"] = 0
    world.say(
        f"In the end, the {pie.label} vanished into the dark, and {child.id} was left alone with the cold room."
    )
    world.say(
        f"{ghost.id} faded away with the last crumb of warmth, and that was the bad ending."
    )


def _resolve_better_end(world: World, child: Entity, ghost: Entity, pie: Entity) -> None:
    child.memes["hope"] += 1
    child.meters["conflict"] = 0
    world.say(
        f"{child.id} took a careful breath and offered the first slice of the {pie.label} instead of running."
    )
    world.say(
        f"{ghost.id} softened, the cold drift in the air eased, and the room felt less empty."
    )
    world.say(
        f"By the last bite, the pie was gone, but the fear was gone too, and that was a small brave ending."
    )


def tell(setting: Setting, pie_cfg: Pie, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost", label=params.ghost_name))
    pie = world.add(Entity(id="pie", kind="thing", type="pie", label="pie", phrase=pie_cfg.phrase))

    world.say(_story_style(setting))
    world.say(
        f"{child.id} loved the smell of {pie_cfg.phrase}, and {child.pronoun('subject')} kept a careful eye on the {pie.label}."
    )
    world.say(
        f"Tonight, {child.id} set the {pie.label} on the table and tried not to stare."
    )
    world.para()

    _ghost_interest(world, ghost, pie)
    _child_notice(world, child, ghost, pie)
    world.say(
        f"{child.id} whispered, \"Who's there?\" and the shadows did not answer right away."
    )
    _twist(world, child, ghost, pie, params.twist)
    world.para()

    if params.ending == "bad":
        _resolve_bad_ending(world, child, ghost, pie)
    else:
        _resolve_better_end(world, child, ghost, pie)

    world.facts.update(
        child=child,
        ghost=ghost,
        pie=pie,
        setting=setting,
        pie_cfg=pie_cfg,
        twist=params.twist,
        ending=params.ending,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the old kitchen", mood="moonlit", affability="quiet"),
    "attic": Setting(place="the attic", mood="dusty", affability="echoing"),
    "cellar": Setting(place="the cellar", mood="cold", affability="still"),
}

PIES = {
    "apple": Pie(flavor="apple", phrase="a warm apple pie"),
    "berry": Pie(flavor="berry", phrase="a sweet berry pie"),
    "pumpkin": Pie(flavor="pumpkin", phrase="a round pumpkin pie"),
}

CHILD_NAMES = ["Mina", "Theo", "June", "Eli", "Ivy", "Nora"]
GHOST_NAMES = ["Whisper", "Pale Tom", "Murmur", "Mrs. Gray", "Boo", "Lantern"]
TWISTS = ["memory", "kindness", "warning"]
ENDINGS = ["bad", "good"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for pie in PIES:
            for twist in TWISTS:
                combos.append((place, pie, twist))
    return combos


@dataclass
class QAConfig:
    question: str
    answer: str


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about a {f["pie_cfg"].flavor} pie and a spooky surprise.',
        f"Tell a gentle but eerie story where {f['child'].id} finds a {f['pie_cfg'].phrase} in {f['setting'].place}.",
        f"Write a story with a twist in which a ghost's interest in a pie changes the meaning of the night.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    pie: Entity = f["pie"]
    setting: Setting = f["setting"]
    twist: str = f["twist"]
    ending: str = f["ending"]

    qa = [
        QAItem(
            question=f"Who found the pie in {setting.place}?",
            answer=f"{child.id} found the {pie.label} in {setting.place}.",
        ),
        QAItem(
            question=f"What made the night feel spooky?",
            answer=f"The ghost named {ghost.id} made the night feel spooky because {ghost.pronoun('subject')} showed such strong interest in the {pie.label}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=(
                "The twist was that the ghost's strange behavior had a hidden meaning, "
                "not just a scary one."
            )
            if twist != "memory"
            else f"The twist was that the {pie.label} was tied to a promise, and {ghost.id} had waited for it.",
        ),
        QAItem(
            question="Did the story end happily?",
            answer=(
                "No, it ended badly, with loss and a cold room left behind."
                if ending == "bad"
                else "Not exactly happily, but it ended more gently, with fear turning into a small kind moment."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pie: Pie = f["pie_cfg"]
    return [
        QAItem(
            question="What is pie?",
            answer="Pie is a baked dessert with a filling inside a crust, often sweet and served in slices.",
        ),
        QAItem(
            question="What does interest mean?",
            answer="Interest means paying attention to something because it seems important, curious, or fun.",
        ),
        QAItem(
            question=f"What kind of pie was in the story?",
            answer=f"The story used {pie.phrase}, which is a kind of pie.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that may whisper, drift, or appear from the dark in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child(C) :- child_name(C).
ghost(G) :- ghost_name(G).
pie(P) :- pie_name(P).

interesting(P) :- pie_flavor(P, _).
interest_up(G, P) :- ghost(G), pie(P), interesting(P).
conflict_up(C, G) :- child(C), ghost(G).
twist(memory) :- twist_kind(memory).
twist(kindness) :- twist_kind(kindness).
twist(warning) :- twist_kind(warning).

bad_ending :- ending_kind(bad).
good_ending :- ending_kind(good).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_name", sid))
    for pid, pie in PIES.items():
        lines.append(asp.fact("pie_name", pid))
        lines.append(asp.fact("pie_flavor", pid, pie.flavor))
    for t in TWISTS:
        lines.append(asp.fact("twist_kind", t))
    for e in ENDINGS:
        lines.append(asp.fact("ending_kind", e))
    for c in CHILD_NAMES:
        lines.append(asp.fact("child_name", c))
    for g in GHOST_NAMES:
        lines.append(asp.fact("ghost_name", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show pie_name/1."))
    if model is None:
        print("No ASP model found.")
        return 1
    print("OK: ASP program loads.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with pie, interest, twist, and conflict.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--pie", choices=PIES.keys())
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--ghost", choices=GHOST_NAMES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--ending", choices=ENDINGS)
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    pie = args.pie or rng.choice(list(PIES.keys()))
    twist = args.twist or rng.choice(TWISTS)
    ending = args.ending or rng.choice(ENDINGS)
    name = args.name or rng.choice(CHILD_NAMES)
    ghost = args.ghost or rng.choice(GHOST_NAMES)
    if ending == "bad" and args.twist is None:
        twist = rng.choice(["memory", "warning"])
    return StoryParams(
        place=place,
        pie=pie,
        child_name=name,
        child_type="girl" if name in {"Mina", "June", "Ivy", "Nora"} else "boy",
        ghost_name=ghost,
        twist=twist,
        ending=ending,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PIES[params.pie], params)
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
    StoryParams(place="kitchen", pie="apple", child_name="Mina", child_type="girl", ghost_name="Whisper", twist="memory", ending="bad"),
    StoryParams(place="attic", pie="berry", child_name="Theo", child_type="boy", ghost_name="Murmur", twist="kindness", ending="good"),
    StoryParams(place="cellar", pie="pumpkin", child_name="June", child_type="girl", ghost_name="Mrs. Gray", twist="warning", ending="good"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ending_kind/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show pie_name/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
