#!/usr/bin/env python3
"""
citric_flashback_teamwork_sound_effects_tall_tale.py
====================================================

A small standalone story world for a tall-tale flavored citric adventure.
A child-sized problem grows, then is solved by remembering an old trick, a
little teamwork, and some vivid sound effects.

The world models:
- a citric prize that can be spoiled by rough handling
- a flashback to a past lesson
- teamwork that prevents loss or mess
- sound effects that make the story feel big and lively
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    mess: str
    zone: set[str]
    keyword: str = "citric"
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
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.flashback_seen = False
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        clone.paragraphs = [[]]
        return clone


def sound_effect(activity: Activity) -> str:
    return {
        "squeeze": "SPLISH-SPLAT, squeeze-squeak!",
        "roll": "whirr-whirr-WHUM!",
        "carry": "hup-hup-HOORAY!",
    }.get(activity.id, "tap-tap-TA-DA!")


def flashback_line(hero: Entity) -> str:
    return f"That reminded {hero.pronoun('object')} of an old day when a bright trick saved the whole basket."


def predict_spill(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("dirty", 0) >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    if narrate:
        world.say(f"{sound_effect(activity)} The {activity.gerund} began in a blink, and the air felt bigger already.")


def maybe_spoil(world: World, actor: Entity, prize: Entity, activity: Activity) -> bool:
    if not predict_spill(world, actor, activity, prize.id):
        return False
    prize.meters["dirty"] = prize.meters.get("dirty", 0) + 1
    world.say(f"The citric juice splashed up and left {prize.pronoun('possessive')} {prize.label} sticky.")
    return True


def teamwork_fix(world: World, hero: Entity, helper: Entity, prize: Entity, gear: Gear, activity: Activity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1
    world.say(f"{helper.id} said, \"Let's do it together.\"")
    world.say(f"{gear.prep}.")
    world.say(f"With {gear.label} in place, the {activity.verb} went on without ruining {prize.phrase}.")
    world.say(f"{gear.tail} {sound_effect(activity)} and everybody laughed like thunder in a tin cup.")
    prize.meters["dirty"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"squeeze", "carry"}),
    "porch": Setting(place="the porch", affords={"roll", "carry"}),
    "kitchen": Setting(place="the kitchen", affords={"squeeze"}),
}

ACTIVITIES = {
    "squeeze": Activity(
        id="squeeze",
        verb="squeeze the citric fruit",
        gerund="squeezing the citric fruit",
        rush="dash to the table",
        sound="SPLISH-SPLAT",
        mess="sticky",
        zone={"hands", "torso"},
        keyword="citric",
        tags={"citric", "sticky"},
    ),
    "roll": Activity(
        id="roll",
        verb="roll the basket of citric fruit",
        gerund="rolling the basket",
        rush="heave the basket downhill",
        sound="whirr-whirr",
        mess="dusty",
        zone={"hands"},
        keyword="citric",
        tags={"citric"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the citric crate",
        gerund="carrying the citric crate",
        rush="haul the crate across the yard",
        sound="hup-hup",
        mess="bumped",
        zone={"hands"},
        keyword="citric",
        tags={"citric"},
    ),
}

PRIZES = {
    "napkin": Prize(label="napkin", phrase="a clean napkin", type="napkin", region="torso"),
    "shirt": Prize(label="shirt", phrase="a white shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a blue apron", type="apron", region="torso"),
}

GEAR = [
    Gear(
        id="tray",
        label="a wide tray",
        guards={"sticky"},
        prep="They slid a wide tray under the fruit first",
        tail="The tray caught the drips",
    ),
    Gear(
        id="towel",
        label="a thick towel",
        guards={"sticky", "dusty", "bumped"},
        prep="They wrapped the prize in a thick towel",
        tail="The towel kept the mess away",
    ),
]

NAMES = ["Mabel", "Otto", "Cora", "June", "Percy", "Nell", "Bert", "Ada"]
HELPERS = ["Grandma", "Uncle Jo", "Aunt Bea", "Papa"]
TRAITS = ["bold", "bright", "spry", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    continue
                if act.mess in {"sticky"} and prize.region == "torso":
                    out.append((place, act_id, prize_id))
                elif act.mess in {"dusty", "bumped"}:
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale citric teamwork story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
        raise StoryError("(No valid citric tall-tale combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mabel", "Cora", "June", "Nell", "Ada"} else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman" if params.helper in {"Grandma", "Aunt Bea"} else "man"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=helper.id))

    activity = ACTIVITIES[params.activity]
    gear = GEAR[0] if activity.mess == "sticky" else GEAR[1]

    world.say(f"{hero.id} was a {params.trait} little storyteller who loved anything citric.")
    world.say(f"{hero.id} and {helper.id} had a basket of {activity.keyword} fruit and a job as big as a barn.")
    world.say(f"They were in {world.setting.place} when {hero.id} wanted to {activity.verb}.")

    world.para()
    world.say(f"{helper.id} frowned at the clean {prize.label}.")
    if predict_spill(world, hero, activity, prize.id):
        world.say(f'"Careful," {helper.id} said. "That could splash right onto the {prize.label}."')
    world.say(f"{hero.id} reached for the fruit anyway, and {sound_effect(activity)} the work nearly turned wild.")
    world.say(flashback_line(hero))
    maybe_spoil(world, hero, prize, activity)

    world.para()
    world.say(f"{hero.id} remembered the old lesson, and {helper.id} did too.")
    teamwork_fix(world, hero, helper, prize, gear, activity)

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, gear=gear, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a tall tale for a child that includes the word "{p.activity}" and the sound effect "{ACTIVITIES[p.activity].sound}".',
        f"Tell a citric story where {p.name} and {p.helper} solve a sticky problem by working together.",
        "Write a lively flashback story with a big fruit problem, a remembered trick, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    activity = world.facts["activity"]
    gear = world.facts["gear"]
    return [
        QAItem(
            question=f"What did {p.name} want to do with the citric fruit?",
            answer=f"{p.name} wanted to {activity.verb}. That made the day feel huge and lively.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the {prize.label}?",
            answer=f"{helper.id} worried because the citric juice could splash onto the {prize.label} and leave it sticky.",
        ),
        QAItem(
            question="What old memory helped them solve the problem?",
            answer="A flashback reminded them of a previous day when a bright trick kept the fruit mess from spreading.",
        ),
        QAItem(
            question="How did teamwork help in the end?",
            answer=f"{hero.id} and {helper.id} worked together with {gear.label}, so the {prize.label} stayed clean while the citric work went on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does citric mean?",
            answer="Citric means related to sour fruits like lemons and oranges.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that briefly remembers something from earlier or from the past.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="Why do sound effects matter in a tall tale?",
            answer="Sound effects make the action feel lively, big, and exciting, which fits a tall tale style.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
at_risk(P) :- prize(P), worn_on(P, torso), splashes(A, torso), activity(A).
needs_help(A) :- activity(A), at_risk(P), prize(P).
has_fix(A, G) :- needs_help(A), gear(G), guards(G, sticky).
valid(Place, A, P) :- affords(Place, A), at_risk(P), has_fix(A, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for a, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("mess_of", a, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", a, r))
    for p, pr in PRIZES.items():
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("worn_on", p, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(place="orchard", activity="squeeze", prize="apron", name="Mabel", helper="Grandma", trait="bright"),
    StoryParams(place="porch", activity="roll", prize="shirt", name="Otto", helper="Uncle Jo", trait="spry"),
    StoryParams(place="kitchen", activity="squeeze", prize="napkin", name="Cora", helper="Aunt Bea", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
