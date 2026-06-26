#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/collar_sound_effects_dialogue_repetition_tall_tale.py
==============================================================================================================

A small, self-contained story world with a tall-tale flavor:
a child, a beloved collar, loud sound effects, dialogue, and repetition.

Premise:
- A big-hearted child and a giant farm dog set out for a noisy adventure.
- The dog wears a special collar with a jangly charm.
- The collar's sound is part of the fun, but it can also cause trouble.

World model:
- Physical meters track noise, dust, distance, and snugness.
- Emotional memes track delight, worry, pride, and embarrassment.
- Narration is driven by state changes, not by a fixed template.

The stories are designed to feel like short tall tales:
- bigger-than-life comparisons
- repeated phrases
- sound effects
- spoken lines
- a playful, concrete ending image that proves what changed
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
SOUND_WORDS = {"jingle", "jangle", "clink", "clang", "ding", "ring", "tink"}


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
    ambience: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    sound: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
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


def _noise_name(activity: Activity) -> str:
    return activity.sound


def _r_noise_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("noise", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("noise_spread", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] = item.meters.get("dust", 0.0) + 1
            item.memes["embarrassment"] = item.memes.get("embarrassment", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.noun()} got dusty from the commotion.")
    return out


def _r_sound_echo(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("noise", 0.0) < THRESHOLD:
            continue
        sig = ("echo", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"Out went the sound: {_noise_name(world.facts['activity'])}!")
    return out


CAUSAL_RULES = [_r_sound_echo, _r_noise_spread]


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
    return {
        "soiled": bool(prize and prize.meters.get("dust", 0.0) >= THRESHOLD),
        "noise": sum(e.meters.get("noise", 0.0) for e in sim.characters()),
    }


def place_detail(setting: Setting) -> str:
    return setting.ambience or f"{setting.place.capitalize()} looked big and bright, like it had room for three adventures and a fourth besides."


def introduce(world: World, child: Entity, dog: Entity, prize: Entity) -> None:
    world.say(
        f"{child.id} had a giant farm dog named {dog.id}, and {dog.id} wore a {prize.label} that could jingle like a tiny brass orchestra."
    )


def loves(world: World, child: Entity, dog: Entity, prize: Entity, activity: Activity) -> None:
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1
    dog.memes["pride"] = dog.memes.get("pride", 0.0) + 1
    world.say(
        f"{child.id} loved that collar and loved its {_noise_name(activity)}-sound. {child.id} loved it so much {child.id} said, \"Jingle once, jingle twice, jingle all the way to the fence!\""
    )


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} does not reasonably support {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters["noise"] = actor.meters.get("noise", 0.0) + 1
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["delight"] = actor.memes.get("delight", 0.0) + 1
    propagate(world, narrate=narrate)


def arrive(world: World, child: Entity, dog: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {child.id} and {dog.id} went to {world.setting.place}. The wind was wide, the sky was high, and the collar went {_noise_name(activity)}-jangle with every step."
    )
    world.say(place_detail(world.setting))


def want(world: World, child: Entity, activity: Activity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    world.say(
        f"{child.id} wanted to {activity.verb}, and wanted it again, and wanted it once more."
    )


def warn(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, child, activity, prize.id)
    if not pred["soiled"] and pred["noise"] < THRESHOLD:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f"\"That {prize.label} will go {_noise_name(activity)}-clang and {_noise_name(activity)}-clatter, and it may come home {activity.soil},\" {parent.id} said."
    )
    return True


def defies(world: World, child: Entity, activity: Activity) -> None:
    child.memes["stubbornness"] = child.memes.get("stubbornness", 0.0) + 1
    world.say(
        f"{child.id} laughed and said, \"Let it jingle! Let it jangle! Let the whole wide world hear it!\""
    )
    world.say(
        f"{child.id} tried to {activity.rush}."
    )


def _gear_for(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def grab_and_conflict(world: World, parent: Entity, child: Entity, activity: Activity) -> None:
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    world.say(
        f"Then {parent.id} laughed a big laugh, caught {child.id} by the sleeve, and said, \"Easy now, easy now.\""
    )


def compromise(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = _gear_for(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=child.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = child.id
    if predict_mess(world, child, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"\"How about we {gear_def.prep}?\" {parent.id} asked. \"Then the collar can keep its song, but the song can be a softer song.\""
    )
    return gear


def accept(world: World, parent: Entity, child: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["conflict"] = 0.0
    world.say(
        f"{child.id} nodded, then nodded again, then nodded so hard it looked like a little fence post bouncing in a summer gale."
    )
    world.say(
        f"They tied on the {gear_def.label}, and the collar went {activity.sound}-soft instead of {activity.sound}-wild. Soon {child.id} and {child.id}'s dog were {activity.gerund}, and the {prize.label} stayed clean."
    )


SETTINGS = {
    "barnyard": Setting(
        place="the barnyard",
        outdoors=True,
        affords={"mud-run", "hay-dash", "pasture-trot"},
        ambience="The barnyard was big as a picnic blanket and twice as noisy, with a gate, a wagon, and a patch of sunshine all talking at once.",
    ),
    "pasture": Setting(
        place="the pasture",
        outdoors=True,
        affords={"pasture-trot", "hay-dash"},
        ambience="The pasture rolled on forever, as green as a painted meadow and as wide as a giant's promise.",
    ),
    "fairground": Setting(
        place="the fairground",
        outdoors=True,
        affords={"hay-dash", "mud-run"},
        ambience="The fairground buzzed and blustered, with flags snapping like little sails.",
    ),
}

ACTIVITIES = {
    "mud-run": Activity(
        id="mud-run",
        verb="race through the mud",
        gerund="racing through the mud",
        rush="dash straight through the mud",
        mess="muddy",
        soil="mud-spattered",
        zone={"feet", "legs"},
        sound="jingle-jangle",
        keyword="mud",
        tags={"mud", "collar", "sound"},
    ),
    "hay-dash": Activity(
        id="hay-dash",
        verb="dash over the hay",
        gerund="dashing over the hay",
        rush="dash over the hay bales",
        mess="dusty",
        soil="dust-covered",
        zone={"feet", "legs", "torso"},
        sound="clang-clang",
        keyword="hay",
        tags={"hay", "collar", "sound"},
    ),
    "pasture-trot": Activity(
        id="pasture-trot",
        verb="trot across the pasture",
        gerund="trotting across the pasture",
        rush="trot clear across the pasture",
        mess="dusty",
        soil="dust-dappled",
        zone={"feet", "legs"},
        sound="ding-ding",
        keyword="pasture",
        tags={"pasture", "collar", "sound"},
    ),
}

PRIZES = {
    "bell-collar": Prize(
        id="bell-collar",
        label="bell collar",
        phrase="a shiny brass collar with a tiny bell",
        type="collar",
        region="neck",
        genders={"girl", "boy"},
    ),
    "leather-collar": Prize(
        id="leather-collar",
        label="leather collar",
        phrase="a sturdy leather collar with a bright buckle",
        type="collar",
        region="neck",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="soft-bandana",
        label="soft bandana",
        covers={"neck"},
        guards={"dusty"},
        prep="tie a soft bandana over the collar bell",
        tail="walked the dust down to a whisper",
    ),
    Gear(
        id="mud-wrap",
        label="mud wrap",
        covers={"neck"},
        guards={"muddy"},
        prep="wrap the collar in a mud wrap before the dash",
        tail="kept the mud from making a joke of the collar",
    ),
]

CHILD_NAMES = ["Lula", "Mabel", "Joey", "Eddie", "Nell", "Toby", "Rosie", "Bea"]
DOG_NAMES = ["Bruno", "Hank", "Molly", "Big Ben", "Rufus", "Gus", "Daisy"]
PARENT_NAMES = ["Aunt June", "Uncle Will", "Mama Dot", "Pa", "Gran", "Old Ned"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    child: str
    dog: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region == "neck" and _gear_for(act, prize) is not None:
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a tall-tale style story for a child who loves a collar and keeps hearing "{activity.sound}".',
        f"Tell a short story where {child.id} wants to {activity.verb} but worries about the {prize.label}.",
        f'Write a playful story with sound effects, dialogue, and repetition that includes the word "collar".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    dog: Entity = f["dog"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    gear: Optional[Gear] = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was wearing the {prize.label} in the story?",
            answer=f"{dog.id} was wearing the {prize.label}, and {child.id} loved listening to it jingle.",
        ),
        QAItem(
            question=f"What did {child.id} want to do at {world.setting.place}?",
            answer=f"{child.id} wanted to {activity.verb} with {dog.id}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=(
                f"{parent.id} worried that the {prize.label} would make too much {_noise_name(activity)} and come home {activity.soil}."
            ),
        ),
    ]
    if gear is not None:
        qa.append(QAItem(
            question=f"How did the family make the {prize.label} safer for the trip?",
            answer=f"They used a {gear.label} so the collar could keep on making music, but more softly.",
        ))
        qa.append(QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and proud, because the plan worked and the {prize.label} stayed clean.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a collar?",
            answer="A collar is a band that goes around an animal's neck, often with a buckle or tag.",
        ),
        QAItem(
            question="Why do bells on collars make sound?",
            answer="A bell on a collar makes sound because it bumps and shakes when the animal moves.",
        ),
        QAItem(
            question="What is mud?",
            answer="Mud is wet dirt that can stick to shoes, paws, and clothes.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, child_name: str, dog_name: str, parent_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in {"Lula", "Mabel", "Nell", "Rosie", "Bea"} else "boy"))
    dog = world.add(Entity(id=dog_name, kind="character", type="dog"))
    parent = world.add(Entity(id=parent_name, kind="character", type="adult"))
    prize = world.add(Entity(
        id="collar",
        type="collar",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=dog.id,
        caretaker=parent.id,
        region=prize_cfg.region,
    ))
    prize.worn_by = dog.id

    world.facts.update(child=child, dog=dog, parent=parent, prize=prize, activity=activity)

    introduce(world, child, dog, prize)
    loves(world, child, dog, prize, activity)
    world.para()
    arrive(world, child, dog, activity)
    want(world, child, activity)
    warn(world, parent, child, activity, prize)
    defies(world, child, activity)
    grab_and_conflict(world, parent, child, activity)
    world.para()
    gear_def = compromise(world, parent, child, activity, prize)
    world.facts["gear"] = gear_def
    if gear_def is not None:
        accept(world, parent, child, activity, prize, gear_def)
        dog.memes["pride"] = dog.memes.get("pride", 0.0) + 1
    return world


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
    for gid, g in enumerate(GEAR):
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.verb} does not reasonably pair with a {prize.label} here, because there is no safe fix that keeps the collar's neck-region protected.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about a collar, sound effects, dialogue, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--dog")
    ap.add_argument("--parent")
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
        if _gear_for(act, pr) is None:
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        child=args.name or rng.choice(CHILD_NAMES),
        dog=args.dog or rng.choice(DOG_NAMES),
        parent=args.parent or rng.choice(PARENT_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.child, params.dog, params.parent)
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
    StoryParams(place="barnyard", activity="mud-run", prize="bell-collar", child="Lula", dog="Bruno", parent="Aunt June"),
    StoryParams(place="pasture", activity="pasture-trot", prize="leather-collar", child="Joey", dog="Big Ben", parent="Pa"),
    StoryParams(place="fairground", activity="hay-dash", prize="bell-collar", child="Rosie", dog="Molly", parent="Mama Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:10} {act:12} {prize}")
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
            header = f"### {p.child} / {p.dog} at {p.place} ({p.activity}, {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
