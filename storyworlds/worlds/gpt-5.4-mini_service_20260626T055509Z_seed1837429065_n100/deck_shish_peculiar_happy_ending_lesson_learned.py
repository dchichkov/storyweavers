#!/usr/bin/env python3
"""
A small storyworld about a peculiar deck-day shish snack and a teamwork fix.

This world is built around a child-friendly rhyming story:
- a little cast with typed entities
- physical meters and emotional memes
- a state-driven turn and happy ending
- a reasonableness gate for valid stories
- an inline ASP twin for parity checks
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the deck"
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] = item.meters.get("mess", 0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got spotted and smudgy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] = caretaker.memes.get("worry", 0) + 1
        out.append(f"That would make more work for {caretaker.label}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character" and e.id == world.facts.get("hero_id")), None)
    helper = next((e for e in world.characters() if e.id == world.facts.get("helper_id")), None)
    if not hero or not helper:
        return out
    if hero.memes.get("stuck", 0) < THRESHOLD or helper.memes.get("helping", 0) < THRESHOLD:
        return out
    sig = ("teamwork", hero.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    out.append("__teamwork__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spill, _r_worry, _r_teamwork):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            if s != "__teamwork__":
                world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_spill(world: World, actor: Entity, activity: Activity, prize: Prize) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.get("prize")
    return item.meters.get("dirty", 0) >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    propagate(world, narrate=narrate)


def setup_line(hero: Entity, helper: Entity, activity: Activity, prize: Prize, setting: Setting) -> str:
    return (
        f"On the deck, {hero.id} and {helper.id} stood in sunlit cheer, "
        f"while a {prize.label} looked rather dear."
    )


def rhyme_line(activity: Activity) -> str:
    return f"{activity.keyword.capitalize()} was peculiar, with a tickle and a click; it made the day feel brisk."


def tell_story(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity, gear: Optional[Gear]) -> None:
    world.say(setup_line(hero, helper, activity, prize, world.setting))
    world.say(f"{hero.id} loved to {activity.verb}, with a grin so bright and bold.")
    world.say(rhyme_line(activity))
    world.say(f"But {hero.id} saw {prize.phrase}, and {hero.pronoun('possessive')} heart did hold.")
    world.say(
        f"{helper.id} warned, 'If you {activity.verb}, your {prize.label} may get {activity.soil}.'"
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["stuck"] = hero.memes.get("stuck", 0) + 1
    helper.memes["helping"] = helper.memes.get("helping", 0) + 1
    world.say(f"{hero.id} frowned, then pointed at the sky, and tried not to make a fuss.")
    gear_def = gear
    if gear_def:
        world.say(f"Then {helper.id} smiled and said, '{gear_def.prep}, and we can still make a truce.'")
        g = world.add(Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            protective=True,
            owner=hero.id,
        ))
        g.worn_by = hero.id
        hero.memes["stuck"] = 0
        _do_activity(world, hero, activity, narrate=True)
        if world.get("prize").meters.get("dirty", 0) < THRESHOLD:
            world.say(
                f"{hero.id} and {helper.id} went together, side by side, to {activity.gerund}, "
                f"and the {prize.label} stayed neat."
            )
            world.say(f"They laughed in the breeze, and all the worry drifted away.")
        else:
            world.say(f"Oops, the plan did not help, so the deck-day turned to a sticky fright.")
    else:
        world.say(f"No snug fix could fit, so the day stayed in a messy fight.")


SETTINGS = {
    "deck": Setting(place="the deck", affords={"shish"}),
}

ACTIVITIES = {
    "shish": Activity(
        id="shish",
        verb="make shish",
        gerund="making shish",
        rush="rush to the skewers",
        mess="splash",
        soil="splotchy",
        zone={"hands", "torso"},
        keyword="shish",
        tags={"shish", "peculiar"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
}

GEAR = [
    Gear(
        id="apron",
        label="a little apron",
        covers={"torso"},
        guards={"splash"},
        prep="let's tie on a little apron",
        tail="tied on the little apron",
    ),
]

CURATED = [
    ("deck", "shish", "shirt"),
]

GIRL_NAMES = ["Mina", "Lila", "Tara", "Nina"]
BOY_NAMES = ["Owen", "Theo", "Ravi", "Finn"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about a {f["place"]} and the word "{f["activity"].keyword}".',
        f"Tell a gentle tale where {f['hero'].id} wants to {f['activity'].verb} but a {f['prize'].label} needs to stay clean.",
        f"Write a peculiar little story with teamwork, a happy ending, and a learned lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the deck?",
            answer=f"{hero.id} wanted to {activity.verb}, and the day felt peculiar and bright.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the {prize.label}?",
            answer=f"{helper.id} worried because {activity.gerund} could make the {prize.label} {activity.soil}.",
        ),
        QAItem(
            question="What did they learn together?",
            answer="They learned that teamwork can turn a tricky moment into a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a deck?",
            answer="A deck is a flat wooden platform beside a house where people can sit, play, or eat outside.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to finish something.",
        ),
        QAItem(
            question="What does peculiar mean?",
            answer="Peculiar means a little strange or unusual in a way that stands out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        out.append(f"{e.id} ({e.type}): {' '.join(bits)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not honestly threaten the {prize.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "deck":
        raise StoryError("(No story: this tiny world only knows the deck.)")
    combos = valid_combos()
    if args.activity and args.activity != "shish":
        raise StoryError("(No story: this world only knows shish-making.)")
    if args.prize and args.prize != "shirt":
        raise StoryError("(No story: this world only knows the shirt prize.)")
    if not combos:
        raise StoryError("(No valid story combo.)")
    place, act, prize = combos[0]
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or "Mom"
    return StoryParams(place=place, activity=act, prize=prize, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy"))
    helper = world.add(Entity(id=params.helper, kind="character", type="mother" if params.helper == "Mom" else "father", label=params.helper))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, caretaker=helper.id))
    activity = ACTIVITIES[params.activity]
    gear = select_gear(activity, PRIZES[params.prize])

    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, place=params.place)
    world.facts["hero_id"] = hero.id
    world.facts["helper_id"] = helper.id

    world.say(f"On the deck, {hero.id} found a shish skewered snack, so shiny and slick.")
    world.say(f"It looked peculiar and tasty, and made {hero.pronoun('possessive')} smile grow quick.")
    world.say(f"But {helper.id} frowned a little, for the {prize.label} must stay clean and bright.")
    world.say(f"'{activity.verb.capitalize()} is fun,' said {hero.id}, 'but I want a happy night.'")
    hero.memes["stuck"] = 1
    helper.memes["helping"] = 1

    if gear:
        g = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, owner=hero.id))
        g.worn_by = hero.id
        world.say(f"Then {helper.id} said, '{gear.prep}.' That plan felt just right.")
        _do_activity(world, hero, activity, narrate=True)
        if prize.meters.get("dirty", 0) < THRESHOLD:
            world.say(f"Together they laughed and learned: teamwork can turn wrong into right.")
            world.say(f"So the deck stayed neat, the shish stayed rich, and the story ended in delight.")
    else:
        world.say("No tidy fix was found, so the day could not take flight.")

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: deck, shish, peculiar, teamwork, happy ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


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
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, act, prize in CURATED:
            params = StoryParams(place=place, activity=act, prize=prize, name="Mina", helper="Mom")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
