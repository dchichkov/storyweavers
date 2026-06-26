#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/clearance_valentine_kindness_lesson_learned_cautionary_animal.py
====================================================================================================================

A compact animal-story world about a child animal, a clearance shelf, and a
Valentine choice that teaches kindness with a cautionary turn.

Seed tale:
---
On the day before Valentine's Day, a little rabbit named Miso visited a tiny
shop with her mother. A bright clearance basket was full of leftover valentines
with shiny hearts and sparkly stickers. Miso wanted the fanciest one for her
friend, but the mother noticed one card was bent and another chocolate heart was
already cracking in the cold air.

Miso reached for the prettiest wrapper anyway, but her mother held up a paw and
said, "Slow down. Clearance treats can be fine, but only if we check them first.
A broken heart candy can make a sticky mess, and rushed choices can hurt more
than help."

Miso listened. She picked a simple card with a strong envelope, drew her own
little heart on it, and wrote a kind note inside. Her friend smiled when the
card was delivered, and Miso learned that kindness is better than glitter.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "rabbit", "hare", "cat", "mouse", "fox", "deer"}
        male = {"boy", "rabbit-boy", "hare-boy", "fox-boy"}
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
    indoors: bool = False
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
        return any(region in g.meters.get("covers", set()) for g in self.worn_items(actor))

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rush", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.label != "clearance valentine" or item.meters.get("fragile", 0.0) < THRESHOLD:
                continue
            sig = ("break", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["torn"] = item.meters.get("torn", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} bent at the edge.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("torn", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("mess", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["work"] = carer.meters.get("work", 0.0) + 1
        out.append(f"That could make extra work for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("break", "physical", _r_break), Rule("mess", "physical", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["rush"] = actor.meters.get("rush", 0.0) + 1
    actor.memes["want"] = actor.memes.get("want", 0.0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"torn": prize.meters.get("torn", 0.0) >= THRESHOLD}


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    friend = world.add(Entity(id="Friend", kind="character", type="boy", label="the friend"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    hero.meters["kindness"] = 0.0
    hero.memes["love"] = 1.0
    friend.memes["hope"] = 1.0

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved Valentine season.")
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place}.")
    world.say(f"At the shop, a bright clearance basket held leftover valentines and tiny treats.")
    world.say(f"{hero.id} wanted {hero.pronoun('possessive')} {prize.label} right away because {prize.phrase} looked special.")

    world.para()
    world.say(f"But the {parent_type if parent_type != 'mother' else 'mother'} lifted a paw and said,")
    world.say(f"\"Slow down. Clearance finds can be kind choices, but we should check them first.\"")
    if predict(world, hero, activity, prize.id)["torn"]:
        world.say(f"\"If you rush at the {activity.keyword}, your {prize.label} could get {activity.soil}, and that would not be kind to the person who gets it.\"")
    world.say(f"{hero.id} paused, then reached more carefully into the basket.")
    _do_activity(world, hero, activity, narrate=True)

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No reasonable repair choice exists for this story.")
    gear = world.add(Entity(id=gear_def.id, type="thing", label=gear_def.label, owner=hero.id))
    gear.meters["covers"] = set(gear_def.covers)  # for trace only
    world.say(f"{hero.id} chose {gear_def.label} instead of the fragile one and added a hand-drawn heart.")
    world.say(f"Then {hero.id} used {gear_def.prep} and wrote a warm note inside the card.")
    world.say(f"{gear_def.tail.capitalize()}, and the valentines stayed neat enough to give with a smile.")

    hero.meters["kindness"] += 1.0
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1.0
    world.say(f"When {hero.id} delivered the gift, {friend.label} smiled wide.")
    world.say(f"{hero.id} learned that kindness is not about the glittery thing you grab; it is about checking, choosing, and sharing carefully.")

    world.facts.update(
        hero=hero, parent=parent, friend=friend, prize=prize, activity=activity,
        setting=setting, gear=gear_def, conflict=True, resolved=True,
    )
    return world


SETTINGS = {
    "shop": Setting(place="the little corner shop", indoors=True, affords={"browse"}),
    "market": Setting(place="the busy market stall", indoors=False, affords={"browse"}),
    "school": Setting(place="the school craft table", indoors=True, affords={"make"}),
}

ACTIVITIES = {
    "browse": Activity(
        id="browse",
        verb="look through the clearance valentines",
        gerund="browsing the clearance valentines",
        rush="reach fast for the prettiest card",
        mess="bent",
        soil="bent and torn",
        zone={"torso"},
        keyword="clearance",
        tags={"clearance", "valentine"},
    ),
    "make": Activity(
        id="make",
        verb="make a valentine",
        gerund="making a valentine",
        rush="grab the glue too hard",
        mess="smudged",
        soil="smudged with glue",
        zone={"torso"},
        keyword="valentine",
        tags={"valentine", "kindness"},
    ),
}

PRIZES = {
    "card": Prize(label="valentine card", phrase="a bright valentine card", type="card", region="torso"),
    "treat": Prize(label="chocolate heart", phrase="a shiny chocolate heart", type="candy", region="torso", plural=False),
    "sticker": Prize(label="heart sticker pack", phrase="a tiny heart sticker pack", type="stickers", region="torso", plural=True),
}

GEAR = [
    Gear(
        id="envelope",
        label="a sturdy envelope",
        covers={"torso"},
        guards={"bent", "smudged"},
        prep="slip it into a sturdy envelope first",
        tail="they tucked the card into the sturdy envelope",
    ),
    Gear(
        id="box",
        label="a little box",
        covers={"torso"},
        guards={"bent"},
        prep="place it in a little box first",
        tail="they placed the card in a little box",
    ),
]

GIRL_NAMES = ["Miso", "Poppy", "Luna", "Nori", "Mina"]
BOY_NAMES = ["Taro", "Bun", "Kip", "Milo", "Tobi"]
TRAITS = ["gentle", "curious", "careful", "cheerful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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
    "clearance": [("What does clearance mean?",
                   "Clearance means a shop is selling leftover items for a lower price so the shelf can make room for new things.")],
    "valentine": [("What is a valentine?",
                  "A valentine is a card or note that says someone is cared about on Valentine's Day.")],
    "kindness": [("What is kindness?",
                  "Kindness means choosing to help, share, or speak gently so someone else feels safe and cared for.")],
    "lesson": [("What does it mean to learn a lesson?",
                 "Learning a lesson means understanding something important after an experience, so you can do better next time.")],
    "cautionary": [("What is a cautionary story?",
                     "A cautionary story is a story that warns about a mistake and shows a safer, wiser choice.")],
}
KNOWLEDGE_ORDER = ["clearance", "valentine", "kindness", "lesson", "cautionary"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short animal story for a little child about "{act.keyword}" and a surprise from a clearance shelf.',
        f"Tell a gentle cautionary story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Write a Valentine's Day story about kindness, a clear choice, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, friend, prize, act = f["hero"], f["parent"], f["friend"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id}'s {parent.label} tell {hero.id} to slow down at {world.setting.place}?",
            answer=f"{parent.label.capitalize()} told {hero.id} to slow down because the clearance valentines needed checking first, and a rushed choice could make {prize.label} end up {act.soil}.",
        ),
        QAItem(
            question=f"What did {hero.id} choose instead of the fragile {prize.label}?",
            answer=f"{hero.id} chose a sturdier way to give the Valentine, then added a hand-drawn heart and a kind note.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end of the story?",
            answer=f"{hero.id} learned that kindness means checking carefully and choosing what will truly help the friend, not just what looks sparkly.",
        ),
        QAItem(
            question=f"Who smiled after receiving the Valentine?",
            answer=f"{friend.label} smiled when {hero.id} delivered the card.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("kindness")
    tags.add("lesson")
    tags.add("cautionary")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shop", activity="browse", prize="card", name="Miso", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="market", activity="browse", prize="treat", name="Tobi", gender="boy", parent="father", trait="curious"),
    StoryParams(place="school", activity="make", prize="sticker", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not reasonably endanger {prize.label}, so the cautionary turn would be weak.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s choice here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
needs_gear(A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), gear(G).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), needs_gear(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
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
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about clearance valentines, kindness, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
            print(f"  {place:10} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
