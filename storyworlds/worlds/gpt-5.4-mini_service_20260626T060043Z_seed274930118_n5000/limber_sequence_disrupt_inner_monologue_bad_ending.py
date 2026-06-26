#!/usr/bin/env python3
"""
storyworlds/worlds/limber_sequence_disrupt_inner_monologue_bad_ending.py
=======================================================================

A small space-adventure storyworld about a crew member trying to complete a
quest by following a careful sequence of ship tasks, limbering up before EVA,
and then facing a disruption that breaks the plan. The world is intentionally
limited and constraint-checked: the crew can only attempt quests that are
physically plausible, and the ending is a bad ending when the disruption wins.

Seed tale premise:
- A crew member on a small exploration ship must complete a sequence of tasks.
- Before a spacewalk, they limber up in zero gravity.
- A disruption interrupts the quest, and the final attempt fails.
- The story includes inner monologue and a clear, child-facing bad ending.

This world is written to satisfy the Storyweavers contract:
- typed entities with meters and memes
- world-state-driven prose
- a Python reasonableness gate with an inline ASP twin
- generation, QA, JSON, trace, and verification support
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "captain", "pilot", "engineer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    ship: str
    sector: str
    low_grav: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    sequence: list[str]
    limber_action: str
    disrupts: list[str]
    risk: str
    reward: str
    location: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    protects: set[str]
    helps: set[str]
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
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.trace = list(self.trace)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_disrupt(world: World) -> list[str]:
    out: list[str] = []
    for crew in world.crew():
        if crew.memes.get("disrupted", 0.0) < THRESHOLD:
            continue
        sig = ("disrupt", crew.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crew.memes["fear"] = crew.memes.get("fear", 0.0) + 1
        crew.memes["focus"] = max(0.0, crew.memes.get("focus", 0.0) - 1)
        out.append(f"The surprise broke {crew.id}'s focus.")
    return out


CAUSAL_RULES = [
    _r_disrupt,
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


def _do_limber(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    actor.memes["limber"] = actor.memes.get("limber", 0.0) + 1
    actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1
    if narrate:
        world.say(
            f"{actor.id} took a slow breath and limbered up in the low gravity "
            f"before the {quest.location} task."
        )


def _do_sequence(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    actor.memes["quest"] = actor.memes.get("quest", 0.0) + 1
    if narrate:
        steps = ", then ".join(quest.sequence[:-1]) + f", and finally {quest.sequence[-1]}"
        world.say(
            f"The quest had a careful sequence: first {steps}. "
            f"{actor.id} repeated it inside {actor.pronoun('possessive')} head."
        )


def _do_disrupt(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    actor.memes["disrupted"] = actor.memes.get("disrupted", 0.0) + 1
    if narrate:
        world.say(
            f"Then something went wrong: one sudden disrupting burst from the ship's "
            f"old system shook the corridor."
        )
    propagate(world, narrate=narrate)


def _attempt_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> bool:
    if quest.id not in world.setting.affords:
        return False
    needed = set(quest.sequence)
    if not needed.issubset({step for step in quest.sequence}):
        return False
    if actor.memes.get("disrupted", 0.0) < THRESHOLD:
        actor.memes["success"] = actor.memes.get("success", 0.0) + 1
        if narrate:
            world.say(f"{actor.id} finished the quest safely.")
        return True
    actor.memes["failure"] = actor.memes.get("failure", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} could not finish the quest after the disruption.")
    return False


def predict_outcome(world: World, actor: Entity, quest: Quest) -> dict:
    sim = world.copy()
    _do_limber(sim, sim.get(actor.id), quest, narrate=False)
    _do_sequence(sim, sim.get(actor.id), quest, narrate=False)
    _do_disrupt(sim, sim.get(actor.id), quest, narrate=False)
    ok = _attempt_quest(sim, sim.get(actor.id), quest, narrate=False)
    return {
        "success": ok,
        "fear": sim.get(actor.id).memes.get("fear", 0.0),
        "failure": sim.get(actor.id).memes.get("failure", 0.0),
    }


def intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a {hero.label} aboard {world.setting.ship}, watching "
        f"the stars slide past the glass."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had one quest: to reach {quest.location} and "
        f"{quest.reward}."
    )


def inner_monologue(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f'"I can do this," {hero.id} thought. "If I keep the sequence in order, '
        f'I will not get lost."'
    )


def set_plan(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} checked the panel and whispered the sequence again: "
        f"{', '.join(quest.sequence)}."
    )


def disruption_scene(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"Just as {hero.id} reached the hatch, {quest.risk} flashed through the cabin "
        f"and the ship lurched."
    )


def bad_ending(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} tried to keep going, but the plan was broken. "
        f"The quest did not get {quest.reward}, and the hatch stayed shut."
    )
    world.say(
        f'{hero.id} stood still and listened to the quiet ship. "I wish I had '
        f"more time," {hero.id} thought."
    )


def tell(world: World, hero: Entity, quest: Quest, tool: Optional[Tool] = None) -> World:
    intro(world, hero, quest)
    world.para()
    _do_limber(world, hero, quest)
    set_plan(world, hero, quest)
    inner_monologue(world, hero, quest)
    world.para()
    _do_sequence(world, hero, quest)
    disruption_scene(world, hero, quest)
    _do_disrupt(world, hero, quest)
    _attempt_quest(world, hero, quest)
    world.para()
    bad_ending(world, hero, quest)
    if tool is not None:
        world.say(
            f"The {tool.label} lay unused, because the disruption came before it could help."
        )
    world.facts.update(hero=hero, quest=quest, tool=tool, setting=world.setting)
    return world


SETTINGS = {
    "orbital_hall": Setting(
        ship="the Star Linden",
        sector="orbital hall",
        low_grav=True,
        affords={"relay"},
    ),
    "cargo_ring": Setting(
        ship="the Star Linden",
        sector="cargo ring",
        low_grav=True,
        affords={"repair"},
    ),
    "moon_gate": Setting(
        ship="the Star Linden",
        sector="moon gate",
        low_grav=True,
        affords={"signal"},
    ),
}

QUESTS = {
    "relay": Quest(
        id="relay",
        title="relay the beacon codes",
        sequence=["strap in", "limber the arms", "check the map", "open the hatch", "send the codes"],
        limber_action="limber the arms",
        disrupts=["static", "alarm"],
        risk="a burst of static",
        reward="the beacon codes sent",
        location="orbital hall",
        keyword="sequence",
        tags={"sequence", "quest", "space", "relay"},
    ),
    "repair": Quest(
        id="repair",
        title="repair the broken panel",
        sequence=["brace the boots", "limber the fingers", "lock the tool", "open the panel", "tighten the wires"],
        limber_action="limber the fingers",
        disrupts=["spark", "warning"],
        risk="a shower of sparks",
        reward="the panel repaired",
        location="cargo ring",
        keyword="disrupt",
        tags={"disrupt", "quest", "space", "repair"},
    ),
    "signal": Quest(
        id="signal",
        title="send a moon signal",
        sequence=["warm the radio", "limber the shoulders", "aim the dish", "press the switch", "wait for reply"],
        limber_action="limber the shoulders",
        disrupts=["glitch", "flicker"],
        risk="a glitch in the radio",
        reward="the moon signal answered",
        location="moon gate",
        keyword="limber",
        tags={"limber", "quest", "space", "signal"},
    ),
}

TOOLS = {
    "gloves": Tool(
        id="gloves",
        label="grip gloves",
        protects={"spark", "static"},
        helps={"repair"},
        prep="put on the grip gloves first",
        tail="would have helped hold the wire",
    ),
    "visor": Tool(
        id="visor",
        label="a bright visor",
        protects={"glitch", "flicker"},
        helps={"signal"},
        prep="lower the bright visor first",
        tail="would have helped read the panel lights",
    ),
    "belt": Tool(
        id="belt",
        label="a safety belt",
        protects={"alarm", "static"},
        helps={"relay"},
        prep="clip on the safety belt first",
        tail="would have kept the body steady",
    ),
}


HEROES = [
    ("Nova", "pilot"),
    ("Mira", "engineer"),
    ("Juno", "captain"),
    ("Tali", "pilot"),
    ("Orin", "engineer"),
]

TRAITS = ["brave", "careful", "curious", "steady", "hopeful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = QUESTS[qid]
            if quest.id in setting.affords:
                out.append((sid, qid, next(iter(TOOLS))))
    return out


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    return [
        f'Write a short space-adventure story for a young child that uses the words "{quest.keyword}", "sequence", and "disrupt".',
        f"Tell a story where {hero.id} must complete a quest on {world.setting.ship} but an unexpected disruption ruins the plan.",
        f"Write a gentle but sad space story about {hero.id} thinking to {hero.pronoun('self') if False else 'themself'} about a careful sequence before a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was {hero.id}'s quest on {setting.ship}?",
            answer=f"{hero.id} was trying to {quest.title} in {quest.location}.",
        ),
        QAItem(
            question=f"What did {hero.id} do before the quest to get ready?",
            answer=f"{hero.id} limbered up first and repeated the sequence in order.",
        ),
        QAItem(
            question=f"What went wrong in the middle of the story?",
            answer=f"A disruption shook the ship and broke the plan before the quest could be finished.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended badly: the quest was not completed, and {quest.reward} never happened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sequence?",
            answer="A sequence is a set of steps in the right order, like first, then, and last.",
        ),
        QAItem(
            question="What does it mean to disrupt something?",
            answer="To disrupt something means to break into it or interrupt it so it cannot keep going smoothly.",
        ),
        QAItem(
            question="What does limber mean?",
            answer="Limber means loose and ready to move easily, like stretching before a climb or a spacewalk.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that someone tries hard to finish.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orbital_hall", quest="relay", hero_name="Nova", hero_type="pilot", trait="brave"),
    StoryParams(place="cargo_ring", quest="repair", hero_name="Mira", hero_type="engineer", trait="careful"),
    StoryParams(place="moon_gate", quest="signal", hero_name="Juno", hero_type="captain", trait="hopeful"),
]


def explain_rejection(setting: Setting, quest: Quest) -> str:
    return (
        f"(No story: {setting.ship} does not support a reasonable {quest.id} quest here.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.low_grav:
            lines.append(asp.fact("low_grav", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("keyword", qid, q.keyword))
        lines.append(asp.fact("location", qid, q.location))
        for step in q.sequence:
            lines.append(asp.fact("step", qid, step))
        for d in q.disrupts:
            lines.append(asp.fact("disruptor", qid, d))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in t.protects:
            lines.append(asp.fact("protects", tid, p))
        for h in t.helps:
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q) :- setting(S), quest(Q), affords(S,Q).
featured_keyword(Q,K) :- keyword(Q,K).
good_story(S,Q,K) :- valid(S,Q), featured_keyword(Q,K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((s, q) for s, q, _ in valid_combos())
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
    ap = argparse.ArgumentParser(
        description="Space-adventure storyworld with limbering, sequences, disruption, inner monologue, quest, and bad endings."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=["pilot", "engineer", "captain"])
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
    if args.place and args.quest and args.quest not in SETTINGS[args.place].affords:
        raise StoryError(explain_rejection(SETTINGS[args.place], QUESTS[args.quest]))
    combos = [
        (s, q)
        for s, q, _ in valid_combos()
        if (args.place is None or s == args.place)
        and (args.quest is None or q == args.quest)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(sorted(combos))
    name, typ = (args.name, args.type)
    if name is None or typ is None:
        name, typ = rng.choice(HEROES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, hero_name=name, hero_type=typ, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    quest = QUESTS[params.quest]
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.trait,
    ))
    tool = None
    if quest.id == "repair":
        tool = TOOLS["gloves"]
    elif quest.id == "signal":
        tool = TOOLS["visor"]
    else:
        tool = TOOLS["belt"]
    tell(world, hero, quest, tool)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, quest) combos:\n")
        for s, q in triples:
            print(f"  {s:12} {q:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
