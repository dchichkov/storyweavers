#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    place: str
    obstacles: set[str]
    opening: str
    edge_dim: bool = True


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    obstacle: str
    ghost_name: str
    memory: str
    clue: str
    resting_place: str


@dataclass
class Tool:
    id: str
    label: str
    solves: set[str]
    carry: str
    use: str
    glow: bool = False


@dataclass
class StoryParams:
    place: str
    keepsake: str
    tool: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def setting_image(setting: Setting) -> str:
    if setting.id == "attic":
        return "Dust floated in the thin gray light, and the rafters made long, careful shadows."
    if setting.id == "pond":
        return "The reeds leaned over the water, and the air felt cool and silver."
    return "The old gate stood where the garden met the lane, with leaves whispering on both sides."


def can_solve(setting: Setting, keepsake: Keepsake, tool: Tool) -> bool:
    return keepsake.obstacle in setting.obstacles and keepsake.obstacle in tool.solves


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for kid, keepsake in KEEPSAKES.items():
            for tid, tool in TOOLS.items():
                if can_solve(setting, keepsake, tool):
                    out.append((place, kid, tid))
    return sorted(out)


def explain_rejection(setting: Setting, keepsake: Keepsake, tool: Tool) -> str:
    if keepsake.obstacle not in setting.obstacles:
        return (
            f"(No story: {keepsake.phrase} is lost where something is {keepsake.obstacle}, "
            f"but {setting.place} does not fit that kind of search.)"
        )
    return (
        f"(No story: {tool.label} does not solve the real problem here. "
        f"The quest needs help with something {keepsake.obstacle}, and the fix must actually work.)"
    )


def intro(world: World, hero: Entity, elder: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked listening to gentle ghost stories with "
        f"{hero.pronoun('possessive')} {elder.label}."
    )
    world.say(
        f"One evening, {elder.label} took {hero.pronoun('object')} to {world.setting.place}, "
        f"the edge-dim part of the old place where twilight always seemed to stay a little longer."
    )
    world.say(setting_image(world.setting))


def meet_ghost(world: World, hero: Entity, ghost: Entity, keepsake: Keepsake) -> None:
    hero.memes["wonder"] += 1
    hero.memes["fear"] += 1
    ghost.memes["lonely"] += 1
    world.say(
        f"Then a pale little ghost drifted out and stopped beside a patch of shadow. "
        f'"Please do not run," whispered {ghost.label}. "I lost {keepsake.phrase}, and I cannot rest without it."'
    )
    world.say(
        f"{hero.id}'s hands felt cold, because a true ghost was much more real than a bedtime story."
    )


def elder_guides(world: World, hero: Entity, elder: Entity, tool: Tool, keepsake: Keepsake) -> None:
    hero.memes["trust"] += 1
    world.say(
        f'{elder.label.capitalize()} squeezed {hero.pronoun("possessive")} shoulder and said, '
        f'"Being brave does not mean feeling nothing. It means helping even while your knees are shaky."'
    )
    world.say(
        f'Together they brought {tool.label}. "{tool.carry}," {elder.label} said, '
        f'"and look where {ghost_name(world).label} remembers seeing {keepsake.label} last."'
    )


def search(world: World, hero: Entity, ghost: Entity, tool: Tool, keepsake: Keepsake) -> None:
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 2
    hero.meters["steps"] += 1
    world.say(
        f"{hero.id} took a slow breath and walked closer. {tool.use.capitalize()}."
    )
    if tool.glow:
        world.say(
            f"The small light made the dark look less like a hungry mouth and more like an ordinary hiding place."
        )
    world.say(
        f"{ghost.label.capitalize()} floated beside {hero.pronoun('object')} and pointed toward {keepsake.resting_place}."
    )


def recover(world: World, hero: Entity, ghost: Entity, keepsake: Keepsake) -> None:
    hero.meters["found"] += 1
    ghost.memes["hope"] += 1
    world.say(
        f"At last {hero.id} found {keepsake.phrase}. It gave a tiny sound, {keepsake.clue}, as if it had been waiting to be held again."
    )
    world.say(
        f'{hero.pronoun().capitalize()} placed it in {ghost.label}\'s misty hands. '
        f'"I remember now," whispered the ghost. "{keepsake.memory}."'
    )


def settle_ghost(world: World, hero: Entity, ghost: Entity, elder: Entity, keepsake: Keepsake) -> None:
    ghost.memes["peace"] += 2
    ghost.memes["lonely"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["pride"] += 1
    world.say(
        f"A soft glow spread through the ghost. The air stopped feeling tight and strange."
    )
    world.say(
        f'"Thank you for finishing my little quest," said {ghost.label}. '
        f'"Now I can go where the night is kind."'
    )
    world.say(
        f"The ghost bowed to {hero.id} and {elder.label}, then thinned into silver dust. "
        f"{hero.id} stood very still, listening to the quiet place that did not feel scary anymore."
    )


def ghost_name(world: World) -> Entity:
    return world.get("ghost")


def tell(
    setting: Setting,
    keepsake: Keepsake,
    tool: Tool,
    *,
    hero_name: str,
    hero_type: str,
    trait: str,
    elder_type: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    elder_label = {"aunt": "aunt", "uncle": "uncle", "grandmother": "grandma", "grandfather": "grandpa"}[elder_type]
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label=elder_label))
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label=keepsake.ghost_name,
            phrase=f"the ghost named {keepsake.ghost_name}",
        )
    )
    thing = world.add(
        Entity(
            id="keepsake",
            kind="thing",
            type="keepsake",
            label=keepsake.label,
            phrase=keepsake.phrase,
            location=keepsake.resting_place,
        )
    )
    helper = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.label,
            owner=hero.id,
        )
    )

    intro(world, hero, elder)
    world.para()
    meet_ghost(world, hero, ghost, keepsake)
    elder_guides(world, hero, elder, tool, keepsake)
    world.para()
    search(world, hero, ghost, tool, keepsake)
    recover(world, hero, ghost, keepsake)
    settle_ghost(world, hero, ghost, elder, keepsake)

    world.facts.update(
        hero=hero,
        elder=elder,
        ghost=ghost,
        keepsake=keepsake,
        tool=tool,
        setting=setting,
        bravery=hero.memes["bravery"],
        peace=ghost.memes["peace"],
        solved=hero.meters["found"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the old attic stairs",
        obstacles={"high"},
        opening="the rafters leaned close over the steps",
    ),
    "pond": Setting(
        id="pond",
        place="the edge-dim pond path",
        obstacles={"muddy"},
        opening="the path slipped beside black water and reeds",
    ),
    "gate": Setting(
        id="gate",
        place="the garden gate at the edge of the lane",
        obstacles={"thorny"},
        opening="the gate clicked softly while vines curled around it",
    ),
}

KEEPSAKES = {
    "bell": Keepsake(
        id="bell",
        label="bell",
        phrase="a small brass bell",
        obstacle="high",
        ghost_name="Mira",
        memory="I used to ring this bell before supper, so my family could find me",
        clue="ting-ting",
        resting_place="a crooked attic beam",
    ),
    "key": Keepsake(
        id="key",
        label="key",
        phrase="a round old key",
        obstacle="muddy",
        ghost_name="Tobin",
        memory="I kept the key to our boat in my pocket when the pond was young and bright",
        clue="clink",
        resting_place="the soft mud under the reeds",
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="ribbon",
        phrase="a moon-pale ribbon",
        obstacle="thorny",
        ghost_name="Elsie",
        memory="I wore this ribbon on festival nights and danced by the gate lamps",
        clue="a faint silk whisper",
        resting_place="the middle of a thorn bush",
    ),
}

TOOLS = {
    "stool": Tool(
        id="stool",
        label="a wooden step stool",
        solves={"high"},
        carry="Set it down slowly and climb one step at a time",
        use="Using the wooden step stool, the high beam came within reach",
    ),
    "boots": Tool(
        id="boots",
        label="a pair of rain boots",
        solves={"muddy"},
        carry="Pull these on first so the mud cannot trap your shoes",
        use="With the rain boots on, the wet bank became safe enough to search",
    ),
    "gloves": Tool(
        id="gloves",
        label="a pair of garden gloves",
        solves={"thorny"},
        carry="Wear these so the thorns cannot scratch your fingers",
        use="The garden gloves let brave fingers part the branches without getting hurt",
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Tess", "Ivy", "Wren"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Jude", "Theo", "Ash"]
TRAITS = ["careful", "quiet", "curious", "steady", "gentle", "thoughtful"]


CURATED = [
    StoryParams(
        place="attic",
        keepsake="bell",
        tool="stool",
        name="Lina",
        gender="girl",
        elder="grandmother",
        trait="careful",
    ),
    StoryParams(
        place="pond",
        keepsake="key",
        tool="boots",
        name="Finn",
        gender="boy",
        elder="uncle",
        trait="steady",
    ),
    StoryParams(
        place="gate",
        keepsake="ribbon",
        tool="gloves",
        name="Ivy",
        gender="girl",
        elder="aunt",
        trait="curious",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    keepsake = f["keepsake"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        'Write a short ghost story for a 3-to-5-year-old that feels gentle, brave, and complete, and include the phrase "edge-dim".',
        f"Tell a child-facing story about a {hero.type} named {hero.id} who goes on a small quest at {setting.place} to find {keepsake.phrase} for a lonely ghost.",
        f"Write a tiny bravery quest where {hero.id} feels scared, {elder.label} offers {tool.label}, and the ending shows the ghost finally at peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    ghost = f["ghost"]
    keepsake = f["keepsake"]
    tool = f["tool"]
    setting = f["setting"]
    pos = hero.pronoun("possessive")
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    return [
        QAItem(
            question=f"Where did {hero.id} go when the ghost story began?",
            answer=(
                f"{hero.id} went to {setting.place} with {pos} {elder.label}. "
                f"It was the edge-dim part of the place, so it felt quiet and mysterious."
            ),
        ),
        QAItem(
            question=f"Why was {ghost.label} sad?",
            answer=(
                f"{ghost.label} was sad because {ghost.pronoun('subject')} had lost {keepsake.phrase}. "
                f"Without it, the ghost felt lonely and could not rest."
            ),
        ),
        QAItem(
            question=f"How did {tool.label} help on the quest?",
            answer=(
                f"{tool.label.capitalize()} helped because it solved the real problem in the search. "
                f"With it, {hero.id} could safely reach the place where {keepsake.label} was hidden."
            ),
        ),
        QAItem(
            question=f"Was {hero.id} brave even though {sub} felt afraid?",
            answer=(
                f"Yes. {hero.id} was brave because {sub} still chose to help while feeling scared. "
                f"{elder.label.capitalize()} reminded {obj} that bravery means helping even with shaky knees."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"At the end, {hero.id} found {keepsake.phrase} and gave it back to {ghost.label}. "
                f"The ghost turned peaceful and the place no longer felt scary."
            ),
        ),
    ]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story about a spirit or ghost. In a gentle ghost story, the ghost may seem spooky at first, but it usually wants help or kindness."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right or helpful thing even when you feel scared."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip or mission to find something important or to solve a problem."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool is a small stool that helps you reach something high."
        )
    ],
    "boots": [
        (
            "Why do rain boots help in mud?",
            "Rain boots keep your feet dry and make it easier to stand on wet, muddy ground."
        )
    ],
    "gloves": [
        (
            "Why do garden gloves help near thorns?",
            "Garden gloves cover your hands so sharp thorns do not scratch your skin."
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a ringing sound that can help people notice it."
        )
    ],
    "key": [
        (
            "What is a key for?",
            "A key is used to open or lock something, like a door, a box, or a little gate."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth that can be tied as a decoration."
        )
    ],
}

TOPIC_ORDER = ["ghost", "bravery", "quest", "stool", "boots", "gloves", "bell", "key", "ribbon"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"ghost", "bravery", "quest", f["tool"].id, f["keepsake"].id}
    out: list[QAItem] = []
    for tag in TOPIC_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
fits(Place, Keepsake, Tool) :-
    affords(Place, Need),
    needs(Keepsake, Need),
    solves(Tool, Need).

valid_story(Place, Keepsake, Tool) :- fits(Place, Keepsake, Tool).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for need in sorted(setting.obstacles):
            lines.append(asp.fact("affords", pid, need))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("needs", kid, keepsake.obstacle))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for need in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show fits/3."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between Python and ASP:")
        if py - asp_set:
            print(" only in python:", sorted(py - asp_set))
        if asp_set - py:
            print(" only in asp:", sorted(asp_set - py))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("Verification failed: empty story")
            return 1
        if "Thank you for finishing my little quest" not in sample.story:
            print("Verification failed: missing quest resolution")
            return 1
    print(f"OK: ASP matches Python on {len(py)} combos, and curated stories render cleanly.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a child takes a bravery quest to help a lonely ghost."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["aunt", "uncle", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list valid (place, keepsake, tool) triples from ASP")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.keepsake and args.tool:
        setting = SETTINGS[args.place]
        keepsake = KEEPSAKES[args.keepsake]
        tool = TOOLS[args.tool]
        if not can_solve(setting, keepsake, tool):
            raise StoryError(explain_rejection(setting, keepsake, tool))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.keepsake is None or c[1] == args.keepsake)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, keepsake, tool = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["aunt", "uncle", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        keepsake=keepsake,
        tool=tool,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    hero_type = "girl" if params.gender == "girl" else "boy"
    world = tell(
        SETTINGS[params.place],
        KEEPSAKES[params.keepsake],
        TOOLS[params.tool],
        hero_name=params.name,
        hero_type=hero_type,
        trait=params.trait,
        elder_type=params.elder,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for place, keepsake, tool in asp_valid_combos():
            print(f"{place:6} {keepsake:7} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.keepsake} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
