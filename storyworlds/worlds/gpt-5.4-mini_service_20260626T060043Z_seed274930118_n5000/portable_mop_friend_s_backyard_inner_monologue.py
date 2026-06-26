#!/usr/bin/env python3
"""
A small whodunit-style storyworld set in a friend's backyard.

Premise:
A child visits a friend's backyard, notices a strange wet mess, and carries a
portable mop. The mystery is who made the mess and how the friends solve it
without turning the whole afternoon gloomy.

The story is driven by typed entities with physical meters and emotional memes.
The simulation keeps track of mess, suspicion, clues, and relief, so the prose
follows the changing world state rather than a fixed template.

Narrative instruments:
- Inner monologue
- Humor
- Whodunit tone
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    use: str = ""
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def __post_init__(self):
        for k in ("wet", "muddy", "sticky", "tipped", "clean"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "suspicion", "relief", "amusement", "pride", "guilt"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    suspect: str
    item: str
    clue: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy
        return World(
            entities=copy.deepcopy(self.entities),
            facts=dict(self.facts),
            fired=set(self.fired),
            paragraphs=[[]],
        )


CHARACTER_TRAITS = ["curious", "brave", "silly", "careful", "cheerful", "nosy"]
CHILD_NAMES = ["Mia", "Noah", "Lina", "Eli", "Ava", "Theo", "Nora", "Ben"]
FRIEND_NAMES = ["Pip", "Jules", "Mina", "Owen", "Tess", "Rory", "Milo", "Ivy"]

ITEMS = {
    "toy_wagon": {"label": "toy wagon", "phrase": "a little red toy wagon", "portable": True},
    "garden_shovel": {"label": "garden shovel", "phrase": "a small garden shovel", "portable": True},
    "bucket": {"label": "bucket", "phrase": "a bright blue bucket", "portable": True},
    "sprinkler": {"label": "sprinkler", "phrase": "a wheezing backyard sprinkler", "portable": False},
    "flower_pot": {"label": "flower pot", "phrase": "a clay flower pot", "portable": False},
}

CLUES = {
    "mud_tracks": "muddy footprints near the gate",
    "water_ring": "a ring of water on the patio",
    "grass_blade": "a bent blade of grass stuck to the mop head",
    "glove_print": "a tiny glove print on the bucket handle",
}

SUSPECTS = {
    "dog": {"type": "dog", "label": "the dog"},
    "friend": {"type": "boy", "label": "the friend"},
    "neighbor": {"type": "woman", "label": "the neighbor"},
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld in a friend's backyard.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    item = args.item or rng.choice(list(ITEMS))
    clue = args.clue or rng.choice(list(CLUES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES if child_gender == "girl" else CHILD_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if child_name == friend_name:
        friend_name = next(n for n in FRIEND_NAMES if n != child_name)
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=rng.choice(["girl", "boy"]),
        suspect=suspect,
        item=item,
        clue=clue,
    )


def valid_story(params: StoryParams) -> bool:
    return params.item in ITEMS and params.clue in CLUES and params.suspect in SUSPECTS


def build_world(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("Invalid story parameters.")
    world = World()
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        traits=["little", random.choice(CHARACTER_TRAITS)],
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_gender,
        traits=["little", random.choice(CHARACTER_TRAITS)],
    ))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(
        id="mop",
        kind="thing",
        type="mop",
        label="portable mop",
        phrase="a portable mop with a bright yellow handle",
        owner=child.id,
        portable=True,
        use="clean up a mystery mess",
    ))
    mess = world.add(Entity(
        id="mess",
        kind="thing",
        type="mess",
        label="mystery mess",
        phrase="a mysterious wet patch",
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="character" if params.suspect != "dog" else "animal",
        type=SUSPECTS[params.suspect]["type"],
        label=SUSPECTS[params.suspect]["label"],
        phrase=SUSPECTS[params.suspect]["label"],
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=CLUES[params.clue],
        phrase=CLUES[params.clue],
    ))
    prop = world.add(Entity(
        id=item_cfg["label"],
        kind="thing",
        type=item_cfg["label"],
        label=item_cfg["label"],
        phrase=item_cfg["phrase"],
        portable=item_cfg["portable"],
    ))
    world.facts.update(child=child, friend=friend, item=item, mess=mess, suspect=suspect, clue=clue, prop=prop, params=params)
    return world


def narrate_setup(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    prop = world.facts["prop"]
    world.say(
        f"{child.id} came over to {friend.id}'s backyard on a warm afternoon, "
        f"carrying a portable mop like it was the most serious tool in the world."
    )
    world.say(
        f"{child.id} noticed {prop.phrase} and felt a tiny thrill of curiosity. "
        f"\"A backyard clue,\" {child.id} thought. \"This could be a real case.\""
    )
    world.say(
        f"{friend.id} laughed and said the yard had been tidy before lunch, which only made the mystery feel bigger."
    )
    item.carried_by = child.id
    item.memes["curiosity"] += 1


def apply_mess(world: World) -> None:
    mess = world.facts["mess"]
    clue = world.facts["clue"]
    suspect = world.facts["suspect"]
    child = world.facts["child"]
    if ("mess", "spread") in world.fired:
        return
    world.fired.add(("mess", "spread"))
    mess.meters["wet"] += 1
    mess.memes["suspicion"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Near the patio, {clue.label} caught {child.id}'s eye. "
        f"{child.id} stared at it and had an inner monologue that sounded very detective-like: "
        f"\"Wet patch, clue shape, suspicious timing. Hm.\""
    )
    world.say(
        f"Then {child.id} saw {suspect.label} by the hose and nearly accused {suspect.pronoun('object')} out loud, "
        f"but the evidence was still too wobbly."
    )


def investigate(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    clue = world.facts["clue"]
    suspect = world.facts["suspect"]
    item = world.facts["item"]
    if ("investigate", clue.id) in world.fired:
        return
    world.fired.add(("investigate", clue.id))
    world.say(
        f"{child.id} knelt beside the {clue.label} and held up the portable mop like a magnifying glass by mistake."
    )
    world.say(
        f"\"If the {suspect.label} did it, there should be a trail,\" {child.id} thought. "
        f"\"If not, I am about to blame a poor innocent lawn decoration.\""
    )
    if clue.id == "mud_tracks":
        world.say(
            f"{friend.id} pointed at the path and said the muddy footprints were too small for a grown-up."
        )
    elif clue.id == "water_ring":
        world.say(
            f"{friend.id} pointed at the ring of water and said something nearby must have sprayed the patio."
        )
    elif clue.id == "grass_blade":
        world.say(
            f"{friend.id} lifted the grass blade from the mop head and said it probably came from the hose corner."
        )
    else:
        world.say(
            f"{friend.id} held up the tiny glove print and said, with a grin, that the mystery had one clumsy hand."
        )
    item.memes["curiosity"] += 1
    child.memes["amusement"] += 1


def reveal(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    suspect = world.facts["suspect"]
    if ("reveal", suspect.id) in world.fired:
        return
    world.fired.add(("reveal", suspect.id))
    world.say(
        f"At last, {child.id} found the answer: {suspect.label} had not made the whole mess on purpose."
    )
    world.say(
        f"The real trick was a leaky hose, and {friend.id} had already started laughing because the case was silly once solved."
    )
    child.memes["suspicion"] = max(0.0, child.memes["suspicion"] - 1)
    child.memes["relief"] += 1


def clean_up(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    mess = world.facts["mess"]
    if ("clean", "done") in world.fired:
        return
    world.fired.add(("clean", "done"))
    mess.meters["wet"] = 0
    mess.meters["clean"] = 1
    item.meters["wet"] = 1
    child.memes["pride"] += 1
    child.memes["relief"] += 1
    friend.memes["amusement"] += 1
    world.say(
        f"{child.id} used the portable mop to sweep the water back into place while {friend.id} held the hose steady."
    )
    world.say(
        f"Soon the patio looked neat again, and {child.id} felt proud for solving the mystery without making a bigger splash."
    )


def tell_story(world: World) -> World:
    narrate_setup(world)
    world.para()
    apply_mess(world)
    investigate(world)
    reveal(world)
    world.para()
    clean_up(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a funny whodunit for children set in {p.friend_name}'s backyard involving a portable mop.",
        f"Tell a short mystery where {p.child_name} thinks hard about a wet clue and solves the backyard mess.",
        f"Create a playful detective story with inner monologue, humor, and a portable mop in a friend's backyard.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    friend = world.facts["friend"]
    suspect = world.facts["suspect"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question=f"Where did {child.id} go to solve the mystery?",
            answer=f"{child.id} went to {friend.id}'s backyard, where the strange wet clue was waiting near the patio.",
        ),
        QAItem(
            question=f"What tool did {child.id} carry while investigating?",
            answer="They carried a portable mop, which made the whole search feel like a very tiny detective job.",
        ),
        QAItem(
            question=f"What clue made the case feel suspicious?",
            answer=f"The clue was {clue.label}, which suggested someone or something had been splashing around recently.",
        ),
        QAItem(
            question=f"Who did {child.id} first suspect?",
            answer=f"{child.id} first suspected {suspect.label}, but the evidence was not strong enough to blame {suspect.pronoun('object')} yet.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} solved the case, cleaned the mess with the portable mop, and left {friend.id}'s backyard tidy again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a portable mop used for?",
            answer="A portable mop is used to clean wet or dirty spots, especially when you want to carry it from place to place.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues so they can figure out what happened instead of guessing.",
        ),
        QAItem(
            question="Why can a wet floor be funny in a story?",
            answer="A wet floor can be funny in a story because it can lead to silly slipping, splashing, and surprise accidents without hurting anyone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.portable:
            bits.append("portable=True")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


ASP_RULES = r"""
portable(item) :- item(item), portable_item(item).
clue(C) :- clue_item(C).
wet_mess(M) :- mess(M), wet(M).
suspicious(C) :- clue(C).
possible_suspect(S) :- suspect(S).

solve(C, S) :- character(C), possible_suspect(S), clue(CLU), suspicious(CLU).
cleans(C) :- character(C), portable(mop), wet_mess(mess).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, cfg in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if cfg["portable"]:
            lines.append(asp.fact("portable_item", iid))
    for cid in CLUES:
        lines.append(asp.fact("clue_item", cid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("item", "mop"))
    lines.append(asp.fact("portable_item", "mop"))
    lines.append(asp.fact("mess", "mess"))
    lines.append(asp.fact("wet", "mess"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show portable/1.\n#show suspect/1.\n"))
    ok1 = set(asp.atoms(model, "portable")) == {("mop",)}
    ok2 = set(asp.atoms(model, "suspect")) == set((k,) for k in SUSPECTS)
    if ok1 and ok2:
        print("OK: ASP facts and rules are consistent.")
        return 0
    print("MISMATCH in ASP verification.")
    return 1


def asp_available() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show suspect/1.\n"))
    return sorted(set(asp.atoms(model, "suspect")))


CURATED = [
    StoryParams("Mia", "girl", "Pip", "boy", "dog", "toy_wagon", "mud_tracks"),
    StoryParams("Noah", "boy", "Tess", "girl", "friend", "bucket", "water_ring"),
    StoryParams("Ava", "girl", "Rory", "boy", "neighbor", "garden_shovel", "grass_blade"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        child_gender=args.gender or rng.choice(["girl", "boy"]),
        friend_name=args.friend_name or rng.choice(FRIEND_NAMES),
        friend_gender=rng.choice(["girl", "boy"]),
        suspect=args.suspect or rng.choice(list(SUSPECTS)),
        item=args.item or rng.choice(list(ITEMS)),
        clue=args.clue or rng.choice(list(CLUES)),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show suspect/1.\n#show portable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspect/1.\n"))
        print("ASP suspects:", ", ".join(s for (s,) in sorted(set(asp.atoms(model, "suspect")))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
