#!/usr/bin/env python3
"""
storyworlds/worlds/tacky_transformation_rhyme_suspense_space_adventure.py
========================================================================

A small space-adventure story world with a tacky transformation, a little
rhyme, and a suspenseful choice between rushing and fixing things safely.

Initial seed-tale shape:
---
A child astronaut named Nova loves building tiny rocket models in the moon
workshop. One day, Nova gets a pot of tacky star-glue and wants to transform a
plain model into a bright comet rocket before the launch bell rings.

But the glue is messy. Nova's parent worries it will stick to Nova's flight
badge and make a sticky disaster right before the tour begins. Nova wants to
rush ahead anyway. Then a cheerful repair robot starts talking in rhymes and
offers a safer plan: put on a smock first, then finish the transformation.

The story ends with the model changed, the badge clean, and the launch bell
still waiting.
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
METER_KEYS = {"tacky"}
MEME_KEYS = {"joy", "desire", "worry", "defiance", "calm", "suspense"}


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
        for k in METER_KEYS:
            self.meters.setdefault(k, 0.0)
        for k in MEME_KEYS:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the moon workshop"
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
    keyword: str = "tacky"
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
        self.facts: dict = {}
        self.trace: list[str] = []

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


def warn(world: World, msg: str) -> None:
    world.trace.append(msg)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters["tacky"] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("tacky", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["tacky"] += 1
                actor.memes["suspense"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got tacky.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_tacky(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = copy_world(world)
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["tacky"] >= THRESHOLD}


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    clone.facts = dict(world.facts)
    clone.paragraphs = [[]]
    return clone


def setting_detail(setting: Setting) -> str:
    return "The workshop hummed softly, and a launch bell blinked red by the door."


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little space explorer who loved shiny tools and brave ideas.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because every tiny part could turn into something new."
    )


def prize_sentence(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a badge of honor."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    hero.memes["suspense"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, before the blinking bell could ring."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_tacky(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    parent.memes["worry"] += 1
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"You\'ll get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s slow down."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the idea kept sparkling in {hero.pronoun('possessive')} head.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def rhyme_bot(world: World, bot: Entity) -> None:
    bot.memes["calm"] += 1
    world.say(
        f'{bot.id} rolled closer and sang, "Stick with care, take time to spare. '
        f'Shine can wait, but a mess is there."'
    )


def grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} gently held {hero.pronoun('possessive')} hand near the worktable."
    )


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    inst = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    inst.worn_by = hero.id
    if predict_tacky(world, hero, activity, prize.id)["soiled"]:
        del world.entities[inst.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. '
        f'"How about we {gear.prep} and {activity.verb} together?"'
    )
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["calm"] += 1
    hero.memes["suspense"] = 0.0
    world.say(
        f"{hero.id} grinned and hugged {hero.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f'They {gear.tail}. Soon the little rocket was {activity.gerund}, {prize.label} stayed clean, and the red bell still had not rung.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nova", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    bot = world.add(Entity(id="Ribbit", kind="character", type="robot", label="the repair robot"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    intro(world, hero)
    loves_activity(world, hero, activity)
    prize_sentence(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    world.say(setting_detail(setting))
    wants(world, hero, activity)
    if warn(world, parent, hero, activity, prize):
        defies(world, hero, activity)
        grab(world, parent, hero)
        rhyme_bot(world, bot)

    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, bot=bot, prize=prize, activity=activity, setting=setting, gear=gear)
    return world


SETTINGS = {
    "moon_workshop": Setting(place="the moon workshop", indoor=True, affords={"transform"}),
    "starport_bay": Setting(place="the starport bay", indoor=True, affords={"transform"}),
    "asteroid_garage": Setting(place="the asteroid garage", indoor=True, affords={"transform"}),
}

ACTIVITIES = {
    "transform": Activity(
        id="transform",
        verb="transform the little rocket model",
        gerund="transforming the little rocket model",
        rush="dash to the glue and stick on the silver fins",
        mess="tacky",
        soil="all tacky",
        zone={"torso", "hands"},
        keyword="tacky",
        tags={"tacky", "transformation", "space"},
    ),
}

PRIZES = {
    "badge": Prize(
        label="flight badge",
        phrase="a bright flight badge",
        type="badge",
        region="torso",
    ),
    "gloves": Prize(
        label="space gloves",
        phrase="a pair of space gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="smock",
        label="a repair smock",
        covers={"torso"},
        guards={"tacky"},
        prep="put on a repair smock first",
        tail="slid into the repair smock and got back to work",
    ),
    Gear(
        id="gloves",
        label="tough repair gloves",
        covers={"hands"},
        guards={"tacky"},
        prep="pull on tough repair gloves first",
        tail="pulled on the tough repair gloves and kept the glue off",
        plural=True,
    ),
]

NAMES = ["Nova", "Ari", "Milo", "Zuri", "Ivy", "Kai"]
TRAITS = ["brave", "curious", "cheerful", "bold"]


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure story world about tacky transformation and rhyme.")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (pr.region in act.zone and select_gear(act, pr)):
            raise StoryError("That combination is not reasonable for this world.")
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short space-adventure story for a little kid about "{act.keyword}" and a safe transformation.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.label}.",
        f"Write a story with a tiny rhyme and a suspenseful moment in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qas = [
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why was {hero.pronoun('possessive')} {parent.label_word} worried?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.label_word} worried that the {act.keyword} glue would get {f['predicted_soil']} on the {prize.label}.",
        ),
        QAItem(
            question=f"What did the repair robot say?",
            answer='It sang a little rhyme: "Stick with care, take time to spare. Shine can wait, but a mess is there."',
        ),
    ]
    if gear:
        qas.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"It let {hero.id} {act.verb} without getting the {prize.label} messy.",
        ))
        qas.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} happily {act.gerund}, the {prize.label} clean, and the launch bell still waiting.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tacky mean?",
            answer="Tacky means sticky, so it can cling to fingers and paper.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like care and spare.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next.",
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), fix(_,A,P).
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="moon_workshop", activity="transform", prize="badge", name="Nova", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="starport_bay", activity="transform", prize="gloves", name="Kai", gender="boy", parent="father", trait="brave"),
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
        model = asp.one_model(asp_program("#show valid/3."))
        print(asp.atoms(model, "valid"))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
