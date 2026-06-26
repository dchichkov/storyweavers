#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/twirl_misunderstanding_inner_monologue_pirate_tale.py
================================================================================================

A small pirate-tale storyworld built from the seed idea:
a twirl, a misunderstanding, and an inner monologue that helps a captain
turn worry into a better choice.

The world is classical and constraint-checked:
- a pirate crew has a harbor setting, a weather cue, and a small treasure plan
- one action causes a visible signal
- another character misreads that signal
- an inner monologue reveals the hero's careful thought
- the turn resolves the misunderstanding with a concrete change in world state

The resulting story should read like a complete children's pirate tale:
beginning, tension, turn, and ending image.
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
    wore: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    signal: str
    effect: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    counters: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _rule_signal(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("twirl", 0.0) < THRESHOLD:
            continue
        for child in world.characters():
            if child.id == actor.id:
                continue
            sig = ("signal", actor.id, child.id)
            if sig in world.fired:
                continue
            if child.memes.get("misunderstanding", 0.0) >= THRESHOLD:
                continue
            world.fired.add(sig)
            child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0.0) + 1
            out.append(f"{child.id} took the twirl the wrong way.")
    return out


CAUSAL_RULES = [_rule_signal]


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


def tell_sign(world: World, actor: Entity, action: Action) -> None:
    actor.meters["twirl"] = actor.meters.get("twirl", 0.0) + 1
    world.say(
        f"{actor.id} gave the wheel a proud {action.verb}, and the cape hem made a little twirl in the salt wind."
    )
    propagate(world, narrate=True)


def inner_monologue(world: World, actor: Entity, action: Action, prize: Entity) -> None:
    actor.memes["thought"] = actor.memes.get("thought", 0.0) + 1
    world.say(
        f"In {actor.pronoun('possessive')} own mind, {actor.id} thought, "
        f'"If I keep spinning by the mast, I can still keep {prize.id} safe and show the crew the route."'
    )
    world.facts["inner_monologue"] = True


def clarify(world: World, speaker: Entity, listener: Entity, action: Action, prize: Entity) -> None:
    listener.memes["misunderstanding"] = 0.0
    listener.memes["trust"] = listener.memes.get("trust", 0.0) + 1
    world.say(
        f"{speaker.id} pointed at the chart and said, "
        f'"I am not dancing for show. I am turning to keep the {prize.label} from slipping overboard."'
    )
    world.say(
        f"{listener.id} blinked, then grinned, because the twirl was really a careful move after all."
    )


def resolve(world: World, hero: Entity, crew: Entity, prize: Entity, action: Action) -> None:
    hero.meters["steady"] = hero.meters.get("steady", 0.0) + 1
    crew.memes["relief"] = crew.memes.get("relief", 0.0) + 1
    world.say(
        f"With the truth spoken, {hero.id} tied the rope tighter, the ship held its course, "
        f"and the {prize.label} stayed safe in the lantern glow."
    )


def is_valid_combo(setting: Setting, action: Action, prize: Prize, fix: Fix) -> bool:
    return prize.region in action.zone and prize.region in fix.covers and action.keyword in fix.counters


@dataclass
class StoryParams:
    setting: str
    action: str
    prize: str
    hero_name: str
    hero_gender: str
    crew_name: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", indoors=False, affords={"twirl", "signal"}),
    "ship": Setting(place="the deck of a small ship", indoors=False, affords={"twirl", "signal"}),
    "cove": Setting(place="the moonlit cove", indoors=False, affords={"twirl", "signal"}),
}

ACTIONS = {
    "twirl": Action(
        id="twirl",
        verb="twirl",
        gerund="twirling",
        signal="a bright cape swish",
        effect="a careful turn",
        zone={"deck", "hands"},
        keyword="twirl",
        tags={"twirl", "signal"},
    ),
    "signal": Action(
        id="signal",
        verb="wave the lantern",
        gerund="waving the lantern",
        signal="a lantern flash",
        effect="a warning light",
        zone={"deck", "hands"},
        keyword="signal",
        tags={"signal", "light"},
    ),
}

PRIZES = {
    "map": Prize(
        id="map",
        label="treasure map",
        phrase="a rolled treasure map with red X marks",
        type="map",
        region="hands",
    ),
    "compass": Prize(
        id="compass",
        label="gold compass",
        phrase="a little gold compass on a cord",
        type="compass",
        region="hands",
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a glass belly",
        type="lantern",
        region="hands",
    ),
}

FIXES = {
    "rope": Fix(
        id="rope",
        label="a braided rope loop",
        covers={"hands"},
        counters={"twirl", "signal"},
        prep="wrap a braided rope loop around the chest",
        tail="tied the rope loop snugly",
    ),
    "hook": Fix(
        id="hook",
        label="a belt hook",
        covers={"hands"},
        counters={"signal"},
        prep="clip a belt hook to the sash",
        tail="clipped the belt hook tight",
    ),
}

HERO_NAMES = ["Mara", "Pip", "Ned", "Tess", "Jory", "Sailor May", "Ari"]
CREW_NAMES = ["first mate", "bosun", "captain", "deckhand"]
TRAITS = ["brave", "sly", "quick", "cheerful", "scrappy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for a_id in setting.affords:
            action = ACTIONS[a_id]
            for p_id, prize in PRIZES.items():
                for f in FIXES.values():
                    if is_valid_combo(setting, action, prize, f):
                        out.append((s_id, a_id, p_id))
                        break
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with twirl, misunderstanding, and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--crew-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate-tale combination matches the given options.)")
    setting, action, prize = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    return StoryParams(setting=setting, action=action, prize=prize, hero_name=hero_name, hero_gender=hero_gender, crew_name=crew_name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    prize = PRIZES[params.prize]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl" if params.hero_gender == "girl" else "boy"))
    crew = world.add(Entity(id=params.crew_name, kind="character", type="captain", label="the crew"))
    treasure = world.add(Entity(id=prize.id, type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id, region=prize.region, plural=prize.plural))
    world.facts.update(hero=hero, crew=crew, prize=treasure, action=action, setting=setting)

    world.say(f"{hero.id} was a {rng_trait := random.choice(TRAITS)} little pirate who loved the salt wind and the sea charts.")
    world.say(f"On the deck at {setting.place}, {hero.id} kept {treasure.id} close, because {treasure.phrase} mattered dearly.")
    world.para()
    world.say(f"One dusk, {hero.id} started {action.gerund}, and the cape hem made a bright twirl beside the mast.")
    world.say(f"{crew.id} saw the twirl and took it the wrong way, thinking {hero.id} was only fooling around.")
    world.para()
    inner_monologue(world, hero, action, treasure)
    clarify(world, hero, crew, action, treasure)
    resolve(world, hero, crew, treasure, action)

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    action = f["action"]
    return [
        f"Write a short pirate tale for a young child where {hero.id} does a {action.keyword} and another pirate misunderstands it.",
        f"Tell a gentle sea story about a twirl, a worried crew member, and {prize.label} staying safe.",
        f"Write a story in pirate style that includes an inner monologue and ends with the misunderstanding being cleared up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    crew = f["crew"]
    prize = f["prize"]
    action = f["action"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the pirate story about at {setting.place}?",
            answer=f"It was about {hero.id}, a little pirate who cared about the {prize.label} and the ship's safe path.",
        ),
        QAItem(
            question=f"What did {hero.id} do that caused the misunderstanding?",
            answer=f"{hero.id} started {action.gerund}, and that twirl looked like play instead of a careful move.",
        ),
        QAItem(
            question=f"Why did {crew.id} first get the wrong idea?",
            answer=f"{crew.id} saw the twirl and thought {hero.id} was just fooling around, not guarding the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} think in the inner monologue?",
            answer=f"In private, {hero.id} thought that keeping the {prize.label} safe mattered and that the spinning turn could still help the ship.",
        ),
        QAItem(
            question=f"How was the misunderstanding fixed?",
            answer=f"{hero.id} explained the careful plan, and then {crew.id} understood that the twirl was part of keeping the {prize.label} safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a sea adventurer who sails ships, searches for treasure, and works with a crew.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone sees or hears something and gets the wrong idea about it.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the thinking voice inside someone's mind, where they quietly work things out.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="harbor", action="twirl", prize="map", hero_name="Mara", hero_gender="girl", crew_name="captain"),
    StoryParams(setting="ship", action="twirl", prize="compass", hero_name="Pip", hero_gender="boy", crew_name="first mate"),
    StoryParams(setting="cove", action="signal", prize="lantern", hero_name="Tess", hero_gender="girl", crew_name="bosun"),
]


ASP_RULES = r"""
% A prize is at risk when the chosen action and prize share the same vulnerable region.
at_risk(A,P) :- action(A), prize(P), zone(A,R), region(P,R).

% A fix is reasonable when it covers the same vulnerable region and counters the action.
compatible(F,A,P) :- at_risk(A,P), fix(F), covers(F,R), region(P,R), counters(F,A).
valid_story(S,A,P) :- setting(S), affords(S,A), at_risk(A,P), compatible(_,A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id, s in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", s_id, a))
    for a_id, a in ACTIONS.items():
        lines.append(asp.fact("action", a_id))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", a_id, z))
    for p_id, p in PRIZES.items():
        lines.append(asp.fact("prize", p_id))
        lines.append(asp.fact("region", p_id, p.region))
    for f_id, f in FIXES.items():
        lines.append(asp.fact("fix", f_id))
        for c in sorted(f.covers):
            lines.append(asp.fact("covers", f_id, c))
        for c in sorted(f.counters):
            lines.append(asp.fact("counters", f_id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def explain_rejection() -> str:
    return "(No story: the chosen pirate pieces do not make a believable misunderstanding with a safe fix.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize:
        if not any((args.setting or s_id) == s_id and (args.action or a_id) == a_id and (args.prize or p_id) == p_id for s_id, a_id, p_id in valid_combos()):
            raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid pirate-tale combination matches the given options.)")
    setting, action, prize = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    return StoryParams(setting=setting, action=action, prize=prize, hero_name=hero_name, hero_gender=hero_gender, crew_name=crew_name)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.hero_name}: {p.action} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
