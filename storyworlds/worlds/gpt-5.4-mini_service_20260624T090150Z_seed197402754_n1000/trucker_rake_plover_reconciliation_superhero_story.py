#!/usr/bin/env python3
"""
A small superhero storyworld about a trucker, a rake, and a plover, built around
reconciliation after a messy rescue.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "trucker"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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
    weather: str
    keyword: str = ""
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
        self.weather: str = ""
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in {"wet", "muddy"}:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone or item.worn_by != actor.id:
                    continue
                if any(item.region in g.covers and g.label for g in world.worn_items(actor)):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("hurt", 0.0) < THRESHOLD:
        return out
    if friend.memes.get("sorry", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hurt"] = 0.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    friend.memes["peace"] = friend.memes.get("peace", 0.0) + 1
    out.append("They made up and the grumpy feeling slipped away.")
    return out


CAUSAL_RULES = [(_r_soak), (_r_reconcile)]


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
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a brave superhero trucker who watched the road and the sky.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} because it felt like helping the whole town.")


def buys(world: World, ally: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One bright morning, {ally.label} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.it()} proudly, as if it were part of the uniform of hero work.")


def arrive(world: World, hero: Entity, ally: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {ally.label} went to {world.setting.place}.")
    world.say(f"The {world.setting.place} was ready for trouble, and {activity.keyword} looked wild ahead.")


def wants(world: World, hero: Entity, ally: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} heart beat fast with worry.")


def warn(world: World, ally: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    world.say(
        f'"If you rush in, your {prize.label} will get {activity.soil}," '
        f'{ally.pronoun("subject")} said. "Let us choose a safer way."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["anger"] = hero.memes.get("anger", 0.0) + 1
    world.say(f"{hero.id} frowned and tried to {activity.rush}, but the air felt heavy.")


def reconcile(world: World, ally: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=ally.id,
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(f'{ally.id} lifted a calm hand. "How about we {gear_def.prep} and work together?"')
    world.say(f"{hero.id} looked at the {prize.label}, then at the gear, and nodded.")
    hero.memes["sorry"] = hero.memes.get("sorry", 0.0) + 1
    propagate(world, narrate=True)
    return gear_def


def accept(world: World, ally: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["hurt"] = 0.0
    world.say(
        f"{hero.id} smiled, and the two of them used {gear_def.label}. "
        f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the day felt heroic again."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Tara",
    hero_type: str = "trucker",
    parent_type: str = "helper",
) -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    ally = world.add(Entity(id="Ally", kind="character", type=parent_type, label="the city helper"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=ally.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts["hero"] = hero
    world.facts["friend"] = ally
    world.facts["prize"] = prize
    world.facts["activity"] = activity
    world.facts["setting"] = setting
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, ally, hero, prize)
    loves_prize(world, hero, prize)
    world.para()
    arrive(world, hero, ally, activity)
    wants(world, hero, ally, activity)
    warn(world, ally, hero, activity, prize)
    defies(world, hero, activity)
    world.para()
    gear_def = reconcile(world, ally, hero, activity, prize)
    if gear_def:
        accept(world, ally, hero, activity, prize, gear_def)
    world.facts["gear"] = gear_def
    return world


SETTINGS = {
    "harbor": Setting(place="the harbor", indoor=False, affords={"rake"}),
    "yard": Setting(place="the yard", indoor=False, affords={"rake"}),
    "roof": Setting(place="the rooftop garden", indoor=False, affords={"plover"}),
}

ACTIVITIES = {
    "rake": Activity(
        id="rake",
        verb="rake the leaves",
        gerund="raking leaves",
        rush="rush through the leaf pile",
        mess="scratched",
        soil="scratched and dusty",
        zone={"hands", "arms"},
        weather="windy",
        keyword="rake",
        tags={"leaf", "yard"},
    ),
    "plover": Activity(
        id="plover",
        verb="help the plover nest",
        gerund="guarding the plover nest",
        rush="dash toward the nest",
        mess="muddy",
        soil="muddy and upset",
        zone={"hands", "arms", "torso"},
        weather="windy",
        keyword="plover",
        tags={"bird", "nest"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a red cape", type="cape", region="torso"),
    "gloves": Prize(label="gloves", phrase="shiny rescue gloves", type="gloves", region="hands", plural=True),
    "boots": Prize(label="boots", phrase="blue hero boots", type="boots", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="workgloves",
        label="work gloves",
        covers={"hands", "arms"},
        guards={"scratched"},
        prep="put on work gloves first",
        tail="slipped on the work gloves",
        plural=True,
    ),
    Gear(
        id="raincloak",
        label="a rain cloak",
        covers={"torso", "arms"},
        guards={"muddy"},
        prep="wear a rain cloak first",
        tail="buttoned up the rain cloak",
    ),
    Gear(
        id="highboots",
        label="high boots",
        covers={"feet"},
        guards={"muddy"},
        prep="put on high boots first",
        tail="pulled on the high boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Tara", "Mina", "Juno", "Lena"]
BOY_NAMES = ["Rex", "Owen", "Milo", "Cal"]
TRAITS = ["brave", "kind", "quick", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rake": [("What is a rake?", "A rake is a tool with teeth that helps gather leaves or grass into a pile.")],
    "plover": [("What is a plover?", "A plover is a small bird that often lives near water, sand, or open ground.")],
    "cape": [("What is a cape?", "A cape is a piece of clothing that hangs from the shoulders like a superhero's cloak.")],
    "gloves": [("What are gloves for?", "Gloves help cover your hands and keep them safer or cleaner while you work.")],
    "boots": [("What are boots for?", "Boots help protect your feet when the ground is wet, rough, or messy.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ally, act, prize = f["hero"], f["friend"], f["activity"], f["prize"]
    return [
        f'Write a short superhero story for a child about a {hero.type} named {hero.id} who wants to {act.verb}.',
        f"Tell a story where {hero.id} and {ally.label} face a problem with {prize.phrase} and find a calm reconciliation.",
        f'Write a gentle heroic story that includes the word "{act.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id}, a brave {hero.type}, and {ally.label}, who helps the town stay safe.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, which was the big action of the story.",
        ),
        QAItem(
            question=f"Why did {ally.label} worry about the {prize.label}?",
            answer=f"{ally.label} worried because if {hero.id} rushed ahead, the {prize.label} would get {act.soil}.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did the two friends solve the problem?",
            answer=f"They used {gear.label} so {hero.id} could keep helping without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm after the reconciliation, and the team felt strong again.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in world.facts["activity"].tags | {world.facts["prize"].label}:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", activity="rake", prize="gloves", name="Tara", gender="girl", trait="brave"),
    StoryParams(place="roof", activity="plover", prize="cape", name="Rex", gender="boy", trait="steady"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the prize is not really at risk in this action.)"
    return "(No story: no gear in this world can fairly solve that problem.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
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
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: trucker, rake, plover, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--trait")
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender)
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
        import asp

        model = asp.one_model(asp_program("#show valid/3.\n#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid"))))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
