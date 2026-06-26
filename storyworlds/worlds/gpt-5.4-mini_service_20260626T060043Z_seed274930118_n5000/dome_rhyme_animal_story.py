#!/usr/bin/env python3
"""
storyworlds/worlds/dome_rhyme_animal_story.py
============================================

A small, self-contained story world about animals inside a dome, with rhyme,
gentle tension, and a child-facing ending image.

Seed premise:
A little animal loves to rhyme in a shiny dome, but a special prize on the
animal's head might not stay put if the rhyme gets too bouncy. A parent or
friend notices the risk, suggests a safer way, and the animal gets to rhyme
anyway.

The simulation tracks:
- physical meters: bounce, wobble, shine, dust, comfort
- emotional memes: joy, worry, pride, closeness, fear, patience
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
        for k in ("bounce", "wobble", "shine", "dust", "comfort"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "pride", "closeness", "fear", "patience"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "tom", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
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
    weather: str = ""
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
        self.zone: set[str] = set()
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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_bounce(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["bounce"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("wobble", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wobble"] += 1
            item.meters["dust"] += 0.5
            out.append(f"{actor.label_word.capitalize()}'s {item.label} began to wobble.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["wobble"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That gave {carer.label_word} a worried look.")
    return out


CAUSAL_RULES = [
    _r_bounce,
    _r_worry,
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "wobble": prize.meters["wobble"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["bounce"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def tell(world_setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Milo", gender: str = "boy",
         traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(world_setting)

    hero = world.add(Entity(
        id=name, kind="character", type=gender, traits=["little"] + (traits or ["curious", "gentle"])
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    love_rhyme(world, hero, activity)
    give_prize(world, parent, hero, prize)
    love_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    touch(world, parent, hero)

    world.para()
    pause(world, hero)
    gear = compromise(world, parent, hero, activity, prize)
    if gear is not None:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity,
                       setting=world_setting, gear=gear,
                       conflict=hero.memes["fear"] >= THRESHOLD,
                       resolved=gear is not None)
    return world


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "bright")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved words that sang.")


def love_rhyme(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.gerund}; "
        f"each line bounced like a tiny ball in the bright dome."
    )


def give_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label_word} gave {hero.pronoun('object')} {prize.phrase}.")


def love_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["pride"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to the dome.")
    world.say("The dome was round and shiny, with warm light on the floor and echo-soft walls.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 0.5
    world.say(f"{hero.id} wanted to {activity.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["wobble"]:
        return False
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"If you {activity.verb}, your {prize.label} may wobble loose," '
        f'{hero.pronoun("possessive")} {parent.label_word} said softly.'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 0.5
    hero.memes["patience"] += 0.25
    world.say(f"{hero.id} still took one bouncy step toward the center of the dome.")


def touch(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["fear"] += 0.5
    hero.memes["closeness"] += 0.5
    world.say(f"Then {hero.pronoun('possessive')} {parent.label_word} touched {hero.pronoun('possessive')} paw and waited.")


def pause(world: World, hero: Entity) -> None:
    if hero.memes["fear"] >= THRESHOLD:
        world.say(f"{hero.id} paused and looked down at the prize.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["wobble"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and said, '
        f'"How about we {gear_def.prep} and still {activity.verb}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity,
           prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["closeness"] += 1
    world.say(f"{hero.id}'s face brightened, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}.")
    world.say(
        f"Together they used the {gear_def.label}, and soon {hero.id} was {activity.gerund}, "
        f"with {prize.label} steady and the dome filled with happy rhyme."
    )


SETTINGS = {
    "dome": Setting(place="the dome", indoor=True, affords={"rhyme"}),
    "sun_dome": Setting(place="the sun dome", indoor=True, affords={"rhyme"}),
    "music_dome": Setting(place="the music dome", indoor=True, affords={"rhyme"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="rhyme aloud",
        gerund="rhyme aloud",
        rush="dash to the middle and rhyme too hard",
        mess="wobble",
        soil="wobbly",
        zone={"head"},
        keyword="dome",
        tags={"rhyme", "dome"},
    ),
    "chant": Activity(
        id="chant",
        verb="chant a rhyme",
        gerund="chanting a rhyme",
        rush="skip in and chant too fast",
        mess="wobble",
        soil="wobbly",
        zone={"head", "torso"},
        keyword="rhyme",
        tags={"rhyme"},
    ),
}

PRIZES = {
    "crown": Prize(
        label="crown",
        phrase="a shiny leaf crown",
        type="crown",
        region="head",
    ),
    "hat": Prize(
        label="hat",
        phrase="a bright little hat",
        type="hat",
        region="head",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a soft ribbon scarf",
        type="scarf",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="chinstrap",
        label="a chin strap",
        covers={"head"},
        guards={"wobble"},
        prep="put on a chin strap first",
        tail="kept the crown steady",
    ),
    Gear(
        id="pin",
        label="a tiny pin",
        covers={"torso"},
        guards={"wobble"},
        prep="pin the scarf in place",
        tail="kept the scarf from sliding",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Poppy", "Nori", "Mabel"]
BOY_NAMES = ["Milo", "Finn", "Otto", "Pip", "Toby"]
TRAITS = ["brave", "gentle", "cheerful", "curious", "playful"]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short animal story for a young child about "{act.keyword}" in a dome.',
        f"Tell a gentle rhyme story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a simple story that includes a dome, a rhyme, and a safer way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is this story about?",
            answer=f"It is about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), hero.type)} {hero.type}, and {hero.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the dome?",
            answer=f"{hero.id} wanted to {act.verb} in the dome.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried because if {hero.id} {act.verb}, the {prize.label} could become wobbly and not stay in place.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did the animals solve the problem?",
                answer=f"They used {gear.label} so {hero.id} could {act.verb} without losing the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy and close to {hero.pronoun('possessive')} {parent.label_word}, and the dome was full of happy rhyme.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dome?",
            answer="A dome is a round roof or room with a curved top. It can make sounds echo a little.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word pattern where the sounds at the end of words match, like cat and hat.",
        ),
        QAItem(
            question="Why do people use a chin strap with a hat or crown?",
            answer="A chin strap helps keep a hat or crown steady so it does not slip off during bouncy play.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dome", activity="rhyme", prize="crown", name="Milo", gender="boy", parent="mother", trait="playful"),
    StoryParams(place="sun_dome", activity="rhyme", prize="hat", name="Mia", gender="girl", parent="father", trait="curious"),
    StoryParams(place="music_dome", activity="chant", prize="scarf", name="Pip", gender="boy", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} would not be in the way of {activity.gerund}, so there is no honest worry.)"
    return f"(No story: nothing in the gear catalog keeps a {prize.label} steady for this kind of rhyme.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for this prize.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


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
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: animals, dome, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name,
                       gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
