#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/conference_email_curiosity_sharing_moral_value_whodunit.py
=========================================================================================

A small standalone storyworld: a child at a conference, a missing email, and a
gentle whodunit about curiosity, sharing, and moral value.

This world keeps the mystery tiny and concrete:
- a conference has a shared program email
- one child notices something odd
- the child follows clues instead of accusing
- a hidden cause is found
- sharing the truth helps everyone
- the ending proves the changed state

The style aims for child-facing whodunit: clues, suspicion, reveal, and a moral
turn toward honesty and sharing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Conference:
    id: str
    setting: str
    place: str
    program: str
    crowd: str
    sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class EmailLead:
    id: str
    subject: str
    sender: str
    clue: str
    location: str
    secret: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HelperMove:
    id: str
    sense: int
    effect: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    conference: str
    email: str
    lead: str
    move: str
    child: str
    child_gender: str
    organizer: str
    organizer_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CONFERENCES = {
    "science_fair": Conference(
        id="science_fair",
        setting="a small school conference",
        place="the bright hall",
        program="the science program email",
        crowd="families and teachers",
        sound="soft voices and chair scrapes",
        tags={"conference", "email"},
    ),
    "library_day": Conference(
        id="library_day",
        setting="a cozy reading conference",
        place="the library room",
        program="the reading program email",
        crowd="kids, parents, and librarians",
        sound="pages turning and whispers",
        tags={"conference", "email"},
    ),
}

EMAILS = {
    "missing_schedule": EmailLead(
        id="missing_schedule",
        subject="schedule email",
        sender="the organizer",
        clue="the message had been forwarded to the shared board",
        location="the notice board",
        secret="the schedule was not lost at all",
        tags={"email"},
    ),
    "wrong_attachment": EmailLead(
        id="wrong_attachment",
        subject="email with the map",
        sender="the organizer",
        clue="the attachment showed a photo of the staff table",
        location="the staff table",
        secret="someone had mixed up the attachments",
        tags={"email"},
    ),
}

MORAL_MOVES = {
    "share_truth": HelperMove(
        id="share_truth",
        sense=3,
        effect=3,
        text="shared the email with everyone and told the truth out loud",
        qa_text="shared the truth and the correct email with everyone",
        tags={"sharing"},
    ),
    "post_copy": HelperMove(
        id="post_copy",
        sense=2,
        effect=2,
        text="posted a copy of the email on the board so everyone could see it",
        qa_text="posted a copy of the email for everyone to read",
        tags={"sharing"},
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Nora", "Ivy", "Zoe"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Noah", "Eli"]


def _investigate(world: World, child: Entity, lead: EmailLead) -> list[str]:
    if ("mystery", lead.id) in world.fired:
        return []
    world.fired.add(("mystery", lead.id))
    child.memes["curiosity"] += 1
    child.memes["care"] += 1
    world.say(
        f"{child.id} noticed something odd about the {lead.subject}. "
        f"{child.pronoun().capitalize()} kept looking instead of guessing."
    )
    world.say(
        f"{child.id} followed a clue: {lead.clue}. That made the whole mystery feel smaller."
    )
    return []


def _reveal(world: World, child: Entity, lead: EmailLead, organizer: Entity) -> list[str]:
    if ("reveal", lead.id) in world.fired:
        return []
    world.fired.add(("reveal", lead.id))
    world.say(
        f"At last, {child.id} found the answer at {lead.location}. "
        f"It turned out that {lead.secret}."
    )
    child.memes["relief"] += 1
    organizer.memes["surprise"] += 1
    return []


def _share(world: World, child: Entity, organizer: Entity, move: HelperMove) -> list[str]:
    if ("share", move.id) in world.fired:
        return []
    world.fired.add(("share", move.id))
    child.memes["sharing"] += 1
    child.memes["moral_value"] += 1
    organizer.memes["gratitude"] += 1
    world.say(
        f"Then {child.id} {move.text}. "
        f"{organizer.id} smiled, because telling the truth helped everyone at once."
    )
    return []


def _peace(world: World, child: Entity, conference: Conference, organizer: Entity) -> list[str]:
    if ("peace", conference.id) in world.fired:
        return []
    world.fired.add(("peace", conference.id))
    world.say(
        f"After that, the conference felt calm again. "
        f"The {conference.crowd} listened to the corrected message, and the room filled with easy laughter."
    )
    world.say(
        f"{child.id} walked back through {conference.place} feeling proud, because {child.pronoun()} had helped by sharing."
    )
    return []


CAUSAL_RULES = [
    Rule("investigate", lambda w: _investigate(w, w.get("child"), w.facts["lead"])),
    Rule("reveal", lambda w: _reveal(w, w.get("child"), w.facts["lead"], w.get("organizer"))),
    Rule("share", lambda w: _share(w, w.get("child"), w.get("organizer"), w.facts["move"])),
    Rule("peace", lambda w: _peace(w, w.get("child"), w.facts["conference"], w.get("organizer"))),
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            sents = rule.apply(world)
            if len(world.fired) != before:
                changed = True
            out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for c_id, conf in CONFERENCES.items():
        for e_id, lead in EMAILS.items():
            for m_id, move in MORAL_MOVES.items():
                if conf and lead and move.sense >= 2:
                    combos.append((c_id, e_id, m_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly whodunit at a conference involving an email, curiosity, sharing, and moral value."
    )
    ap.add_argument("--conference", choices=CONFERENCES)
    ap.add_argument("--email", choices=EMAILS)
    ap.add_argument("--move", choices=MORAL_MOVES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--organizer")
    ap.add_argument("--organizer-gender", choices=["woman", "man"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    c_id = args.conference or rng.choice(list(CONFERENCES))
    e_id = args.email or rng.choice(list(EMAILS))
    m_id = args.move or rng.choice(list(MORAL_MOVES))
    if (c_id, e_id, m_id) not in combos:
        raise StoryError("That conference, email, and move do not make a reasonable whodunit.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    organizer_gender = args.organizer_gender or rng.choice(["woman", "man"])
    child = args.child or _pick_name(rng, child_gender)
    organizer = args.organizer or ("Ms. Reed" if organizer_gender == "woman" else "Mr. Reed")
    return StoryParams(
        conference=c_id,
        email=e_id,
        lead=e_id,
        move=m_id,
        child=child,
        child_gender=child_gender,
        organizer=organizer,
        organizer_gender=organizer_gender,
    )


def tell(conf: Conference, lead: EmailLead, move: HelperMove, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="curious child"))
    organizer = world.add(Entity(id=params.organizer, kind="character", type=params.organizer_gender, role="organizer"))
    world.facts["conference"] = conf
    world.facts["lead"] = lead
    world.facts["move"] = move

    world.say(
        f"At {conf.setting}, {child.id} went to {conf.place} with {organizer.id}. "
        f"The air held {conf.sound}, and everyone expected the {conf.program} to be ready."
    )
    world.say(
        f"But something was wrong: the {lead.subject} was not where it should have been. "
        f"{child.id} felt a prick of curiosity and looked again."
    )
    world.para()
    propagate(world, narrate=False)
    world.say(
        f"That is how the little mystery began. {child.id} asked careful questions instead of pointing fingers."
    )
    world.para()
    world.say(
        f"When the clue finally made sense, {child.id} did the right thing and {move.text}."
    )
    world.say(
        f"{organizer.id} thanked {child.id} for the help, because sharing the answer was kinder than keeping it secret."
    )
    world.say(
        f"In the end, the {conf.program} was back where everyone could read it, and the conference could begin."
    )

    world.facts.update(
        child=child,
        organizer=organizer,
        outcome="solved",
        moral_value=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    conf = world.facts["conference"]
    lead = world.facts["lead"]
    return [
        f"Write a child-friendly whodunit set at {conf.setting} where a curious child notices a problem with an email and shares the answer.",
        f"Tell a short mystery story that includes the words 'conference' and 'email' and ends with someone sharing the truth kindly.",
        f"Write a gentle whodunit about a conference email, curiosity, sharing, and moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    conf = world.facts["conference"]
    lead = world.facts["lead"]
    child = world.facts["child"]
    organizer = world.facts["organizer"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was that the conference email was not where everyone expected it to be. {child.id} solved it by looking carefully instead of making a quick guess.",
        ),
        QAItem(
            question="How did curiosity help?",
            answer=f"{child.id} stayed curious and followed the clue. That careful looking led to the answer and helped the group fix the problem.",
        ),
        QAItem(
            question="Why was sharing important?",
            answer=f"Sharing mattered because {child.id} told the truth and showed the correct email to everyone. That made the conference calm again and helped {organizer.id} start on time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a conference?",
            answer="A conference is a meeting where people gather to learn, listen, or talk about a topic.",
        ),
        QAItem(
            question="What is an email?",
            answer="An email is a message sent on a computer or phone so people can share news quickly.",
        ),
        QAItem(
            question="Why is sharing a good moral value?",
            answer="Sharing is a good moral value because it helps other people and keeps a group fair and kind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(conference="science_fair", email="missing_schedule", lead="missing_schedule", move="share_truth", child="Mia", child_gender="girl", organizer="Ms. Reed", organizer_gender="woman"),
    StoryParams(conference="library_day", email="wrong_attachment", lead="wrong_attachment", move="post_copy", child="Leo", child_gender="boy", organizer="Mr. Reed", organizer_gender="man"),
]


def generate(params: StoryParams) -> StorySample:
    if params.conference not in CONFERENCES:
        raise StoryError("Unknown conference.")
    if params.email not in EMAILS:
        raise StoryError("Unknown email lead.")
    if params.move not in MORAL_MOVES:
        raise StoryError("Unknown sharing move.")
    world = tell(CONFERENCES[params.conference], EMAILS[params.email], MORAL_MOVES[params.move], params)
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
valid(C,E,M) :- conference(C), email(E), move(M), sense(M,S), S >= min_sense.
mystery(E) :- email(E).
solved :- curious(C), shared(M), valid(_,_,M).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("min_sense", 2)]
    for c in CONFERENCES:
        lines.append(asp.fact("conference", c))
    for e in EMAILS:
        lines.append(asp.fact("email", e))
    for m, move in MORAL_MOVES.items():
        lines.append(asp.fact("move", m))
        lines.append(asp.fact("sense", m, move.sense))
        if "sharing" in move.tags:
            lines.append(asp.fact("shared", m))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser_and_main() -> None:
    pass


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
