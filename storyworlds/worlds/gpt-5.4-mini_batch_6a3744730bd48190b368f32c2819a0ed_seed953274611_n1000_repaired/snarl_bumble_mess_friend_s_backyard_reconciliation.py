#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snarl_bumble_mess_friend_s_backyard_reconciliation.py
======================================================================================

A small mystery-leaning storyworld: one child visits a friend's backyard, hears a
snarl, notices a bumble, finds a mess, and discovers that the clue trail points to
a simple misunderstanding. The ending always includes reconciliation and a lesson
learned.

The world is built from a tiny state machine with typed entities, physical meters
and emotional memes, and a forward-chained causal model. The prose is authored
from the simulated state rather than by swapping nouns in a frozen paragraph.
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
SENSE_MIN = 2


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
class Place:
    id: str
    label: str
    owner_label: str
    features: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class Clue:
    id: str
    label: str
    hint: str
    source: str
    meaning: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    clue: str
    response: str
    delay: int = 0
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


PLACES = {
    "backyard": Place(
        id="backyard",
        label="a friend's backyard",
        owner_label="friend",
        features=["shed", "berry bush", "wooden fence", "small path"],
    )
}

CHILDREN_GIRL = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
CHILDREN_BOY = ["Tom", "Finn", "Max", "Ben", "Leo", "Sam"]

CLUES = {
    "snarl": Clue(
        id="snarl",
        label="a low snarl",
        hint="snarl",
        source="under the berry bush",
        meaning="something alive was nearby",
        tags={"snarl", "mystery"},
    ),
    "bumble": Clue(
        id="bumble",
        label="a soft bumble",
        hint="bumble",
        source="behind the shed",
        meaning="something small was moving and buzzing",
        tags={"bumble", "mystery"},
    ),
    "mess": Clue(
        id="mess",
        label="the messy trail",
        hint="mess",
        source="near the garden gate",
        meaning="the clue path was not danger, just a spill",
        tags={"mess", "mystery"},
    ),
}

RESPONSES = {
    "speak_softly": Response(
        id="speak_softly",
        sense=3,
        power=3,
        text="spoke softly to the hidden shape and followed the clues until the worry faded",
        fail="spoke softly, but the misunderstanding was still too tangled to sort out",
        qa_text="spoke softly and followed the clues until the worry faded",
        tags={"calm", "reconcile"},
    ),
    "bring_treats": Response(
        id="bring_treats",
        sense=3,
        power=4,
        text="brought a small snack and waited until the hidden shape came out friendly",
        fail="brought a small snack, but the hidden shape stayed shy and the clue trail stayed confusing",
        qa_text="brought a small snack and waited until things felt friendly",
        tags={"calm", "reconcile"},
    ),
    "call_friend": Response(
        id="call_friend",
        sense=2,
        power=4,
        text="called for the friend and asked about the strange sounds before guessing the worst",
        fail="called for the friend, but the backyard puzzle still needed one more careful look",
        qa_text="called for the friend and asked before guessing the worst",
        tags={"calm", "reconcile"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        power=1,
        text="shouted at the shadows and made everyone more upset",
        fail="shouted at the shadows and made the confusion grow",
        qa_text="shouted at the shadows",
        tags={"bad", "noisy"},
    ),
}

TRAITS = ["curious", "careful", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for cid in CLUES:
            for rid, resp in RESPONSES.items():
                if resp.sense >= SENSE_MIN:
                    combos.append((pid, cid, rid))
    return combos


def reasonableness_gate(clue: Clue, response: Response) -> bool:
    return clue.id in CLUES and response.sense >= SENSE_MIN


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(P,C,R) :- place(P), clue(C), response(R), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
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


def _r_snarl(world: World) -> list[str]:
    out = []
    if world.get("friend").meters["unease"] >= THRESHOLD and ("snarl",) not in world.fired:
        world.fired.add(("snarl",))
        world.get("child").memes["fear"] += 1
        out.append("The snarl made the yard feel like a secret.")
    return out


def _r_mess(world: World) -> list[str]:
    if world.get("clue").meters["noticed"] >= THRESHOLD and ("mess",) not in world.fired:
        world.fired.add(("mess",))
        world.get("child").memes["curiosity"] += 1
        return ["The messy trail looked odd, but it led somewhere important."]
    return []


def _r_reconcile(world: World) -> list[str]:
    if world.get("child").memes["reassured"] >= THRESHOLD and ("reconcile",) not in world.fired:
        world.fired.add(("reconcile",))
        world.get("friend").memes["relief"] += 1
        world.get("child").memes["relief"] += 1
        return ["The two friends found the truth and their smiles matched again."]
    return []


CAUSAL_RULES = [
    _r_snarl,
    _r_mess,
    _r_reconcile,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_resolution(world: World, response: Response) -> bool:
    sim = world.copy()
    sim.get("child").memes["reassured"] += response.power
    return response.power >= 3


def setup(world: World, child: Entity, friend: Entity, place: Place, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    friend.memes["unease"] += 1
    world.say(
        f"{child.id} visited {friend.id} in {place.label}. "
        f"The yard was neat except for one strange clue: {clue.label} {clue.source}."
    )


def mystery_turn(world: World, child: Entity, friend: Entity, clue: Clue) -> None:
    world.say(
        f"Then came the odd part -- a {clue.hint} from one side of the fence, "
        f"and a tiny pause from the other."
    )
    world.say(
        f"{friend.id} frowned because the clue seemed wrong, while {child.id} felt the puzzle tug harder."
    )
    child.meters["noticed"] += 1
    world.get("clue").meters["noticed"] += 1
    propagate(world)


def reveal(world: World, child: Entity, friend: Entity, clue: Clue, response: Response) -> None:
    child.memes["reassured"] += response.power
    world.say(
        f"{child.id} {response.text}."
    )
    world.say(
        f"It turned out the sound was only {clue.meaning}, and {friend.id} had been worried for nothing."
    )


def lesson(world: World, child: Entity, friend: Entity) -> None:
    world.say(
        f"After that, {child.id} and {friend.id} laughed together and put the backyard back in order."
    )
    world.say(
        "They learned that a strange sound is not always trouble, and that a calm question can solve a mystery faster than a guess."
    )


def tell(place: Place, clue: Clue, response: Response, child_name: str = "Mia",
         child_gender: str = "girl", friend_name: str = "Ben",
         friend_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="clue", type="clue", label=clue.label))

    setup(world, child, friend, place, clue)
    world.para()
    mystery_turn(world, child, friend, clue)
    world.para()
    reveal(world, child, friend, clue, response)
    world.para()
    lesson(world, child, friend)

    world.facts.update(
        child=child, friend=friend, place=place, clue=clue, response=response,
        reconciled=True, lesson=True, outcome="reconciled",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short mystery story for a 3-to-5-year-old that includes the words "snarl", "bumble", and "mess".',
        f"Tell a gentle mystery set in {f['place'].label} where {f['child'].id} and {f['friend'].id} solve a confusing clue and make up by the end.",
        "Write a child-facing mystery with a calm ending, a misunderstanding, reconciliation, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, clue = f["child"], f["friend"], f["clue"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a little mystery story set in {f['place'].label}. The strange clue sounds scary at first, but the friends solve it calmly.",
        ),
        QAItem(
            question="Why did the child feel curious about the backyard?",
            answer=f"{child.id} heard {clue.label} and saw {clue.source}, so the yard felt puzzling. The odd clue made {child.pronoun()} want to know the truth instead of guessing.",
        ),
        QAItem(
            question="How did the friends end the story?",
            answer=f"They reconciled after the mystery was explained. {child.id} and {friend.id} smiled again because the strange sounds were only a harmless misunderstanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where you do not know what is happening yet. Careful looking and calm thinking help solve it.",
        ),
        QAItem(
            question="Why should people ask a calm question when something sounds strange?",
            answer="A calm question helps everyone hear the facts and stop guessing the worst. That can keep friends from worrying and can fix misunderstandings faster.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a problem or worry. People talk kindly, understand each other, and feel close again.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(k[0] for k in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="backyard", child="Mia", child_gender="girl", friend="Ben", friend_gender="boy", clue="snarl", response="speak_softly"),
    StoryParams(place="backyard", child="Tom", child_gender="boy", friend="Lily", friend_gender="girl", clue="bumble", response="bring_treats"),
    StoryParams(place="backyard", child="Zoe", child_gender="girl", friend="Max", friend_gender="boy", clue="mess", response="call_friend"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld set in a friend's backyard.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--friend")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too noisy for a calm mystery story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, response = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if child_gender == "girl" else "girl"
    child = args.child or rng.choice(CHILDREN_GIRL if child_gender == "girl" else CHILDREN_BOY)
    friend = args.friend or rng.choice(CHILDREN_BOY if friend_gender == "boy" else CHILDREN_GIRL)
    if friend == child:
        friend = (set(CHILDREN_BOY + CHILDREN_GIRL) - {child}).pop()
    return StoryParams(place=place, child=child, child_gender=child_gender, friend=friend, friend_gender=friend_gender, clue=clue, response=response, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    resp = RESPONSES[params.response]
    if resp.sense < SENSE_MIN:
        raise StoryError("Chosen response is not sensible enough for this storyworld.")
    world = tell(PLACES[params.place], CLUES[params.clue], resp, params.child, params.child_gender, params.friend, params.friend_gender)
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


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    sensible = set(asp_sensible())
    if sensible == {rid for rid, r in RESPONSES.items() if r.sense >= SENSE_MIN}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c, r in combos:
            print(f"  {p:9} {c:6} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
