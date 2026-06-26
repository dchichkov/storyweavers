#!/usr/bin/env python3
"""
Standalone storyworld: chitchat, roam, a small mystery to solve, and a moral value.

Premise:
- A child strolls through a cozy slice-of-life setting, chatting with a friend.
- A small mystery appears: a missing item, a strange sound, or a misplaced note.
- The child roams the setting, gathers clues, and solves it in a gentle way.
- A simple moral value is learned or demonstrated: honesty, sharing, patience, kindness, or fairness.

This world is intentionally small and constraint-checked. It generates a complete
short story plus grounded Q&A, and it includes an ASP twin for the reasonableness gate.
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
class Place:
    id: str
    label: str
    mood: str
    invites_roam: bool = True


@dataclass
class Character:
    id: str
    name: str
    role: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.role in {"girl", "mother", "woman"}:
            return "she"
        if self.role in {"boy", "father", "man"}:
            return "he"
        return "they"

    def possessive(self) -> str:
        return {"she": "her", "he": "his", "they": "their"}[self.pronoun()]


@dataclass
class Clue:
    id: str
    label: str
    where: str
    discovered_by_roam: bool = True


@dataclass
class Mystery:
    id: str
    label: str
    lost_item: str
    solved_by: str
    moral: str
    clue_ids: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    mystery: str
    moral: str
    hero_name: str
    hero_role: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.roamed = False
        self.solved = False

    def add(self, ent):
        self.entities[getattr(ent, "id")] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "street": Place("street", "the quiet street", "sunlit"),
    "market": Place("market", "the little market", "busy"),
    "garden": Place("garden", "the community garden", "green"),
    "library": Place("library", "the small library", "calm", invites_roam=True),
    "park": Place("park", "the neighborhood park", "breezy"),
}

MYSTERIES = {
    "lost_key": Mystery(
        id="lost_key",
        label="a lost key",
        lost_item="key",
        solved_by="finding it near the bench",
        moral="careful attention helps other people",
        clue_ids=["bench_glint", "jingle_sound"],
    ),
    "missing_note": Mystery(
        id="missing_note",
        label="a missing note",
        lost_item="note",
        solved_by="seeing it tucked in a book",
        moral="honesty matters even when something seems small",
        clue_ids=["paper_corner", "book_mark"],
    ),
    "mixed_baskets": Mystery(
        id="mixed_baskets",
        label="two mixed-up baskets",
        lost_item="basket tag",
        solved_by="reading the labels and swapping them back",
        moral="fairness means putting things back where they belong",
        clue_ids=["label_tag", "red_ribbon"],
    ),
}

CLUES = {
    "bench_glint": Clue("bench_glint", "a tiny glint on the bench", "by the bench"),
    "jingle_sound": Clue("jingle_sound", "a soft jingle from the path", "near the path"),
    "paper_corner": Clue("paper_corner", "a folded paper corner", "inside a book"),
    "book_mark": Clue("book_mark", "a bookmark sticking out", "between library pages"),
    "label_tag": Clue("label_tag", "a paper label", "on a basket handle"),
    "red_ribbon": Clue("red_ribbon", "a red ribbon", "on a shelf"),
}

MORAL_VALUES = {
    "kindness": "kindness means helping without making a fuss",
    "honesty": "honesty means telling the truth right away",
    "patience": "patience means slowing down and looking carefully",
    "fairness": "fairness means sharing and putting things in order",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life chitchat, roam, mystery, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-role", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
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
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    moral = args.moral or rng.choice(list(MORAL_VALUES))
    hero_role = args.hero_role or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(
        ["Mia", "Nina", "Leah", "Ari", "Nora", "Eli", "Noah", "Finn"]
        if hero_role == "girl" else
        ["Leo", "Ben", "Theo", "Milo", "Owen", "Sam", "Finn", "Max"]
    )
    friend_name = args.friend_name or rng.choice(
        ["Pip", "June", "Kit", "Tess", "Jules", "Remy", "Milo", "Sage"]
    )
    if place == "market" and mystery == "missing_note":
        pass
    if place == "library" and mystery == "lost_key":
        pass
    if not PLACES[place].invites_roam:
        raise StoryError("That place is too cramped for a roam-and-look-around story.")
    return StoryParams(
        place=place,
        mystery=mystery,
        moral=moral,
        hero_name=hero_name,
        hero_role=hero_role,
        friend_name=friend_name,
    )


def rhyme_line(mystery: Mystery, moral: str) -> str:
    rhyme = {
        "lost_key": "Look and peek, then speak with care; small clues hide everywhere.",
        "missing_note": "If something's not where it ought to be, look slowly and you may see.",
        "mixed_baskets": "When things are mixed, don't guess too fast; read the tags and make them last.",
    }[mystery.id]
    return f'"{rhyme}"'


def generate_story(world: World, params: StoryParams) -> None:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    moral_text = MORAL_VALUES[params.moral]

    hero = world.add(Character("hero", params.hero_name, params.hero_role, traits=["curious", "gentle"]))
    friend = world.add(Character("friend", params.friend_name, "friend", traits=["chatty", "kind"]))
    world.facts.update(hero=hero, friend=friend, place=place, mystery=mystery, moral=params.moral)

    world.say(f"{hero.name} and {friend.name} were having a little chitchat at {place.label}.")
    world.say(f"They liked to roam there after lunch, because the place felt {place.mood} and safe.")

    world.para()
    world.say(f"Then {hero.name} noticed {mystery.label}.")
    world.say(f"{friend.name} said, {rhyme_line(mystery, params.moral)}")
    world.say(f"{hero.name} smiled and kept roaming, looking for clues instead of making a fuss.")

    clue_sentences = {
        "lost_key": [
            f"Near the bench, {hero.name} saw {CLUES['bench_glint'].label}.",
            f"A little later, {friend.name} heard {CLUES['jingle_sound'].label}.",
        ],
        "missing_note": [
            f"Inside the library, {hero.name} spotted {CLUES['paper_corner'].label}.",
            f"Then {friend.name} found {CLUES['book_mark'].label}.",
        ],
        "mixed_baskets": [
            f"By the basket table, {hero.name} noticed {CLUES['label_tag'].label}.",
            f"On a shelf nearby, {friend.name} found {CLUES['red_ribbon'].label}.",
        ],
    }[mystery.id]
    world.say(clue_sentences[0])
    world.say(clue_sentences[1])

    world.para()
    world.say(f"At last, they solved the mystery by {mystery.solved_by}.")
    world.say(f"The lost thing went back where it belonged, and everybody could breathe easy again.")
    world.say(f"{hero.name} learned that {moral_text}.")
    world.say(f"That made the day feel even nicer, like a tidy little smile at the end." )

    world.facts["solved"] = True
    world.facts["moral_text"] = moral_text
    world.facts["rhyme"] = rhyme_line(mystery, params.moral)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle slice-of-life story about {f['hero'].id} and {f['friend'].id} who chitchat while they roam {f['place'].label}.",
        f"Tell a short mystery story where the children notice {f['mystery'].label} and solve it with careful looking.",
        f"Write a child-friendly story that includes a rhyme, a small mystery, and the moral idea of {f['moral']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    place: Place = f["place"]
    mystery: Mystery = f["mystery"]
    moral = f["moral_text"]
    return [
        QAItem(
            question=f"Who was chitchatting at {place.label}?",
            answer=f"{hero.name} and {friend.name} were chitchatting at {place.label}.",
        ),
        QAItem(
            question=f"What mystery did they notice while they roamed?",
            answer=f"They noticed {mystery.label} while they roamed around {place.label}.",
        ),
        QAItem(
            question=f"How did they solve the mystery?",
            answer=f"They solved it by {mystery.solved_by}.",
        ),
        QAItem(
            question=f"What moral did the story end with?",
            answer=f"The story ended with the moral that {moral}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to roam?",
            answer="To roam means to walk around without hurrying, often to look at what is nearby.",
        ),
        QAItem(
            question="What is chitchat?",
            answer="Chitchat is light, friendly talking about small everyday things.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like care and everywhere.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea about how to treat other people well, like honesty or kindness.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for eid, ent in world.entities.items():
        if isinstance(ent, Character):
            lines.append(f"  {eid}: character name={ent.name} role={ent.role} traits={ent.traits}")
    lines.append(f"  place={world.facts['place'].label}")
    lines.append(f"  mystery={world.facts['mystery'].label}")
    lines.append(f"  moral={world.facts['moral']}")
    lines.append(f"  solved={world.facts.get('solved', False)}")
    return "\n".join(lines)


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
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
character(C) :- hero(C).
character(C) :- friend(C).
mystery(M) :- mystery_item(M).
moral(M) :- moral_value(M).

can_story(P, M, V) :- setting(P), mystery_item(M), moral_value(V), roam_ok(P), mystery_ok(P, M).

roam_ok(street).
roam_ok(market).
roam_ok(garden).
roam_ok(library).
roam_ok(park).

mystery_ok(street, lost_key).
mystery_ok(market, mixed_baskets).
mystery_ok(garden, lost_key).
mystery_ok(library, missing_note).
mystery_ok(park, lost_key).
mystery_ok(park, mixed_baskets).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_item", mid))
    for mv in MORAL_VALUES:
        lines.append(asp.fact("moral_value", mv))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    clingo_set = set(asp.atoms(model, "can_story"))
    python_set = {
        (p, m, v)
        for p in PLACES
        for m in MYSTERIES
        for v in MORAL_VALUES
        if p in {"street", "market", "garden", "library", "park"} and m in {"lost_key", "missing_note", "mixed_baskets"}
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams("park", "lost_key", "patience", "Mia", "girl", "Pip"),
    StoryParams("library", "missing_note", "honesty", "Leo", "boy", "June"),
    StoryParams("market", "mixed_baskets", "fairness", "Nina", "girl", "Kit"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    generate_story(world, params)
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


def resolve_all(args: argparse.Namespace, seed: int) -> list[StoryParams]:
    rng = random.Random(seed)
    if args.all:
        return CURATED
    return [resolve_params(args, random.Random(seed + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_story/3."))
        triples = sorted(set(asp.atoms(model, "can_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
