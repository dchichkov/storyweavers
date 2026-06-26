#!/usr/bin/env python3
"""
storyworlds/worlds/teat_quest_rhyme_whodunit.py
================================================

A small whodunit-style storyworld about a missing teat, a careful quest,
and a few playful rhyming clues.

Premise
-------
A hungry young animal needs its feeding teat right now.
The teat has gone missing, and the household turns into a tiny mystery.
A child detective and a grown helper follow clues, ask suspects, and find
the teat in a place that makes the final reveal feel earned.

World model
-----------
This world tracks:
- physical state: where the teat is, who has it, and whether the bottle is usable
- emotional state: worry, suspicion, and relief
- narrative state: clue trail, suspect list, and the final reveal

Narrative instruments
---------------------
- Quest: the search is deliberate, step-by-step, and goal-driven.
- Rhyme: some clues arrive as short child-friendly rhyming lines.
- Whodunit: the story pivots on a plausible suspect and a satisfying reveal.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "room"
    hides: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    hint: str
    can_hide: bool = False


@dataclass
class StoryParams:
    place: str
    suspect: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "caretaker": v.caretaker, "location": v.location,
            "carried_by": v.carried_by, "meters": dict(v.meters),
            "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_search_worry(world: World) -> list[str]:
    out: list[str] = []
    teat = world.get("teat")
    if teat.location == "missing":
        for person in world.entities.values():
            if person.kind == "character":
                if person.memes.get("worry", 0.0) >= THRESHOLD:
                    sig = f"worry:{person.id}"
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    out.append(f"{person.label} kept looking at the empty spot and worrying.")
    return out


def _r_return_teat(world: World) -> list[str]:
    teat = world.get("teat")
    bottle = world.get("bottle")
    if teat.carried_by == "detective" and teat.location == "found":
        sig = "return"
        if sig in world.fired:
            return []
        world.fired.add(sig)
        teat.carried_by = bottle.id
        teat.location = "on_bottle"
        bottle.meters["usable"] = 1.0
        return ["The bottle was ready again."]
    return []


CAUSAL_RULES = [Rule("search_worry", _r_search_worry), Rule("return_teat", _r_return_teat)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", hides={"drawer", "sink", "chair"}),
    "laundry": Place("laundry", "the laundry room", hides={"basket", "shelf", "pocket"}),
    "barn": Place("barn", "the barn", hides={"hay", "bucket", "crate"}),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "It was sleeping all morning.", "The clue said, 'A purr on the floor, but the teat is not where it was before.'"),
    "brother": Suspect("brother", "the big brother", "He was sweeping the floor.", "The clue said, 'A broom can roam, but it is not the teat's home.'"),
    "mouse": Suspect("mouse", "the mouse", "It was nibbling crumbs near the wall.", "The clue said, 'A tiny thief may scurry fast, but crumbs are not where teats are cast.'", can_hide=True),
}

HERO_NAMES = ["Mina", "Toby", "Lila", "Pip", "Nora", "Ben"]
HELPERS = {"mom": "mother", "dad": "father", "grandma": "grandmother"}


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in PLACES for s in SUSPECTS]


@dataclass
class WorldState:
    world: World
    detective: Entity
    helper: Entity
    baby: Entity
    teat: Entity
    bottle: Entity
    suspect: Suspect
    found_place: str = ""
    clue_lines: list[str] = field(default_factory=list)
    solved: bool = False


def setup_world(params: StoryParams) -> WorldState:
    place = PLACES[params.place]
    world = World(place)

    detective = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["curious", "careful"],
        memes={"worry": 0.0, "joy": 0.0, "suspicion": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        traits=["patient"],
        memes={"worry": 0.0, "joy": 0.0},
    ))
    baby = world.add(Entity(
        id="baby",
        kind="character",
        type="baby",
        label="the little kid",
        traits=["hungry"],
        memes={"worry": 1.0},
    ))
    teat = world.add(Entity(
        id="teat",
        type="teat",
        label="the teat",
        phrase="the little rubber teat",
        owner="bottle",
        location="missing",
    ))
    bottle = world.add(Entity(
        id="bottle",
        type="bottle",
        label="the bottle",
        phrase="the baby bottle",
        location="table",
        meters={"usable": 0.0},
    ))
    world.add(bottle)

    suspect = SUSPECTS[params.suspect]

    world.facts.update(
        place=place,
        detective=detective,
        helper=helper,
        baby=baby,
        teat=teat,
        bottle=bottle,
        suspect=suspect,
    )
    return WorldState(world, detective, helper, baby, teat, bottle, suspect)


def tell(params: StoryParams) -> WorldState:
    state = setup_world(params)
    w = state.world
    p = state.detective
    h = state.helper
    b = state.baby
    teat = state.teat
    suspect = state.suspect
    place = w.place

    p.memes["worry"] += 1
    b.memes["worry"] += 1

    w.say(
        f"{p.label} was a curious little {p.type} who liked tiny mysteries. "
        f"One morning, the little bottle was ready, but the teat was gone."
    )
    w.say(
        f"The little one got fussy, and {h.label} said, "
        f'"This is a job for a careful quest."'
    )
    w.para()

    w.say(
        f"They started in {place.label}. {p.label} looked under the chair, by the sink, "
        f"and behind the door."
    )
    w.say(
        f"Then a clue came in a rhyme: 'Near the chair, then far from there; if it is not seen, keep looking elsewhere.'"
    )
    state.clue_lines.append("chair-rhyme")
    p.memes["suspicion"] += 1

    w.say(
        f"{p.label} asked {suspect.label} first, because every whodunit needs a suspect with a reason."
    )
    w.say(suspect.alibi)
    w.say(suspect.hint)
    if suspect.can_hide:
        p.memes["suspicion"] += 1

    w.para()
    w.say(
        f"The quest went on. They checked the basket, the shelf, and the pocket pile."
    )
    if params.place == "laundry":
        state.found_place = "pocket"
    elif params.place == "kitchen":
        state.found_place = "drawer"
    else:
        state.found_place = "hay"

    rhyme_map = {
        "drawer": "A clatter, a rattle, a place to store; if the teat is lost, it may hide in a drawer.",
        "pocket": "A pocket is small and a little tight; it keeps a teat out of sight.",
        "hay": "In a pile of hay, the straw can play; a missing teat may hide that way.",
    }
    w.say(f"Another rhyme whispered: '{rhyme_map[state.found_place]}'")

    teat.location = "found"
    teat.carried_by = p.id
    p.memes["suspicion"] += 0.0
    propagate(w, narrate=True)

    w.para()
    p.memes["joy"] += 1
    p.memes["relief"] += 1
    b.memes["worry"] = 0.0
    state.solved = True
    w.say(
        f"At last, {p.label} found {teat.label} tucked in the {state.found_place}, "
        f"just where the clue had pointed."
    )
    w.say(
        f'{h.label} smiled. "That is the end of the riddle," {h.label} said. '
        f'"The bottle can feed the little one now."'
    )
    w.say(
        f"Soon the teat was back on the bottle, the little one was calm, and the room felt ordinary again."
    )

    return state


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a missing teat in {f["place"].label}.',
        f"Tell a gentle quest story where {f['detective'].label} follows rhyme clues to find the teat.",
        f'Write a tiny mystery with a suspect, a clue, and a happy ending where the bottle works again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    teat = f["teat"]
    suspect = f["suspect"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was missing at {place.label}?",
            answer=f"The teat was missing, and the little bottle could not feed the baby until it was found.",
        ),
        QAItem(
            question=f"Who acted like a detective in the story?",
            answer=f"{detective.label} acted like the detective and followed the clues step by step.",
        ),
        QAItem(
            question=f"Who helped solve the whodunit?",
            answer=f"{helper.label} helped with the careful quest and kept the search calm.",
        ),
        QAItem(
            question=f"Why did {suspect.label} seem worth asking about?",
            answer=f"{suspect.label} was a believable suspect in the mystery, so the detective asked first and checked the alibi.",
        ),
        QAItem(
            question=f"What proved the mystery was solved at the end?",
            answer=f"The teat was back on the bottle, so the baby could drink again and the room felt peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a teat?",
            answer="A teat is the soft part on a bottle or feeder that helps a baby or young animal drink milk.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, done step by step until the goal is reached.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a short bit of language where sounds match near the ends of words, which can make clues easy to remember.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story that asks who did it and then shows the answer with clues.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = list(PLACES.keys())
CURATED = [
    StoryParams(place="kitchen", suspect="cat", name="Mina", gender="girl", helper="mom"),
    StoryParams(place="laundry", suspect="brother", name="Toby", gender="boy", helper="dad"),
    StoryParams(place="barn", suspect="mouse", name="Lila", gender="girl", helper="grandma"),
]


ASP_RULES = r"""
% A teat is missing in a place.
missing_teat(P) :- at(teat, missing), place(P).

% A suspect is plausible when there is a hint and an alibi.
plausible(S) :- suspect(S), alibi(S, _), hint(S, _).

% A story is valid when the place and suspect are both available.
valid_story(P, S) :- place(P), suspect(S), plausible(S), missing_teat(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(p.hides):
            lines.append(asp.fact("hides", pid, h))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("alibi", sid, s.alibi))
        lines.append(asp.fact("hint", sid, s.hint))
    lines.append(asp.fact("at", "teat", "missing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, s) for p, s in valid_combos()}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: a missing teat, a quest, and rhyme clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
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
    combos = valid_combos()
    if args.place and args.suspect and (args.place, args.suspect) not in combos:
        raise StoryError("No valid mystery scene matches those explicit options.")
    choices = [c for c in combos
               if (args.place is None or c[0] == args.place)
               and (args.suspect is None or c[1] == args.suspect)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, suspect = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, suspect=suspect, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    state = tell(params)
    story = state.world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(state.world),
        story_qa=story_qa(state.world),
        world_qa=world_qa(state.world),
        world=state.world,
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible mystery combos:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: mystery at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
