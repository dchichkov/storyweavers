#!/usr/bin/env python3
"""
storyworlds/worlds/consonant_olive_accident_curiosity_tall_tale.py
===================================================================

A small tall-tale story world about Curiosity, a bowl of olives, and an
accident that turns a careful lesson about consonants into a bigger, funnier,
kindlier adventure.

Seed-tale premise:
- Curiosity loves sounding out words.
- A shiny bowl of olives sits near the lesson table.
- One little accident makes the olives roll everywhere.
- The grown-up turns the mishap into a playful hunt that teaches the child how
  consonants shape words, sounds, and naming.

The world keeps track of both physical state (meters) and feelings (memes), so
the prose comes from the simulation instead of from a fixed template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the reading nook"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "table"
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


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
        clone.zone = set(self.zone)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _rule_olives_roll(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("bump", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.type != "olive_bowl":
                continue
            sig = ("roll", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["spilled"] = item.meters.get("spilled", 0.0) + 1
            actor.memes["surprise"] = actor.memes.get("surprise", 0.0) + 1
            out.append("The olives rolled like marbles across the floor.")
    return out


def _rule_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.type != "olive_bowl":
            continue
        if item.meters.get("spilled", 0.0) < THRESHOLD:
            continue
        sig = ("cleanup", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.characters():
            ent.memes["help"] = ent.memes.get("help", 0.0) + 1
        out.append("The grown-up and the child picked up every last olive together.")
    return out


CAUSAL_RULES = [
    _rule_olives_roll,
    _rule_cleanup,
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


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that activity.")
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    world.zone = {"table", "floor"}
    propagate(world, narrate=narrate)


def predict_accident(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("spilled", 0.0) >= THRESHOLD


def build_setting() -> Setting:
    return Setting(
        place="the reading nook beside the window",
        affords={"letters", "sorting"},
    )


SETTINGS = {
    "nook": build_setting(),
}

ACTIVITIES = {
    "letters": Activity(
        id="letters",
        verb="sort the consonants",
        gerund="sorting consonants",
        rush="dash toward the letter cards",
        mess="bump",
        soil="a little knocked askew",
        keyword="consonant",
        tags={"consonant", "letters"},
    ),
    "sorting": Activity(
        id="sorting",
        verb="line up the consonants",
        gerund="lining up consonants",
        rush="lean across the table",
        mess="bump",
        soil="a little knocked askew",
        keyword="consonant",
        tags={"consonant", "letters"},
    ),
}

PRIZES = {
    "olive_bowl": Prize(
        label="bowl of olives",
        phrase="a shiny bowl of green olives",
        type="olive_bowl",
        region="table",
    ),
}

FIXES = [
    Fix(
        id="tray",
        label="a wide tray",
        prep="put the olives on a wide tray first",
        tail="moved the olives to a wide tray",
        guards={"bump"},
    ),
    Fix(
        id="cloth",
        label="a thick cloth",
        prep="spread a thick cloth under the bowl",
        tail="laid a thick cloth under the bowl",
        guards={"bump"},
    ),
]

HERO_NAMES = ["Curiosity", "Mabel", "Nina", "Eli"]
HELPER_NAMES = ["Aunt Poppy", "Uncle Reed", "Mama June", "Papa Will"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def choose_fix() -> Fix:
    return FIXES[0]


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if hero_name == "Curiosity" else "child",
        traits=["curious", "bright"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="aunt" if "Aunt" in helper_name else "uncle",
    ))
    prize = world.add(Entity(
        id="olives",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=helper.id,
    ))
    hero.memes["curiosity"] = 1.0
    world.say(
        f"{hero.id} loved the handsome sound of consonants, the kind of sound that could march, tumble, and sing."
    )
    world.say(
        f"Near the lesson table sat {prize.phrase}, glinting like green jewels in a pirate's treasure chest."
    )
    world.para()
    world.say(
        f"One afternoon, {hero.id} wanted to {activity.verb} in {setting.place} while {helper_name} watched with a smile."
    )
    world.say(
        f"{hero.id} leaned closer and closer, because curiosity can be a long-legged thing."
    )
    world.say(
        f"Then came the accident: {hero.id} gave the table a bump, and the bowl shivered."
    )
    hero.meters["bump"] = hero.meters.get("bump", 0.0) + 1
    propagate(world, narrate=True)
    world.para()
    fix = choose_fix()
    world.say(
        f'{helper_name} pointed to {fix.label} and said, "Let us make this into a safer sort of parade."'
    )
    world.say(
        f"They {fix.tail}, and the lesson went on with the consonants lined up like tidy fence posts."
    )
    world.say(
        f"By the end, {hero.id} was still curious, but now {hero.id} knew that a small accident can become a clever idea."
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        fix=fix,
        accident=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = f["activity"]
    return [
        f'Write a short tall tale for a child who loves the word "consonant" and gets into an olive accident.',
        f"Tell a lively story about {hero.id}, {helper.id}, and a bowl of olives while they work with consonants.",
        f"Write a funny, gentle story in which curiosity leads to an accident, then to a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = f["activity"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who got the story started by loving consonants so much?",
            answer=f"It was {hero.id}, who loved the handsome sound of consonants and could not stop looking at the lesson table.",
        ),
        QAItem(
            question=f"What accident happened with the olives?",
            answer=f"{hero.id} bumped the table, the bowl shivered, and the olives rolled everywhere.",
        ),
        QAItem(
            question=f"How did {helper.id} help after the accident?",
            answer=f"{helper.id} turned the spill into a safer plan by using {f['fix'].label} and helping pick up every olive.",
        ),
        QAItem(
            question=f"What was still true about {hero.id} at the end?",
            answer=f"{hero.id} was still curious, but now {hero.id} knew an accident could be turned into a clever idea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a consonant?",
            answer="A consonant is a speech sound made when the mouth partly blocks the breath, like the sounds in b, c, d, and t.",
        ),
        QAItem(
            question="What is an olive?",
            answer="An olive is a small fruit that can be green or black, and people often eat it from a jar or a bowl.",
        ),
        QAItem(
            question="What is an accident?",
            answer="An accident is something that happens by mistake, not because somebody meant for it to happen.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(letters).
activity(sorting).
setting(nook).
prize(olive_bowl).

affords(nook,letters).
affords(nook,sorting).

mess_of(letters,bump).
mess_of(sorting,bump).
splashes(letters,table).
splashes(letters,floor).
splashes(sorting,table).
splashes(sorting,floor).

worn_on(olive_bowl,table).

% A story is reasonable if the activity can cause an accident and there is a
% fix that can contain it.
can_accident(A,P) :- affords(S,A), prize(P), splashes(A,table), worn_on(P,table).
has_fix(A) :- mess_of(A,M), guard(F,M).
valid_story(S,A,P) :- affords(S,A), can_accident(A,P), has_fix(A).

guard(tray,bump).
guard(cloth,bump).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        for tag in sorted(ACTIVITIES[aid].tags):
            lines.append(asp.fact("tag", aid, tag))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            lines.append(asp.fact("affords", place, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("splashes", aid, "table"))
        lines.append(asp.fact("splashes", aid, "floor"))
        lines.append(asp.fact("mess_of", aid, act.mess))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    ap = argparse.ArgumentParser(description="Tall-tale story world about Curiosity, consonants, olives, and an accident.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero, params.helper)
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
    StoryParams(place="nook", activity="letters", prize="olive_bowl", hero="Curiosity", helper="Aunt Poppy"),
]


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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:\n")
        for row in combos:
            print(" ", row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
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
            header = f"### {p.hero}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
