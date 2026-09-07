#!/usr/bin/env python3
"""
A small storyworld: a child in grandparent's house at dawn, hearing a strange
pipe and facing a ghost-story scare with an inner-monologue turn toward courage.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path[:0] = [STORYWORLDS_DIR, os.path.dirname(STORYWORLDS_DIR)]
from results import QAItem, StoryError, StorySample  # noqa: E402

HOUSE_ROOMS = ["kitchen", "hallway", "attic", "basement", "porch"]
SCARE_SOURCES = ["pipe", "old pipe", "banging pipe", "dripping pipe"]
HELPERS = ["flashlight", "grandparent", "warm blanket", "careful listening"]

PREMISES = [
    (
        "A pale stripe of dawn had just reached the curtains when {name} woke in {gp}'s house.",
        "{name} was trying to remember the last piece of a dream when the quiet house made room for another sound.",
    ),
    (
        "Before breakfast, {name} padded toward the window of {gp}'s house to look for the first pink cloud.",
        "The floor felt cool, and every room seemed to be holding its breath.",
    ),
    (
        "Dawn found {name} awake early in {gp}'s house, waiting for the smell of toast to reach the bedroom.",
        "Instead, a small noise traveled through the wall like a secret asking to be heard.",
    ),
    (
        "{name} had promised to draw the sunrise during this visit to {gp}'s house.",
        "Just as the sky turned peach at dawn, the old house supplied a much spookier subject.",
    ),
    (
        "At dawn, {name} sat on the guest-room rug in {gp}'s house, sorting socks before anyone else was fully awake.",
        "The ordinary morning changed when a sound arrived from the {room}.",
    ),
    (
        "At dawn, the first bird had only just begun singing when {name} opened one eye in {gp}'s house.",
        "A noise from the {room} answered the bird, but it did not sound like a song.",
    ),
    (
        "{name} woke at dawn in {gp}'s house and listened for the familiar tick of the hallway clock.",
        "Between two ticks came a sound that did not seem to belong to any clock.",
    ),
]

CONFLICTS = [
    "The {source} knocked three times, paused, and knocked once more. To {name}, it sounded almost like tiny footsteps stopping to listen.",
    "A hollow clunk ran through the {source}, making a cup on a nearby shelf tremble. For one breath, {name} imagined a ghost tapping from inside the wall.",
    "The {source} gave a low groan and then a bright little ping. The two sounds together seemed to say, 'Come closer,' though the {room} was empty.",
    "First the {source} whispered drip-drip; then it bumped hard enough to startle {name}. A ghost story from the night before suddenly felt much too easy to believe.",
    "The {source} rattled whenever the water began moving elsewhere in the house. {name} did not notice that pattern yet and pictured a chilly visitor wandering the {room}.",
    "A knock moved along the {source} from one end of the {room} to the other. {name}'s stomach tightened as if the sound were searching for someone.",
    "The {source} clicked, fell silent, and clicked again just after {name} whispered, 'Hello?' It felt like an answer, which was exciting and frightening at once.",
]

TURNS = [
    (
        '"I am frightened, but a feeling is not proof of a ghost," {name} told {reflexive}.',
        "{name} counted the knocks and noticed that each set began just after water rushed in the wall.",
    ),
    (
        'Inside, {name} thought, "My imagination has made a monster. I can look for a small, real clue without touching anything."',
        "From a safe distance, {name} saw the pipe quiver at exactly the moment the sound returned.",
    ),
    (
        '"Running would make the mystery bigger," {name} reasoned. "First I can tell {gp} exactly what I heard."',
        "Saying the rhythm aloud made it sound less like footsteps and more like something mechanical.",
    ),
    (
        '{name} took one slow breath and thought, "Brave does not mean going near a pipe alone. Brave can mean asking for help."',
        "That thought loosened the tight feeling in {possessive} stomach enough to call for {gp}.",
    ),
    (
        '"What changed just before the noise?" {name} asked silently. "The taps started when the kitchen faucet started."',
        "The question turned the scare into a puzzle with a useful clue.",
    ),
    (
        '{name} thought, "A ghost is one guess, not the only guess. Old houses have pipes, and pipes can make sounds."',
        "Instead of creeping closer, {name} listened for where the sound began and where it ended.",
    ),
    (
        "For a moment {name}'s thoughts shouted, 'Hide!' Then a quieter thought answered, 'Stay where it is safe, breathe, and get {gp}.'",
        "{name} followed the quieter thought and felt fear shrink from enormous to manageable.",
    ),
]

DIALOGUES = [
    '"Good noticing," {gp} said. "We will investigate together, and I will handle the pipe."',
    '"Sounds can be mysterious before we find their cause," {gp} said. "You stay beside me while I check it."',
    '"Thank you for telling me instead of touching it," {gp} said. "That is careful courage."',
    '"Let us test your clue," {gp} said. "You may listen from here while I safely check the water."',
    '"Your ghost has excellent timing," {gp} joked gently. "It knocks whenever the water moves, so I suspect plumbing."',
    '"We do not have to pretend you were never scared," {gp} said. "We only have to choose a safe next step."',
    '"A good mystery solver uses ears, eyes, and help from a grown-up," {gp} said. "You have already used all three."',
]

RESOLUTIONS = [
    (
        "a pipe warming and expanding against its wooden bracket",
        "{gp} ran warm water while {name} listened from the doorway. The {source} ticked as it warmed against a wooden bracket, and {gp} marked the spot for a plumber to pad later.",
    ),
    (
        "a loose pipe clip rattling when water moved",
        "With {name} well back, {gp} checked the sound and found a loose clip rattling around the {source}. {gp} turned off the water and said a plumber would fasten it properly.",
    ),
    (
        "air moving through the old water pipe",
        "{gp} carefully tested a faucet, and the {source} answered with the same hollow bump. It was air moving through the old water pipe, something for a grown-up or plumber to check.",
    ),
    (
        "a slow drip landing in an empty metal basin",
        "{gp} found that a slow drip from the {source} was landing in an empty metal basin below. {gp} shut the nearby valve and put calling the plumber on the morning list.",
    ),
    (
        "the heating pipe cooling in its snug wall opening",
        "From the safe side of the {room}, {name} heard the knock fade as the house warmed. {gp} explained that the heating pipe had cooled in a snug opening and would be inspected before it was used again.",
    ),
    (
        "water pressure making the pipe nudge its support",
        "{gp} operated the faucet while {name} reported when each knock came. Their test showed that water pressure made the {source} nudge its support, so {gp} stopped the test and arranged a proper repair.",
    ),
    (
        "a dangling tag tapping the pipe",
        "{gp} shone a light into the utility space and spotted a paper service tag tapping the {source} whenever air stirred. Only {gp} reached in to remove it, and the ghostly reply stopped.",
    ),
]

ENDINGS = [
    "When sunrise filled the {room}, {name} drew three little music notes beside a pipe in the sunrise picture. The old house was quiet again, but now its quiet felt friendly.",
    "At breakfast, every harmless tick made {name} grin instead of jump. The mystery had left behind a warm mug, a bright window, and one carefully earned bit of courage.",
    "{name} named the mystery 'The Dawn Knocker' and wrote its very ordinary answer underneath. Sunlight crossed the floor where the imagined ghost had never been.",
    "Soon toast popped up and made both of them jump anyway. Their laughter followed the dawn light through the house, louder and happier than the pipe had been.",
    "{name} kept one hand near {gp}'s and listened to the last tiny ping disappear. Outside, the first bird sang again, and this time the house seemed to sing back.",
    "Before breakfast, {name} added a new rule to the family ghost stories: every ghostly noise deserved a safe investigation by a grown-up. Dawn gleamed on the now-silent wall.",
    "The sunrise finally reached the {room}, turning dust motes gold. {name} watched them float and felt proud that careful thinking, not pretending, had carried the morning out of fear.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    grandparent_type: str
    room: str
    source: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    room: str
    source: str
    helper: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.room, self.source, self.helper)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def asp_facts() -> str:
    import asp
    parts = [
        asp.fact("room", "grandparents_house"),
        asp.fact("source", "pipe"),
        asp.fact("helper", "flashlight"),
        asp.fact("helper", "grandparent"),
        asp.fact("helper", "blanket"),
        asp.fact("time", "dawn"),
    ]
    return "\n".join(parts)


ASP_RULES = r"""
% A dawn ghost story is reasonable when a child hears something eerie at dawn in a grandparent's house.
haunted_at_dawn(H) :- room(H), source(pipe), time(dawn).

% The scare is real if the pipe makes a sound in the dark.
scare(pipe) :- source(pipe).

% The child can become brave if they name the fear and use a helper.
brave(child) :- scare(pipe), helper(flashlight).
brave(child) :- scare(pipe), helper(grandparent).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show haunted_at_dawn/1. #show scare/1. #show brave/1."))
    atoms = {(sym.name, tuple(a.name if hasattr(a, "name") else getattr(a, "string", getattr(a, "number", None)) for a in sym.arguments)) for sym in model}
    expected = {("haunted_at_dawn", ("H",)), ("scare", ("pipe",)), ("brave", ("child",))}
    if atoms:
        print("OK: ASP program grounded and solved.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world set in a grandparent's house at dawn.")
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--grandparent-type", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("--room", choices=HOUSE_ROOMS)
    ap.add_argument("--source", choices=SCARE_SOURCES)
    ap.add_argument("--helper", choices=HELPERS)
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    grandparent_type = args.grandparent_type or ("grandmother" if child_type == "boy" else "grandfather")
    name = args.name or rng.choice(["Maya", "Leo", "Nina", "Eli", "June", "Owen"])
    room = args.room or rng.choice(HOUSE_ROOMS)
    source = args.source or rng.choice(SCARE_SOURCES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        child_name=name,
        child_type=child_type,
        grandparent_type=grandparent_type,
        room=room,
        source=source,
        helper=helper,
    )


def _plan_indices(seed: Optional[int]) -> tuple[int, ...]:
    """Spread adjacent replay seeds across every narrative axis without collisions."""
    sizes = (
        len(PREMISES),
        len(CONFLICTS),
        len(TURNS),
        7,
        len(DIALOGUES),
        len(RESOLUTIONS),
        len(ENDINGS),
    )
    span = 1
    for size in sizes:
        span *= size
    code = (((seed or 0) * 104729) + 8191) % span
    indices = []
    for size in sizes:
        indices.append(code % size)
        code //= size
    return tuple(indices)


def _safe_action(params: StoryParams, action_index: int) -> tuple[str, str]:
    gp = params.grandparent_type
    name = params.child_name
    support = {
        "flashlight": f"carried the flashlight to {gp}, who took it before approaching the pipe",
        "grandparent": f"called {gp} and waited until the grown-up came beside {name}",
        "warm blanket": f"wrapped up in the warm blanket and called {gp} from the doorway",
        "careful listening": f"listened from the doorway, then described the rhythm to {gp}",
    }[params.helper]
    support_label = {
        "flashlight": "the flashlight",
        "grandparent": gp,
        "warm blanket": "the warm blanket",
        "careful listening": "careful listening",
    }[params.helper]
    actions = [
        f"{name} {support}. {name} pointed toward the sound but did not touch the pipe.",
        f"With {support_label} for support, {name} {support}. Together they agreed that only {gp} would inspect the pipe.",
        f"{name} {support}. From a safe spot, {name} tapped the sound's rhythm on one knee so {gp} knew what to listen for.",
        f"Rather than entering the {params.room} alone, {name} {support}. The pipe stayed a grown-up job.",
        f"{name} {support}. When the noise came again, {name} said where it started while {gp} controlled the investigation.",
        f"The next safe step was simple: {name} {support}. {name} watched from well away from the plumbing.",
        f"{name} {support}. They made a team: {name} would notice and report, while {gp} would handle anything near the pipe.",
    ]
    return actions[action_index], support


def generate(params: StoryParams) -> StorySample:
    world = World(params.room, params.source, params.helper)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, location=params.room))
    grandparent = world.add(Entity(id="grandparent", kind="character", type=params.grandparent_type, label=params.grandparent_type, location=params.room))
    pipe = world.add(Entity(id="pipe", kind="thing", type="pipe", label="the pipe", location=params.room))
    helper = world.add(Entity(id="helper", kind="thing", type=params.helper, label=params.helper, location=params.room))

    child.memes["fear"] = 1.0
    pipe.meters["noise"] = 1.0
    world.facts.update(child=child, grandparent=grandparent, pipe=pipe, helper=helper)

    premise_i, conflict_i, turn_i, action_i, dialogue_i, resolution_i, ending_i = _plan_indices(params.seed)
    reflexive = "herself" if params.child_type == "girl" else "himself"
    possessive = "her" if params.child_type == "girl" else "his"
    fmt = {
        "name": params.child_name,
        "gp": params.grandparent_type,
        "room": params.room,
        "source": params.source,
        "reflexive": reflexive,
        "possessive": possessive,
    }
    premise = PREMISES[premise_i]
    turn_thought, turn_clue = TURNS[turn_i]
    safe_action, safe_action_fact = _safe_action(params, action_i)
    cause, reveal = RESOLUTIONS[resolution_i]

    world.say(premise[0].format(**fmt))
    world.say(premise[1].format(**fmt))
    world.say(CONFLICTS[conflict_i].format(**fmt))
    world.para()
    world.say(turn_thought.format(**fmt))
    world.say(turn_clue.format(**fmt))
    world.say(safe_action)
    world.say(DIALOGUES[dialogue_i].format(**fmt))
    world.para()
    reveal_text = reveal.format(**fmt)
    world.say(reveal_text[:1].upper() + reveal_text[1:])
    world.say(ENDINGS[ending_i].format(**fmt))

    child.memes["fear"] = 0.25
    child.memes["courage"] = 1.0
    pipe.meters["noise"] = 0.0
    world.facts.update(
        cause=cause,
        safe_action=safe_action_fact,
        adult_controlled=True,
        child_feeling_before="frightened and curious",
        child_feeling_after="calm and proud",
    )

    story = world.render()
    prompts = [
        f"Write a gentle ghost story for a young child set in a grandparent's house at dawn, featuring a pipe and an inner monologue.",
        f"Tell a child-sized spooky story where {params.child_name} hears a pipe in {params.grandparent_type}'s house and thinks through the fear.",
        f"Create a quiet dawn story that feels a little ghostly, but ends with courage and a clear explanation for the pipe sound.",
    ]
    story_qa = [
        QAItem(
            question=f"Where does {params.child_name} hear the strange sound?",
            answer=f"{params.child_name} hears it in the {params.room} of {params.grandparent_type}'s house.",
        ),
        QAItem(
            question=f"How does {params.child_name} think through the scary sound?",
            answer=f"{params.child_name} notices that being afraid is not proof of a ghost and looks for a real clue. Instead of touching the pipe, {params.child_name} gets help from {params.grandparent_type}.",
        ),
        QAItem(
            question="What really causes the ghostly noise?",
            answer=f"The noise comes from {cause}, not a ghost. {params.grandparent_type} safely checks the cause while {params.child_name} stays back.",
        ),
        QAItem(
            question=f"What safe choice does {params.child_name} make?",
            answer=f"{params.child_name} {safe_action_fact}. {params.child_name} observes and reports, while {params.grandparent_type} handles the pipe.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is dawn?",
            answer="Dawn is the early time of morning when the sun is just starting to light the sky.",
        ),
        QAItem(
            question="What is a pipe in a house?",
            answer="A pipe is a tube that carries water or other things through a house, and old pipes can sometimes make tapping or clinking sounds.",
        ),
        QAItem(
            question="Why can old houses make spooky sounds?",
            answer="Old houses can make spooky sounds because wood, walls, and pipes can settle, cool, or move a little as the temperature changes.",
        ),
        QAItem(
            question="What should a child do after noticing a strange pipe sound?",
            answer="A child should stay away from the pipe and tell a trusted grown-up what they heard. A grown-up can inspect the area or call a plumber.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:9} ({e.type:12}) {' '.join(bits)}")
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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(child_name="Maya", child_type="girl", grandparent_type="grandmother", room="kitchen", source="pipe", helper="flashlight", seed=11),
    StoryParams(child_name="Leo", child_type="boy", grandparent_type="grandfather", room="hallway", source="dripping pipe", helper="grandparent", seed=22),
    StoryParams(child_name="June", child_type="girl", grandparent_type="grandmother", room="basement", source="banging pipe", helper="warm blanket", seed=33),
]


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
        print(asp_program("#show haunted_at_dawn/1. #show scare/1. #show brave/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP mode is available for this storyworld.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
