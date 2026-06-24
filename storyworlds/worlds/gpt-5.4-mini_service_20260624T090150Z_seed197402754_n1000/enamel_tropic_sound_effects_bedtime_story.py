#!/usr/bin/env python3
"""
storyworlds/worlds/enamel_tropic_sound_effects_bedtime_story.py
===============================================================

A small bedtime-story world about a warm tropic evening, a shiny enamel prize,
and a child who loves sound effects a little too much at sleep time.

The story starts from a simple source tale:
- a child is settled in a tropic home at bedtime
- they adore a tiny enamel object that makes bright sounds
- the child wants to keep playing with the sounds
- a parent worries the noise will wake others and spoil the calm
- they find a gentle compromise that keeps the bedtime mood soft

This script models that premise as world state, then narrates a complete
beginning-middle-end story from it.
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
        for key in ["noise", "sleepiness", "calm", "worry", "joy", "love", "tenderness", "noise_risk"]:
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the tropic porch"
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _soft_sound(word: str) -> str:
    return {
        "tropic": "chirp-chirp",
        "enamel": "ting-ting",
        "bedtime": "tap-tap",
        "rain": "pitter-patter",
    }.get(word, "soft-soft")


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("noise", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["noise_risk"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} trembled with little {item.meters['noise_risk']:.0f} bright clinks.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"boy", "girl"}), None)
    parent = next((e for e in world.characters() if e.type in {"mother", "father"}), None)
    if not child or not parent:
        return out
    if child.meters["noise"] < THRESHOLD:
        return out
    sig = ("worry", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["worry"] += 1
    out.append(f"The little noises were cheerful, but they were also a little too bright for bedtime.")
    return out


CAUSAL_RULES = [
    ("noise", _r_noise),
    ("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
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


def predict_noise(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "noisy": bool(prize and prize.meters["noise_risk"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside, the room was cool and sleepy, and a mosquito net swayed by the window."
    return f"The tropic air smelled of leaves and moonlight, and {setting.place} felt hushed and warm."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved listening for tiny sounds at night.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} adored {hero.pronoun('possessive')} {prize.label}, "
        f"because it went {prize.phrase} with a bright little {prize.label} sound."
    )


def bedtime(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One tropic evening, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} "
        f"were getting ready for bed at {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to keep making sound effects right away, "
        f"because {activity.gerund} felt cozy and fun."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_noise(world, hero, activity, prize.id)
    if not pred["noisy"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["worry"]
    world.say(
        f'"If you make {activity.soil}, you may wake everyone," {parent.label_word} said softly. '
        f'"Let us choose a gentler sound."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    hero.meters["noise"] += 1
    world.say(
        f"{hero.id} listened, but the tiny clink-clink wish was still hopping in {hero.pronoun('possessive')} chest."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    hero.memes["conflict"] += 1
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} held {hero.pronoun('possessive')} hand and smiled. "
        f'"We can keep the bedtime magic, just more quietly," {parent.label_word} said.'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_noise(world, hero, activity, prize.id)["noisy"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label_word} looked at the {prize.label} and found a gentle idea: "{gear_def.prep}."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face brightened, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f"They {gear_def.tail}. Soon the sounds were only {activity.keyword} { _soft_sound(activity.keyword) }, "
        f"and {prize.label} stayed lovely and calm."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["gentle", "curious"]),
    ))
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

    introduce(world, hero)
    loves_prize(world, hero, prize)
    world.para()
    bedtime(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero)
    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes["grabbed_by"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "tropic_poroch": Setting(place="the tropic porch", indoor=False, affords={"sound_effects"}),
    "tropic_room": Setting(place="the tropic room", indoor=True, affords={"sound_effects"}),
    "lantern_nook": Setting(place="the lantern nook", indoor=True, affords={"sound_effects"}),
}

ACTIVITIES = {
    "sound_effects": Activity(
        id="sound_effects",
        verb="make bedtime sound effects",
        gerund="making tiny sound effects",
        rush="jingle the enamel prize louder and louder",
        mess="noisy",
        soil="too noisy",
        zone={"torso"},
        weather="warm",
        keyword="tink",
        tags={"sound", "bedtime", "tropic", "enamel"},
    ),
}

PRIZES = {
    "bell": Prize(
        label="enamel bell",
        phrase="a soft, shiny note",
        type="bell",
        region="torso",
    ),
    "cup": Prize(
        label="enamel cup",
        phrase="a little bright clink",
        type="cup",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="cloth_wrap",
        label="a soft cloth wrap",
        covers={"torso"},
        guards={"noisy"},
        prep="wrap the enamel bell in a soft cloth and tap it on the pillow",
        tail="wrapped the enamel bell in a soft cloth and tapped it on the pillow",
    ),
    Gear(
        id="pillow_drum",
        label="a pillow drum",
        covers={"torso"},
        guards={"noisy"},
        prep="use a pillow drum instead",
        tail="used the pillow drum instead",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ari", "Tia"]
BOY_NAMES = ["Sami", "Noel", "Ravi", "Eli", "Jun"]
TRAITS = ["gentle", "curious", "sleepy", "playful", "sweet"]


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
    "enamel": [(
        "What is enamel?",
        "Enamel is a hard, smooth coating on metal or pottery that makes it shiny and easier to wash."
    )],
    "sound": [(
        "What are sound effects?",
        "Sound effects are little sounds made on purpose to help tell a story or make a scene feel real."
    )],
    "bedtime": [(
        "Why do children need bedtime?",
        "Bedtime helps a child’s body and mind slow down so they can rest and grow."
    )],
    "tropic": [(
        "What is tropic weather like?",
        "Tropic weather is usually warm, and it often feels soft and humid, with plants growing in plenty of sunlight."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a bedtime story for a young child in a tropic home that includes the word "enamel".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} with {hero.pronoun('possessive')} {prize.label} after dark.",
        f"Write a short bedtime tale about sound effects, a shiny enamel object, and a parent choosing a quiet compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who wanted to make sound effects at bedtime?",
            answer=f"{hero.id} wanted to make sound effects at bedtime."
        ),
        QAItem(
            question=f"What shiny object did {hero.id} love?",
            answer=f"{hero.id} loved the {prize.label}."
        ),
        QAItem(
            question=f"Where did the story take place?",
            answer=f"It took place at {world.setting.place} in a warm tropic bedtime scene."
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry?",
            answer=f"{parent.label_word.capitalize()} worried that the sounds would be too noisy and wake everyone."
        ),
        QAItem(
            question=f"What did they do instead?",
            answer=f"They used the soft cloth wrap so {hero.id} could keep the bedtime sounds gentle."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the cloth wrap help?",
            answer=f"It let {hero.id} keep playing with {prize.label} while making the sounds soft enough for bedtime."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("enamel")
    tags.add("sound")
    out: list[QAItem] = []
    for tag in ["enamel", "sound", "bedtime", "tropic"]:
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach {noun}, so there is no honest bedtime worry.)"
        )
    return (
        f"(No story: the gear box has no quiet fix for {noun} in this sound-effects scene.)"
    )


CURATED = [
    StoryParams(
        place="tropic_room",
        activity="sound_effects",
        prize="bell",
        name="Mina",
        gender="girl",
        parent="mother",
        trait="gentle",
    ),
    StoryParams(
        place="lantern_nook",
        activity="sound_effects",
        prize="cup",
        name="Sami",
        gender="boy",
        parent="father",
        trait="curious",
    ),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- zone_of(A, R), wears_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     guards(G, M), noise_of(A, M),
                     covers(G, R), wears_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("noise_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone_of", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears_on", pid, pr.region))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime story world with tropic air, enamel shine, and gentle sound effects."
    )
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
        raise StoryError(f"(No story: {PRIZES[args.prize].label} is not a typical {args.gender}'s item here.)")
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
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "sweet"],
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
            print(f"  {place:14} {act:14} {prize:8}  [{', '.join(genders)}]")
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
