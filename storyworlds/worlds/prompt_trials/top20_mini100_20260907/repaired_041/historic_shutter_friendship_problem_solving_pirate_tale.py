#!/usr/bin/env python3
"""
A standalone Storyweavers world: a small pirate tale about a historic shutter,
friendship, and problem solving.

Premise:
- A ship-shaped museum room keeps a historic shutter as its pride.
- During a busy visit, the shutter sticks and blocks a little display.
- Two pirate friends must solve the problem without breaking the old wood.
- Their friendship and careful plan restore the room and earn a warm ending.

This script follows the Storyworld contract:
- standalone stdlib Python
- lazy ASP import for verification/query modes
- world simulation with physical meters and emotional memes
- StorySample/QAItem/StoryError from storyworlds.results
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THEME = "historic shutter"
SEED_WORDS = {"historic", "shutter"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["stuck", "dust", "scratched", "open", "closed", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "trust", "joy", "curiosity", "patience", "pride", "friendship", "courage"]:
            self.memes.setdefault(k, 0.0)


@dataclass
class StoryParams:
    captain: str = "Mara"
    mate: str = "Bram"
    guide: str = "Nell"
    case: int = 0
    telling_mode: int = 0
    thought_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    place: str
    task: str
    trouble: str
    first_clue: str
    false_lead: str
    thought: str
    dialogue: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


CASES = [
    Case(
        place="the old harbor museum hall",
        task="open the lantern display for the afternoon visitors",
        trouble="the historic shutter jammed halfway and blocked the lantern room",
        first_clue="a line of pale salt dust on the lower rail and a tiny chip of blue paint near the latch",
        false_lead="the sea breeze rattled the window and made it seem as if the whole wall was loose",
        thought="A breeze can shake a room, but dust on the rail means the shutter itself moved and scraped.",
        dialogue="Mara said, 'We will not force it.' Bram answered, 'Then we solve it like careful pirates.'",
        discovery="slid a thin wooden wedge under the swollen edge and eased the shutter open a finger at a time",
        cause="had left the old frame closed after the rain and the damp wood had swelled around the latch",
        repair="wiped the rail dry, rubbed in a little oil, and tied the display cord back with a neat sailor's knot",
        proof="the shutter glided without a groan and the lantern light reached the whole room",
        lesson="Friendship makes a hard job easier when everyone stays calm and shares the plan.",
        ending="By evening, the old shutter stood open, and the lantern glow fell warmly across the museum floor.",
    ),
    Case(
        place="the captain's chart room",
        task="show the visitors a painted map of the coast",
        trouble="the shutter would not budge, so the map stayed in shadow",
        first_clue="a squeak from one hinge and a narrow smear of tar on the inside frame",
        false_lead="a loose curtain flapped like a flag and made the room look haunted",
        thought="The curtain is noisy, but the hinge squeak points right to the shutter's own joints.",
        dialogue="Nell said, 'One of you hold the door.' Mara said, 'And one of us works the hinge.'",
        discovery="worked the rusty pin free, then lifted the shutter with both hands and set it level",
        cause="had pushed the shutter shut with a tar-sticky glove after patching the deck rail",
        repair="cleaned the hinge pin, oiled the joint, and hung the map where the light could show every coast line",
        proof="the map shone bright, and the hinge moved smooth as a gull's wing",
        lesson="A good crew does not guess first; it listens, looks, and checks the real cause.",
        ending="The coast map gleamed by the open shutter while the three friends smiled like victorious sailors.",
    ),
    Case(
        place="the ship museum's small treasure alcove",
        task="unlock a glass case holding a brass compass",
        trouble="the shutter panel jammed the case door and trapped the compass in darkness",
        first_clue="a split nail and a trail of sawdust along the sill",
        false_lead="one shiny coin on the floor tempted everyone to blame a greedy thief",
        thought="A dropped coin tells a story about pockets, not about the jammed panel and sawdust.",
        dialogue="Bram whispered, 'We should not accuse a thief without proof.' Mara nodded, 'Then let's follow the wood dust.'",
        discovery="lifted the panel just enough to free the bent corner and slide the case door clear",
        cause="had slammed the shutter after a loud thunderclap and bent the old nail in its frame",
        repair="replaced the split nail, brushed away the sawdust, and set the compass on a velvet pad",
        proof="the compass needle spun true and the case door latched without catching",
        lesson="Problem solving means choosing the clue that fits the object, not the one that sounds exciting.",
        ending="Under the fixed shutter, the brass compass flashed once like a tiny sun and pointed north.",
    ),
    Case(
        place="a low stone quay beside the museum",
        task="hang signal flags for the harbor festival",
        trouble="the shutter on the storage hut stuck fast and hid the flags inside",
        first_clue="a damp rope fiber caught in the shutter latch and a wet boot print on the stone",
        false_lead="gulls were pecking at crumbs, which made the crew think the flags had been stolen",
        thought="Gulls love crumbs; rope fiber and a wet print are better clues for a stuck latch.",
        dialogue="Nell said, 'We can share the work.' Mara replied, 'Aye, you pull, and I will steady the frame.'",
        discovery="pulled the rope fiber free, then lifted the shutter while Bram propped the door with a crate",
        cause="had shut the hut fast to keep out spray, and the wet rope caught under the latch",
        repair="dried the latch, coiled the rope higher on its hook, and hung the flags in bright order",
        proof="the flags snapped in the breeze while the hut door stayed open and safe",
        lesson="Friends solve trouble faster when each one takes a different job and trusts the others.",
        ending="Red and gold flags fluttered above the quay, and the open shutter no longer blocked the fun.",
    ),
    Case(
        place="the museum's pirate kitchen",
        task="serve apple cakes before the tour left",
        trouble="the shutter would not open, and the kitchen filled with steam",
        first_clue="beads of water on the sill and a sticky handprint near the latch",
        false_lead="the oven's smoke made everyone think the cakes had burned",
        thought="Smoke can frighten a crew, but water beads show the room is damp, not ruined.",
        dialogue="Mara said, 'Keep breathing slow.' Bram said, 'We fix the shutter first, then check the cakes.'",
        discovery="opened the lower catch and propped the shutter with a spoon handle so the steam could escape",
        cause="had closed the shutter before the kettle boiled, and the warm wet air made the wood cling",
        repair="aired the kitchen, turned the cakes once, and wiped the latch until it clicked cleanly",
        proof="the cakes came out golden and the kitchen air turned fresh again",
        lesson="Calm hands can solve a problem before worry makes it bigger.",
        ending="The apple cakes cooled by the open shutter, sweet and safe in the clear seaside air.",
    ),
    Case(
        place="the shipwright's gallery",
        task="reveal a model ship under a cloth",
        trouble="the shutter stuck and cast a dark stripe right over the model",
        first_clue="a sliver of shell caught in the track and a fresh scratch on the sill",
        false_lead="a blinking lamp made the shadow look like a hidden ghost",
        thought="Ghosts do not leave shell slivers; the track itself is the place to inspect.",
        dialogue="Bram said, 'I can reach the track.' Mara answered, 'And I can hold the cloth back.'",
        discovery="fished the shell out, then slid the shutter along its track until the room brightened",
        cause="had brushed a shell from a pocket after a beach walk and dropped it into the rail",
        repair="cleared the track, polished the wood, and uncovered the model ship with a proud sweep",
        proof="the model's sails shone in daylight and the shadow stripe vanished",
        lesson="A small thing in the wrong place can stop a big job, so careful eyes matter.",
        ending="The model ship sailed in a bar of sunshine while the historic shutter rested open beside it.",
    ),
    Case(
        place="the lighthouse visitor room",
        task="show a wall of old sea tales",
        trouble="the shutter on the east window jammed and made the room too dark to read",
        first_clue="flaked white paint on the latch and a sandy ridge along the sill",
        false_lead="the lamp's dim wick made it seem like the whole lighthouse had gone sleepy",
        thought="The lamp is weak, but the sandy ridge tells me the shutter was dragged after the beach walk.",
        dialogue="Nell said, 'Let us read the clues, not the gloom.' Mara grinned, 'Aye, that sounds like true pirate work.'",
        discovery="lifted the sandy latch, shook free the grit, and opened the shutter wide",
        cause="had pushed the shutter in with sandy gloves after helping haul nets",
        repair="brushed the sill clean, relit the lamp, and marked the glove hook by the door",
        proof="the tales on the wall could be read from the doorway and the light stayed steady",
        lesson="A problem often hides in the smallest grit, not in the biggest shadow.",
        ending="White light spilled over the sea tales as the open shutter let the room breathe again.",
    ),
    Case(
        place="the museum's rope loft",
        task="lower a bundle of flags from the rafters",
        trouble="the shutter jammed and trapped the pull-rope behind it",
        first_clue="a frayed rope strand and a knot tied backward on the cleat",
        false_lead="a squealing pulley made the crew blame the loft beam instead of the shutter",
        thought="The pulley can squeal, but the backward knot shows the rope was rushed and snagged at the shutter.",
        dialogue="Mara said, 'We untie it together.' Bram replied, 'And no one yanks until we are both ready.'",
        discovery="untied the snagged line, then opened the shutter enough to free the rope from behind it",
        cause="had hurried to drop the flags before lunch and wrapped the line the wrong way",
        repair="retied the rope, greased the pulley, and lowered the flags one by one with care",
        proof="the bundle came down straight, and the shutter hung clear of the rope",
        lesson="Friendship is strong when people pause, explain, and solve the snag together.",
        ending="The flags swung gently from the loft beam while the shutter sat open and harmless.",
    ),
    Case(
        place="a narrow passage beside the captain's cabin",
        task="carry a message chest to the dock",
        trouble="the historic shutter swung shut and blocked the path like a stubborn gate",
        first_clue="a wet thumbprint and a puff of sawdust on the hinge side",
        false_lead="a distant drumbeat sounded urgent enough to make everyone rush",
        thought="The drumbeat can wait; the thumbprint and dust show where the shutter was touched.",
        dialogue="Bram asked, 'Should we force it?' Mara shook her head. 'No. We use our heads before our shoulders.'",
        discovery="held the shutter with one hand and worked the hinge pin loose with a small iron nail",
        cause="had swung it wide with wet hands after scrubbing the deck and then left it hanging crooked",
        repair="straightened the hinge, dried the wood, and carried the message chest through the clear passage",
        proof="the path stayed open and the chest reached the dock without a bump",
        lesson="A smart crew saves strength by solving the real problem first.",
        ending="The passage stood clear, and the message chest rolled safely under the open shutter.",
    ),
    Case(
        place="the harbor archive room",
        task="find a record of old pirate names",
        trouble="the shutter door stuck and blocked the archive cabinet",
        first_clue="an ink dot on the latch and a torn catalog slip on the floor",
        false_lead="the dusty shelves made the room feel like the answer had been lost forever",
        thought="Dust makes everything look old, but the ink dot says someone was near the latch recently.",
        dialogue="Nell said, 'We can sort by clues.' Mara replied, 'Then let's start with the ink dot.'",
        discovery="opened the cabinet after nudging the shutter free and found the record book tucked behind it",
        cause="had leaned the wet catalog against the latch and pressed the shutter shut by mistake",
        repair="blotted the ink, refiled the slips, and made a neat shelf marker so the book would not hide again",
        proof="the record book sat in plain sight and the cabinet opened without a snag",
        lesson="Careful sorting and honest talking can turn a muddle into a map.",
        ending="The old pirate names rested on the shelf, bright in the daylight from the freed shutter.",
    ),
    Case(
        place="the museum's little pump room",
        task="bring water to the deck for washing brushes",
        trouble="the shutter jammed over the pump window and kept the room too hot",
        first_clue="a warm drip track down the glass and a patch of rust at the latch",
        false_lead="a bucket tipped over loudly enough to sound like a disaster",
        thought="A bucket splash is noisy, but the drip track and rust tell me the shutter itself needs help.",
        dialogue="Bram said, 'I will hold the latch.' Mara answered, 'And I will turn the pump after the air cools.'",
        discovery="slid the rust loose with an oiled pin and opened the shutter to let in the sea breeze",
        cause="had shut the window tight before the pump started working hard",
        repair="cooled the room, filled the brush bucket, and left a cloth by the latch for next time",
        proof="the water stayed clear and the room no longer felt like a kettle",
        lesson="A small tool and a calm plan can solve what force cannot.",
        ending="Cool breeze and clean water returned together through the opened historic shutter.",
    ),
    Case(
        place="the museum stair landing",
        task="welcome a school group up the steps",
        trouble="the shutter on the landing window froze shut and made the stairway dim",
        first_clue="a tiny pebble caught in the track and a bright scuff on the paint",
        false_lead="the children chattering below made it seem as if the stairs were already full",
        thought="Noise from below is just noise; the pebble in the track is the thing the shutter cannot ignore.",
        dialogue="Mara said, 'You spot the pebble, I will hold the frame.' Bram grinned, 'That sounds like a tidy pirate plan.'",
        discovery="picked the pebble out with a hook and opened the shutter far enough for sunlight to pour in",
        cause="had left the landing window open after a windy visit, and the pebble rolled in with the dust",
        repair="cleaned the track, wiped the rail, and greeted the school group at the bright landing",
        proof="the steps gleamed and the shutter slid easily for the next visitor",
        lesson="When friends divide the work, even a small stairway problem becomes simple.",
        ending="Sunlight climbed the stairs under the open shutter, and the children laughed as they entered.",
    ),
]


@dataclass
class World:
    captain: Entity
    mate: Entity
    guide: Entity
    shutter: Entity
    lantern: Entity
    museum: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _new_entity(eid: str, kind: str, type_: str, label: str, phrase: str = "", **kwargs) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, phrase=phrase, **kwargs)


def build_world(params: StoryParams) -> World:
    captain = _new_entity(params.captain, "character", "girl", "captain")
    mate = _new_entity(params.mate, "character", "boy", "mate")
    guide = _new_entity(params.guide, "character", "person", "guide")
    shutter = _new_entity("shutter", "thing", "shutter", "historic shutter", "the old wooden shutter")
    lantern = _new_entity("lantern", "thing", "lantern", "lantern display", "the bright lantern display")
    museum = _new_entity("museum", "place", "building", "museum hall", "the harbor museum")
    world = World(captain=captain, mate=mate, guide=guide, shutter=shutter, lantern=lantern, museum=museum)
    world.facts["theme"] = THEME
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, s, g = world.captain, world.mate, world.guide
    sh, ln = world.shutter, world.lantern
    case = CASES[params.case % len(CASES)]

    sh.meters["stuck"] = 1
    sh.memes["worry"] += 1
    h.memes["worry"] += 1
    s.memes["curiosity"] += 1
    h.memes["friendship"] += 2
    s.memes["friendship"] += 2

    openings = [
        f"In {case.place}, {h.id}, {s.id}, and {g.id} prepared to {case.task}.",
        f"The {THEME} sat bright beside the sea, and on that day {h.id} and {s.id} tried to {case.task}.",
        f"Inside {case.place}, an old pirate spirit seemed to live in every beam while {h.id} and {s.id} worked together.",
        f"When visitors arrived at {case.place}, the friends planned to {case.task} with help from {g.id}.",
        f"The morning began with salt air, creaking boards, and a job to {case.task}.",
    ]
    world.say(openings[params.telling_mode % len(openings)])
    world.say(f"Then the trouble came: {case.trouble}.")
    world.say("The room still smelled of tar, sea wind, and old rope, but nobody wanted to break the ancient wood.")

    world.para()
    world.say(f"Near the frame, they noticed {case.first_clue}.")
    world.say(f"At first, {case.false_lead}.")
    world.say(f"{case.thought}")
    world.say(f"{h.id} said, \"{case.dialogue.split('Mara said, ')[1].split('\"')[1] if 'Mara said,' in case.dialogue else 'Let us think this through.'}\"" if False else case.dialogue)
    world.say(f"\"Let's try the clue that fits the wood,\" said {h.id}. \"Aye,\" answered {s.id}, \"and we will do it together.\"")

    world.para()
    world.say(f"First, {h.id} and {s.id} {case.discovery}.")
    sh.meters["stuck"] = 0
    sh.meters["open"] = 1
    sh.meters["closed"] = 0
    sh.memes["worry"] = max(0.0, sh.memes["worry"] - 1)
    h.memes["joy"] += 1
    s.memes["joy"] += 1
    h.memes["trust"] += 1
    s.memes["trust"] += 1
    g.memes["pride"] += 1

    world.say(f"Then {g.id} explained the cause: {case.cause}.")
    world.say(f"The three of them repaired the problem by {case.repair}.")
    world.say(f"They checked their work and saw that {case.proof}.")
    world.say(f"{h.id} smiled. \"{case.lesson}\"")
    world.say(f"{s.id} nodded. \"That is what friendship is for.\"")
    world.say(f"The old shutter and the bright lantern display were safe again.")

    world.para()
    world.say(f"{case.ending}")

    world.facts.update(
        captain=h,
        mate=s,
        guide=g,
        shutter=sh,
        lantern=ln,
        museum=world.museum,
        resolved=True,
        project=case.task,
        trouble=case.trouble,
        clue=case.first_clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        qa_style=params.telling_mode,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h, s, g = world.facts["captain"], world.facts["mate"], world.facts["guide"]
    style = world.facts["qa_style"] % 4
    mystery_questions = [
        f"What went wrong while the friends tried to {world.facts['project']}?",
        f"Why did the work at {world.facts['museum'].label} stop?",
        f"What problem did the pirate friends face first?",
        f"Which old object caused trouble in the story?",
    ]
    clue_questions = [
        f"Which clue helped {h.id} and {s.id} solve the problem?",
        f"What evidence mattered more than the false lead?",
        f"How did the friends know the shutter itself was the issue?",
        f"What detail pointed them to the real cause?",
    ]
    cause_questions = [
        f"What caused the historic shutter to jam?",
        f"How did {g.id} explain the trouble?",
        f"Why was the shutter stuck?",
        f"What did the team discover about the wood and latch?",
    ]
    repair_questions = [
        "How did friendship help fix the problem?",
        f"What did the friends do together after opening the shutter?",
        "How did the crew prove the solution worked?",
        f"What repair made the room safe again?",
    ]
    lesson_questions = [
        "What did the friends learn about solving problems together?",
        "Why was careful thinking better than forcing the shutter?",
        "What lesson did the pirate crew share at the end?",
        "How did the story show friendship and problem solving?",
    ]
    return [
        QAItem(
            question=mystery_questions[style],
            answer=f"The {world.facts['trouble']} stopped the visit and kept the lantern display in shadow.",
        ),
        QAItem(
            question=clue_questions[style],
            answer=f"They trusted {world.facts['clue']}. That clue fit the shutter better than {world.facts['false_lead']}.",
        ),
        QAItem(
            question=cause_questions[style],
            answer=f"{g.id} explained that {world.facts['cause']}. The damp or snagged wood was the real reason it jammed.",
        ),
        QAItem(
            question=repair_questions[style],
            answer=f"The friends {world.facts['repair']}. After that, {world.facts['proof']}.",
        ),
        QAItem(
            question=lesson_questions[style],
            answer=f"They learned that {world.facts['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a historic shutter?",
            answer="A historic shutter is an old wooden panel on a window or doorway that has been kept because it is part of a special old place.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means people care about each other, share trust, and help one another when things go wrong.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding out what caused trouble and choosing a careful way to fix it.",
        ),
        QAItem(
            question="What does a pirate tale usually feel like?",
            answer="A pirate tale usually has sea air, brave friends, maps or ships, and a lively adventurous mood.",
        ),
        QAItem(
            question="Why should old wood not be forced?",
            answer="Old wood can crack or break if it is pushed too hard, so gentle care keeps it safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly pirate tale set in a {THEME} where friends must solve a problem without breaking the old wood.",
        f"Tell a short story about friendship and problem solving in {world.facts['museum'].label}, ending with a clear change in the shutter and the light.",
        "Include a brief spoken back-and-forth between the friends, and make the ending image prove that the historic shutter is fixed.",
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
    for e in [world.captain, world.mate, world.guide, world.shutter, world.lantern, world.museum]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(historic_shutter_pirate_tale).
requires(setting(historic_shutter_pirate_tale), friendship).
requires(setting(historic_shutter_pirate_tale), problem_solving).

valid_story(S) :- setting(S), requires(S, friendship), requires(S, problem_solving).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("setting", "historic_shutter_pirate_tale"),
            asp.fact("requires", "historic_shutter_pirate_tale", "friendship"),
            asp.fact("requires", "historic_shutter_pirate_tale", "problem_solving"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if ok:
        print("OK: ASP rules recognize the historic shutter pirate tale domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about a historic shutter.")
    ap.add_argument("--captain", default=None)
    ap.add_argument("--mate", default=None)
    ap.add_argument("--guide", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    captain = args.captain or rng.choice(["Mara", "Lina", "Tess", "June", "Nia"])
    mate = args.mate or rng.choice(["Bram", "Eli", "Finn", "Oren", "Jax"])
    guide = args.guide or rng.choice(["Nell", "Ivo", "Ria", "Pia"])
    if captain == mate or captain == guide or mate == guide:
        raise StoryError("The captain, mate, and guide must be different characters.")
    offset = sample_seed - base_seed
    return StoryParams(
        captain=captain,
        mate=mate,
        guide=guide,
        case=offset % len(CASES),
        telling_mode=(offset // len(CASES)) % 5,
        thought_style=(offset // (len(CASES) * 5)) % 4,
        ending_style=(offset // (len(CASES) * 5 * 4)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(captain="Mara", mate="Bram", guide="Nell"),
    StoryParams(captain="Tess", mate="Finn", guide="Ria"),
    StoryParams(captain="June", mate="Jax", guide="Pia"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
