#!/usr/bin/env python3
"""
Stand-alone story world: a small pirate tale about a curious little pirate,
repeated tries, and a kind turn.

Seed inspiration:
- pastel
- blossom

The world is intentionally tiny and constraint-checked: one child pirate,
one delicate pastel blossom object, one risky curiosity-driven action,
and one kindness-based resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain-girl"}
        male = {"boy", "father", "dad", "man", "captain-boy"}
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
    sound: str
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
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0
MESS_KINDS = {"wet", "torn", "stained"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", sound="the gulls cried over the water", affords={"blossom", "paint"}),
    "deck": Setting(place="the ship deck", sound="the rigging creaked in the wind", affords={"blossom", "rope"}),
    "garden_island": Setting(place="the island garden", sound="the sea hummed behind the palms", affords={"blossom"}),
}

ACTIVITIES = {
    "blossom": Activity(
        id="blossom",
        verb="pick the blossom",
        gerund="picking blossoms",
        rush="reach for the blossom",
        mess="stained",
        soil="creased and stained",
        zone={"hands"},
        keyword="blossom",
        tags={"blossom", "pastel", "kindness"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a sign",
        gerund="painting signs",
        rush="grab the paint pot",
        mess="stained",
        soil="spattered with paint",
        zone={"hands", "torso"},
        keyword="pastel",
        tags={"pastel", "kindness"},
    ),
    "rope": Activity(
        id="rope",
        verb="climb the rope",
        gerund="climbing ropes",
        rush="dash to the rope ladder",
        mess="torn",
        soil="frayed and torn",
        zone={"hands"},
        keyword="pirate",
        tags={"pirate"},
    ),
}

PRIZES = {
    "flower_sash": Prize(
        label="flower sash",
        phrase="a soft pastel flower sash",
        type="sash",
        region="torso",
    ),
    "gloves": Prize(
        label="gloves",
        phrase="a pair of white gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
    "hat": Prize(
        label="hat",
        phrase="a little sea hat with a ribbon",
        type="hat",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="washcloth",
        label="a washcloth wrap",
        covers={"hands"},
        guards={"stained"},
        prep="wrap the hands in a washcloth",
        tail="carefully unwrapped the washcloth",
    ),
    Gear(
        id="sleeves",
        label="long sleeves",
        covers={"hands", "torso"},
        guards={"stained"},
        prep="pull on long sleeves first",
        tail="pulled off the long sleeves",
        plural=True,
    ),
    Gear(
        id="rope_gloves",
        label="rope gloves",
        covers={"hands"},
        guards={"torn"},
        prep="put on rope gloves first",
        tail="tightened the rope gloves",
        plural=True,
    ),
]

TRAITS = ["curious", "kind", "cheerful", "bold"]
GIRL_NAMES = ["Mina", "Lena", "Pia", "Nori", "Saila"]
BOY_NAMES = ["Cai", "Jory", "Tavin", "Milo", "Ren"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return sorted(out)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach the {prize.region}, "
            f"so the {prize.label} would stay safe and there is no honest worry.)"
        )
    return (
        f"(No story: there is no gear that can honestly protect the {prize.label} "
        f"from {activity.gerund}.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    msgs = _soak(world)
    if narrate:
        for msg in msgs:
            world.say(msg)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def tale_sound(setting: Setting, activity: Activity) -> str:
    if "pastel" in activity.tags:
        return f"The {setting.place.removeprefix('the ')} glowed gentle and bright, and {setting.sound}."
    return setting.sound


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} pirate who loved bright things and brave little chances.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; even the word "
        f"seemed to bounce like a tiny drum on the deck."
    )


def set_sail(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(tale_sound(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, then wanted to do it again, and still wanted one more try.")


def warns(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"Careful," {hero.pronoun("possessive")} {parent.label} said. '
        f'"If you {activity.verb}, your {prize.label} may get {activity.soil}."'
    )
    return True


def repeat_try(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["repetition"] = hero.memes.get("repetition", 0.0) + 1
    world.say(f"{hero.id} reached once, then again, and then one last time, because curiosity is a stubborn tide.")


def kind_turn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    sim = world.copy()
    h = sim.get(hero.id)
    g = sim.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers)))
    g.worn_by = h.id
    _do_activity(sim, h, activity, narrate=False)
    sim_prize = sim.get(prize.id)
    if sim_prize.meters.get("dirty", 0.0) >= THRESHOLD:
        return None
    real = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    real.worn_by = hero.id
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled kindly and said, "
        f'"How about we {gear.prep} and then {activity.verb} together?"'
    )
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["curiosity"] = max(0.0, hero.memes.get("curiosity", 0.0) - 0.5)
    world.say(
        f"{hero.id} nodded, then grinned. {hero.id} liked the kind plan and wore the safe gear."
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, {prize.phrase} stayed clean, and the {parent.label} laughed like a warm wave."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"traits": ["little", trait], "curiosity": 0.0, "kindness": 0.0, "repetition": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves(world, hero, activity)
    world.say(f"The captain gave {hero.id} {prize.phrase}.")
    world.say(f"{hero.id} treasured {prize.label} like a tiny flag from a bright harbor.")

    world.para()
    set_sail(world, hero, parent, activity)
    wants(world, hero, activity)
    warns(world, parent, hero, activity, prize)
    repeat_try(world, hero, activity)

    _do_activity(world, hero, activity, narrate=True)
    world.say(f"The first try was not enough; the second try made the {prize.label} look a little risky.")
    gear = kind_turn(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)
        hero.memes["kindness"] += 1

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short pirate tale for a young child that includes the word "{act.keyword}" and the word "pastel".',
        f"Tell a story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Write a gentle pirate story with repetition, curiosity, and kindness, ending with a safe plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} pirate, and {hero.pronoun('possessive')} captain.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}, and {hero.id} wanted to try it again because curiosity kept tugging.",
        ),
        QAItem(
            question=f"What made the captain worry about the {prize.label}?",
            answer=f"The captain worried because {act.gerund} could leave the {prize.label} {act.soil}.",
        ),
        QAItem(
            question=f"What kind words helped the story end well?",
            answer=f"The captain offered a kind safer plan, and that turned the problem into a happy choice.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the safe gear help?",
            answer=f"The story used {gear.label} so {hero.id} could {act.verb} without ruining {prize.phrase}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and try to learn more.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, or speak gently so someone else feels cared for.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again.",
        ),
        QAItem(
            question="What is a blossom?",
            answer="A blossom is a flower bloom, often soft and pretty when it opens.",
        ),
        QAItem(
            question="What does pastel mean?",
            answer="Pastel means soft, light colors that look gentle and bright.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with pastel blossoms, repetition, curiosity, and kindness.")
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
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="harbor", activity="blossom", prize="flower_sash", name="Mina", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="deck", activity="blossom", prize="gloves", name="Cai", gender="boy", parent="father", trait="kind"),
            StoryParams(place="garden_island", activity="blossom", prize="flower_sash", name="Lena", gender="girl", parent="mother", trait="cheerful"),
        ]
        samples = [generate(p) for p in curated]
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
