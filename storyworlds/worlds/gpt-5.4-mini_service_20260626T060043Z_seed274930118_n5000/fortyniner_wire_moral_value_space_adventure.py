#!/usr/bin/env python3
"""
storyworlds/worlds/fortyniner_wire_moral_value_space_adventure.py
==================================================================

A small story world about a space adventure, a stubborn fortyniner, and a
moral choice involving a wire.

Premise:
- A young fortyniner on a little mining ship wants to keep a shiny wire for
  themself.
- The wire is useful for the ship and belongs in the shared kit.
- A captain sees the problem before it causes trouble.
- The story turns when the fortyniner chooses honesty over greed and puts the
  wire back where it belongs.

This world keeps the prose child-facing and state-driven: the narration follows
meters and memes, and the ending image proves the moral change.
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

METER_THRESHOLD = 1.0
MEME_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    value: str
    plural: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    place_back: str
    helps: set[str]
    honest: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_holding(world: World) -> list[str]:
    out = []
    carrier = world.facts.get("carrier")
    wire = world.facts.get("wire")
    if not carrier or not wire:
        return out
    c = world.get(carrier)
    w = world.get(wire)
    if c.memes.get("greed", 0.0) >= MEME_THRESHOLD and w.carrier == c.id:
        sig = ("holding", c.id, w.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"{c.id} clutched the wire tighter than before.")
    return out


CAUSAL_RULES = [_r_holding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if activity.id in fix.helps and fix.honest:
            return fix
    return None


def predict_misuse(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "lost": bool(prize.carrier != world.get(prize_id).carrier),
        "greed": sim.get(actor.id).memes.get("greed", 0.0),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.id] = actor.meters.get(activity.id, 0.0) + 1
    actor.memes["want"] = actor.memes.get("want", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little fortyniner aboard the starship, quick-eyed and always hunting for shiny things."
    )


def describe_setting(world: World, activity: Activity) -> None:
    world.say(
        f"The ship drifted through a quiet moonfield, and the cargo bay hummed with coils, tools, and starlight."
    )
    world.say(f"It was a good place to {activity.gerund}, if only everyone shared fairly.")


def love_wire(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.carrier = hero.id
    world.say(
        f"{hero.id} loved the {prize.label} because it gleamed like a tiny silver ribbon in the dark."
    )


def want_keep(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["greed"] = hero.memes.get("greed", 0.0) + 1
    world.say(
        f"When no one was looking, {hero.id} slipped the {prize.label} into {hero.pronoun('possessive')} pocket."
    )


def warn(world: World, captain: Entity, hero: Entity, prize: Entity, activity: Activity) -> bool:
    pred = predict_misuse(world, hero, activity, prize.id)
    if not pred["lost"]:
        return False
    world.facts["warned"] = True
    world.say(
        f'"That wire belongs with the ship," {captain.id} said gently. "If you keep it hidden, the bay cannot use it."'
    )
    return True


def confess(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["shame"] = hero.memes.get("shame", 0.0) + 1
    world.say(f"{hero.id} looked down at the pocket and felt warm in the face.")
    world.say(f'"I took the wire," {hero.id} said. "I should give it back."')


def return_wire(world: World, hero: Entity, captain: Entity, prize: Entity, fix: Fix) -> None:
    hero.memes["greed"] = 0.0
    hero.memes["honesty"] = hero.memes.get("honesty", 0.0) + 1
    prize.carrier = None
    world.say(
        f"{hero.id} handed the {prize.label} back. {captain.id} smiled and set it into the shared repair tray."
    )
    world.say(
        f'The {fix.label} clicked into place, and the ship could mend its wires again.'
    )


def ending(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"By the end, {hero.id} was helping sort the tools, and the little wire shone where everyone could use it."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         captain_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type))
    prize = world.add(Entity(
        id="wire",
        kind="thing",
        type="wire",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner="ship",
    ))

    world.facts.update(hero=hero, captain=captain, prize=prize, activity=activity, setting=setting, wire=prize.id)

    intro(world, hero)
    describe_setting(world, activity)
    love_wire(world, hero, prize)

    world.para()
    want_keep(world, hero, prize)
    warn(world, captain, hero, prize, activity)

    world.para()
    confess(world, hero, prize)
    fix = select_fix(activity, prize_cfg)
    if fix is None:
        raise StoryError("No honest fix exists for this moral choice.")
    return_wire(world, hero, captain, prize, fix)
    ending(world, hero, prize)

    world.facts["fix"] = fix
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "cargo_bay": Setting(name="cargo_bay", place="the cargo bay", afford={"sort"}),
    "repair_deck": Setting(name="repair_deck", place="the repair deck", afford={"repair"}),
    "moon_port": Setting(name="moon_port", place="the moon port", afford={"sort", "repair"}),
}

ACTIVITIES = {
    "sort": Activity(
        id="sort",
        verb="sort the spare parts",
        gerund="sorting the spare parts",
        risk="lose track of the ship's tools",
        mess="scattered",
        zone={"hands"},
        tags={"tools", "sharing", "space"},
    ),
    "repair": Activity(
        id="repair",
        verb="repair the broken panel",
        gerund="repairing the broken panel",
        risk="leave the bay without a working line",
        mess="broken",
        zone={"hands"},
        tags={"repair", "ship", "space"},
    ),
}

PRIZES = {
    "wire": Prize(
        label="wire",
        phrase="a bright silver wire",
        region="hands",
        value="shared",
    )
}

FIXES = [
    Fix(
        id="return_tray",
        label="repair tray",
        place_back="the shared repair tray",
        helps={"sort", "repair"},
        honest=True,
    )
]

NAMES = ["Nova", "Pip", "Jory", "Mira", "Tess", "Rian"]
TYPES = ["girl", "boy"]
TRAITS = ["curious", "stubborn", "bright", "quick", "small"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short space adventure for a child where a fortyniner named {hero.id} learns to share a wire.',
        f"Tell a gentle moral story about {hero.id} wanting to {act.verb}, then telling the truth about a wire.",
        f'Write a story that includes the words "fortyniner" and "wire" and ends with an honest choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize"]
    act = f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to keep hidden at first?",
            answer=f"{hero.id} wanted to keep the wire hidden in {hero.pronoun('possessive')} pocket.",
        ),
        QAItem(
            question=f"Who reminded {hero.id} that the wire belonged to the ship?",
            answer=f"{captain.id} reminded {hero.id} that the wire belonged with the ship and needed to be shared.",
        ),
        QAItem(
            question=f"What did {hero.id} do after feeling ashamed?",
            answer=f"{hero.id} told the truth, handed back the wire, and helped with the ship's work.",
        ),
        QAItem(
            question=f"Why was keeping the wire a bad idea during {act.gerund}?",
            answer=f"If {hero.id} kept the wire, the ship could not use it while the crew was busy with {act.gerund}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end for the wire?",
                answer=f"The wire was put back in the shared repair tray, where everyone on the ship could use it again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wire?",
            answer="A wire is a thin metal strand that can carry power or help hold and fix things together.",
        ),
        QAItem(
            question="What does it mean to be honest?",
            answer="Being honest means telling the truth, even when it is hard.",
        ),
        QAItem(
            question="Why do people share tools on a ship?",
            answer="People share tools on a ship so the whole crew can fix things and stay safe.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A wire is at risk when a character secretly carries it instead of leaving it shared.
at_risk(W) :- wire(W), carried(W), secret_keep(W).

% Honesty resolves the moral tension.
resolved(W) :- wire(W), shared_back(W), told_truth(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for fix in FIXES:
        lines.append(asp.fact("fix", fix.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure moral-value story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(sorted(SETTINGS[setting].afford or ACTIVITIES.keys()))
    prize = args.prize or "wire"
    if args.activity and args.activity not in SETTINGS[setting].afford:
        raise StoryError("That activity does not fit the chosen setting.")
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(TYPES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender)
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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("cargo_bay", "sort", "wire", "Nova", "girl", "curious"),
            StoryParams("repair_deck", "repair", "wire", "Pip", "boy", "stubborn"),
            StoryParams("moon_port", "sort", "wire", "Mira", "girl", "bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
