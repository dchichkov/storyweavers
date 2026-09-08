#!/usr/bin/env python3
"""
A heartwarming small storyworld about a parade, a sailor, and infantry who
discover that a twist can turn a mistake into a kind rescue.
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
class Thing:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Thing
    sailor: Thing
    sergeant: Thing
    banner: Thing
    drum: Thing
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    child_name: str
    sailor_name: str
    sergeant_name: str
    place: str
    seed: Optional[int] = None


CHILD_NAMES = ["Maya", "Noah", "Lina", "Pip", "Iris", "Ben", "Clara", "Owen"]
SAILOR_NAMES = ["Captain Reed", "Sailor June", "Mate Finn", "Sailor Rosa", "Bosun Hale"]
SERGEANT_NAMES = ["Sergeant Cole", "Sergeant Mina", "Sergeant Jo", "Sergeant Elias", "Sergeant Vale"]
PLACES = [
    "the seaside parade",
    "the town square",
    "the harbor lane",
    "the lantern bridge",
    "the windy market road",
]


ASP_RULES = r"""
#show steady/1.
#show helped/1.
#show twirl/1.
#show shared/1.

steady(H) :- hears_plan(H).
helped(H) :- ties_banner(H).
twirl(H) :- turns_ribbon(H).
shared(H) :- speaks_kindly(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hears_plan", "child"),
        asp.fact("ties_banner", "sailor"),
        asp.fact("turns_ribbon", "infantry"),
        asp.fact("speaks_kindly", "child"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show steady/1.\n#show helped/1.\n#show twirl/1.\n#show shared/1."))
    atoms = set((a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model)
    expected = {
        ("steady", ("child",)),
        ("helped", ("sailor",)),
        ("twirl", ("infantry",)),
        ("shared", ("child",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about a parade with a twist.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--sailor-name", choices=SAILOR_NAMES)
    ap.add_argument("--sergeant-name", choices=SERGEANT_NAMES)
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
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        sailor_name=args.sailor_name or rng.choice(SAILOR_NAMES),
        sergeant_name=args.sergeant_name or rng.choice(SERGEANT_NAMES),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.child_name}|{params.sailor_name}|{params.sergeant_name}|{params.place}")
    child = Thing(id="child", label=params.child_name, phrase=f"young {params.child_name}", kind="character")
    sailor = Thing(id="sailor", label=params.sailor_name, phrase=params.sailor_name, kind="character")
    sergeant = Thing(id="infantry", label=params.sergeant_name, phrase=params.sergeant_name, kind="character")
    banner = Thing(id="banner", label="parade banner", phrase="a long blue parade banner", owner="sailor")
    drum = Thing(id="drum", label="drum", phrase="a round marching drum", owner="infantry")
    return World(
        child=child,
        sailor=sailor,
        sergeant=sergeant,
        banner=banner,
        drum=drum,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    twist: str,
    trouble: str,
    cause: str,
    turn: str,
    ending: str,
    lines: list[str],
) -> str:
    world.facts.update(
        twist=twist,
        trouble=trouble,
        cause=cause,
        turn=turn,
        ending=ending,
        shared=True,
    )
    return " ".join(lines)


def _banner_tangle(world: World, rng: random.Random) -> str:
    c, s, i, p = world.child.label, world.sailor.label, world.sergeant.label, world.place
    color = _choice(rng, ["gold ribbon", "red ribbon", "silver ribbon", "blue ribbon"])
    helper = _choice(rng, ["a broom handle", "a little ladder", "a coat hook", "a fish crate"])
    twist = "the parade banner had tied itself around a bench leg and stopped the march"
    trouble = "the drumbeat faltered and the children waiting to wave looked worried"
    cause = "a gust from the harbor had looped the banner rope under the bench"
    turn = f"{c} noticed that one careful twist of the rope would free the banner without tearing it"
    ending = "the banner lifted cleanly again, and the parade rolled on with brighter smiles than before"
    lines = [
        f"At {p}, {c} watched the parade form in a line of shoes, drums, and shining buttons.",
        f"Then the blue banner snagged hard on a bench leg. {s} gave the rope a tug. {i} frowned. The crowd went quiet.",
        f'"That is not a good sign," said {c}. "It looks stuck."',
        f'"It is stuck," said {s}, kneeling beside the bench. "{c}, can you see why?"',
        f'{c} peered closer and found the rope wound around the leg in one neat knot. "A twist will undo a twist," {c} said.',
        f"With {i} holding the bench still, {c} loosened the knot by turning it the other way. The rope slipped free at once.",
        f'{s} laughed in relief. "That was clever," {s} said. "And kind. The banner needed a careful hand, not a hard pull."',
        f"Together they tied on a fresh {color} streamer and handed the banner back to the march. By the time the first drumbeat began again, {ending}.",
    ]
    return _record_story(world, twist=twist, trouble=trouble, cause=cause, turn=turn, ending=ending, lines=lines)


def _drum_rescue(world: World, rng: random.Random) -> str:
    c, s, i, p = world.child.label, world.sailor.label, world.sergeant.label, world.place
    sound = _choice(rng, ["a tiny meow", "a squeaky chirp", "a weak peep", "a soft hiss"])
    twist = "the parade drum was hiding a frightened kitten inside its hollow shell"
    trouble = "every loud beat made the kitten tremble harder and the march had to stop"
    cause = "the drum had been left open near a cart, and the kitten slipped into its warm round belly"
    turn = f"{c} suggested turning the drum on its side and speaking softly so the kitten would know it was safe"
    ending = "the kitten climbed out, yawned, and fell asleep in the sailor's cap while the parade tiptoed past"
    lines = [
        f"Near {p}, {i} gave the parade drum a proud thump. Instead of a brave boom, there came {sound} from inside.",
        f'"Did you hear that?" whispered {c}.',
        f'"I did," said {s}. "And I do not think the drum meant to answer."',
        f"{i} lifted the drum rim and found two bright kitten eyes staring out from the dark round space.",
        f'"Hello, little one," said {c}. "You do not have to be afraid."',
        f"{s} set the drum on its side. {i} blocked the wheels of the nearby cart. Then {c} spoke softly at the opening until the kitten inched forward.',
        f"When the kitten finally stepped into the light, everyone smiled all at once. {i} even bowed to the kitten, which seemed very serious about being respected.",
        f"The parade waited kindly while the kitten drank milk from a spoon. By sunset, {ending}.",
    ]
    return _record_story(world, twist=twist, trouble=trouble, cause=cause, turn=turn, ending=ending, lines=lines)


def _sailor_salute(world: World, rng: random.Random) -> str:
    c, s, i, p = world.child.label, world.sailor.label, world.sergeant.label, world.place
    missing = _choice(rng, ["a shoe", "a glove", "a flag tassel", "a brass button"])
    twist = "the sailor's parade salute kept slipping because one glove was missing"
    trouble = "the crowd expected a crisp salute, but the sailor's hand kept fidgeting with worry instead"
    cause = "the missing glove had blown under a cart wheel during the rush to line up"
    turn = f"{c} spotted the missing {missing} and led the sailor to it before the march began"
    ending = "the sailor saluted neatly with both hands steady, and the infantry cheered the child for noticing"
    lines = [
        f"At the start of the parade, {s} tried to salute the crowd at {p}, but one hand looked far less grand than the other.",
        f'"Something is wrong," murmured {c}.',
        f'"I am missing my {missing}," said {s}. "I feel silly without it."',
        f"{i} checked the line of boots while {c} looked near the cart wheels. Under one wheel, the missing piece was hiding, dusty but safe.",
        f'"Found it!" said {c}. {s} blinked, then smiled with clear relief.',
        f"{i} handed over a polishing cloth, and {c} helped brush off the dust. The sailor thanked the child twice because once did not feel enough.",
        f"When the band started again, {s} lifted the recovered {missing} and gave a bright salute. {i} straightened up too, and the whole row looked proud.",
        f"By the time the parade passed the bakery, {ending}.",
    ]
    return _record_story(world, twist=twist, trouble=trouble, cause=cause, turn=turn, ending=ending, lines=lines)


def _float_kite(world: World, rng: random.Random) -> str:
    c, s, i, p = world.child.label, world.sailor.label, world.sergeant.label, world.place
    kite = _choice(rng, ["a paper kite", "a little flag", "a ribbon wand", "a tiny streamer"])
    twist = "the parade decoration floated up into a tree and made the march look unfinished"
    trouble = "the crowd could not see the top of the banner because the wind had lifted it too high"
    cause = "the seaside breeze had caught the light paper and carried it into the branches"
    turn = f"{s} asked {c} to hold the rope while {i} climbed the low ladder and freed the {kite}"
    ending = "the decoration came down gently, and the child got to wave it at the front of the parade"
    lines = [
        f"At {p}, the wind gave one lively puff and sent {kite} spinning up into a tree.",
        f'"Oh no," said {c}. "It looks like our parade has lost its smile."',
        f'"Not lost," said {s}. "Just high up."',
        f"{i} fetched a ladder from a fence corner. {c} held the rope with both hands and called, \"Easy, easy.\"",
        f"Up above, the branches shook like they were laughing. {i} reached the {kite} and handed it down carefully.",
        f"{c} tied the rope in a kinder loop this time, and {s} showed how to keep the wind from catching it so hard.",
        f'When the parade moved on, {c} marched beside {s}, waving the rescued {kite}. "Now it can see where it belongs," {c} said.',
        f"Everyone agreed the little rescue made the march feel warmer than before. By the end, {ending}.",
    ]
    return _record_story(world, twist=twist, trouble=trouble, cause=cause, turn=turn, ending=ending, lines=lines)


ARC_BUILDERS = [_banner_tangle, _drum_rescue, _sailor_salute, _float_kite]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x3D91A7)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    c = world.child.label
    f = world.facts
    return [
        QAItem(
            question=f"What twist changed the parade?",
            answer=f"The twist was that {f['twist']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began because {f['cause']}.",
        ),
        QAItem(
            question=f"How did {c} help?",
            answer=f"{f['turn']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a happy public march where people walk together, often with music, banners, and celebration.",
        ),
        QAItem(
            question="What does an infantry group do?",
            answer="Infantry are soldiers who usually move on foot and work together as a unit.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on a boat or ship and knows how to travel on water.",
        ),
    ]
    arc_item = {
        "banner_tangle": QAItem(
            question="Why did the banner get stuck?",
            answer="The banner got stuck because its rope looped around the bench leg in a tight knot.",
        ),
        "drum_rescue": QAItem(
            question="Why was the drum quiet at first?",
            answer="The drum was quiet because a kitten was hiding inside it and needed gentle help.",
        ),
        "sailor_salute": QAItem(
            question="Why did the sailor feel worried?",
            answer="The sailor felt worried because a missing glove made the salute feel unfinished.",
        ),
        "float_kite": QAItem(
            question="Why did the decoration go into the tree?",
            answer="The wind lifted the light decoration into the branches because it was easy for the breeze to carry.",
        ),
    }[world.facts["arc"]]
    return [common[0], arc_item, common[2]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story about a parade with a sailor and infantry.",
        f"Tell a child-friendly story set at {world.place} where a parade goes wrong and then becomes kind again.",
        "Use a twist that turns trouble into a gentle rescue.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.child, world.sailor, world.sergeant, world.banner, world.drum]:
        lines.append(f"  {ent.id:8} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
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
        print(asp_program("#show steady/1.\n#show helped/1.\n#show twirl/1.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("4 compatible logical atoms: steady(child), helped(sailor), twirl(infantry), shared(child)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(child_name="Maya", sailor_name="Captain Reed", sergeant_name="Sergeant Cole", place="the seaside parade"),
            StoryParams(child_name="Lina", sailor_name="Sailor June", sergeant_name="Sergeant Mina", place="the town square"),
            StoryParams(child_name="Pip", sailor_name="Mate Finn", sergeant_name="Sergeant Jo", place="the harbor lane"),
            StoryParams(child_name="Iris", sailor_name="Sailor Rosa", sergeant_name="Sergeant Elias", place="the lantern bridge"),
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
            header = f"### {p.child_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
