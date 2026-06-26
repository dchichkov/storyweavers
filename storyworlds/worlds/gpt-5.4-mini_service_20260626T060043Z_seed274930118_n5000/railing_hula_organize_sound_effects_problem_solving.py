#!/usr/bin/env python3
"""
storyworlds/worlds/railing_hula_organize_sound_effects_problem_solving.py
==========================================================================

A tiny tall-tale story world about a child, a railing, a hula wish, and the
careful art of organizing sound effects before the whole show rattles loose.

The seed idea:
- A child wants to hula near a railing.
- The show has sound effects that clatter and tinkle.
- A grown-up worries the noise and motion will cause trouble.
- They solve it by organizing the sound effects and choosing a safer spot.

This script keeps the story world small, classical, and state-driven:
- physical meters: noisiness, clutter, wobble, calm
- emotional memes: excitement, worry, pride, relief
- the ending proves what changed in the world model.

It also includes an inline ASP twin for the main reasonableness gate:
- the setting must support the hula act
- the at-risk object must actually be at risk
- there must be a believable organizing fix

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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["noise", "clutter", "wobble", "calm"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "relief", "focus", "spirit"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    effect: str
    zone: set[str]
    keyword: str


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
    quiets: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_noise_spread(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or item.worn_by != actor.id:
                continue
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("noise_spread", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wobble"] += 1
            item.meters["clutter"] += 1
            out.append(f"The {item.label} started to wobble with the racket.")
    return out


def _r_clutter_worry(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["clutter"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That sent a speck of worry through {carer.label}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_noise_spread, _r_clutter_worry):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the porch":
        return "The porch boards were wide as piecrusts, and the railing ran along the edge like a fence of straight-backed soldiers."
    if setting.place == "the barn":
        return "The barn had a long aisle, a high roof, and beams that seemed ready to echo every tap."
    return f"{setting.place.capitalize()} was open and bright, ready for a big little show."


def predict_trouble(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return prize.meters["clutter"] >= THRESHOLD or prize.meters["wobble"] >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["noise"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id in gear.quiets and prize.region in gear.covers:
            return gear
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a big wish and a bigger smile.")


def loves_show(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["spirit"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; every beat made {hero.pronoun('possessive')} toes want to leap.")


def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} as carefully as if it were a crown.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["focus"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right there by the railing.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_trouble(world, hero, activity, prize.id):
        return False
    world.facts["trouble"] = True
    world.say(f'"If you start to {activity.verb}, your {prize.label} may get knocked askew," {parent.label} said.')
    return True


def rattle(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} tried to {activity.rush}, and the sound effects went clink, clank, and clatter.")


def problem_solve(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    g.worn_by = hero.id
    if predict_trouble(world, hero, activity, prize.id):
        g.worn_by = None
        del world.entities[g.id]
        return None
    world.say(f"{parent.label} had a notion: {gear.prep}.")
    return gear


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["worry"] = 0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} nodded, and together they {gear.tail}.")
    world.say(f"Then the sound effects were arranged neat as cornhusks, {hero.id} began to {activity.gerund}, and the {prize.label} stayed steady by the railing.")


SETTINGS = {
    "porch": Setting(place="the porch", outdoors=True, affords={"hula"}),
    "yard": Setting(place="the yard", outdoors=True, affords={"hula"}),
    "barn": Setting(place="the barn", outdoors=False, affords={"hula"}),
}

ACTIVITIES = {
    "hula": Activity(
        id="hula",
        verb="hula",
        gerund="hula-hooping",
        rush="whirl faster",
        sound="clink-clank",
        effect="a merry whirl",
        zone={"torso", "arms"},
        keyword="hula",
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a paper lantern with gold stars",
        type="lantern",
        region="torso",
    ),
    "bellbox": Prize(
        label="bell box",
        phrase="a bright little bell box",
        type="bellbox",
        region="arms",
    ),
    "banner": Prize(
        label="banner",
        phrase="a long parade banner",
        type="banner",
        region="torso",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="basket",
        label="a woven basket",
        covers={"torso", "arms"},
        quiets={"hula"},
        prep="put the sound effects in a woven basket and tie the lid down",
        tail="moved the clatter into the basket and laced it shut",
    ),
    Gear(
        id="cloth",
        label="a thick cloth wrap",
        covers={"arms"},
        quiets={"hula"},
        prep="wrap the bell box in a thick cloth",
        tail="wrapped the noisy bits until they sat snug as kittens",
    ),
]

NAMES = ["Molly", "June", "Nell", "Toby", "Penny", "Wes", "Lena", "Ike"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            activity = ACTIVITIES[act]
            for prize_id, prize in PRIZES.items():
                if prize.region in activity.zone and select_gear(activity, prize):
                    combos.append((place, act, prize_id))
    return combos


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if name in {"Molly", "June", "Nell", "Penny", "Lena"} else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region, caretaker=parent.id))
    sound = world.add(Entity(id="SoundEffects", type="thing", label="sound effects", phrase="a bundle of clinks and jingles", region="arms", caretaker=parent.id))
    hero.memes["joy"] += 1

    introduce(world, hero)
    loves_show(world, hero, activity)
    prize_line(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    world.say(f"Near the railing sat the sound effects, all mixed together like a drawer after a windstorm.")
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    rattle(world, hero, activity)

    world.para()
    gear = problem_solve(world, parent, hero, activity, prize)
    if gear:
        resolve(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear, sound=sound)
    return world


KNOWLEDGE = {
    "hula": [("What is hula dancing?", "Hula dancing is a dance with swaying hips, gentle steps, and graceful arm movements.")],
    "railing": [("What is a railing?", "A railing is a long bar or fence-like support along stairs, porches, or balconies to help keep people from falling.")],
    "organize": [("What does it mean to organize something?", "To organize something means to sort it, arrange it, and put it where it belongs so it is easier to use.")],
    "sound": [("What are sound effects?", "Sound effects are special noises made on purpose to help a story, play, or show feel lively.")],
    "problem": [("What is problem solving?", "Problem solving means thinking carefully about a trouble and choosing a good way to fix it.")],
}


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), quiets(G, A), covers(G, R), worn_on(P, R).
valid_story(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for q in sorted(g.quiets):
            lines.append(asp.fact("quiets", g.id, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story about {f["hero"].id} trying to {f["activity"].verb} near a railing while the sound effects jingle and jangle.',
        f"Tell a child-friendly story where {f['hero'].id} has to solve a noisy problem before {f['hero'].pronoun('possessive')} hula can begin.",
        "Write a short story with a railing, hula, and a clever way to organize sound effects.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do by the railing?",
            answer=f"{hero.id} wanted to {activity.verb} by the railing, because {hero.pronoun().capitalize()} had a great big hula wish.",
        ),
        QAItem(
            question=f"What worried the {parent.type} about the {prize.label}?",
            answer=f"The {parent.type} worried that the {prize.label} might get knocked askew by all the motion and clatter near the railing.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They solved it by using {gear.label} to organize the sound effects, which made the noisy pieces sit still and safe.",
        ),
        QAItem(
            question="What was true at the end of the story?",
            answer=f"At the end, {hero.id} was {activity.gerund}, the sound effects were neat and quiet, and the {prize.label} stayed steady by the railing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("railing", "hula", "organize", "sound", "problem"):
        for q, a in KNOWLEDGE[key]:
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not reasonably threaten a {prize.label} in this tiny world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (pr.region in act.zone and select_gear(act, pr)):
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
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent)
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
    ap = argparse.ArgumentParser(description="Tall-tale story world: railing, hula, organize, and sound-effects problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - asps))
    print("clingo only:", sorted(asps - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=r, name="June", parent="mother")) for p, a, r in valid_combos()]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
