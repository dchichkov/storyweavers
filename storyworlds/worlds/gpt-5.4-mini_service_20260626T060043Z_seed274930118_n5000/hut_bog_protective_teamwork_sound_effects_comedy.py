#!/usr/bin/env python3
"""
storyworlds/worlds/hut_bog_protective_teamwork_sound_effects_comedy.py
======================================================================

A small comedy storyworld about a hut, a bog, protective gear, teamwork,
and cheerful sound effects.

The seed imagines a tiny tale:
- a small crew wants to cross the bog beside a hut,
- one friend worries about mud and splashes,
- they put on protective gear together,
- their teamwork turns the soggy problem into a funny success.

The world is intentionally small and constraint-checked so every generated
story has a clear setup, a comic turn, and a satisfying ending image.
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
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"muddy": 0.0, "dry": 0.0, "help": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "teamwork": 0.0, "laugh": 0.0}

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


@dataclass
class Setting:
    place: str = "the hut"
    bog: str = "the bog"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    sound: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ProtectiveGear:
    id: str
    label: str
    phrase: str
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
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hut": Setting(place="the hut", bog="the bog", affords={"cross_bog", "bog", "cleanup"}),
    "pondside_hut": Setting(place="the hut by the pond", bog="the bog path", affords={"cross_bog", "bog"}),
    "old_hut": Setting(place="the old hut", bog="the marshy yard", affords={"cross_bog", "bog", "cleanup"}),
}

ACTIVITIES = {
    "cross_bog": Activity(
        id="cross_bog",
        verb="cross the bog",
        gerund="tiptoeing across the bog",
        rush="splash through the bog",
        mess="muddy",
        sound="squelch-splish",
        keyword="bog",
        tags={"bog", "mud", "sound"},
    ),
    "bog": Activity(
        id="bog",
        verb="play in the bog",
        gerund="bouncing near the bog",
        rush="dash into the bog",
        mess="muddy",
        sound="splat-squish",
        keyword="bog",
        tags={"bog", "mud", "sound"},
    ),
    "cleanup": Activity(
        id="cleanup",
        verb="clean the bog path",
        gerund="scrubbing the bog stones",
        rush="rush to the muddy path",
        mess="muddy",
        sound="scrub-scrub",
        keyword="cleanup",
        tags={"cleanup", "teamwork", "sound"},
    ),
}

GEAR = [
    ProtectiveGear(
        id="boots",
        label="rubber boots",
        phrase="shiny rubber boots",
        covers={"feet"},
        guards={"muddy"},
        prep="put on rubber boots first",
        tail="stomped back out in their rubber boots",
    ),
    ProtectiveGear(
        id="raincoat",
        label="raincoat",
        phrase="a bright raincoat",
        covers={"torso"},
        guards={"muddy"},
        prep="wear a raincoat too",
        tail="marched back out in the raincoat",
    ),
    ProtectiveGear(
        id="gloves",
        label="work gloves",
        phrase="small work gloves",
        covers={"hands"},
        guards={"muddy"},
        prep="pull on work gloves for everybody",
        tail="went back to the bog with their work gloves on",
        plural=True,
    ),
    ProtectiveGear(
        id="towel_capes",
        label="towel capes",
        phrase="flappy towel capes",
        covers={"torso"},
        guards={"muddy"},
        prep="wrap up in towel capes",
        tail="came back looking like brave laundry ghosts",
        plural=True,
    ),
]

GIRL_NAMES = ["Mia", "Nina", "Lila", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Max", "Noah", "Toby"]
CREW_NAMES = ["Mia", "Leo", "Nina", "Ben", "Zoe", "Finn"]
TRAITS = ["cheerful", "curious", "silly", "bright", "bouncy", "helpful"]


# ---------------------------------------------------------------------------
# Validation / reasonableness
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity) -> bool:
    return activity.mess == "muddy"


def select_gear(activity: Activity) -> Optional[ProtectiveGear]:
    for gear in GEAR:
        if activity.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            if prize_at_risk(ACTIVITIES[act_id]) and select_gear(ACTIVITIES[act_id]):
                out.append((place, act_id))
    return out


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A) :- activity(A), mess_of(A, muddy).
has_fix(A) :- prize_at_risk(A), gear(G), guards(G, muddy).
valid(Place, A) :- affords(Place, A), prize_at_risk(A), has_fix(A).
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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story machinery
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    act: Activity = f["activity"]
    gear: ProtectiveGear = f["gear"]
    return [
        f'Write a funny short story for a young child about {hero.id}, a hut, and a bog, using the word "{act.keyword}".',
        f"Tell a comedy story where {hero.id} wants to {act.verb} near the hut but needs {gear.label} first.",
        f"Write a cheerful teamwork story with sound effects like '{act.sound}' and a happy ending near the bog.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    act: Activity = f["activity"]
    gear: ProtectiveGear = f["gear"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"Where did {hero.id} and {parent.label} go in the story?",
            answer=f"They went to {place}, where the bog was waiting nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the bog?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What protective thing helped the crew stay less muddy?",
            answer=f"{gear.label} helped because it was {gear.phrase} and kept the messy bog from ruining their clothes.",
        ),
        QAItem(
            question=f"What funny sound did the muddy teamwork make?",
            answer=f"It made a silly '{act.sound}' sound.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the teamwork problem get fixed?",
                answer=(
                    f"They laughed, shared the gear, and used {gear.label} together. "
                    f"That let {hero.id} finish {act.gerund} without getting stuck in the mud."
                ),
            )
        )
    return qa


KNOWLEDGE = {
    "bog": [
        (
            "What is a bog?",
            "A bog is a wet, squishy place with soft ground and lots of water in the soil.",
        )
    ],
    "hut": [
        (
            "What is a hut?",
            "A hut is a small simple house, usually made for quick shelter or cozy living.",
        )
    ],
    "protective": [
        (
            "What does protective mean?",
            "Protective means something helps keep people or things safe from harm or mess.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help each other and work together to do a job.",
        )
    ],
    "sound": [
        (
            "What is a sound effect in a story?",
            "A sound effect is a made-up word or sound in the story that helps you imagine what is happening, like splish or thump.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("hut")
    tags.add("bog")
    tags.add("protective")
    tags.add("teamwork")
    out: list[QAItem] = []
    for key in ["hut", "bog", "protective", "teamwork", "sound"]:
        if key in tags or key == "sound":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = {"feet", "hands", "torso"}
    actor.meters["muddy"] += 1
    actor.memes["joy"] += 1
    actor.memes["worry"] += 1
    if narrate:
        world.say(f"{actor.id} went {activity.gerund}, and the bog went '{activity.sound}!'")
        world.say(f"The mud made a comic {activity.sound} sound under their feet.")


def predict_mess(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {"muddy": any(e.meters["muddy"] >= THRESHOLD for e in sim.characters())}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('joy', 0) and 'little' or 'small'} {hero.type} with a big grin.")
    world.say(f"{hero.id} noticed the hut, the bog, and every wobble in between.")


def teamwork_setup(world: World, hero: Entity, friend: Entity, act: Activity) -> None:
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(f"{hero.id} and {friend.id} wanted to {act.verb}, but the ground said, 'Glub!'")
    world.say(f"They looked at each other and said, 'Teamwork time!'")


def warn(world: World, parent: Entity, hero: Entity, act: Activity) -> bool:
    pred = predict_mess(world, hero, act)
    if not pred["muddy"]:
        return False
    world.say(f'"If we rush in, we\'ll get muddy," {parent.id} said.')
    return True


def comedy_reaction(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["laugh"] += 1
    friend.memes["laugh"] += 1
    world.say("The bog answered with a loud 'Blorp!'")
    world.say(f"{hero.id} laughed so hard they nearly wiggled sideways.")


def choose_gear(activity: Activity) -> ProtectiveGear:
    gear = select_gear(activity)
    if gear is None:
        raise StoryError("No protective gear fits this muddy bog story.")
    return gear


def compromise(world: World, parent: Entity, hero: Entity, friend: Entity, activity: Activity) -> ProtectiveGear:
    gear = choose_gear(activity)
    if gear.id == "gloves":
        world.say(f"{parent.id} pointed to {gear.phrase} and said, 'Let's share these.'")
    else:
        world.say(f"{parent.id} found {gear.phrase} and said, 'That looks protective enough.'")
    world.say(f"Together they {gear.prep}.")
    for ch in (hero, friend):
        g = world.add(Entity(
            id=f"{ch.id}_{gear.id}",
            kind="thing",
            type="gear",
            label=gear.label,
            phrase=gear.phrase,
            plural=gear.plural,
            owner=ch.id,
            protective=True,
            covers=set(gear.covers),
            worn_by=ch.id,
        ))
        g.meters["dry"] = 1.0
    return gear


def resolve(world: World, hero: Entity, friend: Entity, parent: Entity, act: Activity, gear: ProtectiveGear) -> None:
    hero.memes["worry"] = 0
    friend.memes["worry"] = 0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(f"Then they went back and {act.gerund} together.")
    world.say(f"Their boots went 'plop-plip,' the bog went 'squish-squash,' and nobody minded the silliness.")
    world.say(f"At the end, {hero.id} and {friend.id} were still smiling, and {parent.id} was laughing beside the hut.")
    world.facts["resolved"] = True


def tell(setting: Setting, activity: Activity, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id="Friend", kind="character", type="boy" if hero_type == "girl" else "girl", label="the friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    world.facts.update(hero=hero, friend=friend, parent=parent, activity=activity, setting=setting)

    introduce(world, hero)
    world.say(f"{hero.id} loved {activity.gerund} because it sounded like '{activity.sound}' and felt silly.")
    world.say(f"{trait.capitalize()} {hero.id} and {friend.id} had come to {setting.place} beside {setting.bog}.")

    world.para()
    teamwork_setup(world, hero, friend, activity)
    warn(world, parent, hero, activity)
    comedy_reaction(world, hero, friend)

    world.para()
    gear = compromise(world, parent, hero, friend, activity)
    resolve(world, hero, friend, parent, activity, gear)
    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_name_pool(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(valid_name_pool(gender))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.gender, params.parent, params.trait)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="hut", activity="cross_bog", name="Mia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="pondside_hut", activity="bog", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="old_hut", activity="cleanup", name="Zoe", gender="girl", parent="mother", trait="helpful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a hut, a bog, protective gear, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (place, activity) combos:")
        for place, act in combos:
            print(f"  {place:12} {act}")
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
