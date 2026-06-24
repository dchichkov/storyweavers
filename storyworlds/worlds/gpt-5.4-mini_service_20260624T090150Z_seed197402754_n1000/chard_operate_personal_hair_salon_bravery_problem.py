#!/usr/bin/env python3
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Salon:
    place: str = "the hair salon"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
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


class World:
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        w = World(self.salon)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


THRESHOLD = 1.0
MESS_KINDS = {"wet", "painted", "sticky"}
REGIONS = {"feet", "torso", "hands"}


def _m(x: float) -> float:
    return 1.0 if x >= THRESHOLD else 0.0


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if not any(_m(v) for k, v in actor.meters.items() if k in MESS_KINDS):
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meter(item, "dirty", 1.0)
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


def _r_burden(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("burden", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        _add_meter(carer, "workload", 1.0)
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [_r_soil, _r_burden]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> bool:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("dirty", 0.0) >= THRESHOLD


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.salon.affords:
        return
    world.zone = set(action.zone)
    _add_meter(actor, action.mess, 1.0)
    _add_meme(actor, "joy", 1.0)
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"In the old days of the hair salon, {hero.id} was a little {hero.type} "
        f"with a brave heart and a personal secret: {hero.id} listened closely when the mirrors spoke."
    )


def love_world(world: World, hero: Entity, action: Action) -> None:
    _add_meme(hero, "love", 1.0)
    world.say(
        f"{hero.pronoun().capitalize()} loved to {action.verb}, because even the combs seemed to sing when {hero.id} was near."
    )


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One bright morning, {hero.id}'s {parent.label} brought home {hero.pronoun('object')} {prize.phrase}."
    )


def prize_love(world: World, hero: Entity, prize: Entity) -> None:
    _add_meme(hero, "pride", 1.0)
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} like a crown.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"Then one day, {hero.id} and {hero.pronoun('possessive')} {parent.label} came to {world.salon.place}.")
    world.say("The salon smelled of soap, warm towels, and stories older than the street outside.")


def want(world: World, hero: Entity, action: Action) -> None:
    _add_meme(hero, "desire", 1.0)
    world.say(f"{hero.id} wanted to {action.verb}, but the wish was bigger than small hands could hide.")


def warn(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    if not prize_at_risk(action, prize):
        return False
    if not predict_mess(world, hero, action, prize.id):
        return False
    world.facts["predicted_soil"] = action.soil
    world.say(
        f'"If you {action.verb}, your {prize.label} will get {action.soil}," '
        f"{hero.pronoun('possessive')} {parent.label} said. "
        f'"We must choose with wisdom."'
    )
    return True


def defy(world: World, hero: Entity, action: Action) -> None:
    _add_meme(hero, "bravery", 1.0)
    _add_meme(hero, "defiance", 1.0)
    world.say(f"But {hero.id}'s bravery blazed, and {hero.pronoun()} tried to {action.rush}.")


def ask_help(world: World, parent: Entity, hero: Entity) -> None:
    _add_meme(hero, "uncertain", 1.0)
    world.say(f"At once, {hero.pronoun('possessive')} {parent.label} held up a steady hand, not to punish, but to guide.")


def compromise(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Gear]:
    gear = select_gear(action, prize)
    if gear is None:
        return None
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    item.worn_by = hero.id
    if predict_mess(world, hero, action, prize.id):
        del world.entities[item.id]
        return None
    world.say(
        f"{parent.label.capitalize()} smiled and said, "
        f'"How about we {gear.prep} and then {action.verb}?"'
    )
    return item


def resolve(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity, gear: Gear) -> None:
    _add_meme(hero, "bravery", 1.0)
    _add_meme(hero, "joy", 1.0)
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, and the storm inside {hero.pronoun('possessive')} chest turned gentle."
    )
    world.say(
        f"Together they {gear.tail}. Soon {hero.id} was {action.gerund}, {prize.label} stayed clean, and the mirrors shone like moon water."
    )


def tell(salon: Salon, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(salon)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    intro(world, hero)
    love_world(world, hero, action)
    buy_prize(world, parent, hero, prize)
    prize_love(world, hero, prize)
    world.para()
    arrive(world, hero, parent)
    want(world, hero, action)
    warn(world, parent, hero, action, prize)
    defy(world, hero, action)
    ask_help(world, parent, hero)
    world.para()
    gear = compromise(world, parent, hero, action, prize)
    if gear:
        resolve(world, parent, hero, action, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, gear=gear,
                       resolved=gear is not None, salon=salon)
    return world


SETTINGS = {
    "salon": Salon(place="the hair salon", affords={"trim", "dye", "curl"}),
}

ACTIONS = {
    "trim": Action(
        id="trim",
        verb="get a trim",
        gerund="getting a trim",
        rush="dart toward the scissors",
        mess="sticky",
        soil="snipped and sticky",
        zone={"hands", "torso"},
        keyword="trim",
        tags={"hair", "problem solving"},
    ),
    "dye": Action(
        id="dye",
        verb="help with dye",
        gerund="helping with dye",
        rush="reach for the dye bowls",
        mess="painted",
        soil="brightly stained",
        zone={"hands", "torso"},
        keyword="dye",
        tags={"hair", "color"},
    ),
    "curl": Action(
        id="curl",
        verb="use the curling iron",
        gerund="using the curling iron",
        rush="run to the hot chair",
        mess="wet",
        soil="damp and tangled",
        zone={"hands", "torso"},
        keyword="curl",
        tags={"heat", "hair"},
    ),
}

PRIZES = {
    "robe": Prize(label="robe", phrase="a soft white robe", type="robe", region="torso", genders={"girl", "boy"}),
    "cape": Prize(label="cape", phrase="a shining salon cape", type="cape", region="torso", genders={"girl", "boy"}),
    "braid": Prize(label="braid", phrase="a careful braided ribbon", type="braid", region="hands", genders={"girl", "boy"}),
}

GEAR = [
    Gear(id="cover", label="a cloth cover", covers={"torso"}, guards={"painted", "sticky"}, prep="wrap the cloth cover around you", tail="wrapped the cloth cover around them"),
    Gear(id="gloves", label="thin gloves", covers={"hands"}, guards={"painted", "sticky", "wet"}, prep="put on thin gloves first", tail="put on the thin gloves"),
    Gear(id="apron", label="a salon apron", covers={"torso", "hands"}, guards={"painted", "sticky", "wet"}, prep="put on a salon apron first", tail="fastened the salon apron"),
]

NAMES = ["Ari", "Mira", "Noa", "Sage", "Lina", "Ravi"]
TRAITS = ["brave", "thoughtful", "curious", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, salon in SETTINGS.items():
        for aid in salon.affords:
            act = ACTIONS[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, action, prize = f["hero"], f["parent"], f["action"], f["prize"]
    return [
        f'Write a mythic story in a hair salon about "{action.keyword}" and a child named {hero.id}.',
        f"Tell a gentle tale where {hero.id} wants to {action.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f'Create a myth-like story of bravery and problem solving in {world.salon.place}, using the word "{action.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, action, prize = f["hero"], f["parent"], f["action"], f["prize"]
    qas = [
        QAItem(
            question=f"Who was the brave child at the hair salon?",
            answer=f"It was {hero.id}, a little {hero.type} who loved {action.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the worry began?",
            answer=f"{hero.id} wanted to {action.verb} in {world.salon.place}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label.capitalize()} worried that the {prize.label} would get {action.soil} if {hero.id} went ahead without help.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qas.append(QAItem(
            question="How did the family solve the problem?",
            answer=f"They chose {gear.label}, which helped {hero.id} {action.verb} while the {prize.label} stayed clean.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a hair salon?", answer="A hair salon is a place where people wash, cut, comb, and style hair."),
        QAItem(question="What does bravery mean?", answer="Bravery means doing something hard or scary while still trying your best."),
        QAItem(question="What is problem solving?", answer="Problem solving means finding a smart way to fix a hard situation."),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic hair-salon story world about bravery and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        act, pr = ACTIONS[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("No story: that activity does not create a real problem that this salon can solve.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.activity], PRIZES[params.prize], params.name, "girl" if params.gender == "girl" else "boy", [params.trait], params.parent)
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
    StoryParams(place="salon", activity="trim", prize="robe", name="Chard", gender="boy", parent="mother", trait="brave"),
    StoryParams(place="salon", activity="dye", prize="cape", name="Mira", gender="girl", parent="father", trait="thoughtful"),
    StoryParams(place="salon", activity="curl", prize="braid", name="Noa", gender="boy", parent="mother", trait="curious"),
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
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
