#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/email_contaminate_conflict_surprise_ghost_story.py
==============================================================================================================================

A standalone story world for a tiny ghost story about an email that seems to
contaminate a child's quiet night, then turns into a surprising message from a
ghost.

Premise:
- A child is using a screen at bedtime.
- A strange email arrives and may contaminate the inbox with spooky clutter.
- A worried parent fears the bad message will spread fear and ruin the calm room.
- The child wants to open it anyway, causing conflict.
- The surprise: the "haunted" email is actually a lonely ghost asking for help.
- A simple, reasonable fix keeps the device clean and lets the child help the ghost.

This world uses physical meters and emotional memes as required by the contract.
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
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    guards: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"contaminate": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "conflict": 0.0, "surprise": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    quiet: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class GhostMail:
    id: str
    subject: str
    hook: str
    contaminate: str
    surprise: str
    tail: str
    keyword: str = "email"


@dataclass
class FilterGear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mail: str
    prize: str
    name: str
    gender: str
    parent: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": Setting(place="the bedroom", quiet=True, affords={"email"}),
    "kitchen": Setting(place="the kitchen", quiet=True, affords={"email"}),
    "attic": Setting(place="the attic room", quiet=False, affords={"email"}),
}

MAILS = {
    "ghost_note": GhostMail(
        id="ghost_note",
        subject="A whispery email from the dark",
        hook="an email that glowed like moonlight",
        contaminate="contaminate the inbox with spooky clutter",
        surprise="the message was from a lonely ghost",
        tail="the ghost only wanted a little help",
        keyword="email",
    ),
    "lost_bell": GhostMail(
        id="lost_bell",
        subject="Please find my bell",
        hook="a strange email with a tiny bell icon",
        contaminate="contaminate the screen with flickering cobwebs",
        surprise="the sender was a shy ghost under the stairs",
        tail="the ghost had dropped its bell and could not sleep without it",
        keyword="email",
    ),
    "midnight_wave": GhostMail(
        id="midnight_wave",
        subject="Hello from the moonlit hall",
        hook="a midnight email with a soft blue glow",
        contaminate="contaminate the inbox with chilly little sparks",
        surprise="the note was signed by a ghost in a nightcap",
        tail="the ghost wanted a friend, not trouble",
        keyword="email",
    ),
}

PRIZES = {
    "blanket": Entity(id="blanket", type="blanket", label="blanket", phrase="a warm striped blanket"),
    "lamp": Entity(id="lamp", type="lamp", label="lamp", phrase="a tiny bedside lamp"),
    "photo": Entity(id="photo", type="photo", label="photo", phrase="a favorite family photo"),
}

FILTERS = [
    FilterGear(
        id="spam_filter",
        label="a spam filter",
        prep="turn on the spam filter first",
        tail="turned on the spam filter",
        guards={"contaminate"},
    ),
    FilterGear(
        id="quiet_folder",
        label="a quiet folder",
        prep="move the email into a quiet folder",
        tail="moved the email into a quiet folder",
        guards={"contaminate"},
    ),
]

GIRL_NAMES = ["Mia", "Ava", "Lily", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Theo", "Max"]
TRAITS = ["curious", "gentle", "brave", "sleepy", "thoughtful", "small"]


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mail_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, mail_id, prize_id))
    return combos


def prize_at_risk(mail: GhostMail, prize: str) -> bool:
    return prize in {"blanket", "lamp", "photo"} and mail.keyword == "email"


def select_filter(mail: GhostMail, prize: str) -> Optional[FilterGear]:
    return FILTERS[0] if prize_at_risk(mail, prize) else None


def explain_rejection(mail: GhostMail, prize: str) -> str:
    return (
        f"(No story: this email would not plausibly contaminate a {prize} in a way "
        f"that creates a real conflict, so the ghost story would be too weak.)"
    )


def _do_check(world: World, hero: Entity, mail: GhostMail, narrate: bool = True) -> None:
    hero.meters["contaminate"] += 1
    hero.memes["curiosity"] += 1
    if hero.meters["contaminate"] >= THRESHOLD:
        hero.memes["fear"] += 1
    if narrate:
        world.say(
            f"When {hero.pronoun().capitalize()} opened the {mail.keyword}, "
            f"it seemed to {mail.contaminate}."
        )


def predict(world: World, hero: Entity, mail: GhostMail) -> dict:
    sim = world.copy()
    _do_check(sim, sim.get(hero.id), mail, narrate=False)
    return {
        "contaminate": sim.get(hero.id).meters["contaminate"] >= THRESHOLD,
        "fear": sim.get(hero.id).memes["fear"],
    }


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------

def tell(setting: Setting, mail: GhostMail, prize: Entity,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize_ent = world.add(Entity(
        id=prize.id, type=prize.type, label=prize.label, phrase=prize.phrase, caretaker=parent.id
    ))

    hero.memes["sleepy"] += 1
    world.say(
        f"{hero.name if hasattr(hero, 'name') else hero.id} was a little {trait} {hero.type} "
        f"who liked quiet nights in {setting.place}."
    )
    world.say(
        f"At bedtime, {hero.id} noticed {mail.hook} waiting in the inbox."
    )
    world.say(
        f"{hero.id} also loved {prize_ent.phrase}, and {prize_ent.label} sat nearby like a soft, safe thing."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to open the {mail.keyword} right away, but {hero.pronoun('possessive')} "
        f"{parent_type} frowned."
    )
    world.say(
        f'"That message might {mail.contaminate}," {hero.pronoun("possessive")} {parent_type} said.'
    )

    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} still leaned closer, because the glow looked curious."
    )
    _do_check(world, hero, mail, narrate=True)

    world.para()
    world.say(
        f"Then came a surprise: {mail.surprise}."
    )
    hero.memes["surprise"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    world.say(
        f"The email was not a trick after all. {mail.tail}."
    )

    gear = select_filter(mail, prize_ent.id)
    if gear:
        world.say(
            f"{hero.pronoun('possessive').capitalize()} {parent_type} said, "
            f'"Let\'s {gear.prep} before we answer."'
        )
        world.say(
            f"{hero.id} agreed, and they {gear.tail}. After that, {hero.id} sent a kind reply, "
            f"and the spooky clutter faded from the screen."
        )
        hero.memes["care"] += 1
        hero.memes["conflict"] = 0.0
    else:
        world.say(
            f"They closed the screen and waited until morning, so the strange glow could not spread."
        )

    world.say(
        f"In the end, the room was quiet again, and {prize_ent.label} stayed clean beside the bed."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize_ent,
        mail=mail,
        setting=setting,
        gear=gear,
        conflict=True,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    mail: GhostMail = f["mail"]
    return [
        f'Write a short ghost story for a small child that includes the word "{mail.keyword}".',
        f"Tell a bedtime story where {hero.id} finds a strange {mail.keyword}, gets into a conflict with {parent.label}, and then learns a surprising truth.",
        f'Write a gentle haunted-house story about an email that seems to contaminate a quiet room, but ends with kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    prize: Entity = f["prize"]
    mail: GhostMail = f["mail"]
    gear = f["gear"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Why did {hero.id}'s {parent.label} worry about the {mail.keyword}?",
            answer=(
                f"Because the message looked spooky, and it might {mail.contaminate} "
                f"the quiet room before bedtime."
            ),
        ),
        QAItem(
            question=f"What caused the conflict between {hero.id} and {parent.label}?",
            answer=(
                f"{hero.id} wanted to open the {mail.keyword} right away, but {parent.label} wanted to be careful."
            ),
        ),
        QAItem(
            question=f"What was the surprising truth about the email?",
            answer=(
                f"The surprise was that {mail.surprise}, so the scary message was really a request for help."
            ),
        ),
        QAItem(
            question=f"What stayed safe while they dealt with the {mail.keyword}?",
            answer=(
                f"{prize.label.capitalize()} stayed safe and clean beside the bed in {place}."
            ),
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help after the {mail.keyword} looked risky?",
                answer=(
                    f"They used {gear.label} to keep the strange message contained, so the spooky clutter faded and they could answer safely."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an email?",
            answer="An email is a message sent on a computer or phone so people can write to each other quickly.",
        ),
        QAItem(
            question="What does contaminate mean?",
            answer="To contaminate means to make something dirty, spoiled, or mixed up in a bad way.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that people often imagine in dark rooms, old houses, or bedtime tales.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(M, P) :- mail(M), prize(P).
has_filter(M, P) :- prize_at_risk(M, P), filter(F), helps(F, contaminate).
valid_story(Place, M, P, Gender) :- setting(Place), affords(Place, M), mail(M), prize(P), wears(Gender, P), has_filter(M, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid in MAILS:
        lines.append(asp.fact("mail", mid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        for g in ("girl", "boy"):
            lines.append(asp.fact("wears", g, pid))
    for fg in FILTERS:
        lines.append(asp.fact("filter", fg.id))
        for g in sorted(fg.guards):
            lines.append(asp.fact("helps", fg.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about an email that seems to contaminate a quiet room.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mail", choices=MAILS)
    ap.add_argument("--prize", choices=PRIZES)
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
    if args.mail and args.prize:
        if not prize_at_risk(MAILS[args.mail], args.prize):
            raise StoryError(explain_rejection(MAILS[args.mail], args.prize))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mail is None or c[1] == args.mail)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mail_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mail=mail_id,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MAILS[params.mail],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="bedroom", mail="ghost_note", prize="blanket", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="kitchen", mail="lost_bell", prize="photo", name="Leo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="attic", mail="midnight_wave", prize="lamp", name="Nora", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mail, prize) combos:\n")
        for c in combos:
            print(" ", c)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mail} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
