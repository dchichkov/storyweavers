#!/usr/bin/env python3
"""
storyworlds/worlds/folder_moral_value_magic_tall_tale.py
========================================================

A small Tall Tale-style story world about a magic folder, a moral choice, and a
surprising good turn.

The seed image:
- A child finds a strange folder that can hold more than paper.
- The folder's magic reacts to how the child uses it.
- A moral choice matters: keeping, sharing, or returning what was found.
- The ending should prove the choice changed the world.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicFolder:
    id: str
    label: str
    phrase: str
    magic: str
    reward: str
    moral: str
    can_hold: set[str] = field(default_factory=set)
    reacts_to: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    folder: str
    moral_choice: str
    hero_name: str
    hero_kind: str
    helper_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def char(self, eid: str) -> Entity:
        return self.entities[eid]


HEROES = [
    ("Milo", "boy"),
    ("Nina", "girl"),
    ("Toby", "boy"),
    ("Pia", "girl"),
    ("Owen", "boy"),
    ("Luna", "girl"),
]

HELPERS = ["grandma", "grandpa", "neighbor", "teacher"]
MORAL_CHOICES = ["return it", "share it", "tell the truth", "keep it secret"]
ACTIONS = ["collect leaves", "carry notes", "sort buttons", "deliver papers", "gather seeds"]

PLACES = {
    "library_steps": Place(
        id="library_steps",
        label="the library steps",
        detail="The steps were as broad as a barn roof, and the wind could whistle a tune through them.",
        affords={"collect leaves", "carry notes"},
    ),
    "market_square": Place(
        id="market_square",
        label="the market square",
        detail="The square rang with voices, wagons, and a bell that sounded taller than a ladder.",
        affords={"carry notes", "deliver papers"},
    ),
    "old_orchard": Place(
        id="old_orchard",
        label="the old orchard",
        detail="The orchard had trees so knuckly they looked like they had been shaking hands with the sky for years.",
        affords={"collect leaves", "gather seeds"},
    ),
}

FOLDERS = {
    "blue_folder": MagicFolder(
        id="blue_folder",
        label="a blue folder",
        phrase="a bright blue folder with a silver clasp",
        magic="it could tuck away more than paper; it could hold a promise for the whole day",
        reward="the folder gave back a warm glow and a helpful plan",
        moral="truth and kindness make magic work best",
        can_hold={"paper", "seeds", "notes", "leaves"},
        reacts_to={"return it", "share it", "tell the truth"},
    ),
    "red_folder": MagicFolder(
        id="red_folder",
        label="a red folder",
        phrase="a red folder that gleamed like a sunset in a pocket",
        magic="it could keep a secret in one flap and a good deed in the other",
        reward="the folder hummed and turned the air cheerful",
        moral="sharing and honesty make the brightest kind of magic",
        can_hold={"paper", "notes", "buttons"},
        reacts_to={"share it", "tell the truth"},
    ),
}

ASP_RULES = r"""
place(place_library_steps).
place(place_market_square).
place(place_old_orchard).

action(collect_leaves).
action(carry_notes).
action(sort_buttons).
action(deliver_papers).
action(gather_seeds).

folder(blue_folder).
folder(red_folder).

moral(return_it).
moral(share_it).
moral(tell_the_truth).
moral(keep_it_secret).

affords(place_library_steps,collect_leaves).
affords(place_library_steps,carry_notes).
affords(place_market_square,carry_notes).
affords(place_market_square,deliver_papers).
affords(place_old_orchard,collect_leaves).
affords(place_old_orchard,gather_seeds).

can_hold(blue_folder,paper).
can_hold(blue_folder,seeds).
can_hold(blue_folder,notes).
can_hold(blue_folder,leaves).

can_hold(red_folder,paper).
can_hold(red_folder,notes).
can_hold(red_folder,buttons).

reacts_to(blue_folder,return_it).
reacts_to(blue_folder,share_it).
reacts_to(blue_folder,tell_the_truth).

reacts_to(red_folder,share_it).
reacts_to(red_folder,tell_the_truth).

valid(P,A,F,M) :- affords(P,A), can_hold(F,paper), moral(M), reacts_to(F,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for f in FOLDERS.values():
        lines.append(asp.fact("folder", f.id))
        for c in sorted(f.can_hold):
            lines.append(asp.fact("can_hold", f.id, c))
        for r in sorted(f.reacts_to):
            lines.append(asp.fact("reacts_to", f.id, r))
    for m in MORAL_CHOICES:
        lines.append(asp.fact("moral", m.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def moral_gate(place: Place, action: str, folder: MagicFolder, moral_choice: str) -> bool:
    return action in place.affords and moral_choice in folder.reacts_to


def explain_invalid(place: Place, action: str, folder: MagicFolder, moral_choice: str) -> str:
    if action not in place.affords:
        return f"(No story: {action} does not fit {place.label}.)"
    if moral_choice not in folder.reacts_to:
        return f"(No story: this folder's magic does not answer to {moral_choice}.)"
    return "(No story: that combination does not make a believable tall tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale world: a magic folder and a moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--folder", choices=FOLDERS)
    ap.add_argument("--moral-choice", choices=MORAL_CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--hero-kind", choices=["boy", "girl"])
    ap.add_argument("--helper-kind", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    action = args.action or rng.choice(sorted(PLACES[place].affords))
    folder = args.folder or rng.choice(list(FOLDERS))
    moral_choice = args.moral_choice or rng.choice(MORAL_CHOICES)
    if not moral_gate(PLACES[place], action, FOLDERS[folder], moral_choice):
        raise StoryError(explain_invalid(PLACES[place], action, FOLDERS[folder], moral_choice))
    hero_kind = args.hero_kind or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice([n for n, k in HEROES if k == hero_kind])
    helper_kind = args.helper_kind or rng.choice(HELPERS)
    return StoryParams(place, action, folder, moral_choice, hero_name, hero_kind, helper_kind)


def story_intro(world: World, hero: Entity, helper: Entity, folder: MagicFolder) -> None:
    world.say(
        f"{hero.id} was a little {hero.kind} with quick feet and a bigger heart than a wagon wheel."
    )
    world.say(
        f"One morning {hero.id} found {folder.phrase}; it looked ordinary, but it hid a very peculiar shine."
    )
    world.say(
        f"{helper.label.capitalize()} said the folder's magic was simple and mighty: {folder.magic}."
    )


def story_middle(world: World, hero: Entity, helper: Entity, folder: MagicFolder, action: str, moral_choice: str) -> None:
    place = world.place
    world.para()
    world.say(f"{place.detail}")
    world.say(
        f"{hero.id} wanted to {action}, and {hero.id} tucked the found folder under an arm as if it were a treasure chest."
    )
    if moral_choice == "keep it secret":
        hero.memes["greed"] = hero.memes.get("greed", 0) + 1
        world.say(
            f"{hero.id} thought about keeping it secret, but the folder's clasp gave a tiny click like a cough in a church."
        )
        world.say(
            f"That sound reminded {hero.id} that magic can grow crooked when nobody tells the truth."
        )
    elif moral_choice == "return it":
        hero.memes["honesty"] = hero.memes.get("honesty", 0) + 1
        world.say(
            f"{hero.id} decided to return it, because a borrowed thing should find its own house again."
        )
    elif moral_choice == "share it":
        hero.memes["generosity"] = hero.memes.get("generosity", 0) + 1
        world.say(
            f"{hero.id} chose to share it, because one happy heart can make room for two."
        )
    else:
        hero.memes["honesty"] = hero.memes.get("honesty", 0) + 1
        world.say(
            f"{hero.id} told the truth at once, and the truth went off like a brass bell at noon."
        )

    if moral_choice in folder.reacts_to:
        hero.meters["wonder"] = hero.meters.get("wonder", 0) + 1
        hero.memes["hope"] = hero.memes.get("hope", 0) + 1
        world.say(
            f"The folder answered with a warm shimmer, as if it knew {hero.id} had done the right tall thing."
        )
    else:
        hero.memes["trouble"] = hero.memes.get("trouble", 0) + 1


def story_turn(world: World, hero: Entity, helper: Entity, folder: MagicFolder, moral_choice: str) -> None:
    world.para()
    if moral_choice == "keep it secret":
        world.say(
            f"Before long the folder felt heavier than a rain barrel, and {hero.id}'s conscience felt heavier still."
        )
        world.say(
            f"{helper.label.capitalize()} noticed the frown and said that a secret can bend a spirit like wet laundry on a line."
        )
        world.say(
            f"Then {hero.id} admitted the truth, and the folder's silver clasp flashed like a happy fish."
        )
    elif moral_choice == "return it":
        world.say(
            f"{hero.id} carried the folder back to its owner, and every step rang like a drum on a parade wagon."
        )
        world.say(
            f"The moment the folder was returned, it opened itself and out came a note, a grin, and a grateful nod."
        )
    elif moral_choice == "share it":
        world.say(
            f"{hero.id} shared the folder with {helper.label}, and together they sorted the papers like moonbeams being folded into place."
        )
        world.say(
            f"The folder glowed brighter each time they took turns, because magic likes a pair of fair hands."
        )
    else:
        world.say(
            f"When {hero.id} told the truth, the whole place seemed to stand taller, as if the world had straightened its hat."
        )
        world.say(
            f"{helper.label.capitalize()} smiled and said honesty had just opened the best lock in town."
        )


def story_end(world: World, hero: Entity, helper: Entity, folder: MagicFolder, action: str, moral_choice: str) -> None:
    world.para()
    if moral_choice in folder.reacts_to:
        hero.memes["joy"] = hero.memes.get("joy", 0) + 2
        world.say(
            f"At the end of the day, {hero.id} still got to {action}, but now the work was lighter and the laughter was bigger."
        )
        world.say(
            f"{folder.label.capitalize()} glimmered in {hero.id}'s hands, and its magic seemed to say that truth and kindness make the best kind of spark."
        )
    else:
        world.say(
            f"{hero.id} learned that a clever trick may shine for a minute, but a good choice shines longer than a lighthouse."
        )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    folder = FOLDERS[params.folder]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind=params.hero_kind))
    helper = world.add(Entity(id=params.helper_kind, kind="adult", label=f"the {params.helper_kind}"))
    magic = world.add(Entity(id=folder.id, kind="thing", label=folder.label, phrase=folder.phrase, owner=hero.id))
    hero.owner = None

    world.facts.update(hero=hero, helper=helper, folder=magic, action=params.action, moral=params.moral_choice)

    story_intro(world, hero, helper, folder)
    story_middle(world, hero, helper, folder, params.action, params.moral_choice)
    story_turn(world, hero, helper, folder, params.moral_choice)
    story_end(world, hero, helper, folder, params.action, params.moral_choice)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    folder: Entity = f["folder"]
    return [
        f'Write a tall tale for young children about {hero.id} and {folder.label} that teaches a moral choice.',
        f"Tell a magical story where {hero.id} finds {folder.phrase} and learns that honesty matters.",
        f'Create a child-friendly tall tale about a magic folder, a helpful grown-up, and a choice between keeping or returning it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    folder: Entity = f["folder"]
    action = f["action"]
    moral = f["moral"]
    place = world.place.label
    return [
        QAItem(
            question=f"What did {hero.id} find at {place}?",
            answer=f"{hero.id} found {folder.phrase} at {place}. It looked ordinary, but it was magical.",
        ),
        QAItem(
            question=f"Why did {hero.id} choose to {moral}?",
            answer=f"{hero.id} chose to {moral} because the folder's magic worked best with truth and kindness.",
        ),
        QAItem(
            question=f"Who helped {hero.id} understand what the folder meant?",
            answer=f"{helper.label.capitalize()} helped by explaining that the folder's magic was tied to good choices.",
        ),
        QAItem(
            question=f"What did {hero.id} still get to do at the end?",
            answer=f"{hero.id} still got to {action}, but the task felt lighter because the moral choice made the magic work well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a folder?",
            answer="A folder is something you use to hold papers, notes, or other flat things together.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and not pretending something is yours when it is not.",
        ),
        QAItem(
            question="Why can sharing be kind?",
            answer="Sharing is kind because it lets other people use or enjoy something instead of leaving them out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place={world.place.id}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library_steps", "carry notes", "blue_folder", "tell the truth", "Milo", "boy", "grandma"),
    StoryParams("market_square", "deliver papers", "red_folder", "share it", "Nina", "girl", "teacher"),
    StoryParams("old_orchard", "gather seeds", "blue_folder", "return it", "Toby", "boy", "neighbor"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for p in PLACES.values():
        for a in p.affords:
            for f in FOLDERS.values():
                for m in MORAL_CHOICES:
                    if moral_gate(p, a, f, m):
                        out.append((p.id, a, f.id, m))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.action and args.action not in PLACES[args.place].affords:
        raise StoryError(f"(No story: {args.action} does not fit {PLACES[args.place].label}.)")
    place = args.place or rng.choice(list(PLACES))
    action = args.action or rng.choice(sorted(PLACES[place].affords))
    folder = args.folder or rng.choice(list(FOLDERS))
    moral_choice = args.moral_choice or rng.choice(MORAL_CHOICES)
    if not moral_gate(PLACES[place], action, FOLDERS[folder], moral_choice):
        raise StoryError(explain_invalid(PLACES[place], action, FOLDERS[folder], moral_choice))
    hero_kind = args.hero_kind or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice([n for n, k in HEROES if k == hero_kind])
    helper_kind = args.helper_kind or rng.choice(HELPERS)
    return StoryParams(place, action, folder, moral_choice, hero_name, hero_kind, helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, action, folder, moral) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.action} at {p.place} (folder: {p.folder})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
