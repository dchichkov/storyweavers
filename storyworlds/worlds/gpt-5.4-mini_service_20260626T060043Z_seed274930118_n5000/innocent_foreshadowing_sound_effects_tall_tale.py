#!/usr/bin/env python3
"""
A standalone Storyweavers world: innocent foreshadowing with sound effects in a
small tall-tale domain.

Premise:
- A child hears funny sounds around a farmyard, a barn, and a creek.
- The sounds foreshadow a harmless surprise.
- The child helps solve the little problem, and the ending proves what changed.

This world keeps the tale child-facing, concrete, and state-driven. It uses
meters for physical state and memes for emotional state, includes an inline ASP
twin, and supports the standard Storyweavers CLI modes.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "wet": 0.0, "noise": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "delight": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    action: str
    sound: str
    foreshadow: str
    mess: str
    zone: set[str]
    clue: str
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
class Fix:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dust"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            out.append(f"{actor.id}'s {item.label} got dusty.")
    return out


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("wet", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            out.append(f"{actor.id}'s {item.label} got damp.")
    return out


def _r_worry(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["curiosity"] >= THRESHOLD and actor.meters["noise"] >= THRESHOLD:
            sig = ("worry", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worry"] += 1
            return [f"{actor.id} listened hard, because the noise sounded like it meant something."]
    return []


def _r_relief(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["worry"] >= THRESHOLD and actor.meters["noise"] < THRESHOLD:
            sig = ("relief", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["relief"] += 1
            return [f"{actor.id} grinned, because the worry had turned into a harmless surprise."]
    return []


RULES = [_r_dust, _r_wet, _r_worry, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def foreshadow_phrase(event: Event) -> str:
    return {
        "creak": "a soft creak like a gate yawning awake",
        "chime": "a bright chime like tin cups singing",
        "hum": "a low hum like the ground was whispering",
        "plink": "a plink-plink sound like little raindrops tapping a pail",
    }.get(event.sound, "a funny sound in the air")


def setting_detail(setting: Setting) -> str:
    if setting.indoors:
        return f"Inside {setting.place}, the boards were warm and the corners held their own quiet."
    return f"Out at {setting.place}, the wind had room to run and the shadows had long legs."


def choose_fix(event: Event, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if event.mess in fix.guards and prize.region in fix.covers:
            return fix
    return None


def prize_at_risk(event: Event, prize: Prize) -> bool:
    return prize.region in event.zone


def predict(world: World, hero: Entity, event: Event, prize_id: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(hero.id), event, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": bool(prize.meters[event.mess] >= THRESHOLD),
        "worry": sim.get(hero.id).memes["worry"],
    }


def _do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    if event.id not in world.setting.affords:
        raise StoryError(f"Setting {world.setting.place} cannot host {event.id}.")
    world.zone = set(event.zone)
    actor.meters[event.mess] += 1
    actor.meters["noise"] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big pair of ears and an even bigger imagination."
    )


def loves_sound(world: World, hero: Entity, event: Event) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {event.action}, especially when the air carried {foreshadow_phrase(event)}."
    )


def buys_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One afternoon, {hero.id}'s {parent.type} bought {hero.pronoun('object')} {prize.phrase}."
    )


def wears_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere."
    )


def arrive(world: World, hero: Entity, parent: Entity, event: Event) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting))
    world.say(f"Before long, they heard {foreshadow_phrase(event)}.")


def wants(world: World, hero: Entity, event: Event) -> None:
    world.say(f"{hero.id} wanted to {event.action} right away.")
    world.say(f"{hero.pronoun().capitalize()} even started to lean toward the sound, like a beanpole in a breeze.")


def warn(world: World, parent: Entity, hero: Entity, event: Event, prize: Entity) -> None:
    pred = predict(world, hero, event, prize.id)
    if pred["soiled"]:
        world.facts["predicted_soil"] = event.foreshadow
        world.say(
            f'"Wait a spell," {parent.type} said. "If you go now, your {prize.label} will get {event.foreshadow}."'
        )


def hesitate(world: World, hero: Entity, event: Event) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} paused and listened, wondering what the sound might be hiding.")


def reveal(world: World, parent: Entity, hero: Entity, event: Event) -> None:
    world.say(
        f"Then the truth came out with a {event.sound.upper()} and a smile: the noise was only {event.clue}."
    )


def compromise(world: World, parent: Entity, hero: Entity, event: Event, prize: Entity) -> Optional[Fix]:
    fix = choose_fix(event, prize)
    if not fix:
        return None
    if not prize_at_risk(event, prize):
        return None
    world.add(Entity(
        id=fix.id,
        type="thing",
        label=fix.label,
        protective=True,
        covers=set(fix.covers),
        owner=hero.id,
        caretaker=parent.id,
        plural=fix.plural,
    )).worn_by = hero.id
    if predict(world, hero, event, prize.id)["soiled"]:
        del world.entities[fix.id]
        return None
    world.say(
        f'{parent.id} smiled and said, "How about we {fix.prep} first?"'
    )
    return fix


def accept(world: World, hero: Entity, parent: Entity, event: Event, prize: Entity, fix: Fix) -> None:
    hero.memes["relief"] += 1
    hero.memes["delight"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id}'s face opened like a barn door in spring, and {hero.pronoun()} nodded yes."
    )
    world.say(
        f"They {fix.tail}. Soon {hero.id} was {event.action}, {prize.label} stayed clean, and the harmless sound kept company with their laughter."
    )


def tell(setting: Setting, event: Event, prize_cfg: Prize, hero_name: str = "Mabel",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))

    intro(world, hero)
    loves_sound(world, hero, event)
    buys_prize(world, parent, hero, prize)
    wears_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, event)
    wants(world, hero, event)
    warn(world, parent, hero, event, prize)
    hesitate(world, hero, event)
    reveal(world, parent, hero, event)

    world.para()
    fix = compromise(world, parent, hero, event, prize)
    if fix:
        accept(world, hero, parent, event, prize, fix)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       event=event, setting=setting, fix=fix)
    return world


SETTINGS = {
    "barnyard": Setting(place="the barnyard", indoors=False, affords={"creak", "chime", "hum", "plink"}),
    "creek": Setting(place="the creek bank", indoors=False, affords={"plink", "hum"}),
    "porch": Setting(place="the porch", indoors=False, affords={"creak", "chime"}),
    "loft": Setting(place="the hay loft", indoors=True, affords={"hum", "creak"}),
}

EVENTS = {
    "creak": Event(
        id="creak",
        action="follow the creaky boards",
        sound="creak",
        foreshadow="dusty",
        mess="dust",
        zone={"feet", "legs"},
        clue="Grandpa rocking a wheelbarrow into place",
        keyword="creak",
        tags={"dust", "wood", "barn"},
    ),
    "chime": Event(
        id="chime",
        action="tiptoe toward the chime",
        sound="chime",
        foreshadow="wet",
        mess="wet",
        zone={"feet"},
        clue="a row of tin cups swinging in the breeze",
        keyword="chime",
        tags={"wet", "metal"},
    ),
    "hum": Event(
        id="hum",
        action="peek where the humming was coming from",
        sound="hum",
        foreshadow="dusty",
        mess="dust",
        zone={"torso"},
        clue="a sleepy calf humming through its nose",
        keyword="hum",
        tags={"dust", "animal"},
    ),
    "plink": Event(
        id="plink",
        action="go see the plinking sound",
        sound="plink",
        foreshadow="wet",
        mess="wet",
        zone={"feet", "legs"},
        clue="rainwater dripping from a feeder into a pail",
        keyword="plink",
        tags={"wet", "water"},
    ),
}

FIXES = [
    Fix(
        id="boots",
        label="rubber boots",
        covers={"feet"},
        guards={"wet"},
        prep="put on the rubber boots",
        tail="stomped back out to the creek bank wearing the rubber boots",
        plural=True,
    ),
    Fix(
        id="apron",
        label="a long apron",
        covers={"torso"},
        guards={"dust"},
        prep="tie on a long apron",
        tail="marched back into the barnyard with the long apron on",
    ),
    Fix(
        id="wrap",
        label="a dry wrap",
        covers={"legs"},
        guards={"wet", "dust"},
        prep="wrap up in a dry wrap",
        tail="went back out wrapped from knees to toes",
    ),
]

PRIZES = {
    "overalls": Prize(
        label="overalls",
        phrase="a pair of bright overalls",
        type="overalls",
        region="legs",
        plural=True,
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a clean white shirt",
        type="shirt",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="little yellow boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GIRL_NAMES = ["Mabel", "Lena", "June", "Tilly", "Etta", "Ruby", "Nell", "Willa"]
BOY_NAMES = ["Otis", "Eli", "Bram", "Hank", "Jasper", "Milo", "Cal", "Otto"]
TRAITS = ["brave", "curious", "cheerful", "sharp-eyed", "restless"]


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for eid in setting.affords:
            ev = EVENTS[eid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(ev, prize) and choose_fix(ev, prize):
                    combos.append((place, eid, pid))
    return combos


KNOWLEDGE = {
    "creak": [("What makes a creaking sound?", "A creaking sound often comes from old wood moving a little, like a door or a porch step.")],
    "chime": [("What is a chime?", "A chime is a gentle ringing sound, often made by metal pieces tapping together.")],
    "hum": [("What is a hum?", "A hum is a low, steady sound, like a bee or a machine making a soft note.")],
    "plink": [("What is a plink sound?", "A plink is a tiny light sound, often made by water drops or a small thing tapping a pail.")],
    "dust": [("What is dust?", "Dust is made of tiny bits of dirt or skin and can settle on things when they sit still too long.")],
    "wet": [("Why do wet clothes feel heavy?", "Wet clothes feel heavy because water gets inside the fabric and adds extra weight.")],
    "boots": [("What are rubber boots for?", "Rubber boots help keep feet dry when the ground is wet or muddy.")],
    "apron": [("What is an apron for?", "An apron helps keep clothes clean when you are working or making a mess.")],
    "wrap": [("What is a wrap?", "A wrap is something you can put around yourself to stay clean or warm.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, ev, prize = f["hero"], f["parent"], f["event"], f["prize_cfg"]
    return [
        f'Write a short tall tale for a child that includes the word "{ev.keyword}" and a harmless surprise.',
        f"Tell a story where {hero.id} hears a {ev.sound} at {world.setting.place} and worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Write an innocent foreshadowing story with sound effects, a parent, and a clever little fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, ev = f["hero"], f["parent"], f["prize"], f["event"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a little {hero.type} named {hero.id} and {hero.pronoun('possessive')} {parent.type}.",
        ),
        QAItem(
            question=f"What sound made {hero.id} curious at {world.setting.place}?",
            answer=f"{hero.id} heard a {ev.sound} sound that felt like {foreshadow_phrase(ev)}.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn {hero.id} about the {prize.label}?",
            answer=f"{parent.id} warned {hero.id} because going toward the sound could have made the {prize.label} get {ev.foreshadow}.",
        ),
    ]
    if f.get("fix"):
        fix = f["fix"]
        qa.append(QAItem(
            question=f"How did {fix.label} help?",
            answer=f"They used {fix.label} so {hero.id} could keep going without ruining the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["event"].tags)
    if world.facts.get("fix"):
        tags.add(world.facts["fix"].id)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barnyard", event="creak", prize="overalls", name="Mabel", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="creek", event="plink", prize="boots", name="Otis", gender="boy", parent="father", trait="cheerful"),
    StoryParams(place="porch", event="chime", prize="shirt", name="June", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="loft", event="hum", prize="shirt", name="Bram", gender="boy", parent="father", trait="restless"),
]


def explain_rejection(event: Event, prize: Prize) -> str:
    if not prize_at_risk(event, prize):
        return f"(No story: the {prize.label} would not be at risk in this event.)"
    if not choose_fix(event, prize):
        return f"(No story: there is no sensible fix in the catalog for this combination.)"
    return "(No story: invalid explicit combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Innocent foreshadowing with sound effects in a tall-tale story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
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
    if args.event and args.prize:
        ev, pr = EVENTS[args.event], PRIZES[args.prize]
        if not (prize_at_risk(ev, pr) and choose_fix(ev, pr)):
            raise StoryError(explain_rejection(ev, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, prize = rng.choice(sorted(combos))
    p = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(p.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, event=event, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], PRIZES[params.prize],
                params.name, params.gender, params.parent)
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


ASP_RULES = r"""
at_risk(E,P) :- event(E), prize(P), zone(E,R), worn_on(P,R).
fixable(E,P) :- at_risk(E,P), fix(F), guards(F,M), mess_of(E,M), covers(F,R), worn_on(P,R).
valid(Place,E,P) :- affords(Place,E), at_risk(E,P), fixable(E,P).
valid_story(Place,E,P,G) :- valid(Place,E,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for e in sorted(s.affords):
            lines.append(asp.fact("affords", sid, e))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("mess_of", eid, e.mess))
        for r in sorted(e.zone):
            lines.append(asp.fact("zone", eid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for f in FIXES:
        lines.append(asp.fact("fix", f.id))
        for m in sorted(f.guards):
            lines.append(asp.fact("guards", f.id, m))
        for r in sorted(f.covers):
            lines.append(asp.fact("covers", f.id, r))
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, event, prize) combos ({len(stories)} with gender):\n")
        for place, event, prize in triples:
            genders = sorted(g for (pl, ev, pr, g) in stories if (pl, ev, pr) == (place, event, prize))
            print(f"  {place:10} {event:8} {prize:10} [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.event} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
