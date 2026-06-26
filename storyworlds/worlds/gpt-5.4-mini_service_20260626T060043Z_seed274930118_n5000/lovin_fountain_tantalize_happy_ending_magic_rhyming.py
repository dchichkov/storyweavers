#!/usr/bin/env python3
"""
A standalone storyworld for a rhyming, magical fountain tale with a happy ending.

Premise:
- A child loves a fountain in a garden or courtyard.
- The fountain's sparkle and bubbling water tantalize the child.
- Magic offers a tempting wish, but there is a gentle rule or limit.
- The child learns to wait, share, or help, leading to a happy ending.

The simulation tracks:
- meters: physical state like sparkle, water, bubbles, thirst, wetness, glow
- memes: emotional state like joy, longing, patience, pride, love

The prose is driven by world state, not a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("sparkle", "water", "bubbles", "wet", "glow", "thirst", "wish"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "lovin", "longing", "patience", "pride", "wonder", "tantalize"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    kind: str = "garden"  # garden, courtyard, park, plaza
    honors_waiting: bool = True


@dataclass
class Magic:
    id: str
    label: str
    effect: str
    rhyme: str
    rule: str
    gift: str
    glimmer: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.magic_used: bool = False
        self.magic_allowed: bool = True

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.magic_used = self.magic_used
        w.magic_allowed = self.magic_allowed
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", kind="garden", honors_waiting=True),
    "courtyard": Setting(place="the courtyard", kind="courtyard", honors_waiting=True),
    "park": Setting(place="the park", kind="park", honors_waiting=True),
}

MAGICS = {
    "wish": Magic(
        id="wish",
        label="wish magic",
        effect="grant a small wish",
        rhyme="glow and flow",
        rule="magic should be shared, not snatched",
        gift="a tiny silver lily",
        glimmer="a bright silver sparkle",
    ),
    "song": Magic(
        id="song",
        label="song magic",
        effect="make a tune drift from the water",
        rhyme="sing and ring",
        rule="magic wakes best with kindness",
        gift="a ringing pebble",
        glimmer="a warm musical shimmer",
    ),
    "rainbow": Magic(
        id="rainbow",
        label="rainbow magic",
        effect="paint the spray in soft colors",
        rhyme="shine and twine",
        rule="magic likes patience and a gentle heart",
        gift="a tiny rainbow ribbon",
        glimmer="a glassy rainbow glimmer",
    ),
}

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    magic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lina", "Maya", "Nia", "Ava", "Zoe", "Rina", "Tia", "Lily"]
BOY_NAMES = ["Noah", "Milo", "Eli", "Theo", "Finn", "Leo", "Ollie", "Ben"]
TRAITS = ["gentle", "curious", "cheerful", "playful", "brave", "lovin"]


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
class StoryState:
    def __init__(self, world: World) -> None:
        self.world = world

    @property
    def child(self) -> Entity:
        return self.world.get("child")

    @property
    def parent(self) -> Entity:
        return self.world.get("parent")

    @property
    def fountain(self) -> Entity:
        return self.world.get("fountain")

    @property
    def magic(self) -> Magic:
        return self.world.facts["magic"]


def _rhyming_opening(child: Entity, setting: Setting, magic: Magic) -> None:
    world = child_world(child)
    world.say(
        f"{child.id} was a {next((t for t in world.facts['child_traits'] if t != 'lovin'), 'little')} "
        f"{child.type} who loved the {setting.place} so bright, "
        f"where a fountain sang softly in the light."
    )
    world.say(
        f"The water went splash and the bubbles went pop, "
        f"and {child.id} could not help but stop."
    )
    world.say(
        f"The spray looked {magic.glimmer}, so shiny and grand, "
        f"it felt like a secret was tucked in the land."
    )


def child_world(child: Entity) -> World:
    return child.meters.get("_world_ref")  # type: ignore[return-value]


def set_world_ref(world: World) -> None:
    for e in world.entities.values():
        e.meters["_world_ref"] = world  # type: ignore[assignment]


def predict_temptation(world: World) -> bool:
    sim = world.copy()
    sim.get("child").memes["longing"] += 1
    sim.get("child").memes["tantalize"] += 1
    return sim.get("child").memes["longing"] >= THRESHOLD


def setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    fountain = world.add(Entity(id="fountain", kind="thing", type="fountain", label="fountain"))
    world.facts["magic"] = MAGICS[params.magic]
    world.facts["child_name"] = params.name
    world.facts["child_gender"] = params.gender
    world.facts["child_parent"] = params.parent
    world.facts["child_traits"] = ["lovin", params.trait]
    world.facts["setting"] = SETTINGS[params.place]
    set_world_ref(world)
    child.memes["lovin"] += 1
    child.memes["wonder"] += 1
    fountain.meters["water"] += 1
    fountain.meters["sparkle"] += 1
    fountain.meters["bubbles"] += 1


def intro(world: World) -> None:
    c, f = world.get("child"), world.get("fountain")
    setting = world.facts["setting"]
    magic = world.facts["magic"]
    world.say(
        f"{c.id} came to {setting.place}, where the fountain was lively and bright."
    )
    world.say(
        f"It made a merry little scene, all shimmer and spray, "
        f"and {c.id} felt a warm lovin' sway."
    )
    world.say(
        f"The fountain's song was {magic.glimmer}, a twinkling delight; "
        f"it tantalized {c.id} from morning till night."
    )


def temptation(world: World) -> None:
    c = world.get("child")
    c.memes["longing"] += 1
    c.memes["tantalize"] += 1
    c.meters["thirst"] += 1
    world.say(
        f"{c.id} leaned in and sighed, 'Oh, what a sweet lure! "
        f"That splashy, bright water looks cool and pure.'"
    )
    world.say(
        f"The fountain kept glittering, calling in rhyme, "
        f"like a tiny gold bell in the middle of time."
    )


def warn(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    magic = world.facts["magic"]
    world.say(
        f'{p.label.capitalize()} said, "Wait a small moment; that is the right way. '
        f"Magic is nicer when shared in play."
    )
    world.say(
        f'"If you rush at the fountain, the spell may grow wild; '
        f"but patience can bless a small heart and a child."'
    )
    if predict_temptation(world):
        c.memes["longing"] += 0.5


def challenge(world: World) -> None:
    c = world.get("child")
    c.memes["longing"] += 1
    c.memes["tantalize"] += 1
    c.meters["wet"] += 1
    world.say(
        f"{c.id} wanted the splash right then and there, "
        f"but the bubbly magic still hung in the air."
    )
    world.say(
        f"So {c.id} tiptoed close with a shaky little grin, "
        f"while the fountain kept singing, 'Come play from within.'"
    )


def resolve(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    fountain = world.get("fountain")
    magic = world.facts["magic"]
    if c.memes["longing"] < THRESHOLD:
        return
    if ("magic", magic.id) not in world.fired:
        world.fired.add(("magic", magic.id))
        world.magic_used = True
        c.memes["patience"] += 1
        c.memes["joy"] += 1
        c.memes["lovin"] += 1
        fountain.meters["glow"] += 1
        fountain.meters["sparkle"] += 1
        world.say(
            f"Then the fountain gave a soft little gleam, "
            f"and the magic awoke like a friendly dream."
        )
        world.say(
            f"It did not say, 'Take!' in a greedy old tone; "
            f"it said, 'Share, and the joy will be grown.'"
        )
        world.say(
            f"{c.id} waited, then smiled as the water played fair; "
            f"{magic.label} made a tiny gift there."
        )
        world.say(
            f"{p.label.capitalize()} clapped in delight, and the fountain shone white, "
            f"while {c.id} felt calm, cozy, and right."
        )
        c.memes["pride"] += 1
        world.facts["gift"] = magic.gift


def ending(world: World) -> None:
    c = world.get("child")
    p = world.get("parent")
    magic = world.facts["magic"]
    gift = world.facts.get("gift", magic.gift)
    c.memes["joy"] += 1
    c.memes["patience"] += 1
    world.say(
        f"In the happy ending, {c.id} held {gift} near, "
        f"and the fountain sang softly for all to hear."
    )
    world.say(
        f"The spray still sparkled, the bubbles still flew, "
        f"and kindness made magic feel fresh and true."
    )
    world.say(
        f"{c.id} went home with a smile warm and wide, "
        f"lovin' the fountain and the calm in {p.label}'s side."
    )


def tell(setting: Setting, magic: Magic, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    world.add(Entity(id="parent", kind="character", type=parent, label=parent))
    world.add(Entity(id="fountain", kind="thing", type="fountain", label="fountain"))
    world.facts["magic"] = magic
    world.facts["setting"] = setting
    world.facts["child_traits"] = ["lovin", trait]
    set_world_ref(world)

    # Setup state
    child.memes["lovin"] += 1
    child.memes["wonder"] += 1
    world.get("fountain").meters["water"] += 1
    world.get("fountain").meters["sparkle"] += 1
    world.get("fountain").meters["bubbles"] += 1

    # Narrative acts
    _rhyming_opening(child, setting, magic)
    world.para()
    intro(world)
    temptation(world)
    warn(world)
    challenge(world)
    world.para()
    resolve(world)
    ending(world)

    world.facts.update(
        child=child,
        parent=world.get("parent"),
        fountain=world.get("fountain"),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    setting = world.facts["setting"]
    magic = world.facts["magic"]
    return [
        f'Write a short rhyming story for a child named {c.id} at {setting.place} with a magical fountain.',
        f"Tell a happy-ending story where the fountain's magic tantalizes {c.id}, but patience helps in the end.",
        f'Write a magical rhyming tale with the words "lovin", "fountain", and "tantalize".',
        f"Create a gentle story in {setting.place} where {c.id} learns to wait for {magic.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    setting = world.facts["setting"]
    magic = world.facts["magic"]
    qa = [
        QAItem(
            question=f"Where does {c.id} visit the fountain?",
            answer=f"{c.id} visits the fountain at {setting.place}.",
        ),
        QAItem(
            question=f"Why did the fountain tantalize {c.id}?",
            answer=f"It tantalized {c.id} because the water was bright, bubbly, and magical, so it looked very tempting.",
        ),
        QAItem(
            question=f"What did {p.label} tell {c.id} to do first?",
            answer="The parent told the child to wait a small moment and choose the gentle way.",
        ),
        QAItem(
            question=f"What happy thing happened at the end?",
            answer=f"{magic.label.capitalize()} gave a tiny gift, and {c.id} left smiling in a happy ending.",
        ),
    ]
    if world.magic_used:
        qa.append(
            QAItem(
                question=f"How did the magic help {c.id}?",
                answer=f"The magic rewarded patience with {magic.gift}, so {c.id} could enjoy the fountain without turning the moment greedy or rough.",
            )
        )
    return qa


KNOWLEDGE = {
    "fountain": [
        QAItem(
            question="What is a fountain?",
            answer="A fountain is a structure that sends water up or out so it can splash, sparkle, and look pretty.",
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special wonder that can make unusual things happen, like a gift, a glow, or a wish.",
        )
    ],
    "rhyming": [
        QAItem(
            question="What does it mean for a story to rhyme?",
            answer="A rhyming story uses words with matching ending sounds, like light and night or flow and glow.",
        )
    ],
    "patience": [
        QAItem(
            question="Why is patience a good thing?",
            answer="Patience is good because it helps someone wait calmly, think kindly, and make safer choices.",
        )
    ],
    "happy": [
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the worry is solved and the characters finish feeling safe, calm, or joyful.",
        )
    ],
    "water": [
        QAItem(
            question="Why can water sparkle?",
            answer="Water can sparkle when light shines on moving drops, making them look bright and shiny.",
        )
    ],
}
KNOWLEDGE_ORDER = ["fountain", "water", "magic", "rhyming", "patience", "happy"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"fountain", "water", "magic", "rhyming", "patience", "happy"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A fountain story is valid when the setting has a fountain, the child is
% tempted by magic, and the ending resolves with a gift.
valid_setting(S) :- setting(S).

tempting_magic(M) :- magic(M).

happy_ending(S, M) :- valid_setting(S), tempting_magic(M).

#show valid_setting/1.
#show tempting_magic/1.
#show happy_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_validate() -> bool:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    atoms = set(asp.atoms(model, "happy_ending"))
    expected = {(s, m) for s in SETTINGS for m in MAGICS}
    return atoms == expected


# ---------------------------------------------------------------------------
# Parsing and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming magical fountain storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    magic = args.magic or rng.choice(list(MAGICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, magic=magic, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MAGICS[params.magic], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"magic_used={world.magic_used}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", magic="wish", name="Lina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="courtyard", magic="song", name="Theo", gender="boy", parent="father", trait="playful"),
    StoryParams(place="park", magic="rainbow", name="Maya", gender="girl", parent="mother", trait="cheerful"),
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


def asp_verify() -> int:
    if asp_validate():
        print("OK: ASP twin agrees with the simple happy-ending gate.")
        return 0
    print("MISMATCH: ASP twin did not match expected facts.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/2."))
        for atom in sorted(set(asp.atoms(model, "happy_ending"))):
            print(atom)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
