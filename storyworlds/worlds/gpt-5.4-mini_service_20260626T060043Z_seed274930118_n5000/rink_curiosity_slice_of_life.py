#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str = "the rink"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str
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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_curious_touch(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if actor.meters.get("reach", 0) < THRESHOLD:
            continue
        sig = ("touch", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
        out.append(f"{actor.id} leaned closer, curious enough to touch the edge of the rink.")
    return out


def _r_slip(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("skate", 0) < THRESHOLD:
            continue
        if actor.meters.get("steady", 0) >= THRESHOLD:
            continue
        sig = ("slip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0) + 1
        out.append(f"{actor.id} wobbled on the ice and had to slow down.")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("worry", 0) < THRESHOLD:
            continue
        if actor.memes.get("help_offered", 0) < THRESHOLD:
            continue
        sig = ("help", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0
        actor.memes["joy"] = actor.memes.get("joy", 0) + 1
        out.append(f"A helper showed {actor.id} how to balance, and the worry melted away.")
    return out


CAUSAL_RULES = [Rule("curious_touch", _r_curious_touch), Rule("slip", _r_slip), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.say(f"{actor.id} stepped closer to the rink, curious about what would happen next.")
    actor.meters["curious_step"] = actor.meters.get("curious_step", 0) + 1
    actor.meters["skate"] = actor.meters.get("skate", 0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {"slip": sim.get(actor.id).memes.get("worry", 0) >= THRESHOLD}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards:
            return gear
    return None


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return bool(select_gear(activity, prize))


SETTING = Setting(place="the rink", indoors=True, affords={"skate", "watch"})
ACTIVITIES = {
    "skate": Activity(
        id="skate",
        verb="skate on the ice",
        gerund="skating on the ice",
        rush="glide too fast",
        mess="slippery",
        soil="all slippery",
        keyword="rink",
        tags={"rink", "ice", "curiosity"},
    ),
    "watch": Activity(
        id="watch",
        verb="watch the skaters",
        gerund="watching the skaters",
        rush="rush to the rail",
        mess="nothing",
        soil="nothing",
        keyword="rink",
        tags={"rink", "curiosity"},
    ),
}
PRIZES = {
    "mittens": Prize(label="mittens", phrase="a pair of warm mittens", type="mittens", kind="hands", plural=True),
    "scarf": Prize(label="scarf", phrase="a soft blue scarf", type="scarf", kind="neck"),
}
GEAR = [
    Gear(id="helmet", label="a little helmet", covers={"head"}, guards={"slippery"}, prep="put on a little helmet", tail="tied the helmet snugly"),
    Gear(id="knee_pads", label="knee pads", covers={"knees"}, guards={"slippery"}, prep="pull on knee pads", tail="snapped the knee pads into place", plural=True),
]

GIRL_NAMES = ["Mina", "Lily", "Nora", "Tia", "Ivy"]
BOY_NAMES = ["Ben", "Noah", "Eli", "Finn", "Leo"]
TRAITS = ["curious", "gentle", "careful", "bright", "quiet"]


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


ASP_RULES = r"""
setting(rink).
affords(rink, skate).
affords(rink, watch).

activity(skate).
activity(watch).

mess_of(skate, slippery).
mess_of(watch, nothing).

gear(helmet).
guards(helmet, slippery).

gear(knee_pads).
guards(knee_pads, slippery).

prize(mittens).
prize(scarf).

valid(Place, Activity, Prize) :- affords(Place, Activity), activity(Activity), prize(Prize), mess_of(Activity, M), guards(_, M).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "rink"), asp.fact("affords", "rink", "skate"), asp.fact("affords", "rink", "watch")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("mess_of", a, ACTIVITIES[a].mess))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in [SETTING.place.replace("the ", "")]:
        for act in ACTIVITIES:
            for prize in PRIZES:
                if reasonableness_gate(ACTIVITIES[act], PRIZES[prize]):
                    combos.append((place, act, prize))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(p - a))
    print("only in clingo:", sorted(a - p))
    return 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, plural=prize_cfg.plural))

    hero.memes["curiosity"] = 1
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved noticing tiny details.")
    world.say(f"{hero.id} kept looking at {setting.place} because {hero.pronoun('subject')} was curious about the ice and the bright lights above it.")
    world.say(f"{hero.id} had {hero.pronoun('possessive')} {prize.label} on, and the soft {prize.label} felt nice and safe.")

    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} eyes kept drifting toward the shiny edge of the rink.")
    if predict(world, hero, activity)["slip"]:
        world.say(f'"If you rush on that ice, you might wobble," {hero.pronoun("possessive")} {parent.label} said.')
    hero.memes["help_offered"] = 1
    hero.meters["steady"] = 0
    world.say(f"{hero.id} tried a careful step anyway and nearly slid.")
    propagate(world)

    world.para()
    gear = select_gear(activity, prize)
    if gear:
        world.say(f"Then {hero.pronoun('possessive')} {parent.label} smiled and said, \"How about we {gear.prep} first and take it slow?\"")
        world.say(f"{hero.id} nodded, and they {gear.tail}.")
        hero.meters["steady"] = 1
        hero.memes["joy"] = 1
        hero.memes["curiosity"] = 2
        world.say(f"After that, {hero.id} was {activity.gerund}, and the rink felt friendly instead of scary.")
        world.say(f"{hero.id} kept {prize_cfg.label} safe while learning just how the ice moved under little feet.")
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, trait=trait, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short slice-of-life story for a curious child at {world.setting.place} who wants to {act.verb}.',
        f"Tell a gentle story about {hero.id} and {hero.pronoun('possessive')} curiosity at the rink.",
        f'Write a simple story that includes the word "rink" and ends with a small, happy lesson about trying something new carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep staring at the rink?",
            answer=f"{hero.id} was curious about the ice and wanted to see what {act.verb} would feel like.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {parent.label} worry might happen on the ice?",
            answer=f"{parent.label.capitalize()} worried that {hero.id} might wobble or slide too fast while trying to {act.verb}.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel better before {hero.pronoun('possessive')} first careful steps?",
            answer=f"A calmer plan and gentle help from {hero.pronoun('possessive')} {parent.label} helped {hero.id} feel ready.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} at the rink?",
            answer=f"{hero.id} got to {act.gerund} carefully, with curiosity still shining and the day feeling friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a rink?", answer="A rink is a place with a smooth surface for skating, usually on ice or a special floor."),
        QAItem(question="Why do people wear skates at a rink?", answer="People wear skates so they can glide smoothly across the ice instead of walking on it."),
        QAItem(question="Why should someone move carefully on ice?", answer="Ice can be slippery, so careful steps help keep a person from falling."),
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rink", activity="skate", prize="mittens", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="rink", activity="watch", prize="scarf", name="Eli", gender="boy", parent="father", trait="quiet"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: nothing in the little rink world makes {prize.label} a reasoned concern for {activity.gerund}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not reasonableness_gate(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a curious child at the rink.")
    ap.add_argument("--place", choices=["rink"])
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
