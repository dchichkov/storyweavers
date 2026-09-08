#!/usr/bin/env python3
"""
Story world: a tiny pirate tale about a historic shutter, friendship, and problem solving.

On a small harbor island, two pirate friends find an old shutter from a historic house
stuck shut before a storm. They listen, test, and repair it together so the room can
breathe again, and the shutter becomes a proud part of the house's story.
"""

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

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Harbor:
    name: str
    dock: str = "the rickety dock"
    house: str = "the old cliff house"
    lane: str = "the narrow lane by the sea"
    sea: str = "the salt wind"

    def place(self) -> str:
        return f"{self.house} near {self.name}"


@dataclass
class StoryParams:
    harbor: str = "Gullwake Harbor"
    hero_name: str = "Pip"
    friend_name: str = "Mara"
    object_name: str = "historic shutter"
    trouble: str = "stuck closed"
    seed: Optional[int] = None


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HARBORS = {
    "Gullwake Harbor": Harbor(name="Gullwake Harbor"),
    "Crescent Quay": Harbor(name="Crescent Quay", dock="the mossy dock"),
    "Shellcoin Bay": Harbor(name="Shellcoin Bay", lane="the winding lane above the waves"),
}

HERO_NAMES = ["Pip", "Nell", "Bram", "Tessa", "Jory"]
FRIEND_NAMES = ["Mara", "Sail", "Lina", "Finn", "Kett"]

TROUBLES = {
    "stuck closed": {
        "premise": "The old shutter on the cliff house would not open, and the salty room inside had no fresh breeze.",
        "mistake": "{hero} pulled hard on the painted slats, but the shutter only groaned and stayed jammed.",
        "clue": "{friend} brushed away sand from the hinge and found a rusty nail caught in the wood.",
        "change": "They lifted the nail free, oiled the hinge, and tied a neat cord to keep the shutter from scraping the wall.",
        "result": "The shutter swung wide at last, and the room filled with cool sea air.",
        "lesson": "look for the real cause before you yank harder",
        "ending": "At sunset, the repaired shutter clicked open beside the lantern light, proud as a ship's flag.",
    },
    "rattling": {
        "premise": "The historic shutter banged in the wind and woke the sleeping crew in the house above the dock.",
        "mistake": "{hero} wedged a spoon under one corner, but the banging only grew louder.",
        "clue": "{friend} noticed the loose latch and the rope mark where the shutter had been beating the frame.",
        "change": "They tightened the latch, added a soft leather stop, and tied the shutter back before the next gust.",
        "result": "The shutter stayed quiet while the wind raced past the windows.",
        "lesson": "fix the part that is causing the trouble, not just the noise it makes",
        "ending": "The house slept easy while the shutter kept watch like a calm deck hand.",
    },
    "paint_peel": {
        "premise": "Salt air had peeled the shutter's blue paint, and flakes drifted onto the sill like tiny sea shells.",
        "mistake": "{hero} tried to scrub the flakes away at once, which only smeared the wood and made a bigger mess.",
        "clue": "{friend} found an old note in the house drawer that named the paint made for sea weather.",
        "change": "They sanded the rough spots, brushed on sealant, and painted the shutter in strong blue layers.",
        "result": "The shutter looked fresh again and could stand up to the salty wind.",
        "lesson": "choose a repair that fits the place where the object lives",
        "ending": "The blue shutter shone in the rain like a small ship's sail turned toward home.",
    },
    "crooked": {
        "premise": "The shutter hung crooked, and one lower corner scraped the sill every time it moved.",
        "mistake": "{hero} pushed the top harder, but that only bent the frame a little more.",
        "clue": "{friend} held a piece of string across the frame and showed that one hinge sat lower than the other.",
        "change": "They loosened the screws, lifted the hinge level, and packed the gap with a thin wooden wedge.",
        "result": "The shutter moved straight and smooth without scraping the sill.",
        "lesson": "measure first so the repair fits square and true",
        "ending": "The straight shutter opened with a gentle creak, like a sailor giving a quiet cheer.",
    },
    "locked": {
        "premise": "A rusted latch kept the historic shutter locked, and the room inside felt dark as a ship's hold.",
        "mistake": "{hero} shook the latch until it rattled, but the rust held fast.",
        "clue": "{friend} spotted a little key hanging beside an old map in the hall.",
        "change": "They used the key, cleared the rust with oil, and showed the latch how to turn again.",
        "result": "Light poured through the window, and the shutter opened with a proud click.",
        "lesson": "small tools and careful hands can solve a stubborn problem",
        "ending": "The old latch glimmered softly, no longer lost in the dark.",
    },
    "rope_snag": {
        "premise": "A bundle of rope from the fishing porch had snagged the shutter, pinning it halfway open.",
        "mistake": "{hero} tugged the rope bundle in a rush, and the knot only tightened.",
        "clue": "{friend} found the loose end and followed it back through the knot like a map.",
        "change": "They untied the rope loop by loop, then tied it neatly away from the window.",
        "result": "The shutter could open and close without catching the rope again.",
        "lesson": "untangle the knot instead of wrestling it",
        "ending": "With the ropes tucked away, the shutter moved free as a gull over the bay.",
    },
}

ASP_RULES = r"""
historic_shutter(S) :- shutter_name(S), historic_name(S).
friendship(H,F) :- hero_name(H), friend_name(F).
problem_solving(H) :- hero_name(H), solved_problem(H).
repaired(S) :- shutter_name(S), shutter_state(S, repaired).
open(S) :- shutter_name(S), shutter_state(S, open).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for harbor_name in HARBORS:
        lines.append(asp.fact("harbor_name", harbor_name))
    lines.append(asp.fact("historic_name", "historic_shutter"))
    lines.append(asp.fact("shutter_name", "historic_shutter"))
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("friend_name", "friend"))
    lines.append(asp.fact("shutter_state", "historic_shutter", "repaired"))
    lines.append(asp.fact("shutter_state", "historic_shutter", "open"))
    lines.append(asp.fact("solved_problem", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show historic_shutter/1.\n#show friendship/2.\n#show problem_solving/1.\n#show repaired/1.\n#show open/1."))
    atoms = {(sym.name, tuple(arg.string if arg.type == arg.type.String else arg.number if arg.type == arg.type.Number else arg.name for arg in sym.arguments)) for sym in model}
    want = {
        ("historic_shutter", ("historic_shutter",)),
        ("friendship", ("hero", "friend")),
        ("problem_solving", ("hero",)),
        ("repaired", ("historic_shutter",)),
        ("open", ("historic_shutter",)),
    }
    if atoms == want:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about a historic shutter, friendship, and problem solving.")
    ap.add_argument("--harbor", choices=HARBORS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--trouble", choices=TROUBLES)
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
    harbor = args.harbor or rng.choice(list(HARBORS))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    if friend == hero:
        raise StoryError("The friend should be different from the hero.")
    trouble = args.trouble or rng.choice(list(TROUBLES))
    return StoryParams(harbor=harbor, hero_name=hero, friend_name=friend, trouble=trouble)


def generate(params: StoryParams) -> StorySample:
    harbor = HARBORS[params.harbor]
    world = World(harbor)
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    trouble = TROUBLES[params.trouble]
    rng = random.Random(params.seed if params.seed is not None else f"{params.harbor}:{params.hero_name}:{params.friend_name}:{params.trouble}")

    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, type="pirate"))
    friend = world.add(Entity(id="friend", kind="character", label=params.friend_name, type="pirate"))
    shutter = world.add(Entity(
        id="shutter",
        kind="thing",
        label="historic shutter",
        phrase="the historic shutter with blue paint and iron hinges",
        type="shutter",
        owner=harbor.house,
        meters={"open": 0.0, "rust": 1.0, "sway": 0.0},
        memes={"pride": 1.0, "worry": 1.0},
    ))

    world.say(f"At {harbor.place()}, two pirate friends found {shutter.phrase}.")
    world.say(trouble["premise"])
    world.say(rng.choice([
        f'“That shutter has seen many storms,” {params.friend_name} said. “Let us help it tell one more good story.”',
        f'“Easy now,” {params.friend_name} said. “A good pirate solves a problem with a clear eye, not a louder tug.”',
        f'“We fix it together,” {params.hero_name} said, and {params.friend_name} nodded with a grin.',
        f'“First we watch, then we act,” {params.friend_name} said, tapping the shutter frame like a captain tapping a map.',
    ]))
    world.say(trouble["mistake"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(rng.choice([
        f"{params.friend_name} held the lantern closer so they could see the hinges and the paint.",
        f"They looked for what changed the shutter's motion instead of guessing at the whole house.",
        f"{params.hero_name} stopped tugging long enough to listen for the creak that came before the jam.",
        f"They checked the frame, the latch, and the sill, one piece at a time.",
        f"{params.friend_name} pointed to the narrow gap where wind and salt had gathered.",
        f"They spoke softly, like shipmates sharing one chart in a storm.",
    ]))
    world.say(trouble["clue"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(rng.choice([
        f'“There it is,” {params.hero_name} said. “We found the real trouble.”',
        f'“Aye,” {params.friend_name} replied. “Now the repair can fit the problem.”',
        f'“That is why friends make a fine crew,” {params.hero_name} said.',
        f'“Together we can fix what one quick pull could not,” {params.friend_name} said.',
    ]))

    shutter.meters["rust"] = 0.0
    shutter.meters["open"] = 1.0
    shutter.memes["worry"] = 0.0
    shutter.memes["pride"] = 2.0
    hero.memes["confidence"] = 1.0
    friend.memes["confidence"] = 1.0

    world.say(trouble["change"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(f"The historic shutter no longer fought the house; it moved the way it was meant to move.")
    world.say(trouble["result"].format(hero=params.hero_name, friend=params.friend_name))
    world.say(rng.choice([
        f'{params.hero_name} laughed and said, “Friendship makes the hard jobs lighter.”',
        f'{params.friend_name} answered, “And problem solving keeps us from making a bigger mess.”',
        f'Together they said, “A good crew listens before it fixes.”',
        f'{params.hero_name} smiled. “We did not battle the shutter. We helped it.”',
    ]))
    world.say(trouble["ending"].format(hero=params.hero_name, friend=params.friend_name))

    world.facts.update(
        hero=hero,
        friend=friend,
        shutter=shutter,
        harbor=harbor,
        solved=True,
        lesson_text=trouble["lesson"],
        trouble=params.trouble,
    )

    prompts = [
        f"Write a pirate tale about {params.hero_name} and {params.friend_name} fixing a historic shutter at {harbor.name}.",
        f"Tell a child-facing story with friendship and problem solving in which the clue '{trouble['clue'].format(hero=params.hero_name, friend=params.friend_name)}' matters.",
        f"Write a complete story with a beginning, turning point, and ending image about a shutter that is {params.trouble}.",
    ]

    story_qa = [
        QAItem(
            question="What problem did the friends find?",
            answer=trouble["premise"],
        ),
        QAItem(
            question="What clue helped them solve it?",
            answer=trouble["clue"].format(hero=params.hero_name, friend=params.friend_name),
        ),
        QAItem(
            question="How did they fix the shutter?",
            answer=trouble["change"].format(hero=params.hero_name, friend=params.friend_name),
        ),
        QAItem(
            question="What did the hero learn?",
            answer=f"{params.hero_name} learned that {trouble['lesson']}.",
        ),
        QAItem(
            question="What showed the problem was solved?",
            answer=trouble["result"].format(hero=params.hero_name, friend=params.friend_name),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a board or set of panels that covers a window and can open or close to let in light and air.",
        ),
        QAItem(
            question="Why do pirate friends work well together?",
            answer="Friends can share ideas, notice clues, and do careful work together, which helps solve problems more safely.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking at a trouble, finding the cause, and choosing a useful way to fix it.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show historic_shutter/1.\n#show friendship/2.\n#show problem_solving/1.\n#show repaired/1.\n#show open/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for harbor_name in HARBORS:
            params = StoryParams(harbor=harbor_name, hero_name=HERO_NAMES[0], friend_name=FRIEND_NAMES[0], trouble="stuck closed")
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
