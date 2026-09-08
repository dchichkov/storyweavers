#!/usr/bin/env python3
"""Pirate tale storyworld about a historic shutter, friendship, and problem solving."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "mate", "pirate", "deckhand", "parrot"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Captain Finn"
    friend: str = "Mira"
    helper: str = "Toby"
    place: str = "harbor"
    incident: int = 0
    opening: int = 0
    turn: int = 0
    dialogue: int = 0
    ending: int = 0


CAPTAINS = ["Captain Finn", "Captain Jun", "Captain Bea", "Captain Row"]
FRIENDS = ["Mira", "Toby", "Lina", "Nell"]
HELPERS = ["Jory", "Pip", "Sail", "Rin"]
PLACES = ["harbor", "wharf", "cove", "dockside"]

INCIDENTS = [
    {
        "title": "the stuck historic shutter",
        "premise": "A museum ship at the harbor had a historic shutter that guarded a lantern room.",
        "problem": "A storm jammed the shutter halfway open, and sea spray rushed through the gap.",
        "mistake": "The first tug only made the old hinge groan: kreeeak!",
        "clue": "Mira noticed salt crust packed around the bottom pin, like tiny white rocks.",
        "action": "The friends washed the pin, greased it with lamp oil, and lifted together: heave-ho, click!",
        "result": "The shutter swung shut and the lantern stayed bright for the night watch.",
        "lesson": "A careful look can solve what a hard pull cannot.",
        "ending": "The historic shutter rested snug and square in the lantern room wall.",
        "object": "historic shutter",
    },
    {
        "title": "the crooked map shutter",
        "premise": "Below deck, an old chart room had a shutter that kept knocking against the frame.",
        "problem": "Every wobble made the treasure map table shake, and the ink pen slid away.",
        "mistake": "Captain Finn slammed the shutter once. Bang! It shook even worse.",
        "clue": "Toby saw the latch hook was bent just enough to miss its catch.",
        "action": "The crew straightened the hook with a spoon handle and tested it twice: tap, tap, steady.",
        "result": "The map table stopped rattling, and the crew could plan the next sail.",
        "lesson": "Small fixes can matter more than big noise.",
        "ending": "The chart room was quiet except for one soft, steady breeze.",
        "object": "chart room shutter",
    },
    {
        "title": "the pirate bakery shutter",
        "premise": "A dockside bakery used an old shutter to keep gulls out of the warm buns.",
        "problem": "The shutter would not close, and the gulls swooped in shouting, 'Cake! Cake!'",
        "mistake": "Captain Finn chased the birds, but the birds only laughed and flapped higher.",
        "clue": "Mira found a bead of sticky jam wedged in the lower track.",
        "action": "The friends scraped the jam clean, then pulled the shutter down together: scritch, thunk.",
        "result": "The buns stayed safe, and the bakery owner waved with a floury grin.",
        "lesson": "Solve the cause, not just the flying problem.",
        "ending": "Warm buns cooled safely behind the shut bakery window.",
        "object": "bakery shutter",
    },
    {
        "title": "the rain-soaked signal shutter",
        "premise": "On the masthouse wall, a signal shutter flashed messages to waiting boats.",
        "problem": "Rain made the painted slats swell, so the shutter would not open for the evening code.",
        "mistake": "The helper tugged hard and only made the rope twist: snap, twirl!",
        "clue": "Captain Finn felt the swollen wood and saw the rope knot was binding the top rail.",
        "action": "Mira loosened the knot while Toby held the rail straight, then the crew tried again together.",
        "result": "The shutter opened in time to send the safe-water signal to three ships.",
        "lesson": "Friendship means sharing the work and the thinking.",
        "ending": "Three lantern boats answered the bright shutter signal from the dark water.",
        "object": "signal shutter",
    },
    {
        "title": "the museum ghost shutter",
        "premise": "Visitors said a ghost rattled the old museum ship at midnight.",
        "problem": "The noise came from a loose shutter banging in the wind.",
        "mistake": "The deckhands whispered and tiptoed, but the banging kept going: clack-clack-clack.",
        "clue": "Lina spotted a loose peg swinging on a string of frayed sailcloth.",
        "action": "The friends tied the peg tight, wedged the shutter, and checked the latch under moonlight.",
        "result": "The ghostly noise stopped, and the visitors slept without fear.",
        "lesson": "A scary story can have a simple, real cause.",
        "ending": "Moonlight rested on the quiet museum ship and its still shutter.",
        "object": "museum shutter",
    },
    {
        "title": "the storm cellar shutter",
        "premise": "A seaside storm cellar had to stay sealed before the tide rose.",
        "problem": "The heavy shutter was jammed by a shell caught in the groove.",
        "mistake": "Captain Finn pried with a hook, but the shell only wedged tighter: screech!",
        "clue": "Jory noticed the shell was cracked and easy to break apart by hand.",
        "action": "The crew tapped the shell free, wiped the groove, and shut the door together.",
        "result": "The cellar stayed dry when the tide rushed past outside.",
        "lesson": "A shared problem gets easier when everyone looks closely.",
        "ending": "Dry barrels slept behind the sealed cellar shutter.",
        "object": "cellar shutter",
    },
    {
        "title": "the lantern-house shutter",
        "premise": "A lighthouse keeper asked for help with an old lantern-house shutter.",
        "problem": "The shutter would not stay open, so the lamp could not breathe well.",
        "mistake": "The keeper tied it with one rope, but the rope slipped: zip!",
        "clue": "Mira saw that the hinge needed a wooden wedge, not more rope.",
        "action": "The crew cut a neat wedge, fit it under the frame, and tested the opening twice.",
        "result": "The lantern burned clean and bright all evening.",
        "lesson": "The right tool is better than extra force.",
        "ending": "Bright light poured from the lantern house through the open sea wind.",
        "object": "lantern-house shutter",
    },
    {
        "title": "the treasure-room shutter",
        "premise": "An old captain's treasure room on the ship had a shutter carved with anchors.",
        "problem": "The shutter jammed, and the crew could not reach the map chest inside.",
        "mistake": "Toby pushed with both shoulders, but the wood only complained: ugh-creak.",
        "clue": "Captain Finn noticed a rusty nail lifting one corner of the frame.",
        "action": "Mira used a spoon to pull the nail, and the crew opened the shutter gently.",
        "result": "The map chest opened safely, and the treasure stayed untouched.",
        "lesson": "Gentle work can protect old things.",
        "ending": "The carved shutter stood open like a polite grin.",
        "object": "treasure-room shutter",
    },
]

OPENINGS = [
    "At the {place}, {captain} and the crew began the day with tar on their boots and salt in the air.",
    "Near the {place}, {friend} spotted trouble before the bells finished ringing.",
    "The morning wind swept over the {place}, where {captain} was already pacing and thinking.",
    "On the edge of the {place}, an old ship and a brave crew waited for a problem to solve.",
    "Long before noon at the {place}, {friend} called the others over to a curious old shutter.",
]

TURNS = [
    "{captain} said, 'Hard hands won't fix this. We need clear eyes.'",
    "{friend} said, 'Look at the track first. The answer may be hiding there.'",
    "{helper} asked, 'What changed before it got stuck?' and that question opened the way forward.",
    "'Let's work together,' said {captain}. 'One pair of hands can miss what three pairs can find.'",
]

DIALOGUE = [
    "'I'll tug!' said {helper}. 'Wait,' said {friend}, 'let me check the hinge.'",
    "'Do you hear that?' asked {friend}. 'Aye,' said {captain}, 'the shutter is telling us where it hurts.'",
    "'Not more force,' said {captain}. 'Then what?' asked {helper}. 'A better plan,' said {friend}.",
    "'We can do this together,' said {friend}. 'Aye,' said {captain}, 'steady as the tide.'",
]

ENDING_LINES = [
    "By sunset, the crew had solved the trouble, and the old ship felt safe again.",
    "When night came, the harbor shone steady, and the crew smiled at the work they had done.",
    "The last beam of light slipped across the deck, and everyone knew the ship was ready for tomorrow.",
    "With the problem solved, the friends shared a laugh and watched the sea settle down.",
]

ASP_RULES = r"""
#show solved/1.
#show friendship/2.
#show problem_solving/1.

solved(incident) :- fixed(shutter), shared_work, careful_look.
friendship(captain, crew) :- shared_work.
problem_solving(plan) :- careful_look, shared_work.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("fixed", "shutter"),
            asp.fact("shared_work"),
            asp.fact("careful_look"),
            asp.fact("friendship_seed"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about a historic shutter.")
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES, default="harbor")
    ap.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
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
    return StoryParams(
        seed=args.seed,
        captain=args.captain or rng.choice(CAPTAINS),
        friend=args.friend or rng.choice(FRIENDS),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        incident=args.incident if args.incident is not None else rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        turn=rng.randrange(len(TURNS)),
        dialogue=rng.randrange(len(DIALOGUE)),
        ending=rng.randrange(len(ENDING_LINES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))
    friend = world.add(Entity(id=params.friend, kind="character", type="mate", label=params.friend))
    helper = world.add(Entity(id=params.helper, kind="character", type="deckhand", label=params.helper))
    shutter = world.add(Entity(id="historic shutter", kind="object", type="shutter", label="historic shutter"))
    shutter.meters["stuck"] = 1.0
    captain.memes["calm"] = 1.0
    friend.memes["helpful"] = 1.0
    helper.memes["eager"] = 1.0

    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    common = {
        "captain": captain.id,
        "friend": friend.id,
        "helper": helper.id,
        "place": params.place,
    }

    def personalize(text: str) -> str:
        return text.replace("Captain Finn", captain.id).replace("Mira", friend.id).replace("Toby", helper.id)

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**common))
    world.say(personalize(incident["premise"]))
    world.say(personalize(incident["problem"]))
    world.say(TURNS[params.turn % len(TURNS)].format(**common))
    world.say(DIALOGUE[params.dialogue % len(DIALOGUE)].format(**common))
    world.say(personalize(incident["mistake"]))
    world.say(personalize(incident["clue"]))
    world.say(personalize(incident["action"]))
    world.say(personalize(incident["result"]))
    world.say(personalize(incident["lesson"]).capitalize() + ".")
    world.say(ENDING_LINES[params.ending % len(ENDING_LINES)])
    world.say(personalize(incident["ending"]))

    shutter.meters["stuck"] = 0.0
    shutter.meters["open"] = 0.0
    shutter.memes["safe"] = 1.0
    world.facts.update(
        captain=captain,
        friend=friend,
        helper=helper,
        shutter=shutter,
        incident=incident,
        solved=True,
        friendship=True,
        problem_solving=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about {f['captain'].id}, {f['friend'].id}, and a historic shutter that will not move.",
        f"Tell a child-friendly story where friendship and problem solving help fix an old shutter at the harbor.",
        f"Write a sea adventure with dialogue, a stuck shutter, and a calm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    return [
        QAItem(
            question="What was the main problem in the story?",
            answer=f"The main problem was {incident['problem']}",
        ),
        QAItem(
            question="How did the friends solve it?",
            answer=incident["action"],
        ),
        QAItem(
            question="What did the clue reveal?",
            answer=incident["clue"],
        ),
        QAItem(
            question="What changed by the end?",
            answer=incident["ending"],
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship in a story?",
            answer="Friendship is a warm relationship where characters care about each other and help one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a trouble, thinking about its cause, and trying a useful fix.",
        ),
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel or cover that opens and closes over a window, doorway, or lantern room.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:20} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show friendship/2.\n#show problem_solving/1.\n#show solved/1."))
    got_friendship = set(asp.atoms(model, "friendship"))
    got_problem = set(asp.atoms(model, "problem_solving"))
    got_solved = set(asp.atoms(model, "solved"))
    ok = got_friendship == {("captain", "crew")} and got_problem == {("plan",)} and got_solved == {("incident",)}
    if ok:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  friendship:", sorted(got_friendship))
    print("  problem_solving:", sorted(got_problem))
    print("  solved:", sorted(got_solved))
    return 1


CURATED = [
    StoryParams(captain="Captain Finn", friend="Mira", helper="Toby", place="harbor", incident=0),
    StoryParams(captain="Captain Jun", friend="Lina", helper="Pip", place="wharf", incident=3, opening=1, turn=3, dialogue=0, ending=1),
    StoryParams(captain="Captain Bea", friend="Nell", helper="Rin", place="cove", incident=6, opening=4, turn=2, dialogue=3, ending=2),
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
        print(asp_program("#show friendship/2.\n#show problem_solving/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show friendship/2.\n#show problem_solving/1.\n#show solved/1."))
        print("friendship:", asp.atoms(model, "friendship"))
        print("problem_solving:", asp.atoms(model, "problem_solving"))
        print("solved:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if args.all:
            header = f"### {sample.params.captain} at the {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
