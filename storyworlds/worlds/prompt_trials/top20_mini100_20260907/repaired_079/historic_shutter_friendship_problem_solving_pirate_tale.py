#!/usr/bin/env python3
"""
storyworlds/worlds/prompt_trials/top20_mini100_20260907/repaired_079/historic_shutter_friendship_problem_solving_pirate_tale.py
============================================================================================================================

A small pirate-tale storyworld about a historic harbor shutter, a friendship
problem, and a practical fix.

Seed image:
---
On an old seaside fort, a creaky shutter bangs in the wind and keeps waking a
young pirate crew. The crew wants to protect a historic map room, but two friends
disagree about how to fix the shutter. They argue, test one plan that fails, then
solve the problem together and end with a warmer, calmer night.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain", "mate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "bosun"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain_name: str = "Mara"
    friend_name: str = "Jory"
    place_name: str = "Old Gull Fort"
    shutter_name: str = "the west shutter"
    map_room_name: str = "the map room"


NAMES = ["Mara", "Jory", "Nell", "Tobin", "Ria", "Finn", "Pip", "Sail"]
PLACES = ["Old Gull Fort", "Covewatch Keep", "Harbor Lantern Hall", "Brinebell Bastion"]
SHUTTERS = ["the west shutter", "the east shutter", "the attic shutter", "the sea-facing shutter"]
ROOMS = ["the map room", "the chart room", "the salt archive", "the captain's study"]


INCIDENTS = [
    {
        "title": "the banging shutter by the old map room",
        "problem": "the shutter banged so hard that the lamps shook on the shelf",
        "wrong": "tried to wedge it shut with a rope knot that slipped right out",
        "setback": "the rope knot popped loose, and the shutter clapped open again when the wind returned",
        "clue": "the old iron latch was bent, so the shutter could not close flat on its own",
        "meaning": "Straighten the latch first, then fasten the shutter with a small wooden peg",
        "action": "carefully straightened the latch, cut a peg from a spare broom handle, and set the peg under the hook",
        "recovery": "the shutter held firm, and the lamps stopped trembling",
        "ending": "the fort grew quiet except for the sea, and the historic map room slept soundly through the night",
        "lesson": "A steady fix lasts longer than a quick trick",
    },
    {
        "title": "the salt-sprayed shutter and the torn curtain",
        "problem": "salt wind kept slamming the shutter into a curtain of red cloth",
        "wrong": "pinned the curtain higher without testing whether the shutter could still swing freely",
        "setback": "the cloth tore on a nail, and the room smelled more of salt than supper",
        "clue": "the hinge side needed oil, not more cloth",
        "meaning": "Oil the hinge, then tie the curtain back with a soft cord",
        "action": "oiled the hinge with ship grease, tied the curtain with blue cord, and checked the swing twice",
        "recovery": "the shutter moved smooth as a gull's wing, and the curtain stayed safe",
        "ending": "warm lantern light glowed over the old charts while the wind passed harmlessly outside",
        "lesson": "When something sticks, the real answer may be to ease the moving part",
    },
    {
        "title": "the shutter that hid a secret draft",
        "problem": "a hidden crack behind the shutter made the room icy after sunset",
        "wrong": "stuffed seaweed into the crack before asking where the cold was coming from",
        "setback": "the seaweed dried out and fell away, leaving the draft to whistle louder than before",
        "clue": "the draft came from a loose board near the sill, not from the shutter itself",
        "meaning": "Patch the loose board, then hang the shutter square again",
        "action": "lifted the board, hammered in fresh nails, and hung the shutter square with a new string",
        "recovery": "the cold air stopped sneaking in, and the room kept its warmth",
        "ending": "the friends shared hot tea beside the charts while moonlight rested on the quiet wood",
        "lesson": "A problem is easier to solve when friends look for the true source",
    },
    {
        "title": "the noisy shutter above the treasure ledger",
        "problem": "each gust made the shutter creak over the ledger where the crew counted supplies",
        "wrong": "slammed the shutter shut, which made the old latch jump loose",
        "setback": "the latch sprang open and tapped the ledger ink, smudging one careful page",
        "clue": "the creak came from a dry hinge that only needed oil and patience",
        "meaning": "Oil the hinge and close the shutter slowly while one friend holds the latch",
        "action": "oiled the hinge, held the latch still, and shut the shutter as gently as a held breath",
        "recovery": "the creak faded away, and the ledger page dried neat again",
        "ending": "the pirate crew counted coins by lantern light while the shutter stayed nearly silent",
        "lesson": "A careful hand can fix what a forceful one only worsens",
    },
    {
        "title": "the bright moonlight on the cracked latch",
        "problem": "moonlight slipped through the shutter and woke the youngest cabin boy",
        "wrong": "hung a blanket over the whole window, which trapped too much damp air",
        "setback": "the room turned stuffy, and the boy still woke when the blanket slid off the sill",
        "clue": "only the lower edge needed covering, because the top gap was harmless",
        "meaning": "Cover the lower gap with a narrow board and leave the rest of the shutter free",
        "action": "trimmed a narrow board, fit it below the latch, and tested the light together",
        "recovery": "the moon stayed out of the bunk, and the air stayed fresh",
        "ending": "the youngest sailor slept through the tide change while the friends watched the stars",
        "lesson": "A smaller fix can solve the right part of a problem",
    },
    {
        "title": "the shutter at the historic bell tower",
        "problem": "the shutter rattled every time the bell tower rang the hour",
        "wrong": "tied the shutter with a thick knot that snapped the next time the bell sounded",
        "setback": "the knot snapped, and the shutter burst open with a sharp crack",
        "clue": "the latch needed a leather strip to soften the shake",
        "meaning": "Use a leather strip to catch the motion before it reaches the latch",
        "action": "cut a strip from an old belt, looped it through the latch, and tested it against the bell",
        "recovery": "the leather softened the jolt, and the shutter only gave a gentle tap",
        "ending": "the bell rang proudly while the map room stayed peaceful behind its softened latch",
        "lesson": "A smart buffer can protect a fragile thing from a hard shake",
    },
    {
        "title": "the shutter under the storm flag",
        "problem": "a storm flag cracked above the shutter and made the crew think the room was doomed",
        "wrong": "panicked and nailed the shutter shut before checking the wind",
        "setback": "the closed shutter trapped damp air, and rain still leaked around the frame",
        "clue": "the real danger was the rain gutter above, not the shutter",
        "meaning": "Clear the gutter first, then leave the shutter free to dry",
        "action": "climbed to the gutter, cleared the wet leaves, and opened the shutter wide to dry",
        "recovery": "the rain drained away, and the room dried before dawn",
        "ending": "the storm passed, the flag quieted, and the old room smelled of clean wood again",
        "lesson": "When a danger seems large, check whether it is really the cause",
    },
    {
        "title": "the shutter with the missing handle",
        "problem": "the shutter could not be opened without a proper handle",
        "wrong": "used a spoon as a handle, and it bent at once",
        "setback": "the bent spoon dropped to the floor, and the friends had to start over",
        "clue": "a spare brass hook hung in the tool chest",
        "meaning": "Use the brass hook as a handle and fasten it with two nails",
        "action": "fitted the brass hook in place and tapped in two nails with a careful rhythm",
        "recovery": "the shutter opened smooth and easy at the next try",
        "ending": "the map room breathed in the salt air while the new handle shone in lantern light",
        "lesson": "The right tool makes friendship easier, too, because it saves everyone's patience",
    },
    {
        "title": "the shutter that guarded the old sea chart",
        "problem": "the shutter blocked the chart cabinet when the captain needed one last route",
        "wrong": "pulled hard on the shutter and nearly toppled the cabinet",
        "setback": "the cabinet wobbled, and both friends had to catch it before it fell",
        "clue": "the cabinet had to be moved first so the shutter could swing clear",
        "meaning": "Move the cabinet, then open the shutter with room to spare",
        "action": "lifted the cabinet together, slid it aside, and opened the shutter in a wide arc",
        "recovery": "the chart was easy to reach, and the room felt roomy again",
        "ending": "the sea chart lay open under a calm lamp while two friends grinned at their teamwork",
        "lesson": "Some problems need space, not strength",
    },
    {
        "title": "the shutter and the spilled ink pot",
        "problem": "the shutter snapped open and sent an ink pot skidding across the desk",
        "wrong": "blamed the desk and kept arguing instead of fixing the wind latch",
        "setback": "the ink blot spread across the page, and the argument made the room tense",
        "clue": "the wind latch had slid loose during the last tide",
        "meaning": "Fix the latch and apologize before the next gust arrives",
        "action": "reset the latch, wiped the desk, and spoke kindly before the next gust",
        "recovery": "the page dried clean enough to copy, and the room grew calm again",
        "ending": "by the time the tide turned, the friends had a neat page and a steadier friendship",
        "lesson": "A problem-solving talk can mend both a room and a mood",
    },
    {
        "title": "the shutter on the lighthouse stair",
        "problem": "the shutter banged near the stair where the lookout rested",
        "wrong": "used a heavy chain that scraped the paint and made more noise",
        "setback": "the chain clattered down the step and woke the lookout anyway",
        "clue": "a soft cloth wrap would quiet the edge without adding weight",
        "meaning": "Wrap the shutter edge and test the swing with one hand on the frame",
        "action": "wrapped the edge in cloth, tested the swing, and listened for the first quiet click",
        "recovery": "the banging stopped, and the stair stayed ready for watch duty",
        "ending": "the lookout slept till dawn while the sea lantern shone above the still shutter",
        "lesson": "Quiet fixes can work better than hard ones",
    },
]


TELLING_MODES = [
    ("The old fort woke with a wooden bang.", "The friends stopped arguing and looked for the true cause."),
    ("At sunset, the shutter began its noisy work again.", "A better plan came only after they tested the first one."),
    ("The sea wind had a habit of testing everything it touched.", "This time the crew answered with patience and a tool chest."),
    ("The map room felt safe until the shutter started to clap.", "Friendship mattered enough to make them listen to each other."),
    ("A narrow room can make a small problem sound much larger.", "The best fix turned out to be careful, not grand."),
    ("The pirates had sailed through storms, but a shutter still bested them at first.", "Then they solved it by working side by side."),
    ("The historic fort was proud of its old wood and old stones.", "That pride led the friends to repair it gently."),
    ("The night began with a grumpy shutter and a grumpier mood.", "Both improved after one honest conversation."),
    ("The wind whistled through the fort like a sneaky lookout.", "The crew found the weak spot, not just the loudest one."),
    ("The room needed peace, and the shutter refused to give it.", "So the friends made peace with a practical plan."),
]


# ---------------------------------------------------------------------------
# Narrative instruments
# ---------------------------------------------------------------------------
@dataclass
class Friendship:
    trust: float = 1.0
    warmth: float = 1.0


@dataclass
class ProblemSolving:
    tried: int = 0
    solved: bool = False


@dataclass
class Historic:
    age: int = 0
    cared_for: bool = False


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _setup(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain_name))
    friend = world.add(Entity(id="friend", kind="character", type="mate", label=params.friend_name))
    place = world.add(Entity(id="place", kind="place", type="place", label=params.place_name))
    shutter = world.add(Entity(id="shutter", kind="thing", type="shutter", label=params.shutter_name))
    room = world.add(Entity(id="room", kind="place", type="room", label=params.map_room_name))
    tools = world.add(Entity(id="tools", kind="thing", type="toolbox", label="tool chest"))

    captain.meters["courage"] = 1.0
    friend.meters["care"] = 1.0
    shutter.meters["noise"] = 3.0
    shutter.meters["stiffness"] = 2.0
    place.meters["age"] = 100.0
    room.meters["warmth"] = 0.0
    tools.meters["useful"] = 1.0
    captain.memes["worry"] = 0.2
    friend.memes["worry"] = 0.2

    world.facts.update(captain=captain, friend=friend, place=place, shutter=shutter, room=room, tools=tools)


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.captain_name}|{params.friend_name}|{params.place_name}|{params.shutter_name}|{params.map_room_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    friendship = Friendship()
    solving = ProblemSolving()
    historic = Historic(age=100, cared_for=False)

    captain = world.facts["captain"]
    friend = world.facts["friend"]
    shutter = world.facts["shutter"]
    room = world.facts["room"]
    token = _selection_token(params)
    incident = INCIDENTS[token % len(INCIDENTS)]
    mode = TELLING_MODES[(token // len(INCIDENTS)) % len(TELLING_MODES)]

    world.say(mode[0])
    world.say(
        f"{captain.label} and {friend.label} stood in {params.place_name}, beside {params.shutter_name} outside {params.map_room_name}. "
        f"The old wood was part of the fort's history, and {incident['problem']}."
    )
    world.say(
        f'"That shutter needs a fix," {captain.label} said. '
        f'"Aye, but we should not break the old fort trying," {friend.label} replied.'
    )

    world.para()
    world.say(
        f"They tried a quick patch first: {incident['wrong']}. "
        f'"See?" {captain.label} said, but {friend.label} pointed at the result.'
    )
    world.say(f"{incident['setback'].capitalize()}.")
    world.say(
        "For a moment, the room felt colder and their friendship felt tighter with worry, "
        "because the first idea had failed in front of them both."
    )

    world.para()
    world.say(
        f'"Let us look again," {friend.label} said. '
        f'"If it is historic, we should treat the wood kindly."'
    )
    world.say(
        f'{captain.label} nodded. "Then tell me what you see." '
        f'"I see that {incident["clue"]}," {friend.label} answered.'
    )
    world.say(f"That changed the plan: {incident['meaning']}.")
    world.say(f"Together they {incident['action']}.")

    world.para()
    world.say(f"{incident['recovery']}.")
    room.meters["warmth"] = 1.0
    shutter.meters["noise"] = 0.0
    shutter.meters["stiffness"] = 0.5
    historic.cared_for = True
    solving.tried = 2
    solving.solved = True
    friendship.trust = 2.0
    friendship.warmth = 2.0
    captain.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0

    world.say(
        f'"We make a good pair," {captain.label} said. '
        f'"Aye," {friend.label} said, "one who listens before the next swing."'
    )
    world.say(f"{incident['lesson']}.")
    world.say(f"In the end, {incident['ending']}.")

    world.facts.update(
        friendship=friendship,
        solving=solving,
        historic=historic,
        incident=incident,
        incident_index=token % len(INCIDENTS),
        mode_index=(token // len(INCIDENTS)) % len(TELLING_MODES),
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story() -> bool:
    return True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["captain"]
    f = world.facts["friend"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly pirate tale about {incident['title']}, with a historic shutter in an old fort.",
        f"Show how {p.label} and {f.label} argue a little, then use friendship and problem solving to repair the shutter.",
        f"Tell a story where the first repair fails, the true cause is discovered, and the ending proves the fort is quieter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    place = world.facts["place"]
    shutter = world.facts["shutter"]
    room = world.facts["room"]
    incident = world.facts["incident"]

    return [
        QAItem(
            question=f"Where did {captain.label} and {friend.label} find the problem?",
            answer=f"They found it in {place.label}, beside {shutter.label} outside {room.label}.",
        ),
        QAItem(
            question="What was the first bad idea?",
            answer=f"They {incident['wrong']}. That plan failed because it did not address the real cause.",
        ),
        QAItem(
            question="What happened after the first repair?",
            answer=f"{incident['setback'].capitalize()}. The shutter still would not stay quiet.",
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=f"They noticed that {incident['clue']}. That clue changed the whole repair.",
        ),
        QAItem(
            question="How did friendship help the crew?",
            answer=f"{captain.label} and {friend.label} listened to each other, shared the work, and chose {incident['meaning'].lower()}.",
        ),
        QAItem(
            question="What was the final result?",
            answer=f"{incident['recovery'].capitalize()} The historic room became calm again.",
        ),
        QAItem(
            question="What ending image shows the story finished well?",
            answer=f"{incident['ending'].capitalize()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a wooden panel that opens and closes over a window or opening to block wind and light.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, listen, and help each other when something goes wrong.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully at a trouble, trying a plan, and changing the plan if needed.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story begins with a historic shutter problem in an old fort.
historic_shutter_story(S) :- historic_place(S), shutter_problem(S).

% Friendship matters when two characters disagree, then listen and help.
friendship_help(S) :- disagreement(S), listening(S), shared_fix(S).

% Problem solving succeeds when the first fix fails and a better cause is found.
problem_solved(S) :- first_fix_failed(S), true_cause_found(S), careful_repair(S).

% A valid story must show all three parts.
valid_story(S) :- historic_shutter_story(S), friendship_help(S), problem_solved(S).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("historic_place", "story1"),
        asp.fact("shutter_problem", "story1"),
        asp.fact("disagreement", "story1"),
        asp.fact("listening", "story1"),
        asp.fact("shared_fix", "story1"),
        asp.fact("first_fix_failed", "story1"),
        asp.fact("true_cause_found", "story1"),
        asp.fact("careful_repair", "story1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story() else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about a historic shutter, friendship, and problem solving.")
    ap.add_argument("--captain-name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place-name", choices=PLACES)
    ap.add_argument("--shutter-name", choices=SHUTTERS)
    ap.add_argument("--map-room-name", choices=ROOMS)
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
    captain = args.captain_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != captain])
    place = args.place_name or rng.choice(PLACES)
    shutter = args.shutter_name or rng.choice(SHUTTERS)
    room = args.map_room_name or rng.choice(ROOMS)
    return StoryParams(seed=None, captain_name=captain, friend_name=friend, place_name=place, shutter_name=shutter, map_room_name=room)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(captain_name="Mara", friend_name="Jory", place_name="Old Gull Fort", shutter_name="the west shutter", map_room_name="the map room"),
    StoryParams(captain_name="Nell", friend_name="Tobin", place_name="Covewatch Keep", shutter_name="the sea-facing shutter", map_room_name="the chart room"),
    StoryParams(captain_name="Ria", friend_name="Finn", place_name="Brinebell Bastion", shutter_name="the attic shutter", map_room_name="the salt archive"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
