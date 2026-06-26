#!/usr/bin/env python3
"""
storyworlds/worlds/hand_pl_dim_reconciliation_friendship_slice_of.py
=====================================================================

A small slice-of-life storyworld about friendship, a shared plan, and a gentle
reconciliation after a misunderstanding.

Seed image:
- Two friends are working on a tiny hand-pl-dim craft at a quiet table.
- One friend gets worried that the other will smear or bend the shared project.
- They pause, talk it through, fix the mistake, and end the day feeling close
  again.

The world is intentionally tiny and constraint-checked:
- There is a clear at-risk item.
- There is a compatible, reasonable fix.
- Invalid combinations raise StoryError.
- The simulated state drives the prose and Q&A.

This file is self-contained aside from the shared result containers.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "mess": 0.0,
                "damage": 0.0,
                "stress": 0.0,
                "calm": 0.0,
                "joy": 0.0,
                "hurt": 0.0,
                "repair": 0.0,
                "apology": 0.0,
                "tension": 0.0,
                "warmth": 0.0,
            }
        if not self.memes:
            self.memes = {
                "annoyance": 0.0,
                "worry": 0.0,
                "sadness": 0.0,
                "affection": 0.0,
                "embarrassment": 0.0,
                "understanding": 0.0,
                "reconciliation": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the community table"
    indoor: bool = False
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            item.meters["damage"] += 1
            out.append(f"{actor.id}'s {item.label} got smudged.")
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["worry"] + actor.memes["annoyance"] < THRESHOLD:
            continue
        sig = ("tension", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["tension"] += 1
        out.append(f"The air between the friends felt tight.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["damage"] < THRESHOLD:
            continue
        sig = ("repair", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["repair"] += 1
        out.append(f"Someone took time to make it neat again.")
    return out


CAUSAL_RULES = [_r_soil, _r_tension, _r_repair]


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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": prize.meters["damage"] >= THRESHOLD,
        "tension": sum(e.meters["tension"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("The setting cannot host that activity.")
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "table": Setting(place="the community table", indoor=True, affords={"craft", "share"}),
    "bench": Setting(place="the park bench", indoor=False, affords={"craft", "share"}),
    "porch": Setting(place="the porch", indoor=False, affords={"craft", "share"}),
}

ACTIVITIES = {
    "craft": Activity(
        id="craft",
        verb="make the hand-pl-dim craft",
        gerund="working on the hand-pl-dim craft",
        rush="reach across the paper too fast",
        mess="smudge",
        soil="smudged",
        zone={"hands", "table"},
        keyword="hand-pl-dim",
        tags={"hand-pl-dim", "craft", "paper"},
    ),
    "share": Activity(
        id="share",
        verb="share the markers",
        gerund="sharing the markers",
        rush="grab the blue marker first",
        mess="smudge",
        soil="smudged",
        zone={"hands", "paper"},
        keyword="hand-pl-dim",
        tags={"hand-pl-dim", "share", "markers"},
    ),
}

PRIZES = {
    "poster": Prize(
        label="poster",
        phrase="a bright poster for the hand-pl-dim project",
        type="poster",
        region="table",
    ),
    "card": Prize(
        label="card",
        phrase="a folded friendship card",
        type="card",
        region="hands",
    ),
    "drawing": Prize(
        label="drawing",
        phrase="a careful little drawing",
        type="drawing",
        region="paper",
    ),
}

GEAR = [
    Gear(
        id="mat",
        label="a clean craft mat",
        covers={"table", "paper"},
        guards={"smudge"},
        prep="put a clean craft mat under the paper",
        tail="slid the mat under the project",
    ),
    Gear(
        id="apron",
        label="an apron",
        covers={"hands", "paper"},
        guards={"smudge"},
        prep="tie on an apron first",
        tail="tied on the apron before touching the markers",
    ),
]

NAMES = ["Mina", "Owen", "Lila", "Theo", "Nora", "Pia", "Eli", "Zuri"]
TRAITS = ["quiet", "curious", "gentle", "cheerful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name_a: str
    name_b: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle slice-of-life story about a hand-pl-dim craft at a quiet table.',
        f"Tell a short story where {f['a'].id} and {f['b'].id} work on {f['activity'].keyword} and "
        f"mend a small friendship worry.",
        f"Write a story that includes the phrase \"{f['activity'].keyword}\" and ends with the friends feeling close again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, prize, act, gear = f["a"], f["b"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"What were {a.id} and {b.id} doing at {world.setting.place}?",
            answer=f"They were {act.gerund} together at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did they worry might get damaged?",
            answer=f"They worried that {prize.phrase} could get smudged if they moved too quickly.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {gear.label} first, which kept the project safe and helped them make up.",
        ),
        QAItem(
            question=f"How did the friends feel at the end?",
            answer="They felt warm and happy again, because they had talked kindly and stayed friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a friendship card?",
            answer="A friendship card is a card you make or give to show someone you care about them.",
        ),
        QAItem(
            question="What does an apron do?",
            answer="An apron helps keep clothes clean when you do messy work like painting or crafting.",
        ),
        QAItem(
            question="What is a craft mat for?",
            answer="A craft mat gives paper and glue a clean place to sit so the table stays neat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    world = World(setting)
    a = world.add(Entity(id=params.name_a, kind="character", type="girl" if params.name_a in {"Mina", "Lila", "Nora", "Pia", "Zuri"} else "boy"))
    b = world.add(Entity(id=params.name_b, kind="character", type="girl" if params.name_b in {"Mina", "Lila", "Nora", "Pia", "Zuri"} else "boy"))
    a.memes["affection"] += 1
    b.memes["affection"] += 1
    prize = world.add(Entity(id="project", type="paper", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=a.id, caretaker=b.id, region=PRIZES[params.prize].region))
    gear = select_gear(activity, PRIZES[params.prize])
    if gear is None:
        raise StoryError("No reasonable protective gear fits this story.")
    gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    world.facts.update(a=a, b=b, prize=prize, activity=activity, gear=gear_ent)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    a, b, prize, act = world.facts["a"], world.facts["b"], world.facts["prize"], world.facts["activity"]
    a_trait = params.trait_a
    b_trait = params.trait_b

    world.say(f"{a.id} and {b.id} were two {a_trait} and {b_trait} friends at {world.setting.place}.")
    world.say(f"They loved {act.keyword} and had a small hand-pl-dim project waiting on the table.")
    world.say(f"{a.id} had brought {prize.phrase}, and both friends wanted it to turn out just right.")
    world.para()
    world.say(f"At first, they leaned over the paper together.")
    world.say(f"{b.id} wanted to {act.verb}, but {a.id} worried the fast movement could leave a smudge.")
    pred = predict_mess(world, b, act, prize.id)
    if pred["soiled"]:
        a.memes["worry"] += 1
        b.memes["annoyance"] += 1
        world.say(f"\"Careful,\" {a.id} said. \"I don't want our {prize.label} to get {act.soil}.\"")
    _do_activity(world, b, act, narrate=False)
    if prize.meters["damage"] >= THRESHOLD:
        world.say(f"The paper nearly got {act.soil}, and both friends went quiet for a moment.")
        world.say(f"{b.id} looked down and said sorry right away.")
        b.memes["apology"] += 1
        b.memes["understanding"] += 1
        a.memes["sadness"] += 1
    world.para()
    world.say(f"Then {a.id} picked up {world.facts['gear'].label} and smiled.")
    world.say(f"\"Let's set this up first,\" {a.id} said, and the friends {world.facts['gear'].label if False else ''}".strip())
    world.say(f"They {gear_tail(world.facts['gear'])}, and the next try stayed neat.")
    prize.meters["damage"] = 0.0
    prize.meters["repair"] += 1
    a.memes["understanding"] += 1
    b.memes["understanding"] += 1
    a.memes["reconciliation"] += 1
    b.memes["reconciliation"] += 1
    a.meters["warmth"] += 1
    b.meters["warmth"] += 1
    world.say(f"By the end, the hand-pl-dim project was clean, and the two friends were laughing again.")
    world.say(f"{a.id} and {b.id} sat side by side, pleased with the little thing they had made together.")
    world.facts["resolved"] = True
    return world


def gear_tail(gear: Entity) -> str:
    return {
        "a clean craft mat": "slid the mat under the project",
        "an apron": "tied on the apron before touching the markers",
    }.get(gear.label, "set the gear in place")


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.keyword} would not reasonably threaten that item in this small slice-of-life world.)"


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
compatible_fix(A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), compatible_fix(A,P).
#show valid/3.
"""


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
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about friendship and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    na = args.name_a or rng.choice(NAMES)
    nb = args.name_b or rng.choice([n for n in NAMES if n != na])
    return StoryParams(place=place, activity=activity, prize=prize, name_a=na, name_b=nb, trait_a=rng.choice(TRAITS), trait_b=rng.choice([t for t in TRAITS if t != "quiet"]))


def generate(params: StoryParams) -> StorySample:
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
        print("--- world model ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, {k: v for k, v in e.meters.items() if v}, {k: v for k, v in e.memes.items() if v})
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="table", activity="craft", prize="poster", name_a="Mina", name_b="Owen", trait_a="gentle", trait_b="curious"),
    StoryParams(place="bench", activity="share", prize="card", name_a="Lila", name_b="Theo", trait_a="cheerful", trait_b="patient"),
    StoryParams(place="porch", activity="craft", prize="drawing", name_a="Nora", name_b="Eli", trait_a="quiet", trait_b="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(*c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name_a} and {p.name_b} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
