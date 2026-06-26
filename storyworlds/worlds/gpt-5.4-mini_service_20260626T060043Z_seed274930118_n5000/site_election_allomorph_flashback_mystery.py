#!/usr/bin/env python3
"""
A small storyworld about a site election mystery with an allomorph clue and a
flashback that helps solve it.

The premise:
- A child detective and a helper are deciding which site should host a tiny
  neighborhood election event.
- Different spoken forms of the same word ("allomorphs" in the phonology sense)
  become clues in a mystery.
- A flashback reveals who first wrote the clue and why it matters.
- The ending shows the chosen site and the solved mystery.

This script follows the Storyweavers world contract.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "site" | "clue"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "she"}
        male = {"boy", "father", "dad", "man", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Site:
    id: str
    label: str
    mood: str
    details: str
    offers: set[str] = field(default_factory=set)


@dataclass
class ClueForm:
    surface: str
    lemma: str
    meaning_hint: str
    place: str


@dataclass
class StoryParams:
    site: str
    mystery: str
    clue: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SITES = {
    "library": Site(
        id="library",
        label="the old library",
        mood="quiet",
        details="Tall shelves made the rooms feel like a whisper, and the front desk had a brass lamp.",
        offers={"meeting", "investigation"},
    ),
    "hall": Site(
        id="hall",
        label="the community hall",
        mood="echoey",
        details="The hall had a polished floor, paper stars, and a bulletin board for notices.",
        offers={"meeting", "election"},
    ),
    "garden": Site(
        id="garden",
        label="the school garden",
        mood="bright",
        details="The garden had bean poles, a stone path, and a bench that faced the sun.",
        offers={"meeting", "election", "investigation"},
    ),
    "station": Site(
        id="station",
        label="the little train station",
        mood="busy",
        details="The station smelled faintly of metal and rain, and people came and went in a hurry.",
        offers={"investigation", "meeting"},
    ),
}

MYSTERIES = {
    "missing_poster": {
        "title": "the missing poster",
        "effect": "poster vanished",
        "cause": "the poster was moved to the wrong board",
        "ending": "the poster was found behind the bulletin board",
    },
    "stolen_stamp": {
        "title": "the stolen stamp",
        "effect": "stamp disappeared",
        "cause": "the stamp had been borrowed and forgotten",
        "ending": "the stamp was returned from a coat pocket",
    },
    "wrong_box": {
        "title": "the wrong ballot box",
        "effect": "ballots looked mixed up",
        "cause": "someone placed the labels in the wrong order",
        "ending": "the labels were fixed and the box made sense again",
    },
}

ALLOMORPHS = {
    "leaf": [
        ClueForm(surface="leaf", lemma="leaf", meaning_hint="one plant leaf", place="garden"),
        ClueForm(surface="leaves", lemma="leaf", meaning_hint="more than one plant leaf", place="garden"),
    ],
    "mouse": [
        ClueForm(surface="mouse", lemma="mouse", meaning_hint="one small mouse", place="library"),
        ClueForm(surface="mice", lemma="mouse", meaning_hint="more than one small mouse", place="library"),
    ],
    "vote": [
        ClueForm(surface="vote", lemma="vote", meaning_hint="one choice in an election", place="hall"),
        ClueForm(surface="votes", lemma="vote", meaning_hint="many choices in an election", place="hall"),
    ],
}

NAMES_GIRL = ["Mina", "Ivy", "Lina", "Nora", "Ada", "Ruby"]
NAMES_BOY = ["Owen", "Theo", "Ben", "Milo", "Eli", "Noah"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "quiet"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(library). place(hall). place(garden). place(station).

offers(library,meeting). offers(library,investigation).
offers(hall,meeting). offers(hall,election).
offers(garden,meeting). offers(garden,election). offers(garden,investigation).
offers(station,meeting). offers(station,investigation).

mystery(missing_poster). mystery(stolen_stamp). mystery(wrong_box).

clue_surface(leaf,leaf). clue_surface(leaf,leaves).
clue_surface(mouse,mouse). clue_surface(mouse,mice).
clue_surface(vote,vote). clue_surface(vote,votes).

clue_place(leaf,garden).
clue_place(mouse,library).
clue_place(vote,hall).

compatible_site(S,M,C) :- place(S), mystery(M), clue_surface(C,_), clue_place(C,S), offers(S,election), offers(S,investigation).
valid_choice(S,M,C) :- place(S), mystery(M), clue_surface(C,_), clue_place(C,S), compatible_site(S,M,C).

#show valid_choice/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, site in SITES.items():
        lines.append(asp.fact("place", sid))
        for offer in sorted(site.offers):
            lines.append(asp.fact("offers", sid, offer))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for key, forms in ALLOMORPHS.items():
        for form in forms:
            lines.append(asp.fact("clue_surface", key, form.surface))
            lines.append(asp.fact("clue_place", key, form.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_choices() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_choice/3."))
    return sorted(set(asp.atoms(model, "valid_choice")))


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def clean_pronoun(name: str, gender: str) -> str:
    return name


def create_world(site_id: str) -> World:
    return World(SITES[site_id])


def detect_clue(world: World, clue: ClueForm, detective: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.id} noticed a small note with the word '{clue.surface}' on it."
    )
    world.say(
        f"It looked ordinary, but the note had been left at {world.site.label}, "
        f"which made the detective pause."
    )


def flashback(world: World, clue: ClueForm, helper: Entity) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    helper.memes["memory"] = helper.memes.get("memory", 0) + 1
    world.para()
    world.say(
        f"Then the detective remembered a flashback: yesterday, {helper.id} had "
        f"copied the clue while helping at the notice board."
    )
    world.say(
        f"In that earlier moment, the same word had changed form, because '{clue.lemma}' "
        f"had been written as '{clue.surface}' to match the meaning."
    )


def explain_mystery(world: World, detective: Entity, helper: Entity, clue: ClueForm, mystery: dict) -> None:
    world.para()
    detective.memes["insight"] = detective.memes.get("insight", 0) + 1
    detective.memes["relief"] = detective.memes.get("relief", 0) + 1
    world.say(
        f"{detective.id} looked again and saw the trick: the clue was an allomorph, "
        f"not a second secret."
    )
    world.say(
        f"The word changed shape because its meaning changed slightly, and that was the real hint."
    )
    world.say(
        f"At last, the mystery of {mystery['title']} made sense. {mystery['ending'].capitalize()}."
    )
    world.say(
        f"{helper.id} smiled, and the two of them could choose the best site without fear."
    )


def resolve_story(params: StoryParams) -> StorySample:
    world = create_world(params.site)
    mystery = MYSTERIES[params.mystery]
    clue_forms = ALLOMORPHS[params.clue]

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_gender,
        meters={"tired": 0.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        meters={"tired": 0.0},
        memes={"helpful": 1.0},
    ))
    clue = clue_forms[0]
    clue_ent = world.add(Entity(
        id="clue",
        kind="clue",
        type="clue",
        label=clue.surface,
        phrase=clue.meaning_hint,
        place=clue.place,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        clue=clue,
        clue_ent=clue_ent,
        mystery=mystery,
        site=world.site,
        allomorph=clue.surface,
    )

    world.say(
        f"At {world.site.label}, the air felt {world.site.mood}, and everyone was busy deciding where the election should happen."
    )
    world.say(world.site.details)
    world.say(
        f"{detective.id} was a quiet detective who liked small puzzles, and {helper.id} helped by watching details no one else noticed."
    )

    world.para()
    world.say(
        f"The problem was {mystery['effect']}, and that made the election feel unsettled."
    )
    detect_clue(world, clue, detective)
    flashback(world, clue, helper)
    explain_mystery(world, detective, helper, clue, mystery)

    world.para()
    if world.site.id == clue.place:
        world.say(
            f"In the end, they kept the election at {world.site.label}, because the clue pointed there all along."
        )
    else:
        world.say(
            f"In the end, they moved the election to {SITES[clue.place].label}, because that was where the clue belonged."
        )
    world.say(
        f"The note was no longer confusing. It was just a small word wearing two different shapes, and the mystery had a tidy ending."
    )

    story = world.render()
    prompts = [
        f"Write a child-friendly mystery about a site election and a clue that is an allomorph.",
        f"Tell a short story where {detective.id} and {helper.id} solve {mystery['title']} with a flashback.",
        f"Write a gentle detective story that uses the words site, election, and allomorph.",
    ]
    story_qa = [
        QAItem(
            question=f"What kind of clue did {detective.id} find at {world.site.label}?",
            answer=f"{detective.id} found an allomorph clue, which looked ordinary but mattered because it had two forms with the same basic meaning.",
        ),
        QAItem(
            question=f"Why did the flashback help the detective solve the mystery?",
            answer=(
                f"The flashback showed that {helper.id} had copied the clue before, so the detective realized "
                f"the strange-looking word was not another secret, just a different form of the same word."
            ),
        ),
        QAItem(
            question=f"Where did the story finally choose to hold the election?",
            answer=(
                f"The election stayed at {world.site.label}"
                if world.site.id == clue.place
                else f"The election moved to {SITES[clue.place].label}"
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an allomorph?",
            answer="An allomorph is a different form of the same word or morpheme that still carries the same basic meaning.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that goes back to an earlier time so the reader can learn something important from the past.",
        ),
        QAItem(
            question="What is an election?",
            answer="An election is when people choose between options or pick someone for a job or role.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# Generation / validation helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a site election and an allomorph clue.")
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--clue", choices=sorted(ALLOMORPHS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for site_id, site in SITES.items():
        if "election" not in site.offers:
            continue
        for mystery_id in MYSTERIES:
            for clue_id, forms in ALLOMORPHS.items():
                if any(f.place == site_id for f in forms):
                    combos.append((site_id, mystery_id, clue_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.site:
        combos = [c for c in combos if c[0] == args.site]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if not combos:
        raise StoryError("No valid story combination matches the chosen site/mystery/clue.")
    site, mystery, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice(NAMES_GIRL if helper_gender == "girl" else NAMES_BOY)
    return StoryParams(
        site=site,
        mystery=mystery,
        clue=clue,
        detective_name=detective_name,
        detective_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    return resolve_story(params)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"site: {world.site.label}")
    for ent in world.entities.values():
        parts = []
        if ent.meters:
            parts.append(f"meters={ent.meters}")
        if ent.memes:
            parts.append(f"memes={ent.memes}")
        if ent.place:
            parts.append(f"place={ent.place}")
        lines.append(f"  {ent.id} ({ent.kind}) " + " ".join(parts))
    lines.append(f"flashback_used: {world.flashback_used}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_choice/3."))
    return sorted(set(asp.atoms(model, "valid_choice")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(site="garden", mystery="missing_poster", clue="leaf", detective_name="Mina", detective_gender="girl", helper_name="Owen", helper_gender="boy"),
    StoryParams(site="hall", mystery="wrong_box", clue="vote", detective_name="Theo", detective_gender="boy", helper_name="Ada", helper_gender="girl"),
    StoryParams(site="library", mystery="stolen_stamp", clue="mouse", detective_name="Ivy", detective_gender="girl", helper_name="Ben", helper_gender="boy"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_sample(args: argparse.Namespace, seed: int) -> StorySample:
    rng = random.Random(seed)
    params = resolve_params(args, rng)
    params.seed = seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_choice/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible choices:")
        for c in combos:
            print("  ", c)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                sample = build_sample(args, base + i)
            except StoryError as e:
                print(e)
                return
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
            header = f"### {p.detective_name}: {p.site} / {p.mystery} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
