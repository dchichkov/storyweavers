#!/usr/bin/env python3
"""
A small pirate tale storyworld about friendship, problem solving, a historic shutter,
and the trouble that starts when a crew must rescue a harbor from a broken routine.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    friend: Item
    elder: Item
    shutter: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    friend_name: str
    elder_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Mina", "Jory", "Tessa", "Pip", "Arlo", "Nori", "Lina", "Ben"]
FRIENDS = ["Bo", "Sailor June", "Ned", "Kia", "Rook", "Mara", "Drew", "Wren"]
ELDERS = ["Captain Salt", "Old Finn", "Aunt Pearl", "Harbor Mayor", "Mate Iris"]
PLACES = ["the old harbor", "the moonlit quay", "the tide-wharf", "the brig docks", "the cliffside cove"]


ASP_RULES = r"""
#show friends/2.
#show solve/1.
#show restored/1.

friends(H,F) :- help(H,F).
solve(H) :- fixes_shutter(H).
restored(P) :- shutter_repaired(P).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("help", "hero", "friend"),
        asp.fact("fixes_shutter", "hero"),
        asp.fact("shutter_repaired", "harbor"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show friends/2.\n#show solve/1.\n#show restored/1."))
    atoms = {(a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model}
    expected = {
        ("friends", ("hero", "friend")),
        ("solve", ("hero",)),
        ("restored", ("harbor",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about friendship and problem solving.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIENDS)
    ap.add_argument("--elder-name", choices=ELDERS)
    ap.add_argument("--place", choices=PLACES)
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
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        elder_name=args.elder_name or rng.choice(ELDERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(id="hero", label=params.name, phrase=f"young sailor {params.name}", kind="character")
    friend = Item(id="friend", label=params.friend_name, phrase=params.friend_name, kind="character")
    elder = Item(id="elder", label=params.elder_name, phrase=params.elder_name, kind="character")
    shutter = Item(
        id="shutter",
        label="historic shutter",
        phrase="a creaky historic shutter with sea-salt paint and brass hinges",
        kind="object",
        owner="harbor",
        meters={"height": 1.2, "width": 0.8},
        memes={"pride": 0.7, "wobble": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.friend_name}|{params.elder_name}|{params.place}")
    return World(hero=hero, friend=friend, elder=elder, shutter=shutter, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    arc: str,
    discovery: str,
    trouble: str,
    cause: str,
    refrain: str,
    resolution: str,
    ending: str,
    humor: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        shared=True,
    )
    return " ".join(lines)


def _storm_arc(world: World, rng: random.Random) -> str:
    h, f, e, p = world.hero.label, world.friend.label, world.elder.label, world.place
    cargo = _choice(rng, ["fish crates", "rope coils", "lantern oil", "pepper sacks"])
    discovery = "the historic shutter was holding shut the wind-battered lighthouse window"
    trouble = f"a storm began to slam spray through the open crack and soaked {cargo}"
    cause = "the shutter's latch had rusted loose, so every gust shoved it open and shut"
    refrain = "Hold fast, old shutter"
    resolution = f"{h} and {f} tied a spare line around the shutter while {e} fetched oil for the latch"
    ending = "the repaired shutter clicked closed, and the lighthouse beam turned steady over the black water"
    humor = f"the gulls tried to steal the dripping {cargo} while the crew chased the wind"
    lines = [
        f"At {p}, {h} found the old historic shutter trembling on the lighthouse window like a sleepy barn door.",
        f"Then the storm rolled in. Wham! The shutter banged open, and sea spray leaped across the room onto {cargo}.",
        f'"Hold fast, old shutter!" called {h}. {f} answered, "Aye, and keep your hinges out of the soup!"',
        f"{e} pointed to the rusty latch and said, \"The wind is winning because the latch has given up.\"",
        f"That made {h} curious. The child tested the latch, the hinges, and the frame, and learned the shutter was not haunted at all; it was merely loose.",
        f"Together, {h} and {f} looped a spare line through the handle and braced the wood while {e} oiled the rusted catch.",
        f"At last the storm could not bully the window anymore. The shutter held, the room dried, and the lighthouse beam swept on like a brave golden sword.",
        f"By midnight, {ending}. {h} and {f} clapped hands with {e}, proud as pirates with a rescued map.",
    ]
    return _record_story(
        world,
        arc="storm",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        lines=lines,
    )


def _signal_arc(world: World, rng: random.Random) -> str:
    h, f, e, p = world.hero.label, world.friend.label, world.elder.label, world.place
    ship = _choice(rng, ["the eel-skipper", "the paint-boat", "the oyster sloop", "the red brig"])
    message = _choice(rng, ["a lost crew", "a crate of medicine", "a birthday feast", "a ferry full of lanterns"])
    discovery = "the historic shutter was being used as a signal board by the harbor watch"
    trouble = f"{ship} could not tell the right dock and nearly missed {message}"
    cause = "the shutter's painted slats had become crooked, so the daytime signal looked wrong"
    refrain = "Straighten the shutter"
    resolution = f"{h} and {f} measured the slats against the dock ropes while {e} read the old signal chart"
    ending = "the corrected shutter flashed the proper pattern, and the ship glided safely to the pier"
    humor = f"the watchman had been waving a mop at sea, which was not the usual language of docks"
    lines = [
        f"One bright morning at {p}, {h} spotted the historic shutter on the signal tower and saluted it like a ship's captain.",
        f"Far off, {ship} drifted in, but the crew kept turning in circles because they could not see the mark for {message}.",
        f'"Straighten the shutter!" shouted {h}. {f} grinned and said, "Aye, and maybe give it a taller hat."',
        f"{e} unfolded an old chart and explained that the slats should match the tide ropes, not the seagull nests.",
        f"Curious, {h} checked the angles one by one. The child found the middle slat leaning sideways, which had muddled the signal.",
        f"With a small hammer and a careful hand, {h} and {f} set the slats straight while {e} watched the pattern.",
        f"When the shutter flashed again, the ship answered with a happy horn blast and steered cleanly to the pier.",
        f"By sunset, {ending}. Even the watchman admitted the mop was better for floors than for maritime language.",
    ]
    return _record_story(
        world,
        arc="signal",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        lines=lines,
    )


def _hide_arc(world: World, rng: random.Random) -> str:
    h, f, e, p = world.hero.label, world.friend.label, world.elder.label, world.place
    item = _choice(rng, ["a brass compass", "a sack of clams", "a silver key", "three pears"])
    discovery = "the historic shutter was hiding a narrow cubby in the wall"
    trouble = f"{item} had slipped inside the cubby, and the crew could not reach it without opening the wrong panel"
    cause = "the shutter covered the only latch, so the hidden space stayed sealed"
    refrain = "Mind the shutter"
    resolution = f"{h} listened for the hollow sound, {f} held a lantern, and {e} guided a thin hook to lift the latch"
    ending = f"the cubby opened at last, and {item} came out safe while the shutter swung back to guard the wall"
    humor = f"the crew had been tapping the wrong board so long that the wall seemed to be playing a joke"
    lines = [
        f"At the end of a salty alley in {p}, {h} found the historic shutter and wondered why it looked puffed up like a proud chest.",
        f"{f} knocked on the boards. Thunk. Thunk. One spot sounded hollow, and then the wall gave a tiny squeak.",
        f'"Mind the shutter," said {e}. "Old things sometimes hide new tricks."',
        f"{h} bent close and asked, \"What are you hiding?\" The shutter did not answer, but the hollow sound did.",
        f"Curious now, {h} and {f} searched along the frame until they found the latch tucked under a flake of blue paint.",
        f"With {e}'s hook and the lantern light, they lifted the latch and reached the little cubby without breaking the old wood.",
        f"Inside was {item}, exactly where it had rolled when the sea shook the harbor office.",
        f"By evening, {ending}. {h} promised to listen before knocking on any mysterious wall again.",
    ]
    return _record_story(
        world,
        arc="hide",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        lines=lines,
    )


def _mouse_arc(world: World, rng: random.Random) -> str:
    h, f, e, p = world.hero.label, world.friend.label, world.elder.label, world.place
    cheese = _choice(rng, ["a wedge of cheddar", "a crumbly biscuit", "a rind of blue cheese", "a heel of bread"])
    discovery = "the historic shutter had been propped open by a mouse-sized wooden peg"
    trouble = f"the peg slipped, the shutter slammed, and {cheese} tumbled into the bilge"
    cause = "the peg was too smooth for the damp wood, so it kept sliding free"
    refrain = "Tiny peg, big job"
    resolution = f"{h} carved a rougher peg while {f} held the shutter and {e} tested the fit"
    ending = "the new peg held the shutter steady, and the saved cheese was shared on deck with laughing thanks"
    humor = f"the mouse watched from a barrel as if it had designed the whole problem on purpose"
    lines = [
        f"Near {p}, {h} heard a pop and saw the historic shutter drop shut with a bang that made the deck jump.",
        f"Down below, {cheese} rolled toward the bilge like a runaway treasure. {f} cried, \"Not the snack chest!\"",
        f'"Tiny peg, big job," muttered {h}, pulling the wooden stopper from the frame.',
        f"{e} said, \"That peg is smooth from weather and salt. Smooth wood slips.\"",
        f"Curious about the answer, {h} rubbed the peg on rough stone, then tried it in the hole. It still skated away.",
        f"So {h} carved a new peg with a knife, making it a little rough and a little thicker.",
        f"Together, {h}, {f}, and {e} fitted it under the shutter. This time the wood held, and the door stayed open to the breeze.",
        f"By supper, {ending}. The mouse got the smallest crumb, which seemed fair for such a tiny job.",
    ]
    return _record_story(
        world,
        arc="mouse",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        lines=lines,
    )


def _fog_arc(world: World, rng: random.Random) -> str:
    h, f, e, p = world.hero.label, world.friend.label, world.elder.label, world.place
    lantern = _choice(rng, ["the mast lantern", "the harbor lamp", "the captain's lantern", "the dock torch"])
    discovery = "the historic shutter was the only thing that could block a blinking light in the fog"
    trouble = f"a foghorn kept confusing ships because {lantern} flashed through the gap at the wrong moment"
    cause = "the shutter was warped, so it could not close fully against the wind"
    refrain = "Shut the shutter"
    resolution = f"{h} and {f} wedged a board under the bent edge while {e} hammered the hinge flat"
    ending = "the light blinked in a clean pattern, the foghorn calmed, and the harbor breathed easier"
    humor = f"one ship had followed the wrong blink for so long that it arrived carrying extra biscuits for nobody"
    lines = [
        f"On a foggy night at {p}, {h} saw the historic shutter rocking beside {lantern} like a sleepy pirate's eyelid.",
        f"The fog thickened. The light blinked crookedly through the crack, and ships below turned the wrong way with every flash.",
        f'"Shut the shutter!" called {f}. {h} answered, "Aye, but first we must learn why it won't shut."',
        f"{e} traced the warped edge with a finger and said, \"The wood has bent in the damp.\"",
        f"Curious, {h} tested the hinge, the latch, and the bottom rail, and discovered the lower corner was too high to seal the gap.",
        f"With a board, a hammer, and two strong shoulders, {h} and {f} pressed the edge down while {e} fixed the hinge.",
        f"At last the shutter closed flat. The lantern blinked once, twice, three safe times through the fog.",
        f"By dawn, {ending}. The harbor kept its biscuits, and the ships found the pier without any more wandering.",
    ]
    return _record_story(
        world,
        arc="fog",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        lines=lines,
    )


ARC_BUILDERS = [_storm_arc, _signal_arc, _hide_arc, _mouse_arc, _fog_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4B2F19)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the shutter?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble in this story?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} and {f} solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="What did the repeated spoken line do in the story?",
            answer=f'The repeated line "{facts["refrain"]}" showed urgency and helped the characters focus on fixing the problem.',
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a close bond between people who care about each other and help one another.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving is figuring out why something is wrong and choosing a good way to fix it.",
        ),
        QAItem(
            question="Why can an old object matter in a story?",
            answer="An old object can matter because it may hide history, a useful job, or a clue to the problem.",
        ),
    ]
    arc_item = {
        "storm": QAItem("Why can salt and rain damage a shutter?", "Salt and rain can make wood swell and rust metal parts, which can keep a shutter from moving well."),
        "signal": QAItem("Why do signal shutters need clear alignment?", "Signal shutters need clear alignment so their patterns can be read correctly from far away."),
        "hide": QAItem("Why might a wall have a hidden cubby?", "Old walls sometimes have hidden cubbies for storage, tools, or small valuables."),
        "mouse": QAItem("Why should a peg fit tightly in wood?", "A tight fit helps the peg stay in place so the object it supports does not slip or fall."),
        "fog": QAItem("Why do ships use lights in fog?", "Ships use lights in fog so they can find safe routes and avoid getting lost."),
    }[world.facts["arc"]]
    return [common[0], arc_item, common[1]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a pirate tale for young children about friendship and a historic shutter.",
        f"Tell a swashbuckling story set at {world.place} where friends must solve a problem with an old shutter.",
        "Create a child-friendly pirate adventure with a clear problem, a clever fix, and a warm ending.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.elder, world.shutter]:
        lines.append(f"  {ent.id:7} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  place={world.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show friends/2.\n#show solve/1.\n#show restored/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: friends(hero,friend), solve(hero), restored(harbor)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", friend_name="Bo", elder_name="Captain Salt", place="the old harbor"),
            StoryParams(name="Pip", friend_name="Kia", elder_name="Old Finn", place="the moonlit quay"),
            StoryParams(name="Tessa", friend_name="Wren", elder_name="Aunt Pearl", place="the tide-wharf"),
            StoryParams(name="Arlo", friend_name="Rook", elder_name="Harbor Mayor", place="the cliffside cove"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
