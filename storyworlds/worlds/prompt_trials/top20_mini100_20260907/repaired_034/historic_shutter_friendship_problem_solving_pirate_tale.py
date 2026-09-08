#!/usr/bin/env python3
"""
A small pirate-tale storyworld about an old shutter, friendship, and problem solving.

Premise:
- A little pirate crew works near a historic dockside house.
- A stubborn shutter will not stay open, and that causes trouble for a useful lookout.
- Two friends solve the problem by listening, testing, and helping each other.
- A brief spoken exchange changes what they decide to do.
- The ending proves the change with a safe, shared result.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Mara"
    friend: str = "Jules"
    place: str = "the old harbor lane"
    object_name: str = "the shutter"
    historic_place: str = "the historic tide house"
    problem: str = "the shutter keeps swinging shut and hiding the lookout window"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    friend: Entity
    place: Entity
    shutter: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Mara", "Jules", "Pip", "Risa", "Ned", "Tessa", "Bo"]
FRIEND_NAMES = ["Jules", "Mara", "Pip", "Risa", "Ned", "Tessa", "Bo"]
PLACES = [
    "the old harbor lane",
    "the windy quay path",
    "the cobbled dock street",
    "the salt-bright pier road",
]
HISTORIC_PLACES = [
    "the historic tide house",
    "the old captain's house",
    "the historic lantern shop",
    "the antique dockmaster's office",
]
OBJECTS = ["the shutter", "the blue shutter", "the painted shutter", "the creaky shutter"]


ARCS = [
    {
        "problem": "the shutter keeps swinging shut and hiding the lookout window",
        "stake": "Without the window, the crew cannot spot the moon tide that guides boats in",
        "temptation": "kick the shutter hard and be done with it",
        "clue": "the shutter only stuck when one loose hinge pin slipped lower than the other",
        "action": "They propped the shutter with a broom, checked the hinge pins, and tied a soft cord through the latch",
        "twist": "the old latch was bent, but a spare nail from the tool box fit it perfectly",
        "sharing": "They split the work: one held the board, one fixed the pin, and both tested the window together",
        "lesson": "a small problem can be solved faster when friends compare clues instead of forcing a quick answer",
        "ending": "the lookout window stood open, and a clear beam from the moon tide lit the safe path home",
        "question": "Why did the crew need the lookout window open?",
        "answer": "They needed it open so they could spot the moon tide and guide boats safely in.",
    },
    {
        "problem": "the shutter rattles so loudly that it wakes the sleeping mapmaker upstairs",
        "stake": "If the mapmaker cannot rest, the crew will lose the next day's chart work",
        "temptation": "tie the shutter shut and ignore the broken catch",
        "clue": "the rattle stopped whenever someone pressed the loose board from below",
        "action": "They wedged a little block under the sill and found the catch had warped in damp air",
        "twist": "the mapmaker offered a waxed strip from an old chart, and it calmed the catch at once",
        "sharing": "They used the strip together and thanked the mapmaker for the useful idea",
        "lesson": "friendship means listening to the people who know the place best",
        "ending": "the mapmaker slept through the night while the shutter stayed quiet as a mouse",
        "question": "What woke the mapmaker upstairs?",
        "answer": "The shutter rattling loudly woke the mapmaker upstairs.",
    },
    {
        "problem": "the shutter will not open wide enough for the signal lantern to shine out",
        "stake": "The signal boat offshore will miss the warning and sail into a rough shoal",
        "temptation": "pry the shutter open with a rusty hook",
        "clue": "the lower frame was blocked by a tiny driftwood wedge from a storm",
        "action": "They lifted the frame, pulled out the wedge, and oiled the hinges with lamp grease",
        "twist": "the wedge had been set there by an old cat to keep rain from blowing in",
        "sharing": "They moved the cat's bed to a drier corner and shared the last of the lamp grease",
        "lesson": "solving a problem well means understanding why it started",
        "ending": "the lantern shone straight out over the water, and the signal boat turned safely away from the shoal",
        "question": "What was blocking the shutter frame?",
        "answer": "A tiny driftwood wedge was blocking the lower frame.",
    },
    {
        "problem": "the shutter keeps snapping shut whenever the sea wind grows strong",
        "stake": "The crew cannot keep watch for the pirate messenger who is late",
        "temptation": "hold the shutter with one arm and boast about it",
        "clue": "the wind came from the left, but the latch bent toward the right",
        "action": "They lashed a rope loop to the wall ring and angled the shutter against the gusts",
        "twist": "the messenger was not late at all; the crew had been watching the wrong road",
        "sharing": "They shared the lookout duty and watched both roads at once",
        "lesson": "a friend helps you see more than one side of a problem",
        "ending": "two pirates kept watch together while the shutter stayed firm against the wind",
        "question": "What helped the crew keep the shutter from snapping shut?",
        "answer": "They used a rope loop and set the shutter against the gusts.",
    },
    {
        "problem": "the shutter jammed because old paint had glued it to the sill",
        "stake": "The crew needs the room open before the tide reaches the stone steps",
        "temptation": "chip the paint away with a knife and risk breaking the wood",
        "clue": "warm sunlight made the paint soften near the top edge",
        "action": "They brought a basin of warm water, loosened the paint gently, and slid a flat spoon under the seam",
        "twist": "the spoon was stamped with the name of the first dock keeper from long ago",
        "sharing": "They cleaned the spoon and placed it on the mantle as a shared keepsake",
        "lesson": "patient hands can rescue old things without hurting them",
        "ending": "the historic room opened with a soft sigh, and the steps stayed dry behind the tide",
        "question": "How did the friends loosen the glued shutter?",
        "answer": "They used warm water and a flat spoon to loosen it gently.",
    },
    {
        "problem": "the shutter's little hook is missing, so it cannot stay open",
        "stake": "The chart room will be too dark to read the night harbor notes",
        "temptation": "borrow a hook from another door without asking",
        "clue": "a bent fishhook hung from a line of spare keys in the tool box",
        "action": "They shaped the fishhook into a new latch and measured it with a ribbon",
        "twist": "the fishhook belonged to the hero's friend, who had saved it for a lucky day",
        "sharing": "They used the hook together and made a second hook for the other door",
        "lesson": "asking first is better than taking, and sharing can fix more than one thing",
        "ending": "both doors held open, and the night notes glowed on the chart room table",
        "question": "What did they use to make a new latch?",
        "answer": "They shaped a bent fishhook into a new latch.",
    },
    {
        "problem": "the shutter keeps banging because a loose rope flaps against it",
        "stake": "The noise may frighten the harbor cats and scare away the fishers",
        "temptation": "cut the rope and leave the knot behind",
        "clue": "the rope only slapped the shutter when the knot swung too low",
        "action": "They shortened the line, tied a neater knot, and hooked the rope higher on the beam",
        "twist": "the rope had once belonged to the old lighthouse keeper, who had tied it for storm season",
        "sharing": "They kept the rope in use and shared the story of the keeper with the younger crew",
        "lesson": "one careful fix can honor the past and quiet the present",
        "ending": "the harbor stayed calm, and the cats curled back to sleep beside the warm stones",
        "question": "What made the shutter bang loudly?",
        "answer": "A loose rope was flapping against the shutter.",
    },
    {
        "problem": "the shutter is too stiff to open after a cold night of sea spray",
        "stake": "The morning lookout cannot check the reef before the boats depart",
        "temptation": "pull with all their strength and force it open",
        "clue": "the wood moved a little when rubbed with a dry cloth",
        "action": "They warmed the hinges with a lantern, wiped the salt away, and worked the shutter slowly back and forth",
        "twist": "the cold had also made the latch shrink, so a small shim solved the last pinch",
        "sharing": "They passed the lantern, cloth, and shim between them until the shutter moved freely",
        "lesson": "big strength is not always the best tool; steady teamwork can do more",
        "ending": "the reef came into view, and the first boats glided past the rocks in a safe line",
        "question": "Why was the shutter too stiff to open?",
        "answer": "It was stiff because cold sea spray had made the wood and latch tight.",
    },
]

OPENINGS = [
    "Morning mist clung to the docks like a soft gray sail",
    "A bright gull cry bounced over the pier and woke the lane",
    "The sea breeze smelled of tar, salt, and wet rope",
    "At sunrise, the old harbor lane looked sleepy but shining",
    "Blue water flashed beyond the pilings while the tide crept in",
    "The first light touched the historic house and turned its windows gold",
]

DIALOGUE_LINES = [
    "{hero} said, “Let’s look before we push.”",
    "{friend} answered, “A friend who looks twice finds more than a friend who rushes.”",
    "{hero} said, “Then I will test the hinge, not the wood.”",
    "{friend} said, “Good. I will hold the board while you try.”",
    "{hero} asked, “Do you see the real trouble?”",
    "{friend} replied, “Yes, and we can fix it together.”",
]

CLOSINGS = [
    "{hero} grinned, because the old shutter now worked like a friendly door in the wind.",
    "{hero} and {friend} left the historic house with salt on their sleeves and pride in their steps.",
    "The small crew sailed on, knowing the lookout would hold steady for the next tide.",
    "{hero} looked back once and saw the open window shining like a lantern for friends.",
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale storyworld about a historic shutter and friendship.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--historic-place", choices=HISTORIC_PLACES)
    ap.add_argument("--object-name", choices=OBJECTS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    place = args.place or rng.choice(PLACES)
    historic_place = args.historic_place or rng.choice(HISTORIC_PLACES)
    object_name = args.object_name or rng.choice(OBJECTS)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        hero=hero,
        friend=friend,
        place=place,
        object_name=object_name,
        historic_place=historic_place,
        problem=rng.choice(ARCS)["problem"],
        seed=None,
    )

def build_world(params: StoryParams) -> World:
    hero = Entity(name=params.hero, kind="hero")
    friend = Entity(name=params.friend, kind="friend")
    place = Entity(name=params.place, kind="place")
    shutter = Entity(name=params.object_name, kind="object")
    return World(params=params, hero=hero, friend=friend, place=place, shutter=shutter)

def choose_arc(params: StoryParams) -> dict:
    for arc in ARCS:
        if arc["problem"] == params.problem:
            return arc
    return ARCS[0]

def simulate(world: World) -> None:
    p = world.params
    arc = choose_arc(p)
    h = world.hero
    f = world.friend
    rng = random.Random(p.seed)
    h.memes["care"] = 1.0
    f.memes["helping"] = 1.0
    world.facts["historic_place"] = p.historic_place
    world.facts["object"] = p.object_name
    world.facts["problem"] = arc["problem"]

    opening = rng.choice(OPENINGS)
    world.say(f"{opening}. Near {p.historic_place}, {h.name} and {f.name} worked by {p.place}, where {p.object_name} had gone stubborn.")
    world.say(f"The trouble was simple and serious: {arc['problem']}. {arc['stake']}.")
    world.para()

    world.say(f"{h.name} frowned and said, “{arc['temptation'].capitalize()}.”")
    world.say(f"{f.name} shook their head and said, “Not yet. Let's solve it first.”")
    world.say("The two friends leaned closer, looked at the wood, and listened to the creak of the frame.")
    world.say(f"They noticed a clue: {arc['clue']}.")
    world.para()

    d1 = rng.choice(DIALOGUE_LINES).format(hero=h.name, friend=f.name)
    d2 = rng.choice([x for x in DIALOGUE_LINES if x != d1]).format(hero=h.name, friend=f.name)
    world.say(d1)
    world.say(d2)
    world.say(f"That back-and-forth changed the plan. {arc['action']}.")
    world.say(f"Then came the surprise: {arc['twist']}.")
    world.para()

    world.say(f"Because they had shared the work, the fix held. {arc['sharing']}.")
    world.say(f"{h.name} learned that {arc['lesson']}.")
    world.say(f"{rng.choice(CLOSINGS).format(hero=h.name, friend=f.name)} {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["ending"] = arc["ending"]

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = choose_arc(params)
    prompts = [
        f"Write a pirate tale about {params.hero} and {params.friend} solving a shutter problem near a historic house.",
        f"Tell a child-friendly story where friendship and problem solving fix {params.object_name}.",
        f"Make the ending show how the old shutter becomes useful again.",
    ]
    story_qa = [
        QAItem(question=f"What problem did {params.hero} and {params.friend} face?", answer=f"They faced a problem with {params.object_name}: {arc['problem']}."),
        QAItem(question=f"Why was the problem important?", answer=f"It was important because {arc['stake']}."),
        QAItem(question="What clue helped them solve it?", answer=f"They noticed that {arc['clue']}."),
        QAItem(question="What did the friends do together?", answer=f"They worked together and {arc['action'].lower()}."),
        QAItem(question="What changed by the end of the story?", answer=f"By the end, {arc['ending']}"),
    ]
    world_qa = [
        QAItem(question="What is friendship?", answer="Friendship means caring about someone and helping each other."),
        QAItem(question="What is problem solving?", answer="Problem solving means looking carefully and trying ideas until you find a good fix."),
        QAItem(question="What is a shutter?", answer="A shutter is a board or panel that opens and closes over a window."),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.place, world.shutter]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:12} ({ent.kind:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

ASP_RULES = r"""
#show valid/1.
valid(story).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("domain", "pirate_tale"),
        asp.fact("feature", "friendship"),
        asp.fact("feature", "problem_solving"),
        asp.fact("seed_word", "historic"),
        asp.fact("seed_word", "shutter"),
    ])

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1

CURATED = [
    StoryParams(hero="Mara", friend="Jules", place="the old harbor lane", object_name="the shutter", historic_place="the historic tide house", problem=ARCS[0]["problem"], seed=101),
    StoryParams(hero="Pip", friend="Risa", place="the cobbled dock street", object_name="the blue shutter", historic_place="the old captain's house", problem=ARCS[4]["problem"], seed=202),
    StoryParams(hero="Tessa", friend="Ned", place="the salt-bright pier road", object_name="the painted shutter", historic_place="the historic lantern shop", problem=ARCS[7]["problem"], seed=303),
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
