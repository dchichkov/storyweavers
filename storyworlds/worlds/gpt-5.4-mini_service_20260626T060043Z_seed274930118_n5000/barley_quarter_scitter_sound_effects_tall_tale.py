#!/usr/bin/env python3
"""
storyworlds/worlds/barley_quarter_scitter_sound_effects_tall_tale.py
=====================================================================

A small stand-alone tall-tale storyworld about barley, a quarter, and a
scittering sound effect.

Core premise:
- A child and an elder are loading barley at a barn.
- A shiny quarter starts making a scitter-scitter sound in the grain.
- The sound leads to a small problem, then a clever fix.
- The ending proves the change: the barley is safe, the quarter is found, and
  the child is braver and happier.

This world is intentionally compact and constraint-driven:
- one character-driven tale shape
- one main tension/fix pair
- sound effects are part of the world model and prose
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
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "noise": 0.0, "lost": 0.0, "fullness": 0.0}
        if not self.memes:
            self.memes = {"wonder": 0.0, "worry": 0.0, "pride": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_scitter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.type != "quarter" or item.worn_by != actor.id:
                continue
            sig = ("scitter", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["lost"] += 1
            out.append(f"{item.label.capitalize()} went scitter-scitter in the barley.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["wonder"] += 1
        out.append(f"{actor.id} listened hard, trying to guess what the sound meant.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.type != "quarter" or item.meters["lost"] < THRESHOLD:
            continue
        for actor in world.characters():
            if actor.memes["pride"] < THRESHOLD:
                continue
            sig = ("relief", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["relief"] += 1
            out.append("The little quarter was found safe and shining again.")
    return out


CAUSAL_RULES = [
    Rule("scitter", _r_scitter),
    Rule("worry", _r_worry),
    Rule("relief", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"lost": bool(prize and prize.meters["lost"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That activity does not belong in this setting.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["noise"] += 1
    actor.memes["wonder"] += 1
    if narrate:
        world.say(f"{actor.id} {activity.verb}, and the barn answered with {activity.sound}.")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big hat and a bigger curiosity."
    )


def setup(world: World, hero: Entity, elder: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"At the barn, {hero.id} and {elder.label} worked by the mountain of barley."
    )
    world.say(
        f"{hero.id} kept a shiny {prize.label} tucked close, because it had been "
        f"saved from a jar of change for a very special day."
    )
    world.say(
        f"{hero.id} loved the way the barley looked, all gold and whispery, and "
        f"the whole place felt ready for a tall tale."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["lost"]:
        return False
    hero.memes["worry"] += 1
    world.say(
        f'"Easy now," {elder.label} said. "If you go flinging that barley around, '
        f"your {prize.label} may go scitter-scatter right out of sight.""
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} wanted to prove {hero.pronoun('possessive')} hands were quicker "
        f"than a hiccup in a henhouse."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tried to {activity.rush}, and the grain "
        f"answered with a mighty {activity.sound}."
    )


def find_fix(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        label=gear_def.label,
        type="gear",
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["lost"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{elder.label} blinked once and grinned. "How about we {gear_def.prep}?"'
    )
    return gear_def


def accept(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["pride"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} nodded, and together they {gear_def.tail}."
    )
    world.say(
        f"Then {hero.id} could keep {hero.pronoun('possessive')} {prize.label} safe, "
        f"hear only a cheerful {activity.sound}, and finish the job with a smile."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mabel", hero_type: str = "girl",
         parent_type: str = "grandfather") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type, label="Grandpa Quill"))
    prize = world.add(Entity(
        id="quarter",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    setup(world, hero, elder, prize, activity)

    world.para()
    _do_activity(world, hero, activity, narrate=True)
    warn(world, elder, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear_def = find_fix(world, hero, elder, activity, prize)
    if gear_def:
        accept(world, hero, elder, activity, prize, gear_def)

    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "barn": Setting(place="the red barn", affords={"barley_turn", "barley_haul"}),
    "threshing_floor": Setting(place="the threshing floor", affords={"barley_turn"}),
}

ACTIVITIES = {
    "barley_turn": Activity(
        id="barley_turn",
        verb="turn the barley with a great sweeping shove",
        gerund="turning the barley",
        rush="scoop both arms through the grain",
        sound="scitter-scatter",
        mess="dusty",
        zone={"hands", "torso"},
        keyword="barley",
    ),
    "barley_haul": Activity(
        id="barley_haul",
        verb="haul the barley sacks to the wagon",
        gerund="hauling barley sacks",
        rush="heave the sacks higher and higher",
        sound="clatter-scitter",
        mess="dusty",
        zone={"hands", "torso"},
        keyword="barley",
    ),
}

PRIZES = {
    "quarter": Prize(
        label="quarter",
        phrase="a bright silver quarter",
        type="quarter",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="pocketcloth",
        label="a buttoned pocket-cloth",
        covers={"hands"},
        guards={"dusty"},
        prep="button the pocket-cloth over the quarter",
        tail="buttoned the pocket-cloth around the quarter",
    )
]

NAMES = ["Mabel", "Ruth", "Toby", "Nell", "Hank"]
TRAITS = ["bold", "curious", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    return [
        f'Write a tall tale for a small child that includes the word "{act.keyword}" and the sound "{act.sound}".',
        f"Tell a barnyard story where {hero.id} tries to {act.verb}, but a shiny {prize.label} starts making a scittering sound.",
        f"Write a short story about barley, a quarter, and a clever fix that keeps the quarter from getting lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} hear when the barley started moving?",
            answer=f"{hero.id} heard {act.sound}, a quick scitter-scatter sound in the barley.",
        ),
        QAItem(
            question=f"Why did Grandpa Quill worry about the quarter?",
            answer=(
                f"Grandpa Quill worried because the {prize.label} could slip into the barley "
                f"and get lost when {hero.id} tried to {act.verb}."
            ),
        ),
        QAItem(
            question=f"What helped {hero.id} keep the quarter safe at the end?",
            answer=(
                f"{hero.id} used a buttoned pocket-cloth, so the {prize.label} stayed safe "
                f"while the barley was finished."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is barley?",
            answer="Barley is a kind of grain. People can use it for food and feed, and it looks like little golden seeds.",
        ),
        QAItem(
            question="What is a quarter?",
            answer="A quarter is a coin worth twenty-five cents in the United States.",
        ),
        QAItem(
            question="What does scitter-scatter mean?",
            answer="Scitter-scatter is a quick, tiny sound, like little feet or a little object skimming over a floor.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", activity="barley_turn", prize="quarter", name="Mabel", gender="girl", parent="grandfather", trait="curious"),
    StoryParams(place="threshing_floor", activity="barley_turn", prize="quarter", name="Toby", gender="boy", parent="grandfather", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not honestly put the {prize.label} at risk here.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
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
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld: barley, a quarter, and a scittering sound.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandfather"])
    ap.add_argument("--name")
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or "grandfather"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:18} {act:14} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
