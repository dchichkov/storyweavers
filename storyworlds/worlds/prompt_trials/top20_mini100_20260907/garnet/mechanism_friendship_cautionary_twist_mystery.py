#!/usr/bin/env python3
"""
A small mystery storyworld about friendship, caution, and a puzzling mechanism
that turns an ordinary day into a careful little investigation.
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
    mechanism: Item
    setting: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    hero_name: str
    friend_name: str
    elder_name: str
    setting: str
    seed: Optional[int] = None


HERO_NAMES = ["Mina", "Eli", "Pia", "Jude", "Nora", "Sami", "Iris", "Ben"]
FRIEND_NAMES = ["Theo", "Lina", "Omar", "Zoe", "Mara", "Finn", "Ada", "Noah"]
ELDER_NAMES = ["Mrs. Vale", "Mr. Bram", "Aunt Kora", "Old June", "Grandpa Ren"]
SETTINGS = [
    "the quiet museum hall",
    "the lantern-lit workshop",
    "the old garden shed",
    "the small station platform",
    "the attic room above the bakery",
]


ASP_RULES = r"""
#show curious/1.
#show careful/1.
#show trusted/1.
#show solved/1.
#show warned/1.

curious(H) :- notices_mechanism(H).
careful(H) :- hears_warning(H).
trusted(H) :- shares_clue(H).
solved(H) :- reveals_source(H).
warned(H) :- stops_in_time(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("notices_mechanism", "hero"),
        asp.fact("hears_warning", "hero"),
        asp.fact("shares_clue", "hero"),
        asp.fact("reveals_source", "hero"),
        asp.fact("stops_in_time", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show curious/1.\n#show careful/1.\n#show trusted/1.\n#show solved/1.\n#show warned/1."))
    atoms = {(a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model}
    expected = {
        ("curious", ("hero",)),
        ("careful", ("hero",)),
        ("trusted", ("hero",)),
        ("solved", ("hero",)),
        ("warned", ("hero",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about friendship and a strange mechanism.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--elder-name", choices=ELDER_NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
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
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        elder_name=args.elder_name or rng.choice(ELDER_NAMES),
        setting=args.setting or rng.choice(SETTINGS),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(id="hero", label=params.hero_name, phrase=f"young {params.hero_name}", kind="character")
    friend = Item(id="friend", label=params.friend_name, phrase=f"friend {params.friend_name}", kind="character")
    elder = Item(id="elder", label=params.elder_name, phrase=params.elder_name, kind="character")
    mechanism = Item(
        id="mechanism",
        label="mechanism",
        phrase="a small brass mechanism with a latch, a wheel, and a spring",
        kind="thing",
        owner="",
        meters={"width": 0.3, "height": 0.2},
        memes={"mystery": 0.8},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.hero_name}|{params.friend_name}|{params.elder_name}|{params.setting}")
    return World(hero=hero, friend=friend, elder=elder, mechanism=mechanism, setting=params.setting, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    clue: str,
    warning: str,
    twist: str,
    resolution: str,
    ending: str,
    dialogue: str,
    lines: list[str],
) -> str:
    world.facts.update(
        clue=clue,
        warning=warning,
        twist=twist,
        resolution=resolution,
        ending=ending,
        dialogue=dialogue,
        solved=True,
        warned=True,
        careful=True,
        trusted=True,
        curious=True,
    )
    return " ".join(lines)


def _museum_arc(world: World, rng: random.Random) -> str:
    h, f, e, s = world.hero.label, world.friend.label, world.elder.label, world.setting
    exhibit = _choice(rng, ["a glass display case", "a velvet rope", "a brass plaque", "a painted floor tile"])
    sound = _choice(rng, ["tick", "click", "whirr", "tap"])
    clue = f"{sound}ing came from behind a narrow panel"
    warning = "the mechanism looked harmless, but it moved whenever the floorboards creaked"
    twist = "the missing museum key was not stolen; it was tucked into the mechanism's spring as part of an old puzzle lock"
    resolution = f"{h} and {f} asked {e} for a flashlight, then gently opened the panel and slid the key free before any part jammed"
    ending = "the key hung safely on its hook, and the quiet hall no longer answered with secret little clicks"
    dialogue = f'"Do you hear that?" asked {h}. "{sound}?" whispered {f}. "{Yes, but do not touch it yet," said {e}, "first we look."'
    lines = [
        f"At {s}, {h} noticed a tiny {sound} from behind {exhibit}.",
        f"{f} leaned closer. {h} pulled back at once. \"Wait,\" said {h}, \"something in there is working.\"",
        f"The two friends listened together, and the sound changed each time someone stepped near the wall.",
        f'"Do you hear that?" asked {h}. "{sound}?" whispered {f}. "{e} said, "Yes, but do not touch it yet. First we look."',
        f"That warning mattered. The mechanism was old, and every bump made its spring twitch like a nervous cat.",
        f"{h} found a note under the plaque: \"Turn the wheel only after the hall is empty.\"",
        f"The note was the twist. The missing museum key was not stolen; it was tucked into the mechanism's spring as part of an old puzzle lock.",
        f"With a flashlight from {e}, the friends opened the panel slowly and eased the key out before anything could jam.",
        f"By the end of the evening, {ending}. {h} and {f} smiled at each other, glad they had trusted caution before curiosity became trouble.",
    ]
    return _record_story(world, clue=clue, warning=warning, twist=twist, resolution=resolution, ending=ending, dialogue=dialogue, lines=lines)


def _workshop_arc(world: World, rng: random.Random) -> str:
    h, f, e, s = world.hero.label, world.friend.label, world.elder.label, world.setting
    tool = _choice(rng, ["a spool of red thread", "a chipped screwdriver", "a tin wrench", "a wax pencil"])
    clue = "a small track of shiny dust led under the workbench"
    warning = "the mechanism's spring was wound too tight and could snap shut if grabbed fast"
    twist = "the strange missing bell was never missing at all; it had been hidden inside the mechanism to keep it from ringing in the wind"
    resolution = f"{h} held the light, {f} turned the release slowly, and {e} used {tool} to guide the bell out without jolting the spring"
    ending = "when the bell finally came free, it made one soft chime and then rested like it had been waiting for a friend"
    dialogue = f'"Let me help," said {f}. "{Not yet," said {h}, "the spring is listening." "{Good," said {e}, "then we will be patient."'
    lines = [
        f"In {s}, {h} spotted a trail of shiny dust under the workbench.",
        f"{f} followed it to a small brass mechanism with a wheel that would not stop trembling.",
        f'"Let me help," said {f}. "{Not yet," said {h}, "the spring is listening." "{Good," said {e}, "then we will be patient."',
        f"The warning was wise. The mechanism's spring was wound too tight and could snap shut if grabbed fast.",
        f"{h} became curious about the dust, and that clue pointed to the hidden bell inside the casing.",
        f"The twist made the room go still: the bell was never missing at all; it had been hidden inside the mechanism to keep it from ringing in the wind.",
        f"Together, the friends moved slowly. {h} held the light, {f} turned the release, and {e} used {tool} to guide the bell free.",
        f"At last, {resolution}.",
        f"By morning, {ending}.",
    ]
    return _record_story(world, clue=clue, warning=warning, twist=twist, resolution=resolution, ending=ending, dialogue=dialogue, lines=lines)


def _garden_arc(world: World, rng: random.Random) -> str:
    h, f, e, s = world.hero.label, world.friend.label, world.elder.label, world.setting
    plant = _choice(rng, ["the bean trellis", "the rose pot", "the seed drawer", "the watering can shelf"])
    clue = f"a thin ribbon tied to the mechanism pointed toward {plant}"
    warning = "the latch could pinch a finger if it snapped back"
    twist = "the supposed secret box held only a note saying the garden gate needed a friend to hold it open"
    resolution = f"{h} and {f} used two hands on the latch while {e} read the note aloud and showed them the safer way to open it"
    ending = "the gate stayed propped open with a wooden wedge, and the mystery became a simple, useful lesson"
    dialogue = f'"Should we open it?" asked {f}. "{Carefully," said {h}. "{Exactly," said {e}, "mysteries can bite if rushed."'
    lines = [
        f"Near {s}, {h} noticed a ribbon tied around a small mechanism beside {plant}.",
        f"{f} wanted to tug it right away, but {h} put out a hand and asked {e} to look first.",
        f'"Should we open it?" asked {f}. "{Carefully," said {h}. "{Exactly," said {e}, "mysteries can bite if rushed."',
        f"The warning was real. The latch could pinch a finger if it snapped back.",
        f"{h} studied the ribbon and found a clue in the knot: someone had tied it as a marker, not a trap.",
        f"The twist was gentle but surprising. The supposed secret box held only a note saying the garden gate needed a friend to hold it open.",
        f"Working together, {h} and {f} kept the latch steady while {e} read the note and showed them the safer way to open it.",
        f"In the end, {resolution}.",
        f"That evening, {ending}. {h} and {f} walked home side by side, proud that they had solved the puzzle without a scratch.",
    ]
    return _record_story(world, clue=clue, warning=warning, twist=twist, resolution=resolution, ending=ending, dialogue=dialogue, lines=lines)


def _station_arc(world: World, rng: random.Random) -> str:
    h, f, e, s = world.hero.label, world.friend.label, world.elder.label, world.setting
    train = _choice(rng, ["the noon train", "the mail cart", "the night trolley", "the early freight"])
    clue = "a brass tag on the mechanism matched a number painted on the platform bench"
    warning = "the mechanism was connected to the signal bell, so touching it could confuse the driver"
    twist = "the missing whistle was not lost; it had rolled into the mechanism and wedged there to stop a false alarm"
    resolution = f"{h} asked {f} to keep watch while {e} signaled the conductor, then they gently freed the whistle and reset the lever"
    ending = f"{train} arrived on time, and the fixed signal gave one clean note before the platform went calm again"
    dialogue = f'"Do not pull that," said {h}. "{Why not?" asked {f}. "{Because," said {e}, "some clues are attached to danger."'
    lines = [
        f"At {s}, {h} found a small mechanism under the bench, right beside a brass tag.",
        f"{f} counted the numbers on the tag and matched them to the platform marker while the wind pressed cold fingers through the railings.",
        f'"Do not pull that," said {h}. "{Why not?" asked {f}. "{Because," said {e}, "some clues are attached to danger."',
        f"The warning was serious. The mechanism was connected to the signal bell, so touching it could confuse the driver.",
        f"{h} heard one faint rattle and noticed the clue: the whistle had rolled into the mechanism and wedged there to stop a false alarm.",
        f"The twist explained the whole mystery. The whistle was not missing at all; it was hidden by the lever.",
        f"With {e} watching, {h} asked {f} to keep watch while the whistle was freed and the signal reset.",
        f"Before long, {resolution}.",
        f"At the end, {ending}. The friends walked away together, glad that caution had kept the station safe.",
    ]
    return _record_story(world, clue=clue, warning=warning, twist=twist, resolution=resolution, ending=ending, dialogue=dialogue, lines=lines)


def _attic_arc(world: World, rng: random.Random) -> str:
    h, f, e, s = world.hero.label, world.friend.label, world.elder.label, world.setting
    object_name = _choice(rng, ["a cookie tin", "an old music box", "a folded map", "a wooden bird cage"])
    clue = f"the mechanism clicked each time moonlight touched {object_name}"
    warning = "the attic floorboards were weak near the beam, so stepping too fast could send dust and boxes sliding"
    twist = "the supposed ghost was only a loose latch opening and closing with the night breeze"
    resolution = f"{h} and {f} followed the clicks, then asked {e} to hold the lantern while they tied the latch with twine"
    ending = "the attic grew still, and the moonlight looked peaceful on the tied-down latch and the sleepy boxes"
    dialogue = f'"I heard it again," said {f}. "{Then we go slow," said {h}. "{Slow is smart," said {e}, "and smart friends stay together."'
    lines = [
        f"In {s}, {h} heard a click from above an old beam and climbed one careful step at a time.",
        f"{f} followed, carrying the lantern low so the light would not wobble.",
        f'"I heard it again," said {f}. "{Then we go slow," said {h}. "{Slow is smart," said {e}, "and smart friends stay together."',
        f"The warning was important. The attic floorboards were weak near the beam, so stepping too fast could send dust and boxes sliding.",
        f"{h} studied the shadow and found a clue: the mechanism clicked whenever moonlight touched {object_name}.",
        f"The twist made them grin. The supposed ghost was only a loose latch opening and closing with the night breeze.",
        f"Together, the friends waited for {e} to lift the lantern high while they tied the latch with twine.",
        f"After that, {resolution}.",
        f"By midnight, {ending}. The mystery had a plain answer, but the careful teamwork made it feel like a victory.",
    ]
    return _record_story(world, clue=clue, warning=warning, twist=twist, resolution=resolution, ending=ending, dialogue=dialogue, lines=lines)


ARC_BUILDERS = [_museum_arc, _workshop_arc, _garden_arc, _station_arc, _attic_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x5A17C3)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    f = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} and {f} discover about the mechanism?",
            answer=f"They discovered that {facts['twist']}.",
        ),
        QAItem(
            question="What warning mattered most in the story?",
            answer=f"The warning was that {facts['warning']}.",
        ),
        QAItem(
            question=f"How did the friends solve the mystery safely?",
            answer=f"They solved it by moving carefully: {facts['resolution']}.",
        ),
        QAItem(
            question="How did friendship help the story?",
            answer=f"{h} and {f} listened to each other, shared clues, and asked {world.elder.label} for help when the mystery got tricky.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to do a job, like a latch, wheel, spring, or lever.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful because something could be risky or easy to break.",
        ),
        QAItem(
            question="What is a mystery in a story?",
            answer="A mystery is a puzzle with clues that characters have to notice, think about, and solve.",
        ),
    ]
    arc_item = {
        "museum": QAItem("Why can a hidden key matter in a mystery?", "A hidden key can unlock a locked place or reveal that a clue was part of a puzzle all along."),
        "workshop": QAItem("Why can a tight spring be risky?", "A tight spring can snap shut suddenly and pinch fingers or make a part jump out."),
        "garden": QAItem("Why should a latch be opened slowly?", "A latch can pinch or slam if it is rushed, so slow hands are safer."),
        "station": QAItem("Why should people be careful around signals?", "Signals help direct trains or vehicles, and touching them at the wrong time can cause confusion or danger."),
        "attic": QAItem("Why can old floorboards be dangerous?", "Old floorboards can be weak, so stepping too fast might cause someone to slip or make boxes fall."),
    }[world.facts["setting_key"] if "setting_key" in world.facts else ["museum", "workshop", "garden", "station", "attic"][world.seed % 5]]
    return [common[0], arc_item, common[1]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly mystery story about friends and a strange mechanism.",
        f"Write a cautious, twisty story set in {world.setting} where clues lead to a hidden truth.",
        "Tell a short story where friendship helps solve a mystery without rushing into danger.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.friend, world.elder, world.mechanism]:
        lines.append(f"  {ent.id:9} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  setting={world.setting}")
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


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show careful/1.\n#show trusted/1.\n#show solved/1.\n#show warned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("5 compatible logical atoms: curious(hero), careful(hero), trusted(hero), solved(hero), warned(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(hero_name="Mina", friend_name="Theo", elder_name="Mrs. Vale", setting="the quiet museum hall"),
            StoryParams(hero_name="Eli", friend_name="Lina", elder_name="Mr. Bram", setting="the lantern-lit workshop"),
            StoryParams(hero_name="Pia", friend_name="Omar", elder_name="Aunt Kora", setting="the old garden shed"),
            StoryParams(hero_name="Jude", friend_name="Zoe", elder_name="Old June", setting="the small station platform"),
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
            header = f"### {p.hero_name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
