#!/usr/bin/env python3
"""
storyworlds/worlds/aunt_clothed_companion_bad_ending_fairy_tale.py
====================================================================

A small fairy-tale story world about an aunt, a clothed companion, and a
warning that goes unheeded.

Premise:
- An aunt cares for a young companion who wears a special cloak.
- They travel through a fairy-tale setting with a dangerous path.
- The aunt warns that the cloak will catch on the briars.
- The companion ignores the warning and goes on.
- The cloak is torn, the companion is lost for a while, and the tale ends badly.

This world is intentionally narrow: it favors one strong, state-driven story
over many weak variations.

Bad-ending feature:
- The ending does not fully repair the loss.
- The final image proves what changed: the cloak is ruined, the companion is
  still upset, and the aunt is left holding the torn hem.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type == "aunt":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Setting:
    place: str
    sentence: str
    hazard: str
    shadow: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["braving"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id == "cloak" and "cloak" in world.fired:
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["torn"] += 1
            item.meters["dirty"] += 1
            out.append(f"The {item.label} was caught and torn.")
    return out


def _r_lost(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["lost"] < THRESHOLD:
            continue
        sig = ("lost", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        return ["__lost__"]
    return []


CAUSAL_RULES = [
    _r_soil,
    _r_lost,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__lost__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "torn": bool(prize.meters["torn"] >= THRESHOLD),
        "fear": sum(e.memes["fear"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["braving"] += 1
    actor.memes["excitement"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, aunt: Entity, companion: Entity, prize: Entity) -> None:
    world.say(
        f"Once in a little fairy-tale place, {aunt.id} the aunt kept watch over "
        f"{companion.id}, a clothed companion who loved to wear {prize.phrase}."
    )


def setting_line(world: World, setting: Setting) -> None:
    world.say(setting.sentence)


def warning(world: World, aunt: Entity, companion: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, companion, activity, prize.id)
    if pred["torn"]:
        world.facts["predicted_torn"] = True
        world.say(
            f'"Do not {activity.verb}," {aunt.pronoun("possessive")} aunt said. '
            f'"The {prize.label} will catch on the {world.setting.hazard}."'
        )


def ignore(world: World, companion: Entity, activity: Activity) -> None:
    companion.memes["stubborn"] += 1
    world.say(
        f"But the clothed companion only smiled, took a breath, and tried to "
        f"{activity.rush}."
    )


def turn_bad(world: World, aunt: Entity, companion: Entity, activity: Activity, prize: Prize) -> None:
    companion.memes["lost"] += 1
    world.say(
        f"The path twisted under the gray trees, and the {world.setting.shadow} "
        f"made the way hard to see."
    )
    world.say(
        f"At last, the {prize.label} caught on the {world.setting.hazard}, and "
        f"{companion.id} could not keep up."
    )
    world.say(
        f"{aunt.id} called and called, but only the wind answered."
    )


def ending(world: World, aunt: Entity, companion: Entity, prize: Entity) -> None:
    world.say(
        f"When the dusk came down, {aunt.id} found only a torn thread of the "
        f"{prize.label} in the briars, and the companion was still missing from "
        f"the path home."
    )


SETTINGS = {
    "wood": Setting(
        place="the dark wood",
        sentence="The wood was full of blackberry briars, narrow paths, and old roots that curled like knuckles.",
        hazard="briars",
        shadow="owl-shadow",
        affords={"wander"},
    ),
    "heath": Setting(
        place="the windy heath",
        sentence="The heath was open and lonely, with long grass bending under a cold wind.",
        hazard="thistles",
        shadow="cloud-shadow",
        affords={"wander"},
    ),
}

ACTIVITIES = {
    "wander": Activity(
        id="wander",
        verb="wander into the thorns",
        gerund="wandering among the brambles",
        rush="go farther into the briars",
        mess="braved",
        soil="torn and snagged",
        zone={"torso"},
        keyword="companion",
        tags={"wood", "cloak", "aunt"},
    )
}

PRIZES = {
    "cloak": Prize(
        label="cloak",
        phrase="a bright blue cloak with silver thread",
        type="cloak",
        region="torso",
    )
}

GEAR = [
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"braved"},
        prep="put on soft gloves",
        tail="went on with soft gloves",
    )
]

AUNT_NAMES = ["Aunt Mara", "Aunt Elin", "Aunt Tessa", "Aunt Brin"]
COMPANION_NAMES = ["Robin", "Pip", "Nell", "Jory", "Mina"]
TRAITS = ["little", "brave", "curious", "stubborn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    aunt_name: str
    companion_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        aunt_name=args.name or rng.choice(AUNT_NAMES),
        companion_name=args.companion or rng.choice(COMPANION_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, aunt_name: str, companion_name: str, trait: str) -> World:
    world = World(setting)
    aunt = world.add(Entity(id=aunt_name, kind="character", type="aunt", label="aunt"))
    companion = world.add(Entity(id=companion_name, kind="character", type="companion", label="companion"))
    prize = world.add(Entity(
        id="cloak", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=companion.id, caretaker=aunt.id, worn_by=companion.id
    ))

    intro(world, aunt, companion, prize)
    setting_line(world, setting)
    world.para()
    world.say(f"{companion.id} was a {trait} clothed companion, and {prize.label} suited {companion.pronoun('possessive')} shoulders just so.")
    world.say(f"{companion.id} loved to {activity.gerund}, though the path was full of trouble.")
    warning(world, aunt, companion, activity, prize)
    ignore(world, companion, activity)
    turn_bad(world, aunt, companion, activity, prize_cfg)
    world.para()
    ending(world, aunt, companion, prize)

    world.facts.update(
        aunt=aunt,
        companion=companion,
        prize=prize,
        activity=activity,
        setting=setting,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    aunt = f["aunt"]
    companion = f["companion"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        "Write a short fairy tale with an aunt, a clothed companion, and a bad ending.",
        f"Tell a gentle fairy tale where {companion.id} wants to {activity.verb} but {aunt.id} warns about {prize.label}.",
        f"Write a story about an aunt and a clothed companion in the {world.setting.place} that ends with a torn {prize.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    aunt = f["aunt"]
    companion = f["companion"]
    activity = f["activity"]
    prize = f["prize"]
    setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was watching over the clothed companion in the fairy-tale story?",
            answer=f"{aunt.id}, the aunt, was watching over {companion.id}.",
        ),
        QAItem(
            question=f"What did the companion want to do in {setting.place}?",
            answer=f"{companion.id} wanted to {activity.verb} in {setting.place}.",
        ),
        QAItem(
            question=f"Why did the aunt worry about the {prize.label}?",
            answer=f"She worried because the {prize.label} could catch on the {setting.hazard} and get torn.",
        ),
        QAItem(
            question=f"What kind of companion was {companion.id}?",
            answer=f"{companion.id} was a {trait} clothed companion who loved the cloak, even though the path was dangerous.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the {prize.label} was torn, and {companion.id} did not come home right away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a briar?",
            answer="A briar is a thorny plant with prickly stems that can snag cloth and skin.",
        ),
        QAItem(
            question="What is a cloak for?",
            answer="A cloak is a loose garment worn over clothes to keep someone warm or dressed up.",
        ),
        QAItem(
            question="Why do thorny places feel dangerous?",
            answer="Thorny places can scratch skin and tear clothes, so they are hard to walk through safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.aunt_name, params.companion_name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(
            place=p, activity=a, prize=pr,
            aunt_name=AUNT_NAMES[0], companion_name=COMPANION_NAMES[0], trait=TRAITS[0]
        )) for p, a, pr in valid_combos()]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
