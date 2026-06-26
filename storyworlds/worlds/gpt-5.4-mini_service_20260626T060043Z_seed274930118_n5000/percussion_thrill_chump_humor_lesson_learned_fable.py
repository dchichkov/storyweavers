#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/percussion_thrill_chump_humor_lesson_learned_fable.py
===============================================================================================================================

A tiny fable-style storyworld about a proud chump who loves percussion,
chases the thrill of making a loud fuss, and learns a gentle lesson.

The world is deliberately small and constraint-checked:
- one setting, one activity family, one fragile prize, one sensible fix
- child-facing prose with humor and a clear lesson learned
- physical state changes drive the ending image
- inline ASP rules mirror the Python reasonableness gate

Seed ingredients reflected in the world:
- percussion
- thrill
- chump

Style target:
- fable
- humor
- lesson learned
"""

from __future__ import annotations

import argparse
import dataclasses
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "raccoon", "badger", "wolf", "lion", "dog", "cat"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "animal"})


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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("loud", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.id == actor.id or item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("rattle", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["shaken"] = item.meters.get("shaken", 0.0) + 1
            if item.meters["shaken"] >= THRESHOLD:
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"The {item.label} gave a little shiver.")
    return out


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    if world.zone != {"shelf"}:
        return out
    for ent in world.characters():
        if ent.meters.get("loud", 0.0) < THRESHOLD:
            continue
        if ent.memes.get("showoff", 0.0) < THRESHOLD:
            continue
        sig = ("startle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["embarrassment"] = ent.memes.get("embarrassment", 0.0) + 1
        out.append("__startle__")
    return out


CAUSAL_RULES = [
    _r_rattle,
    _r_startle,
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
                produced.extend(s for s in sents if s != "__startle__")
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
    prize = sim.entities[prize_id]
    return {
        "shaken": prize.meters.get("shaken", 0.0) >= THRESHOLD,
        "dirty": prize.meters.get("dirty", 0.0) >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["thrill"] = actor.memes.get("thrill", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.label} was a little chump of a fox who loved to make a grand noise."
    )


def loves_music(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved percussion, and the thrill of a beat made "
        f"{hero.pronoun('possessive')} tail twitch with happiness."
    )


def prize_arrives(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One morning, {hero.id}'s {parent.label} brought home {hero.pronoun('object')} "
        f"{prize.phrase}."
    )
    world.say(f"{hero.id} stared at {prize.it()} as if it were a tiny treasure chest.")


def arrive_at_setting(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One bright day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to "
        f"{world.setting.place}."
    )
    if world.setting.indoor:
        world.say("The room was quiet enough to hear a crumb fall.")
    else:
        world.say("The air felt open and ready for a joke or two.")


def wants_to_play(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} newest prize "
        f"sat right in the way."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not (pred["shaken"] or pred["dirty"]):
        return False
    world.facts["warning"] = True
    world.say(
        f'"If you bang that hard," {parent.label} said, "you'll make {prize.it()} rattle, '
        f'and then the whole room will know you are a chump."'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["showoff"] = hero.memes.get("showoff", 0.0) + 1
    world.say(
        f"{hero.id} puffed up. {hero.pronoun().capitalize()} wanted the thrill more than the caution."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def embarrassment(world: World, hero: Entity) -> None:
    if hero.memes.get("embarrassment", 0.0) >= THRESHOLD:
        world.say(
            f"Then the loudness bounced back at {hero.id}, and everyone could see that the "
            f"boast was bigger than the beat."
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
            worn_by=hero.id,
        )
    )
    if predict(world, hero, activity, prize.id)["shaken"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{parent.label} smiled and said, "
        f"'{gear_def.prep}, and then you may {activity.verb} without trouble.'"
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1
    hero.memes["showoff"] = 0.0
    world.say(
        f"{hero.id} grinned, because the better trick was not the loudest one. "
        f"{hero.id} {gear_def.tail}, and this time the beat stayed merry instead of wild."
    )
    world.say(
        f"At last, {hero.id} played {activity.gerund}, and {prize.label} sat safe and sound."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip",
         hero_type: str = "fox", parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            label=f"{hero_name} the chump",
        )
    )
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, label="mother")
    )
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    introduce(world, hero)
    loves_music(world, hero, activity)
    prize_arrives(world, parent, hero, prize)

    world.para()
    arrive_at_setting(world, hero, parent, activity)
    wants_to_play(world, hero, activity, prize)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    propagate(world)
    embarrassment(world, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        lesson=True,
        joke=True,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "barn": Setting(place="the old barn", indoor=True, affords={"percussion"}),
    "green": Setting(place="the village green", indoor=False, affords={"percussion"}),
    "hall": Setting(place="the school hall", indoor=True, affords={"percussion"}),
}

ACTIVITIES = {
    "percussion": Activity(
        id="percussion",
        verb="play percussion",
        gerund="playing percussion",
        rush="rush to the drum and bang it like a thundercloud",
        mess="loud",
        soil="too loud and rattly",
        zone={"shelf"},
        keyword="percussion",
        tags={"percussion", "music", "loud"},
    ),
}

PRIZES = {
    "glassbell": Prize(
        label="glass bell",
        phrase="a bright glass bell on a low shelf",
        type="bell",
        region="shelf",
    ),
    "teacup": Prize(
        label="teacup",
        phrase="a small teacup with a gold rim",
        type="cup",
        region="shelf",
    ),
    "jar": Prize(
        label="jam jar",
        phrase="a jam jar with a lid that liked to wobble",
        type="jar",
        region="shelf",
    ),
}

GEAR = [
    Gear(
        id="feltsticks",
        label="soft felt drumsticks",
        covers={"shelf"},
        guards={"loud"},
        prep="put on soft felt drumsticks first",
        tail="put on the soft felt drumsticks",
    ),
    Gear(
        id="mat",
        label="a thick mat under the drum",
        covers={"shelf"},
        guards={"loud"},
        prep="set a thick mat under the drum",
        tail="set the thick mat under the drum",
    ),
]

NAMES = ["Pip", "Milo", "Ned", "Wren", "Toby", "Otis"]
PARENTS = ["mother", "father"]
TRAITS = ["proud", "silly", "eager", "cheerful"]


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
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "percussion": [("What is percussion?", "Percussion is music made by hitting, shaking, or tapping things like drums and bells.")],
    "bell": [("What does a bell do?", "A bell rings when you tap or move it, so people can hear a clear sound.")],
    "cup": [("Why are cups easy to break?", "A cup can break if it falls or gets knocked against something hard.")],
    "jar": [("What is a jar for?", "A jar is a container that can hold jam, honey, buttons, or other small things.")],
    "loud": [("Why can a loud sound be a problem?", "A very loud sound can startle people or animals and make a calm place feel jumpy.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is a good idea someone remembers after making a mistake or seeing a better way.")],
    "humor": [("What is humor?", "Humor is something funny or playful that makes people smile or laugh.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        f'Write a fable for children about a chump named {hero.id} who loves {activity.keyword} and learns a lesson.',
        f"Tell a short humorous story where {hero.id} chases the thrill of {activity.verb} but must protect {prize.label}.",
        f'Write a gentle lesson-learned story that includes "{activity.keyword}" and ends with a wise change in behavior.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little chump of a {hero.type}, and {hero.pronoun('possessive')} careful {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} love to do?",
            answer=f"{hero.id} loved percussion and the thrill of making a big beat.",
        ),
        QAItem(
            question=f"What treasure was at risk when {hero.id} wanted to {activity.verb}?",
            answer=f"{hero.pronoun('possessive').capitalize()} {prize.label} sat on a shelf, and it could rattle if the beat got too wild.",
        ),
    ]
    if f.get("warning"):
        qa.append(
            QAItem(
                question=f"Why did {parent.label} warn {hero.id}?",
                answer=f"{parent.label} warned {hero.id} because a loud percussion burst could make the {prize.label} shake and spoil the calm place.",
            )
        )
    if gear:
        qa.append(
            QAItem(
                question=f"How did the fix help?",
                answer=f"The soft gear kept the sound gentle, so {hero.id} could {activity.verb} without upsetting the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"What lesson did {hero.id} learn at the end?",
                answer=f"{hero.id} learned that the best thrill is not always the loudest one, and a careful choice can keep everyone happy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("lesson")
    tags.add("humor")
    out: list[QAItem] = []
    for tag in ["percussion", "bell", "cup", "jar", "loud", "lesson", "humor"]:
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", activity="percussion", prize="glassbell", name="Pip", parent="mother", trait="proud"),
    StoryParams(place="green", activity="percussion", prize="teacup", name="Milo", parent="father", trait="silly"),
    StoryParams(place="hall", activity="percussion", prize="jar", name="Wren", parent="mother", trait="eager"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach {noun}, so there is no honest warning to make.)"
    return f"(No story: no reasonable fix protects {noun} from {activity.gerund}.)"


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style story world about percussion, thrill, humor, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "fox", params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:12} {prize}")
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
