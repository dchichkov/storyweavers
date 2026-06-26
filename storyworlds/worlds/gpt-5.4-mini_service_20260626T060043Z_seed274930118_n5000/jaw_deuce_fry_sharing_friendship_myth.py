#!/usr/bin/env python3
"""
storyworlds/worlds/jaw_deuce_fry_sharing_friendship_myth.py
============================================================

A standalone story world for a tiny mythic tale of sharing and friendship.

Seed tale:
---
At the edge of an old sea, three young friends named Jaw, Deuce, and Fry found a
small golden gift in a shell shrine. Jaw wanted to keep it all for himself.
Deuce and Fry reminded Jaw that the gift was brighter when it was shared. The
three friends learned to place the gift in a common bowl and take turns carrying
it, so the light could guide them all home.

World model:
---
The story tracks a simple mythic social system:
* a treasured object can be hoarded or shared
* a broken circle of friendship creates tension
* a communal vessel can restore sharing and friendship
* the final image proves the change by showing the object in common use
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shine": 0.0, "weight": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "greed": 0.0, "sharing": 0.0, "friendship": 0.0, "hurt": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False
    shareable: bool = True


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _p(name: str, *args) -> str:
    if not args:
        return f"{name}."
    def term(v):
        if isinstance(v, int):
            return str(v)
        s = str(v)
        return s if s and (s[0].islower() or s[0] == "_") and all(c.isalnum() or c == "_" for c in s) else f'"{s}"'
    return f"{name}({','.join(term(a) for a in args)})."


SETTING_REGISTRY = {
    "shore": Setting(place="the moonlit shore", sky="silver sky", affords={"gather", "share"}),
    "grove": Setting(place="the shell grove", sky="green dusk", affords={"gather", "share"}),
    "cairn": Setting(place="the old cairn", sky="wind-bright sky", affords={"gather", "share"}),
}

ACTIVITY_REGISTRY = {
    "gather": Activity(id="gather", verb="gather the gift", gerund="gathering the gift", risk="it would be lost alone", keyword="gift", tags={"gift", "moon"}),
    "share": Activity(id="share", verb="share the gift", gerund="sharing the gift", risk="it would grow cold in one hand", keyword="share", tags={"share", "friendship"}),
}

PRIZE_REGISTRY = {
    "golden_fry": Prize(label="golden fry", phrase="a tiny golden fry that glowed like a lantern", type="golden_fry"),
    "shell_bowl": Prize(label="shell bowl", phrase="a small shell bowl with a bright rim", type="shell_bowl", shareable=False),
    "moon_bread": Prize(label="moon bread", phrase="a round loaf pale as the moon", type="moon_bread"),
}

GEAR_REGISTRY = [
    Gear(id="common_bowl", label="a common bowl", prep="place it in a common bowl and take turns carrying it", tail="walked home with the bowl between them"),
    Gear(id="shared_cloth", label="a shared cloth", prep="wrap it in a shared cloth and hold the corners together", tail="stepped softly with the cloth held by all three"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTING_REGISTRY.items():
        for act in setting.affords:
            for prize_id, prize in PRIZE_REGISTRY.items():
                if prize.shareable:
                    combos.append((place, act, prize_id))
    return combos


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if not prize.shareable:
        return None
    return GEAR_REGISTRY[0] if activity.id == "share" or prize.type == "golden_fry" else GEAR_REGISTRY[1]


def predict_mess(world: World, actor: Entity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["greed"] += 1
    sim.get(actor.id).memes["sharing"] -= 1
    prize = sim.get(prize_id)
    soiled = sim.get(actor.id).memes["greed"] > 0 and prize.label == "golden fry"
    return {"soiled": soiled, "hurt": sim.get(actor.id).memes["hurt"]}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize) -> World:
    world = World(setting)
    jaw = world.add(Entity(id="Jaw", kind="character", type="friend"))
    deuce = world.add(Entity(id="Deuce", kind="character", type="friend"))
    fry = world.add(Entity(id="Fry", kind="character", type="friend"))
    prize = world.add(Entity(id="gift", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=jaw.id))
    world.facts.update(jaw=jaw, deuce=deuce, fry=fry, prize=prize, activity=activity, setting=setting, prize_cfg=prize_cfg)

    # Act I
    world.say(f"At {setting.place}, under the {setting.sky}, Jaw, Deuce, and Fry were three friends who had come to the old stones together.")
    world.say(f"They found {prize_cfg.phrase}, and its little light shone on all three faces.")
    jaw.memes["joy"] += 1
    deuce.memes["joy"] += 1
    fry.memes["joy"] += 1
    prize.meters["shine"] += 1

    # Act II
    world.para()
    world.say(f"Jaw wanted to {activity.verb} first, and {activity.risk}.")
    jaw.memes["greed"] += 1
    deuce.memes["friendship"] += 1
    fry.memes["friendship"] += 1
    world.say("Deuce and Fry looked at Jaw with patient eyes and reminded him that a gift grows brighter when it passes from hand to hand.")
    if predict_mess(world, jaw, prize.id)["soiled"]:
        world.say(f"Jaw felt the weight of the moment and knew the gift should not stay lonely.")

    # Act III
    world.para()
    gear = select_gear(activity, prize_cfg)
    if gear:
        world.say(f"Then Deuce spoke gently: “We can {gear.prep}.”")
        prize.owner = "all"
        jaw.memes["greed"] = 0.0
        jaw.memes["sharing"] += 1
        jaw.memes["friendship"] += 1
        deuce.memes["sharing"] += 1
        deuce.memes["friendship"] += 1
        fry.memes["sharing"] += 1
        fry.memes["friendship"] += 1
        prize.meters["shine"] += 2
        world.say(f"Jaw nodded. The three friends {gear.tail}, and {prize_cfg.label} glimmered warmly between them.")
        world.say(f"By the end, they were {activity.gerund}, and the little light made one circle instead of three separate shadows.")

    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about {f["jaw"].id}, {f["deuce"].id}, and {f["fry"].id} learning to {f["activity"].verb}.',
        f"Tell a gentle mythic story about sharing, friendship, and a glowing {f['prize_cfg'].label}.",
        f'Write a small myth where the word "{f["activity"].keyword}" matters and the friends end by sharing what they found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    jaw, deuce, fry, prize, act = f["jaw"], f["deuce"], f["fry"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who found the glowing {prize.label} at {world.setting.place}?",
            answer=f"Jaw, Deuce, and Fry found it together at {world.setting.place}. The light shone on all three of them, which made it feel like a true shared treasure.",
        ),
        QAItem(
            question=f"What did Jaw want to do before the friends chose sharing?",
            answer=f"Jaw wanted to {act.verb} first. That meant keeping the gift too long in one hand, which was not kind to the others.",
        ),
        QAItem(
            question=f"How did friendship change the end of the story?",
            answer="Friendship helped Jaw listen, so the three friends chose a shared way to carry the gift. In the end, nobody stood apart, and the light belonged to all of them together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something too, instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind, trusted bond between people who care for one another and want to help.",
        ),
        QAItem(
            question="Why can a group be stronger than one person alone?",
            answer="A group can be stronger because friends can take turns, help each other, and remember things together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), shareable(P), wants_first(A).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), fits(G,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P) :- valid(Place,A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITY_REGISTRY.items():
        lines.append(asp.fact("activity", aid))
        if aid == "share":
            lines.append(asp.fact("wants_first", aid))
    for pid, p in PRIZE_REGISTRY.items():
        lines.append(asp.fact("prize", pid))
        if p.shareable:
            lines.append(asp.fact("shareable", pid))
    for g in GEAR_REGISTRY:
        lines.append(asp.fact("gear", g.id))
        lines.append(asp.fact("fits", g.id, "share", "golden_fry"))
        lines.append(asp.fact("fits", g.id, "gather", "golden_fry"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about sharing and friendship.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--activity", choices=ACTIVITY_REGISTRY)
    ap.add_argument("--prize", choices=PRIZE_REGISTRY)
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(place=place, activity=activity, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING_REGISTRY[params.place], ACTIVITY_REGISTRY[params.activity], PRIZE_REGISTRY[params.prize])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind:9}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(place="shore", activity="share", prize="golden_fry"),
    StoryParams(place="grove", activity="gather", prize="moon_bread"),
    StoryParams(place="cairn", activity="share", prize="shell_bowl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(models, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
