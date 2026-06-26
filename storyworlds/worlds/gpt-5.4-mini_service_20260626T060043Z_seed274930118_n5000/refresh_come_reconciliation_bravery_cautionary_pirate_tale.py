#!/usr/bin/env python3
"""
A pirate-tale story world about bold sailing, cautionary warnings, and
reconciliation after a near-disaster.

The seed premise:
- A small pirate crew wants to rush out to sea.
- A careful captain sees the danger and warns them.
- The brave choice is not reckless: they refresh the ship, mend the sails,
  and come back together with a safer plan.
- A rival boat becomes an ally by the end.

The generated stories use a tiny simulated world with physical meters and
emotional memes, plus an inline ASP twin for the reasonableness gate.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
        for k in ["damage", "wet", "tired", "safe", "fresh"]:
            self.meters.setdefault(k, 0.0)
        for k in ["bravery", "caution", "joy", "fear", "relief", "grudge", "friendship"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sea: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    damage: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["damage"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} took a hard beating.")
    return out


def _r_refresh(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["damage"] < THRESHOLD:
            continue
        sig = ("refresh", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["fresh"] += 1
        item.meters["damage"] = max(0.0, item.meters["damage"] - 1)
        out.append(f"A good refresh made {item.label} look ready for another voyage.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["grudge"] < THRESHOLD or actor.memes["friendship"] < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["grudge"] = 0.0
        actor.memes["relief"] += 1
        out.append(f"Old anger slipped away, and the crew came together again.")
    return out


CAUSAL_RULES = [
    _r_damage,
    _r_refresh,
    _r_reconcile,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def danger_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "damaged": prize.meters["damage"] >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["damage"] += 1
    actor.memes["bravery"] += 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"{setting.place.capitalize()} sat by {setting.sea}, with the wind tugging at every rope."


def hero_intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "little"), "bold")
    return f"{hero.id} was a little {trait} pirate who loved the open water."


def love_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because {activity.keyword} made the whole day feel alive."
    )


def arrive(world: World, hero: Entity, mate: Entity, activity: Activity) -> None:
    world.say(
        f"One salt-bright day, {hero.id} and {hero.pronoun('possessive')} {mate.label} came to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, mate: Entity, activity: Activity) -> None:
    hero.memes["caution"] += 0.0
    world.say(f"{hero.id} wanted to {activity.verb}, but the tide looked mean.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_damage(world, hero, activity, prize.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(
        f'"If you go now, your {prize.label} will get {activity.damage}," '
        f"{captain.pronoun('possessive')} {captain.label} said. "
        f'"Come back and choose the careful way."'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} frowned, but the brave thought in {hero.pronoun('possessive')} chest would not sink.")
    world.say(f"{hero.pronoun().capitalize()} still tried to go near the waves.")


def hold_back(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["grudge"] += 1
    world.say(
        f"Then {captain.id} stepped in front of the spray and held up a steady hand."
    )
    world.say(
        f'"Bravery can wait for a safe moment," {captain.pronoun("possessive")} {captain.label} said.'
    )


def compromise(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=captain.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_damage(world, hero, activity, prize.id)["damaged"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{captain.id} nodded toward the {prize.label}. "How about we {gear_def.prep} and then go?"'
    )
    return gear_def


def accept(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["friendship"] += 1
    hero.memes["grudge"] = 0.0
    hero.memes["relief"] += 1
    world.say(f"{hero.id}'s face softened, and {hero.pronoun()} hugged {hero.pronoun('possessive')} captain.")
    world.say(
        f'"Aye," {hero.pronoun()} said. "{gear_def.tail}."'
    )
    world.say(
        f"Soon the crew was {activity.gerund}, {prize.label} stayed safe, and even the rival ship waved from afar."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "bold", "stubborn"]))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, label="captain"))
    rival = world.add(Entity(id="Rival", kind="character", type="pirate", label="old rival"))
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
    rival.memes["grudge"] += 1

    world.say(hero_intro(hero))
    love_activity(world, hero, activity)
    world.say(f"Their treasure was {prize.phrase}.")
    world.para()
    arrive(world, hero, captain, activity)
    wants(world, hero, captain, activity)
    warn(world, captain, hero, activity, prize)
    defy(world, hero, activity)
    hold_back(world, captain, hero)
    world.para()
    gear_def = compromise(world, captain, hero, activity, prize)
    if gear_def:
        accept(world, captain, hero, activity, prize, gear_def)
    rival.memes["friendship"] += 1
    propagate(world, narrate=True)
    world.say(
        f"In the end, the rival came to share water and stories, and the harbor felt brighter than before."
    )

    world.facts.update(
        hero=hero,
        captain=captain,
        rival=rival,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
        warned=True,
    )
    return world


SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the dark blue sea", affords={"storm", "reef", "sail"}),
    "cove": Setting(place="the cove", sea="the silver sea", affords={"reef", "sail"}),
    "dock": Setting(place="the dock", sea="the choppy bay", affords={"storm", "sail"}),
}

ACTIVITIES = {
    "storm": Activity(
        id="storm",
        verb="sail into the storm",
        gerund="sailing through the storm",
        rush="rush into the storm",
        hazard="wet",
        damage="soaked and battered",
        zone={"torso"},
        keyword="storm",
        tags={"storm", "wet"},
    ),
    "reef": Activity(
        id="reef",
        verb="cut past the reef",
        gerund="cutting past the reef",
        rush="dash toward the reef",
        hazard="scratched",
        damage="scratched and torn",
        zone={"torso"},
        keyword="reef",
        tags={"reef", "sharp"},
    ),
    "sail": Activity(
        id="sail",
        verb="hoist the sail",
        gerund="hoisting the sail",
        rush="pull the sail hard",
        hazard="wet",
        damage="damp and heavy",
        zone={"torso"},
        keyword="sail",
        tags={"sail", "wet"},
    ),
}

PRIZES = {
    "map": Prize("map", "a hand-drawn treasure map", "map", "torso"),
    "sail": Prize("sail", "bright red sailcloth", "sail", "torso"),
    "coat": Prize("coat", "a fine captain's coat", "coat", "torso"),
}

GEAR = [
    Gear("oilskin", "an oilskin coat", {"torso"}, {"wet"}, "pull on an oilskin coat first", "put on the oilskin coat"),
    Gear("patch", "a patched sail cover", {"torso"}, {"scratched"}, "wrap the sail in a patched cover", "wrapped the sail in a patched cover"),
    Gear("wrap", "a rain wrap", {"torso"}, {"wet", "scratched"}, "bundle up in a rain wrap", "bundled up in a rain wrap"),
]

NAMES = ["Mira", "Finn", "Jory", "Lena", "Pip", "Nell"]
TRAITS = ["brave", "spry", "cheeky", "quick", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if danger_at_risk(act, prize) and select_gear(act, prize):
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


KNOWLEDGE = {
    "storm": [("What is a storm?", "A storm is rough weather with strong wind, rain, and big waves.")],
    "reef": [("What is a reef?", "A reef is a rocky place under the water where boats have to be careful.")],
    "wet": [("Why do wet clothes feel heavy?", "Wet clothes feel heavy because water soaks into the cloth and adds weight.")],
    "scratched": [("What scratches wood?", "Sharp rocks, rough boards, and hard bumps can scratch wood and paint.")],
    "oilskin": [("What is an oilskin coat?", "An oilskin coat is a coat treated to help keep water out.")],
    "map": [("What is a treasure map?", "A treasure map is a picture that shows where someone thinks treasure might be hidden.")],
}
KNOWLEDGE_ORDER = ["storm", "reef", "wet", "scratched", "oilskin", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a short pirate tale for a child that includes the word "{act.keyword}" and the word "refresh".',
        f"Tell a cautionary pirate story where {f['hero'].id} wants to {act.verb}, but the captain says come back first.",
        f"Write a brave but careful sea adventure about a crew that chooses a safer way and then reconciles after the warning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, act = f["hero"], f["captain"], f["prize"], f["activity"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb}, but the captain worried about {prize.label}.",
        ),
        QAItem(
            question=f"Why did the captain warn {hero.id}?",
            answer=f"The captain warned {hero.id} because going into the {act.keyword} could leave {prize.label} {act.damage}.",
        ),
        QAItem(
            question=f"What did the crew do instead of rushing ahead?",
            answer=f"They chose to {gear.prep} and then go together, which was the careful choice.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the story end after the warning?",
            answer=f"{hero.id} listened, the crew stayed safe, and the old grudge faded into reconciliation.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "storm", "map", "Mira", "girl", "captain", "bold"),
    StoryParams("cove", "reef", "sail", "Finn", "boy", "captain", "brave"),
    StoryParams("dock", "sail", "coat", "Jory", "boy", "captain", "spry"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not danger_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not threaten the {prize.label}.)"
    return f"(No story: no gear in this world can reasonably protect the {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok}; this world does not constrain gender strongly.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), wears_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), hazard_of(A,M), covers(G,R), wears_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), gender_ok(Gender,P).
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
        lines.append(asp.fact("hazard_of", aid, a.hazard))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears_on", pid, p.region))
        for g in p.genders:
            lines.append(asp.fact("gender_ok", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with caution and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (danger_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "pirate" if params.gender == "boy" else "captain", params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
