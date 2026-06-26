#!/usr/bin/env python3
"""
A standalone story world for a small pirate-tale domain.

Seed premise:
- A bold young pirate wants to race a little ship called the Twist.
- A thunderstorm threatens the sail and a special flag.
- A careful grown-up pirate warns first, then offers a safer way to join the fun.

The story keeps close to pirate-tale rhythms: ship, sea, crew, storm, rope,
sail, deck, and a cheerful turn toward a safer plan.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "torn": 0.0, "tilt": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "pride": 0.0, "warning": 0.0, "stubborn": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the harbor"
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
    weather: str
    keyword: str = ""


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
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return any(it.protective and region in it.covers for it in self.worn_items(actor))

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.weather = self.weather
        w.fired = set(self.fired)
        return w


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["torn"] += 1
            out.append(f"{actor.id}'s {item.label} got wet and rough in the spray.")
    return out


def _r_tidework(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["torn"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("fix", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_tidework,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"sail", "twist"}),
    "cove": Setting(place="the cove", affords={"sail", "twist"}),
    "open_sea": Setting(place="the open sea", affords={"sail", "twist"}),
}

ACTIVITIES = {
    "sail": Activity(
        id="sail",
        verb="sail into the wind",
        gerund="sailing into the wind",
        rush="rush at the sail",
        mess="wet",
        soil="soaked and salty",
        zone={"torso"},
        weather="storm",
        keyword="thunder",
    ),
    "twist": Activity(
        id="twist",
        verb="twist the rope",
        gerund="twisting the rope",
        rush="grab the rope and yank hard",
        mess="wet",
        soil="slippery with spray",
        zone={"hands"},
        weather="storm",
        keyword="twist",
    ),
}

PRIZES = {
    "flag": Prize(
        label="flag",
        phrase="a bright bold republican flag",
        type="flag",
        region="torso",
    ),
    "hat": Prize(
        label="hat",
        phrase="a bold red captain's hat",
        type="hat",
        region="head",
    ),
    "boots": Prize(
        label="boots",
        phrase="strong sea boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="oilcloth",
        label="an oilcloth cloak",
        covers={"torso"},
        guards={"wet"},
        prep="put on an oilcloth cloak first",
        tail="pulled on the oilcloth cloak",
    ),
    Gear(
        id="gripgloves",
        label="grip gloves",
        covers={"hands"},
        guards={"wet"},
        prep="tie on grip gloves first",
        tail="tied on the grip gloves",
        plural=True,
    ),
    Gear(
        id="seahood",
        label="a sea hood",
        covers={"head"},
        guards={"wet"},
        prep="wear a sea hood first",
        tail="wore the sea hood",
    ),
]

NAMES = ["Mara", "Finn", "Nell", "Bram", "Ivy", "Jory", "Pip", "Sage"]
TITLES = ["bold", "cheerful", "quick", "brave", "lively"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.region == "torso" and activity.id == "sail"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} would not truly threaten {prize.label} in this setup.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
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


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = ACTIVITIES[act_id]
            for pr_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    out.append((place, act_id, pr_id))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    seed: Optional[int] = None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["wet"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["torn"] >= THRESHOLD}


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=params.name, kind="character", type="pirate"))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["pride"] += 1
    world.say(f"{hero.id} was a {random.choice(TITLES)} pirate with a grin like a gull over water.")
    world.say(f"{hero.id} loved the ship called Twist and the roar of thunder over the waves.")
    world.say(f"The crew had given {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore it like treasure.")

    world.para()
    world.say(f"One stormy day, {hero.id} and {hero.pronoun('possessive')} captain went to {world.setting.place}.")
    world.say(f"Gray clouds rolled in, and the thunder sounded like drums in the sky.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} captain lifted a hand and looked hard at the sky.")

    if predict(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"You will get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} captain said.')
        hero.memes["warning"] += 1

    hero.memes["stubborn"] += 1
    world.say(f"{hero.id} tried to {activity.rush}, but the sea wind shoved back.")

    world.para()
    gear = select_gear(activity, prize)
    if gear:
        worn = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
            owner=hero.id,
            caretaker=captain.id,
        ))
        worn.worn_by = hero.id
        world.say(f"{hero.pronoun('possessive').capitalize()} captain smiled and said, \"How about we {gear.prep} and then {activity.verb}?\"")
        hero.memes["stubborn"] = 0.0
        hero.memes["calm"] += 1
        hero.memes["joy"] += 1
        world.say(f"{hero.id} nodded, and they {gear.tail}.")
        world.say(f"Then {hero.id} was {activity.gerund}, the {prize.label} stayed safe, and the Twist cut through the thunder like a brave little arrow.")
    else:
        world.say(f"{hero.id} and {hero.pronoun('possessive')} captain waited out the worst of the storm on the deck.")
        world.say(f"When the thunder drifted off, the sea was calmer, and the {prize.label} still shone bright.")

    world.facts.update(hero=hero, captain=captain, prize=prize, activity=activity, gear=gear, resolved=gear is not None)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    pr = f["prize"]
    return [
        f'Write a short pirate story for a child that includes "{act.keyword}" and the word "thunder".',
        f"Tell a gentle sea story about {hero.id} wanting to {act.verb} while a captain worries about {pr.label}.",
        f'Write a story with the ship Twist, a bold crew, and a safe compromise before the storm gets rough.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    out = [
        QAItem(
            question=f"What did {hero.id} want to do on the stormy day?",
            answer=f"{hero.id} wanted to {act.verb} on the ship Twist while thunder boomed overhead.",
        ),
        QAItem(
            question=f"Why did {captain.label} worry about {prize.label}?",
            answer=f"{captain.label} worried because the storm and spray could ruin the {prize.label}.",
        ),
    ]
    if gear:
        out.append(QAItem(
            question=f"How did the crew keep the {prize.label} safe?",
            answer=f"They put on {gear.label} first, so {hero.id} could keep playing without ruining the {prize.label}.",
        ))
        out.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm, because the safer plan let the fun keep going on the Twist.",
        ))
    return out


KNOWLEDGE = {
    "thunder": [("What is thunder?", "Thunder is the loud sound that comes after lightning lights up the sky.")],
    "pirate": [("What is a pirate ship?", "A pirate ship is a boat that sails on the sea and carries a pirate crew.")],
    "flag": [("What is a flag?", "A flag is a piece of cloth that shows a group, place, or crew.")],
    "rope": [("What is rope for?", "Rope can tie things, pull things, and help hold a sail or a load steady.")],
    "storm": [("What is a storm?", "A storm is rough weather with strong wind, rain, thunder, or lightning.")],
    "twist": [("What does it mean to twist something?", "To twist something means to turn it around and around.")],
    "wet": [("Why do wet things feel slippery?", "Wet things can feel slippery because water makes surfaces harder to grip.")],
}


def world_qa(world: World) -> list[QAItem]:
    tags = {world.facts["activity"].keyword, "thunder", "pirate", "rope", "storm", "twist", "wet"}
    out: list[QAItem] = []
    for tag in ["thunder", "pirate", "flag", "rope", "storm", "twist", "wet"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"meters={meters}" if meters else "", f"memes={memes}" if memes else ""]
        bits = [b for b in bits if b]
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate Tale storyworld with a storm, a Twist, and a safer compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("harbor", "sail", "flag", "Mara"),
            StoryParams("cove", "twist", "boots", "Finn"),
        ]:
            samples.append(generate(p))
    else:
        seen = set()
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
