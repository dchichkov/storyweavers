#!/usr/bin/env python3
"""
side_park_twist_fairy_tale.py
=============================

A small fairy-tale storyworld about a child, a side path in a park, and a
twist that turns worry into a kinder choice.
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

# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mud": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hope": 0.0, "stubborn": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "princess", "queen", "fairy", "mother", "woman"}
        masculine = {"boy", "prince", "king", "father", "man", "knight"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the park"
    side: str = "the side path"
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


@dataclass
class StoryParams:
    place: str
    side: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0
MESS_KINDS = {"muddy", "wet"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "park": Setting(place="the park", side="the side path", affords={"twist", "wander"}),
    "grove": Setting(place="the grove", side="the side path", affords={"twist"}),
}

ACTIVITIES = {
    "twist": Activity(
        id="twist",
        verb="follow the twisty side path",
        gerund="following the twisty side path",
        rush="dash toward the twisty side path",
        mess="muddy",
        soil="muddy",
        zone={"feet", "legs"},
        weather="soft rain",
        keyword="twist",
        tags={"twist", "path", "mud"},
    ),
    "wander": Activity(
        id="wander",
        verb="wander beside the pond",
        gerund="wandering by the pond",
        rush="hurry to the pond's edge",
        mess="wet",
        soil="wet",
        zone={"feet", "legs"},
        weather="soft rain",
        keyword="side",
        tags={"side", "water"},
    ),
}

PRIZES = {
    "slippers": Prize(
        label="slippers",
        phrase="a pair of satin slippers",
        type="slippers",
        region="feet",
        plural=True,
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a little blue cloak",
        type="cloak",
        region="torso",
    ),
    "skirt": Prize(
        label="skirt",
        phrase="a bright green skirt",
        type="skirt",
        region="legs",
        genders={"girl"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"muddy", "wet"},
        prep="put on rain boots first",
        tail="walked on in their rain boots",
        plural=True,
    ),
    Gear(
        id="cloakpin",
        label="a clasped cloak",
        covers={"torso"},
        guards={"wet"},
        prep="fasten the cloak with a silver pin",
        tail="went on with the cloak fastened",
    ),
]

GIRL_NAMES = ["Mina", "Elsa", "Faye", "Lina", "Ivy", "Nora"]
BOY_NAMES = ["Oren", "Theo", "Pip", "Rowan", "Finn", "Emil"]
TRAITS = ["brave", "gentle", "curious", "stubborn", "bright", "cheerful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def build_child(world: World, name: str, gender: str, trait: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, memes={"joy": 0.0, "worry": 0.0, "hope": 0.0, "stubborn": 0.0, "trust": 0.0}))


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_gender: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["joy"] += 1
    hero.memes["hope"] += 1
    world.say(f"Once upon a time, {hero.id} was a {hero_traits[0]} little {hero.gender if hasattr(hero, 'gender') else hero.type} who loved the {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, and the side path glittered like a ribbon beside the trees.")
    world.say(f"One day, {hero.id}'s {parent.label} brought {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} everywhere.")

    world.para()
    world.say(f"On a soft-rain day, {hero.id} and {hero.pronoun('possessive')} {parent.label} came to {setting.side} in {setting.place}.")
    hero.memes["stubborn"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} lifted a careful hand.")
    if prize_at_risk(activity, prize):
        hero.memes["worry"] += 1
        world.say(f'"If you go now, your {prize.label} will get {activity.soil}," {hero.pronoun("possessive")} {parent.label} said.')

    world.say(f"{hero.id} pouted and tried to {activity.rush}.")
    hero.memes["stubborn"] += 1

    gear = select_gear(activity, prize)
    if gear is not None:
        world.para()
        world.say(f"Then a tiny fairy with bright eyes stepped from the hedges and smiled.")
        world.say(f'"How about we {gear.prep} and still {activity.verb}?" she asked.')
        hero.memes["trust"] += 1
        hero.memes["joy"] += 1
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
        item = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
            worn_by=hero.id,
        ))
        world.zone = set(activity.zone)
        hero.meters[activity.mess] += 1
        if not item.protective:
            pass
        if not world.covered(hero, prize.region):
            prize.meters[activity.mess] += 1
            prize.meters["lost"] += 0
        world.say(f"{hero.id} agreed at once.")
        world.say(f"They {gear.tail}. Soon {hero.id} was {activity.gerund}, and {hero.pronoun('possessive')} {prize.label} stayed clean.")

        if activity.id == "twist":
            world.say("At the bend, the side path opened to a little fountain where a sleepy duckling was hiding under a fern.")
            world.say(f"{hero.id} set the duckling free, and the duckling bobbed away as if it had been waiting for a hero all morning.")
        else:
            world.say("By the pond, a silver koi leaped once, and the water shone like a smiling mirror.")
        hero.memes["joy"] += 1
        hero.memes["worry"] = 0.0
    else:
        world.para()
        world.say("But no kindly gear in the kingdom could have helped, so the tale kept its worry and ended there.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Prompts and Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "twist": [("What is a twist?", "A twist is a turning change in a path, rope, ribbon, or story that bends one way and then another.")],
    "path": [("What is a path?", "A path is a small way to walk on, like a trail through grass or trees.")],
    "mud": [("What is mud?", "Mud is soft, wet earth that can stick to shoes and clothes.")],
    "side": [("What does side mean?", "Side means next to something, like a path beside a garden or a tree beside a bench.")],
    "boots": [("What are rain boots for?", "Rain boots keep feet dry when the ground is wet or muddy.")],
}

KNOWLEDGE_ORDER = ["twist", "path", "side", "mud", "boots"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short fairy tale for a young child about "{world.setting.side}" in "{world.setting.place}" and a hidden twist.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f'Write a fairy tale that includes the word "{act.keyword}" and ends with a kind compromise near the side path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about in the park?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the side path?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the parent worry about the {prize.label}?",
            answer=f"The parent worried because {prize.phrase} could get {act.soil} on the twisty side path.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What helped {hero.id} keep playing without ruining the {prize.label}?",
                answer=f"A small fairy and {f['gear'].label} helped {hero.id} play safely while the {prize.label} stayed clean.",
            )
        )
        qa.append(
            QAItem(
                question=f"What did the hidden twist reveal at the end?",
                answer="It revealed a little fountain and a sleepy duckling hiding by the bend in the path.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("side", sid))
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
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about a side path in a park and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--side", choices=["side"])
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
            raise StoryError("No reasonable fairy-tale conflict can be made from those options.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, side="side", activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(place="park", side="side", activity="twist", prize="slippers", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="park", side="side", activity="twist", prize="cloak", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="grove", side="side", activity="twist", prize="skirt", name="Lina", gender="girl", parent="mother", trait="bright"),
]


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


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
            print(f"  {place:6} {act:8} {prize:8}  [{', '.join(genders)}]")
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
