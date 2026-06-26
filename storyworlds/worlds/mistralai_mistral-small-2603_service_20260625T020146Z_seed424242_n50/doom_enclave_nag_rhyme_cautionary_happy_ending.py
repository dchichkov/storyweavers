#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# Meter keys for the "doom" tension and "hope" for resolution
TENSION = "doom_tension"
HOPE = "future_hope"
RISK = "outdoor_risk"

# Body regions for gear/safety (though gear may not be main focus, safety is key)
REGIONS = {"extremities", "torso", "head"}

# Danger level for outdoor regions
DANGER_ZONES = {"approach", "threshold", "perimeter"}

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    phrase: str = ""
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "daughter", "child"}
        male = {"boy", "son", "child"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    place: str = "the enclave"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str = ""
    gerund: str = ""
    rush: str = ""
    risk: str = "doom"
    region: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    rhyme: str = ""

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = ""
    plural: bool = False

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.danger: dict = {}
        self.facts: dict = {}
        self.rhymes: list[str] = []

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.danger = dict(self.danger)
        clone.rhymes = list(self.rhymes)
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters[TENSION] >= THRESHOLD:
            sig = ("tension", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{actor.pronoun().capitalize()} felt the {TENSION.replace('_', ' ')} rising like a dark tide.")
    return out

def _r_hope(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters[HOPE] >= THRESHOLD:
            sig = ("hope", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                if HOPE in actor.memes:
                    actor.memes[HOPE] += 1.0
                out.append(f"But in the {actor.id}'s heart, a small light began to glow.")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="tension", tag="social", apply=_r_tension),
    Rule(name="hope", tag="social", apply=_r_hope),
]

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

# Verb functions for the screenplay
def warn_doom(world: World, guardian: Entity, child: Entity, prize: Entity, activity: Activity) -> bool:
    if activity.id not in world.setting.affords:
        return False
    danger = 1.0 if world.danger.get("current", {}).get(RISK, 0) >= THRESHOLD else 0.5
    child.memes[TENSION] += danger * 2.0
    guardian.memes[TENSION] += danger * 1.5
    guardian.meters["concern"] += 1.0

    verse = f"""
    "{activity.rhyme}" {guardian.pronoun('possessive')} voice was grave,
    "The doom beyond our walls we cannot brave.""
    """
    world.say(verse)
    world.facts["warning"] = activity.rhyme
    return True

def nag_plead(world: World, child: Entity, activity: Activity, guardian: Entity) -> None:
    child.memes["desire"] += 2.0
    child.memes[TENSION] += 1.5

    plea = f"""
    {child.pronoun().capitalize()} clutched {child.pronoun('possessive')} treasure tight,
    "{activity.rhyme}!" {child.pronoun()} cried with all {child.pronoun('possessive')} might.
    """
    world.say(plea)

def cross_threshold(world: World, child: Entity, guardian: Entity) -> None:
    child.memes[TENSION] += 2.0
    conflict = (
        f"{child.id} stepped past the guardian's warning gaze, "
        f"into {child.pronoun('possessive')} heart a creeping haze."
    )
    world.say(conflict)
    child.meters["reckless"] += 2.0
    guardian.memes["fear"] += 3.0

def discover_safe_path(world: World, child: Entity, elder: Entity, prize: Entity) -> None:
    child.memes[HOPE] += 3.0
    safe_msg = (
        f"{elder.pronoun().capitalize()} nodded slow and wise to see it done, "
        f"{child.pronoun('possessive')} face now catching golden sun. "
        "A hidden path, a beamed array, where light kept doom far at bay!"
    )
    world.say(safe_msg)
    child.meters[HOPE] += 5.0
    world.facts["resolved"] = True

def happy_ending(world: World, child: Entity, guardian: Entity) -> None:
    resolution = (
        f"Thus {child.id}, with guardian near, "
        f"found both thrill and safety clear. From doom they'd stayed afar, "
        f"yet played still, beneath a near, kind star."
    )
    world.say(resolution)
    child.memes[HOPE] = max(child.memes.get(HOPE, 0), 5.0)
    child.memes["joy"] = max(child.memes.get("joy", 0), 4.0)
    world.facts["ending"] = "happy_clean"

def introduce_enclave(world: World, child: Entity, elder: Entity) -> None:
    intro = (
        f"Within the {world.setting.place} walls so tight, "
        f"lived {child.id}, cared for by {elder.label_word}, "
        f"where circuits hummed with golden light."
    )
    world.say(intro)

def love_treasure(world: World, child: Entity, prize: Entity) -> None:
    holds = "them" if prize.plural else "it"
    love = (
        f"{child.pronoun().capitalize()} loved and clutched {child.pronoun('possessive')} prize so dear, "
        f"{prize.phrase}, never to forsake dear."
    )
    prize.worn_by = child.id
    world.say(love)
    child.memes["treasure_love"] += 2.0

ACTIVITIES = {
    "glimpse_outside": Activity(
        id="glimpse_outside",
        verb="peek beyond the gates",
        gerund="peeking at the doom",
        rush="dart to the threshold fast",
        risk="the doom beyond our walls",
        region={"threshold"},
        tags={"doom", "threshold", "plea"},
        rhyme='"Beware! The air out there is rot!"',
    ),
    "puddle_echo": Activity(
        id="puddle_echo",
        verb="sing to the puddles",
        gerund="singing sweet to rain's refrain",
        rush="race to splash the shimmering plain",
        risk="the doom that hides in water's sheen",
        region={"approach"},
        tags={"song", "water", "echo"},
        rhyme='"Though waves may dance, they taste of blight!"',
    ),
    "signal_chase": Activity(
        id="signal_chase",
        verb="track the blinking light",
        gerund="chasing signal trips so bright",
        rush="dash through danger's narrow sight",
        risk="the doom that lurks in flickering might",
        region={"perimeter"},
        tags={"signal", "light", "hunt"},
        rhyme='"Behold the beacon yet beware its might!"',
    ),
}

SETTINGS = {
    "engine_room": Setting(
        place="the enclave's humming heart",
        indoor=True,
        affords={"glimpse_outside", "signal_chase"},
    ),
    "garden_patch": Setting(
        place="the garden ring where old ones tend life's thread",
        indoor=False,
        affords={"puddle_echo"},
    ),
    "library_niche": Setting(
        place="the scroll-lit nook where elders pore",
        indoor=True,
        affords={"signal_chase"},
    ),
}

PRIZES = {
    "signal_cube": Prize(
        label="cube",
        phrase="a hand-sized cube that hums and glows",
        type="device",
    ),
    "echo_pebble": Prize(
        label="pebble",
        phrase="a smooth pebble still warm from yesterday's sun",
        type="token",
    ),
    "thread_spool": Prize(
        label="spool",
        phrase="a spool of iridescent thread",
        type="craft",
    ),
}

TRAITS = ["curious", "fearless", "stubborn", "hopeful"]
NAMES = [
    "Rune", "Sol", "Mira", "Kai", "Tess", "Joss", "Eira", "Lir", "Nim", "Cor"
]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, setting in SETTINGS.items():
        if not setting.affords:
            continue
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for _, prize in PRIZES.items():
                if act_id.startswith("glimpse") and prize.type == "device":
                    combos.append((place_id, act_id, prize.label))
                if act_id == "puddle_echo" and prize.type == "token":
                    combos.append((place_id, act_id, prize.label))
                if act_id == "signal_chase" and prize.type == "craft":
                    combos.append((place_id, act_id, prize.label))
    return list(dict.fromkeys(combos))

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    elder: str = "elder"
    seed: Optional[int] = None

def generation_prompts(world: World) -> list[str]:
    act = world.facts["activity"]
    prize = world.facts["prize"]
    f = world.facts
    return [
        f"Tell a short cautionary folk-tale for children about a {world.facts['name']} who lived inside an enclave full of doom beyond the walls.",
        f"Write a rhyming story where a curious child wants to go outside the enclave to {act.gerund.rstrip(', ')}, but a wise elder warns of doom beyond.",
        f"Compose a simple folk-tale verse for kids with rhymes, about a {f['name']} who nags to go into danger, but learns a safer way.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    act = f["activity"]
    prize = f["prize"]
    sub, pos = child.pronoun("subject"), child.pronoun("possessive")
    verses = world.rhymes or [""] if "warning" in f else []
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What lived inside the {world.setting.place} where {child} lived?"
            ),
            answer=(
                f"Inside the {world.setting.place} lived {child}, "
                f"cared for by {pos} {elder.label_word}."
            ),
        ),
        QAItem(
            question=(
                f"What did little {child} love to clutch and hold tight?"
            ),
            answer=(
                f"Little {child} loved and clutched {pos} "
                f"{prize.phrase}, never to forsake dear."
            ),
        ),
    ]
    if "resolved" in f:
        if f["resolved"]:
            res = "They found a secret path where golden light cut doom away."
            qa.append(QAItem(
                question=(
                    f"How did {child} play outside {pos} treasure without falling to {act.risk}?"
                ),
                answer=res,
            ))
            qa.append(QAItem(
                question=(
                    f"What lesson did {child} learn that day?"
                ),
                answer=(
                    f"{child.capitalize()} learned that though {sub} yearned to explore, "
                    f"some treasures were safer kept in-doors forever."
                ),
            ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an enclave?",
            answer=(
                "An enclave is a small, safe community living within a larger, "
                "dangerous area. Like an island of safety in the middle of a storm."
            ),
        ),
        QAItem(
            question="Why do children sometimes nag their guardians?",
            answer=(
                "Children nag when they are excited about something or really want "
                "to do an activity that their guardian says no to, often because of "
                "concern for their safety."
            ),
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

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Rune", elder_type: str = "elder",
         trait: str = "curious") -> World:
    world = World(setting)
    world.danger["current"] = {RISK: random.uniform(0.7, 1.3)}
    child = world.add(Entity(
        id=name, type="child", kind="character",
        traits=[trait],
        label=name,
    ))
    elder = world.add(Entity(
        id="ElderVeyra", type=elder_type, kind="character",
        label="Elder Veyra",
        phrase="Elder Veyra, whose eyes held maps of the old world and maps of the soul",
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=child.id, region="held",
    ))

    world.para()
    introduce_enclave(world, child, elder)
    love_treasure(world, child, prize)

    world.para()
    world.say(f"One dawn, when light was soft and low,")
    if activity.rhyme:
        world.rhymes.append(activity.rhyme)

    world.para()
    warn_doom(world, elder, child, prize, activity)
    nag_plead(world, child, activity, elder)
    cross_threshold(world, child, elder)

    world.para()
    discover_safe_path(world, child, elder, prize)

    world.para()
    happy_ending(world, child, elder)

    world.facts.update(
        child=name, elder="Elder Veyra",
        activity=activity, prize=prize_cfg,
        resolved="resolved" in world.facts,
    )
    return world

ASP_RULES = r"""
% An enclave story is valid when the prize type matches the allowed activity type
% for that place, forming a reasonable cautionary pair.

valid(Place, Activity, Prize) :-
    affords(Place, Activity),
    set(Prize, Type),
    rhymes_with(Type, Tag),
    matches(Tag, Activity).

cautionary_story(Place, A, P) :- valid(Place, A, P).
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
        for t in sorted(a.tags):
            lines.append(asp.fact("rhyme_tag", aid, t))
        lines.append(asp.fact("risk", aid, a.risk))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid, pr.type))
        for t in pr.type.split():
            lines.append(asp.fact("matches", pid, t))
    lines.append(asp.fact("#show cautionary_story/3."))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

CURATED = [
    StoryParams(place="engine_room", activity="glimpse_outside", prize="signal_cube", name="Rune", trait="fearless"),
    StoryParams(place="garden_patch", activity="puddle_echo", prize="echo_pebble", name="Kai", trait="curious"),
    StoryParams(place="library_niche", activity="signal_chase", prize="thread_spool", name="Mira", trait="stubborn"),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: a {prize.type} cannot {activity.gerund.rstrip(', ')} safely. "
        f"Choose a prize suited to {prize.type} adventures near the enclave's walls.)"
    )

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: 'the child, the nag, the enclave'."
    )
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not (
            (args.activity == "glimpse_outside" and args.prize == "signal_cube") or
            (args.activity == "puddle_echo" and args.prize == "echo_pebble") or
            (args.activity == "signal_chase" and args.prize == "thread_spool")
        ):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No compatible combination found for given constraints.)")
    place, activity, prize_id = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, trait=params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world model state ---")
        print(f"danger zones assessed: {sample.world.danger.get('current', {})}")
        print(f"fired rules: {sorted(set(n for n, *_ in sample.world.fired))}")
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_story/3."))
        return

    if args.verify:
        try:
            import asp
            model = asp.one_model(asp_program("#show cautionary_story/3."))
            triples = set(asp.atoms(model, "cautionary_story"))
            print(f"OK: ASP verified {len(triples)} compatible tales.")
        except Exception as e:
            sys.exit(f"ASP verify failed: {e}")

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show set/2."))
            print("ASP-computed valid combos:\n")
            for (pid, a, t) in asp.atoms(model, "set"):
                place = [k for k, v in SETTINGS.items() if a in v.affords][0]
                prize = [k for k, v in PRIZES.items() if v.type == t][0]
                print(f"  {place:>18} -> {a:>12} {prize}")
        except Exception as e:
            print(f"Error: {e}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        if (args.all or len(samples) > 1) and sample.params:
            p = sample.params
            header = f"### {p.name}: '{p.activity}' with the '{p.prize}' in '{p.place}'"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "~" * 70 + "\n")

if __name__ == "__main__":
    main()
