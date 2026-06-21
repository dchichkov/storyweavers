#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hydrant_bookstore_magic_whodunit.py
====================================================================

A standalone story world for a small bookstore whodunit with magic, a hydrant,
a hidden clue, and a tidy reveal.

Premise:
- A child and a careful grown-up are in a bookstore.
- A magical mishap makes a hydrant clue appear where it should not.
- The characters investigate by following physical evidence and emotions.
- A harmless magical trick becomes the key to solving the mystery.

The world is intentionally small and constraint-checked: only plausible
bookstore whodunits are generated, and invalid user choices raise StoryError.
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    magical: bool = False
    clue_like: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    shelves: str
    quiet: str


@dataclass
class Magic:
    id: str
    title: str
    effect: str
    spark: str
    tag: str = "magic"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    is_hydrant: bool = False
    clue_kind: str = "object"


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    setting: str
    magic: str
    clue: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_spell(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["mystery"] >= THRESHOLD and ("mystery", e.id) not in world.fired:
            world.fired.add(("mystery", e.id))
            world.get("helper").memes["curiosity"] += 1
            out.append("__mystery__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["fear"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        world.get("child").memes["relief"] += 1
        out.append("The uneasy feeling slowly loosened.")
    return out


CAUSAL_RULES = [_r_spell, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, magic in MAGICS.items():
            for cid, clue in CLUES.items():
                if setting.id == "bookstore" and clue.is_hydrant:
                    combos.append((sid, mid, cid))
    return combos


def outcome_of(params: StoryParams) -> str:
    if RESPONSES[params.response].power >= 2:
        return "solved"
    return "muddled"


def explain_rejection(clue: Clue) -> str:
    return f"(No story: {clue.label} is the wrong kind of clue for a bookstore whodunit.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low for a clever story.)"


def tell(setting: Setting, magic: Magic, clue: Clue, response: Response,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         parent_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              traits=["careful", "clever"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    shelf = world.add(Entity(id="shelf", type="place", label=setting.place))
    clue_ent = world.add(Entity(id="clue", type="object", label=clue.label, magical=magic.id == "magic",
                                clue_like=True))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["setting"] = setting
    world.facts["magic"] = magic
    world.facts["clue"] = clue
    world.facts["response"] = response

    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(f"{child.id} and {helper.id} walked through {setting.place}, where the shelves stood quiet and tall.")
    world.say(f"Then a small spark of {magic.title.lower()} flashed near the stacks, and {magic.effect}.")
    world.say(f"At the end of the aisle, a {clue.label} showed up in the wrong place: {clue.phrase}.")
    world.say(f'"That does not belong here," {helper.id} whispered. "{child.id}, let us look closely."')

    world.para()
    child.meters["mystery"] += 1
    propagate(world, narrate=True)
    world.say(f"{child.id} noticed {clue.where}, and the odd clue seemed to point deeper into the bookstore.")
    world.say(f'"Maybe the trick is hiding the real answer," said {helper.id}.')
    world.say(f'"Or maybe it is trying to be seen," said {child.id}.')

    world.para()
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))
    if response.power >= 2:
        child.memes["brave"] += 1
        world.say(f"Together they followed the clue, and {helper.id} used the quiet plan to uncover the truth.")
        world.say(f"{parent.label_word.capitalize()} came over, listened, and {response.text}.")
        world.say(f"The mystery was solved when the false clue led them to a hidden note tucked behind a mystery novel.")
        world.say(f"In the end, the {clue.label} was only a magical pointer, and the bookstore grew calm again.")
        world.get("child").memes["relief"] += 1
    else:
        world.say(f"{parent.label_word.capitalize()} came over, but {response.fail}.")
        world.say(f"The clue stayed confusing, and the story ended with everyone still puzzling over the shelves.")
    world.facts["outcome"] = "solved" if response.power >= 2 else "muddled"
    return world


SETTINGS = {
    "bookstore": Setting(id="bookstore", place="the bookstore", shelves="the shelves", quiet="quiet"),
}

MAGICS = {
    "spark": Magic(id="spark", title="Magic Spark", effect="a trail of blue light twisted between the books", spark="blue"),
    "ink": Magic(id="ink", title="Magic Ink", effect="a silver word floated into the air", spark="silver"),
    "glimmer": Magic(id="glimmer", title="Magic Glimmer", effect="a soft glow blinked on and off like a lantern", spark="gold"),
}

CLUES = {
    "hydrant": Clue(id="hydrant", label="hydrant", phrase="a tiny red hydrant charm", where="between two mystery books", is_hydrant=True, clue_kind="object"),
    "bookmark": Clue(id="bookmark", label="bookmark", phrase="a torn bookmark with a spiral mark", where="inside a thick detective book", clue_kind="paper"),
    "key": Clue(id="key", label="key", phrase="a brass key with a star on it", where="under a stack of picture books", clue_kind="metal"),
}

RESPONSES = {
    "follow_clue": Response(id="follow_clue", sense=3, power=3,
                            text="followed the clue, found the hidden note, and read the answer out loud",
                            fail="followed the clue in circles and got more mixed up",
                            qa_text="followed the clue and found the hidden note"),
    "ask_bookseller": Response(id="ask_bookseller", sense=3, power=2,
                               text="asked the bookseller, who smiled and pointed to the hidden note",
                               fail="asked the bookseller, but the wrong question made things less clear",
                               qa_text="asked the bookseller and learned where the note was"),
    "peel_back_poster": Response(id="peel_back_poster", sense=2, power=2,
                                 text="carefully peeled back the poster and found the note behind it",
                                 fail="peeled back the poster too fast and made a mess of the clue",
                                 qa_text="carefully peeled back the poster and found the note"),
    "scatter_pages": Response(id="scatter_pages", sense=1, power=0,
                              text="scattered the pages, which only made a bigger jumble",
                              fail="scattered the pages and never found anything useful",
                              qa_text="scattered the pages"),
}

CHILD_NAMES = ["Mina", "Leo", "Nora", "Ari", "Pia", "Owen", "Zoe", "Eli"]
HELPER_NAMES = ["Jules", "Mara", "Tess", "Theo", "Noah", "Ivy", "June", "Sage"]


@dataclass
class StoryMeta:
    setting: str = "bookstore"
    magic: str = "spark"
    clue: str = "hydrant"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bookstore magic whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.clue and not CLUES[args.clue].is_hydrant:
        raise StoryError(explain_rejection(CLUES[args.clue]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.magic:
        combos = [c for c in combos if c[1] == args.magic]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, mid, cid = rng.choice(combos)
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=sid, magic=mid, clue=cid, response=response,
                       child=child, child_gender=child_gender, helper=helper,
                       helper_gender=helper_gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit set in {f["setting"].place} that includes the word "{f["clue"].label}" and a little bit of magic.',
        f'Tell a mystery story where {f["child"].id} and {f["helper"].id} notice a {f["clue"].label} in the bookstore and use a magical clue to solve the puzzle.',
        f'Write a short bookstore mystery with magic, a clue shaped like a hydrant, and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    clue: Clue = f["clue"]
    response: Response = f["response"]
    qa = [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens in {f['setting'].place}. The quiet shelves and narrow aisles make it feel like a place where clues can hide.",
        ),
        QAItem(
            question="What strange thing did they find?",
            answer=f"They found a {clue.label} in the wrong place. It looked like a clue because it was {clue.phrase}, not because it belonged there.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They used careful thinking and {response.qa_text}. That helped them notice the hidden note and understand what the magic was doing.",
        ),
    ]
    if f.get("outcome") == "solved":
        qa.append(QAItem(
            question=f"What did {child.id} learn by the end?",
            answer=f"{child.id} learned that a strange clue is only useful if you look at it calmly. With {helper.id}'s help, {child.pronoun()} could solve the case without causing a fuss.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a shop where people buy and read books. It is usually quiet, with shelves full of stories.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic is something unusual and impossible in real life. In a story, it can make strange lights, sounds, or clues appear.",
        ),
    ]
    if f["clue"].is_hydrant:
        items.append(QAItem(
            question="What is a hydrant?",
            answer="A hydrant is a water pipe or water outlet, often painted red and found outdoors. It can also be used in a story as a funny or surprising clue.",
        ))
    return items


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.magical:
            parts.append("magical=True")
        if e.clue_like:
            parts.append("clue_like=True")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    magic = MAGICS[params.magic]
    clue = CLUES[params.clue]
    response = RESPONSES[params.response]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent"))
    world.add(Entity(id="store", type="place", label=setting.place))
    clue_ent = world.add(Entity(id="clue", type="object", label=clue.label, magical=True, clue_like=True))
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1

    world.say(f"{child.id} and {helper.id} were in {setting.place}, where the shelves stood like rows of quiet secrets.")
    world.say(f"Then {magic.effect}, and the bookstore flickered with a little trick of {magic.title.lower()}.")
    world.say(f"Near the mystery books, a {clue.label} appeared out of place: {clue.phrase}.")
    world.say(f'"That is a clue," {helper.id} said softly. "{child.id}, let us solve this like detectives."')

    world.para()
    clue_ent.meters["mystery"] += 1
    child.meters["mystery"] += 1
    propagate(world, narrate=True)
    world.say(f"{child.id} looked at {clue.where} and noticed the clue was trying to point somewhere on purpose.")
    world.say(f"{helper.id} checked the books nearby and found a tiny note tucked where only a careful reader would look.")

    world.para()
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))
    if response.power >= 2:
        world.say(f"{parent.label_word.capitalize()} came over, listened to the story of the clue, and {response.text}.")
        world.say("The answer was simple in the end: the magic had hidden a note, and the hydrant clue was only there to lead the way.")
        world.say(f"So the mystery was solved, and {setting.place} went calm again with its shelves full of ordinary books.")
        child.memes["relief"] += 1
    else:
        world.say(f"{parent.label_word.capitalize()} came over, but {response.fail}.")
        world.say("The clue stayed puzzling, and the bookstore remained a jumble of guesses and whispers.")
    world.facts.update(child=child, helper=helper, parent=parent, setting=setting, magic=magic,
                       clue=clue, response=response, outcome="solved" if response.power >= 2 else "muddled")
    return world


CURATED = [
    StoryParams(setting="bookstore", magic="spark", clue="hydrant", response="follow_clue",
                child="Mina", child_gender="girl", helper="Jules", helper_gender="girl",
                parent="mother"),
    StoryParams(setting="bookstore", magic="ink", clue="hydrant", response="ask_bookseller",
                child="Leo", child_gender="boy", helper="Mara", helper_gender="girl",
                parent="father"),
    StoryParams(setting="bookstore", magic="glimmer", clue="hydrant", response="peel_back_poster",
                child="Nora", child_gender="girl", helper="Theo", helper_gender="boy",
                parent="mother"),
]


ASP_RULES = r"""
setting(bookstore).
magic(spark). magic(ink). magic(glimmer).
clue(hydrant). hydrant(hydrant).
response(follow_clue). response(ask_bookseller). response(peel_back_poster).
sense(follow_clue,3). sense(ask_bookseller,3). sense(peel_back_poster,2).
sense_min(2).
valid(S, M, C) :- setting(S), magic(M), clue(C), hydrant(C).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "bookstore")]
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.is_hydrant:
            lines.append(asp.fact("hydrant", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, magic=None, clue=None, response=None, parent=None,
            child=None, helper=None, child_gender=None, helper_gender=None
        ), random.Random(1)))
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.magic not in MAGICS:
        raise StoryError("unknown magic")
    if params.clue not in CLUES:
        raise StoryError("unknown clue")
    if params.response not in RESPONSES:
        raise StoryError("unknown response")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print(row)
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
            except StoryError as exc:
                print(exc)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
