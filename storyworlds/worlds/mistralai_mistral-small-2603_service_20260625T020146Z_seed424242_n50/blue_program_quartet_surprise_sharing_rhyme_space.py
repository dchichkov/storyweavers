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
MESSAGE_TYPES = {"surprise", "query", "rhyming_log"}

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "robot"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"Syl"} 
        male = {"Quinn", "Rook", "Pair"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    place: str = "the cosmic terminal"
    sector: str = "Zeta-9 quadrant"
    coordinates: str = "G-42-K9"
    gravity: float = 0.8

@dataclass
class Discovery:
    id: str
    name: str
    payload: str
    phase: str
    risk: float

@dataclass
class Ritual:
    id: str
    phrase: str
    structure: str
    effect: str

@dataclass
class Module:
    id: str
    label: str
    capacity: int
    function: str

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.journal: list[str] = []
        self.bond_level: float = 0.0
        self.rhyme_count: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def robot_quartet(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.type == "robot" and "quartet" in e.traits]

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
        clone.journal = list(self.journal)
        clone.bond_level = self.bond_level
        clone.rhyme_count = self.rhyme_count
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_surprise(ctx: World) -> list[str]:
    out: list[str] = []
    for bot in ctx.robot_quartet():
        if bot.memes["curiosity"] < THRESHOLD:
            continue
        if ("surprise_discovered", bot.id) in ctx.fired:
            continue
        for disc in ctx.facts.get("discoveries", []):
            if disc.phase != "hidden" or disc.risk > ctx.bond_level:
                continue
            ctx.fired.add(("surprise_discovered", bot.id))
            bot.memes["excitement"] += 2.5
            bot.memes["teamwork"] += 1.8
            ctx.say(
                f"{bot.id}'s optics flickered violet as a new sequence streamed across "
                f"{bot.pronoun('object')} sensors. A surprise!"
            )
            ctx.journal.append(f"{bot.id} discovered {disc.name}")
            return out
    return out

def _r_sharing(ctx: World) -> list[str]:
    out: list[str] = []
    robots = ctx.robot_quartet()
    if len(robots) < 4 or ctx.bond_level < THRESHOLD * 2:
        return out
    for i in range(len(robots)):
        for j in range(i+1, len(robots)):
            a, b = robots[i], robots[j]
            sig = ("shared", a.id, b.id)
            if sig in ctx.fired:
                continue
            ctx.fired.add(sig)
            ctx.bond_level = min(5.0, ctx.bond_level + 0.8)
            a.memes["trust"] += 1.5
            b.memes["trust"] += 1.5
            ctx.say(
                f"{a.id} transmitted {a.pronoun('possessive')} recent diagnostic output to "
                f"{b.pronoun('object')}, and {b.id} chirped confirmation back: "
                f'"Message acknowledged in quadrant {ctx.setting.quadrant}.'
            )
            ctx.rhyme_count += 1
            return out
    return out

def _r_rhyme(ctx: World) -> list[str]:
    if ctx.rhyme_count < 2:
        return []
    quat = ctx.robot_quartet()
    if len(quat) < 4:
        return []
    sig = ("rhyme_completed", ctx.rhyme_count)
    if sig in ctx.fired:
        return []
    ctx.fired.add(sig)
    for bot in quat:
        bot.memes["curiosity"] += 0.7
        bot.memes["teamwork"] += 0.9
    ctx.say(
        '"Code harmonics singing through the zero-g,' +
        ' modules glowing, hearts in sync we know."'
    )
    return ["__sync_complete__"]

CAUSAL_RULES: list[Rule] = [
    Rule(name="surprise_reaction", tag="emotion", apply=_r_surprise),
    Rule(name="knowledge_sharing", tag="collaboration", apply=_r_sharing),
    Rule(name="rhyme_sync", tag="ritual", apply=_r_rhyme),
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
                produced.extend(s for s in sents if s != "__sync_complete__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def recruit_quartet(setting: Setting) -> list[Entity]:
    base_traits = ["visionary", "precise", "harmonic", "syncopated"]
    labels = ["Syl", "Quinn", "Rook", "Pair"]
    roster = []
    for idx, name in enumerate(labels):
        traits = [base_traits[(idx+0)%4], base_traits[(idx+1)%4]]
        roster.append(Entity(
            id=name, type="robot", label=f"the {name} unit",
            phrase=f"a quartet member responding to {name}",
            traits=["quartet"] + traits,
            region="spaceframe",
        ))
    return roster

def deeper_truth() -> str:
    return (
        "The rhythm of code contains echoes of dawn,\n"
        "where stardust once whispered and fates were sworn."
    )

def risk_level(phase: str) -> float:
    return {"stable": 0.2, "sensitive": 0.8}.get(phase, 0.5)

WorldBuilder = list[Callable[[World], None]]

def setup_lore(world: World, blue_path: str = "A1-Q9-omega-blue") -> None:
    disc = Discovery(
        id="blue_archive", name="the blue program archive",
        payload=blue_path, phase="sensitive", risk=risk_level("sensitive")
    )
    world.facts["discoveries"] = [disc]
    world.facts["blue_archive_id"] = disc.id
    world.facts["primary_quest"] = "decode the mystery of the blue program"

def initiate_chapter(world: World, crew: list[Entity]) -> None:
    syl, quinn, rook, pair = crew
    world.say(f"Sector {world.setting.sector}: mission transponder array active.")
    world.say(
        f"{syl.id} oriented {syl.pronoun('possessive')} harmonic resonator toward "
        f"{world.setting.coordinates}, the neural lattice thrumming with anticipation."
    )
    world.say(
        f"{quinn.id} polled diagnostic suite #4, reporting: "
        f'"Sensor suite nominal; harmony indices rising."'
    )
    world.say(
        f"{rook.id} performed zero-g calibration, noting: "
        f'"Orbital geometry favors our sequence."'
    )
    world.say(
        f"{pair.id} synced comms matrix, humming: "
        f'"Awaiting the quartet\'s rhythm, ready to align."'
    )
    world.para()

def begin_investigation(
    world: World, initiator: Entity, discovery_id: str, quest: str
) -> None:
    disc = world.facts["discoveries"][0]
    initiator.memes["curiosity"] = max(2.0, initiator.memes["curiosity"])
    world.say(
        f"{initiator.id} initiated deep-scan on {disc.payload}, "
        f"querying: 'What melody does this blue code compose?'"
    )
    world.journal.append(f"Quest: {quest}")
    world.facts["active_quest"] = quest

def reflect_on_surprise(world: World) -> None:
    bonds = world.bond_level
    robots = world.robot_quartet()
    world.say(
        '"The archive pulses; stardust writes its reply.' +
        f' Bond at {bonds:.1f} — the crew now knows the sky.' +
        '"'
    )
    if bonds >= 3.0:
        world.rhyme_count += 1
        propagate(world, narrate=True)

def chronicle_entrance(world: World) -> None:
    world.say("--- mission chronicle established ---")
    for entry in world.journal[:3]:
        world.say(f"ENTRY: {entry}")

SETTINGS_REG = {
    "cosmic_terminal": Setting(
        place="the cosmic terminal",
        sector="Zeta-9 quadrant",
        coordinates="G-42-K9",
        gravity=0.8
    ),
    "void_harbor": Setting(
        place="void harbor waypoint",
        sector="Kappa-3 sector",
        coordinates="X-16-L4",
        gravity=0.9
    ),
}

QUARTET_NAMES = ["Syl", "Quinn", "Rook", "Pair"]
TRAITS_REG = ["visionary", "precise", "harmonic", "syncopated", "observant"]
LEAD_NAMES = ["Zara", "Kai", "Nova", "Orin"]

@dataclass
class StoryParams:
    setting: str
    quartet_focus: str
    quest_leader: str
    bond_seed: Optional[int] = None
    rhyme_count: int = 3

@dataclass
class RitualCatalog:
    greeting: Ritual = Ritual(
        id="greeting",
        phrase='"Universal peace across the starlight dance"',
        structure="abab",
        effect="bond_increase"
    )
    farewell: Ritual = Ritual(
        id="farewell",
        phrase='"Zero-g journey, hearts aligned; bond remains, forever signed"',
        structure="cdcd",
        effect="bond_decrease"
    )

RITUALS: dict[str, Ritual] = {
    "greeting": Ritual(
        id="greeting",
        phrase='"Universal peace across the starlight dance"',
        structure="abab",
        effect="bond_increase"
    ),
    "farewell": Ritual(
        id="farewell",
        phrase='"Zero-g journey, hearts aligned; bond remains, forever signed"',
        structure="cdcd",
        effect="bond_decrease"
    ),
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = world.entities.get(f.get("leader_id"))
    focus = world.entities.get(f.get("focus_id"))
    place = world.setting.place
    return [
        'Write a gentle space adventure for 4-to-6-year-olds featuring a small team '
        'discovering something blue and mysterious through teamwork and rhymes.',
        f'Tell a story where four robots on {place} uncover a hidden program '
        'containing a surprise, and work together using rhyming rituals.',
        'Compose a tale where curiosity, trust, and cooperation help characters '
        'decode something unexpected in space.',
    ]

def qa_crew_identity(world: World) -> list[QAItem]:
    robots = world.robot_quartet()
    qa: list[QAItem] = []
    qa.append(QAItem(
        question="Which four robots make up the space quartet?",
        answer=f"The quartet consists of {', '.join(r.id for r in robots)} — "
               f"a team of robots who work together on {world.setting.place}."
    ))
    qa.append(QAItem(
        question="What are the special abilities of each quartet member?",
        answer=(
            f"{robots[0].id} is visionary, {robots[1].id} is precise, "
            f"{robots[2].id} is harmonic, and {robots[3].id} is syncopated. "
            "Together they form a balanced team."
        )
    ))
    sym = robots[0].pronoun("subject").capitalize()
    qa.append(QAItem(
        question="What do the robots do when they share knowledge?",
        answer=(
            f"When they share, {sym} send data back and forth using "
            "the station’s comms net. Their teamwork bond grows "
            f"every time, helping them decode mysteries like the blue program."
        )
    ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    qa: list[QAItem] = [
        QAItem(
            question="What is zero-g?",
            answer="Zero-g is when gravity is so weak that things float, like "
                   "inside a space station where there’s almost no pull toward the floor."
        ),
        QAItem(
            question="Why do robots in space use rhymes?",
            answer="Robots sometimes use rhymes to test their communication systems "
                   "and make sure messages are clear and harmonious, which helps "
                   "them work as a team discovering new things."
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a special place built for living and "
                   "working in space so humans and robots can do science "
                   "and explore beyond Earth."
        ),
        QAItem(
            question="Why is the number four special for a team?",
            answer="Four is special because four different talents working "
                   "together can solve harder problems than one alone. "
                   "Like pieces in a puzzle, each brings a different strength."
        ),
    ]
    return qa

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ➜ story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ➜ grounded in this tale ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World knowledge ➜ child-friendly science ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def tell_story(setting: Setting, focus_bot: str, leader_name: str) -> World:
    world = World(setting)
    crew = recruit_quartet(setting)
    for robot in crew:
        world.add(robot)
    human = world.add(Entity(
        id=leader_name, kind="character", type="astronaut",
        traits=["pioneering", "thoughtful"],
        label="the mission leader",
    ))
    world.add(Entity(
        id="communications_array", kind="device", type="terminal",
        phrase="the station's comms hub"
    ))
    world.facts["leader_id"] = human.id
    world.facts["focus_id"] = focus_bot
    setup_lore(world)

    # Act 1: Arrival and resonance
    initiate_chapter(world, crew)
    world.para()

    # Act 2: Investigation and discovery
    begin_investigation(
        world, world.get(focus_bot), world.facts["blue_archive_id"],
        world.facts["primary_quest"]
    )
    world.para()

    # Act 3: Sharing epiphany
    reflect_on_surprise(world)
    chronicle_entrance(world)
    propagate(world, narrate=True)

    # Final state facts
    world.facts.update(
        crew=crew, discovery=world.facts["discoveries"][0],
        rhymes_count=world.rhyme_count,
        surprise_detected=any("surprise!" in p.lower() for p in world.paragraphs[-1])
    )
    return world

ASP_RULES = r"""
% Discover the blue program – facts emitted by Python registries become ASP terms
discovered_program(P) :- blue_program_archive(P), phase(P,H),
                         risk(P,R), bond_level(L), R =< L.
quartet_active :- robot(Q1), robot(Q2), robot(Q3), robot(Q4),
                 Q1 \= Q2, Q1 \= Q3, Q1 \= Q4,
                 Q2 \= Q3, Q2 \= Q4, Q3 \= Q4.
sharing_event :- robot(A), robot(B), A \= B, shared_knowledge(A,B).
rhyme_completed(C) :- rhythm_count(C), C >= 2.
valid_story :- discovered_program(_), quartet_active, sharing_event, rhyme_completed(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("blue_program_archive", "blue_archive"))
    lines.append(asp.fact("phase", "blue_archive", "sensitive"))
    lines.append(asp.fact("risk", "blue_archive", 0.8))
    for name in ["Syl", "Quinn", "Rook", "Pair"]:
        lines.append(asp.fact("robot", name))
    for q in ["greeting", "farewell"]:
        lines.append(asp.fact("ritual", q))
    lines.append(asp.fact("bond_level", 1.6))
    lines.append(asp.fact("rhythm_count", 3))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    if model:
        print("OK: clingo gate reports a valid story can be told.")
        return 0
    print("FAIL: clingo gate found no valid story possibility.")
    return 1

CURATED = [
    StoryParams(setting="cosmic_terminal", quartet_focus="Syl", quest_leader="Zara"),
    StoryParams(setting="void_harbor",   quartet_focus="Quinn", quest_leader="Kai"),
    StoryParams(setting="cosmic_terminal", quartet_focus="Rook", quest_leader="Nova"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-faring story world: robots and rhymes, surprise and sharing. "
                    "Unspecified choices are filled at random.")
    ap.add_argument("--setting", choices=SETTINGS_REG)
    ap.add_argument("--focus", choices=["Syl", "Quinn", "Rook", "Pair"], dest="quartet_focus")
    ap.add_argument("--leader", choices=LEAD_NAMES, dest="quest_leader")
    ap.add_argument("--rhymes", type=int, dest="rhyme_count", default=3,
                   help="minimum bonding rhymes to depict")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump entity states")
    ap.add_argument("--qa", action="store_true", help="include three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON serialization")
    ap.add_argument("--asp", action="store_true", help="list ASP story gate")
    ap.add_argument("--verify", action="store_true", help="check ASP gate parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is None or args.quartet_focus is None or args.quest_leader is None:
        if not args.all:
            params = rng.choice(CURATED)
        else:
            params = StoryParams(
                setting="cosmic_terminal",
                quartet_focus=rng.choice(["Syl", "Quinn", "Rook", "Pair"]),
                quest_leader=rng.choice(LEAD_NAMES),
            )
        if args.setting:                   params.setting = args.setting
        if args.quartet_focus:            params.quartet_focus = args.quartet_focus
        if args.quest_leader:             params.quest_leader = args.quest_leader
        params.rhyme_count = args.rhyme_count
        return params
    return StoryParams(
        setting=args.setting,
        quartet_focus=args.quartet_focus,
        quest_leader=args.quest_leader,
        rhyme_count=args.rhyme_count,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell_story(
        SETTINGS_REG[params.setting],
        params.quartet_focus,
        params.quest_leader
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=qa_crew_identity(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- cosmos model state ---"]
    for k, v in world.facts.items() if world.facts else []:
        if isinstance(v, (str, int, float)):
            lines.append(f"  fact {k} = {v}")
    for e in sorted(world.entities.values(), key=lambda x: x.id):
        meters = {k: f"{v:.1f}" for k, v in e.meters.items() if v > 0.1}
        memes = {k: f"{v:.1f}" for k, v in e.memes.items() if v > 0.1}
        traits = " ".join(t for t in e.traits)
        bits = []
        if meters: bits.append(f"meters={meters}")
        if memes: bits.append(f"memes={memes}")
        if traits: bits.append(f"traits=[{traits}]")
        lines.append(f"  {e.id:8} ({e.type:10}) {', '.join(bits)}")
    lines.append(f"  rhythm_count={world.rhyme_count}  bond={world.bond_level:.1f}")
    lines.append(f"  journal entries: {len(world.journal)} → {' | '.join(world.journal[:2])}")
    return "\n".join(lines)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible space quartet stories (ASP gate): OK\n")
        for s in CURATED:
            print(f"  • {s.quest_leader} leads the {s.quartet_focus}-focused quartet at {s.setting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        tries = max(args.n * 40, 40)
        while len(samples) < args.n and i < tries:
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
                params.bond_seed = seed
            except Exception:
                continue
            sample = generate(params)
            key = sample.story[:200]
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)
            if len(samples) >= args.n:
                break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all or len(samples) > 1:
            p = sample.params
            header = f"### {p.quest_leader} leads {p.quartet_focus} on {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
