#!/usr/bin/env python3
"""
storyworlds/worlds/pepe_ammunition_lesson_learned_curiosity_happy_ending.py
=========================================================================

A small pirate-tale storyworld about Pepe, ammunition, curiosity, and a lesson
learned that ends in a happy ending.

The world is intentionally tiny and constraint-driven:
- Pepe is a young pirate on a ship.
- The ship carries ammunition for the cannons.
- Pepe's curiosity can lead to a risky choice.
- A captain or mate warns Pepe, and a safer task resolves the tension.
- The ending proves Pepe learned the lesson and the ship stays ready.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- Python reasonableness gate and inline ASP twin
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "captain", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the pirate ship"
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


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
    helper: str
    trait: str
    seed: Optional[int] = None


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


SETTINGS = {
    "ship": Setting(place="the pirate ship", affords={"signal", "repair"}),
    "deck": Setting(place="the bright deck", affords={"signal"}),
    "cove": Setting(place="the hidden cove", affords={"signal"}),
}

ACTIVITIES = {
    "signal": Activity(
        id="signal",
        verb="help with the cannon signal",
        gerund="helping with the cannon signal",
        rush="run toward the cannon and touch the powder",
        mess="soot",
        soil="smudged with soot",
        zone={"hands", "face"},
        keyword="cannon",
        tags={"cannon", "ammunition", "pirate"},
    ),
    "repair": Activity(
        id="repair",
        verb="help load ammunition",
        gerund="loading ammunition carefully",
        rush="reach for the powder bag",
        mess="dust",
        soil="dusty and messy",
        zone={"hands"},
        keyword="ammunition",
        tags={"ammunition", "pirate"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a shiny pirate hat",
        type="hat",
        region="head",
        genders={"boy", "girl"},
    ),
    "jacket": Prize(
        label="jacket",
        phrase="a neat little jacket",
        type="jacket",
        region="torso",
        genders={"boy", "girl"},
    ),
    "gloves": Prize(
        label="gloves",
        phrase="new sailing gloves",
        type="gloves",
        region="hands",
        plural=True,
        genders={"boy", "girl"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a canvas apron",
        covers={"hands", "torso"},
        guards={"soot", "dust"},
        prep="put on a canvas apron first",
        tail="went to fetch the canvas apron",
    ),
    Gear(
        id="mask",
        label="a cloth mask",
        covers={"face"},
        guards={"soot"},
        prep="tie on a cloth mask first",
        tail="went to get the cloth mask",
    ),
    Gear(
        id="washcloth",
        label="a wet washcloth",
        covers={"hands"},
        guards={"dust"},
        prep="wrap his hands with a wet washcloth first",
        tail="went to get the wet washcloth",
    ),
]

GIRL_NAMES = ["Pia", "Mina", "Luna", "Nia", "Tess"]
BOY_NAMES = ["Pepe", "Javi", "Nico", "Toma", "Rico"]
HELPERS = ["captain", "mate"]
TRAITS = ["curious", "brave", "cheerful", "playful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), region(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), region(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
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
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
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


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if actor.meters.get("mess", 0) < THRESHOLD:
                continue
            if item.region not in world.zone:
                continue
            if ("soak", actor.id, item.id) in world.fired:
                continue
            world.fired.add(("soak", actor.id, item.id))
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            out.append(f"{actor.id}'s {item.label_word} got smudged.")
    return out


def _lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if actor.memes.get("warned", 0) < THRESHOLD:
            continue
        if ("lesson", actor.id) in world.fired:
            continue
        world.fired.add(("lesson", actor.id))
        actor.memes["lesson_learned"] = actor.memes.get("lesson_learned", 0) + 1
        actor.memes["curiosity"] = 0
        out.append(f"{actor.id} remembered the warning and slowed down.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_soak, _lesson):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_gear_for(activity: Activity, prize: Prize) -> Optional[Gear]:
    return select_gear(activity, prize)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         helper_type: str, hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or [])))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    world.say(f"{hero.id} was a little {hero.traits[1] if len(hero.traits) > 1 else 'curious'} pirate on {world.setting.place}.")
    world.say(f"{hero.id} loved {activity.gerund}, because {activity.keyword} was full of mystery.")
    world.say(f"One day, {helper.label_word} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} saw the ship's ammunition near the cannon.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {helper.label_word} held up a hand and warned, \"Not too close.\"")
    hero.memes["warned"] = hero.memes.get("warned", 0) + 1
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f"{hero.id}'s eyes got wide with curiosity.")
    world.say(f"{hero.id} tried to {activity.rush},")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    _do_activity(world, hero, activity, narrate=True)

    world.para()
    gear = select_gear_for(activity, prize)
    if gear is None:
        raise StoryError("No reasonable gear exists for this combination.")
    world.say(f"Then {helper.label_word} smiled and said, \"Let's be careful and use {gear.label} instead.\"")
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0) + 1
    world.say(f"{hero.id} listened, and {hero.id} saw the lesson clearly: safe hands keep everyone ready.")
    world.say(f"They {gear.tail}, and soon {hero.id} could help without making a mess.")
    world.say(f"In the end, {hero.id} was still {activity.gerund}, {prize.label} stayed clean, and the ship was ready to sail with a happy ending.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short pirate tale for a young child about {hero.id}, ammunition, and a careful lesson learned.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} near the cannon but learns a safer way with help.",
        f'Write a happy-ending pirate story that uses the word "{act.keyword}" and includes a curious child pirate.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"The story is about {hero.id}, a little pirate who was curious on the ship.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the cannon?",
            answer=f"{hero.id} wanted to {act.verb}, but that was risky because the ship carried ammunition.",
        ),
        QAItem(
            question=f"Who helped {hero.id} make a safer choice?",
            answer=f"The {helper.type} helped {hero.id} slow down and choose a safer way to help.",
        ),
        QAItem(
            question=f"Why was {hero.id} warned about the ammunition?",
            answer=f"{helper.label_word} warned {hero.id} because getting too close could make a mess and spoil the careful work near the cannon.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} learning the lesson, staying curious but careful, and the ship having a happy ending.",
        ),
        QAItem(
            question=f"What gear helped the plan work?",
            answer=f"They used {gear.label} so {hero.id} could help without making a mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ammunition?",
            answer="Ammunition is what a cannon uses, like cannonballs or powder, to help it fire safely when the crew is ready.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone remembers after trying something risky or making a mistake.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe and glad.",
        ),
    ]


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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", activity="signal", prize="hat", name="Pepe", gender="boy", helper="captain", trait="curious"),
    StoryParams(place="deck", activity="repair", prize="gloves", name="Pepe", gender="boy", helper="mate", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put {prize.label} at risk.)"
    return f"(No story: no gear in this little pirate world can safely fix {activity.verb} with {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about Pepe, ammunition, curiosity, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper", choices=HELPERS)
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
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or (rng.choice(BOY_NAMES) if gender == "boy" else rng.choice(GIRL_NAMES))
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.helper, [params.trait])
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
            print(f"  {place:8} {act:8} {prize:8}")
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
