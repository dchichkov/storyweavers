#!/usr/bin/env python3
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


ASP_RULES = r"""
% A small pirate-tale world with a historic shutter, friendship, and problem solving.
place(harbor).
feature(friendship).
feature(problem_solving).
feature(historic).
feature(shutter).

shutter_is_old :- feature(historic), feature(shutter).
crew_can_help :- feature(friendship), feature(problem_solving).
safe_fix :- shutter_is_old, crew_can_help.

happy_story :- safe_fix.
#show happy_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Captain Mira"
    friend: str = "Jory"
    vessel: str = "the Gull"
    place: str = "harbor"
    object_name: str = "the historic shutter"
    treasure: str = "a brass star map"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the shutter that would not shut",
        "premise": "the historic shutter on the old lighthouse kept swinging open in the sea wind",
        "obstacle": "It made a loud clack-clack and let rain splash onto the chart room floor",
        "clue": "fresh rope fibers were caught on one brass hinge",
        "mistake": "{captain} first tried to force the shutter closed with one hand on the wet frame",
        "action": "{friend} held the lantern steady while {captain} measured the hinge and tied the loose rope back with a sailor's knot",
        "dialogue": "'Two hands and two minds are safer than one quick tug,' {captain} said",
        "resolution": "The shutter settled into its old groove, and the room stayed dry",
        "ending": "moonlight rested on the fixed shutter like a silver flag at the harbor window",
        "lesson": "friendship and problem solving turn a noisy trouble into a careful repair",
    },
    {
        "title": "the shutter map clue",
        "premise": "behind the historic shutter, salt dust had left a pale stripe shaped like an X",
        "obstacle": "The crew feared a hidden leak or a hidden thief in the lighthouse wall",
        "clue": "the stripe matched the exact width of the shutter slat, not a crack in the stone",
        "mistake": "{captain} wanted to accuse the deckhand in a hurry, but {friend} asked for one more look",
        "action": "{captain} and {friend} traced the stripe together, then opened the lower panel to find a jammed drawer",
        "dialogue": "'Let's solve the puzzle before we blame the people,' {friend} whispered",
        "resolution": "Inside the drawer sat the spare brass key and a map tube that had been missing for weeks",
        "ending": "the recovered tube leaned beside the shutter while gulls circled above the calm harbor",
        "lesson": "careful looking protects friendships and finds the true answer",
    },
    {
        "title": "the shutter and the storm bell",
        "premise": "the historic shutter rattled each time the storm bell rang at dusk",
        "obstacle": "A loose latch threatened to snap and wake the whole harbor with its banging",
        "clue": "the latch only slipped when the bell rope swung past it",
        "mistake": "{friend} nearly tied the rope tighter, but noticed the knot would only make the swing worse",
        "action": "{captain} sent {friend} to hold the bell rope still while {captain} wedged the latch with a carved wooden shim",
        "dialogue": "'Hold fast, mate, and I can think,' {captain} called",
        "resolution": "With the rope quiet, the latch stayed set and the storm bell could ring without trouble",
        "ending": "the shutter stood firm while the bell sang above the harbor like a safe, steady song",
        "lesson": "problem solving works best when friends share the load",
    },
    {
        "title": "the shutter with the missing paint",
        "premise": "one panel of the historic shutter had peeled to reveal an old blue stripe under the paint",
        "obstacle": "The crew argued whether to repaint it or leave the stripe as a sign of the lighthouse's age",
        "clue": "the stripe matched a painted mark in the keeper's journal",
        "mistake": "{captain} almost chose a bright new color at once, but {friend} slowed the decision and opened the journal",
        "action": "{captain} read the note aloud while {friend} brushed away dust from the panel edges",
        "dialogue": "'History is part of the ship's story, even when it is only a shutter,' {friend} said",
        "resolution": "They cleaned the panel and left the old blue stripe showing, safe under a clear coat",
        "ending": "the shutter glowed with age and care, as proud as a treasure chest on deck",
        "lesson": "friendship can help a crew honor the past while fixing the present",
    },
    {
        "title": "the shutter on the tide line",
        "premise": "high tide sent a thin line of foam licking the base of the historic shutter",
        "obstacle": "If water climbed higher, it would rot the wood and spoil the chart room",
        "clue": "the tide line stopped where a broken crate had stacked against the wall",
        "mistake": "{captain} thought the crate should be tossed overboard, but {friend} saw it could be turned into a shield",
        "action": "{captain} and {friend} hauled the crate apart and built a small splash guard from its boards",
        "dialogue": "'A broken thing can still help if we use it wisely,' {captain} said",
        "resolution": "The splash guard kept the next wave from the shutter, and the wood stayed dry",
        "ending": "foam hissed below the new guard while the shutter held like a loyal deckhand",
        "lesson": "problem solving can turn wreckage into a useful tool",
    },
    {
        "title": "the shutter lantern mystery",
        "premise": "the historic shutter flashed bright and dim when the lantern outside the lighthouse bobbed in the breeze",
        "obstacle": "The harbor boats mistook the flashes for a distress call",
        "clue": "the lantern chain was snagged on the shutter hook",
        "mistake": "{friend} reached for the hook too quickly and nearly pinched a finger",
        "action": "{captain} held the chain high while {friend} loosened the snag with a safe wooden hook",
        "dialogue": "'Slow is smooth, and smooth keeps friends safe,' {captain} told {friend}",
        "resolution": "The lantern steadied, the flashes stopped, and the boats kept on their routes",
        "ending": "the shutter and lantern shone together like two calm stars above the black water",
        "lesson": "a steady plan can calm confusion before it becomes a bigger problem",
    },
    {
        "title": "the shutter and the sea ledger",
        "premise": "behind the historic shutter was a damp sea ledger full of ship names and cargo marks",
        "obstacle": "The ink was smudging, and the lighthouse keeper needed the record before morning",
        "clue": "the driest corner of the room lay beside a closed shutter seam",
        "mistake": "{captain} first waved the pages in the wind, which only bent the paper",
        "action": "{friend} fetched clean cloth while {captain} pressed the ledger flat and used the shutter seam to keep off the spray",
        "dialogue": "'You watch the door, and I'll watch the pages,' {friend} said",
        "resolution": "Together they saved the names, and the keeper could read every line at dawn",
        "ending": "the ledger dried safe beside the repaired shutter, neat as a sailor's folded coat",
        "lesson": "good friends share the job and save what matters",
    },
    {
        "title": "the shutter under the moon flag",
        "premise": "a moon flag had snagged on the historic shutter and would not come free",
        "obstacle": "The flag blocked the signal that told incoming boats the harbor was open",
        "clue": "the cloth pulled only when the wind shifted from the west",
        "mistake": "{captain} wanted to climb fast, but {friend} pointed to the slippery sill",
        "action": "{captain} tied off the ladder while {friend} guided the pole and freed the cloth one corner at a time",
        "dialogue": "'We can be brave without being foolish,' {friend} said",
        "resolution": "The moon flag rose clear, and the harbor lantern answered with a bright welcome",
        "ending": "the open shutter framed the flag as it flapped above the safe, sleeping ships",
        "lesson": "problem solving is strongest when bravery listens to caution",
    },
]


OPENINGS = [
    "At the harbor, {captain} and {friend} boarded {vessel} just as the evening breeze touched the masts.",
    "The sea air smelled of salt when {captain}, {friend}, and {vessel} reached the old harbor at dusk.",
    "By the lighthouse door, {captain} found {friend} waiting beside {vessel} and a warm lantern glow.",
    "When the tide turned, {captain} and {friend} arrived at the harbor with {vessel} creaking softly.",
    "A gull cried overhead as {captain} and {friend} stepped onto the boards near the old harbor wall.",
    "The crew had barely tied off {vessel} when {captain} noticed trouble near the lighthouse shutter.",
    "At dusk, {captain} and {friend} carried a lantern toward the harbor lighthouse.",
    "The harbor was quiet until {captain} heard a sharp clack from the historic shutter.",
]

TURNS = [
    "That was the moment the crew stopped guessing and started solving.",
    "Friendship kept the worry small enough to think about.",
    "A careful second look changed the whole plan.",
    "The first idea was hurried, but the better idea was steady.",
    "Once they spoke plainly to each other, the answer began to show itself.",
    "The trouble looked bigger than it was, until they split the task into smaller parts.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about a historic shutter, friendship, and problem solving.")
    ap.add_argument("--captain")
    ap.add_argument("--friend")
    ap.add_argument("--vessel")
    ap.add_argument("--place")
    ap.add_argument("--object-name")
    ap.add_argument("--treasure")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "harbor"
    object_name = args.object_name or "the historic shutter"
    treasure = args.treasure or "a brass star map"
    if place != "harbor":
        raise StoryError("This pirate tale is built around the harbor.")
    if "shutter" not in object_name.lower():
        raise StoryError("The story object must be a shutter.")
    return StoryParams(
        seed=None,
        captain=args.captain or rng.choice(["Captain Mira", "Captain Bea", "Captain Nia", "Captain Sol"]),
        friend=args.friend or rng.choice(["Jory", "Pip", "Luma", "Tess"]),
        vessel=args.vessel or rng.choice(["the Gull", "the Tern", "the Ruby Finch"]),
        place=place,
        object_name=object_name,
        treasure=treasure,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "harbor"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "historic"),
            asp.fact("feature", "shutter"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_story/0."))
    asp_ok = bool(asp.atoms(model, "happy_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the happy story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]

    captain = world.add_character(Character(name=p.captain, role="captain"))
    friend = world.add_character(Character(name=p.friend, role="friend"))
    vessel = world.add_object(ObjectThing(name=p.vessel, kind="ship"))
    shutter = world.add_object(ObjectThing(name=p.object_name, kind="historic_shutter"))
    treasure = world.add_object(ObjectThing(name=p.treasure, kind="map"))

    captain.add_meme("responsibility", 1)
    friend.add_meme("loyalty", 1)
    shutter.add_meter("age", 80)
    shutter.add_meme("history", 1)

    values = {
        "captain": p.captain,
        "friend": p.friend,
        "vessel": p.vessel,
    }

    world.say(opening.format(**values))
    world.say(
        f"They had come to check {p.object_name}, a historic shutter older than the dock bells, "
        f"because {p.treasure} was kept nearby and the night tide was rising."
    )
    world.say(f"The trouble was simple to hear: {scenario['premise']}.")
    world.say(f"{scenario['obstacle']}. {scenario['clue']}.")
    world.say(f"{scenario['mistake'].format(**values)}. {turn}")
    captain.add_meter("steps", 6)
    friend.add_meter("steps", 6)
    world.say(f"{scenario['action'].format(**values)}.")
    world.say(f"{scenario['dialogue'].format(**values)}.")
    world.say(f"{scenario['resolution']}.")
    captain.add_meme("relief", 1)
    friend.add_meme("pride", 1)
    shutter.add_meter("stability", 1)
    treasure.add_meter("safety", 1)
    world.say(
        f"By the end, {p.object_name} was steady again, and the crew could keep {p.treasure} dry and safe. "
        f"{scenario['ending']}."
    )
    world.say(
        f"That was how {scenario['lesson']}. "
        f"{p.captain} and {p.friend} smiled at each other, glad they had solved it together."
    )

    world.facts = {
        "captain": p.captain,
        "friend": p.friend,
        "vessel": p.vessel,
        "place": p.place,
        "object_name": p.object_name,
        "treasure": p.treasure,
        "scenario": scenario["title"],
        "premise": scenario["premise"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "resolution": scenario["resolution"],
        "ending_image": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    facts = world.facts
    return [
        QAItem(
            question=f"What problem did {p.captain} and {p.friend} face?",
            answer=f"They faced this trouble: {facts['obstacle']}. It mattered because the historic shutter had to be fixed to keep the harbor room safe.",
        ),
        QAItem(
            question="What clue helped them understand the trouble?",
            answer=f"The clue was: {facts['clue']}. That clue showed where to focus instead of guessing.",
        ),
        QAItem(
            question="How did friendship matter in the story?",
            answer=f"{p.captain} and {p.friend} worked side by side, shared the job, and spoke kindly. Their friendship made the solution easier and safer.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"The problem was solved when {facts['resolution']}. They used careful problem solving instead of a rushed fix.",
        ),
        QAItem(
            question="What ending image proves the change?",
            answer=f"The ending image is: {facts['ending_image']}. It shows the shutter settled, which proves the repair worked.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship in this world?",
            answer="Friendship means helping each other, speaking honestly, and staying close when a problem appears.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing clues, trying a careful plan, and changing course when the first idea is not the best.",
        ),
        QAItem(
            question="What makes a shutter historic?",
            answer="A historic shutter is old and worth keeping because it carries the memory and style of the place.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    facts = world.facts
    return [
        f"Write a pirate tale about {p.captain} and {p.friend} at the harbor with {p.object_name}.",
        f"Include the clue {facts['clue']} and show how friendship helps solve the problem.",
        f"End with this image: {facts['ending_image']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show happy_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_story/0."))
        print("happy_story" if asp.atoms(model, "happy_story") else "(no happy_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        try:
            params = resolve_params(args, random.Random(base_seed))
        except StoryError as err:
            print(err)
            return
        params.seed = base_seed
        samples = [generate(params)]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
