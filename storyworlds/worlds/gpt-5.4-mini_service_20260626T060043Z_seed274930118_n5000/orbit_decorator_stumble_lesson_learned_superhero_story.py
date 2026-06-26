#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero-story domain:
an orbiting hero, a decorator, a stumble, and a lesson learned.

The story premise is simple:
- a young hero loves a daring sky-orbit trick
- a decorator is preparing something important
- an awkward stumble creates a problem
- the hero learns a lesson and fixes things with help

The world is simulated with typed entities, physical meters, and emotional memes.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    stumble: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in getattr(e, "covers", set()) for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _rule_stumble(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("stumble", 0) < THRESHOLD:
            continue
        sig = ("stumble", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["embarrassed"] = actor.memes.get("embarrassed", 0) + 1
        out.append(f"{actor.pronoun().capitalize()} nearly fell and had to catch {actor.pronoun('object')}self.")
    return out


def _rule_scuff(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("stumble", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.owner != actor.id:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("scuff", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scuffed"] = item.meters.get("scuffed", 0) + 1
            actor.memes["worry"] = actor.memes.get("worry", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got scuffed in the rush.")
    return out


CAUSAL_RULES = [
    _rule_stumble,
    _rule_scuff,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, hero: Entity, action: Action, prize: Prize) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    prize_ent = sim.get(prize.id)
    return {
        "scuffed": prize_ent.meters.get("scuffed", 0) >= THRESHOLD,
        "worry": hero.memes.get("worry", 0),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        raise StoryError("That action does not fit this setting.")
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0) + 1
    actor.meters["stumble"] = actor.meters.get("stumble", 0) + 1
    actor.memes["rush"] = actor.memes.get("rush", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little superhero who loved doing brave things in the sky.")


def loves_orbit(world: World, hero: Entity, action: Action) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved to {action.verb}, especially when the city lights glittered below.")


def decorator_scene(world: World, decorator: Entity, prize: Entity) -> None:
    world.say(
        f"{decorator.id} the decorator was carefully working on {prize.phrase}, "
        f"because the celebration had to look perfect."
    )


def arrives(world: World, hero: Entity, decorator: Entity, action: Action) -> None:
    world.say(f"One day, {hero.id} and {decorator.id} went to {world.setting.place}.")
    world.say(f"The plan was to {action.verb}, but the air felt tricky and windy.")


def wants(world: World, hero: Entity, action: Action) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {action.verb} right away.")


def warn(world: World, decorator: Entity, hero: Entity, action: Action, prize: Prize) -> None:
    pred = predict(world, hero, action, prize)
    if pred["scuffed"]:
        world.facts["lesson"] = "look before you leap"
        world.say(
            f'"Careful," {decorator.id} said. "If you {action.verb}, you may stumble "
            f"and spoil {hero.pronoun("possessive")} {prize.label}."'
        )


def stumble(world: World, hero: Entity, action: Action) -> None:
    hero.memes["stuck"] = hero.memes.get("stuck", 0) + 1
    world.say(f"But {hero.id} did not slow down, and {hero.pronoun()} stumbled hard while trying to {action.verb}.")
    world.say(f"{hero.pronoun().capitalize()} wobbled, windmilled {hero.pronoun('possessive')} arms, and almost dropped the costume ribbon.")


def fix(world: World, decorator: Entity, hero: Entity, action: Action, prize: Prize, gear: Gear) -> None:
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=decorator.id,
        protective=True,
    ))
    gear_ent.worn_by = hero.id
    gear_ent.covers = set(gear.covers)  # type: ignore[attr-defined]
    world.say(
        f'Then {decorator.id} smiled and said, "{gear.prep}."'
    )
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    hero.memes["learned"] = hero.memes.get("learned", 0) + 1
    hero.memes["embarrassed"] = 0
    world.say(
        f"{hero.id} took a deep breath, wore {gear.label}, and tried again more carefully."
    )
    world.say(
        f"This time {hero.id} could {action.verb}, {prize.label} stayed safe, and the day felt proud instead of shaky."
    )
    world.say(f"Lesson learned: brave heroes look before they leap.")
    world.say(f"After that, {hero.id} kept orbiting with steadier feet and a wiser grin.")


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, decorator_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero"))
    decorator = world.add(Entity(id=decorator_name, kind="character", type="decorator"))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type="prize",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=decorator.id,
    ))

    intro(world, hero)
    loves_orbit(world, hero, action)
    decorator_scene(world, decorator, prize)

    world.para()
    arrives(world, hero, decorator, action)
    wants(world, hero, action)
    warn(world, decorator, hero, action, prize)
    stumble(world, hero, action)

    world.para()
    gear = select_gear(action, prize)
    if gear is None:
        raise StoryError("No reasonable gear exists for this story.")
    fix(world, decorator, hero, action, prize, gear)

    world.facts.update(hero=hero, decorator=decorator, prize=prize, action=action, gear=gear, setting=setting)
    return world


SETTINGS = {
    "tower": Setting(place="the clock tower rooftop", affords={"orbit"}),
    "dock": Setting(place="the harbor dock", affords={"orbit"}),
    "museum": Setting(place="the museum balcony", affords={"decorator"}),
}

ACTIONS = {
    "orbit": Action(
        id="orbit",
        verb="orbit the tall tower",
        gerund="orbiting the tower",
        stumble="stumble on the ledge",
        risk="stumble",
        mess="dizzy",
        zone={"feet", "legs"},
        keyword="orbit",
        tags={"orbit", "sky"},
    ),
    "decorator": Action(
        id="decorator",
        verb="help the decorator hang streamers",
        gerund="helping the decorator",
        stumble="stumble into the paint tray",
        risk="stumble",
        mess="busy",
        zone={"hands", "torso"},
        keyword="decorator",
        tags={"decorator", "celebration"},
    ),
}

PRIZES = {
    "cape": Prize(id="cape", label="cape", phrase="a bright red cape", region="torso"),
    "badge": Prize(id="badge", label="badge", phrase="a shiny hero badge", region="torso"),
    "boots": Prize(id="boots", label="boots", phrase="polished rescue boots", region="feet", plural=True),
}

GEAR = [
    Gear(id="grip_gloves", label="grip gloves", covers={"hands"}, guards={"stumble"}, prep="put on grip gloves first", tail="slowed down and tried again", plural=True),
    Gear(id="hover_belt", label="a hover belt", covers={"legs", "feet"}, guards={"stumble"}, prep="clip on a hover belt first", tail="hovered safely and tried again"),
    Gear(id="steady_cape", label="a steady cape clip", covers={"torso"}, guards={"stumble"}, prep="fasten the cape clip first", tail="moved carefully and tried again"),
]

HERO_NAMES = ["Nova", "Blaze", "Piper", "Milo", "Zara", "Finn", "Juno", "Kai"]
DECORATOR_NAMES = ["Dottie", "Mina", "Rico", "Tess", "Nell"]
TRAITS = ["brave", "curious", "spunky", "kind", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIONS[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    decorator: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story using the words "orbit", "{f["decorator"].id}", and "stumble".',
        f"Tell a child-friendly superhero story where {f['hero'].id} wants to {f['action'].verb} but learns a lesson after a stumble.",
        f"Write a story about a decorator, a brave hero, and a lesson learned in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    decorator = f["decorator"]
    prize = f["prize"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who wanted to {action.verb} in the story?",
            answer=f"{hero.id}, the little superhero, wanted to {action.verb}."
        ),
        QAItem(
            question=f"Why did {decorator.id} worry about {hero.id}?",
            answer=f"{decorator.id} worried because {hero.id} might stumble and ruin {hero.pronoun('possessive')} {prize.label}."
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was to look before you leap and slow down when the path is tricky."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does orbit mean?", answer="To orbit means to move around something in a circle."),
        QAItem(question="What is a decorator?", answer="A decorator is a person who makes a place look nice with things like banners and colors."),
        QAItem(question="What does it mean to stumble?", answer="To stumble means to trip or lose your balance for a moment."),
        QAItem(question="What does lesson learned mean?", answer="It means someone understood a better way to act after something went wrong."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"protective=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(parts)}")
    return "\n".join(lines)


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return f"(No story: {action.gerund} does not endanger a {prize.label} here.)"
    return f"(No story: no gear in this world can reasonably protect a {prize.label} from that stumble.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIONS[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    decorator = args.decorator or rng.choice(DECORATOR_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, decorator=decorator, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.activity], PRIZES[params.prize], params.hero, params.decorator)
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
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,"stumble"), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
        lines.append(asp.fact("risk", aid, a.risk))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: orbit, decorator, stumble, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--decorator")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="tower", activity="orbit", prize="cape", hero="Nova", decorator="Dottie", trait="brave"),
    StoryParams(place="dock", activity="orbit", prize="boots", hero="Blaze", decorator="Rico", trait="curious"),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
