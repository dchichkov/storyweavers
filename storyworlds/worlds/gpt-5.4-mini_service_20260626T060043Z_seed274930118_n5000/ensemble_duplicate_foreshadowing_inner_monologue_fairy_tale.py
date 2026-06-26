#!/usr/bin/env python3
"""
A small fairy-tale storyworld about an ensemble, a duplicate token, and a gentle
choice that keeps a cherished prize safe.

The seed image behind this world:
A little child in a moonlit kingdom longs to join the royal ensemble. A second,
duplicate token causes a little worry, because the wrong token could lead them
through the misty garden at the wrong time. A wise caretaker notices the risk,
foresees the muddle, and offers a simple way through it.

The story model tracks:
- physical meters: wetness, muddle, brightness, and wear
- emotional memes: hope, worry, pride, trust, and relief

The style is meant to feel like a fairy tale: concrete, gentle, and lightly
magical, while still being state-driven rather than purely decorative.
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
    kind: str = "thing"  # "character" | "thing"
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
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ["wet", "mud", "wear", "bright"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "pride", "trust", "relief", "joy", "tension"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "mother", "queen", "woman"}
        male = {"boy", "prince", "father", "king", "man"}
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
    indoor: bool
    affords: set[str] = field(default_factory=set)
    mood: str = ""


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
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return any(i.protective and region in i.covers for i in self.worn_items(actor))

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
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["wear"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} grew damp.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["wet"] >= THRESHOLD and item.caretaker:
            sig = ("worry", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            carer = world.get(item.caretaker)
            carer.memes["worry"] += 1
            out.append(f"That would trouble {carer.label_word}.")
    return out


CAUSAL_RULES = [ _r_soak, _r_worry ]


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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["wet"] >= THRESHOLD, "worry": sim.get("mother").memes["worry"]}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That activity does not belong in this setting.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add(Entity(id="mother", kind="character", type=parent_type, label="the mother"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    duplicate = world.add(Entity(
        id="duplicate", type="thing", label="duplicate token", phrase="a duplicate token",
        owner=hero.id, region="hands"
    ))

    hero.memes["hope"] += 1
    world.say(f"Once in a moonlit kingdom, {hero.id} was a little {trait} {gender} who longed to join the royal ensemble.")
    world.say(f"{hero.pronoun('possessive').capitalize()} favorite thing was {activity.gerund}, especially when the lanterns shone like stars.")
    world.say(f"The seamstress had given {hero.id} {prize.phrase}, and a duplicate token lay beside it, glittering with a sly promise.")
    world.say(f"{hero.id} wondered if the duplicate token might help, yet some small hush in the wind made {hero.pronoun('object')} uneasy.")

    world.para()
    world.say(f"One {activity.weather or 'fine'} evening, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {setting.place}.")
    world.say(f"The grass there was slick with dew, and the ensemble was already warming up under the silver sky.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} heart beat a little faster when {hero.pronoun('subject')} saw the wet ground.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f'"If I step out now, my {prize.label} will get {activity.soil}," {hero.id} thought. "And then the mother will have extra work."')
        world.say(f'"You will lose your shine," {hero.pronoun("possessive")} {parent.label_word} said gently. "Let us choose wisely."')
        world.say(f"{hero.id} tried to {activity.rush}, but the wish to go ahead made {hero.pronoun('possessive')} steps clumsy.")
        hero.memes["worry"] += 1
        world.say(f"At once, {hero.pronoun('possessive')} {parent.label_word} held up a hand and kept {hero.pronoun('object')} close.")
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No gentle fix exists for this combination.")
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id, caretaker=parent.id,
        protective=True, covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        raise StoryError("The proposed gear does not truly solve the problem.")
    world.say(f'Then {hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and said, "{gear_def.prep}."')
    hero.memes["trust"] += 1
    hero.memes["worry"] = 0
    world.say(f"{hero.id}'s face grew bright. {hero.id} hugged {hero.pronoun('possessive')} {parent.label_word} and agreed at once.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, the {prize.label} stayed clean, and the royal ensemble played on as if the night itself were singing.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, duplicate=duplicate)
    return world


SETTINGS = {
    "castle_garden": Setting(place="the castle garden", indoor=False, affords={"dance", "sing"}, mood="moonlit"),
    "village_green": Setting(place="the village green", indoor=False, affords={"dance", "sing"}, mood="bright"),
    "moon_bridge": Setting(place="the moon bridge", indoor=False, affords={"dance"}, mood="silver"),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance in the dew",
        gerund="dancing in the dew",
        rush="run into the shining grass",
        mess="wet",
        soil="soaked and muddy",
        zone={"feet", "legs"},
        weather="moonlit",
        keyword="ensemble",
        tags={"wet", "ensemble"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing beside the lanterns",
        gerund="singing beside the lanterns",
        rush="hurry to the lantern circle",
        mess="bright",
        soil="smudged with wax",
        zone={"hands"},
        weather="moonlit",
        keyword="duplicate",
        tags={"bright", "duplicate"},
    ),
}

PRIZES = {
    "slippers": Prize(label="slippers", phrase="a pair of silver slippers", type="slippers", region="feet", plural=True),
    "cloak": Prize(label="cloak", phrase="a blue velvet cloak", type="cloak", region="torso"),
    "crown": Prize(label="crown", phrase="a little golden crown", type="crown", region="head"),
}

GEAR = [
    Gear(id="boots", label="soft boots", covers={"feet"}, guards={"wet"}, prep="put on your soft boots first", tail="walked back through the gate to fetch the soft boots", plural=True),
    Gear(id="cloak_pin", label="a cloak pin", covers={"torso"}, guards={"wet", "bright"}, prep="pin your cloak tight before you go", tail="adjusted the cloak pin and returned to the path"),
    Gear(id="gloves", label="little gloves", covers={"hands"}, guards={"bright"}, prep="wear little gloves for the lantern light", tail="went back for the little gloves", plural=True),
]

GIRL_NAMES = ["Mira", "Lina", "Elsa", "Nora", "Ayla", "Tessa"]
BOY_NAMES = ["Robin", "Finn", "Perrin", "Alden", "Milo", "Jasper"]
TRAITS = ["curious", "brave", "gentle", "cheerful", "stubborn"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy-tale story about an ensemble, a duplicate token, and a wise compromise.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} at {f['setting'].place} but a duplicate token and a cherished {f['prize'].label} make the choice tricky.",
        f"Write a short child-friendly tale that includes the words 'ensemble' and 'duplicate' and ends with a safe plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id}, the little {hero.type}, wanted to {act.verb} with the royal ensemble.",
        ),
        QAItem(
            question=f"Why did the mother worry about the {prize.label}?",
            answer=f"She knew the wet grass could make the {prize.label} {act.soil}, and that would mean more work.",
        ),
        QAItem(
            question=f"What safe choice did they make instead?",
            answer=f"They chose to use {gear.label} first, so {hero.id} could join the music without ruining the {prize.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ensemble?",
            answer="An ensemble is a group that performs together, like singers, players, or dancers sharing one show.",
        ),
        QAItem(
            question="What does duplicate mean?",
            answer="Duplicate means an extra copy that looks the same as the original.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not sensibly endanger the {prize.label} in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: ensemble, duplicate, foreshadowing, and a gentle compromise.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "mother"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="castle_garden", activity="dance", prize="slippers", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="village_green", activity="sing", prize="cloak", name="Robin", gender="boy", parent="mother", trait="gentle"),
    StoryParams(place="moon_bridge", activity="dance", prize="crown", name="Ayla", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, act, prize in combos:
            print(place, act, prize)
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
