#!/usr/bin/env python3
"""
storyworlds/worlds/hug_genie_suspense_rhyming_story.py
=======================================================

A small story world about a child, a genie, a suspenseful wish, and a hug.
The stories are short, child-facing, and lightly rhyming in the style of a
TinyStories-like rhyming tale.

Premise:
- A child finds a genie lamp in a quiet place.
- The genie can grant one wish, but the wish must be chosen carefully.
- Suspense grows as the child worries about what to ask for.
- The turn comes when the child chooses a kind wish that resolves fear.
- The ending image proves what changed: worry becomes warmth, and a hug.

The simulation tracks:
- meters: physical things like lamp glow, smoke, distance to lamp, huggedness
- memes: emotions like worry, hope, joy, trust, suspense

The prose is driven by state changes rather than a frozen template.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    quiet: bool = True


@dataclass
class Wish:
    id: str
    phrase: str
    rhyme: str
    suspense_kind: str
    resolves: str
    outcome: str


@dataclass
class StoryParams:
    place: str
    wish: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        out: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    out.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            out.append(" ".join(current))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic"),
    "garden": Setting(place="the garden"),
    "bedroom": Setting(place="the bedroom"),
    "closet": Setting(place="the closet"),
}

WISHES = {
    "hug": Wish(
        id="hug",
        phrase="a warm hug that made the dark feel small",
        rhyme="hug",
        suspense_kind="fear",
        resolves="worry",
        outcome="warm and safe",
    ),
    "light": Wish(
        id="light",
        phrase="a soft light to chase the night away",
        rhyme="light",
        suspense_kind="dark",
        resolves="fear",
        outcome="bright and calm",
    ),
    "friend": Wish(
        id="friend",
        phrase="a gentle friend to stay and play",
        rhyme="friend",
        suspense_kind="lonely",
        resolves="loneliness",
        outcome="kind and glad",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Max", "Sam"]
TRAITS = ["brave", "curious", "small", "soft-spoken", "silly", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story needs one setting, one wish, and one compatible child gender.
valid_story(P, W, G) :- place(P), wish(W), gender(G), can_appear(G, W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for w in WISHES.values():
        lines.append(asp.fact("wish", w.id))
        lines.append(asp.fact("suspense", w.suspense_kind))
        lines.append(asp.fact("resolves", w.id, w.resolves))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for wish_id, wish in WISHES.items():
        if wish.id == "friend":
            lines.append(asp.fact("can_appear", "girl", wish_id))
            lines.append(asp.fact("can_appear", "boy", wish_id))
        else:
            lines.append(asp.fact("can_appear", "girl", wish_id))
            lines.append(asp.fact("can_appear", "boy", wish_id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def rhymes(word: str) -> str:
    return {
        "hug": "snug as a bug",
        "light": "bright in the night",
        "friend": "good things tend",
    }.get(word, "sweet and neat")


def build_story(world: World, child: Entity, parent: Entity, genie: Entity, wish: Wish) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    genie.meters["lamp_smoke"] = 1
    genie.memes["mystery"] = 1
    world.say(f"In {world.setting.place}, a lamp lay still and gleamed in the dim.")
    world.say(f"{child.id} found it there, and the air felt thin and grim.")
    world.say(f"When the lamp gave a blink and a swirl and a spin,")
    world.say(f"out popped a genie with a grin-grin-grin.")

    world.say("")
    world.say(f'"Ask one wish," said the genie, voice low as a purr.')
    world.say(f"{child.id} felt suspense in a tiny little blur.")
    child.memes["suspense"] = child.memes.get("suspense", 0) + 2
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"Would it be too big? Would it go wrong with a whirr?")
    world.say(f"The lamp gave a shimmer, then a hush, then a stir.")

    world.say("")
    world.say(f"{child.id} thought of {wish.phrase},")
    world.say(f"and that thought felt kind and neat.")
    world.say(f"But {child.pronoun('possessive')} heart still tapped fast, like little quick feet.")
    if wish.id == "hug":
        world.say(f"{child.id} said, 'I wish for a hug that can help me feel snug.'")
    elif wish.id == "light":
        world.say(f"{child.id} said, 'I wish for a light that can make the dark hug me tight.'")
    else:
        world.say(f"{child.id} said, 'I wish for a friend who will stay until the end.'")

    child.memes["trust"] = child.memes.get("trust", 0) + 2
    genie.memes["kindness"] = genie.memes.get("kindness", 0) + 1
    genie.meters["glow"] = 1

    world.say("")
    world.say(f"The genie nodded, then gave a soft, shining cheer.")
    world.say(f"With a puff and a poof, the answer appeared near.")
    world.say(f"{wish.outcome.capitalize()} came over {child.id} like a warm summer rug,")
    world.say(f"and the wish turned to {rhymes(wish.id)} in a snug little hug.")

    child.memes["joy"] = child.memes.get("joy", 0) + 3
    child.memes["worry"] = 0
    child.memes["suspense"] = 0
    child.meters["huggedness"] = 1
    genie.meters["smoke"] = 0
    genie.memes["mystery"] = 0

    world.say("")
    world.say(f"{child.id} hugged {genie.id}, and the room felt wide and slow.")
    world.say(f"No more fret, no more dread, just a soft golden glow.")
    world.say(f"And there in {world.setting.place}, where the lamp used to budge,")
    world.say(f"was a child and a genie, sharing one gentle hug.")


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful rhyming genie story world.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--wish", choices=WISHES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    wish = args.wish or rng.choice(list(WISHES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, wish=wish, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    genie = world.add(Entity(id="Genie", kind="character", type="genie"))
    wish = WISHES[params.wish]
    world.facts.update(child=child, parent=parent, genie=genie, wish=wish, params=params)
    build_story(world, child, parent, genie, wish)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    wish: Wish = world.facts["wish"]  # type: ignore[assignment]
    return [
        f'Write a short rhyming story with suspense about a child named {params.name} and a genie.',
        f"Tell a gentle bedtime story where a {params.gender} meets a genie in {params.place} and asks for a {wish.id}.",
        f'Write a simple story that uses the words "genie" and "{wish.id}" and ends with a hug.',
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    wish: Wish = world.facts["wish"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who found the lamp in {world.setting.place}?",
            answer=f"{params.name} found the lamp in {world.setting.place}, and that is how the genie story began.",
        ),
        QAItem(
            question="Why did the child feel suspense?",
            answer=f"{params.name} felt suspense because the genie said to ask one wish, and the child had to choose carefully.",
        ),
        QAItem(
            question=f"What wish did {params.name} ask for?",
            answer=f"{params.name} asked for {wish.phrase}, which was a kind wish and felt safe to choose.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, worry was gone, joy grew bigger, and {params.name} hugged the genie.",
        ),
    ]
    if child.memes.get("suspense", 0) > 0:
        qa.append(QAItem(
            question=f"How did {params.name} feel before asking the wish?",
            answer=f"Before asking, {params.name} felt nervous and suspenseful, but then bravery helped the wish come out.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a genie?",
            answer="A genie is a magical character from a lamp who can grant wishes in a surprising, mysterious way.",
        ),
        QAItem(
            question="What does suspense mean?",
            answer="Suspense is the feeling of not knowing what will happen next, which can make a story exciting.",
        ),
        QAItem(
            question="What is a hug?",
            answer="A hug is when someone wraps their arms around another person in a caring way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {
        (p, w, g) for p in SETTINGS for w in WISHES for g in ["girl", "boy"]
    }
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(clingo_set - python_set))
    print("Python only:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="attic", wish="hug", name="Mia", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="garden", wish="light", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="closet", wish="friend", name="Nora", gender="girl", parent="mother", trait="cheerful"),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story forms:")
        for item in stories:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
