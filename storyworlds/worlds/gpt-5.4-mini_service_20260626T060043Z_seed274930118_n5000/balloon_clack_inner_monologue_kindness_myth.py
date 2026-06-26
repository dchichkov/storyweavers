#!/usr/bin/env python3
"""
storyworlds/worlds/balloon_clack_inner_monologue_kindness_myth.py
=================================================================

A small mythic story world about a child, a balloon, a clack in the wind,
an inner monologue, and a kindness that changes the ending.

Seed tale premise:
---
In an old village near a bright shrine, a child loved a blue balloon that
shone like a piece of sky. One windy afternoon, the balloon clacked against
the stone gate of the shrine, and the child heard a stern little voice inside
the head: keep it close, do not let it go, do not be foolish. But when a
younger child looked on in wonder, the first child chose kindness instead and
found a gentle way to share the balloon without letting it burst.

The world models:
- physical meters: breeze, height, tension, safety, wear
- emotional memes: wonder, worry, pride, kindness, shame, resolve, patience

Narrative instruments:
- inner monologue
- kindness
- mythic setting and cadence

This file follows the Storyweavers contract: it is standalone, includes a
Python reasonableness gate and inline ASP twin, emits ASP facts, and supports
default generation, QA, JSON, trace, all, and verify modes.
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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.kind == "character":
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


SETTING = Setting(place="the shrine courtyard", indoor=False, affords={"watch", "walk", "dance"})

ACTIVITIES = {
    "watch": Activity(
        id="watch",
        verb="watch the sky",
        gerund="watching the sky",
        rush="run toward the gate",
        mess="restless",
        soil="too excited",
        zone={"head"},
        weather="windy",
        keyword="sky",
        tags={"wind", "watch"},
    ),
    "walk": Activity(
        id="walk",
        verb="walk by the stone gate",
        gerund="walking by the stone gate",
        rush="hurry past the gate",
        mess="wind-tossed",
        soil="jostled by the wind",
        zone={"hand", "torso"},
        weather="windy",
        keyword="gate",
        tags={"wind", "gate"},
    ),
    "dance": Activity(
        id="dance",
        verb="dance with the balloon",
        gerund="dancing with a balloon",
        rush="spin near the stone steps",
        mess="wind-tossed",
        soil="sent into the rocks",
        zone={"hand", "torso"},
        weather="windy",
        keyword="balloon",
        tags={"wind", "balloon"},
    ),
}

PRIZES = {
    "balloon": Prize(
        label="balloon",
        phrase="a bright blue balloon",
        type="balloon",
        region="hand",
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a red ribbon tied to the wrist",
        type="ribbon",
        region="hand",
    ),
}

GEAR = [
    Gear(
        id="soft_cloth",
        label="a soft cloth wrap",
        covers={"hand"},
        guards={"wind-tossed", "restless"},
        prep="wrap the string in a soft cloth first",
        tail="walked more slowly beside the gate with the cloth on the string",
    ),
    Gear(
        id="quiet_path",
        label="the quiet path",
        covers={"hand", "torso"},
        guards={"wind-tossed"},
        prep="take the quiet path around the shrine",
        tail="went around the gate where the wind was gentler",
    ),
]

GIRL_NAMES = ["Asha", "Mira", "Lina", "Nia", "Suri", "Kira"]
BOY_NAMES = ["Arun", "Tariq", "Mika", "Ravi", "Oren", "Sage"]
TRAITS = ["curious", "gentle", "spirited", "careful", "bright", "hopeful"]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS_REGISTRY.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic balloon story world.")
    ap.add_argument("--place", choices=SETTINGS_REGISTRY)
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not truly threaten a {prize.label} here.)"
    return f"(No story: no gear in this world can reasonably protect a {prize.label} from {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: a {args.prize} is not a typical {args.gender}'s item here.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": bool(prize.meters.get("dirty", 0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["restless"] = actor.meters.get("restless", 0) + 1
    actor.memes["wonder"] = actor.memes.get("wonder", 0) + 1
    if narrate:
        world.say(f"The wind moved through {world.setting.place}, and {actor.id} felt it answer back.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Asha", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"wonder": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id, region=prize_cfg.region))
    younger = world.add(Entity(id="Younger", kind="character", type="boy", label="the smaller child"))

    world.say(f"At {setting.place}, {hero.id} was a little {hero_traits[0] if hero_traits else 'curious'} {hero_type} who loved {prize.label}s that shone like captured sky.")
    world.say(f"{hero.id} had {prize.phrase}, and the wind made it dance above {hero.pronoun('possessive')} hand.")
    world.para()
    world.say(f"One windy day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word if hasattr(parent, 'label_word') else 'parent'} came to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the stone gate stood near, and every breath of wind made the string tug and clack.")
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"Inside {hero.id}'s head, a small inner voice whispered, 'Keep it close. Do not lose the balloon. Do not be laughed at.'")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"Then {younger.id} looked up with wide eyes, as if the balloon were a piece of dawn.")
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.para()

    gear = select_gear(activity, prize)
    if gear:
        world.say(f"{hero.id} heard the little clack again and chose a kinder thought: 'If I am gentle, the balloon can be shared.'")
        world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label if parent.label else 'parent'} smiled and said, 'Let us {gear.prep}.'")
        world.say(f"So they did. They {gear.tail}, and {younger.id} held the ribbon with careful hands.")
        world.say(f"The balloon stayed round and blue, the stone gate stayed quiet behind them, and {younger.id} laughed like a bell that had remembered its song.")
        hero.memes["worry"] = 0.0
        hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    else:
        world.say(f"There was no gentle fix, so the myth ended in a small warning instead of a blessing.")
    world.facts.update(hero=hero, parent=parent, prize=prize, younger=younger, activity=activity, setting=setting, gear=gear,
                        resolved=gear is not None)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short mythic story for a child about a {hero.type} named {hero.id}, a balloon, and a clack in the wind.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but chooses kindness so the {prize.label} stays safe.",
        f'Write a tiny myth with inner monologue and kindness that includes the word "balloon" and ends with a soft, happy image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} love at {world.setting.place}?",
            answer=f"{hero.id} loved {prize.phrase}. It shone like a small piece of sky in the wind.",
        ),
        QAItem(
            question=f"What sound kept coming back when {hero.id} stood near the gate?",
            answer="The balloon made a soft clack against the stone gate whenever the wind tugged it.",
        ),
        QAItem(
            question=f"What did the inner voice in {hero.id}'s head say?",
            answer="It whispered to keep the balloon close and not to be foolish, because the wind might take it.",
        ),
        QAItem(
            question=f"How did kindness change the ending for {hero.id} and the younger child?",
            answer=f"{hero.id} chose to share the balloon gently, and the younger child held the ribbon while they walked more slowly together.",
        ),
    ]


KNOWLEDGE = {
    "balloon": [("What is a balloon?", "A balloon is a light, thin bag filled with air or gas that can float and bob in the wind.")],
    "clack": [("What does clack mean?", "Clack is a sharp sound made when hard things tap together, like a stick against stone.")],
    "kindness": [("What is kindness?", "Kindness means choosing to help, share, or care about someone else.")],
    "myth": [("What is a myth?", "A myth is an old story people tell about special events, gods, heroes, or the world.")],
    "wind": [("What is wind?", "Wind is moving air. It can push leaves, flags, and balloons.")],
}

KNOWLEDGE_ORDER = ["myth", "balloon", "clack", "wind", "kindness"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("balloon")
    tags.add("kindness")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS_REGISTRY = {
    "shrine": SETTING,
    "courtyard": Setting(place="the courtyard of old bells", indoor=False, affords={"watch", "walk", "dance"}),
}

CURATED = [
    StoryParams(place="shrine", activity="walk", prize="balloon", name="Asha", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="shrine", activity="dance", prize="balloon", name="Ravi", gender="boy", parent="father", trait="hopeful"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS_REGISTRY.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS_REGISTRY[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
