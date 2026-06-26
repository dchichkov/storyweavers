#!/usr/bin/env python3
"""
storyworlds/worlds/threat_suspense_cautionary_myth.py
======================================================

A small mythic story world about a child, a tempting wonder, and a clear threat.

Seed tale used to shape the world model:
---
In a valley below the moon hills, a little child named Iri loved to listen to old
myths. One evening, Iri found a silver path that shone beside the black reeds.
The grandmother warned that the path led to the Hollow Gate, where a hungry
shadow waited for anyone who crossed without a light.

Iri wanted to see the gate anyway. The night was quiet, but not safe. The reeds
whispered, the wind paused, and the shadow seemed to move closer each time the
light faded. Grandmother placed a lantern in Iri's hands and said that a brave
heart was not the same as a careless one.

Iri carried the lantern, crossed with care, and found that the shadow could not
come near the bright flame. The gate stayed shut, the path stayed clear, and the
child returned with a better story: some doors are not for opening, only for
remembering.

Causal shape:
---
    desire for forbidden place -> suspense
    omen/threat noticed         -> caution
    tempting advance            -> threat intensifies
    protective light used       -> threat recedes
    careful turnback            -> safety and wiser memory

Narration style:
---
Mythic, concrete, and child-facing, with a clear warning, a tense middle, and an
ending image that proves what changed.
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
REGIONS = {"hand", "head", "torso", "path"}


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
        for k in ["danger", "darkness", "travel", "safety"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "desire", "caution", "hope", "awe", "resolve", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elder"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the valley path"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["desire"] < THRESHOLD or actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("suspense", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        out.append("The quiet made every step feel watched.")
    return out


def _r_threat(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        sig = ("threat", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append("A threat had come close enough to matter.")
    return out


def _r_light(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["safety"] < THRESHOLD:
            continue
        sig = ("light", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hope"] += 1
        actor.memes["caution"] += 1
        out.append("The bright light pushed the dark back.")
    return out


CAUSAL_RULES = [_r_suspense, _r_threat, _r_light]


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


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoors:
        return f"The hall was hush-quiet, and the old stones held their own shadows."
    return f"{setting.place.capitalize()} lay still under a pale sky, where even the grass seemed to listen."


def predict_threat(world: World, actor: Entity, activity: Activity, relic_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    relic = sim.get(relic_id)
    return {
        "danger": relic.meters["danger"],
        "fear": actor.memes["fear"],
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That place cannot host this mythic action.")
    world.zone = set(activity.zone)
    actor.meters["travel"] += 1
    actor.memes["desire"] += 1
    actor.meters["danger"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved old stories and bright warnings.")


def love_myth(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["awe"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because it made the world feel full of mystery.")


def gift_relic(world: World, elder: Entity, hero: Entity, relic: Entity) -> None:
    world.say(f"One evening, {elder.label} placed {relic.phrase} into {hero.pronoun('possessive')} hands.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} wanted to {activity.verb}, even though the air had turned still.")


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, relic: Entity) -> bool:
    pred = predict_threat(world, hero, activity, relic.id)
    if pred["danger"] < THRESHOLD:
        return False
    hero.memes["fear"] += 1
    hero.memes["caution"] += 1
    world.say(
        f'"That path carries a threat," {elder.label} said. '
        f'"If you rush, the dark will find your {relic.label}."'
    )
    return True


def hesitate(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} looked at the path and felt both wonder and worry at once.")


def advance(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"Still, {hero.pronoun()} took a careful step and tried to {activity.rush}.")
    hero.meters["danger"] += 1
    propagate(world, narrate=True)


def offer_charm(world: World, elder: Entity, hero: Entity, relic: Entity, activity: Activity) -> Optional[Charm]:
    charm_def = select_charm(activity, relic)
    if charm_def is None:
        return None
    charm = world.add(Entity(
        id=charm_def.id, type="charm", label=charm_def.label,
        owner=hero.id, caretaker=elder.id, protective=True,
        covers=set(charm_def.covers), plural=charm_def.plural,
    ))
    charm.worn_by = hero.id
    if predict_threat(world, hero, activity, relic.id)["danger"] > 0:
        world.say(f"{elder.label} raised {charm_def.label} and said, \"Take this, and walk with care.\"")
        hero.meters["safety"] += 1
        propagate(world, narrate=True)
        return charm_def
    return None


def resolve(world: World, elder: Entity, hero: Entity, activity: Activity, relic: Entity, charm_def: Charm) -> None:
    hero.memes["resolve"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} held the {charm_def.label} close and kept {hero.pronoun('possessive')} steps slow."
    )
    world.say(
        f"The dark stayed back, and {hero.id} returned with {relic.label} still safe. "
        f"{charm_def.tail.capitalize()}."
    )


def select_charm(activity: Activity, relic: Relic) -> Optional[Charm]:
    for charm in CHARM_CATALOG:
        if activity.keyword in charm.wards and relic.region in charm.covers:
            return charm
    return None


SETTINGS = {
    "valley": Setting(place="the valley path", indoors=False, affords={"path", "gate"}),
    "shore": Setting(place="the moon shore", indoors=False, affords={"path"}),
    "hall": Setting(place="the old hall", indoors=True, affords={"gate"}),
}

ACTIVITIES = {
    "path": Activity(
        id="path",
        verb="walk the silver path",
        gerund="walking the silver path",
        rush="follow the silver path",
        risk="the shadow beside the reeds",
        weather="night",
        zone={"path"},
        keyword="path",
        tags={"dark", "path", "threat"},
    ),
    "gate": Activity(
        id="gate",
        verb="approach the Hollow Gate",
        gerund="approaching the Hollow Gate",
        rush="go toward the Hollow Gate",
        risk="the gate's hungry hush",
        weather="night",
        zone={"path", "torso"},
        keyword="gate",
        tags={"gate", "threat", "dark"},
    ),
}

RELICS = {
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="a small bronze lantern",
        type="lantern",
        region="hand",
    ),
    "cloak": Relic(
        id="cloak",
        label="cloak",
        phrase="a wool cloak with a silver clasp",
        type="cloak",
        region="torso",
    ),
}

CHARM_CATALOG = [
    Charm(
        id="bright_lantern",
        label="the bright lantern",
        covers={"hand", "path"},
        wards={"path", "gate"},
        prep="lift the lantern high",
        tail="the child had learned that light is a kind of courage",
    ),
    Charm(
        id="moon_cloak",
        label="the moon-cloak",
        covers={"torso"},
        wards={"gate"},
        prep="fasten the moon-cloak around the shoulders",
        tail="the child had learned that caution can be a gift",
    ),
]

NAMES = ["Iri", "Nera", "Sami", "Tala", "Milo", "Pavi"]
TRAITS = ["curious", "brave", "gentle", "thoughtful", "restless"]


@dataclass
class StoryParams:
    place: str
    activity: str
    relic: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for relic_id, relic in RELICS.items():
                if act.keyword in {"path", "gate"} and relic.region in {"hand", "torso"}:
                    combos.append((place, act_id, relic_id))
    return combos


def explain_rejection(activity: Activity, relic: Relic) -> str:
    return (
        f"(No story: this myth needs a real threat and a useful protection. "
        f"{activity.gerund} only fits relics carried on the {relic.region}, and this pairing does not make a strong cautionary turn.)"
    )


def explain_gender(relic_id: str, gender: str) -> str:
    return f"(No story: {RELICS[relic_id].label} is not a typical {gender}'s gift in this little myth.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic suspense world with a cautionary threat.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    if args.activity and args.relic:
        act, rel = ACTIVITIES[args.activity], RELICS[args.relic]
        if act.keyword not in {"path", "gate"}:
            raise StoryError(explain_rejection(act, rel))
    if args.gender and args.relic:
        if args.gender not in RELICS[args.relic].genders:
            raise StoryError(explain_gender(args.relic, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, relic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(RELICS[relic].genders))
    name = args.name or rng.choice(NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, relic=relic, name=name, gender=gender, elder=elder, trait=trait)


def tell(setting: Setting, activity: Activity, relic_cfg: Relic, name: str, gender: str,
         elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label=f"the {elder_type}"))
    relic = world.add(Entity(
        id=relic_cfg.id, type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase,
        owner=hero.id, caretaker=elder.id, region=relic_cfg.region, plural=relic_cfg.plural
    ))

    introduce(world, hero)
    love_myth(world, hero, activity)
    gift_relic(world, elder, hero, relic)
    world.say(f"That night, the valley was still, and {setting_detail(setting, activity)}")

    world.para()
    wants(world, hero, activity)
    warn(world, elder, hero, activity, relic)
    hesitate(world, hero, activity)
    advance(world, hero, activity)

    world.para()
    charm_def = offer_charm(world, elder, hero, relic, activity)
    if charm_def:
        resolve(world, elder, hero, activity, relic, charm_def)

    world.facts.update(hero=hero, elder=elder, relic=relic, activity=activity, setting=setting, charm=charm_def)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, relic = f["hero"], f["elder"], f["activity"], f["relic"]
    return [
        f'Write a short myth for a small child about "{act.keyword}" and a hidden threat.',
        f"Tell a suspenseful cautionary story where {hero.id} wants to {act.verb} but {elder.label} warns about {relic.phrase}.",
        f"Write a gentle myth in which a child learns that a bright light can help them face a dark threat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, act, relic = f["hero"], f["elder"], f["activity"], f["relic"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who loved old myths and careful courage.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {act.verb}, even though the place felt strange and still.",
        ),
        QAItem(
            question=f"Why did {elder.label} warn {hero.id} about the path?",
            answer=f"{elder.label} warned {hero.id} because there was a threat near the {relic.label}, and rushing ahead would have been unsafe.",
        ),
        QAItem(
            question=f"How did the child stay safe?",
            answer=f"{hero.id} stayed safe by taking the bright charm and moving slowly, so the dark could not come close.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern holds a light that helps people see in the dark.",
        ),
        QAItem(
            question="Why is it wise to listen to a warning?",
            answer="It is wise to listen to a warning because it can help you avoid danger and choose a safer way.",
        ),
        QAItem(
            question="What is a threat?",
            answer="A threat is something that could hurt you or make a situation unsafe.",
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
suspense(A) :- desire(A), fear(A).
threat(A) :- danger(A).
safe(A) :- safety(A).
chosen(A,P) :- hero(A), relic(P).
allowed(Place,A,P) :- setting(Place), affords(Place,A), hero(A), relic(P), chosen(_,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_region", rid, r.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], RELICS[params.relic],
                 params.name, params.gender, params.elder, params.trait)
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
    StoryParams(place="valley", activity="path", relic="lantern", name="Iri", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="shore", activity="path", relic="cloak", name="Milo", gender="boy", elder="grandfather", trait="thoughtful"),
    StoryParams(place="hall", activity="gate", relic="lantern", name="Tala", gender="girl", elder="grandmother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show allowed/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available in this world, but the story gate is driven by the Python model.")
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
            header = f"### {p.name}: {p.activity} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
